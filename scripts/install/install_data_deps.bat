@echo off
chcp 65001 >nul
echo ========================================
echo   Komas Data Module - Install Dependencies
echo ========================================
echo.

cd /d "%~dp0"
cd backend

if not exist "venv" (
    echo [!] Virtual environment not found!
    echo [!] Run install.bat first
    pause
    exit /b 1
)

echo [*] Activating virtual environment...
call venv\Scripts\activate

echo.
echo [*] Installing/updating data module dependencies...
echo.

REM Core dependencies for data module
pip install aiohttp>=3.9.0 --quiet
pip install pandas>=2.0.0 --quiet
pip install pyarrow>=14.0.0 --quiet
pip install pydantic>=2.0.0 --quiet
pip install pydantic-settings>=2.0.0 --quiet

echo.
echo [✓] Dependencies installed successfully!
echo.
echo [*] Installed packages:
pip show aiohttp | findstr "Name Version"
pip show pandas | findstr "Name Version"
pip show pyarrow | findstr "Name Version"

echo.
echo ========================================
echo   Installation Complete!
echo ========================================
pause
