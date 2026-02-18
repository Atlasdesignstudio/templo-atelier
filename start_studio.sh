#!/bin/bash

# Function to kill background processes on exit
cleanup() {
    echo "Shutting down Templo Atelier..."
    kill $(jobs -p) 2>/dev/null
    exit
}

trap cleanup SIGINT

echo "--- 🏛️  Launching Templo Atelier (2026) ---"

# 1. Activate Virtual Environment
source venv/bin/activate

# 2. Start Backend
echo "[1/3] Starting Backend API (Port 8000)..."
uvicorn src.dashboard_api.main:app --reload --port 8000 &
BACKEND_PID=$!

# Wait for backend to be ready
sleep 3

# 3. Start Frontend
echo "[2/3] Starting Frontend UI (Port 3000)..."
cd src/dashboard_ui
npm run dev &
FRONTEND_PID=$!
cd ../..

# 4. Start Drive Watcher
echo "[3/3] Starting Drive Watcher (polls every 5 min)..."
python -m src.operative_core.drive_watcher &
WATCHER_PID=$!

echo ""
echo "--- ✅ Templo Atelier Online ---"
echo "Mission Control:  http://localhost:3000"
echo "API Docs:         http://localhost:8000/docs"
echo "Drive Watcher:    Polling Inbox every 5 min"
echo "--------------------------------"
echo "Press Ctrl+C to stop all services."

wait

