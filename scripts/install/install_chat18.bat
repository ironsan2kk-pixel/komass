@echo off
chcp 65001 >nul
echo ========================================
echo  KOMAS Chat #18: Data Period Selection
echo ========================================
echo.

REM Check if we're in the right directory
if not exist "backend\app\api\indicator_routes.py" (
    echo [ERROR] Please run this script from the komas_indicator root directory!
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo [1/4] Backing up original files...
if not exist "backup_chat18" mkdir backup_chat18
copy "backend\app\api\indicator_routes.py" "backup_chat18\indicator_routes.py.bak" >nul 2>&1
copy "frontend\src\components\Indicator\SettingsSidebar.jsx" "backup_chat18\SettingsSidebar.jsx.bak" >nul 2>&1
copy "frontend\src\pages\Indicator.jsx" "backup_chat18\Indicator.jsx.bak" >nul 2>&1
copy "frontend\src\components\Indicator\StatsPanel.jsx" "backup_chat18\StatsPanel.jsx.bak" >nul 2>&1
echo [OK] Backups created in backup_chat18\

echo [2/4] Patching backend indicator_routes.py...
python patch_indicator_routes.py "backend\app\api\indicator_routes.py"
if errorlevel 1 (
    echo [ERROR] Failed to patch indicator_routes.py
    pause
    exit /b 1
)

echo [3/4] Updating frontend files...
copy /Y "SettingsSidebar.jsx" "frontend\src\components\Indicator\SettingsSidebar.jsx" >nul
if errorlevel 1 (
    echo [ERROR] Failed to copy SettingsSidebar.jsx
    pause
    exit /b 1
)
echo [OK] SettingsSidebar.jsx updated

copy /Y "Indicator.jsx" "frontend\src\pages\Indicator.jsx" >nul
if errorlevel 1 (
    echo [ERROR] Failed to copy Indicator.jsx
    pause
    exit /b 1
)
echo [OK] Indicator.jsx updated

copy /Y "StatsPanel.jsx" "frontend\src\components\Indicator\StatsPanel.jsx" >nul
if errorlevel 1 (
    echo [ERROR] Failed to copy StatsPanel.jsx
    pause
    exit /b 1
)
echo [OK] StatsPanel.jsx updated

echo [4/4] Installation complete!
echo.
echo ========================================
echo  Changes made:
echo  - Added data period selection to sidebar
echo  - Added quick period presets (1m, 3m, 6m, 1y, All)
echo  - Backend returns available data range
echo  - Stats panel shows used period
echo  - Period indicator in header
echo ========================================
echo.
echo Please restart the server to apply changes.
echo.
pause
