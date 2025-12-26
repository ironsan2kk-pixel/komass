@echo off
chcp 65001 >nul
echo ============================================
echo   KOMAS - Clear Calendar Cache
echo ============================================
echo.

cd /d "%~dp0"

echo Deleting calendar cache...
if exist "data\calendar\events_cache.json" (
    del /f "data\calendar\events_cache.json"
    echo Cache deleted!
) else (
    echo No cache file found.
)

echo.
echo Done! Restart backend to fetch fresh data.
pause
