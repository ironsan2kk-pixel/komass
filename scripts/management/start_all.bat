@echo off
chcp 65001 >nul
echo ========================================
echo   KOMAS Trading Server v3.5
echo ========================================
echo.

echo Starting Backend...
start "KOMAS Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

timeout /t 3 >nul

echo Starting Frontend...
start "KOMAS Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo ========================================
echo.
echo Close this window or press any key to exit.
pause >nul
