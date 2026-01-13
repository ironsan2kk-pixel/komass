# Indicator API Module (Refactored)

Модульная структура для indicator API routes.

## 📁 Structure

```
backend/app/api/indicator/
├── __init__.py              # Module exports
├── calculate.py             # ✅ Indicator calculations (Phase 1 DONE)
├── backtest.py              # ✅ Backtest engine (Phase 2 DONE)
├── optimize.py              # ⏳ Optimization logic (Phase 3 TODO)
├── data.py                  # ⏳ Data utilities (Phase 4 TODO)
├── routes.py                # ⏳ Route handlers (Phase 5 TODO)
├── REFACTORING_PLAN.md      # Detailed refactoring plan
└── README.md                # This file
```

## ✅ Phase 1: calculate.py (COMPLETED)

Extracted pure calculation functions:

### Functions:
- `calculate_trg(df, atr_length, multiplier)` - TRG indicator
- `calculate_supertrend(df, period, multiplier)` - SuperTrend
- `calculate_rsi(df, period)` - RSI
- `calculate_adx(df, period)` - ADX
- `generate_signals(df, settings)` - Signal generation
- `apply_trg_with_filters(df, settings)` - Complete TRG pipeline

### Usage Example:
```python
from app.api.indicator.calculate import calculate_trg, generate_signals

# Calculate TRG
df = calculate_trg(df, atr_length=45, multiplier=4.0)

# Generate signals
df = generate_signals(df, settings)
```

---

## ✅ Phase 2: backtest.py (COMPLETED)

Extracted backtest engine functions:

### Functions:
- `calculate_trg(df, atr_length, multiplier)` - TRG indicator
- `calculate_supertrend(df, period, multiplier)` - SuperTrend
- `calculate_rsi(df, period)` - RSI
- `calculate_adx(df, period)` - ADX
- `generate_signals(df, settings)` - Signal generation
- `apply_trg_with_filters(df, settings)` - Complete TRG pipeline

### Usage Example:
```python
from app.api.indicator.calculate import calculate_trg, generate_signals

# Calculate TRG
df = calculate_trg(df, atr_length=45, multiplier=4.0)

# Generate signals
df = generate_signals(df, settings)
```

### Functions:
- `run_backtest(df, settings, adaptive_mode)` - Main backtest engine
- `quick_backtest(df, settings, tp_levels, sl_pct)` - Fast backtest for optimization
- `check_exit(position, row, settings, tp_levels, tp_amounts)` - Exit condition checker
- `_build_monthly_stats(trades)` - Monthly breakdown builder
- `calculate_statistics(trades, equity_curve, settings, monthly_stats)` - Comprehensive stats

### Usage Example:
```python
from app.api.indicator.backtest import run_backtest, calculate_statistics

# Run backtest
trades, equity, tp_stats, monthly, params = run_backtest(df, settings)

# Calculate stats
stats = calculate_statistics(trades, equity, settings, monthly)
```

---

## ⏳ Next Steps

### Phase 3: optimize.py
Extract from `indicator_routes.py`:
- `run_single_backtest_*()` (6 variants)
- `generate_*_configs()` (5 generators)
- `calculate_optimization_score()`
- `run_adaptive_optimization()`

### Phase 3: optimize.py
Extract optimization functions:
- `run_single_backtest_*()` (6 variants)
- `generate_*_configs()` (5 generators)
- `calculate_optimization_score()`
- `run_adaptive_optimization()`

### Phase 4: data.py
Extract data utilities:
- `find_data_dir()`
- `download_single_symbol()`
- `prepare_candles()`
- `prepare_indicators()`
- `prepare_trade_markers()`
- `get_current_signal()`

### Phase 5: routes.py
Main route handlers:
- `@router.post("/calculate")`
- `@router.post("/heatmap")`
- `@router.post("/auto-optimize")`
- `@router.get("/auto-optimize-stream")`
- `@router.get("/cache-stats")`
- `@router.post("/cache-clear")`

## 🔄 Migration Strategy

1. **Gradual migration**: Don't break existing code
2. **Keep `indicator_routes.py` working**: It remains the main entry point
3. **Import from modules**: Update indicator_routes.py to import from calculate.py
4. **Test after each phase**: Run all tests before proceeding
5. **Delete old code only when safe**: After all imports verified

## 🧪 Testing

After each phase, run:
```bash
cd backend
pytest tests/ -k indicator
```

## 📝 Notes

- Original file: `indicator_routes.py` (4149 lines)
- Target: 5 modules (~500-800 lines each)
- Benefits: Better maintainability, easier testing, clearer separation of concerns
