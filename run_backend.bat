@echo off
echo Starting AEROS Backend Server on http://localhost:8000 ...
python -m uvicorn aeros.api.main:app --host 0.0.0.0 --port 8000 --reload
pause
