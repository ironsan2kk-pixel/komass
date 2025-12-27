# Chat #28 — Dominant UI: Fixed Stop toggle + Chart markers fix

## Changes

### 1. Fixed Stop Toggle (SettingsSidebar.jsx)
- Added checkbox "Fixed Stop (от входа)" in Stop Loss section for Dominant
- When OFF (default): SL calculated from mid_channel (original behavior)
- When ON: SL calculated from entry price

### 2. Chart Visualization (Indicator.jsx)
- Added price lines for last trade:
  - Entry line (blue)
  - TP1-TP4 lines (green) with checkmark if hit
  - SL line (red) with X if hit
- Improved trade markers with TP hit indicators

### 3. Backend Updates

#### dominant.py
- Added `tp_levels`, `initial_sl`, `final_sl` to track_position return
- These values are used for chart visualization

#### indicator_routes.py
- Added tp_levels, initial_sl, final_sl to adapted_trades
- Improved prepare_trade_markers() with TP hit markers

## Installation

1. Place this folder next to your `komas_indicator` folder
2. Run `install_chat28.bat`
3. Restart backend and frontend

## Git Commit

```
feat(ui): Fixed Stop toggle + chart price lines

- Add Fixed Stop checkbox for Dominant (SL from entry vs mid_channel)
- Add price lines for TP/SL/Entry levels on chart
- Add tp_levels, initial_sl, final_sl to trade data
- Improve trade markers with TP hit indicators

Chat #28: Dominant UI: Fixed Stop toggle + Chart markers fix
```
