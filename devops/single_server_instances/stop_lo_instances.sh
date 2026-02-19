#!/bin/bash

# === Config ===
LOGFILE_DEST="/var/log/learning_observer"
PIDFILE_DIR="$LOGFILE_DEST/pids"
SCRIPT_NAME="learning_observer"

# === Stop All Servers ===
echo "Stopping all $SCRIPT_NAME servers..."

if [ ! -d "$PIDFILE_DIR" ]; then
    echo "PID directory not found. Nothing to stop."
    exit 1
fi

for PIDFILE in "$PIDFILE_DIR"/*.pid; do
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "Stopping PID $PID from $PIDFILE"
            kill "$PID"
        else
            echo "PID $PID not running, skipping."
        fi
        rm -f "$PIDFILE"
    fi
done

echo "✅ All servers stopped."
