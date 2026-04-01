'''
Our goal is to be able to process the log file without spinning up
the Learning Observer. This is a simple script that will read the
log file and reduce the data as per our reducers.

It should be a lot easier to do development this way.
'''

import argparse
import asyncio
import json
import sys

import names

import learning_observer.settings
import learning_observer.stream_analytics
import learning_observer.module_loader
import learning_observer.incoming_student_event
import learning_observer.log_event
import learning_observer.kvs


# Supress printing of all the junk that happens during startup.
learning_observer.log_event.DEBUG_LOG_LEVEL = learning_observer.log_event.LogLevel.NONE

# Run from memory
learning_observer.settings.load_settings({
    "logging": {
        "debug_log_level": "NONE",
        "debug_log_destination": ["console"]
    },
    "kvs": {
        "type": "stub",
    },
    "config": {
        "run_mode": "dev"
    }
})


parser = argparse.ArgumentParser(
    description=__doc__.strip(),
    formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument("--logfiles", "-f", help="The log file(s) to process (separated by commas)")
parser.add_argument("--listfile", "-l", help="A file of paths of log files")

args = parser.parse_args()

reducers = learning_observer.module_loader.reducers()
learning_observer.kvs.kvs_startup_check()
learning_observer.stream_analytics.init()


if args.listfile is not None and args.logfiles is not None:
    print("You can only specify one of --listfile or --logfiles")
    parser.print_usage()
    sys.exit(1)
if args.listfile is None and args.logfiles is None:
    print("You must specify either --listfile or --logfiles")
    parser.print_usage()
    sys.exit(1)

if args.listfile is not None:
    files = open(args.listfile, 'r').readlines()
else:
    files = args.logfiles.split(',')


async def process_files(files):
    for file in files:
        print("Processing file: {}".format(file))
        # We use dummy names because:
        # (1) It is easier to test this way
        # (2) We want to protect ourselves from accidentally seeing PII
        pipeline = await learning_observer.incoming_student_event.student_event_pipeline({
            "source": "org.mitros.dynamic_assessment",
            "auth": {
                "user_id": names.get_first_name(),
                "safe_user_id": names.get_first_name()
            }
        })
        with open(file, 'r') as f:
            for line in f.readlines():
                try:
                    await pipeline(json.loads(line))
                except Exception:  # In case of an error, we'd like to know where it happened
                    print(line)
                    raise

kvs = learning_observer.kvs.KVS()
asyncio.run(process_files(files))
data = asyncio.run(kvs.dump())
print(json.dumps(data, indent=2))
