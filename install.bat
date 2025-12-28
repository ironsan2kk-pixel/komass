@echo off
echo ========================================
echo KOMAS Chat #49 - Optimizer UI Install
echo ========================================
echo.

cd /d "%~dp0"

echo Copying frontend files...
if not exist "frontend\src\pages" mkdir "frontend\src\pages"

copy /Y "frontend\src\pages\Optimizer.jsx" "..\frontend\src\pages\Optimizer.jsx"
copy /Y "frontend\src\App.jsx" "..\frontend\src\App.jsx"

echo Copying docs...
if not exist "..\docs" mkdir "..\docs"
copy /Y "docs\TRACKER.md" "..\docs\TRACKER.md"
copy /Y "docs\CHAT_REFERENCE.md" "..\docs\CHAT_REFERENCE.md"
copy /Y "docs\CHAT_50_INSTRUCTIONS.md" "..\docs\CHAT_50_INSTRUCTIONS.md"

echo Copying tests...
if not exist "..\tests" mkdir "..\tests"
copy /Y "tests\test_optimizer_ui.py" "..\tests\test_optimizer_ui.py"

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo Files installed:
echo   - frontend/src/pages/Optimizer.jsx (NEW)
echo   - frontend/src/App.jsx (UPDATED)
echo   - docs/TRACKER.md (UPDATED)
echo   - docs/CHAT_REFERENCE.md (UPDATED)
echo   - docs/CHAT_50_INSTRUCTIONS.md (NEW)
echo   - tests/test_optimizer_ui.py (NEW)
echo.
echo Please restart frontend server to see changes.
echo.
pause
