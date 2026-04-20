#!/bin/bash
# ============================================================
# Start Next.js frontend (run this via SSH or cron)
# ============================================================

PROJECT_DIR="$HOME/ai-sales-crm/frontend"
LOG_FILE="$HOME/logs/crm-frontend.log"
PID_FILE="$HOME/logs/crm-frontend.pid"

mkdir -p "$HOME/logs"

# Kill any existing instance
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    kill "$OLD_PID" 2>/dev/null
    rm -f "$PID_FILE"
    echo "Stopped old frontend (PID: $OLD_PID)"
fi

cd "$PROJECT_DIR"

# Start Next.js in background
nohup npm start \
    >> "$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
echo "✅ Frontend started (PID: $!)"
echo "   Logs: $LOG_FILE"
