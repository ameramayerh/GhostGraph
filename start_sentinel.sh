#!/bin/bash
echo "==================================================="
echo "            Starting GhostGraph (Kali Linux)"
echo "==================================================="
echo ""

echo "Since your Ollama module is on Windows, we need to connect to it."
read -p "Please enter your Windows Host IP address (e.g. 192.168.1.100). Or press Enter for localhost: " WINDOWS_IP

if [ -n "$WINDOWS_IP" ]; then
    export OLLAMA_HOST="http://$WINDOWS_IP:11434"
    echo "[+] Ollama Host set to: $OLLAMA_HOST"
    echo "IMPORTANT: Make sure your Windows Ollama is configured to listen on 0.0.0.0, not just localhost!"
else
    echo "[+] Using local Ollama on Kali (localhost)"
fi

echo ""
echo "[1/2] Starting Backend Server in background..."
cd backend
if [ ! -d ".venv" ]; then
    echo "Creating python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi
nohup python3 main.py > backend.log 2>&1 &
BACKEND_PID=$!
cd ..

echo "[2/2] Starting Frontend Dashboard in background..."
cd frontend
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi
nohup npm run dev -- --host > frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo ""
echo "==================================================="
echo "Services started!"
echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "To stop them later, run: kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "The Frontend Dashboard will be available at: http://localhost:5173"
echo "The Backend API is running on: http://127.0.0.1:8000"
echo "==================================================="
