# Key-value store

Learning Observer reducers and dashboards communicate through a key-value store (KVS).
Reducers write internal state and dashboard-facing summaries to the store, while
queries and presentation layers read those JSON blobs back. The
[`learning_observer.kvs` module](../../learning_observer/learning_observer/kvs.py)
wraps the different storage backends behind a common async API.

## Router and lifecycle

The `KVSRouter` constructed during startup owns every configured backend. When
`learning_observer.prestartup` runs it reads the `kvs` section from system
settings, instantiates the requested implementations, and exposes them through
the module-level `KVS` callable. Most code imports `learning_observer.kvs.KVS`
and invokes it to obtain the default backend:

```python
from learning_observer import kvs

store = kvs.KVS()  # returns the default backend configured in settings
value = await store[key]
```

Reducers obtain the store implicitly through decorators such as
`kvs_pipeline` and `student_event_reducer`. Those helpers capture the module
context, derive the reducer keys, and persist the reducer's internal and
external state back to the configured KVS.

The router also exposes named backends as attributes. If a module needs to
store data in a non-default backend it can call `kvs.KVS.<name>()` where
`<name>` matches the identifier from configuration.

## Configuring backends

The `kvs` block in `creds.yaml` (or an equivalent PMSS overlay) declares each
backend. Settings accept either a mapping or an array of key/value tuples.
Every entry must provide a `type` that matches one of the built-in
implementations:

```yaml
kvs:
  default:
    type: filesystem
    path: .lo_kvs
  redis_cache:
    type: redis_ephemeral
    expiry: 30
```

During startup the router validates the configuration and raises a
`StartupCheck` error if a backend is missing required parameters or references
an unknown type. Once the process finishes booting, the resulting callable is
available to the rest of the system as `learning_observer.kvs.KVS`.

### Supported types

| Type             | Class                       | Persistence behavior                                                  | Required settings                             |
|------------------|-----------------------------|------------------------------------------------------------------------|-----------------------------------------------|
| `stub`           | `InMemoryKVS`               | Data lives only in process memory and disappears on restart.          | None                                          |
| `redis_ephemeral`| `EphemeralRedisKVS`         | Uses Redis with a per-key TTL for temporary caches.                    | `expiry` (seconds)                            |
| `redis`          | `PersistentRedisKVS`        | Stores data in Redis without an expiry; persistence depends on Redis. | Redis connection parameters in system config. |
| `filesystem`     | `FilesystemKVS`             | Serializes each key to JSON on disk for simple local persistence.      | `path`; optional `subdirs` boolean            |

All backends share the async API: `await store[key]`, `await store.set(key, value)`,
`await store.keys()`, and `await store.dump()` for debugging.

### Filesystem layout

The filesystem implementation writes JSON documents under the configured path.
If `subdirs` is true it mirrors slash-separated key prefixes into nested
folders while prefixing directory names with underscores to avoid collisions.
This backend is convenient for workshops or debugging because state survives
restarts as long as the directory remains intact, but it is not designed for
large-scale deployments.

### Redis variants

Both Redis implementations rely on the shared connection utilities in
`learning_observer.redis_connection`. The ephemeral variant requires an
`expiry` value so it can set a TTL when calling `SET`, making it suitable for
integration tests or scratch environments. The persistent variant omits the TTL
so keys remain until explicitly deleted or until the Redis server evicts them.
Ensure the Redis instance has persistence enabled (`appendonly` or RDB
snapshots) if the deployment expects reducer state to survive reboots.

### In-memory stub

The stub backend keeps a Python dictionary in memory. It is useful for unit
tests or prototype scripts but should not be used when the process restarts or
scales across workers. The module exposes a `clear()` helper to wipe the store
between tests.

## Working with reducer state

Reducer keys follow the pattern `<scope>,<module>,<selector>` where the scope
captures whether the state is internal or external, the module identifies the
producer, and the selector encodes the entity (for example, a student ID). When
reducers process new events they read the previous state from the KVS, compute
an updated value, and call `set()` to write it back. Dashboards and protocol
adapters then fetch the external state by constructing the same key or by using
higher-level query helpers that wrap the KVS API.

If a dashboard appears empty after restarting the server, confirm which backend
is active. In-memory and ephemeral Redis stores start empty on boot, so the
system needs a fresh stream of events to repopulate reducer state. Filesystem
and persistent Redis backends retain data unless their underlying storage was
cleared.
