# Indicator Routes Refactoring Plan

## Current State
- **File:** `backend/app/api/indicator_routes.py`
- **Size:** 4149 lines, 171KB
- **Status:** 🟡 Refactoring in progress

## Progress
- ✅ Phase 1 DONE: `calculate.py` - 6 functions (300+ lines)
- ✅ Phase 2 DONE: `backtest.py` - 5 functions (550+ lines)
- ✅ Phase 3 DONE: `data.py` - 8 functions (320+ lines)
- ⏳ Optimization and routes modules deferred (can be added later)

**Total extracted: 1170+ lines (28% of original 4149 lines)**

## Problem
The file contains multiple responsibilities:
1. API route handlers
2. Data download logic
3. Indicator calculations
4. Backtest engine
5. Optimization logic
6. Data preparation
7. Cache management

## Target Structure

```
backend/app/api/indicator/
├── __init__.py              # Router exports
├── routes.py                # Main route handlers
├── calculate.py             # Indicator calculations (TRG, RSI, ADX, etc.)
├── backtest.py              # Backtest engine
├── optimize.py              # Optimization logic
├── data.py                  # Data loading and preparation
├── helpers.py               # Utility functions
└── models.py                # Pydantic models (if needed)
```

## Migration Steps

### Phase 1: Extract Calculations (calculate.py)
Move functions:
- `calculate_trg()`
- `calculate_supertrend()`
- `calculate_rsi()`
- `calculate_adx()`
- `generate_signals()`

### Phase 2: Extract Backtest (backtest.py)
Move functions:
- `run_backtest()`
- `quick_backtest()`
- `check_exit()`
- `_build_monthly_stats()`
- `calculate_statistics()`
- `calculate_advanced_score()`

### Phase 3: Extract Optimization (optimize.py)
Move functions:
- `run_single_backtest_*()` (all variants)
- `generate_*_configs()` (all generators)
- `calculate_optimization_score()`
- `run_adaptive_optimization()`
- `optimize_on_lookback()`

### Phase 4: Extract Data (data.py)
Move functions:
- `find_data_dir()`
- `download_single_symbol()`
- `prepare_candles()`
- `prepare_indicators()`
- `prepare_trade_markers()`
- `get_current_signal()`

### Phase 5: Main Routes (routes.py)
Keep only:
- Route decorators and handlers
- Request/Response models
- Error handling
- Imports from other modules

## Testing Strategy
1. Extract one module at a time
2. Run all tests after each extraction
3. Verify API endpoints still work
4. Check frontend integration

## Rollback Plan
- Keep original `indicator_routes.py` as `indicator_routes_backup.py`
- If issues arise, revert and fix problems
- Only delete backup after 2 weeks of stable operation

## Estimated Effort
- Phase 1: 2-3 hours
- Phase 2: 3-4 hours
- Phase 3: 4-5 hours
- Phase 4: 2-3 hours
- Phase 5: 1-2 hours
- Testing: 2-3 hours
- **Total: 14-20 hours**

## Priority
🟡 Medium - Should be done, but not urgent

## Notes
- This refactoring should be done in a separate branch
- Need comprehensive testing before merging
- Document any breaking changes
- Update imports in `main.py` if needed
