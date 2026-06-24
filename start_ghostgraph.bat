@echo off
echo ===================================================
echo             Starting GhostGraph
echo ===================================================
echo.

echo [1/2] Starting Backend Server...
start "GhostGraph - Backend" cmd /k "cd backend && .\.venv\Scripts\activate && python main.py"

echo [2/2] Starting Frontend Dashboard...
start "GhostGraph - Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo Both services are starting up!
echo.
echo The Frontend Dashboard will be available at: http://localhost:5173
echo The Backend API is running on: http://127.0.0.1:8000
echo.
echo Make sure Ollama is running in the background on this Windows machine!
echo ===================================================
pause
