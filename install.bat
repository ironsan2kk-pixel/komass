@echo off
chcp 65001 >nul
echo ========================================
echo   KOMAS Frontend v3.5 - Installation
echo ========================================
echo.

cd /d "%~dp0frontend"

echo [1/2] Checking Node.js...
node -v >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js not found!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)
echo OK: Node.js found

echo.
echo [2/2] Installing dependencies...
call npm install

if errorlevel 1 (
    echo.
    echo ERROR: npm install failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Installation complete!
echo ========================================
echo.
echo To start: run start.bat
echo.
pause
