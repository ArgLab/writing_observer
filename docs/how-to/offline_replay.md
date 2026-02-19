# Offline replay with study logs

This guide covers how to replay Learning Observer study logs for offline analysis using `learning_observer/offline.py`.

## Prerequisites

- Install dependencies so the Learning Observer package and its modules are importable
- Change into the Learning Observer directory for proper discoverability of files

```bash
pip install -e learning_observer/
cd learning_observer/
```

- Collect the study logs you want to replay. Study logs are produced with a `.study.log` suffix (optionally `.gz` when compressed). They include replay metadata that the offline pipeline expects; do **not** use the raw `.log` files.

## Processing a single study log file

Use the helper functions in `learning_observer/offline.py` to initialize the environment and process a file. The examples below assume you are running them from the repository root.

```bash
python - <<'PY'
import asyncio
from learning_observer import offline

# Prepare the in-memory KVS and reducers for offline replay
offline.init('creds.yaml')

# TODO: Offline replay currently initializes PMSS with default rulesets only.
# If you need custom `.pmss` overlays or alternate YAML files, update the
# offline initializer to accept ruleset paths.


# Replace this path with the study log you want to replay
log_path = "/path/to/your/session.study.log"

async def main():
    processed, source, user = await offline.process_file(file_path=log_path)
    print(f"Processed {processed} events from {source} as user {user}")

asyncio.run(main())
PY
```

- `process_file` only accepts study logs ending in `.study.log` or `.study.log.gz` and will reject other log types.
- If you do not provide a `userid`, a random safe username is generated to avoid inadvertently reusing PII from the log.

## Processing all study logs in a directory

To replay multiple study logs, point `process_dir` at a directory. It automatically filters to `*.study.log` and `*.study.log.gz` files.

```bash
python - <<'PY'
import asyncio
from learning_observer import offline

offline.init('creds.yaml')

async def main():
    files, events = await offline.process_dir("/path/to/study/logs")
    print(f"Processed {events} events across {files} study logs")

asyncio.run(main())
PY
```

## Resetting state between runs

Offline processing stores data in the in-memory key-value store (KVS). To clear previously replayed events before another run, call `offline.reset()`:

```bash
python - <<'PY'
import asyncio
from learning_observer import offline

offline.init('creds.yaml')

async def main():
    await offline.reset()
    print("KVS cleared")

asyncio.run(main())
PY
```
