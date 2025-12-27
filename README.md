# KOMAS Chat #27 — SL from mid_channel Fix

## Key Changes

### Problem
In original Pine Script, SL is calculated from `fib_5` (mid_channel), NOT from entry_price!

### Pine Script Original (line 2195):
```pine
trade.sl_price := can_long 
    ? (fixed_stop ? entry_price * (1 - sl_percent) : fib_5 * (1 - sl_percent))
    : (fixed_stop ? entry_price * (1 + sl_percent) : fib_5 * (1 + sl_percent))
```

### Fixed Logic:
- `fixed_stop=False` (default): SL = mid_channel × (1 ± sl_percent)
- `fixed_stop=True`: SL = entry_price × (1 ± sl_percent)

## Files Changed

### backend/app/indicators/dominant.py
- Added `fixed_stop` parameter to `track_position()`
- Added `_calculate_sl_for_mode()` helper function
- Initial SL calculated from `mid_channel` by default
- Added `fixed_stop` parameter to `run_full_backtest()`

### backend/app/api/indicator_routes.py
- Added `dominant_fixed_stop: bool = False` to IndicatorSettings
- Pass `fixed_stop` to `run_full_backtest()` call

## Test
```bash
cd tests
python test_sl_from_mid.py
```

## Git Commit
```
fix(dominant): SL calculation from mid_channel (not entry_price)

- Add fixed_stop parameter (default False)
- SL from mid_channel when fixed_stop=False (original behavior)
- SL from entry_price when fixed_stop=True
- Add _calculate_sl_for_mode() helper

Chat #27: Dominant SL from mid_channel fix
```
