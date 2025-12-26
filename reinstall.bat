@echo off
chcp 65001 >nul

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║          KOMAS TRADING SERVER v3.0 - REINSTALL               ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo This will completely reinstall all dependencies.
echo Your data and settings will be preserved.
echo.

set /p CONFIRM="Are you sure? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.

:: Stop running instances
echo [1/5] Stopping running instances...
call stop.bat >nul 2>&1
echo       Done

:: Remove Python venv
echo [2/5] Removing Python virtual environment...
if exist "backend\venv" (
    rmdir /s /q backend\venv
    echo       Removed backend\venv
) else (
    echo       No venv found
)

:: Remove node_modules
echo [3/5] Removing Node modules...
if exist "frontend\node_modules" (
    rmdir /s /q frontend\node_modules
    echo       Removed frontend\node_modules
) else (
    echo       No node_modules found
)

:: Clear cache
echo [4/5] Clearing cache...
if exist "frontend\.vite" rmdir /s /q frontend\.vite
if exist "backend\__pycache__" rmdir /s /q backend\__pycache__
if exist "backend\app\__pycache__" rmdir /s /q backend\app\__pycache__
for /d /r "backend" %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
echo       Cache cleared

:: Run install
echo [5/5] Running fresh installation...
echo.
call install.bat
