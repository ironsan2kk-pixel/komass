@echo off
echo ========================================
echo Installing Chat #28 - Trade Levels Fix
echo ========================================
echo.

echo Copying backend files...
copy /Y "backend\app\indicators\dominant.py" "..\backend\app\indicators\dominant.py"
copy /Y "backend\app\api\indicator_routes.py" "..\backend\app\api\indicator_routes.py"

echo Copying frontend files...
copy /Y "frontend\src\pages\Indicator.jsx" "..\frontend\src\pages\Indicator.jsx"
copy /Y "frontend\src\components\Indicator\SettingsSidebar.jsx" "..\frontend\src\components\Indicator\SettingsSidebar.jsx"
copy /Y "frontend\src\components\Indicator\StatsPanel.jsx" "..\frontend\src\components\Indicator\StatsPanel.jsx"

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo FIXES:
echo - StatsPanel props fix (stats not statistics)
echo - TP/SL/Entry lines for ALL trades
echo - Fixed Stop toggle for Dominant
echo.
pause
