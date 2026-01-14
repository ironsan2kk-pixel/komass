@echo off
echo ========================================
echo Komas Plugins Module - Installation
echo ========================================
echo.

cd /d "%~dp0"

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.11+
    pause
    exit /b 1
)

echo [1/3] Activating virtual environment...
if exist backend\venv\Scripts\activate.bat (
    call backend\venv\Scripts\activate.bat
) else (
    echo Creating virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate.bat
    cd ..
)

echo.
echo [2/3] Installing dependencies...
pip install pydantic fastapi --quiet

echo.
echo [3/3] Verifying installation...
cd backend
set PYTHONPATH=%cd%
python -c "from app.indicators.registry import PluginRegistry; print('Registry: OK')"
python -c "from app.indicators.loader import PluginLoader; print('Loader: OK')"
python -c "from app.api.plugins import router; print('API: OK')"
cd ..

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Files created:
echo   - app/indicators/registry.py (~580 lines)
echo   - app/indicators/loader.py (~710 lines)
echo   - app/indicators/__init__.py
echo   - app/api/plugins.py (~370 lines)
echo   - plugins/trg/manifest.json
echo.
echo Next steps:
echo   1. Add plugins router to main.py
echo   2. Implement TRG plugin (Chat #07)
echo.
pause
