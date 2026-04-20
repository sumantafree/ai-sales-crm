#!/bin/bash
# Stop both backend and frontend

for SERVICE in crm-backend crm-frontend; do
    PID_FILE="$HOME/logs/$SERVICE.pid"
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        kill "$PID" 2>/dev/null && echo "Stopped $SERVICE (PID: $PID)"
        rm -f "$PID_FILE"
    else
        echo "$SERVICE was not running"
    fi
done
