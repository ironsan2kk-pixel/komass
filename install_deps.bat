@echo off
echo ========================================
echo KOMAS - Installing Dependencies
echo ========================================
echo.

cd /d %~dp0

echo [1/2] Installing Python dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo [2/2] Installing Node.js dependencies...
cd ../frontend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node.js dependencies
    pause
    exit /b 1
)

echo.
echo ========================================
echo All dependencies installed successfully!
echo ========================================
pause
