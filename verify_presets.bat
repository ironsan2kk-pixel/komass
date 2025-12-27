@echo off
echo ========================================
echo KOMAS Preset Verification
echo ========================================
echo.

cd /d "%~dp0"
cd backend

if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Run install.bat first
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
set PYTHONPATH=%CD%

echo Verifying TRG presets...
echo.

python "%~dp0scripts\seed_trg_presets.py" --verify

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Verification FAILED - some presets missing or invalid
    echo Run seed_trg_presets.bat --replace to fix
    pause
    exit /b 1
)

echo.
echo All presets verified!
pause
