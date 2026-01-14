@echo off
echo ========================================
echo  KOMAS v3.5 UI Bugfixes Installer
echo  Chat #15: Bugfixes UI
echo ========================================
echo.

set "SCRIPT_DIR=%~dp0"

echo [1/2] Copying fixed components...

if not exist "%SCRIPT_DIR%frontend\src\components\Indicator" (
    mkdir "%SCRIPT_DIR%frontend\src\components\Indicator"
)

copy /Y "%SCRIPT_DIR%frontend\src\components\Indicator\*.jsx" "%SCRIPT_DIR%frontend\src\components\Indicator\" >nul
copy /Y "%SCRIPT_DIR%frontend\src\components\Indicator\index.js" "%SCRIPT_DIR%frontend\src\components\Indicator\" >nul

echo [OK] Components copied

echo [2/2] Copying fixed Indicator page...

if not exist "%SCRIPT_DIR%frontend\src\pages" (
    mkdir "%SCRIPT_DIR%frontend\src\pages"
)

copy /Y "%SCRIPT_DIR%frontend\src\pages\Indicator.jsx" "%SCRIPT_DIR%frontend\src\pages\" >nul

echo [OK] Indicator page copied

echo.
echo ========================================
echo  Installation complete!
echo ========================================
echo.
echo Fixed issues:
echo  - MonthlyPanel: division by zero protection
echo  - StatsPanel: undefined fields protection
echo  - All components: UTF-8 encoding fixed
echo.
echo Restart frontend to apply changes:
echo   cd frontend
echo   npm run dev
echo.
pause
