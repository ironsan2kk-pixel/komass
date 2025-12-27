# 📚 KOMAS v4.0 — Chat Reference

> **Purpose:** Quick reference for all development chats  
> **Last Updated:** 27.12.2025

---

## Phase 1: Stabilization (#15-#19) ✅

| # | Name | Date | Summary |
|---|------|------|---------|
| #15 | Bugfixes UI | 27.12.2025 | Fixed MonthlyPanel, StatsPanel, UTF-8 |
| #16 | Bugfixes Backend | 27.12.2025 | Fixed duplicate timestamps, 500 errors |
| #17 | Data Futures Only | 27.12.2025 | Removed spot, futures only |
| #18 | Data Period Selection | 27.12.2025 | Date picker for data range |
| #19 | Data Caching | 27.12.2025 | LRU cache for optimization |

---

## Phase 2: Dominant Indicator (#20-#27)

| # | Name | Date | Summary |
|---|------|------|---------|
| #20 | Dominant Core | 27.12.2025 | Channel + Fibonacci calculation ✅ |
| #21 | Dominant Signals | 27.12.2025 | Signal generation, trend tracking ✅ |
| #22 | Dominant Filters | 27.12.2025 | 5 filter types ✅ |
| #23 | Dominant SL Modes | — | 5 stop-loss modes ⏳ NEXT |
| #24 | QA Checkpoint #2 | — | Testing & fixes |
| #25 | Dominant AI Resolution | — | Auto-optimization |
| #26 | Dominant Presets DB | — | 37 presets migration |
| #27 | Dominant UI Integration | — | Frontend integration |

---

## Chat #22: Dominant Filters — Details

**Date:** 27.12.2025  
**Status:** ✅ Complete  
**Tests:** 61/61 passed in 1.35s

### Filter Types Implemented:

| Type | Name | Description |
|------|------|-------------|
| 0 | None | No filtering, all signals pass |
| 1 | ATR Condition | Entry when ATR > ATR_MA × multiplier |
| 2 | RSI Condition | Block overbought longs, oversold shorts |
| 3 | Combined | Both ATR and RSI must pass |
| 4 | Volatility | Block during extreme volatility |

### New Functions:

```python
# Core filter function
apply_filter(df, filter_type=0, **params) -> pd.DataFrame

# Indicator helpers
calculate_rsi(series, period=14) -> pd.Series
calculate_atr(df, period=14) -> pd.Series

# Info functions
get_filter_info(filter_type=None) -> dict
get_filter_statistics(df) -> dict

# Convenience
generate_signals_with_filter(df, sensitivity, filter_type, **kwargs) -> pd.DataFrame

# Validation
validate_filter_type(filter_type) -> int
```

### Default Parameters:

```python
FILTER_DEFAULTS = {
    'atr_period': 14,
    'atr_multiplier': 1.5,
    'rsi_period': 14,
    'rsi_overbought': 70,
    'rsi_oversold': 30,
    'volatility_period': 20,
    'volatility_max_mult': 2.0,
}
```

### Output Columns Added:

| Column | Type | Description |
|--------|------|-------------|
| filter_pass_long | bool | Long signal passes filter |
| filter_pass_short | bool | Short signal passes filter |
| filtered_can_long | bool | can_long AND filter_pass |
| filtered_can_short | bool | can_short AND filter_pass |
| filtered_signal | int | 1/-1/0 (filtered) |
| filter_type_applied | int | Which filter was used |
| filter_rsi | float | RSI values (if applicable) |
| filter_atr | float | ATR values (if applicable) |

### Files Changed:

| File | Changes |
|------|---------|
| `backend/app/indicators/dominant.py` | +200 lines, v4.0.2 |
| `backend/app/indicators/__init__.py` | Updated exports |
| `tests/test_dominant.py` | +400 lines, 61 tests |

---

## Git Commit for Chat #22:

```
feat(indicators): add Dominant filter types

- Add 5 filter types (0-4)
- Filter 0: None (no filtering)
- Filter 1: ATR Condition (volume spike)
- Filter 2: RSI Condition (overbought/oversold)
- Filter 3: ATR + RSI Combined
- Filter 4: Volatility Condition
- Add apply_filter() function
- Add calculate_rsi(), calculate_atr() helpers
- Add get_filter_info(), get_filter_statistics()
- Add generate_signals_with_filter() convenience function
- Unit tests (61 tests, all passing)

Chat #22: Dominant Filters
```

---

## Next Chat Preview: #23 — Dominant SL Modes

**Goal:** Implement 5 stop-loss management modes

| Mode | Name | Behavior |
|------|------|----------|
| 0 | Fixed | SL never moves |
| 1 | After TP1 | SL → Entry after TP1 hit |
| 2 | After TP2 | SL → Entry after TP2 hit |
| 3 | After TP3 | SL → Entry after TP3 hit |
| 4 | Cascade | SL trails to previous TP |

---

*Updated: 27.12.2025*
