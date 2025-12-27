@echo off
echo ========================================
echo KOMAS Test Runner - Dominant Filters
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

echo Checking pytest installation...
pip show pytest >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing pytest...
    pip install pytest -q
)

set PYTHONPATH=%CD%\app

echo.
echo Running Dominant indicator tests...
echo.

cd /d "%~dp0"
python -m pytest tests/test_dominant.py -v --tb=short

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo Some tests FAILED
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo All tests PASSED!
echo ========================================
pause
