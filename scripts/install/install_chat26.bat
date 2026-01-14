@echo off
echo ========================================
echo KOMAS Chat #26 - Dominant Presets DB
echo ========================================
echo.

cd /d "%~dp0"

echo Checking files...
echo.

if exist "backend\app\api\preset_routes.py" (
    echo [OK] preset_routes.py
) else (
    echo [MISSING] preset_routes.py
)

if exist "backend\app\database\presets_db.py" (
    echo [OK] presets_db.py
) else (
    echo [MISSING] presets_db.py
)

if exist "backend\app\models\preset_models.py" (
    echo [OK] preset_models.py
) else (
    echo [MISSING] preset_models.py
)

if exist "backend\app\migrations\seed_dominant_presets.py" (
    echo [OK] seed_dominant_presets.py
) else (
    echo [MISSING] seed_dominant_presets.py
)

if exist "backend\app\main.py" (
    echo [OK] main.py (with preset_routes)
) else (
    echo [MISSING] main.py
)

echo.
echo ========================================
echo All files in place after extraction!
echo ========================================
echo.
echo To seed 125 Dominant presets, run:
echo.
echo   cd backend
echo   venv\Scripts\activate
echo   python -m app.migrations.seed_dominant_presets
echo.
echo Or call API after starting server:
echo   POST http://localhost:8000/api/presets/dominant/seed
echo.
pause
