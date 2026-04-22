# Learning Observer — Instance Control Scripts

This directory contains two bash scripts to start and stop multiple instances of the `learning_observer` application.

## Files

* **`start_lo_instances.sh`** — Launches one or more instances of the app on sequential ports, creates log files, and stores process IDs in a PID directory.
* **`stop_lo_instances.sh`** — Stops all running instances recorded in the PID directory.

## Configuration

Before use, edit the scripts to match your system:

* `LEARNING_OBSERVER_LOC` — Path to your project code.
* `VIRTUALENV_PATH` — Path to your Python virtual environment.
* `LOGFILE_DEST` — Directory for logs (default `/var/log/learning_observer`).
* `START_PORT` — First port to use.
* `SCRIPT_NAME` — Command or Python file to run.

## Usage

Start instances (default: 1):

```bash
./start_lo_instances.sh
./start_lo_instances.sh 3   # start 3 instances
```

Stop all instances:

```bash
./stop_lo_instances.sh
```

Logs are saved in `LOGFILE_DEST`, and PIDs are stored in `LOGFILE_DEST/pids`.
You may need to change paths or permissions depending on your environment.

## Nginx Settings

The file `nginx.conf.example` provides a sample configration for Nginx when you start 4 instances of LO.
First, these settings split the incoming events and all other traffic between 2 upstream servers.
Each upstream server balances connections between 2 instances of Learning Observer.

```text
Incoming Request
       │
       ▼
+---------------+
|    NGINX      |
+---------------+
       │
       ▼
      Path starts
    with "/wsapi/in/"?
       ┌───────────────┐
    Yes│               │No
       ▼               ▼
+------------------+ +-----------------+
| wsapi_in_backend | | general_backend |
|                  | |                 |
+-------+----------+ +--------+--------+
        │                  │
   +----+----+        +----+----+   Balanced by least
   | App 1   |        | App 3   |   connections `least_conn`
   | :9001   |        | :9003   |
   +---------+        +---------+
   +----+----+        +----+----+
   | App 2   |        | App 4   |
   | :9002   |        | :9004   |
   +---------+        +---------+
```

Note: these are settings to add to your nginx configuration.
You will likely have other settings, such as ssl certificates.
