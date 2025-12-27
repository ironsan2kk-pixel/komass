@echo off
echo ========================================
echo Seeding 125 Dominant Presets
echo ========================================
echo.

cd /d "%~dp0"
cd backend

call venv\Scripts\activate.bat

echo Running migration...
echo.

python -m app.migrations.seed_dominant_presets

echo.
echo ========================================
echo Done! Check API: GET /api/presets/dominant/list
echo ========================================
pause
