@echo off
chcp 65001 >nul
echo ========================================
echo KOMAS Chat #48 - Complete Fix
echo ========================================
echo.
echo This patch includes:
echo  1. SSE GET endpoint for TRG optimization
echo  2. Preset Optimizer GET endpoint  
echo  3. Optimization button on Presets page
echo  4. PresetOptimizerModal component
echo.

cd /d "%~dp0"

echo Step 1: Creating backups...
if exist "backend\app\api\indicator_routes.py" (
    copy /y "backend\app\api\indicator_routes.py" "backend\app\api\indicator_routes.py.bak"
    echo    - indicator_routes.py backed up
)
if exist "backend\app\api\optimizer_routes.py" (
    copy /y "backend\app\api\optimizer_routes.py" "backend\app\api\optimizer_routes.py.bak"
    echo    - optimizer_routes.py backed up
)
if exist "frontend\src\pages\Presets.jsx" (
    copy /y "frontend\src\pages\Presets.jsx" "frontend\src\pages\Presets.jsx.bak"
    echo    - Presets.jsx backed up
)
echo.

echo Step 2: Copying backend files...
copy /y "patch\backend\app\api\indicator_routes.py" "backend\app\api\indicator_routes.py"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to copy indicator_routes.py
    pause
    exit /b 1
)
echo    - indicator_routes.py updated (SSE GET fix)

copy /y "patch\backend\app\api\optimizer_routes.py" "backend\app\api\optimizer_routes.py"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to copy optimizer_routes.py
    pause
    exit /b 1
)
echo    - optimizer_routes.py updated (Preset optimizer GET fix)
echo.

echo Step 3: Copying frontend files...
copy /y "patch\frontend\src\pages\Presets.jsx" "frontend\src\pages\Presets.jsx"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to copy Presets.jsx
    pause
    exit /b 1
)
echo    - Presets.jsx updated (Optimization button added)

if not exist "frontend\src\components\Presets" mkdir "frontend\src\components\Presets"
copy /y "patch\frontend\src\components\Presets\PresetOptimizerModal.jsx" "frontend\src\components\Presets\PresetOptimizerModal.jsx"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to copy PresetOptimizerModal.jsx
    pause
    exit /b 1
)
echo    - PresetOptimizerModal.jsx added
echo.

echo ========================================
echo SUCCESS! All files updated.
echo ========================================
echo.
echo What was fixed:
echo  1. TRG optimization (Indicator tab) - now works with EventSource
echo  2. Preset optimization (Presets page) - new feature
echo.
echo Next steps:
echo  1. Run: stop.bat
echo  2. Run: start.bat  
echo  3. Refresh browser
echo.
echo Test:
echo  - Go to Indicator tab, try TRG optimization
echo  - Go to Presets page, click orange "Optimization" button
echo.
pause
