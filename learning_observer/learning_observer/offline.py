'''
Learning Observer Library

Helpers to support the use of Learning Observer in scripts, in
other applications, and in Jupyter notebooks.
'''
import asyncio
import gzip
import itertools
import json
import os

import names

import learning_observer.constants
import learning_observer.settings
import learning_observer.stream_analytics
import learning_observer.module_loader
import learning_observer.incoming_student_event
import learning_observer.log_event
import learning_observer.kvs
import learning_observer.rosters
import learning_observer.dashboard

from learning_observer.stream_analytics.helpers import kvs_pipeline, KeyField, EventField, Scope


# For interactive data analysis
INTERACTIVE_SETTINGS = {
    'kvs': {'default': {'type': 'stub'}},
    'config': {
        'run_mode': 'interactive'
    },
    "logging": {
        "debug_log_level": "NONE",
        "debug_log_destination": ["console"]
    },
    "roster_data": {
        "source": "all"
    }
}


def init(settings=INTERACTIVE_SETTINGS):
    '''
    Initialize the Learning Observer library.

    Returns:
        None

    This function will load the settings, and initialize the KVS to
    run from memory.
    '''
    # We override the debug log level since we don't want to spew logs if we do
    # anything before we've loaded the settings. This might not be necessary,
    # depending on the (still-changing) startup order
    learning_observer.log_event.DEBUG_LOG_LEVEL = learning_observer.log_event.LogLevel.NONE
    # TODO: Allow offline callers to pass PMSS ruleset files or directories.
    learning_observer.settings.init_pmss_settings()
    learning_observer.settings.load_settings(settings)
    learning_observer.prestartup.startup_checks_and_init()
    learning_observer.kvs.kvs_startup_check()  # Set up the KVS
    # Force load of the reducers. This is not necessary right now, but it was
    # before, and might be later again. We should remove this call once the
    # system has stabilized a little bit.
    reducers = learning_observer.module_loader.reducers()
    learning_observer.stream_analytics.init()  # Load existing reducers
    learning_observer.rosters.init()


async def process_file(
    file_path=None,
    events_list=None,
    source=None,
    userid=None,
    pipeline=None
):
    '''
    Process a single study log file.

    Args:
        file_path (str): The path to the study log file to process
                         (``*.study.log`` or ``*.study.log.gz``).
        source (str): The source of events (e.g. org.mitros.dynamic_assessment)
                      If not specified, the source will be inferred from the
                      events.
        userid (str): The userid of the user that generated the events. If not
                        specified, the userid will be generated with `names`.

    Returns:
        Number of events processed, source, and userid

    If `source` is not specified, the source will be inferred from the
    log file. Only study logs should be used for replay to ensure the
    appended timestamp and metadata are handled correctly.

    If `userid` is not specified, a username will be generated with
    `names.get_first_name()`. We do this because we don't want to
    accidentally use a real name. This minimizes the risk of exposing
    PII. It'd be easy to infer the real name from the log file, but
    that should be done with care, and a parameter would be needed to
    enable this.
    '''
    if events_list is not None and file_path is not None:
        raise AttributeError("Please specify either an events list or a file path, not both")

    # Opener returns an iterator of events. It handles diverse sources:
    # lists, log files, and compressed log files
    def opener():
        if events_list is not None:
            return iter(events_list)

        if file_path is None:
            raise ValueError("Either events_list or file_path must be provided")

        def decode_event(line):
            # Study logs append a timestamp separated by a tab; strip it off before decoding
            line = line.decode("utf-8") if isinstance(line, bytes) else line
            if "\t" in line:
                payload, suffix = line.rsplit("\t", 1)
                line = payload
            return json.loads(line)

        if file_path.endswith('.study.log'):
            file_handle = open(file_path, 'r')
        elif file_path.endswith('.study.log.gz'):
            file_handle = gzip.open(file_path, 'rt')
        else:
            raise ValueError("Unknown study log type (expected .study.log or .study.log.gz): " + file_path)

        with file_handle as fp:
            for line in fp:
                yield decode_event(line)

    # We need to inspect the events to determine source, but also reuse them for processing
    events_iter, events_for_processing = itertools.tee(opener())

    if source is None:
        try:
            first_event = next(events_iter)
        except StopIteration:
            raise ValueError("No events available to infer source")
        source = first_event['client']['source']
        events_for_processing = itertools.chain([first_event], events_for_processing)

    # In most cases, for development, a dummy name is good.
    if userid is None:
        userid = names.get_first_name()

    metadata = {
        "source": source,
        "auth": {
            learning_observer.constants.USER_ID: userid,
            "safe_user_id": userid
        }
    }

    if pipeline is None:
        pipeline = await learning_observer.incoming_student_event.student_event_pipeline(metadata)
    else:
        pipeline = await pipeline(metadata)

    n = 0  # Number of events processed
    for event in events_for_processing:
        try:
            await pipeline(event)
            n += 1
        except Exception:
            print(event)
            raise

    return n, source, userid


async def process_files(files):
    '''
    Process a list of study log files.

    Args:
        files (list): A list of study log files to process.

    Returns:
        Total number of events processed

    This function will process each study log file in the list, and print the
    results.
    '''
    total = 0
    for file in files:
        n, source, userid = await process_file(file)
        print("{} events processed from {} with user ID {}".format(n, source, userid))
        total += n

    return total


async def process_dir(path=os.getcwd()):
    '''
    Process all study log files in a directory.

    Args:
        path (str): The path to the directory to process.

    Returns:
        Number of files processed, total number of events processed

    This function will process all study log files (``*.study.log`` or
    ``*.study.log.gz``) in the directory, and print the results. These logs
    include replay metadata and should be used instead of raw ``.log`` files
    when re-running offline analyses.
    '''
    files = [
        os.path.join(path, f)
        for f in os.listdir(path)
        if f.endswith('.study.log') or f.endswith('.study.log.gz')
    ]
    events_processed = await process_files(files)
    return len(files), events_processed


async def reset():
    '''
    Reset the Learning Observer library, clearing all processed events
    from the KVS.

    In the future, this might also clear the modules, etc.
    '''
    kvs = learning_observer.kvs.KVS()
    await kvs.clear()


async def aggregate(module_id):
    '''
    Aggregate the results of a module.

    This has a lot of overlap with dashboard.py, and should be refactored.
    '''
    course_id = 12345
    course_aggregator_module, default_data = learning_observer.dashboard.find_course_aggregator(module_id)

    if course_aggregator_module is None:
        print("Bad module: ", module_id)
        available = learning_observer.module_loader.course_aggregators()
        print("Available modules: ", [available[key]['short_id'] for key in available])
        raise ValueError(text="Invalid module: {}".format(module_id))

    roster = await learning_observer.rosters.courseroster("request", course_id)
    student_state_fetcher = learning_observer.dashboard.fetch_student_state(
        course_id,
        module_id,
        course_aggregator_module,
        roster,
        default_data
    )
    aggregator = course_aggregator_module.get('aggregator', lambda x: {})
    sd = await student_state_fetcher()
    data = {
        "student_data": sd   # Per-student list
    }
    data.update(aggregator(sd))
    return data


async def default_aggregation(function):
    """
    Return the aggregated data from this reducer function. This doesn't
    require any aggregators to be loaded, which is nice.

    This is only for offline operation (e.g. with the `all` roster)
    """
    roster = await learning_observer.rosters.courseroster(None, 12345)
    student_state_fetcher = learning_observer.dashboard.fetch_student_state(
        12345,
        "test_case_unused",
        {"sources": [function]},
        roster,
        {}
    )
    sd = await student_state_fetcher()
    return {"student_data": sd}


@kvs_pipeline(
    scope=Scope([KeyField.STUDENT]),
    module_override="testcase",
    qualname_override="event_count"
)
async def test_reducer(event, state):
    if state is None:
        state = {}
    state['event_count'] = state.get('event_count', 0) + 1
    return state, state


async def test_case():
    init()
    print("Reducers:")
    print(learning_observer.module_loader.reducers())
    kvs = learning_observer.kvs.KVS()
    print("Keys:")
    print(await kvs.keys())
    import tempfile
    import os
    (handle, filename) = tempfile.mkstemp(text=True, suffix=".log")
    with os.fdopen(handle, "w") as fp:
        for i in range(5):
            fp.write("{}\n")
    await process_file(
        file_path=filename,
        source="org.ets.testcase",
        pipeline=test_reducer,
        userid="Bob"
    )
    os.unlink(filename)
    await process_file(
        events_list=[{}] * 3,
        source="org.ets.testcase",
        pipeline=test_reducer,
        userid="Sue"
    )
    print("Keys:")
    keys = await kvs.keys()
    print(keys)
    for key in keys:
        print("{key} {value}".format(
            key=key,
            value=await kvs[key]
        ))
    print(await default_aggregation(test_reducer))

# A lot of Learning Observer calls expect app object, request objects, etc.
# These are dummy stub versions.


class StubApp():
    def __init__(self):
        self.loop = asyncio.get_event_loop()

    def add_routes(self, *args, **kwargs):
        pass


app = StubApp()


class StubRequest():

    def __init__(self):
        self.app = app

    def __contains__(self, item):
        if item == learning_observer.constants.AUTH_HEADERS:
            return True
        return False

    def __getitem__(self, item):
        return {}


request = StubRequest()


if __name__ == '__main__':
    asyncio.run(test_case())
