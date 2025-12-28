@echo off
echo ========================================
echo KOMAS v4 - Protection Filters Tests
echo Chat #42
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

echo Running protection filter tests...
echo.

python -m pytest "%~dp0tests\test_protection_filters.py" -v --tb=short

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo TESTS FAILED
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo ALL TESTS PASSED
echo ========================================
pause
