@echo off
chcp 65001 >nul
echo ============================================
echo    KOMAS INDICATOR API - TEST RUNNER
echo ============================================
echo.

cd /d "%~dp0"
cd backend

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment not found!
    echo Run install.bat first.
    pause
    exit /b 1
)

echo Running tests...
echo.

python -m app.api.test_indicator_api

echo.
if %ERRORLEVEL% EQU 0 (
    echo [SUCCESS] All tests passed!
) else (
    echo [ERROR] Some tests failed!
)

echo.
pause
