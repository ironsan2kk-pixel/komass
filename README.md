# Chat #28 — Trade Levels Visualization (TRG + Dominant)

## New Features

### 1. Trade Level Lines on Chart
For **ALL trades** (not just the last one):
- **Entry line** (blue) — from entry to exit time
- **TP lines** (green) — solid if hit, dashed if not
- **SL line** (red) — solid if hit, dashed if not

Lines are bounded by trade time — they start at entry and end at exit!

### 2. TP Hit Markers
- Green checkmarks `TP1✓`, `TP2✓` etc. on the chart
- Shows exactly where each TP was hit

### 3. Fixed Stop Toggle (Dominant)
- Checkbox in Stop Loss section
- OFF: SL from mid_channel (default behavior)
- ON: SL from entry price

### 4. Toggle Switch
- Header has "Уровни" checkbox to show/hide level lines
- Default: ON

## Works For Both Indicators
- **TRG**: Uses `tp_levels`, `sl_level`, `tp_hit: [true, true, false, false]`
- **Dominant**: Uses `tp_levels`, `sl_level`, `tps_hit: [1, 2]`

## Files Changed

### Backend
- `dominant.py` — Added tp_levels, initial_sl, final_sl to track_position
- `indicator_routes.py` — Added levels to adapted_trades, improved markers

### Frontend
- `Indicator.jsx` — Trade level lines for all trades, TP hit markers
- `SettingsSidebar.jsx` — Fixed Stop checkbox for Dominant

## Installation
1. Place folder next to `komas_indicator`
2. Run `install_chat28.bat`
3. Restart backend and frontend

## Git Commit
```
feat(chart): Trade level lines for all trades (TRG + Dominant)

- Add TP/SL/Entry lines bounded by trade entry-exit time
- Add TP hit checkmarks on chart
- Add Fixed Stop toggle for Dominant
- Add "Levels" toggle in header
- Support both TRG and Dominant trade formats

Chat #28: Trade Levels Visualization
```
