@echo off
echo ========================================
echo  KOMAS v3.5 UI Bugfixes Installer
echo  Chat #15: Bugfixes UI
echo ========================================
echo.

set "SCRIPT_DIR=%~dp0"

echo Current directory: %SCRIPT_DIR%
echo.

REM Try to find frontend folder in common locations
if exist "%SCRIPT_DIR%frontend" (
    set "FRONTEND_DIR=%SCRIPT_DIR%frontend"
    goto :found
)

if exist "%SCRIPT_DIR%..\frontend" (
    set "FRONTEND_DIR=%SCRIPT_DIR%..\frontend"
    goto :found
)

if exist "%SCRIPT_DIR%..\..\frontend" (
    set "FRONTEND_DIR=%SCRIPT_DIR%..\..\frontend"
    goto :found
)

REM Not found - ask user
echo [ERROR] Frontend folder not found automatically!
echo.
echo Please drag and drop this bat file into your KOMAS project root folder
echo OR enter the path to your KOMAS project:
echo.
set /p "PROJECT_PATH=KOMAS project path: "

if exist "%PROJECT_PATH%\frontend" (
    set "FRONTEND_DIR=%PROJECT_PATH%\frontend"
    goto :found
)

echo [ERROR] Frontend folder still not found at %PROJECT_PATH%\frontend
pause
exit /b 1

:found
echo [OK] Found frontend at: %FRONTEND_DIR%
echo.

echo [1/2] Copying fixed components...

if not exist "%FRONTEND_DIR%\src\components\Indicator" (
    mkdir "%FRONTEND_DIR%\src\components\Indicator"
)

copy /Y "%SCRIPT_DIR%frontend\src\components\Indicator\*.jsx" "%FRONTEND_DIR%\src\components\Indicator\" >nul 2>&1
copy /Y "%SCRIPT_DIR%frontend\src\components\Indicator\index.js" "%FRONTEND_DIR%\src\components\Indicator\" >nul 2>&1

if errorlevel 1 (
    echo [ERROR] Failed to copy components
    pause
    exit /b 1
)

echo [OK] Components copied

echo [2/2] Copying fixed Indicator page...

if not exist "%FRONTEND_DIR%\src\pages" (
    mkdir "%FRONTEND_DIR%\src\pages"
)

copy /Y "%SCRIPT_DIR%frontend\src\pages\Indicator.jsx" "%FRONTEND_DIR%\src\pages\" >nul 2>&1

if errorlevel 1 (
    echo [ERROR] Failed to copy Indicator.jsx
    pause
    exit /b 1
)

echo [OK] Indicator page copied

echo.
echo ========================================
echo  Installation complete!
echo ========================================
echo.
echo Fixed issues:
echo  - MonthlyPanel: division by zero protection
echo  - StatsPanel: undefined fields protection
echo  - LogsPanel: UTF-8 encoding fixed
echo  - TradesTable: UTF-8 encoding fixed
echo  - HeatmapPanel: UTF-8 encoding fixed
echo  - AutoOptimizePanel: UTF-8 encoding fixed
echo  - SettingsSidebar: UTF-8 encoding fixed
echo  - Indicator.jsx: UTF-8 encoding fixed
echo.
echo Restart frontend to apply changes:
echo   cd frontend
echo   npm run dev
echo.
pause
