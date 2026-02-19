'''
Toy-SBA Module

Toy-SBA Module
'''
import learning_observer.communication_protocol.util
from learning_observer.stream_analytics.helpers import KeyField, Scope

import lo_toy_sba.reducers

# Name for the module
NAME = 'Toy-SBA Module'

'''
Define execution DAGs for this module. We provide a default DAG
for fetching information from the provided reducer. The internal
structure looks like:

`execution_dag`: defined directed acyclic graph (DAG) for querying data
    <node name>: q.select() # or some other communication protocol query
`exports`: fetchable nodes from the execution dag
    <name for export>: {
        "returns": <node name>,
        "parameters": ["list", "of", "parameters", "needed"]
    }

NOTE interfacing with the communication protocol may change,
the current flow is the first iteration. We will mark where things
ought to be improved.
'''
EXECUTION_DAG = learning_observer.communication_protocol.util.generate_base_dag_for_student_reducer('student_event_counter', 'lo_toy_sba')

'''
This is a simple reducer we use to ensure events are
passed into the event pipeline to save/fetch state.
We need a reducer whose context matches the source of
a page using LO Event.
'''
REDUCERS = [
    {
        'context': 'org.ets.sba',
        'scope': Scope([KeyField.STUDENT]),
        'function': lo_toy_sba.reducers.student_event_counter,
        'default': {'count': 0}
    }
]

'''
Which pages to link on the home page.
'''
COURSE_DASHBOARDS = [
    # {
    #     'name': NAME,
    #     'url': "/lo_toy_sba/toy-sba/",
    #     "icon": {
    #         "type": "fas",
    #         "icon": "fa-play-circle"
    #     }
    # }
]


'''
Additional API calls we can define, this one returns the colors of the rainbow
'''
EXTRA_VIEWS = [
    # {
    #     'name': 'Colors of the Rainbow',
    #     'suburl': 'api/llm',
    #     'method': 'POST',
    #     'handler': function_to_call
    # }
]

'''
Built NextJS pages we want to serve.
'''
NEXTJS_PAGES = [
    # {'path': 'toy_sba/'}
]
