@echo off
chcp 65001 > nul
echo ============================================
echo   KOMAS TRADING SERVER - REINSTALL
echo ============================================
echo.
echo WARNING: This will delete virtual environment!
echo.
set /p confirm="Are you sure? (y/n): "
if /i not "%confirm%"=="y" (
    echo Cancelled.
    pause
    exit /b 0
)

cd /d "%~dp0"

echo.
echo Stopping servers...
call stop.bat > nul 2>&1

echo.
echo Removing virtual environment...
if exist "backend\venv" (
    rmdir /s /q backend\venv
    echo     ✓ Virtual environment removed
)

echo.
echo Removing node_modules...
if exist "frontend\node_modules" (
    rmdir /s /q frontend\node_modules
    echo     ✓ Node modules removed
)

echo.
echo Starting fresh installation...
call install.bat

echo.
echo ============================================
echo   REINSTALL COMPLETE!
echo ============================================
echo.
