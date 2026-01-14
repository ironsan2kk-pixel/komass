@echo off
REM ============================================
REM KOMAS Test Runner - Chat #21
REM Dominant Indicator Signal Tests
REM ============================================

echo ========================================
echo KOMAS Dominant Indicator Tests
echo ========================================
echo.

cd /d "%~dp0"
cd backend

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Run install.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
set PYTHONPATH=%CD%\app

cd ..

echo Running quick test...
python run_tests.py --quick

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Quick test FAILED
    pause
    exit /b 1
)

echo.
echo Running full test suite...
python run_tests.py -v

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
