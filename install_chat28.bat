@echo off
echo ========================================
echo Installing Chat #28 Updates
echo ========================================
echo.

echo Copying backend files...
copy /Y "backend\app\indicators\dominant.py" "..\backend\app\indicators\dominant.py"
copy /Y "backend\app\api\indicator_routes.py" "..\backend\app\api\indicator_routes.py"

echo Copying frontend files...
copy /Y "frontend\src\pages\Indicator.jsx" "..\frontend\src\pages\Indicator.jsx"
copy /Y "frontend\src\components\Indicator\SettingsSidebar.jsx" "..\frontend\src\components\Indicator\SettingsSidebar.jsx"

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Changes:
echo - Fixed Stop toggle for Dominant (SL from entry vs mid_channel)
echo - Chart shows TP/SL/Entry price lines for last trade
echo - Improved trade markers with TP hit indicators
echo.
pause
