@echo off
echo ========================================
echo KOMAS Dominant SL Modes - Test Runner
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

cd ..
python run_tests.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Some tests FAILED
    pause
    exit /b 1
)

echo.
echo All tests completed!
pause
