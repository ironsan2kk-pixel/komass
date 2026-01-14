@echo off
echo ========================================
echo KOMAS - Seed Dominant Presets
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
set PYTHONPATH=%CD%\app

echo.
echo Seeding 125+ Dominant presets from GG Pine Script...
echo.

python -c "from app.migrations.seed_dominant_presets import seed_all_dominant_presets; result = seed_all_dominant_presets(); print(f'Created: {result.get(\"created\", 0)}'); print(f'Skipped: {result.get(\"skipped\", 0)}'); print(f'Errors: {result.get(\"errors\", 0)}')"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Seeding failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Dominant presets seeded successfully!
echo ========================================
pause
