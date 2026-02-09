'''
Merkle DAG Log Storage System
==============================

A prototype append-only log storage system that organizes event streams into
a content-addressed Merkle DAG (Directed Acyclic Graph). Every event is
cryptographically chained to its predecessors, making tampering detectable
and providing a verifiable audit trail.

Overview
--------
Events arrive in the context of a **session** -- a dict of category→value
pairs (e.g. ``{"student": ["John"], "tool": ["editor"]}``).  Each session
is an append-only stream of **items**, where every item contains:

- The original event payload.
- A list of **children** hashes (the hash of the event content, the hash of
  the previous item in the stream, and any additional references).
- A **timestamp**.
- A **node hash** computed over the sorted children list and the timestamp.

Because each item's hash depends on its predecessor, the final item's hash
is a commitment to the *entire* stream -- the defining property of a Merkle
chain.  Modifying, inserting, or removing any item changes the final hash,
which makes tampering evident to anyone who recorded it.

Session Lifecycle
-----------------
1. **start** -- creates the first item in a new stream.
2. **event_to_session** -- appends an event to the running stream.
3. **close_session** -- appends a ``close`` event, renames the stream to
   its final hash (content-addressing), and propagates a
   ``child_session_finished`` event to every *parent* category stream.
4. **break_session** (optional) -- closes the current segment and
   immediately starts a continuation segment that references the old one.
   Useful for bounding segment size or inserting periodic checkpoints.

Parent Streams / Categories
----------------------------
When a session is closed, the system automatically notifies *parent*
streams.  For example, closing a session ``{"student": ["John"],
"tool": ["editor"]}`` appends a ``child_session_finished`` event to both
the ``{"student": "John"}`` stream and the ``{"tool": "editor"}`` stream.
This lets you walk from any category value down to every session that
involved it -- critical for data-subject access requests (GDPR Article 15)
and deletion requests (Article 17).

Deletion & Tombstones
---------------------
``delete_stream_with_tombstone`` removes all event data for a stream but
leaves behind a **tombstone** record that preserves:

- The stream key and final hash (so references from parent streams still
  make structural sense).
- The list of per-item hashes (so an auditor can confirm *which* data was
  deleted, even though the data itself is gone).
- A reason string and timestamp.

This satisfies the "right to erasure" while preserving the Merkle tree's
structural integrity for the data that *was* retained.

Verification
------------
``verify_chain`` walks a stream item-by-item and checks:

1. The event payload's hash appears in the item's children list.
2. The previous item's hash appears in the item's children list (except
   for the first item).
3. The node hash matches ``SHA-256(sorted(children) || timestamp)``.

If any check fails, a ``ValueError`` is raised with a diagnostic message.

Storage Backends
----------------
Two backends are provided:

- **InMemoryStorage** -- dict-of-lists; useful for tests and short-lived
  pipelines.
- **FSStorage** -- one file per stream (JSONL format); stream names are
  mapped to filenames via SHA-256 to avoid path-traversal issues.

Both are thread-safe (coarse ``threading.Lock``).  The ``StreamStorage``
base class defines the interface so that Kafka, S3, or database backends
can be added without changing the Merkle logic.

Async Integration
-----------------
``AsyncMerkle`` wraps ``Merkle`` and delegates every call to
``loop.run_in_executor`` so that blocking storage I/O does not stall an
``asyncio`` event loop.  See the "Pipeline Integration" section in the
companion documentation for a real-world usage example.

Visualization
-------------
If ``networkx`` and ``pydot`` are installed, any storage backend can be
exported to a NetworkX ``DiGraph`` or a Graphviz ``pydot.Dot`` object for
visual inspection of the DAG structure.  Visualizations include:

- **Color-coded nodes** by event type (start, close, continue, parent
  propagation, normal events, tombstones, deleted placeholders).
- **Typed edges** distinguishing chain links, content-hash references,
  cross-stream references, and tombstone→deleted relationships.
- **Stream clustering** via Graphviz subgraphs so that items belonging
  to the same stream are visually grouped.
- **Tombstone rendering** with placeholder nodes for deleted items and
  octagonal tombstone nodes showing deletion metadata.
- **Legend** explaining the visual encoding.

Design Goals
------------
1.  **Scalability** -- the only primitive is "append an item whose identity
    is its hash", which maps naturally to distributed stores (Kafka topics,
    S3 objects, etc.).
2.  **Data portability** -- every stream is self-contained; a data-subject
    access request can be fulfilled by exporting a bounded set of streams.
3.  **Erasure** -- tombstones remove PII while preserving the hash skeleton.
4.  **Auditability** -- the cryptographic chain lets any party verify that
    retained data has not been modified.  Publishing a daily top-level hash
    extends this guarantee to third parties.
5.  **Reproducibility** -- in the future, computation logs will be chained
    into the same DAG so that every analytical result can be traced back to
    the data and code that produced it.

Prototype Caveats
-----------------
This is a working prototype.  Production hardening would include:

- Kafka or equivalent backend for durable, distributed streaming.
- Full ``asyncio``-native storage (not executor-wrapped blocking I/O).
- Batched / periodic Merkle root publication.
- Proper stream-name escaping or deterministic session-ID generation.
- Chunk boundaries (hourly, daily, size-based) within long-lived streams.
- Encryption at rest for PII-bearing streams.
- Comprehensive property-based and integration tests.
'''

import hashlib
import json
import datetime
import os
import threading
from typing import Any, Dict, List, Optional, Set, Iterator, Tuple, Union
from dataclasses import dataclass, field

try:
    import pydot
    import networkx
    HAS_VIZ = True
except ImportError:
    HAS_VIZ = False


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def json_dump(obj: Any) -> str:
    '''Canonical JSON serialization (sorted keys, no extra whitespace).

    Sorting keys is essential: two dicts with the same content must always
    produce the same string so that their hashes agree.

    Parameters
    ----------
    obj : Any
        A JSON-serializable Python object.

    Returns
    -------
    str
        A compact JSON string with keys in sorted order.
    '''
    return json.dumps(obj, sort_keys=True)


def json_load(string: str) -> Any:
    '''Deserialize a JSON string.

    Parameters
    ----------
    string : str
        A valid JSON string.

    Returns
    -------
    Any
        The deserialized Python object.
    '''
    return json.loads(string)


# ---------------------------------------------------------------------------
# Thread-safe counter
# ---------------------------------------------------------------------------

class _AtomicCounter:
    '''Monotonically increasing counter safe for concurrent access.

    Used internally to generate unique sequence numbers when needed.
    Each call to :meth:`next` returns a value strictly greater than
    every previous call, regardless of which thread invokes it.
    '''

    def __init__(self):
        self._count = 0
        self._lock = threading.Lock()

    def next(self) -> int:
        '''Return the next integer in the sequence.'''
        with self._lock:
            self._count += 1
            return self._count


_counter = _AtomicCounter()


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

# In production this should be ``None`` (no truncation).  Set to a small
# integer for human-readable debugging output only.
HASH_TRUNCATE: Optional[int] = None


def merkle_hash(*strings: str) -> str:
    '''Compute a SHA-256 hex digest of tab-joined input strings.

    The inputs are joined with a tab character (``\\t``) before hashing.
    Tabs are forbidden *inside* any input string to guarantee that the
    concatenation is unambiguous (i.e. ``hash("a", "b")`` can never
    collide with ``hash("a\\tb")``).

    Parameters
    ----------
    *strings : str
        One or more strings, none of which may contain a tab.

    Returns
    -------
    str
        A lowercase hex SHA-256 digest, optionally truncated to
        :data:`HASH_TRUNCATE` characters for debugging.

    Raises
    ------
    ValueError
        If any input string contains a tab character.

    Examples
    --------
    >>> merkle_hash('hello', 'world')  # doctest: +SKIP
    'b0a43a0640...'
    '''
    for s in strings:
        if '\t' in s:
            raise ValueError(f'Input to merkle_hash must not contain tabs: {s!r}')
    digest = hashlib.sha256('\t'.join(strings).encode('utf-8')).hexdigest()
    if HASH_TRUNCATE is not None:
        return digest[:HASH_TRUNCATE]
    return digest


# ---------------------------------------------------------------------------
# Timestamps
# ---------------------------------------------------------------------------

def timestamp() -> str:
    '''Return the current UTC time as an ISO-8601 string.

    Used as the ``timestamp`` field in every Merkle item.  Including
    the timestamp in the hash input means that replaying the same event
    at a different time produces a different hash, preventing replay
    attacks.

    Returns
    -------
    str
        e.g. ``"2025-01-15T08:30:00.123456"``
    '''
    return datetime.datetime.utcnow().isoformat()


# ---------------------------------------------------------------------------
# Session key
# ---------------------------------------------------------------------------

def session_key(session: dict) -> str:
    '''Compute a deterministic string key for a *live* session dict.

    The key is the canonical JSON serialization of ``session``.  This
    guarantees that two calls with the same logical session always map
    to the same underlying stream, while different sessions never
    collide (assuming no hash truncation).

    Once a session is **closed**, its stream is renamed from this key to
    the stream's final content hash.

    Parameters
    ----------
    session : dict
        The session descriptor, e.g.
        ``{"student": ["Alice"], "tool": ["editor"]}``.

    Returns
    -------
    str
        The canonical JSON string of *session*.
    '''
    return json_dump(session)


# ---------------------------------------------------------------------------
# Visualization helpers
# ---------------------------------------------------------------------------

def _item_display_label(item: dict, stream_name: str = '') -> str:
    '''Build a multi-line label for a Merkle item node.

    Includes the event type (if present), a truncated hash, the
    timestamp, and the stream name (truncated).

    Parameters
    ----------
    item : dict
        A standard Merkle item with ``hash``, ``children``, ``event``,
        and ``timestamp`` fields.
    stream_name : str, optional
        The stream key this item belongs to.

    Returns
    -------
    str
        A newline-separated label string for Graphviz rendering.
    '''
    lines = []

    # Event type / label
    event = item.get('event', {})
    if isinstance(event, dict):
        etype = event.get('type', '')
        if etype:
            lines.append(etype.upper())
    if item.get('label') and (not lines or lines[0].lower() != item['label'].lower()):
        lines.append(item['label'])

    # Truncated hash
    h = item.get('hash', '?')
    lines.append(f'hash: {h[:12]}...')

    # Timestamp (just time portion if available)
    ts = item.get('timestamp', '')
    if 'T' in ts:
        lines.append(f'ts: {ts.split("T")[1][:12]}')
    elif ts:
        lines.append(f'ts: {ts[:16]}')

    # Stream context
    if stream_name:
        display_stream = stream_name if len(stream_name) <= 30 else stream_name[:27] + '...'
        lines.append(f'stream: {display_stream}')

    # Child count
    n_children = len(item.get('children', []))
    lines.append(f'children: {n_children}')

    return '\\n'.join(lines)


def _tombstone_display_label(tombstone: dict) -> str:
    '''Build a multi-line label for a tombstone node.

    Parameters
    ----------
    tombstone : dict
        A tombstone record with ``deleted_stream``, ``final_hash``,
        ``item_count``, ``reason``, ``timestamp``, and
        ``tombstone_hash`` fields.

    Returns
    -------
    str
        A newline-separated label string for Graphviz rendering.
    '''
    lines = [
        'TOMBSTONE',
        f'stream: {tombstone.get("deleted_stream", "?")[:20]}...',
        f'final: {tombstone.get("final_hash", "?")[:12]}...',
        f'items deleted: {tombstone.get("item_count", "?")}',
        f'reason: {tombstone.get("reason", "?")}',
    ]
    ts = tombstone.get('timestamp', '')
    if ts:
        lines.append(f'deleted: {ts[:19]}')
    th = tombstone.get('tombstone_hash', '?')
    lines.append(f'tombstone_hash: {th[:12]}...')
    return '\\n'.join(lines)


# Node style constants for Graphviz
_STYLE_NORMAL = {
    'shape': 'box',
    'style': 'filled',
    'fillcolor': '#E8F4FD',
    'fontname': 'Courier',
    'fontsize': '9',
}
_STYLE_START = {
    'shape': 'box',
    'style': 'filled,bold',
    'fillcolor': '#C8E6C9',
    'fontname': 'Courier',
    'fontsize': '9',
}
_STYLE_CLOSE = {
    'shape': 'box',
    'style': 'filled,bold',
    'fillcolor': '#FFCDD2',
    'fontname': 'Courier',
    'fontsize': '9',
}
_STYLE_CONTINUE = {
    'shape': 'box',
    'style': 'filled,dashed',
    'fillcolor': '#FFF9C4',
    'fontname': 'Courier',
    'fontsize': '9',
}
_STYLE_PARENT_EVENT = {
    'shape': 'box',
    'style': 'filled',
    'fillcolor': '#E1BEE7',
    'fontname': 'Courier',
    'fontsize': '9',
}
_STYLE_TOMBSTONE = {
    'shape': 'octagon',
    'style': 'filled,bold',
    'fillcolor': '#FFAB91',
    'fontname': 'Courier',
    'fontsize': '9',
    'penwidth': '2',
}
_STYLE_DELETED_PLACEHOLDER = {
    'shape': 'box',
    'style': 'dashed',
    'fillcolor': '#F5F5F5',
    'fontname': 'Courier',
    'fontsize': '8',
    'fontcolor': '#999999',
    'color': '#CCCCCC',
}
_EDGE_CHAIN = {
    'color': '#1565C0',
    'penwidth': '1.5',
}
_EDGE_CONTENT = {
    'color': '#999999',
    'style': 'dotted',
    'penwidth': '0.8',
}
_EDGE_CROSS_REF = {
    'color': '#E65100',
    'style': 'dashed',
    'penwidth': '1.2',
}
_EDGE_TOMBSTONE = {
    'color': '#D32F2F',
    'style': 'bold',
    'penwidth': '2',
}


def _classify_item(item: dict) -> str:
    '''Return a style classification string for an item.

    Parameters
    ----------
    item : dict
        A standard Merkle item.

    Returns
    -------
    str
        One of ``"start"``, ``"close"``, ``"continue"``,
        ``"parent_event"``, ``"normal"``.
    '''
    event = item.get('event', {})
    if not isinstance(event, dict):
        return 'normal'
    etype = event.get('type', '')
    if etype == 'start':
        return 'start'
    if etype == 'continue':
        return 'continue'
    if etype == 'close':
        return 'close'
    if etype == 'child_session_finished':
        return 'parent_event'
    return 'normal'


def _style_for_classification(classification: str) -> dict:
    '''Return the Graphviz attribute dict for a classification.

    Parameters
    ----------
    classification : str
        One of the strings returned by :func:`_classify_item`.

    Returns
    -------
    dict
        Graphviz node attributes.
    '''
    return {
        'start': _STYLE_START,
        'close': _STYLE_CLOSE,
        'continue': _STYLE_CONTINUE,
        'parent_event': _STYLE_PARENT_EVENT,
        'normal': _STYLE_NORMAL,
    }.get(classification, _STYLE_NORMAL)


# ---------------------------------------------------------------------------
# Merkle DAG
# ---------------------------------------------------------------------------

class Merkle:
    '''Core Merkle DAG engine.

    Manages append-only event streams, session lifecycle, chain
    verification, and tombstone deletion.

    Parameters
    ----------
    storage : StreamStorage
        The backend that persists streams.
    categories : set of str
        The set of category keys (e.g. ``{"student", "teacher"}``) that
        trigger parent-stream propagation when a session is closed.

    Attributes
    ----------
    storage : StreamStorage
    categories : set of str

    Notes
    -----
    This class is **not** thread-safe by itself; thread safety is
    delegated to the storage backend.  If two threads concurrently
    append to the *same* session, the chain linkage may be inconsistent.
    In production, each session should be owned by a single writer.
    '''

    def __init__(self, storage: 'StreamStorage', categories: Set[str]):
        self.storage = storage
        self.categories = categories

    # ---- core append ---------------------------------------------------

    def event_to_session(
        self,
        event: dict,
        session: dict,
        children: Optional[List[str]] = None,
        label: Optional[str] = None,
    ) -> dict:
        '''Append *event* to the Merkle chain for *session*.

        Constructs a new **item** whose ``hash`` field is a commitment
        to:

        - The SHA-256 of the event payload (ensures content integrity).
        - The hash of the previous item in the stream (ensures ordering
          and completeness -- no item can be removed or reordered
          without changing downstream hashes).
        - Any additional child hashes passed by the caller (e.g.
          cross-references to other streams).
        - The UTC timestamp (ensures temporal ordering and prevents
          replay).

        The item is appended to the stream identified by
        ``session_key(session)``.

        Parameters
        ----------
        event : dict
            Arbitrary JSON-serializable event payload.
        session : dict
            The session descriptor that identifies the target stream.
        children : list of str, optional
            Extra child hashes to include (e.g. references to other
            streams).  The event hash and previous-item hash are added
            automatically.
        label : str, optional
            A human-readable label stored on the item for visualization
            purposes.  Does **not** affect the hash.

        Returns
        -------
        dict
            The persisted item envelope with keys ``hash``,
            ``children``, ``timestamp``, ``event``, and optionally
            ``label``.
        '''
        if children is None:
            children = []
        else:
            children = list(children)          # don't mutate caller's list

        storage = self.storage
        sid = session_key(session)
        ts = timestamp()

        # 1. Hash the event payload itself
        event_hash = merkle_hash(json_dump(event))
        children.append(event_hash)

        # 2. Link to the previous item in this stream (if any)
        last_item = storage._most_recent_item(sid)
        if last_item is not None:
            children.append(last_item['hash'])

        # 3. Compute node hash AFTER children are fully assembled
        node_hash = merkle_hash(*sorted(children), ts)

        item = {
            'children': children,
            'hash': node_hash,
            'timestamp': ts,
            'event': event,
        }
        if label is not None:
            item['label'] = label

        storage._append_to_stream(sid, item)
        return item

    # ---- session lifecycle ---------------------------------------------

    def start(
        self,
        session: dict,
        metadata: Optional[dict] = None,
        continuation_hash: Optional[str] = None,
    ) -> dict:
        '''Open a new session stream (or continue one after a break).

        Creates a ``start`` (or ``continue``) event as the first item
        in a new stream.  If *continuation_hash* is provided, the new
        stream includes it as a child, creating a cross-segment link
        in the DAG.

        Parameters
        ----------
        session : dict
            Session descriptor.
        metadata : dict, optional
            Arbitrary metadata to include in the start event (e.g.
            client version, IP, request headers).
        continuation_hash : str, optional
            The final hash of a preceding segment.  When set, the
            event type is ``continue`` instead of ``start``, and the
            hash is recorded in the ``continues`` field and as a child.

        Returns
        -------
        dict
            The persisted start/continue item.
        '''
        event: Dict[str, Any] = {'type': 'start', 'session': session}
        if metadata is not None:
            event['metadata'] = metadata
        if continuation_hash is not None:
            event['type'] = 'continue'
            event['continues'] = continuation_hash

        extra_children = [continuation_hash] if continuation_hash else []
        return self.event_to_session(event, session,
                                     children=extra_children, label='start')

    def close_session(
        self,
        session: dict,
        logical_break: bool = False,
    ) -> str:
        '''Close *session* and finalize its stream.

        Appends a ``close`` event, renames the stream from its
        session-key to its **final content hash** (content-addressing),
        and -- unless *logical_break* is True -- propagates a
        ``child_session_finished`` event to every parent category
        stream.

        Parent propagation means that closing
        ``{"student": ["Alice"], "tool": ["editor"]}`` will append an
        event to both the ``{"student": "Alice"}`` and
        ``{"tool": "editor"}`` long-lived streams, recording the
        child session's hash.

        Parameters
        ----------
        session : dict
            The session descriptor to close.  Must match the descriptor
            used in :meth:`start`.
        logical_break : bool, optional
            If True, rename the stream but **do not** notify parent
            streams.  Used internally by :meth:`break_session`.

        Returns
        -------
        str
            The final hash of the closed session stream.  This is the
            stream's new key in storage.
        '''
        final_item = self.event_to_session(
            {'type': 'close', 'session': session},
            session,
            label='close',
        )
        session_hash = final_item['hash']
        self.storage._rename_or_alias_stream(session_key(session), session_hash)

        if logical_break:
            return session_hash

        # Propagate to parent (single-category) streams
        for key in session:
            if key not in self.categories:
                continue
            values = session[key]
            if not isinstance(values, list):
                values = [values]
            for value in values:
                parent_session = {key: value}
                self.event_to_session(
                    {
                        'type': 'child_session_finished',
                        'child_hash': session_hash,
                        'child_session': session,
                    },
                    parent_session,
                    children=[session_hash],
                    label=f'{key}:{value}',
                )
        return session_hash

    def break_session(self, session: dict) -> str:
        '''Insert a logical break in *session*.

        Closes the current segment (renaming it to its final hash) and
        immediately starts a new continuation segment that references
        the old one.  Useful for:

        - Bounding segment size for long-running sessions.
        - Creating periodic (e.g. hourly) checkpoints.
        - Enabling partial verification without downloading the full
          stream.

        Parameters
        ----------
        session : dict
            The session descriptor.

        Returns
        -------
        str
            The hash of the closed segment.
        '''
        segment_hash = self.close_session(session, logical_break=True)
        self.start(session, continuation_hash=segment_hash)
        return segment_hash

    # ---- verification --------------------------------------------------

    def verify_chain(self, stream_key: str) -> bool:
        '''Verify the integrity of every item in a stream.

        Walks the stream front-to-back and checks three invariants for
        each item:

        1. **Event inclusion** -- the SHA-256 of the item's ``event``
           payload appears in its ``children`` list.
        2. **Chain linkage** -- the previous item's ``hash`` appears in
           the current item's ``children`` list (skipped for the first
           item).
        3. **Hash correctness** -- the item's ``hash`` equals
           ``SHA-256(sorted(children) || timestamp)``.

        Any violation raises ``ValueError`` with a diagnostic message.

        Parameters
        ----------
        stream_key : str
            The key (typically the final hash) of the stream to verify.

        Returns
        -------
        bool
            ``True`` if the entire chain is valid.

        Raises
        ------
        ValueError
            If the stream is not found, is empty, or any item fails
            verification.
        '''
        data = self.storage._get_stream_data(stream_key)
        if not data:
            raise ValueError(f'Stream {stream_key!r} not found or empty')

        prev_hash: Optional[str] = None
        for i, item in enumerate(data):
            event_hash = merkle_hash(json_dump(item['event']))
            if event_hash not in item['children']:
                raise ValueError(
                    f'Item {i}: event hash {event_hash} not in children'
                )
            if prev_hash is not None and prev_hash not in item['children']:
                raise ValueError(
                    f'Item {i}: previous hash {prev_hash} not in children'
                )
            expected = merkle_hash(*sorted(item['children']), item['timestamp'])
            if item['hash'] != expected:
                raise ValueError(
                    f'Item {i}: hash mismatch (expected {expected}, got {item["hash"]})'
                )
            prev_hash = item['hash']
        return True

    # ---- deletion with tombstone ---------------------------------------

    def delete_stream_with_tombstone(self, stream_key: str, reason: str) -> dict:
        '''Delete a stream's data and leave a cryptographic tombstone.

        The tombstone preserves the stream's structural metadata --
        its key, final hash, the ordered list of per-item hashes, and
        the item count -- so that:

        - Parent streams still have a valid ``child_hash`` reference
          (it now points to a tombstone instead of data).
        - Auditors can confirm *what* was deleted and *when*, without
          being able to recover the deleted content.

        The tombstone itself is hashed and stored under the key
        ``__tombstone__<stream_key>``.

        Parameters
        ----------
        stream_key : str
            The key of the stream to delete (typically its final hash).
        reason : str
            A human-readable reason for deletion, e.g.
            ``"GDPR Article 17 erasure request"``.

        Returns
        -------
        dict
            The tombstone record, including its own
            ``tombstone_hash``.

        Raises
        ------
        ValueError
            If the stream does not exist or is already empty.
        '''
        data = self.storage._get_stream_data(stream_key)
        if not data:
            raise ValueError(f'Stream {stream_key!r} not found or empty')

        final_hash = data[-1]['hash']
        all_hashes = [item['hash'] for item in data]

        tombstone = {
            'type': 'tombstone',
            'deleted_stream': stream_key,
            'final_hash': final_hash,
            'item_hashes': all_hashes,
            'item_count': len(data),
            'reason': reason,
            'timestamp': timestamp(),
        }
        tombstone['tombstone_hash'] = merkle_hash(json_dump(tombstone))

        self.storage._delete_stream(stream_key)
        self.storage._append_to_stream(
            f'__tombstone__{stream_key}', tombstone
        )
        return tombstone


# ---------------------------------------------------------------------------
# Storage backends
# ---------------------------------------------------------------------------

class StreamStorage:
    '''Abstract base class for stream storage backends.

    A **stream** is an ordered list of JSON-serializable dicts
    (items) identified by a string key.  Backends must implement the
    following operations:

    - ``_append_to_stream(stream, item)`` -- append one item.
    - ``_rename_or_alias_stream(stream, alias)`` -- rename the stream
      key (used when a session is closed and the stream is
      content-addressed).
    - ``_get_stream_data(stream)`` -- return the full list of items,
      or ``None`` if the stream does not exist.
    - ``_delete_stream(stream)`` -- remove the stream entirely.
    - ``_most_recent_item(stream)`` -- return the last appended item,
      or ``None``.
    - ``_walk()`` -- iterate over every item in every stream (used for
      visualization and bulk export).
    - ``_walk_streams()`` -- iterate over ``(stream_key, items_list)``
      pairs (used for stream-aware visualization).

    All mutating operations must be **thread-safe**.  The simplest
    approach is a per-backend coarse lock (as used by
    :class:`InMemoryStorage` and :class:`FSStorage`).
    '''

    def _append_to_stream(self, stream: str, item: dict):
        '''Append *item* to the end of *stream*, creating it if needed.'''
        raise NotImplementedError

    def _rename_or_alias_stream(self, stream: str, alias: str):
        '''Rename *stream* to *alias*.  If they are equal, no-op.'''
        raise NotImplementedError

    def _get_stream_data(self, stream: str) -> Optional[List[dict]]:
        '''Return all items in *stream*, or ``None`` if it does not exist.

        An existing but empty stream should return ``[]``.
        '''
        raise NotImplementedError

    def _delete_stream(self, stream: str):
        '''Remove *stream* and all its items.  No-op if absent.'''
        raise NotImplementedError

    def _most_recent_item(self, stream: str) -> Optional[dict]:
        '''Return the last item in *stream*, or ``None`` if empty/absent.'''
        raise NotImplementedError

    def _walk(self) -> Iterator[dict]:
        '''Yield every item in every stream (arbitrary order).'''
        raise NotImplementedError

    def _walk_streams(self) -> Iterator[Tuple[str, List[dict]]]:
        '''Yield ``(stream_key, items_list)`` for every stream.

        Subclasses should override this for efficiency.  The default
        implementation raises ``NotImplementedError``.

        Returns
        -------
        Iterator of (str, list of dict)
            Each tuple contains the stream key and the full list of
            items (or tombstone records) in that stream.
        '''
        raise NotImplementedError

    # ---- internal helpers for visualization ----------------------------

    def _is_tombstone(self, item: dict) -> bool:
        '''Check whether *item* is a tombstone record (not a standard Merkle item).

        Tombstones have ``type == "tombstone"`` at the top level, whereas
        standard Merkle items have their ``type`` nested inside the ``event``
        dict.

        Parameters
        ----------
        item : dict
            An item or tombstone from a stream.

        Returns
        -------
        bool
        '''
        return item.get('type') == 'tombstone'

    def _collect_all_items(self) -> Tuple[Dict[str, List[dict]], Dict[str, List[dict]]]:
        '''Collect all items and tombstones, grouped by stream.

        Returns
        -------
        tuple of (items_by_stream, tombstones_by_stream)
            ``items_by_stream`` maps stream_key -> list of normal Merkle items.
            ``tombstones_by_stream`` maps stream_key -> list of tombstone dicts.
        '''
        items_by_stream: Dict[str, List[dict]] = {}
        tombstones_by_stream: Dict[str, List[dict]] = {}

        for stream_key, items in self._walk_streams():
            for item in items:
                if self._is_tombstone(item):
                    tombstones_by_stream.setdefault(stream_key, []).append(item)
                else:
                    items_by_stream.setdefault(stream_key, []).append(item)

        return items_by_stream, tombstones_by_stream

    # ---- convenience / visualization -----------------------------------

    def _make_label(self, item: dict, stream_name: str = '') -> str:
        '''Derive a short human-readable label for *item*.

        Priority:

        1. The explicit ``label`` field, if present.
        2. A ``category:value`` string if the event contains a
           single-key session dict.
        3. The first 8 hex characters of the item hash.

        Parameters
        ----------
        item : dict
            A standard Merkle item.
        stream_name : str, optional
            The stream key (unused in the short label but accepted for
            API consistency with :func:`_item_display_label`).

        Returns
        -------
        str
        '''
        if item.get('label'):
            return item['label']
        event = item.get('event', {})
        if isinstance(event, dict) and 'session' in event and isinstance(event['session'], dict):
            keys = list(event['session'].keys())
            if len(keys) == 1:
                k = keys[0]
                return f'{k}:{event["session"][k]}'
        return item.get('hash', '?')[:8]

    def to_networkx(self):
        '''Export the entire DAG as a :class:`networkx.DiGraph`.

        Each Merkle item becomes a node keyed by its hash, with
        attributes for ``label``, ``short_label``, ``stream``,
        ``event_type``, ``classification``, ``timestamp``, and
        ``tombstone`` (bool).

        Tombstones are included as nodes keyed by their
        ``tombstone_hash``, with ``tombstone=True`` and additional
        attributes ``deleted_stream``, ``reason``, and ``item_count``.

        Edges carry an ``edge_type`` attribute:

        - ``"chain"`` -- link to the previous item in the same stream.
        - ``"content"`` -- link to the event-payload hash (a virtual
          node representing the raw content).
        - ``"cross_ref"`` -- any other child reference (e.g. to a
          closed session from a parent stream).
        - ``"tombstone"`` -- from a tombstone to each of the deleted
          item hashes it records.

        Returns
        -------
        networkx.DiGraph

        Raises
        ------
        ImportError
            If ``networkx`` or ``pydot`` are not installed.
        '''
        if not HAS_VIZ:
            raise ImportError('networkx/pydot not installed')

        G = networkx.DiGraph()
        items_by_stream, tombstones_by_stream = self._collect_all_items()

        # All known item hashes (so we can distinguish chain vs cross-ref edges)
        all_item_hashes: Set[str] = set()
        for items in items_by_stream.values():
            for item in items:
                all_item_hashes.add(item['hash'])

        # Add normal item nodes and edges
        for stream_key, items in items_by_stream.items():
            prev_hash = None
            for item in items:
                classification = _classify_item(item)
                event = item.get('event', {})
                event_type = event.get('type', '') if isinstance(event, dict) else ''

                G.add_node(
                    item['hash'],
                    label=_item_display_label(item, stream_key),
                    short_label=self._make_label(item, stream_key),
                    stream=stream_key,
                    event_type=event_type,
                    classification=classification,
                    timestamp=item.get('timestamp', ''),
                    tombstone=False,
                )

                # Classify edges
                event_hash = merkle_hash(json_dump(item['event']))
                for child in item.get('children', []):
                    if child == prev_hash:
                        G.add_edge(item['hash'], child, edge_type='chain')
                    elif child == event_hash:
                        # Content hash -- may not correspond to a real item node
                        if child not in G:
                            G.add_node(
                                child,
                                label=f'content\\n{child[:12]}...',
                                short_label=child[:8],
                                classification='content_hash',
                                tombstone=False,
                            )
                        G.add_edge(item['hash'], child, edge_type='content')
                    else:
                        G.add_edge(item['hash'], child, edge_type='cross_ref')

                prev_hash = item['hash']

        # Add tombstone nodes and edges
        for stream_key, tombstones in tombstones_by_stream.items():
            for tombstone in tombstones:
                t_hash = tombstone.get('tombstone_hash', f'tombstone_{id(tombstone)}')
                G.add_node(
                    t_hash,
                    label=_tombstone_display_label(tombstone),
                    short_label=f'tombstone {t_hash[:8]}',
                    stream=stream_key,
                    classification='tombstone',
                    tombstone=True,
                    deleted_stream=tombstone.get('deleted_stream', ''),
                    reason=tombstone.get('reason', ''),
                    item_count=tombstone.get('item_count', 0),
                )

                # Edges to the hashes that were deleted
                for deleted_hash in tombstone.get('item_hashes', []):
                    if deleted_hash not in G:
                        # Add placeholder for the deleted node
                        G.add_node(
                            deleted_hash,
                            label=f'[deleted]\\n{deleted_hash[:12]}...',
                            short_label=f'del {deleted_hash[:8]}',
                            classification='deleted',
                            tombstone=False,
                        )
                    G.add_edge(t_hash, deleted_hash, edge_type='tombstone')

                # Edge from tombstone to the final hash if not already a node
                final_hash = tombstone.get('final_hash', '')
                if final_hash and final_hash not in G:
                    G.add_node(
                        final_hash,
                        label=f'[deleted final]\\n{final_hash[:12]}...',
                        short_label=f'del {final_hash[:8]}',
                        classification='deleted',
                        tombstone=False,
                    )

        return G

    def to_graphviz(self):
        '''Export the entire DAG as a styled :class:`pydot.Dot` Graphviz graph.

        Nodes are color-coded by type:

        - **Green** -- ``start`` / ``continue`` events.
        - **Red (light)** -- ``close`` events.
        - **Yellow (light)** -- ``continue`` events.
        - **Purple** -- ``child_session_finished`` (parent propagation).
        - **Blue (light)** -- normal events.
        - **Orange** (octagon) -- tombstones.
        - **Grey** (dashed) -- deleted-item placeholders.

        Edges are styled by relationship:

        - **Blue solid** -- chain link (prev -> next within a stream).
        - **Grey dotted** -- content hash reference.
        - **Orange dashed** -- cross-stream reference.
        - **Red bold** -- tombstone -> deleted item.

        Items belonging to the same stream are grouped into Graphviz
        ``cluster`` subgraphs with distinct background colors.

        A legend cluster is included to explain the visual encoding.

        Can be rendered to PNG, SVG, PDF, etc. via::

            dot = storage.to_graphviz()
            dot.write_png('merkle_dag.png')

        Returns
        -------
        pydot.Dot

        Raises
        ------
        ImportError
            If ``pydot`` is not installed.
        '''
        if not HAS_VIZ:
            raise ImportError('pydot not installed')

        G = pydot.Dot(
            graph_type='digraph',
            rankdir='TB',
            bgcolor='white',
            fontname='Courier',
            label='Merkle DAG Log',
            labelloc='t',
            fontsize='14',
        )
        G.set_node_defaults(fontname='Courier', fontsize='9')

        items_by_stream, tombstones_by_stream = self._collect_all_items()

        # Track all item hashes for edge classification
        all_item_hashes: Set[str] = set()
        for items in items_by_stream.values():
            for item in items:
                all_item_hashes.add(item['hash'])

        # Group items into subgraphs by stream for visual clustering
        stream_colors = [
            '#E3F2FD', '#F3E5F5', '#E8F5E9', '#FFF8E1',
            '#FCE4EC', '#E0F7FA', '#FBE9E7', '#F1F8E9',
        ]
        color_idx = 0

        for stream_key, items in items_by_stream.items():
            # Create a subgraph cluster for this stream
            cluster_name = f'cluster_{hashlib.sha256(stream_key.encode()).hexdigest()[:12]}'
            display_key = stream_key if len(stream_key) <= 40 else stream_key[:37] + '...'
            subgraph = pydot.Cluster(
                cluster_name,
                label=display_key,
                style='rounded,filled',
                fillcolor=stream_colors[color_idx % len(stream_colors)],
                color='#BBBBBB',
                fontname='Courier',
                fontsize='8',
            )
            color_idx += 1

            prev_hash = None
            for item in items:
                classification = _classify_item(item)
                style_attrs = _style_for_classification(classification)
                label = _item_display_label(item, stream_key)

                node = pydot.Node(item['hash'], label=label, **style_attrs)
                subgraph.add_node(node)

                # Classify and add edges
                event_hash = merkle_hash(json_dump(item['event']))
                for child in item.get('children', []):
                    if child == prev_hash:
                        G.add_edge(pydot.Edge(
                            item['hash'], child, **_EDGE_CHAIN
                        ))
                    elif child == event_hash:
                        # Only add content-hash nodes if they aren't already
                        # a real item (avoids duplicate nodes)
                        if child not in all_item_hashes:
                            content_node = pydot.Node(
                                child,
                                label=f'content\\n{child[:12]}...',
                                shape='ellipse',
                                style='dashed',
                                fillcolor='#FAFAFA',
                                fontname='Courier',
                                fontsize='7',
                                fontcolor='#999999',
                                color='#CCCCCC',
                            )
                            G.add_node(content_node)
                        G.add_edge(pydot.Edge(
                            item['hash'], child, **_EDGE_CONTENT
                        ))
                    else:
                        G.add_edge(pydot.Edge(
                            item['hash'], child, **_EDGE_CROSS_REF
                        ))

                prev_hash = item['hash']

            G.add_subgraph(subgraph)

        # Add tombstone nodes (outside stream clusters since the stream is deleted)
        for stream_key, tombstones in tombstones_by_stream.items():
            for tombstone in tombstones:
                t_hash = tombstone.get('tombstone_hash', f'tombstone_{id(tombstone)}')
                label = _tombstone_display_label(tombstone)

                tomb_node = pydot.Node(t_hash, label=label, **_STYLE_TOMBSTONE)
                G.add_node(tomb_node)

                # Collect all item_hashes from this tombstone for dedup
                tombstone_item_hashes = set(tombstone.get('item_hashes', []))

                # Add placeholder nodes for each deleted item hash
                for deleted_hash in tombstone.get('item_hashes', []):
                    if deleted_hash not in all_item_hashes:
                        placeholder = pydot.Node(
                            deleted_hash,
                            label=f'[deleted]\\n{deleted_hash[:12]}...',
                            **_STYLE_DELETED_PLACEHOLDER,
                        )
                        G.add_node(placeholder)
                    G.add_edge(pydot.Edge(
                        t_hash, deleted_hash, **_EDGE_TOMBSTONE
                    ))

                # Also link to final hash if it's not already a node
                final_hash = tombstone.get('final_hash', '')
                if final_hash and final_hash not in all_item_hashes:
                    if final_hash not in tombstone_item_hashes:
                        placeholder = pydot.Node(
                            final_hash,
                            label=f'[deleted final]\\n{final_hash[:12]}...',
                            **_STYLE_DELETED_PLACEHOLDER,
                        )
                        G.add_node(placeholder)

        # Add a legend
        legend = pydot.Cluster(
            'legend',
            label='Legend',
            style='rounded',
            color='#CCCCCC',
            fontname='Courier',
            fontsize='9',
        )
        legend_items = [
            ('legend_start', 'START', _STYLE_START),
            ('legend_close', 'CLOSE', _STYLE_CLOSE),
            ('legend_continue', 'CONTINUE', _STYLE_CONTINUE),
            ('legend_normal', 'EVENT', _STYLE_NORMAL),
            ('legend_parent', 'PARENT UPDATE', _STYLE_PARENT_EVENT),
            ('legend_tombstone', 'TOMBSTONE', _STYLE_TOMBSTONE),
            ('legend_deleted', '[DELETED]', _STYLE_DELETED_PLACEHOLDER),
        ]
        for node_id, label, style in legend_items:
            legend.add_node(pydot.Node(node_id, label=label, **style))
        G.add_subgraph(legend)

        return G


class InMemoryStorage(StreamStorage):
    '''In-memory storage backend backed by a ``dict[str, list[dict]]``.

    Suitable for tests, short-lived pipelines, and demonstrations.
    All data is lost when the process exits.

    Thread safety is provided by a single ``threading.Lock`` that
    serializes all operations.
    '''

    def __init__(self):
        super().__init__()
        self._store: Dict[str, List[dict]] = {}
        self._lock = threading.Lock()

    def _append_to_stream(self, stream, item):
        with self._lock:
            self._store.setdefault(stream, []).append(item)

    def _rename_or_alias_stream(self, stream, alias):
        with self._lock:
            if alias == stream:
                return
            self._store[alias] = self._store.pop(stream)

    def _get_stream_data(self, stream):
        with self._lock:
            if stream not in self._store:
                return None
            return list(self._store[stream])

    def _delete_stream(self, stream):
        with self._lock:
            self._store.pop(stream, None)

    def _most_recent_item(self, stream):
        with self._lock:
            items = self._store.get(stream)
            if not items:
                return None
            return items[-1]

    def _walk(self):
        with self._lock:
            snapshot = {k: list(v) for k, v in self._store.items()}
        for items in snapshot.values():
            yield from items

    def _walk_streams(self):
        '''Yield ``(stream_key, items_list)`` for every stream.'''
        with self._lock:
            snapshot = {k: list(v) for k, v in self._store.items()}
        for stream_key, items in snapshot.items():
            yield stream_key, items


class FSStorage(StreamStorage):
    '''Filesystem-backed storage (one JSONL file per stream).

    Each stream is stored as a file where every line is a single
    JSON-serialized item.  Filenames are the SHA-256 of the stream
    key to avoid path-traversal and encoding issues.

    Parameters
    ----------
    path : str
        Directory in which stream files are created.  Will be created
        (including parents) if it does not exist.

    Notes
    -----
    This backend is adequate for prototyping but has several
    performance limitations:

    - ``_most_recent_item`` reads the entire file to return the last
      line.
    - ``_rename_or_alias_stream`` is not atomic across crashes.
    - No write-ahead log or fsync guarantees.
    '''

    def __init__(self, path: str):
        super().__init__()
        self.path = path
        os.makedirs(path, exist_ok=True)
        self._lock = threading.Lock()
        # Maintain a reverse mapping: filename_hash -> stream_key
        # so _walk_streams can report meaningful keys
        self._key_map: Dict[str, str] = {}
        self._key_map_lock = threading.Lock()

    def _fn(self, stream: str) -> str:
        '''Map a stream name to a filesystem path.

        Uses SHA-256 of the stream name to produce a safe, fixed-length
        filename that avoids path-traversal and special-character
        issues.
        '''
        safe = hashlib.sha256(stream.encode('utf-8')).hexdigest()
        with self._key_map_lock:
            self._key_map[safe] = stream
        return os.path.join(self.path, safe)

    def _append_to_stream(self, stream, item):
        with self._lock:
            with open(self._fn(stream), 'a') as f:
                f.write(json_dump(item) + '\n')

    def _rename_or_alias_stream(self, stream, alias):
        with self._lock:
            src, dst = self._fn(stream), self._fn(alias)
            if src == dst:
                return
            os.rename(src, dst)

    def _get_stream_data(self, stream):
        path = self._fn(stream)
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            return [json_load(line) for line in f if line.strip()]

    def _delete_stream(self, stream):
        path = self._fn(stream)
        if os.path.exists(path):
            os.remove(path)

    def _most_recent_item(self, stream):
        data = self._get_stream_data(stream)
        if not data:
            return None
        return data[-1]

    def _walk(self):
        for filename in os.listdir(self.path):
            filepath = os.path.join(self.path, filename)
            if not os.path.isfile(filepath):
                continue
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        yield json_load(line)

    def _walk_streams(self):
        '''Yield ``(stream_key, items_list)`` for every stream.'''
        for filename in os.listdir(self.path):
            filepath = os.path.join(self.path, filename)
            if not os.path.isfile(filepath):
                continue
            # Recover stream key from reverse mapping if possible
            with self._key_map_lock:
                stream_key = self._key_map.get(filename, filename)
            items = []
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        items.append(json_load(line))
            yield stream_key, items


# ---------------------------------------------------------------------------
# Async wrapper
# ---------------------------------------------------------------------------

try:
    import asyncio
except ImportError:
    asyncio = None  # type: ignore[assignment]


class AsyncMerkle:
    '''Async wrapper around :class:`Merkle`.

    Delegates every call to ``loop.run_in_executor(None, ...)`` so
    that blocking storage I/O does not stall an ``asyncio`` event loop.

    For the :class:`InMemoryStorage` backend this is largely cosmetic,
    but for filesystem, network, or database backends the executor
    offload prevents event-loop starvation.

    Parameters
    ----------
    merkle : Merkle
        The synchronous Merkle instance to wrap.
    loop : asyncio.AbstractEventLoop, optional
        An explicit event loop.  If ``None``, ``asyncio.get_event_loop()``
        is called at invocation time.

    Examples
    --------
    ::

        storage = InMemoryStorage()
        merkle = Merkle(storage, CATEGORIES)
        am = AsyncMerkle(merkle)

        await am.start(session)
        await am.event_to_session(event, session)
        final_hash = await am.close_session(session)
        assert await am.verify_chain(final_hash)
    '''

    def __init__(self, merkle: Merkle, loop=None):
        self._merkle = merkle
        self._loop = loop

    def _get_loop(self):
        return self._loop or asyncio.get_event_loop()

    async def start(self, session, **kwargs):
        '''Async version of :meth:`Merkle.start`.'''
        return await self._get_loop().run_in_executor(
            None, lambda: self._merkle.start(session, **kwargs)
        )

    async def event_to_session(self, event, session, **kwargs):
        '''Async version of :meth:`Merkle.event_to_session`.'''
        return await self._get_loop().run_in_executor(
            None, lambda: self._merkle.event_to_session(event, session, **kwargs)
        )

    async def close_session(self, session, **kwargs):
        '''Async version of :meth:`Merkle.close_session`.'''
        return await self._get_loop().run_in_executor(
            None, lambda: self._merkle.close_session(session, **kwargs)
        )

    async def verify_chain(self, stream_key):
        '''Async version of :meth:`Merkle.verify_chain`.'''
        return await self._get_loop().run_in_executor(
            None, lambda: self._merkle.verify_chain(stream_key)
        )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

CATEGORIES: Set[str] = {
    'teacher', 'student', 'school', 'classroom', 'course', 'assignment', 'tool',
}
'''
The set of category keys recognized for parent-stream propagation.

When a session containing one of these keys is closed, a
``child_session_finished`` event is appended to the corresponding
single-category parent stream.
'''

STORES = {
    'fs': FSStorage,
    'inmemory': InMemoryStorage,
}
'''
Registry of available storage backends, keyed by short name.

Used by configuration-driven code to instantiate a backend from a
string identifier.
'''


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------

def test_case():
    '''End-to-end smoke test exercising start -> events -> close -> verify -> delete -> visualize.'''
    storage = InMemoryStorage()
    merkle = Merkle(storage, CATEGORIES)

    session = {
        'teacher': ['Mr. A'],
        'student': ['John'],
    }

    merkle.start(session)
    merkle.event_to_session({'type': 'event', 'payload': 'A'}, session, label='A')
    merkle.event_to_session({'type': 'event', 'payload': 'B'}, session, label='B')
    merkle.event_to_session({'type': 'event', 'payload': 'C'}, session, label='C')
    final_hash = merkle.close_session(session)

    # Verify the closed session chain
    assert merkle.verify_chain(final_hash)
    print(f'Chain verified: {final_hash}')

    # Verify parent chains
    for parent_key in [json_dump({'teacher': 'Mr. A'}), json_dump({'student': 'John'})]:
        data = storage._get_stream_data(parent_key)
        if data:
            print(f'Parent stream {parent_key[:40]}... has {len(data)} item(s)')

    # Test tombstone deletion
    tombstone = merkle.delete_stream_with_tombstone(final_hash, reason='GDPR request')
    print(f'Tombstone: {tombstone["tombstone_hash"]}')
    assert storage._get_stream_data(final_hash) is None
    print('All checks passed.')

    # Test visualization (if dependencies available)
    if HAS_VIZ:
        print('\nGenerating visualizations...')

        # NetworkX export
        G = storage.to_networkx()
        print(f'NetworkX graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')

        # Check that tombstone node exists
        tombstone_nodes = [n for n, d in G.nodes(data=True) if d.get('tombstone')]
        print(f'Tombstone nodes: {len(tombstone_nodes)}')

        # Check deleted placeholder nodes exist
        deleted_nodes = [n for n, d in G.nodes(data=True)
                         if d.get('classification') == 'deleted']
        print(f'Deleted placeholder nodes: {len(deleted_nodes)}')

        # Check edge types
        edge_types = {}
        for u, v, d in G.edges(data=True):
            et = d.get('edge_type', 'unknown')
            edge_types[et] = edge_types.get(et, 0) + 1
        print(f'Edge types: {edge_types}')

        # Graphviz export
        dot = storage.to_graphviz()
        print(f'Graphviz DOT: {len(dot.get_node_list())} nodes, '
              f'{len(dot.get_edge_list())} edges')

        # Optionally write to file
        # dot.write_png('merkle_dag.png')
        # dot.write_svg('merkle_dag.svg')
        print('Visualization generation complete.')
    else:
        print('Skipping visualization (networkx/pydot not installed)')


if __name__ == '__main__':
    test_case()
