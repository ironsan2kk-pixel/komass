@echo off
setlocal enabledelayedexpansion

echo ========================================
echo Testing Dominant Indicator Module
echo ========================================
echo.

cd /d "%~dp0"

if not exist "backend\app\indicators\dominant.py" (
    echo ERROR: dominant.py not found
    echo Make sure you extracted the archive correctly
    pause
    exit /b 1
)

cd backend

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Run install.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Running tests...
echo.

set PYTHONPATH=%CD%\app

python -c "from indicators.dominant import calculate_dominant; print('Import test: OK')"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Import failed
    pause
    exit /b 1
)

echo.
python "%~dp0run_tests.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Some tests FAILED
    pause
    exit /b 1
)

echo.
echo ========================================
echo All tests passed!
echo ========================================
pause
