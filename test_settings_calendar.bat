@echo off
echo ============================================
echo   KOMAS - Testing Settings and Calendar API
echo ============================================
echo.

cd /d "%~dp0"

echo [1/2] Installing test dependencies...
call venv\Scripts\activate
pip install pytest httpx psutil cryptography beautifulsoup4 --quiet

echo.
echo [2/2] Running tests...
python -m pytest tests/test_settings_calendar.py -v --tb=short

echo.
echo Done!
pause
