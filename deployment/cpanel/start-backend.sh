#!/bin/bash
# ============================================================
# Start FastAPI backend (run this via SSH or cron)
# ============================================================

# Set your project path
PROJECT_DIR="$HOME/ai-sales-crm/backend"
LOG_FILE="$HOME/logs/crm-backend.log"
PID_FILE="$HOME/logs/crm-backend.pid"

mkdir -p "$HOME/logs"

# Kill any existing instance
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    kill "$OLD_PID" 2>/dev/null
    rm -f "$PID_FILE"
    echo "Stopped old backend (PID: $OLD_PID)"
fi

cd "$PROJECT_DIR"

# Activate virtual environment
source "$HOME/virtualenv/ai-sales-crm/bin/activate"

# Start FastAPI in background
nohup uvicorn main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 2 \
    >> "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
echo "✅ Backend started (PID: $!)"
echo "   Logs: $LOG_FILE"
