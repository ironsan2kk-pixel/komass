@echo off
echo ========================================
echo Komas Plugins Module - Tests
echo ========================================
echo.

cd /d "%~dp0"

if exist backend\venv\Scripts\activate.bat (
    call backend\venv\Scripts\activate.bat
)

echo Running tests...
echo.

python test_plugins.py

echo.
pause
