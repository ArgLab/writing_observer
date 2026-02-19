'''
This file defines reducers we wish to add to the incoming event
pipeline. The `learning_observer.stream_analytics` package includes
helper functions for Scoping the and setting the null state.
'''
from learning_observer.stream_analytics.helpers import student_event_reducer


@student_event_reducer(null_state={"count": 0})
async def {{ cookiecutter.reducer }}(event, internal_state):
    '''
    An example of a per-student event counter
    '''
    state = {"count": internal_state.get('count', 0) + 1}

    return state, state
