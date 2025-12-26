@echo off
chcp 65001 >nul

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║            KOMAS TRADING SERVER v3.0 - STARTING              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check if already running
tasklist /FI "WINDOWTITLE eq Komas Backend*" 2>NUL | find /I /N "cmd.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [WARNING] Backend may already be running!
    echo           Use stop.bat first if you want to restart.
    echo.
)

:: Start Backend
echo [1/2] Starting Backend...
start "Komas Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak >nul
echo       Backend starting on http://localhost:8000

:: Start Frontend
echo [2/2] Starting Frontend...
start "Komas Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"
timeout /t 2 /nobreak >nul
echo       Frontend starting on http://localhost:5173

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                      SERVER STARTED                           ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  Backend:  http://localhost:8000                              ║
echo ║  Frontend: http://localhost:5173                              ║
echo ║  API Docs: http://localhost:8000/docs                         ║
echo ║  Health:   http://localhost:8000/health                       ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  To stop:  run stop.bat                                       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Open browser
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo Press any key to close this window...
pause >nul
