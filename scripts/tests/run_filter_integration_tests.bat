@echo off
echo ========================================
echo KOMAS v4.0 - Filter Integration Tests
echo Chat #43: Filters Integration
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

echo Running filter integration tests...
echo.

python "%~dp0run_filter_integration_tests.py" %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo Tests FAILED with error code %ERRORLEVEL%
    echo ========================================
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ========================================
echo All tests PASSED!
echo ========================================
pause
