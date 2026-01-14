@echo off
echo ========================================
echo KOMAS TRG Preset Seeder
echo 200 System Presets (8 x 5 x 5)
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

echo Running TRG preset seeder...
echo.

python "%~dp0scripts\seed_trg_presets.py" %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Seeding FAILED
    pause
    exit /b 1
)

echo.
echo Done!
pause
