@echo off
echo ========================================
echo KOMAS - Starting Frontend Dev Server
echo ========================================
echo.

cd /d %~dp0\frontend

echo Starting Vite dev server on http://localhost:5173
echo Press Ctrl+C to stop
echo.

call npm run dev

pause
