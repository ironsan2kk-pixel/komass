@echo off
echo ========================================
echo KOMAS v4 - Chat #31-33 Installation
echo Presets Full Module
echo ========================================
echo.

cd /d "%~dp0"

echo [1/4] Backing up existing files...
if exist "backend\app\api\preset_routes.py" (
    copy "backend\app\api\preset_routes.py" "backend\app\api\preset_routes.py.bak" >nul 2>&1
    echo - preset_routes.py backed up
)
if exist "backend\app\database\presets_db.py" (
    copy "backend\app\database\presets_db.py" "backend\app\database\presets_db.py.bak" >nul 2>&1
    echo - presets_db.py backed up
)
if exist "frontend\src\App.jsx" (
    copy "frontend\src\App.jsx" "frontend\src\App.jsx.bak" >nul 2>&1
    echo - App.jsx backed up
)
echo.

echo [2/4] Copying backend files...
copy /Y "backend\app\api\preset_routes.py" "..\..\..\backend\app\api\preset_routes.py" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo - preset_routes.py updated
) else (
    echo - Creating preset_routes.py
    if not exist "..\..\..\backend\app\api" mkdir "..\..\..\backend\app\api"
    copy "backend\app\api\preset_routes.py" "..\..\..\backend\app\api\" >nul 2>&1
)

copy /Y "backend\app\database\presets_db.py" "..\..\..\backend\app\database\presets_db.py" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo - presets_db.py updated
) else (
    echo - Creating presets_db.py
    if not exist "..\..\..\backend\app\database" mkdir "..\..\..\backend\app\database"
    copy "backend\app\database\presets_db.py" "..\..\..\backend\app\database\" >nul 2>&1
)
echo.

echo [3/4] Copying frontend files...
copy /Y "frontend\src\App.jsx" "..\..\..\frontend\src\App.jsx" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo - App.jsx updated
) else (
    echo - Creating App.jsx
    copy "frontend\src\App.jsx" "..\..\..\frontend\src\" >nul 2>&1
)

copy /Y "frontend\src\pages\Presets.jsx" "..\..\..\frontend\src\pages\Presets.jsx" >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo - Presets.jsx created
) else (
    if not exist "..\..\..\frontend\src\pages" mkdir "..\..\..\frontend\src\pages"
    copy "frontend\src\pages\Presets.jsx" "..\..\..\frontend\src\pages\" >nul 2>&1
    echo - Presets.jsx created
)

if not exist "..\..\..\frontend\src\components\Presets" mkdir "..\..\..\frontend\src\components\Presets"
copy /Y "frontend\src\components\Presets\*.jsx" "..\..\..\frontend\src\components\Presets\" >nul 2>&1
copy /Y "frontend\src\components\Presets\*.js" "..\..\..\frontend\src\components\Presets\" >nul 2>&1
echo - Presets components created
echo.

echo [4/4] Copying tests...
if not exist "..\..\..\tests" mkdir "..\..\..\tests"
copy /Y "tests\test_preset_routes.py" "..\..\..\tests\" >nul 2>&1
echo - test_preset_routes.py created
echo.

echo ========================================
echo Installation complete!
echo ========================================
echo.
echo New features:
echo - /api/presets/clone/{id}      - Clone preset
echo - /api/presets/backup          - Backup all presets
echo - /api/presets/restore         - Restore from backup
echo - /api/presets/batch/delete    - Batch delete
echo - /api/presets/batch/update    - Batch update
echo - /api/presets/batch/export    - Batch export
echo.
echo Frontend:
echo - New Presets page with library view
echo - Search, filter, pagination
echo - Import/Export buttons
echo - Backup/Restore functionality
echo.
echo Please restart the backend server!
echo.
pause
