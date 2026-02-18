#!/bin/bash
echo "--- Starting Templo Atelier vFinal (Local) ---"

# 1. Fix Permissions (just in case Docker messed them up)
echo "[1/3] Setting Permissions..."
chmod 777 studio.db* 2>/dev/null

# 2. Check Virtual Environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual Environment (venv) not found!"
    echo "Please run: python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 3. Start Server
echo "[2/3] Starting Uvicorn Server on port 8000..."
echo "✅ Access Dashboard at: http://localhost:8000"
echo "✅ API Docs at: http://localhost:8000/docs"
echo "-----------------------------------------------"

./venv/bin/uvicorn src.dashboard_api.main:app --reload --port 8000
