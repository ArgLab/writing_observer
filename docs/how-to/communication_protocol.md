# How to Build and Run Communication Protocol Queries

This guide explains the end-to-end workflow for turning a reporting idea into a runnable query on the Learning Observer communication protocol. Follow the steps in order—both humans and language models can use this as a checklist when creating or automating queries.

## 1. Frame the Data Task

1. Write a one-sentence description of the insight or dataset you need (e.g., *“Return the latest writing sample for each student in a course”*).
2. Identify the reducers, helper functions, or key-value store documents that expose the data. Concept docs provide summaries of the executor lifecycle, node types, and utilities for transforming reducer outputs. 【F:docs/concepts/communication_protocol.md†L1-L100】
3. Check whether an existing helper (e.g., `generate_base_dag_for_student_reducer`) already provides most of the DAG structure. Reusing helpers keeps queries consistent and concise. 【F:docs/concepts/communication_protocol.md†L62-L87】

## 2. Confirm Your Goal and Required Data

1. Identify the data source(s):

   * **Reducers** - Aggregated documents stored in the key-value store.
   * **Helper functions** - Python callables published with `publish_function`.
   * **Roster/metadata** - Collections that need to be joined with reducer data.
2. Decide which fields must appear in the output. Note whether you need the entire document or only specific fields.
3. List all runtime values (course ID, time range, student list, etc.). These become `parameter` nodes later.

Document these choices (in comments or metadata) so you can refer to them in later steps.

## 3. Declare Parameters and Defaults

Each runtime input must be expressed as a `parameter` node. Parameters can be required or optional and may include default values:

```python
course_id = query.parameter("course_id", required=True)
student_id = query.parameter("student_id", required=False, default=None)
```

For each parameter, document:

* **Name** - Identifier passed to the DAG node.
* **Type** - String, UUID, ISO date, etc.
* **Required** - Boolean flag.
* **Default** - Optional fallback value.

> Tip: Emit parameter declarations first so later steps can reuse variables like `course_id["variable"]` consistently.

For fixed values (e.g., reducer names or field lists), define constants once near where they are used.

## 4. Plan the Data Flow (DAG Skeleton)

Translate the goal into a linear sequence of operations. A typical reducer query involves:

1. Fetching roster metadata or other context.
2. Producing keys for each entity (`keys` nodes).
3. Retrieving reducer documents with `select`.
4. Joining reducer outputs with metadata.
5. (Optional) Post-processing with `map` or `call`.

Example outline:

```
roster = call("get_course_roster", course_id)
reducer_keys = keys(reducer_name, roster.students)
reducer_docs = select(reducer_keys, fields=[...])
enriched = join(reducer_docs, roster, left_on="student.id", right_on="id")
export enriched
```

Verify that every step depends only on earlier outputs, and adjust until the flow is acyclic.

## 5. Construct Nodes with Query Helpers

Use `query.py` helpers to implement the skeleton:

```python
from learning_observer.communication_protocol import query

roster = query.call("get_course_roster", args={"course_id": course_id})
reducer_keys = query.keys(
    "reading_fluency",
    scope_fields={
        "student": {"values": query.variable(roster), "path": "user_id"},
    },
)
reducer_docs = query.select(
    keys=reducer_keys,
    fields=query.SelectFields.SUMMARY,
)
enriched = query.join(
    left=reducer_docs,
    right=query.variable(roster),
    left_on="student_id",
    right_on="id",
)
```

Guidelines:

* Use `query.variable(node, path=None)` for downstream access to prior outputs.
* Encapsulate repeated or complex logic in functions for reuse and testing.
* Use explicit names and keyword arguments—avoid positional arguments for clarity.

### Defining reducer scopes for `keys` (preferred vs. legacy)

Reducers define a scope (e.g., student, student+document, student+document+tab). When
building a `keys` node, pass scope values that align with the reducer scope so the
executor can build the right Redis keys.

**Preferred: `scope_fields` (supports arbitrary scopes)**

Use `scope_fields` to supply each scope axis with either a `values` iterable or a
single value (applied across all items), plus an optional `path` into each item.
The scope field names should match the reducer scope: `student`,
`doc_id`, `tab_id`, `page_id`, etc.

```python
reducer_keys = query.keys(
    "writing_observer.some_tabbed_reducer",
    scope_fields={
        "student": {"values": query.variable("roster"), "path": "user_id"},
        "doc_id": {"values": query.variable("documents"), "path": "doc_id"},
        "tab_id": {"values": query.variable("tabs"), "path": "tab_id"},
        # or a single value
        "student": "bobs_user_id"
    },
)
```

**Legacy: `STUDENTS`/`RESOURCES`**

The older hack only supported student-only or student+document scopes. It is still
accepted for backward compatibility, but prefer `scope_fields` for new work.

```python
reducer_keys = query.keys(
    "writing_observer.last_document",
    STUDENTS=query.variable("roster"),
    STUDENTS_path="user_id",
    RESOURCES=query.variable("documents"),
    RESOURCES_path="doc_id",
)
```

## 6. Define Exports and Integrations

Choose which nodes should be externally accessible:

```python
exports = {
    "reading_fluency": query.export("reading_fluency", enriched)
}
```

If integrating with the async helper layer, pass `exports` to `learning_observer.communication_protocol.integration.bind_exports`.

Document required parameters and defaults with the export definitions.

## 7. Flatten, Validate, and Serialise

1. Convert the nested DAG into executor-ready form:

   ```python
   from learning_observer.communication_protocol import util
   dag = util.flatten(exports)
   ```

2. Confirm all node IDs are unique and reference earlier nodes. Inspect the flattened DAG if generated automatically.

3. Serialise to JSON (e.g., `json.dumps(dag)`) when sending over the wire.

4. Add automated tests—at minimum a smoke test against a fixture store.

## 8. Expose the DAG to Clients

To make the DAG discoverable over the websocket interface:

* Define `EXECUTION_DAG` in the module file and register it with the loader.
* On server start, the DAG will be advertised under the module’s namespace.

Production deployments should prefer predefined DAGs for security. Open-query mode is optional and must be explicitly enabled.

## 9. Execute the Query

Submit the flattened DAG to the communication protocol endpoint with runtime parameters:

```json
{
  "parameters": {
    "course_id": "course-123",
    "start_date": "2023-09-01"
  },
  "exports": ["reading_fluency"],
  "dag": { ... flattened nodes ... }
}
```

On success, the response includes export payloads keyed by export name. Inspect `DAGExecutionException` for error details.

The executor validates each requested export before any DAG work begins. If an
export name is unknown - or if its declared `returns` node cannot be found - the
server responds with a `DAGExecutionException` describing the missing export or
node. Surfacing these errors in logs or UI telemetry helps diagnose typos and
stale configuration quickly.

When using integration bindings, call the generated async function with the same parameters.

## 10. Construct Websocket Requests

Clients interact with `/wsapi/communication_protocol` via JSON messages. Each message contains:

* `execution_dag` - Name of a predefined DAG or a full DAG object.
* `target_exports` - List of exports to run.
* `kwargs` - Runtime parameters.

Example:

```json
{
  "docs_request": {
    "execution_dag": "writing_observer",
    "target_exports": ["docs_with_roster"],
    "kwargs": { "course_id": "COURSE-123" }
  }
}
```

The server streams back updates in messages shaped like:

```json
[
  {
    "op": "update",
    "path": "students.student-1",
    "value": { "text": "...", "provenance": { ... } }
  }
]
```

If `rerun_dag_delay` is set, the server automatically re-executes the DAG and pushes updates.

### Manual testing with the generic websocket dashboards

Two helper scripts live in `scripts/` for exercising websocket flows without running a full dashboard UI:

* `generic_websocket_dashboard.py` (Python + `aiohttp`)
* `generic_websocket_dashboard.js` (Node.js + `ws`)

Both scripts ship with a template payload under the `REQUEST` constant. Update the payload to target the exports and parameters you want to test—for example, changing `execution_dag`, `target_exports`, or `kwargs.course_id`.

To run the Python version:

```bash
python scripts/generic_websocket_dashboard.py
```

The script opens a websocket to `/wsapi/communication_protocol`, sends the JSON request, and pretty-prints any responses. Install dependencies with `pip install aiohttp` if needed.

The Node.js version follows the same pattern. After adjusting `REQUEST`, run:

```bash
node scripts/generic_websocket_dashboard.js
```

If you copy the script into a browser console, delete the `require('ws')` line so the native `WebSocket` implementation is used.

Use these scripts to confirm executor behaviour during development—for example, to observe partial updates or to verify that query parameters are wired correctly before embedding a request in a Dash dashboard.

## 11. Iterate and Maintain

* Profile slow queries; large joins may need new helpers or precomputed reducers.
* Keep DAGs version-controlled. Update dependent queries when reducers or helpers change.
* Review security before exposing exports to untrusted clients.

## 12. Test End-to-End

* **Unit-test** reducers and helpers independently.
* **Reference** `learning_observer/learning_observer/communication_protocol/test_cases.py` for DAG tests.
* **Exercise websocket flows** manually or with automated integration tests.

## 13. Document Parameters and Outputs

Update module documentation with:

* Export descriptions, parameter types, and return structures.
* Sample request payloads.
* Notes on authentication or runtime context.

Good documentation ensures developers and tooling can invoke queries reliably.

### Summary

Following this workflow ensures queries are consistent, testable, and safe to expose across dashboards, notebooks, and automation tools.
