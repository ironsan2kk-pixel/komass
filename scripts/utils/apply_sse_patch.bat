@echo off
echo ========================================
echo Applying SSE GET Endpoint Patch (FIXED)
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Restoring backup if exists...
if exist "backend\app\api\indicator_routes.py.bak" (
    echo Found backup, restoring...
    copy /y "backend\app\api\indicator_routes.py.bak" "backend\app\api\indicator_routes.py"
)

echo.
echo Step 2: Applying patch...
python apply_sse_patch.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Patch failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo SUCCESS! Patch applied.
echo ========================================
echo.
echo Please restart the backend now.
echo.
pause
