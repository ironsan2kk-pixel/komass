@echo off
echo ========================================
echo Installing KOMAS Chat #48 Updates
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Copying backend files...
if not exist "backend\app\api" mkdir "backend\app\api"
copy /Y "backend\app\api\heatmap_routes.py" "..\backend\app\api\heatmap_routes.py"
copy /Y "backend\app\main.py" "..\backend\app\main.py"
echo Backend files copied.
echo.

echo Step 2: Copying frontend files...
if not exist "frontend\src\components\Optimizer" mkdir "frontend\src\components\Optimizer"
copy /Y "frontend\src\components\Optimizer\HeatmapPanel.jsx" "..\frontend\src\components\Optimizer\HeatmapPanel.jsx"
copy /Y "frontend\src\components\Optimizer\index.js" "..\frontend\src\components\Optimizer\index.js"
copy /Y "frontend\src\api.js" "..\frontend\src\api.js"
echo Frontend files copied.
echo.

echo Step 3: Copying test files...
if not exist "..\tests" mkdir "..\tests"
copy /Y "tests\test_optimizer_heatmap.py" "..\tests\test_optimizer_heatmap.py"
echo Test files copied.
echo.

echo Step 4: Copying documentation...
if not exist "..\docs" mkdir "..\docs"
copy /Y "docs\TRACKER.md" "..\docs\TRACKER.md"
copy /Y "docs\CHAT_REFERENCE.md" "..\docs\CHAT_REFERENCE.md"
copy /Y "docs\CHAT_49_INSTRUCTIONS.md" "..\docs\CHAT_49_INSTRUCTIONS.md"
echo Documentation copied.
echo.

echo ========================================
echo Installation complete!
echo ========================================
echo.
echo New files:
echo   - backend/app/api/heatmap_routes.py
echo   - frontend/src/components/Optimizer/HeatmapPanel.jsx
echo   - tests/test_optimizer_heatmap.py
echo.
echo Updated files:
echo   - backend/app/main.py
echo   - frontend/src/components/Optimizer/index.js
echo   - frontend/src/api.js
echo   - docs/TRACKER.md
echo   - docs/CHAT_REFERENCE.md
echo.
echo Please restart the backend server to apply changes.
echo.
pause
