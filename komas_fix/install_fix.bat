@echo off
echo ========================================
echo KOMAS Dominant Presets Fix - Installer
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Copy preset_routes_v3.py...
copy /Y "backend\app\api\preset_routes_v3.py" "..\backend\app\api\preset_routes_v3.py"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to copy preset_routes_v3.py
    pause
    exit /b 1
)
echo OK: preset_routes_v3.py copied

echo.
echo Step 2: Copy main.py...
copy /Y "backend\app\main.py" "..\backend\app\main.py"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to copy main.py
    pause
    exit /b 1
)
echo OK: main.py copied

echo.
echo ========================================
echo Installation complete!
echo.
echo NEXT STEPS:
echo 1. Restart the backend server
echo 2. Generate Dominant presets if needed:
echo    POST /api/presets/generate/dominant
echo    or use SSE: GET /api/presets/generate/dominant-stream
echo ========================================
pause
