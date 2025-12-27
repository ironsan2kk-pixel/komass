@echo off
echo ========================================
echo KOMAS Chat 25 - Running Tests
echo ========================================
echo.

cd /d "%~dp0"

if not exist "backend\venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

cd backend
call venv\Scripts\activate.bat

set PYTHONPATH=%CD%\app
cd ..

python run_tests.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Tests FAILED
    pause
    exit /b 1
)

echo.
echo All tests completed!
pause
