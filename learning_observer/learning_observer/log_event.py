'''
For now, we dump logs into files, crudely.

We're not there yet, but we would like to create a 哈希树, or
Merkle-tree-style structure for our log files.

Or to be specific, a Merkle DAG, like git.

Each item is stored under its SHA hash. Note that items are not
guaranteed to exist. We can prune them, and leave a dangling pointer
with just the SHA.

Each event log will be structured as
   +-----------------+     +-----------------+
<--- Last item (SHA) |  <--- Last item (SHA) | ...
   |                 |     |                 |
   |   Data (SHA)    |     |    Data (SHA)   |
   +-------|---------+     +--------|--------+
           |                        |
           v                        v
       +-------+                +-------+
       | Event |                | Event |
       +-------+                +-------+

Where the top objects form a linked list (each containing a pair of
SHA hashes, one of the previous item, and one of the associated
event).

We will then have a hierarchy, where we have lists per-document,
documents per-student. When we run analyses, those will store the
hashes of where in each event log we are. Likewise, with each layer
of analysis, we'll store pointers to git hashes of code, as well as
of intermediate files (and how those were generated).

Where data is available, we can confirm we're correctly replicating
prior tesults.

The planned data structure is very similar to git, but with the
potential for missing data without an implosion.

Where data might not be available is after a FERPA, CCPA, or GDPR
requests to change data. In those cases, we'll have dangling nodes,
where we'll know that data used to exist, but not what it was.

We might also have missing intermediate files. For example, if we do
a dozen analyses, we'll want to know those happened and what those
were, but we might not keep terabytes of data around (just enough to
redo those analyses).
'''

import datetime
from enum import Enum
import inspect
import io
import json
import hashlib
import os
import os.path
import pmss

import learning_observer.constants
import learning_observer.filesystem_state

import learning_observer.paths as paths
import learning_observer.settings as settings
import learning_observer.prestartup
import learning_observer.util


# These should move into the startup check
#
# Moving this would involve either queuing log messages until that check
# is called, or calling that before any events are generated. That's an
# important to do in either case.
if not os.path.exists(paths.logs()):
    print("Creating path for log files...")
    os.mkdir(paths.logs())

if not os.path.exists(paths.logs("startup")):
    print("Creating path for startup logs...")
    os.mkdir(paths.logs("startup"))

mainlog = open(paths.logs("main_log.json"), "ab", 0)
files = {}
startup_state = {}


# Do we make files for exceptions? Do we print extra stuff on the console?
#
# On deployed systems, this can make a mess. On dev systems, this is super-helpful
#
# We should probably move this to the settings file instead of hardcoding it. There
# was a reason for not placing this in the settings file, but it's no longer relevant
# after a refactor.
class LogLevel(Enum):
    '''
    What level of logging do we want?

    NONE: Don't print anything
    SIMPLE: Print a simple message
    EXTENDED: Print a message with a stack trace and timestamp
    '''
    NONE = 'NONE'
    SIMPLE = 'SIMPLE'
    EXTENDED = 'EXTENDED'


pmss.parser('debug_log_level', parent='string', choices=[level.value for level in LogLevel], transform=None)
pmss.register_field(
    name='debug_log_level',
    type='debug_log_level',
    description='How much information do we want to log.\n'\
                '`NONE`: do not print anything\n'\
                '`SIMPLE`: print simple debug messages\n'\
                '`EXTENDED`: print debug message with stack trace and timestamp'
)

class LogDestination(Enum):
    '''
    Where we log events? We can log to a file, or to the console.
    '''
    CONSOLE = 'CONSOLE'
    FILE = 'FILE'


# Before we've read the settings file, we'll log basic messages to the
# console and to the log file.
DEBUG_LOG_LEVEL = LogLevel.SIMPLE
DEBUG_LOG_DESTINATIONS = (LogDestination.CONSOLE, LogDestination.FILE)


@learning_observer.prestartup.register_init_function
def initialize_logging_framework():
    '''
    On startup, once settings are loaded, we set destinations as per the settings.

    Note that we may get log events before this is set up from other init code, which
    may ignore settings.

    We also log the system startup state.
    '''
    global DEBUG_LOG_LEVEL
    global DEBUG_LOG_DESTINATIONS

    # If we're in deployment, we don't want to print anything.
    DEBUG_LOG_LEVEL = LogLevel.NONE
    DEBUG_LOG_DESTINATIONS = []

    # If we're in development, we want to print to the console and to a file.
    if settings.RUN_MODE == settings.RUN_MODES.DEV:
        DEBUG_LOG_LEVEL = LogLevel.SIMPLE
        DEBUG_LOG_DESTINATIONS = [LogDestination.CONSOLE, LogDestination.FILE]

    # In either case, we want to override from the settings file.
    if "logging" in settings.settings:
        if "debug_log_level" in settings.settings["logging"]:
            DEBUG_LOG_LEVEL = LogLevel(settings.pmss_settings.debug_log_level(types=['logging']))
        if "debug_log_destinations" in settings.settings["logging"]:
            DEBUG_LOG_DESTINATIONS = list(map(LogDestination, settings.settings["logging"]["debug_log_destinations"]))

    debug_log("DEBUG_LOG_LEVEL:", DEBUG_LOG_LEVEL)
    debug_log("DEBUG_DESTINATIONS:", DEBUG_LOG_DESTINATIONS)

    # We're going to save the state of the filesystem on application startup
    # This way, event logs can refer uniquely to running version
    # Do we want the full 512 bit hash? Cut it back? Use a more efficient encoding than
    # hexdigest?
    global startup_state
    startup_state.update(learning_observer.filesystem_state.filesystem_state())
    startup_state_dump = json.dumps(startup_state, indent=3, sort_keys=True)
    STARTUP_STATE_HASH = learning_observer.util.secure_hash(startup_state_dump.encode('utf-8'))
    STARTUP_FILENAME = "{directory}/{time}-{hash}.json".format(
        directory=paths.logs("startup"),
        time=datetime.datetime.utcnow().isoformat(),
        hash=STARTUP_STATE_HASH
    )

    with open(STARTUP_FILENAME, "w") as sfp:
        # gzip can save about 2-3x space. It makes more sense to do this
        # with larger files later. tar.gz should save a lot more
        sfp.write(startup_state_dump)


def encode_json_line(line):
    '''
    For encoding short data, such as an event.

    We use a helper function so we have the same encoding
    everywhere. Our primary goal is replicability -- if
    we encode the same dictionary twice, we'd like to get
    the same string, with the same hash.
    '''
    return json.dumps(line, sort_keys=True)


def encode_json_block(block):
    '''
    For encoding large data, such as the startup log.

    We use a helper function so we have the same encoding
    everywhere. Our primary goal is replicability -- if
    we encode the same dictionary twice, we'd like to get
    the same string, with the same hash.
    '''
    return json.dumps(block, sort_keys=True, indent=3)


def log_event(event, filename=None, preencoded=False, timestamp=False):
    '''
    This isn't done, but it's how we log events for now.
    '''
    if filename is None:
        log_file_fp = mainlog
    elif filename in files:
        log_file_fp = files[filename]
    else:
        log_file_fp = open(paths.logs("" + filename + ".log"), "ab", 0)
        files[filename] = log_file_fp

    if not preencoded:
        event = encode_json_line(event)
    log_file_fp.write(event.encode('utf-8'))
    if timestamp:
        log_file_fp.write("\t".encode('utf-8'))
        log_file_fp.write(datetime.datetime.utcnow().isoformat().encode('utf-8'))
    log_file_fp.write("\n".encode('utf-8'))
    log_file_fp.flush()


def print_to_string(*args, **kwargs):
    '''
    This is a wrapper around print, which returns a string instead of
    printing it.

    :param args: The arguments to print
    :param kwargs: The keyword arguments to print
    :return: A string
    '''
    output = io.StringIO()
    print(*args, file=output, **kwargs)
    contents = output.getvalue()
    output.close()
    return contents


def debug_log(*args):
    '''
    Helper function to help us trace our code.

    We print a time stamp, a stack trace, and a /short/ summary of
    what's going on.

    This is not intended for programmatic debugging. We do change
    format regularly (and you should feel free to do so too -- for
    example, on narrower terminals, a `\n\t` can help)
    '''
    if DEBUG_LOG_LEVEL not in (LogLevel.NONE, LogLevel.SIMPLE, LogLevel.EXTENDED):
        raise ValueError("Invalid debug log type: {}".format(DEBUG_LOG_LEVEL))
    if DEBUG_LOG_LEVEL == LogLevel.NONE:
        return
    text = print_to_string(*args)
    if DEBUG_LOG_LEVEL == LogLevel.SIMPLE:
        message = text
    elif DEBUG_LOG_LEVEL == LogLevel.EXTENDED:
        stack = inspect.stack()
        stack_trace = "{s1}/{s2}/{s3}".format(
            s1=stack[1].function,
            s2=stack[2].function,
            s3=stack[3].function,
        )
        message = "{time}: {st:60}\t{body}".format(
            time=datetime.datetime.utcnow().isoformat(),
            st=stack_trace,
            body=text
        )

    # Flip here to print / not print debug messages
    if LogDestination.CONSOLE in DEBUG_LOG_DESTINATIONS:
        print(message.strip())

    # Print to file. Only helpful for development.
    if LogDestination.FILE in DEBUG_LOG_DESTINATIONS:
        with open(paths.logs("debug.log"), "a", encoding='utf-8') as fp:
            fp.write(message.strip() + "\n")

    # Ideally, we'd like to be able to log these somewhere which won't cause cascading failures.
    # If we e.g. have errors every 100ms, we don't want to create millions of debug files.
    # There are services which handle this pretty well, I believe


AJAX_FILENAME_TEMPLATE = "{directory}/{time}-{payload_hash}.json"


def log_ajax(url, resp_json, request):
    '''
    This is primarily used to log the responses of AJAX requests made
    TO Google and similar providers. This helps us understand the
    context of classroom activity, debug, and recover from failures
    '''
    payload = {
        learning_observer.constants.USER: request[learning_observer.constants.USER],
        'url': url,
        'response': resp_json,
        'timestamp': datetime.datetime.utcnow().isoformat()
    }
    encoded_payload = encode_json_block(payload)
    payload_hash = learning_observer.util.secure_hash(encoded_payload.encode('utf-8'))
    filename = AJAX_FILENAME_TEMPLATE.format(
        directory=paths.logs("ajax"),
        time=datetime.datetime.utcnow().isoformat(),
        payload_hash=payload_hash
    )
    with open(filename, "w") as ajax_log_fp:
        ajax_log_fp.write(encoded_payload)


def log_lms_integration(payload):
    '''
    Log LMS integration payloads for long-term analysis.

    Captures LMS data like rosters, courses, and grades so we can
    review historical context beyond immediate runtime.
    '''
    user = payload.get(learning_observer.constants.USER, {}) or {}
    user_domain = learning_observer.util.get_domain_from_email(user.get('email'))
    should_log = settings.pmss_settings.logging_enabled(
        types=['lms_integration'],
        attributes={'domain': user_domain}
    )
    if not should_log:
        return
    payload.setdefault('timestamp', datetime.datetime.utcnow().isoformat())
    encoded_payload = json.dumps(payload, sort_keys=True, default=str)
    log_event(encoded_payload, filename="lms_integration", preencoded=True)


def close_logfile(filename):
    # remove the file from the dict storing open log files and close it
    if filename not in files:
        # If we logged no events, the file was never created, so the code
        # below fails. This forces the file to be created, and marked
        # as empty, which also gives some logging of something having
        # happened.
        #
        # I don't know if this is the right sentinel to use. Empty file? A
        # single event of some kind?
        log_event("[Empty log file -- no events captured]", preencoded=True, filename=filename)
    old_file = files.pop(filename)
    old_file.close()
