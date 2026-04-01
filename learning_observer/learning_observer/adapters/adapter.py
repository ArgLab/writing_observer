'''
The Adapter class is designed to transform the data from the source into the
data that the reducers expect.

A lot of this is TBD. See the README file for more details.

There's not too much here. It's a placeholder to get the architectural pieces
in the right place.
'''

import learning_observer.adapters.helpers


# In the original code, we had dashes. We want underscores. This is a mapping
# from the old to the new, not just in events, but also in the KVS (but not
# in the config file).
FIELD_RENAMES = {
    "event-type": "event_type",
    "org.mitros.writing-analytics": "org.mitros.writing_analytics",
    "teacher-tag": "teacher_tag",
    "user-tag": "user_tag",
    "process-server": "process_server",
    "unique-id": "unique_id",
    "generated-id": "generated_id",
    "local-storage": "local_storage",
    "wa-source": "wa_source",
    "background-page": "background_page",
    "client-page": "client_page",
    "stream-test-script": "stream_test_script",
    "character-count": "character_count",
    "total-time-on-task": "total_time_on_task",
    "summary-stats": "summary_stats",
    "student-data": "student_data",
    "org.mitros.dynamic-assessment": "org.mitros.dynamic_assessment",
    "da-guest": "da_guest",
}


def dash_to_underscore(event):
    '''
    Convert dashes in events from the alpha version to underscores.
    '''
    event = learning_observer.adapters.helpers.rename_json_keys(
        event, FIELD_RENAMES
    )

    if 'client' in event and 'source' in event['client']:
        event['client']['source'] = event['client']['source'].replace('-', '_')
    if 'source' in event:
        event['source'] = event['source'].replace('-', '_')

    return event

common_transformers = [
    dash_to_underscore
]

def add_common_migrator(migrator, file):
    '''Add a migrator to the common transformers list.
    TODO
    We ought check each module on startup for migrators
    and import them instead of using this function to
    add them to the transformations.
    '''
    print('Adding migrator', migrator, 'from', file),
    common_transformers.append(migrator)


class EventAdapter:
    def __init__(self, metadata=None):
        self.metadata = metadata

    def canonicalize_event(self, event):
        '''
        Transform the event into the format that the reducers expect.

        This may modify the event in place.

        This is a lousy API since we may want to split and re-combine
        events. At some point, we'll want to figure out how to combine
        `async` and `yield` to do this right.
        '''
        for transformer in common_transformers:
            event = transformer(event)
        return event

    def set_metadata(self, metadata):
        '''
        Set the metadata for the adapter.

        Not implemented, but a placeholder for how the API will work.
        '''
        self.metadata = metadata
        raise NotImplementedError()


""""
We probably want something like:

    async def transform_events(self, events):
        '''
        Transform a list of events.

        This is a generator.
        '''
        async for event in events:
            yield self.canonicalize_event(event)

And to use this as:

ws = aiohttp.web.WebSocketResponse()
json_events = decode_json_events(ws)
adapted_events = adapter.transform_events(json_events)
...

I'm not sure if the above syntax is right; we will try this once we have a
working baseline version.
"""
