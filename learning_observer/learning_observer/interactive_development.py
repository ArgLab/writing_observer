import learning_observer.communication_protocol.query as q
import learning_observer.dashboard
import learning_observer.kvs
import learning_observer.module_loader
import learning_observer.stream_analytics
from learning_observer.stream_analytics.helpers import KeyField, Scope

MODULE_NAME = 'jupyter-helper'

def _transform_reducer_into_classroom_query(id):
    '''Take a reducer and create the execution dag to run
    that query over a classroom.

    HACK much of this is hardcoded and needs to be abstracted

    This relies on the reducer having `scope=Scope([KeyField.STUDENT])`.
    '''
    course_roster = q.call('learning_observer.courseroster')
    # TODO replace event_count stuff with more general items
    dag = {
        "execution_dag": {
            "roster": course_roster(runtime=q.parameter("runtime"), course_id=q.parameter("course_id", required=True)),
            'event_count': q.select(q.keys(id, STUDENTS=q.variable("roster"), STUDENTS_path='user_id'), fields={'event_count': 'event_count'}),
        },
        "exports": {
            'event_count': {
                'returns': 'event_count',
                'parameters': ['course_id']
            }
        }
    }
    return dag


def construct_reducer(reducer_id, reducer_func, module=MODULE_NAME, scope=None, default=None):
    scope = scope if scope else Scope([KeyField.STUDENT])
    reducer = {
        # TODO not sure the best way to handle specifying context
        'context': 'org.mitros.writing_analytics',
        'function': reducer_func,
        'scope': scope,
        'default': default,
        'module': module,
        'id': reducer_id
    }
    return reducer


async def remove_reducer_results_from_kvs(reducer_id):
    '''Find all keys that match the reducer and remove them

    TODO: Figure out if we should move this into kvs.py or otherwise bubble
    it up. It seems like it may be more broadly applicable than just
    interactive development.
    '''
    kvs = learning_observer.kvs.KVS()
    keys = await kvs.keys()
    matched_keys = [k for k in keys if reducer_id in k]
    for m in matched_keys:
        await kvs.remove(m)


async def _restream_prior_event_logs(reducer):
    '''Process event logs through a reducer in the background while
    keeping the old reducer running. Once finished, swap active
    reducers in the event pipeline.
    '''
    # TODO process reducer over files corresponding to the removed keys
    # files_to process = find_files(removed_keys)
    # await learning_observer.offline.process_files(files_to_process)
    raise NotImplementedError('Restreaming of prior event logs has not yet been implemented')


async def _drop_prior_data(reducer):
    '''Remove the specified reducer, re-init our event pipeline, then
    remove any data associated with the removed reducer.
    '''
    reducer_id = reducer['id']
    learning_observer.module_loader.remove_reducer(reducer_id)
    learning_observer.stream_analytics.init()
    await remove_reducer_results_from_kvs(reducer_id)


async def _process_curr_reducer_output_through_func(reducer):
    '''Take the current results of a given reducer and modify them
    based on the provided function.

    The default func should just return the value
    '''
    raise NotImplementedError('Processing reducer output through a migration function is not yet implemented.')


RESTREAM_PRIOR_DATA = 'restream_prior_data'
DROP_DATA = 'drop_data'
PROCESS_REDUCER_FUNC = 'process_reducer_function'
MIGRATION_POLICY = {
    RESTREAM_PRIOR_DATA: _restream_prior_event_logs,
    DROP_DATA: _drop_prior_data,
    PROCESS_REDUCER_FUNC: _process_curr_reducer_output_through_func
}


async def hot_load_reducer(reducer, reload=False, migration_function=None):
    reducer_id = reducer['id']
    adding_reducer = not reload

    reducers = learning_observer.module_loader.reducers()
    existing_reducer = any(r['id'] == reducer_id for r in reducers)

    if migration_function is not None and migration_function not in MIGRATION_POLICY:
        error_msg = f'Migration function, `{migration_function}`, is not a valid type. '\
            f'Available types are: [{", ".join(MIGRATION_POLICY.keys())}, None]'
        raise KeyError(error_msg)

    if adding_reducer and existing_reducer:
        error_msg = f'The reducer, `{reducer_id}`, currently '\
            'exists and the `reload` parameter is set to False (this is the default). '\
            'To add a reducer instead of reloading, use:\n'\
            '`hot_load_reducer(..., reload=True)`'
        raise RuntimeError(error_msg)

    if adding_reducer and migration_function is not None and migration_function != RESTREAM_PRIOR_DATA:
        error_msg = f'Migration function, `{migration_function}`, '\
            'is not available when adding a new reducer.'
        raise RuntimeError(error_msg)

    if migration_function is not None:
        # TODO we want to pass more args/kwargs in here for the other migration policies
        await MIGRATION_POLICY[migration_function](reducer)

    # add reducer to available reducers and re-init our pipeline
    learning_observer.module_loader.add_reducer(reducer)
    learning_observer.stream_analytics.init()

    # TODO determine the best way to update the execution dag
    # much of this is currently hardcoded for Student scope.
    # create a simple "module" to set the execution dag
    obj = lambda: None
    obj.EXECUTION_DAG = _transform_reducer_into_classroom_query(reducer_id)
    learning_observer.module_loader.load_execution_dags(reducer['module'], obj)

    return
