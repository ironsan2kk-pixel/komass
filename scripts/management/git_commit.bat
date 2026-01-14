@echo off
chcp 65001 >nul
echo ========================================
echo  Git Commit: Chat #15 UI Bugfixes
echo ========================================
echo.

cd /d "%~dp0.."

echo [1/3] Adding files to git...
git add frontend/src/components/Indicator/
git add frontend/src/pages/Indicator.jsx

echo [2/3] Creating commit...
git commit -m "fix(ui): resolve encoding issues and null safety in Indicator components

- Fix MonthlyPanel: add null/undefined protection, prevent division by zero
- Fix StatsPanel: add default values and safe number formatting
- Fix LogsPanel: correct UTF-8 encoding for Russian text and emojis
- Fix TradesTable: correct UTF-8 encoding, add null safety
- Fix HeatmapPanel: correct UTF-8 encoding, improve data validation
- Fix AutoOptimizePanel: correct UTF-8 encoding for all labels
- Fix SettingsSidebar: correct UTF-8 encoding for section titles
- Fix Indicator.jsx: correct UTF-8 encoding for tabs and messages

Chat #15: Bugfixes UI
Version: v3.5.1"

echo [3/3] Pushing to GitHub...
git push origin main

echo.
echo ========================================
echo  Git commit completed!
echo ========================================
echo.
pause
