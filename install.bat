@echo off
chcp 65001 >nul
echo ============================================
echo  KOMAS TELEGRAM NOTIFICATIONS - INSTALL
echo ============================================
echo.

echo [1/3] Installing Python dependencies...
cd backend
if not exist venv (
    python -m venv venv
)
call venv\Scripts\activate
pip install python-telegram-bot==20.7 --quiet
echo      ✓ python-telegram-bot installed
pip install pytest pytest-asyncio --quiet
echo      ✓ pytest installed

echo.
echo [2/3] Creating data directory...
if not exist data mkdir data
echo      ✓ data directory ready

echo.
echo [3/3] Running tests...
cd ..
call run_tests.bat

echo.
echo ============================================
echo  INSTALLATION COMPLETE!
echo ============================================
echo.
echo Next steps:
echo   1. Get bot token from @BotFather
echo   2. Configure in Settings → Notifications
echo   3. Send /start to your bot to get chat ID
echo.
pause
