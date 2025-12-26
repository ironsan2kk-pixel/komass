@echo off
chcp 65001 >nul
echo ============================================
echo    KOMAS TRG FILTERS - TEST
echo ============================================
echo.

cd /d "%~dp0"

REM Check if we're in the right directory
if not exist "backend\app\indicators\plugins\trg\filters\test_filters.py" (
    echo ERROR: test_filters.py not found!
    echo Make sure you're in the komas directory
    pause
    exit /b 1
)

REM Activate venv if exists
if exist "backend\venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call backend\venv\Scripts\activate.bat
)

echo.
echo Running tests...
echo.

cd backend\app\indicators\plugins\trg\filters
python test_filters.py

echo.
echo ============================================
if %ERRORLEVEL% EQU 0 (
    echo    ALL TESTS PASSED!
) else (
    echo    SOME TESTS FAILED
)
echo ============================================
echo.

pause
