@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║           KOMAS TRADING SERVER v3.0 - INSTALLATION           ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.11+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo       Python %PYVER% found

:: Check Node.js
echo [2/6] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found! Please install Node.js 20+
    echo Download: https://nodejs.org/
    pause
    exit /b 1
)
for /f %%i in ('node --version') do set NODEVER=%%i
echo       Node.js %NODEVER% found

:: Create directories
echo [3/6] Creating directories...
if not exist "data" mkdir data
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups
echo       Directories created

:: Backend setup
echo [4/6] Setting up Backend...
cd backend

if exist "venv" (
    echo       Removing old virtual environment...
    rmdir /s /q venv
)

echo       Creating virtual environment...
python -m venv venv

echo       Activating virtual environment...
call venv\Scripts\activate.bat

echo       Installing Python dependencies...
pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt

if errorlevel 1 (
    echo [ERROR] Failed to install Python dependencies!
    pause
    exit /b 1
)

deactivate
cd ..
echo       Backend setup complete

:: Frontend setup
echo [5/6] Setting up Frontend...
cd frontend

if exist "node_modules" (
    echo       Removing old node_modules...
    rmdir /s /q node_modules
)

echo       Installing npm dependencies...
call npm install

if errorlevel 1 (
    echo [ERROR] Failed to install npm dependencies!
    pause
    exit /b 1
)

cd ..
echo       Frontend setup complete

:: Final
echo [6/6] Installation complete!
echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    INSTALLATION COMPLETE                      ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  To start the server, run: start.bat                         ║
echo ║                                                               ║
echo ║  Backend:  http://localhost:8000                              ║
echo ║  Frontend: http://localhost:5173                              ║
echo ║  API Docs: http://localhost:8000/docs                         ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
pause
