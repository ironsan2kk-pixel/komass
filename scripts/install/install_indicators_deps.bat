@echo off
REM ============================================
REM Komas Trading System - Install Indicators Dependencies
REM ============================================

echo.
echo [INDICATORS] Installing dependencies...
echo.

cd /d "%~dp0"
cd backend

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
) else (
    echo [WARNING] Virtual environment not found. Creating...
    python -m venv venv
    call venv\Scripts\activate
)

REM Install dependencies
pip install --break-system-packages numpy pandas

echo.
echo [INDICATORS] Dependencies installed successfully!
echo.
echo Required packages:
echo   - numpy (array operations)
echo   - pandas (DataFrame operations)
echo.
echo Note: These are likely already installed from previous modules.
echo.

pause
