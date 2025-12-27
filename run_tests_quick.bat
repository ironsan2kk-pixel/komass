@echo off
echo ========================================
echo KOMAS Quick Test - Dominant Filters
echo ========================================
echo.

cd /d "%~dp0"
cd backend

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

pip show pytest >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Installing pytest...
    pip install pytest -q
)

set PYTHONPATH=%CD%\app

cd /d "%~dp0"

echo Running quick filter tests...
echo.

python -m pytest tests/test_dominant.py -v -k "Filter" --tb=line

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Quick test FAILED
    pause
    exit /b 1
)

echo.
echo Quick test PASSED!
pause
