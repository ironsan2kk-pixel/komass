@echo off
chcp 65001 >nul
echo ========================================
echo   KOMAS Backend - Installation
echo ========================================
echo.

cd /d "%~dp0backend"

echo [1/3] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.11+ from https://python.org/
    pause
    exit /b 1
)
echo OK: Python found

echo.
echo [2/3] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
)
echo OK: venv ready

echo.
echo [3/3] Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo ERROR: pip install failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Installation complete!
echo ========================================
echo.
echo To start: run start_backend.bat
echo.
pause
