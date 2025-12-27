@echo off
echo ========================================
echo KOMAS Chat #36: Signal Score UI Tests
echo ========================================
echo.

cd /d "%~dp0"
cd backend

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
set PYTHONPATH=%CD%\app
python "%~dp0run_tests.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Tests FAILED
    pause
    exit /b 1
)

echo.
echo All tests passed!
pause
