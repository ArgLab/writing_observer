#!/bin/bash

# === Config ===
NUM_SERVERS=${1:-1}     # default 1 server instance
START_PORT=9001
LOGFILE_DEST="/var/log/learning_observer"
PIDFILE_DIR="$LOGFILE_DEST/pids"
LEARNING_OBSERVER_LOC="/path/to/your/code"
VIRTUALENV_PATH="/path/to/your/venv"
SCRIPT_NAME="learning_observer"

# Create log + pid dirs if they don't exist
mkdir -p "$LOGFILE_DEST"
mkdir -p "$PIDFILE_DIR"

# Timestamp for log grouping
LOG_DATE=$(date "+%m-%d-%Y--%H-%M-%S")

# === Start Servers ===
echo "Starting $NUM_SERVERS instances of $SCRIPT_NAME..."

cd "$LEARNING_OBSERVER_LOC"
source "$VIRTUALENV_PATH/bin/activate"

for ((i=0; i<NUM_SERVERS; i++)); do
    PORT=$((START_PORT + i))
    LOGFILE_NAME="$LOGFILE_DEST/${SCRIPT_NAME}_${LOG_DATE}_${PORT}.log"
    PIDFILE_NAME="$PIDFILE_DIR/${SCRIPT_NAME}_${PORT}.pid"

    echo "Starting server on port $PORT"
    echo "  -> Log: $LOGFILE_NAME"
    nohup python $SCRIPT_NAME --port $PORT > "$LOGFILE_NAME" 2>&1 &
    PROCESS_ID=$!
    echo $PROCESS_ID > "$PIDFILE_NAME"
    echo "  -> PID $PROCESS_ID logged to $PIDFILE_NAME"
done

echo "✅ All servers started."
echo "Run ./scripts/stop_lo_instances.sh to stop server processes."
