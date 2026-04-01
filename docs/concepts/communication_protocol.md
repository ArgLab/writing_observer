# Communication Protocol

The communication protocol is Learning Observer's query and transport
layer. It allows dashboards, notebooks, and other clients to request
aggregated data from the key-value store and supporting services by
submitting a declarative *execution DAG* (directed acyclic graph). The
server evaluates the DAG node-by-node, resolves the required
parameters, executes reducers or helper functions, and returns the
assembled result. This document explains how that process fits
together, the core building blocks you can use in a query, and the
helper utilities that make it easier to integrate those queries into
applications.

## Lifecycle of a Request

1. **Query construction** - A client builds a nested query description
   in Python (or another language) with the helpers in
   `learning_observer.communication_protocol.query`. The helpers mirror
   relational concepts such as parameters, joins, and projections and
   produce JSON-serialisable dictionaries. (See: query.py L1-L123)
2. **Flattening** - Before execution, the DAG is normalised so every
   node has a unique identifier and can reference other nodes via
   `variable` pointers. The `flatten` utility rewrites nested
   structures such as `select(keys(...))` into separate nodes to make
   evaluation straightforward. (See: util.py L1-L59)
3. **Execution** - The executor walks the flattened DAG, dispatching
   each node type to a registered handler. Nodes can call Python
   functions, fetch keys from the key-value store, join intermediate
   datasets, or map functions across collections. The executor
   assembles the final payload and enforces error handling through the
   `DAGExecutionException` type. (See: executor.py L1-L145, L147-L220)
4. **Exports** - Queries expose named *exports* that identify the DAG
   nodes clients may request. The integration layer can bind those
   exports to callables so dashboards or notebooks can invoke them as
   regular async functions. (See: util.py L64-L104, integration.py L38-L102)

This flow supports both server-defined queries and open-ended
exploration. Production deployments typically offer curated, predefined
queries while development tooling exposes the full language for
experimentation. (See: README.md L11-L36)

## Core Node Types

Every node in the execution DAG has a `dispatch` type that determines
how the executor evaluates it. The query helper functions generate the
correct shape for each node type. (See: query.py L19-L123) The most common nodes are:

- **`parameter`** - Declares a runtime argument. Parameters can be
  required or optional, and the executor substitutes provided values or
  defaults before downstream nodes run. (See: query.py L33-L42, executor.py L114-L144)
- **`variable`** - References the output of another node in the DAG.
  These indirections are automatically inserted during flattening but
  can also be used explicitly when wiring complex queries. (See: query.py L45-L52, util.py L13-L61)
- **`call`** - Invokes a published Python function on the server.
  Functions are registered with `publish_function`, which ensures every
  callable has a unique name. Called functions may be synchronous or
  asynchronous; the executor awaits results as needed. (See: query.py L55-L67, executor.py L61-L112, integration.py L21-L47)
- **`keys`** - Produces the key descriptions required to fetch reducer
  outputs from the key-value store. Keys nodes typically wrap the
  outputs of roster or metadata queries so downstream `select` nodes
  can retrieve the associated reducer documents. (See: query.py L114-L123, util.py L72-L102)
- **`select`** - Retrieves documents from the key-value store for the
  provided keys. You can request all fields or limit to specific
  projections via `SelectFields` enumerations. (See: query.py L70-L83)
- **`join`** - Merges two lists of dictionaries on matching keys using
  dotted-path lookups. Left rows are preserved even without a matching
  right-hand record, making it straightforward to enrich reducer
  outputs with roster data. (See: query.py L86-L96, executor.py L147-L220)
- **`map`** - Applies a published function to each value in a list,
  optionally in parallel, returning the transformed collection. This is
  useful for server-side post-processing or feature extraction before a
  result is exported. (See: query.py L99-L111)

## Building Queries Efficiently

Writing DAGs by hand is verbose, so the protocol provides shorthands
for common access patterns. For example,
`generate_base_dag_for_student_reducer` returns an execution DAG that
retrieves the latest reducer output for every student in a course,
including roster metadata and a preconfigured export entry. Dashboards
use this helper to quickly expose reducer results without writing the
full DAG each time. (See: util.py L63-L101)

The `integration` module can also bind exports directly to a module so
code can call `await module.student_event_counter_export(course_id=...)`
instead of manually constructing requests. This keeps the protocol's
flexibility while offering ergonomic entry points for UI
components. (See: integration.py L49-L102)

## WebSocket Endpoint

Dashboards and other clients interact with the communication protocol
through a dedicated WebSocket endpoint exposed at
`/wsapi/communication_protocol`. The aiohttp application wires that path
to `websocket_dashboard_handler`, making the protocol available to
browser sessions and backend consumers alike. (See: learning_observer/routes.py L195-L213)

When a client connects, the handler waits for a JSON payload describing
one or more queries. Each entry typically includes the flattened
`execution_dag`, a list of `target_exports` to stream, and optional
`kwargs` that provide runtime parameters. Whenever the client submits a
new payload, the server builds the requested DAG generators, executes
them, and schedules reruns based on the provided settings. Responses are
batched into arrays of `{op, path, value}` records so the client can
efficiently apply partial updates to its local state. (See: learning_observer/dashboard.py L331-L411)

## Tooling and Debugging

Two exploratory tools live alongside the protocol implementation:

- `debugger.py` - Provides an interface for submitting ad-hoc queries
  and inspecting intermediate results.
- `explorer.py` - Lists predefined queries already published on the
  server so you can execute them interactively.

Because the protocol is evolving, these tools occasionally require
updates when the underlying schema changes. Keeping the communication
protocol documented and covered by tests makes it easier to spot and
fix those regressions quickly. (See: README.md L45-L72)

## Security Considerations

Production deployments default to predefined queries so clients can
only request vetted datasets. Open-query mode should be restricted to
trusted environments—such as local notebooks or read replicas—because
it allows arbitrary function calls and joins that may expose sensitive
information or stress backing stores. (See: README.md L11-L36)

Understanding these concepts makes it easier to extend the protocol,
design new reducers, and reason about the performance characteristics
of dashboards built on Learning Observer.
