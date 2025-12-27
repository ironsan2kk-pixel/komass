@echo off
echo ========================================
echo Installing Chat #28 - Trade Levels
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
echo NEW FEATURES:
echo - TP/SL/Entry lines for ALL trades on chart
echo - Lines are bounded by trade entry-exit time
echo - TP hit checkmarks on chart
echo - Fixed Stop toggle for Dominant
echo - Toggle "Levels" checkbox in header to show/hide
echo.
echo Works for both TRG and Dominant indicators!
echo.
pause
