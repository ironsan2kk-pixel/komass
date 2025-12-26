@echo off
chcp 65001 >nul
echo ============================================
echo Testing TRG Backtest Engine
echo ============================================

cd /d "%~dp0"

echo Running tests...

REM Activate venv if exists
if exist "backend\venv\Scripts\activate.bat" (
    call backend\venv\Scripts\activate.bat
)

python test_backtest.py

echo.
echo ============================================
echo Tests completed!
echo ============================================
pause
