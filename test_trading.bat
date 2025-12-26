@echo off
REM Test TRG Trading System
REM ======================

echo ============================================
echo Testing TRG Trading System
echo ============================================

cd /d "%~dp0"
cd backend

if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

echo.
echo Running tests...
echo.

python -m app.indicators.plugins.trg.test_trading

echo.
pause
