from learning_observer.stream_analytics.helpers import student_event_reducer

KEYS_TO_IGNORE = ['metadata', 'source', 'version', 'auth']


@student_event_reducer(null_state={"events": []})
async def student_event_history(event, internal_state):
    '''
    An example of a per-student event counter
    '''
    cleaned_event = {key: value for key, value in event['client'].items() if key not in KEYS_TO_IGNORE}
    internal_state['events'].append(cleaned_event)

    return internal_state, internal_state
