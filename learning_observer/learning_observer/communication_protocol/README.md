# Communication Protocol / Query Language

## Motivation

In our first version of this system, we would simply compile the state for all the students, and ship that to the dashboard. However, that didn't allow us to make interactive dashboards, so we created a query language. This is inspired by SQL (with JOIN and friends), but designed for streaming data.

It can be written in Python or, soon, JavaScript, which compile queries to a JSON object. The JSON object is very similar to SQL.

## Security model

We allow two modes of operation:

- **Predefined queries** are designed for production use. The client cannot make arbitrary queries.
- **Open queries** are designed for development and data analysis, for example, working from a Jupyter notebook. This allows arbitrary queries, including ones which might not be performant or which might reveal sensitive data.

The latter should only be used in a trusted environment, and on a read replica.

## Shorthand / Getting Started

For common queries, we have shorthand notation, to maintain simplicity. In the majority of cases, we want just want the latest reducer data for either a single student or a classroom of students.

In `module.py`, you see this line:

```python
EXECUTION_DAG = learning_observer.communication_protocol.util.generate_base_dag_for_student_reducer('student_event_counter', 'my_event_module')
```

This is shorthand for a common query which JOINs the class roster with the output of the reducers. The Python code for the query itself is [here](https://github.com/ArgLab/writing_observer/blob/berickson/workshop/learning_observer/learning_observer/communication_protocol/util.py#L58), but the jist of the code is:

```python
'roster': course_roster(runtime=q.parameter('runtime'), course_id=q.parameter("course_id", required=True)),
keys_node: q.keys(f'{module}.{reducer}', STUDENTS=q.variable('roster'), STUDENTS_path='user_id'),
select_node: q.select(q.variable(keys_node), fields=q.SelectFields.All),
join_node: q.join(LEFT=q.variable(select_node), RIGHT=q.variable('roster'), LEFT_ON='provenance.provenance.value.user_id', RIGHT_ON='user_id')
```

You can add a `print(EXECUTION_DAG)` statement to see the JSON representation this compiles to.

To see the data protocol, open up develop tools from your browser, click on network, and see the communication_protocol response.

## Playing / Debugging / Interactive operations

* `debugger.py` has a view for executing queries manually.
* `explorer.py` has a view for showing predefined queries already on the server, and running those.

As of this writing, these are likely broken, as it has not been recently tested and there were code changes. Both of these should also:
* Be available from the Jupyter notebook in the future
* Have a command line / test case version

## Python Query Language



## JSON Query Language

