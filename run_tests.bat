@echo off
echo ========================================
echo KOMAS v4.0 - Running Unit Tests
echo Chat #35: Score Multi-TF
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

echo Installing test dependencies...
pip install pytest pytest-asyncio --quiet

echo.
echo Running tests...
echo.
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
