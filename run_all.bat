@echo off
echo ========================================================
echo        AEROS Atmospheric System Launcher
echo ========================================================
echo Starting Backend (FastAPI on http://localhost:8000)...
start "AEROS Backend (FastAPI :8000)" cmd /k "python -m uvicorn aeros.api.main:app --host 0.0.0.0 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo Starting Frontend (Vite on http://localhost:3000)...
start "AEROS Frontend (Vite :3000)" cmd /k "cd frontend && npm run dev"

timeout /t 3 /nobreak >nul

echo Opening browser at http://localhost:3000 ...
start http://localhost:3000

echo.
echo Both servers have been launched!
echo Keep both terminal windows open while presenting.
echo ========================================================
pause
