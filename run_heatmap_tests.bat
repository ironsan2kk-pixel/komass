@echo off
echo ========================================
echo Running Heatmap Tests
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

echo Running tests...
python -m pytest "%~dp0tests\test_optimizer_heatmap.py" -v --tb=short

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
echo All tests passed!
echo ========================================
pause
