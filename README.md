# Chat #28 — Trade Levels + StatsPanel Fix

## Bug Fixes

### StatsPanel Props Mismatch
- **Problem**: StatsPanel expected `statistics` prop but received `stats`
- **Fix**: Changed prop destructuring to `{ stats: statistics, ... }`
- **Result**: Statistics tab now shows data correctly

## New Features

### Trade Level Lines
- Entry line (blue)
- TP lines (green) - solid if hit, dashed if not
- SL line (red) - solid if hit, dashed if not
- Lines bounded by trade entry-exit time

### Fixed Stop Toggle (Dominant)
- Checkbox in Stop Loss section
- OFF: SL from mid_channel
- ON: SL from entry price

## Files

- `StatsPanel.jsx` - Props fix
- `Indicator.jsx` - Trade level lines
- `SettingsSidebar.jsx` - Fixed Stop toggle
- `dominant.py` - tp_levels, initial_sl, final_sl
- `indicator_routes.py` - sl_level in adapted_trades

## Install

```
install_chat28.bat
```
