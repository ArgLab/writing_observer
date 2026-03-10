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

Both expose an async interface.  :class:`InMemoryStorage` methods are
trivially async (no real I/O), while :class:`FSStorage` offloads blocking
file operations to the default executor via
:meth:`asyncio.loop.run_in_executor`.  The :class:`StreamStorage` base
class defines the async interface so that Kafka, S3, or database backends
can be added without changing the Merkle logic.

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
- Batched / periodic Merkle root publication.
- Proper stream-name escaping or deterministic session-ID generation.
- Chunk boundaries (hourly, daily, size-based) within long-lived streams.
- Encryption at rest for PII-bearing streams.
- Comprehensive property-based and integration tests.
'''

import asyncio
import hashlib
import json
import datetime
import os
import threading
from typing import Any, Dict, List, Optional, Set, Iterator, Tuple, Union
from dataclasses import dataclass, field
from concurrent.futures import Executor

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
    '''Core async Merkle DAG engine.

    Manages append-only event streams, session lifecycle, chain
    verification, and tombstone deletion.  All public methods are
    coroutines so they integrate naturally with an ``asyncio`` event
    loop.

    Parameters
    ----------
    storage : StreamStorage
        The backend that persists streams.  All storage methods are
        async.
    categories : set of str
        The set of category keys (e.g. ``{"student", "teacher"}``) that
        trigger parent-stream propagation when a session is closed.

    Attributes
    ----------
    storage : StreamStorage
    categories : set of str

    Notes
    -----
    Each session should be owned by a single writer.  If two
    coroutines concurrently append to the *same* session, the chain
    linkage may be inconsistent.
    '''

    def __init__(self, storage: 'StreamStorage', categories: Set[str]):
        self.storage = storage
        self.categories = categories

    # ---- core append ---------------------------------------------------

    async def event_to_session(
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
        last_item = await storage.most_recent_item(sid)
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

        await storage.append_to_stream(sid, item)
        return item

    # ---- session lifecycle ---------------------------------------------

    async def start(
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
        return await self.event_to_session(event, session,
                                           children=extra_children, label='start')

    async def close_session(
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
        final_item = await self.event_to_session(
            {'type': 'close', 'session': session},
            session,
            label='close',
        )
        session_hash = final_item['hash']
        await self.storage.rename_or_alias_stream(session_key(session), session_hash)

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
                await self.event_to_session(
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

    async def break_session(self, session: dict) -> str:
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
        segment_hash = await self.close_session(session, logical_break=True)
        await self.start(session, continuation_hash=segment_hash)
        return segment_hash

    # ---- verification --------------------------------------------------

    async def verify_chain(self, stream_key: str) -> bool:
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
        data = await self.storage.get_stream_data(stream_key)
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

    async def delete_stream_with_tombstone(self, stream_key: str, reason: str) -> dict:
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
        data = await self.storage.get_stream_data(stream_key)
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

        await self.storage.delete_stream(stream_key)
        await self.storage.append_to_stream(
            f'__tombstone__{stream_key}', tombstone
        )
        return tombstone


# ---------------------------------------------------------------------------
# Storage backends
# ---------------------------------------------------------------------------

class StreamStorage:
    '''Abstract base class for async stream storage backends.

    A **stream** is an ordered list of JSON-serializable dicts
    (items) identified by a string key.  Backends must implement the
    following async operations:

    - ``append_to_stream(stream, item)`` -- append one item.
    - ``rename_or_alias_stream(stream, alias)`` -- rename the stream
      key (used when a session is closed and the stream is
      content-addressed).
    - ``get_stream_data(stream)`` -- return the full list of items,
      or ``None`` if the stream does not exist.
    - ``delete_stream(stream)`` -- remove the stream entirely.
    - ``most_recent_item(stream)`` -- return the last appended item,
      or ``None``.
    - ``walk()`` -- async-iterate over every item in every stream (used
      for visualization and bulk export).
    - ``walk_streams()`` -- async-iterate over ``(stream_key, items_list)``
      pairs (used for stream-aware visualization).

    All mutating operations must be **safe for concurrent awaits**.
    '''

    async def append_to_stream(self, stream: str, item: dict):
        '''Append *item* to the end of *stream*, creating it if needed.'''
        raise NotImplementedError

    async def rename_or_alias_stream(self, stream: str, alias: str):
        '''Rename *stream* to *alias*.  If they are equal, no-op.'''
        raise NotImplementedError

    async def get_stream_data(self, stream: str) -> Optional[List[dict]]:
        '''Return all items in *stream*, or ``None`` if it does not exist.

        An existing but empty stream should return ``[]``.
        '''
        raise NotImplementedError

    async def delete_stream(self, stream: str):
        '''Remove *stream* and all its items.  No-op if absent.'''
        raise NotImplementedError

    async def most_recent_item(self, stream: str) -> Optional[dict]:
        '''Return the last item in *stream*, or ``None`` if empty/absent.'''
        raise NotImplementedError

    async def walk(self) -> List[dict]:
        '''Return every item in every stream (arbitrary order).

        Returns a list rather than an async iterator for simplicity.
        '''
        raise NotImplementedError

    async def walk_streams(self) -> List[Tuple[str, List[dict]]]:
        '''Return ``(stream_key, items_list)`` for every stream.

        Returns a list rather than an async iterator for simplicity.

        Returns
        -------
        list of (str, list of dict)
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

    async def _collect_all_items(self) -> Tuple[Dict[str, List[dict]], Dict[str, List[dict]]]:
        '''Collect all items and tombstones, grouped by stream.

        Returns
        -------
        tuple of (items_by_stream, tombstones_by_stream)
            ``items_by_stream`` maps stream_key -> list of normal Merkle items.
            ``tombstones_by_stream`` maps stream_key -> list of tombstone dicts.
        '''
        items_by_stream: Dict[str, List[dict]] = {}
        tombstones_by_stream: Dict[str, List[dict]] = {}

        for stream_key, items in await self.walk_streams():
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

    async def to_networkx(self):
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
        items_by_stream, tombstones_by_stream = await self._collect_all_items()

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

    async def to_graphviz(self):
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

            dot = await storage.to_graphviz()
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

        items_by_stream, tombstones_by_stream = await self._collect_all_items()

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

    Since all operations are in-memory and non-blocking, the async
    methods are simple coroutines that return immediately.  An
    ``asyncio.Lock`` is used to serialize concurrent access within the
    same event loop.
    '''

    def __init__(self):
        super().__init__()
        self._store: Dict[str, List[dict]] = {}
        self._lock = asyncio.Lock()

    async def append_to_stream(self, stream, item):
        async with self._lock:
            self._store.setdefault(stream, []).append(item)

    async def rename_or_alias_stream(self, stream, alias):
        async with self._lock:
            if alias == stream:
                return
            self._store[alias] = self._store.pop(stream)

    async def get_stream_data(self, stream):
        async with self._lock:
            if stream not in self._store:
                return None
            return list(self._store[stream])

    async def delete_stream(self, stream):
        async with self._lock:
            self._store.pop(stream, None)

    async def most_recent_item(self, stream):
        async with self._lock:
            items = self._store.get(stream)
            if not items:
                return None
            return items[-1]

    async def walk(self):
        async with self._lock:
            snapshot = {k: list(v) for k, v in self._store.items()}
        result = []
        for items in snapshot.values():
            result.extend(items)
        return result

    async def walk_streams(self):
        '''Return ``(stream_key, items_list)`` for every stream.'''
        async with self._lock:
            snapshot = {k: list(v) for k, v in self._store.items()}
        return list(snapshot.items())


class FSStorage(StreamStorage):
    '''Filesystem-backed async storage (one JSONL file per stream).

    Each stream is stored as a file where every line is a single
    JSON-serialized item.  Filenames are the SHA-256 of the stream
    key to avoid path-traversal and encoding issues.

    Blocking file I/O is offloaded to the default thread-pool executor
    via :meth:`asyncio.loop.run_in_executor`.

    Parameters
    ----------
    path : str
        Directory in which stream files are created.  Will be created
        (including parents) if it does not exist.
    executor : concurrent.futures.Executor, optional
        The executor to use for blocking I/O.  ``None`` (the default)
        uses the loop's default executor.

    Notes
    -----
    This backend is adequate for prototyping but has several
    performance limitations:

    - ``most_recent_item`` reads the entire file to return the last
      line.
    - ``rename_or_alias_stream`` is not atomic across crashes.
    - No write-ahead log or fsync guarantees.
    '''

    def __init__(self, path: str, executor: Optional[Executor] = None):
        super().__init__()
        self.path = path
        self._executor = executor
        os.makedirs(path, exist_ok=True)
        # Async lock to serialize operations within the event loop
        self._lock = asyncio.Lock()
        # Maintain a reverse mapping: filename_hash -> stream_key
        # so walk_streams can report meaningful keys
        self._key_map: Dict[str, str] = {}

    def _fn(self, stream: str) -> str:
        '''Map a stream name to a filesystem path.

        Uses SHA-256 of the stream name to produce a safe, fixed-length
        filename that avoids path-traversal and special-character
        issues.
        '''
        safe = hashlib.sha256(stream.encode('utf-8')).hexdigest()
        self._key_map[safe] = stream
        return os.path.join(self.path, safe)

    async def _run_in_executor(self, fn, *args):
        '''Run a blocking callable in the thread-pool executor.'''
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._executor, fn, *args)

    # -- sync helpers called inside the executor -------------------------

    @staticmethod
    def _sync_append(path: str, data: str):
        with open(path, 'a') as f:
            f.write(data + '\n')

    @staticmethod
    def _sync_rename(src: str, dst: str):
        os.rename(src, dst)

    @staticmethod
    def _sync_read(path: str) -> Optional[List[dict]]:
        if not os.path.exists(path):
            return None
        with open(path, 'r') as f:
            return [json_load(line) for line in f if line.strip()]

    @staticmethod
    def _sync_delete(path: str):
        if os.path.exists(path):
            os.remove(path)

    @staticmethod
    def _sync_listdir(directory: str) -> List[str]:
        return os.listdir(directory)

    @staticmethod
    def _sync_read_file(filepath: str) -> List[dict]:
        items = []
        if os.path.isfile(filepath):
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        items.append(json_load(line))
        return items

    # -- async interface -------------------------------------------------

    async def append_to_stream(self, stream, item):
        async with self._lock:
            path = self._fn(stream)
            data = json_dump(item)
            await self._run_in_executor(self._sync_append, path, data)

    async def rename_or_alias_stream(self, stream, alias):
        async with self._lock:
            src, dst = self._fn(stream), self._fn(alias)
            if src == dst:
                return
            await self._run_in_executor(self._sync_rename, src, dst)

    async def get_stream_data(self, stream):
        path = self._fn(stream)
        return await self._run_in_executor(self._sync_read, path)

    async def delete_stream(self, stream):
        path = self._fn(stream)
        await self._run_in_executor(self._sync_delete, path)

    async def most_recent_item(self, stream):
        data = await self.get_stream_data(stream)
        if not data:
            return None
        return data[-1]

    async def walk(self):
        filenames = await self._run_in_executor(self._sync_listdir, self.path)
        result = []
        for filename in filenames:
            filepath = os.path.join(self.path, filename)
            items = await self._run_in_executor(self._sync_read_file, filepath)
            result.extend(items)
        return result

    async def walk_streams(self):
        '''Return ``(stream_key, items_list)`` for every stream.'''
        filenames = await self._run_in_executor(self._sync_listdir, self.path)
        result = []
        for filename in filenames:
            filepath = os.path.join(self.path, filename)
            stream_key = self._key_map.get(filename, filename)
            items = await self._run_in_executor(self._sync_read_file, filepath)
            result.append((stream_key, items))
        return result

class KVSStorage(StreamStorage):
    '''Storage backend that delegates to an existing ``_KVS`` instance.

    Each stream is stored as a single KVS entry whose value is a JSON
    list of items.  Every append does a read-modify-write cycle.

    Parameters
    ----------
    kvs : _KVS
        An instantiated KVS backend (``InMemoryKVS``, ``PersistentRedisKVS``,
        ``EphemeralRedisKVS``, ``FilesystemKVS``, etc.).
    prefix : str, optional
        A key prefix applied to every stream key before storage.
        Defaults to ``"merkle:"``.
    '''

    def __init__(self, kvs: '_KVS', prefix: str = 'merkle:'):
        super().__init__()
        self._kvs = kvs
        self._prefix = prefix
        self._lock = asyncio.Lock()
        # Track keys ourselves because KVS.keys() may return
        # all keys in the backend (including non-merkle ones),
        # and some backends (Redis) decode keys differently.
        self._known_keys: set = set()

    def _key(self, stream: str) -> str:
        '''Prefix a stream name to produce the KVS key.'''
        return f'{self._prefix}{stream}'

    async def append_to_stream(self, stream: str, item: dict):
        async with self._lock:
            key = self._key(stream)
            data = await self._kvs[key]
            if data is None:
                data = []
            if not isinstance(data, list):
                data = []
            data.append(item)
            await self._kvs.set(key, data)
            self._known_keys.add(key)

    async def rename_or_alias_stream(self, stream: str, alias: str):
        async with self._lock:
            if alias == stream:
                return
            src_key = self._key(stream)
            dst_key = self._key(alias)
            data = await self._kvs[src_key]
            if data is None:
                return
            # Write to new key first
            await self._kvs.set(dst_key, data)
            self._known_keys.add(dst_key)
            # Remove old key
            await self._remove_key(src_key)
            self._known_keys.discard(src_key)

    async def _remove_key(self, key: str):
        '''Remove a key from the underlying KVS, trying available methods.'''
        if hasattr(self._kvs, 'remove'):
            await self._kvs.remove(key)
        elif hasattr(self._kvs, '__delitem__'):
            await self._kvs.__delitem__(key)
        else:
            # Last resort: overwrite with None
            await self._kvs.set(key, None)

    async def get_stream_data(self, stream: str) -> Optional[List[dict]]:
        key = self._key(stream)
        data = await self._kvs[key]
        if data is None:
            return None
        if not isinstance(data, list):
            return None
        return list(data)

    async def delete_stream(self, stream: str):
        key = self._key(stream)
        await self._remove_key(key)
        self._known_keys.discard(key)

    async def most_recent_item(self, stream: str) -> Optional[dict]:
        key = self._key(stream)
        data = await self._kvs[key]
        if not data or not isinstance(data, list):
            return None
        return data[-1]

    async def walk(self) -> List[dict]:
        result: List[dict] = []
        for key in list(self._known_keys):
            data = await self._kvs[key]
            if isinstance(data, list):
                result.extend(data)
        return result

    async def walk_streams(self) -> List[Tuple[str, List[dict]]]:
        result: List[Tuple[str, List[dict]]] = []
        prefix_len = len(self._prefix)
        for key in list(self._known_keys):
            data = await self._kvs[key]
            if isinstance(data, list):
                stream_name = key[prefix_len:] if key.startswith(self._prefix) else key
                result.append((stream_name, data))
        return result

    async def debug_dump(self):
        '''Print diagnostic info about what is actually stored.

        Useful for debugging Redis integration issues.
        '''
        print(f'[KVSStorage debug] prefix={self._prefix!r}')
        print(f'[KVSStorage debug] tracked keys ({len(self._known_keys)}):')
        for key in sorted(self._known_keys):
            data = await self._kvs[key]
            item_count = len(data) if isinstance(data, list) else '(not a list)'
            data_type = type(data).__name__
            print(f'  {key!r} -> type={data_type}, items={item_count}')

        # Also check what the KVS backend itself reports
        try:
            all_backend_keys = await self._kvs.keys()
            merkle_keys = [k for k in all_backend_keys if k.startswith(self._prefix)]
            print(f'[KVSStorage debug] backend keys with our prefix ({len(merkle_keys)}):')
            for key in sorted(merkle_keys):
                data = await self._kvs[key]
                item_count = len(data) if isinstance(data, list) else '(not a list)'
                print(f'  {key!r} -> items={item_count}')
        except Exception as e:
            print(f'[KVSStorage debug] could not enumerate backend keys: {e}')


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
    'kvs': KVSStorage,
}
'''
Registry of available storage backends, keyed by short name.

Used by configuration-driven code to instantiate a backend from a
string identifier.
'''


# ---------------------------------------------------------------------------
# Smoke tests
# ---------------------------------------------------------------------------
async def test_case_inmemory():
    '''Original smoke test using InMemoryStorage.'''
    storage = InMemoryStorage()
    merkle = Merkle(storage, CATEGORIES)

    session = {
        'teacher': ['Mr. A'],
        'student': ['John'],
    }

    await merkle.start(session)
    await merkle.event_to_session({'type': 'event', 'payload': 'A'}, session, label='A')
    await merkle.event_to_session({'type': 'event', 'payload': 'B'}, session, label='B')
    await merkle.event_to_session({'type': 'event', 'payload': 'C'}, session, label='C')
    final_hash = await merkle.close_session(session)

    assert await merkle.verify_chain(final_hash)
    print(f'[inmemory] Chain verified: {final_hash}')

    for parent_key in [json_dump({'student': 'John'}), json_dump({'teacher': 'Mr. A'})]:
        data = await storage.get_stream_data(parent_key)
        if data:
            print(f'[inmemory] Parent stream {parent_key[:40]}... has {len(data)} item(s)')

    tombstone = await merkle.delete_stream_with_tombstone(final_hash, reason='GDPR request')
    print(f'[inmemory] Tombstone: {tombstone["tombstone_hash"]}')
    assert await storage.get_stream_data(final_hash) is None
    print('[inmemory] All checks passed.')


async def test_case_kvs_basic():
    '''Basic start -> events -> close -> verify cycle on KVSStorage.'''
    from learning_observer.kvs import InMemoryKVS as KVSInMemory

    kvs_backend = KVSInMemory()
    storage = KVSStorage(kvs_backend)
    merkle = Merkle(storage, CATEGORIES)

    session = {
        'teacher': ['Ms. B'],
        'student': ['Alice'],
    }

    await merkle.start(session)
    await merkle.event_to_session({'type': 'event', 'payload': 'X'}, session, label='X')
    await merkle.event_to_session({'type': 'event', 'payload': 'Y'}, session, label='Y')
    final_hash = await merkle.close_session(session)

    assert await merkle.verify_chain(final_hash)
    print(f'[kvs-basic] Chain verified: {final_hash}')

    # Confirm the stream was renamed (old session key should be gone)
    old_key = session_key(session)
    assert await storage.get_stream_data(old_key) is None, \
        'Session key should be removed after close'

    # Confirm the stream is retrievable by final hash
    data = await storage.get_stream_data(final_hash)
    assert data is not None and len(data) == 4, \
        f'Expected 4 items (start + 2 events + close), got {len(data) if data else 0}'
    print(f'[kvs-basic] Stream has {len(data)} items as expected.')

    # Confirm parent streams were propagated
    for parent_key in [json_dump({'student': 'Alice'}), json_dump({'teacher': 'Ms. B'})]:
        parent_data = await storage.get_stream_data(parent_key)
        assert parent_data is not None and len(parent_data) >= 1, \
            f'Parent stream {parent_key[:30]}... should have at least 1 item'
        print(f'[kvs-basic] Parent stream {parent_key[:30]}... has {len(parent_data)} item(s)')

    print('[kvs-basic] All checks passed.')


async def test_case_kvs_tombstone():
    '''Tombstone deletion on KVSStorage.'''
    from learning_observer.kvs import InMemoryKVS as KVSInMemory

    kvs_backend = KVSInMemory()
    storage = KVSStorage(kvs_backend)
    merkle = Merkle(storage, CATEGORIES)

    session = {'student': ['Bob']}

    await merkle.start(session)
    await merkle.event_to_session({'type': 'event', 'payload': 'secret'}, session, label='secret')
    final_hash = await merkle.close_session(session)

    assert await merkle.verify_chain(final_hash)
    print(f'[kvs-tombstone] Chain verified before deletion: {final_hash}')

    # Delete with tombstone
    tombstone = await merkle.delete_stream_with_tombstone(final_hash, reason='GDPR Art. 17')
    print(f'[kvs-tombstone] Tombstone hash: {tombstone["tombstone_hash"]}')

    # Original stream should be gone
    assert await storage.get_stream_data(final_hash) is None, \
        'Deleted stream should return None'

    # Tombstone should be stored
    tombstone_key = f'__tombstone__{final_hash}'
    tombstone_data = await storage.get_stream_data(tombstone_key)
    assert tombstone_data is not None and len(tombstone_data) == 1, \
        'Tombstone stream should have exactly 1 record'
    assert tombstone_data[0]['type'] == 'tombstone'
    assert tombstone_data[0]['reason'] == 'GDPR Art. 17'
    assert tombstone_data[0]['item_count'] == 3  # start + event + close
    print(f'[kvs-tombstone] Tombstone record verified: {tombstone_data[0]["item_count"]} items recorded.')

    # Attempting to delete again should raise
    try:
        await merkle.delete_stream_with_tombstone(final_hash, reason='duplicate')
        assert False, 'Should have raised ValueError'
    except ValueError:
        print('[kvs-tombstone] Double-delete correctly rejected.')

    print('[kvs-tombstone] All checks passed.')


async def test_case_kvs_break_session():
    '''Session break (segmentation) on KVSStorage.'''
    from learning_observer.kvs import InMemoryKVS as KVSInMemory

    kvs_backend = KVSInMemory()
    storage = KVSStorage(kvs_backend)
    merkle = Merkle(storage, CATEGORIES)

    session = {'student': ['Carol'], 'tool': ['notebook']}

    await merkle.start(session)
    await merkle.event_to_session({'type': 'event', 'payload': 'part1'}, session, label='part1')

    # Break the session — closes segment 1, starts segment 2
    segment1_hash = await merkle.break_session(session)
    print(f'[kvs-break] Segment 1 hash: {segment1_hash}')

    # Verify segment 1
    assert await merkle.verify_chain(segment1_hash)
    print('[kvs-break] Segment 1 verified.')

    # Continue in segment 2
    await merkle.event_to_session({'type': 'event', 'payload': 'part2'}, session, label='part2')
    final_hash = await merkle.close_session(session)
    print(f'[kvs-break] Segment 2 (final) hash: {final_hash}')

    # Verify segment 2
    assert await merkle.verify_chain(final_hash)
    print('[kvs-break] Segment 2 verified.')

    # Segment 2 should reference segment 1 via the continuation link
    seg2_data = await storage.get_stream_data(final_hash)
    assert seg2_data is not None
    first_item = seg2_data[0]
    assert first_item['event']['type'] == 'continue'
    assert first_item['event']['continues'] == segment1_hash
    assert segment1_hash in first_item['children'], \
        'Continuation item should include segment 1 hash in children'
    print('[kvs-break] Cross-segment linkage confirmed.')

    print('[kvs-break] All checks passed.')


async def test_case_kvs_walk():
    '''walk() and walk_streams() on KVSStorage.'''
    from learning_observer.kvs import InMemoryKVS as KVSInMemory

    kvs_backend = KVSInMemory()
    storage = KVSStorage(kvs_backend)
    merkle = Merkle(storage, CATEGORIES)

    # Create two separate sessions
    session_a = {'student': ['Dave']}
    session_b = {'student': ['Eve']}

    await merkle.start(session_a)
    await merkle.event_to_session({'type': 'event', 'payload': 'a1'}, session_a)
    hash_a = await merkle.close_session(session_a)

    await merkle.start(session_b)
    await merkle.event_to_session({'type': 'event', 'payload': 'b1'}, session_b)
    await merkle.event_to_session({'type': 'event', 'payload': 'b2'}, session_b)
    hash_b = await merkle.close_session(session_b)

    # walk() should return all items across all streams
    all_items = await storage.walk()
    print(f'[kvs-walk] Total items across all streams: {len(all_items)}')
    assert len(all_items) > 0

    # walk_streams() should return identifiable stream groups
    streams = await storage.walk_streams()
    stream_keys = [s[0] for s in streams]
    print(f'[kvs-walk] Streams found: {len(streams)}')
    for key, items in streams:
        display = key if len(key) <= 40 else key[:37] + '...'
        print(f'  [{display}] -> {len(items)} item(s)')

    # The closed session streams should appear under their final hashes
    assert any(k == hash_a for k in stream_keys), \
        f'Stream {hash_a[:16]}... not found in walk_streams'
    assert any(k == hash_b for k in stream_keys), \
        f'Stream {hash_b[:16]}... not found in walk_streams'

    print('[kvs-walk] All checks passed.')


async def test_case_kvs_prefix_isolation():
    '''Two KVSStorage instances with different prefixes sharing the same KVS backend.'''
    from learning_observer.kvs import InMemoryKVS as KVSInMemory

    kvs_backend = KVSInMemory()
    storage_a = KVSStorage(kvs_backend, prefix='merkle_a:')
    storage_b = KVSStorage(kvs_backend, prefix='merkle_b:')
    merkle_a = Merkle(storage_a, CATEGORIES)
    merkle_b = Merkle(storage_b, CATEGORIES)

    session = {'student': ['Frank']}

    # Write to storage_a
    await merkle_a.start(session)
    await merkle_a.event_to_session({'type': 'event', 'payload': 'from_a'}, session)
    hash_a = await merkle_a.close_session(session)

    # Write to storage_b with the same session descriptor
    await merkle_b.start(session)
    await merkle_b.event_to_session({'type': 'event', 'payload': 'from_b'}, session)
    hash_b = await merkle_b.close_session(session)

    # Both should verify independently
    assert await merkle_a.verify_chain(hash_a)
    assert await merkle_b.verify_chain(hash_b)
    print(f'[kvs-prefix] Chain A verified: {hash_a[:16]}...')
    print(f'[kvs-prefix] Chain B verified: {hash_b[:16]}...')

    # walk_streams should only see items from their own prefix
    streams_a = await storage_a.walk_streams()
    streams_b = await storage_b.walk_streams()

    items_a = await storage_a.walk()
    items_b = await storage_b.walk()

    # They should not overlap (different payloads, different timestamps → different hashes)
    hashes_a = {item['hash'] for item in items_a if 'hash' in item}
    hashes_b = {item['hash'] for item in items_b if 'hash' in item}
    overlap = hashes_a & hashes_b
    # Parent streams for the same student may not overlap because timestamps differ,
    # but the closed-session hashes definitely shouldn't match
    assert hash_a not in hashes_b, 'Hash A leaked into storage B'
    assert hash_b not in hashes_a, 'Hash B leaked into storage A'
    print(f'[kvs-prefix] Storage A: {len(streams_a)} streams, {len(items_a)} items')
    print(f'[kvs-prefix] Storage B: {len(streams_b)} streams, {len(items_b)} items')

    print('[kvs-prefix] All checks passed.')


async def test_case_kvs_verify_tamper_detection():
    '''Verify that tampering with a stored item is detected.'''
    from learning_observer.kvs import InMemoryKVS as KVSInMemory

    kvs_backend = KVSInMemory()
    storage = KVSStorage(kvs_backend)
    merkle = Merkle(storage, CATEGORIES)

    session = {'student': ['Grace']}

    await merkle.start(session)
    await merkle.event_to_session({'type': 'event', 'payload': 'original'}, session)
    final_hash = await merkle.close_session(session)

    # Verify clean chain
    assert await merkle.verify_chain(final_hash)
    print('[kvs-tamper] Clean chain verified.')

    # Now tamper: modify the event payload of the middle item
    kvs_key = f'{storage._prefix}{final_hash}'
    data = await kvs_backend[kvs_key]
    assert data is not None and len(data) == 3  # start + event + close

    # Corrupt the second item's event
    data[1]['event']['payload'] = 'TAMPERED'
    await kvs_backend.set(kvs_key, data)

    # Verification should now fail
    try:
        await merkle.verify_chain(final_hash)
        assert False, 'Tampered chain should have failed verification'
    except ValueError as e:
        print(f'[kvs-tamper] Tamper correctly detected: {e}')

    print('[kvs-tamper] All checks passed.')


async def test_case_kvs_visualization():
    '''Visualization export on KVSStorage (only runs if networkx/pydot available).'''
    if not HAS_VIZ:
        print('[kvs-viz] Skipping (networkx/pydot not installed)')
        return

    from learning_observer.kvs import InMemoryKVS as KVSInMemory

    kvs_backend = KVSInMemory()
    storage = KVSStorage(kvs_backend)
    merkle = Merkle(storage, CATEGORIES)

    session = {'student': ['Heidi'], 'tool': ['canvas']}

    await merkle.start(session)
    await merkle.event_to_session({'type': 'event', 'payload': 'draw'}, session, label='draw')
    await merkle.event_to_session({'type': 'event', 'payload': 'erase'}, session, label='erase')
    final_hash = await merkle.close_session(session)

    # Delete the session to get a tombstone in the graph
    tombstone = await merkle.delete_stream_with_tombstone(final_hash, reason='test cleanup')

    # NetworkX export
    G = await storage.to_networkx()
    tombstone_nodes = [n for n, d in G.nodes(data=True) if d.get('tombstone')]
    deleted_nodes = [n for n, d in G.nodes(data=True) if d.get('classification') == 'deleted']
    edge_types = {}
    for u, v, d in G.edges(data=True):
        et = d.get('edge_type', 'unknown')
        edge_types[et] = edge_types.get(et, 0) + 1

    print(f'[kvs-viz] NetworkX: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges')
    print(f'[kvs-viz] Tombstone nodes: {len(tombstone_nodes)}')
    print(f'[kvs-viz] Deleted placeholders: {len(deleted_nodes)}')
    print(f'[kvs-viz] Edge types: {edge_types}')

    assert len(tombstone_nodes) >= 1, 'Should have at least one tombstone node'
    assert len(deleted_nodes) >= 1, 'Should have at least one deleted placeholder'

    # Graphviz export
    dot = await storage.to_graphviz()
    print(f'[kvs-viz] Graphviz: {len(dot.get_node_list())} nodes, {len(dot.get_edge_list())} edges')

    print('[kvs-viz] All checks passed.')


async def test_case_kvs_redis():
    '''Full lifecycle on KVSStorage backed by a real Redis instance.

    This test bootstraps the Learning Observer settings system via
    ``learning_observer.offline.init()`` so that the Redis connection
    can resolve its host/port/password from the standard config.  If
    the settings system or Redis is unavailable, the test is skipped
    gracefully.
    '''
    # --- bootstrap the settings system --------------------------------
    try:
        import learning_observer.offline
        learning_observer.offline.init()
    except Exception as e:
        raise e
        print(f'[kvs-redis] Skipping — could not initialize settings: {e}')
        return

    # --- get the KVS that init() wired up -----------------------------
    try:
        from learning_observer.kvs import KVS
        kvs_backend = KVS()
        await kvs_backend.set('__merkle_redis_ping__', 'pong')
        pong = await kvs_backend['__merkle_redis_ping__']
        assert pong == 'pong', f'Redis ping failed: got {pong!r}'
        print('[kvs-redis] Redis connection confirmed.')
    except Exception as e:
        print(f'[kvs-redis] Skipping — could not connect to Redis: {e}')
        return

    import time
    prefix = f'merkle_test_{int(time.time())}:'
    storage = KVSStorage(kvs_backend, prefix=prefix)
    merkle = Merkle(storage, CATEGORIES)

    session = {
        'teacher': ['Dr. Redis'],
        'student': ['Ivy'],
        'tool': ['terminal'],
    }

    # --- lifecycle ----------------------------------------------------
    await merkle.start(session, metadata={'test': True})
    await merkle.event_to_session(
        {'type': 'event', 'payload': 'command_1'}, session, label='cmd1',
    )
    await merkle.event_to_session(
        {'type': 'event', 'payload': 'command_2'}, session, label='cmd2',
    )
    final_hash = await merkle.close_session(session)
    print(f'[kvs-redis] Session closed: {final_hash}')

    # --- debug: show what's actually in Redis -------------------------
    await storage.debug_dump()

    # --- verify -------------------------------------------------------
    assert await merkle.verify_chain(final_hash)
    print('[kvs-redis] Chain verified.')

    data = await storage.get_stream_data(final_hash)
    assert data is not None, 'Stream data is None — rename may have failed'
    assert len(data) == 4, f'Expected 4 items (start + 2 events + close), got {len(data)}'
    print(f'[kvs-redis] Stream has {len(data)} items.')

    # --- parents ------------------------------------------------------
    for parent_key in [json_dump({'student': 'Ivy'}), json_dump({'teacher': 'Dr. Redis'}),
                       json_dump({'tool': 'terminal'})]:
        parent_data = await storage.get_stream_data(parent_key)
        assert parent_data is not None and len(parent_data) >= 1
        print(f'[kvs-redis] Parent {parent_key[:30]}... OK ({len(parent_data)} items)')

    # --- tombstone ----------------------------------------------------
    tombstone = await merkle.delete_stream_with_tombstone(final_hash, reason='GDPR test')
    assert await storage.get_stream_data(final_hash) is None
    tombstone_data = await storage.get_stream_data(f'__tombstone__{final_hash}')
    assert tombstone_data is not None and len(tombstone_data) == 1
    assert tombstone_data[0]['item_count'] == 4
    print(f'[kvs-redis] Tombstone verified.')

    # --- final debug dump ---------------------------------------------
    await storage.debug_dump()

    # --- cleanup ------------------------------------------------------
    try:
        all_keys = await kvs_backend.keys()
        test_keys = [k for k in all_keys if k.startswith(prefix)]
        if hasattr(kvs_backend, 'remove'):
            for k in test_keys:
                await kvs_backend.remove(k)
        print(f'[kvs-redis] Cleaned up {len(test_keys)} test keys.')
    except Exception as e:
        print(f'[kvs-redis] Cleanup warning: {e}')

    print('[kvs-redis] All checks passed.')


async def test_all():
    '''Run all test cases.'''
    tests = [
        ('InMemoryStorage', test_case_inmemory),
        ('KVS Basic', test_case_kvs_basic),
        ('KVS Tombstone', test_case_kvs_tombstone),
        ('KVS Break Session', test_case_kvs_break_session),
        ('KVS Walk', test_case_kvs_walk),
        ('KVS Prefix Isolation', test_case_kvs_prefix_isolation),
        ('KVS Tamper Detection', test_case_kvs_verify_tamper_detection),
        ('KVS Visualization', test_case_kvs_visualization),
        ('KVS Redis Integration', test_case_kvs_redis),
    ]

    passed = 0
    failed = 0
    skipped = 0
    for name, test_fn in tests:
        print(f'\n{"="*60}')
        print(f'Running: {name}')
        print(f'{"="*60}')
        try:
            await test_fn()
            passed += 1
        except Exception as e:
            failed += 1
            print(f'FAILED: {name}')
            import traceback
            traceback.print_exc()

    print(f'\n{"="*60}')
    print(f'Results: {passed} passed, {failed} failed, {passed + failed} total')
    print(f'{"="*60}')

    if failed > 0:
        raise SystemExit(1)


if __name__ == '__main__':
    asyncio.run(test_all())
