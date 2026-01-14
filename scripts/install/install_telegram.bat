@echo off
chcp 65001 >nul
echo ============================================
echo  KOMAS - Install Telegram Notifications
echo ============================================
echo.

cd /d "%~dp0"
cd backend

echo Activating venv...
call venv\Scripts\activate

echo Installing python-telegram-bot...
pip install python-telegram-bot==20.7

echo.
echo ✓ Done!
echo.
pause
