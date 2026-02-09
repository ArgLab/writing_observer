Merkle DAG Log Storage System

A cryptographically verifiable, append-only log storage system for education event data. Every event is chained into a Merkle DAG so that tampering is detectable, data-subject requests are tractable, and analytical provenance is auditable.

---

## Table of Contents

1. [Motivation & Design Goals](#motivation--design-goals)
2. [Core Concepts](#core-concepts)
   - [Events, Sessions, and Streams](#events-sessions-and-streams)
   - [The Merkle Chain](#the-merkle-chain)
   - [Parent Streams and Categories](#parent-streams-and-categories)
3. [Quickstart](#quickstart)
4. [Streaming Pipeline Integration](#streaming-pipeline-integration)
5. [API Reference](#api-reference)
   - [Merkle](#merkle)
   - [AsyncMerkle](#asyncmerkle)
   - [Storage Backends](#storage-backends)
6. [Verification & Audit](#verification--audit)
   - [What Exactly Is Verified?](#what-exactly-is-verified)
   - [Running Verification](#running-verification)
   - [Why This Is Safe](#why-this-is-safe)
   - [Publishing Root Hashes](#publishing-root-hashes)
7. [Deletion & Tombstones](#deletion--tombstones)
8. [Visualization](#visualization)
   - [Graphviz (pydot)](#graphviz-pydot)
   - [NetworkX](#networkx)
   - [Reading the Graph](#reading-the-graph)
9. [Storage Backends In Depth](#storage-backends-in-depth)
10. [Configuration](#configuration)
11. [Security Model & Threat Analysis](#security-model--threat-analysis)
12. [Prototype Limitations & Production Roadmap](#prototype-limitations--production-roadmap)

---

## Motivation & Design Goals

We need a log storage layer that satisfies five sometimes-competing requirements:

| # | Goal | How the Merkle DAG helps |
|---|------|--------------------------|
| 1 | **Scale** to millions of users × millions of events | The only write primitive is "append an item keyed by its hash." This maps to Kafka topics, S3 objects, or any distributed append-only store. |
| 2 | **Data portability** — give a user *all* their data on request | Parent streams index every session a user participated in. Export = walk the parent stream and collect referenced session streams. |
| 3 | **Erasure** — remove or correct data on request | `delete_stream_with_tombstone` removes content but leaves a hash skeleton. Parent references remain structurally valid. |
| 4 | **Archival audit** — prove retained data is unmodified | The final hash of every stream is a commitment to every item. Anyone who recorded that hash can re-derive it and detect changes. |
| 5 | **Computation provenance** (future) | Computation logs will chain into the same DAG, producing a lab-notebook-grade record of every analytical step. |

---

## Core Concepts

### Events, Sessions, and Streams

An **event** is an arbitrary JSON-serializable dict — a click, a keystroke, a page view, a server-side derivation, anything.

A **session** is a dict of category → value(s) that describes the context in which events occur:

```python
session = {
    "student": ["Alice"],
    "tool": ["editor"],
}
```

While a session is open, events are appended to a **stream** keyed by the canonical JSON serialization of the session dict. When the session is closed, the stream is renamed to the SHA-256 hash of its final item — making the stream **content-addressed**.

### The Merkle Chain

Each item in a stream looks like this:

```
┌───────────────────────────────────────────────┐
│  hash:       SHA-256(sorted(children) ‖ ts)   │
│  children:   [event_hash, prev_hash, ...]     │
│  timestamp:  2025-01-15T08:30:00.123456       │
│  event:      { ... original payload ... }     │
│  label:      (optional, for visualization)    │
└───────────────────────────────────────────────┘
```

The `children` list always includes:

1. **The hash of the event payload** — ties the item to its content.
2. **The hash of the previous item** (if any) — ties the item to the entire preceding chain.
3. **Any extra children** passed by the caller — cross-references to other streams (e.g., continuation links, child-session references).

Because `hash` is computed *over* the children, changing any ancestor forces every descendant hash to change, which is immediately detectable.

### Parent Streams and Categories

The system recognizes a set of **categories** (e.g., `student`, `teacher`, `tool`). When a session is closed, the system automatically appends a `child_session_finished` event to the long-lived parent stream for each category value in the session.

```
Session: {"student": ["Alice"], "tool": ["editor"]}
    ↓ close_session
Parent stream {"student": "Alice"}  ← child_session_finished(hash=abc...)
Parent stream {"tool": "editor"}    ← child_session_finished(hash=abc...)
```

This creates a **two-level index**: from a category value you can enumerate every session that involved it, and from each session you can retrieve its complete event stream.

---

## Quickstart

### Installation

The core module has no dependencies beyond the Python standard library. For visualization, install optional packages:

```bash
pip install networkx pydot
```

### Minimal Example

```python
from merkle_store import InMemoryStorage, Merkle, CATEGORIES

storage = InMemoryStorage()
merkle = Merkle(storage, CATEGORIES)

session = {"student": ["Alice"], "tool": ["editor"]}

# 1. Open
merkle.start(session, metadata={"client_version": "1.2.0"})

# 2. Append events
merkle.event_to_session({"type": "keystroke", "key": "a"}, session)
merkle.event_to_session({"type": "keystroke", "key": "b"}, session)
merkle.event_to_session({"type": "submit"},                session)

# 3. Close — returns the final content hash
final_hash = merkle.close_session(session)
print(f"Session hash: {final_hash}")

# 4. Verify
assert merkle.verify_chain(final_hash)
print("Chain integrity verified ✓")
```

### Using Filesystem Storage

```python
from merkle_store import FSStorage, Merkle, CATEGORIES

storage = FSStorage(path="/var/data/merkle_streams")
merkle = Merkle(storage, CATEGORIES)
# ... same API as above ...
```

Each stream becomes a JSONL file under `/var/data/merkle_streams/`. The filename is the SHA-256 of the stream key.

### Streaming Events via `scripts/stream_writing.py`

The repository includes `scripts/stream_writing.py`, which connects to an event source and pipes events through the Merkle pipeline:

```bash
python scripts/stream_writing.py \\
    --store fs \\
    --store-path /var/data/merkle_streams \\
    --student alice \\
    --tool editor
```

This opens a session, streams every incoming event through `event_to_session`, and closes the session when the source terminates (or on `SIGINT`).

---

## Streaming Pipeline Integration

In production, the Merkle logger runs inside an async generator pipeline that sits between the event source and downstream consumers (reducers, dashboards, etc.):

```python
from merkle_store import (
    InMemoryStorage, FSStorage, Merkle, AsyncMerkle,
    CATEGORIES, STORES,
)

# --- bootstrap from config ---
storage_cls = STORES[config["store"]]       # "inmemory" or "fs"
storage = storage_cls(**config.get("params", {}))
merkle = Merkle(storage, CATEGORIES)
async_merkle = AsyncMerkle(merkle)

session = {"student": [request.student], "tool": [request.tool]}

# --- async generator that logs and forwards events ---
async def decode_and_log(events):
    await async_merkle.start(session, metadata=metadata)
    async for msg in events:
        event = msg if isinstance(msg, dict) else json.loads(msg.data)
        await async_merkle.event_to_session(event, session)
        yield event                # forward downstream
    await async_merkle.close_session(session)
```

The pipeline is transparent: downstream consumers receive the same events they would without the Merkle layer. The only side effect is that every event is also appended to the Merkle chain.

---

## API Reference

### `Merkle`

| Method | Description |
|--------|-------------|
| `start(session, metadata=None, continuation_hash=None)` | Open a new session stream. If `continuation_hash` is provided, records it as a `continue` event that links to a prior segment. |
| `event_to_session(event, session, children=None, label=None)` | Append an event to the running stream. Returns the persisted item dict. |
| `close_session(session, logical_break=False)` | Append a `close` event, content-address the stream, propagate to parents. Returns the final hash. |
| `break_session(session)` | Close the current segment and immediately start a continuation. Returns the closed segment's hash. |
| `verify_chain(stream_key)` | Walk the stream and verify all three invariants (event inclusion, chain linkage, hash correctness). Returns `True` or raises `ValueError`. |
| `delete_stream_with_tombstone(stream_key, reason)` | Remove event data; leave a tombstone with hash skeleton and reason. Returns the tombstone dict. |

### `AsyncMerkle`

Wraps a `Merkle` instance and exposes `async` versions of `start`, `event_to_session`, `close_session`, and `verify_chain`. All calls are dispatched to the default executor via `loop.run_in_executor`.

### Storage Backends

| Backend | Key | Description |
|---------|-----|-------------|
| `InMemoryStorage` | `inmemory` | Dict-of-lists. Fast, ephemeral. Good for tests. |
| `FSStorage(path)` | `fs` | One JSONL file per stream under `path`. Persistent across restarts. |

Both implement the `StreamStorage` interface and are registered in the `STORES` dict.

---

## Verification & Audit

### What Exactly Is Verified?

`verify_chain` checks three invariants for every item in a stream:

```
For item[i]:
  1. SHA-256(canonical_json(item[i].event))  ∈  item[i].children
  2. item[i-1].hash                          ∈  item[i].children   (if i > 0)
  3. item[i].hash == SHA-256(sorted(item[i].children) ‖ item[i].timestamp)
```

Together these guarantee:

| Property | Ensured by |
|----------|------------|
| **Content integrity** — no event payload was modified | Invariant 1 |
| **Completeness** — no item was removed or reordered | Invariant 2 |
| **Hash correctness** — the item's self-reported hash is honest | Invariant 3 |
| **Tamper evidence** — any change to any item propagates to the final hash | Invariants 1 + 2 + 3 together |

### Running Verification

```python
# Synchronous
try:
    merkle.verify_chain(final_hash)
    print("Integrity OK")
except ValueError as e:
    print(f"INTEGRITY VIOLATION: {e}")

# Async
assert await async_merkle.verify_chain(final_hash)
```

### Why This Is Safe

The security argument rests on **collision resistance** of SHA-256.

1. **You cannot forge a stream with a different final hash.** The final hash is a commitment to every preceding item. To produce a stream with different content but the same final hash, an attacker must find a SHA-256 collision — computationally infeasible.

2. **You cannot insert, remove, or reorder items.** Each item's hash includes the previous item's hash. Changing any item forces all subsequent hashes to change, which changes the final hash. A verifier who recorded the original final hash will detect the discrepancy.

3. **You cannot modify an event payload.** Each item's hash includes the hash of its event. Modifying the event changes its hash, which changes the item's children list, which changes the item's hash, which propagates forward.

4. **You cannot replay old events at a new time.** The timestamp is an input to the item hash. Same content + different timestamp = different hash.

5. **Cross-stream references are tamper-evident.** When a session is closed, its final hash is recorded as a child in parent streams. Modifying the session stream changes its final hash, which invalidates the parent's child reference.

### Publishing Root Hashes

For third-party auditability, the system is designed to periodically publish **root hashes** — e.g., a daily digest of all parent-stream tip hashes. Once published (to a transparency log, a blockchain, a newspaper, etc.), any party can request the underlying data and verify it against the published root. The Merkle structure means:

- Verification is efficient: you only need the chain of hashes from the item in question up to the published root.
- Publication is compact: a single 256-bit hash covers an arbitrary volume of data.

> **Note:** Root hash publication is not yet implemented in the prototype. The per-stream `verify_chain` provides the building block.

---

## Deletion & Tombstones

### Motivation

Data-subject erasure requests (GDPR Article 17, CCPA, FERPA, etc.) require removing personal data. Naïvely deleting a stream would break the Merkle DAG — parent streams would reference a hash that no longer resolves.

### How Tombstones Work

```python
tombstone = merkle.delete_stream_with_tombstone(
    stream_key=final_hash,
    reason="GDPR Article 17 erasure request from guardian",
)
```

This:

1. Reads the stream and records the **ordered list of per-item hashes** and the **final hash**.
2. Deletes the stream data (all event payloads are gone).
3. Writes a **tombstone** to `__tombstone__<stream_key>` containing:
   - `deleted_stream` — the stream key.
   - `final_hash` — the hash that parent streams reference.
   - `item_hashes` — the ordered list of all item hashes (no payloads).
   - `item_count` — the number of deleted items.
   - `reason` — why the data was deleted.
   - `timestamp` — when the deletion occurred.
   - `tombstone_hash` — SHA-256 of the above, for the tombstone's own integrity.

### What Remains After Deletion

| Retained | Removed |
|----------|---------|
| Tombstone record | All event payloads |
| Per-item hashes (ordered) | All event metadata within items |
| Final stream hash | Timestamps of individual items |
| Deletion reason & timestamp | Session descriptor within events |
| Parent-stream references | Labels |

An auditor can confirm:
- *That* data existed (the tombstone is present).
- *How much* data existed (`item_count`).
- *When* it was deleted and *why*.
- *That the parent reference is consistent* (parent's `child_hash` matches tombstone's `final_hash`).

An auditor **cannot**:
- Recover the deleted event content.
- Determine what the events contained.

---

## Visualization

Visual inspection of the DAG is invaluable for debugging and for explaining the system to stakeholders. Two export formats are supported.

### Prerequisites

```bash
pip install networkx pydot
# Graphviz must also be installed at the system level:
# macOS:  brew install graphviz
# Ubuntu: sudo apt-get install graphviz
```

### Graphviz (pydot)

```python
dot = storage.to_graphviz()

# Render to file
dot.write_png("merkle_dag.png")
dot.write_svg("merkle_dag.svg")
dot.write_pdf("merkle_dag.pdf")

# Get raw DOT source
print(dot.to_string())
```

### NetworkX

```python
import matplotlib.pyplot as plt

G = storage.to_networkx()

labels = {n: d.get("label", n[:8]) for n, d in G.nodes(data=True)}
pos = networkx.spring_layout(G)
networkx.draw(G, pos, labels=labels, with_labels=True,
              node_size=1500, font_size=8, arrows=True)
plt.savefig("merkle_dag_nx.png", dpi=150)
plt.show()
```

### Reading the Graph

The exported graph has the following structure:

```
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  start   │───▶│ event A  │───▶│ event B  │───▶ ...
    └──────────┘    └──────────┘    └──────────┘
         │                               │
         ▼                               ▼
    (event hash)                    (event hash)
```

- **Rectangles** are items (nodes). The label shows either the explicit label, a `category:value` summary, or the first 8 hex chars of the hash.
- **Arrows** point from an item to each of its children (the hashes it depends on). This includes:
  - The event-content hash (a "leaf" node with no outgoing edges of its own, unless the hash happens to collide with another item — which is astronomically unlikely).
  - The previous item in the chain.
  - Any cross-stream references (continuation links, child-session links).

**Parent streams** appear as separate chains. When a session is closed, the parent stream gains a node whose children include the closed session's final hash — visually, an arrow crosses from the parent chain into the session chain.

**Tombstones** appear as isolated nodes (the original stream's nodes are gone). This makes deleted data visually obvious.

---

## Storage Backends In Depth

### InMemoryStorage

- **Structure:** `dict[str, list[dict]]`
- **Thread safety:** single `threading.Lock`
- **Use case:** tests, demos, single-request pipelines
- **Persistence:** none — data lost on process exit

### FSStorage

- **Structure:** one JSONL file per stream under a configurable directory
- **Filename mapping:** `SHA-256(stream_key)` → avoids path traversal and special characters
- **Thread safety:** single `threading.Lock` (coarse — sufficient for prototype)
- **Use case:** persistent prototyping, small-scale deployments
- **Persistence:** survives process restarts; no crash-safety guarantees (no fsync)

### Implementing a Custom Backend

Subclass `StreamStorage` and implement six methods:

```python
class KafkaStorage(StreamStorage):
    def _append_to_stream(self, stream: str, item: dict):
        ...
    def _rename_or_alias_stream(self, stream: str, alias: str):
        ...
    def _get_stream_data(self, stream: str) -> Optional[List[dict]]:
        ...
    def _delete_stream(self, stream: str):
        ...
    def _most_recent_item(self, stream: str) -> Optional[dict]:
        ...
    def _walk(self) -> Iterator[dict]:
        ...
```

Register it so configuration-driven code can find it:

```python
from merkle_store import STORES
STORES["kafka"] = KafkaStorage
```

---

## Configuration

When used inside the async pipeline, the system is bootstrapped from a feature-flag config dict:

```json
{
    "store": "fs",
    "params": {
        "path": "/var/data/merkle_streams"
    }
}
```

| Key | Type | Description |
|-----|------|-------------|
| `store` | `str` | Backend name: `"inmemory"` or `"fs"` (or any key in `STORES`). |
| `params` | `dict` | Keyword arguments forwarded to the backend constructor. For `FSStorage` this is `{"path": "..."}`. For `InMemoryStorage` it should be `{}` or omitted. |

The config is read from `settings.feature_flag('merkle')`. If the flag is absent or falsy, the Merkle pipeline is not attached.

---

## Security Model & Threat Analysis

### Trust Model

The Merkle DAG provides **tamper evidence**, not **tamper prevention**. The system operator has write access to storage and *could* rewrite data. However:

| Threat | Mitigation |
|--------|------------|
| **Modify an event after the fact** | Changes the item hash → changes all downstream hashes → changes the final hash. Detectable by anyone who recorded the original final hash. |
| **Delete an item silently** | Breaks chain linkage (invariant 2). `verify_chain` will raise `ValueError`. |
| **Insert a fake item** | Changes all subsequent hashes. Detectable by final-hash comparison. |
| **Reorder items** | Breaks chain linkage. Detectable. |
| **Replace entire stream with fabricated data** | Produces a different final hash. Detectable if the original hash was published or recorded externally. |
| **Delete a stream without tombstone** | Parent streams still reference the old final hash. Attempting to resolve it fails. Absence is detectable. |
| **Forge a tombstone** | The tombstone hash covers the item-hash list. A forged tombstone would need to predict the per-item hashes of the original data, which requires knowledge of every event payload and timestamp — i.e., the data itself. |

### What You Must Do

For the security guarantees to hold, at least one of the following must be true:

1. **Publish root hashes externally** — to a transparency log, blockchain, append-only public ledger, or even a newspaper. This commits the operator to the current state of the DAG.
2. **Share final hashes with data subjects** — so they can independently verify their own data later.
3. **Use an append-only backend** — e.g., a Kafka topic with immutable retention, or S3 with Object Lock.

Without external commitment, the operator can silently rewrite everything. The Merkle structure makes rewriting *hard* (you must recompute the entire downstream chain), but not *impossible* if no one recorded the original hashes.

### Hash Algorithm

SHA-256 is used throughout. At current (2025) understanding:

- **Collision resistance:** ~2¹²⁸ operations — far beyond feasible computation.
- **Preimage resistance:** ~2²⁵⁶ operations.
- **No known practical attacks.**

The `HASH_TRUNCATE` setting exists **only** for debugging readability. In production, it must be `None` (full 64-character hex digest).

---

## Prototype Limitations & Production Roadmap

| Limitation | Production Fix |
|------------|----------------|
| In-memory and single-file-per-stream backends don't scale | Kafka, S3, or database backend |
| `run_in_executor` wrapping is a stopgap for async | Native async I/O in the storage backend |
| `FSStorage._most_recent_item` reads the entire file | Maintain an in-memory index or use a database |
| No periodic root-hash publication | Scheduled job that computes and publishes a Merkle root over all parent-stream tips |
| No stream chunking | Break long-lived streams on time or size boundaries using `break_session` |
| No encryption at rest | Encrypt PII-bearing streams; store decryption keys separately |
| No formal schema for events | Define and validate event schemas (JSON Schema, Avro, etc.) |
| Session key is raw canonical JSON | Compute a deterministic session ID via HMAC or structured hashing |
| Single-writer assumption per session | Enforce via distributed locking or partition assignment |
| Tombstones do not propagate to parent streams | Add a `child_deleted` event type to parent streams |
| No integration tests or property-based tests | Hypothesis-based chain-integrity tests, crash-recovery tests |

