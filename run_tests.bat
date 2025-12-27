@echo off
echo ========================================
echo KOMAS v4.0 - Running Unit Tests
echo Chat #35: Score Multi-TF
echo ========================================
echo.

cd /d "%~dp0"

REM Activate venv from backend
cd backend
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run install.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

REM Set Python path to services directory
set PYTHONPATH=%CD%\app;%CD%\app\services

echo Installing test dependencies...
pip install pytest pytest-asyncio --quiet

echo.
echo Running tests...
echo.

REM Go back to root and run pytest
cd ..
python -m pytest tests/test_multi_tf_loader.py -v --tb=short --ignore=tests/test_sl_from_mid.py --ignore=tests/test_dominant.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================
    echo Tests FAILED
    echo ============================================
    pause
    exit /b 1
)

echo.
echo ============================================
echo All tests PASSED!
echo ============================================
pause
