@echo off
echo ============================================
echo   KOMAS Trading Server v3 - Frontend Setup
echo ============================================
echo.

cd /d "%~dp0"

echo [1/3] Checking Node.js...
where node >nul 2>nul
if errorlevel 1 (
    echo ERROR: Node.js not found! Install Node.js 18+
    pause
    exit /b 1
)
node -v

echo.
echo [2/3] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ERROR: npm install failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Done!
echo.
echo To start frontend run: npm run dev
echo.
pause
