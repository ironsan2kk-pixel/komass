@echo off
chcp 65001 >nul
echo ============================================
echo   KOMAS Chat #19 - Data Caching Install
echo ============================================
echo.

REM Check current directory
if not exist "backend" (
    echo ERROR: Run this script from komas_indicator root directory!
    echo Current directory should contain 'backend' and 'frontend' folders
    pause
    exit /b 1
)

echo [1/4] Backing up current files...
if not exist "backup_chat19" mkdir backup_chat19
if exist "backend\app\api\indicator_routes.py" (
    copy "backend\app\api\indicator_routes.py" "backup_chat19\indicator_routes.py.bak" >nul
    echo   - indicator_routes.py backed up
)
if exist "frontend\src\pages\Indicator.jsx" (
    copy "frontend\src\pages\Indicator.jsx" "backup_chat19\Indicator.jsx.bak" >nul
    echo   - Indicator.jsx backed up
)
if exist "frontend\src\components\Indicator\SettingsSidebar.jsx" (
    copy "frontend\src\components\Indicator\SettingsSidebar.jsx" "backup_chat19\SettingsSidebar.jsx.bak" >nul
    echo   - SettingsSidebar.jsx backed up
)
if exist "frontend\src\components\Indicator\StatsPanel.jsx" (
    copy "frontend\src\components\Indicator\StatsPanel.jsx" "backup_chat19\StatsPanel.jsx.bak" >nul
    echo   - StatsPanel.jsx backed up
)
echo.

echo [2/4] Installing backend files...
copy /Y "chat19_cache\indicator_routes.py" "backend\app\api\indicator_routes.py" >nul
echo   - indicator_routes.py installed (LRU Cache with TTL)
echo.

echo [3/4] Installing frontend files...
copy /Y "chat19_cache\Indicator.jsx" "frontend\src\pages\Indicator.jsx" >nul
echo   - Indicator.jsx installed (force_recalculate support)

copy /Y "chat19_cache\SettingsSidebar.jsx" "frontend\src\components\Indicator\SettingsSidebar.jsx" >nul
echo   - SettingsSidebar.jsx installed (cache section)

copy /Y "chat19_cache\StatsPanel.jsx" "frontend\src\components\Indicator\StatsPanel.jsx" >nul
echo   - StatsPanel.jsx installed (cache status banner)
echo.

echo [4/4] Done!
echo.
echo ============================================
echo   NEW FEATURES:
echo   - In-memory LRU cache (100 entries max)
echo   - TTL 5 minutes per entry
echo   - Force Recalculate button (orange)
echo   - Cache stats in sidebar
echo   - Cache status in header and stats
echo   - Clear cache button
echo ============================================
echo.
echo API Endpoints:
echo   GET  /api/indicator/cache-stats
echo   POST /api/indicator/cache-clear
echo.
echo Restart backend to apply changes!
echo.
pause
