@echo off
echo ========================================
echo KOMAS v4.0 - Fix Imports and Run Tests
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Fixing signal_score.py imports...
cd backend
call venv\Scripts\activate.bat
cd ..
python fix_imports.py

if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Fix script returned error
)

echo.
echo Step 2: Running tests...
echo.

cd backend
set PYTHONPATH=%CD%\app;%CD%\app\services

cd ..
python -m pytest tests/test_multi_tf_loader.py -v --tb=short

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================
    echo Tests FAILED
    echo ============================================
) else (
    echo.
    echo ============================================
    echo All tests PASSED!
    echo ============================================
)

pause
