@echo off
echo ========================================
echo KOMAS Chat 25 - Installation
echo ========================================
echo.

cd /d "%~dp0"

echo Installing Chat 25: Dominant AI Resolution
echo.

echo Step 1: Backing up existing files...
if exist "backend\app\indicators\dominant.py" (
    copy /Y "backend\app\indicators\dominant.py" "backend\app\indicators\dominant.py.backup"
    echo   Backed up dominant.py
)

echo.
echo Step 2: Copying new files...

REM Create directories if needed
if not exist "backend\app\indicators" mkdir "backend\app\indicators"
if not exist "tests" mkdir "tests"

REM Copy indicator file
copy /Y "komas_chat25\backend\app\indicators\dominant.py" "backend\app\indicators\dominant.py"
echo   Copied dominant.py

REM Copy test files
copy /Y "komas_chat25\tests\test_dominant_ai_resolution.py" "tests\test_dominant_ai_resolution.py"
echo   Copied test_dominant_ai_resolution.py

REM Copy test runner
copy /Y "komas_chat25\run_tests.py" "run_tests.py"
echo   Copied run_tests.py

echo.
echo Step 3: Installation complete!
echo.
echo To test the installation, run: test_chat25.bat
echo.
pause
