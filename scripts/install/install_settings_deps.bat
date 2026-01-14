@echo off
chcp 65001 >nul
echo ============================================
echo   KOMAS - Install Settings Dependencies
echo ============================================
echo.

cd /d "%~dp0"

echo Activating virtual environment...
call backend\venv\Scripts\activate.bat

echo.
echo Installing new dependencies...
pip install cryptography httpx psutil pydantic

echo.
echo Done! Dependencies installed.
pause
