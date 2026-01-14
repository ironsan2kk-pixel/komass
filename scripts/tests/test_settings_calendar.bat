@echo off
chcp 65001 >nul
echo ============================================
echo   KOMAS - Testing Settings and Calendar API
echo ============================================
echo.

cd /d "%~dp0"

echo [1/2] Installing test dependencies...
call backend\venv\Scripts\activate.bat
pip install pytest httpx psutil cryptography beautifulsoup4 pydantic --quiet

echo.
echo [2/2] Running tests...
set PYTHONPATH=%cd%
python -m pytest tests/test_settings_calendar.py -v --tb=short

echo.
echo Done!
pause
