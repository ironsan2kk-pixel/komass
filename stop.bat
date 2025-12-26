@echo off
chcp 65001 >nul

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║            KOMAS TRADING SERVER v3.0 - STOPPING              ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Kill Backend window
echo [1/3] Stopping Backend...
taskkill /FI "WINDOWTITLE eq Komas Backend*" /F >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo       Backend stopped
) else (
    echo       Backend was not running
)

:: Kill Frontend window
echo [2/3] Stopping Frontend...
taskkill /FI "WINDOWTITLE eq Komas Frontend*" /F >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    echo       Frontend stopped
) else (
    echo       Frontend was not running
)

:: Kill any remaining uvicorn/node processes on ports
echo [3/3] Cleaning up ports...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000"') do (
    taskkill /PID %%a /F >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173"') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo       Ports 8000 and 5173 released

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                      SERVER STOPPED                           ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

timeout /t 3
