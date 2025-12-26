@echo off
echo ============================================
echo   KOMAS - Install Settings/Calendar Dependencies
echo ============================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call venv\Scripts\activate

echo.
echo Installing new dependencies...
pip install cryptography httpx psutil beautifulsoup4

echo.
echo Done! Dependencies installed.
pause
