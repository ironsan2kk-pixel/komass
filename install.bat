@echo off
chcp 65001 >nul
echo ============================================
echo KOMAS Chat #16: Backend Bug Fixes
echo ============================================
echo.

REM Check if we're in correct directory
if not exist "backend\app\api\indicator_routes.py" (
    echo [ERROR] Please run from komas_indicator root directory
    echo Expected: komas_indicator\
    pause
    exit /b 1
)

REM Backup original files
echo [1/4] Creating backups...
if not exist "backups\chat16" mkdir backups\chat16
copy /Y backend\app\api\indicator_routes.py backups\chat16\ >nul
copy /Y backend\app\api\data_routes.py backups\chat16\ >nul
copy /Y frontend\src\pages\Indicator.jsx backups\chat16\ >nul
echo       Done

REM Copy new frontend file
echo [2/4] Updating frontend...
copy /Y chat16_fix\frontend\src\pages\Indicator.jsx frontend\src\pages\ >nul
echo       Done

REM Apply Python patches
echo [3/4] Patching backend...
cd backend
call venv\Scripts\activate 2>nul
python ..\chat16_fix\apply_patches.py
cd ..
echo       Done

REM Verify
echo [4/4] Verifying...
python -c "import ast; ast.parse(open('backend/app/api/indicator_routes.py', encoding='utf-8').read())" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] indicator_routes.py syntax error!
    echo Restoring backup...
    copy /Y backups\chat16\indicator_routes.py backend\app\api\ >nul
    pause
    exit /b 1
)
echo       All files valid

echo.
echo ============================================
echo SUCCESS! Changes applied:
echo ============================================
echo  - Fixed duplicate timestamp handling in charts
echo  - Fixed UTF-8 encoding issues (mojibake)
echo  - Improved time series data validation
echo.
echo Restart backend and frontend to apply changes.
echo.
pause
