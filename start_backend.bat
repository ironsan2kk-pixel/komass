@echo off
echo ========================================
echo KOMAS - Starting Backend Server
echo ========================================
echo.

cd /d %~dp0\backend

echo Starting Uvicorn server on http://localhost:8000
echo Press Ctrl+C to stop
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
