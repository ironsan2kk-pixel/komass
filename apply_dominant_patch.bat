@echo off
echo ========================================
echo Applying Dominant Optimization Patch
echo ========================================
echo.

cd /d "%~dp0"
cd backend\app\api

echo Creating backup...
copy indicator_routes.py indicator_routes.py.bak

echo Applying patch...
python "%~dp0apply_patch.py"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Patch failed!
    copy indicator_routes.py.bak indicator_routes.py
    pause
    exit /b 1
)

echo.
echo Patch applied successfully!
echo Restart the backend to apply changes.
pause
