import learning_observer.kvs
import learning_observer.stream_analytics.helpers as sa_helpers

def state_blob():
    '''Dummy function for the reducer name portion of the
    KVS key
    '''
    pass

def _make_key(user_id, source, activity):
    '''Helper function to format keys for the KVS
    '''
    key = sa_helpers.make_key(
        state_blob,
        {
            sa_helpers.EventField('source'): source,
            sa_helpers.EventField('activity'): activity,
            sa_helpers.KeyField.STUDENT: user_id
        },
        sa_helpers.KeyStateType.INTERNAL
    )
    return key

async def fetch_blob(user_id, source, activity):
    '''Fetch the blob from the KVS
    '''
    key = _make_key(user_id, source, activity)
    kvs = learning_observer.kvs.KVS()
    return await kvs[key]

async def save_blob(user_id, source, activity, blob):
    '''Store a blob in the KVS
    '''
    key = _make_key(user_id, source, activity)
    kvs = learning_observer.kvs.KVS()
    await kvs.set(key, blob)
