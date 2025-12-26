@echo off
chcp 65001 >nul
echo ========================================
echo   KOMAS Frontend v3.5 - Starting
echo ========================================
echo.

cd /d "%~dp0frontend"

echo Starting Vite dev server on http://localhost:5173
echo Press Ctrl+C to stop
echo.

call npm run dev
