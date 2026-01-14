@echo off
echo ========================================
echo KOMAS - Signal Bot for Telegram/Cornix
echo ========================================
echo.

cd /d %~dp0\backend

echo Starting Signal Generator...
echo Signals will be sent to Telegram for Cornix
echo.

python -m app.signal_bot

pause
