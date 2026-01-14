@echo off
chcp 65001 >nul
echo ============================================
echo  KOMAS Chat #17 - Data Futures Only Update
echo ============================================
echo.

:: Check if paths exist
if not exist "backend\app\api" (
    echo ERROR: backend\app\api folder not found!
    echo Make sure you run this from komas_indicator root folder
    pause
    exit /b 1
)

if not exist "frontend\src\pages" (
    echo ERROR: frontend\src\pages folder not found!
    echo Make sure you run this from komas_indicator root folder
    pause
    exit /b 1
)

:: Backup existing files
echo [1/4] Creating backups...
if exist "backend\app\api\data_routes.py" (
    copy /Y "backend\app\api\data_routes.py" "backend\app\api\data_routes.py.bak" >nul
    echo   - data_routes.py backed up
)
if exist "frontend\src\pages\Data.jsx" (
    copy /Y "frontend\src\pages\Data.jsx" "frontend\src\pages\Data.jsx.bak" >nul
    echo   - Data.jsx backed up
)

:: Copy new files
echo.
echo [2/4] Installing new files...
copy /Y "chat17_files\data_routes.py" "backend\app\api\data_routes.py" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy data_routes.py
    pause
    exit /b 1
)
echo   - data_routes.py installed

copy /Y "chat17_files\Data.jsx" "frontend\src\pages\Data.jsx" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy Data.jsx
    pause
    exit /b 1
)
echo   - Data.jsx installed

:: Verify
echo.
echo [3/4] Verifying installation...
if exist "backend\app\api\data_routes.py" (
    echo   - Backend: OK
) else (
    echo   - Backend: FAILED
)
if exist "frontend\src\pages\Data.jsx" (
    echo   - Frontend: OK
) else (
    echo   - Frontend: FAILED
)

echo.
echo [4/4] Done!
echo ============================================
echo  Changes in this update:
echo   - Removed Binance Spot API support
echo   - Using only Binance Futures API
echo   - Updated UI to reflect Futures-only mode
echo   - Futures data available from Sept 2019
echo ============================================
echo.
echo Restart the server to apply changes:
echo   stop.bat
echo   start.bat
echo.
pause
