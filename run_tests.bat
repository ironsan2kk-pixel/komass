@echo off
chcp 65001 > nul
echo ============================================
echo   KOMAS SIGNALS API - RUNNING TESTS
echo ============================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call backend\venv\Scripts\activate.bat

echo.
echo Checking pytest installation...
pip show pytest > nul 2>&1
if errorlevel 1 (
    echo Installing pytest...
    pip install pytest pytest-asyncio --quiet
)

echo.
echo Running Signals API tests...
echo.

python -m pytest tests/test_signals_api.py -v --tb=short

echo.
echo ============================================
if errorlevel 1 (
    echo   TESTS FAILED!
) else (
    echo   ALL TESTS PASSED!
)
echo ============================================
echo.
pause
