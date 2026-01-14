@echo off
chcp 65001 >nul

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║            KOMAS TRADING SERVER v3.0 - UPDATE                ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

:: Update Python dependencies
echo [1/3] Updating Python dependencies...
cd backend
call venv\Scripts\activate.bat

echo       Upgrading pip...
pip install --upgrade pip >nul 2>&1

echo       Updating packages...
pip install -r requirements.txt --upgrade

if errorlevel 1 (
    echo [ERROR] Failed to update Python dependencies!
    deactivate
    cd ..
    pause
    exit /b 1
)

deactivate
cd ..
echo       Python dependencies updated

:: Update npm dependencies
echo [2/3] Updating npm dependencies...
cd frontend

echo       Checking for updates...
call npm update

if errorlevel 1 (
    echo [ERROR] Failed to update npm dependencies!
    cd ..
    pause
    exit /b 1
)

cd ..
echo       npm dependencies updated

:: Git pull (if git repo)
echo [3/3] Checking for code updates...
git --version >nul 2>&1
if "%ERRORLEVEL%"=="0" (
    if exist ".git" (
        echo       Pulling latest changes...
        git pull
    ) else (
        echo       Not a git repository, skipping
    )
) else (
    echo       Git not installed, skipping
)

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                      UPDATE COMPLETE                          ║
echo ╠══════════════════════════════════════════════════════════════╣
echo ║  Restart the server to apply updates: stop.bat + start.bat   ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
pause
