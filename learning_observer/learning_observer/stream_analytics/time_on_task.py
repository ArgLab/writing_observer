'''
Helpers for time-on-task reducers.
'''
import pmss

pmss.register_field(
    name='time_on_task_threshold',
    type=pmss.pmsstypes.TYPES.integer,
    description='Maximum time to pass before marking a session as over. '\
        'Should be 60-300 seconds in production, but 5 seconds is nice for '\
        'debugging in a local deployment.',
    default=60
)
pmss.register_field(
    name='binned_time_on_task_bin_size',
    type=pmss.pmsstypes.TYPES.integer,
    description='How large (in seconds) to make timestamp bins when '\
        'recording binned time on task.',
    default=600
)


def default_time_on_task_state():
    return {
        'saved_ts': None,
        'total_time_on_task': 0
    }


def apply_time_on_task(internal_state, current_timestamp, time_delta_threshold):
    if internal_state is None:
        internal_state = default_time_on_task_state()
    last_ts = internal_state['saved_ts']
    internal_state['saved_ts'] = current_timestamp

    if last_ts is None:
        last_ts = internal_state['saved_ts']
    if last_ts is not None:
        delta_t = min(
            time_delta_threshold,
            internal_state['saved_ts'] - last_ts
        )
        internal_state['total_time_on_task'] += delta_t
    return internal_state


def default_binned_time_on_task_state():
    return {
        'saved_ts': None,
        'binned_time_on_task': {},
        'current_bin': None
    }


def get_time_bin(timestamp, bin_size):
    b = (timestamp // bin_size) * bin_size
    return int(b)


def update_binned_time_on_task(internal_state, current_bin, last_timestamp, delta_time, bin_size):
    '''Handle updating the internal state for binned time on task.'''
    next_bin = current_bin + bin_size
    next_bin_str = str(next_bin)

    current_bin_str = str(current_bin)
    if current_bin_str not in internal_state['binned_time_on_task']:
        internal_state['binned_time_on_task'][current_bin_str] = 0

    if last_timestamp + delta_time >= next_bin:
        internal_state['binned_time_on_task'][current_bin_str] += next_bin - last_timestamp
        if next_bin_str not in internal_state['binned_time_on_task']:
            internal_state['binned_time_on_task'][next_bin_str] = 0
        internal_state['binned_time_on_task'][next_bin_str] += last_timestamp + delta_time - next_bin
    else:
        internal_state['binned_time_on_task'][current_bin_str] += delta_time


def apply_binned_time_on_task(
        internal_state,
        current_timestamp,
        time_delta_threshold,
        bin_size
):
    if internal_state is None:
        internal_state = default_binned_time_on_task_state()
    last_timestamp = internal_state['saved_ts']
    current_bin = internal_state['current_bin']
    internal_state['saved_ts'] = current_timestamp

    if last_timestamp is None:
        last_timestamp = internal_state['saved_ts']
    if current_bin is None:
        current_bin = get_time_bin(last_timestamp, bin_size)

    if last_timestamp is not None:
        delta_time = min(
            time_delta_threshold,
            internal_state['saved_ts'] - last_timestamp
        )
        update_binned_time_on_task(internal_state, current_bin, last_timestamp, delta_time, bin_size)

    internal_state['current_bin'] = get_time_bin(internal_state['saved_ts'], bin_size)
    return internal_state
