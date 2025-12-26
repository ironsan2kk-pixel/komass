@echo off
chcp 65001 >nul
title Komas - Install Core Dependencies

echo ============================================================
echo   KOMAS TRADING SERVER - Install Core Dependencies
echo ============================================================
echo.

cd /d "%~dp0"

:: Create backend folder if not exists
if not exist "backend" mkdir backend
if not exist "backend\app" mkdir backend\app
if not exist "data" mkdir data
if not exist "logs" mkdir logs

cd backend

echo [1/4] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Install Python 3.11+
    pause
    exit /b 1
)

echo.
echo [2/4] Setting up virtual environment...
if exist "venv\Scripts\activate.bat" (
    echo Virtual environment exists
    call venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Virtual environment created
)

echo.
echo [3/4] Creating requirements.txt if needed...
if not exist "requirements.txt" (
    echo # Komas Core Dependencies> requirements.txt
    echo sqlalchemy==2.0.23>> requirements.txt
    echo aiosqlite==0.19.0>> requirements.txt
    echo fastapi==0.104.1>> requirements.txt
    echo uvicorn[standard]==0.24.0>> requirements.txt
    echo pydantic==2.5.2>> requirements.txt
    echo Created requirements.txt
)

echo.
echo [4/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Trying direct install...
    pip install sqlalchemy aiosqlite fastapi uvicorn pydantic
)

echo.
echo ============================================================
echo   SUCCESS! Core dependencies installed
echo ============================================================
echo.
echo Installed packages:
pip show sqlalchemy 2>nul | findstr "Name Version"
pip show aiosqlite 2>nul | findstr "Name Version"
pip show fastapi 2>nul | findstr "Name Version"
echo.
echo Next: run start_backend.bat or test_database.bat
echo.

pause
