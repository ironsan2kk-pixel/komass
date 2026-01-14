@echo off
chcp 65001 >nul
echo ============================================
echo   KOMAS Chat #19 - Bug Fix + Data Caching
echo ============================================
echo.

REM Create backup directory
echo Creating backup...
if not exist "backup_chat19" mkdir backup_chat19

REM Backup existing files
if exist "backend\app\api\indicator_routes.py" (
    copy "backend\app\api\indicator_routes.py" "backup_chat19\" >nul
    echo   [OK] Backed up indicator_routes.py
)
if exist "frontend\src\pages\Indicator.jsx" (
    copy "frontend\src\pages\Indicator.jsx" "backup_chat19\" >nul
    echo   [OK] Backed up Indicator.jsx
)
if exist "frontend\src\components\Indicator\SettingsSidebar.jsx" (
    copy "frontend\src\components\Indicator\SettingsSidebar.jsx" "backup_chat19\" >nul
    echo   [OK] Backed up SettingsSidebar.jsx
)
if exist "frontend\src\components\Indicator\StatsPanel.jsx" (
    copy "frontend\src\components\Indicator\StatsPanel.jsx" "backup_chat19\" >nul
    echo   [OK] Backed up StatsPanel.jsx
)

echo.
echo Installing new files...

REM Copy backend file
copy /Y "indicator_routes.py" "backend\app\api\indicator_routes.py" >nul
echo   [OK] indicator_routes.py - LRU Cache added

REM Copy frontend files
copy /Y "Indicator.jsx" "frontend\src\pages\Indicator.jsx" >nul
echo   [OK] Indicator.jsx - includes bug fixed, cache UI added

copy /Y "SettingsSidebar.jsx" "frontend\src\components\Indicator\SettingsSidebar.jsx" >nul
echo   [OK] SettingsSidebar.jsx - Cache section added

copy /Y "StatsPanel.jsx" "frontend\src\components\Indicator\StatsPanel.jsx" >nul
echo   [OK] StatsPanel.jsx - Cache banner added

echo.
echo ============================================
echo   Installation Complete!
echo ============================================
echo.
echo NEW FEATURES:
echo   - Bug Fix: "Cannot read properties of undefined (reading 'includes')"
echo   - LRU Cache: 100 entries max, 5 min TTL
echo   - Force Recalculate button (orange)
echo   - Cache status indicator in header
echo   - Cache statistics in sidebar
echo   - Cache banner in Stats tab
echo.
echo CACHE ENDPOINTS:
echo   GET  /api/indicator/cache-stats
echo   POST /api/indicator/cache-clear
echo.
echo Please restart the server to apply changes.
echo.
pause
