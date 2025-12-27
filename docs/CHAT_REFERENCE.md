# KOMAS v4.0 - Chat Reference

> **Last Updated:** 27.12.2025  
> **GitHub:** https://github.com/ironsan2kk-pixel/komass

---

## 📋 COMPLETED CHATS

### Phase 1: Stabilization

| # | Name | Date | Key Changes |
|---|------|------|-------------|
| 15 | Bugfixes UI | 27.12.2025 | MonthlyPanel, StatsPanel, UTF-8 fixes |
| 16 | Bugfixes Backend | 27.12.2025 | Duplicate timestamps, error handling |
| 17 | Data Futures Only | 27.12.2025 | Removed spot, fapi endpoints |
| 18 | Data Period Selection | 27.12.2025 | Date picker, period filtering |
| 19 | QA Checkpoint #1 | 27.12.2025 | Phase 1 testing complete |

### Phase 2: Dominant Indicator

| # | Name | Date | Key Changes |
|---|------|------|-------------|
| 20 | Dominant Core | 27.12.2025 | Channel + Fibonacci calculation |
| 21 | Dominant Signals | 27.12.2025 | Signal generation, trend tracking |
| 22 | Dominant Filters | 27.12.2025 | 5 filter types (None/ATR/RSI/Combined/Vol) |
| 23 | Dominant SL Modes | 27.12.2025 | 5 SL modes (Fixed/BE TP1-3/Cascade) |
| 24 | QA Checkpoint #2 | 27.12.2025 | Dominant testing complete |
| 25 | Dominant AI Resolution | 27.12.2025 | Scoring, backtest, multi-core optimization |

---

## 📦 CHAT #25 DETAILS

### Summary
Implemented AI Resolution for Dominant indicator - automatic optimization of sensitivity parameter (12-60) using multi-core parallel processing.

### Files Modified
- `backend/app/indicators/dominant.py` (v4.0.3 → v4.0.4)

### New Functions Added

```python
# Scoring (0-100 points)
calculate_sensitivity_score(metrics: Dict) -> float

# Full backtest with metrics
run_full_backtest(df, sensitivity, filter_type, sl_mode, ...) -> Dict

# Multi-core optimization
optimize_sensitivity(df, filter_type, sl_mode, sensitivities, workers, progress_callback) -> Dict

# Comparison DataFrame
compare_sensitivities(df, sensitivities, ...) -> pd.DataFrame

# Score breakdown
get_score_breakdown(metrics) -> Dict

# Formatted summary
get_optimization_summary(result) -> str

# Module info
get_ai_resolution_info() -> Dict
```

### Scoring Formula
```
Score = Profit(30%) + WinRate(25%) + Stability(25%) + Drawdown(20%)

- Profit: PnL -20% to +50% → 0 to 30 points
- Win Rate: 0% to 100% → 0 to 25 points
- Stability: StdDev 0 to 20% → 25 to 0 points
- Drawdown: DD 0% to 40% → 20 to 0 points
```

### Sensitivities Tested
```python
OPTIMIZATION_SENSITIVITIES = [12, 15, 18, 21, 25, 30, 35, 40, 45, 50, 55, 60]
```

### Git Commit
```
feat(indicators): add Dominant AI Resolution

- Add calculate_sensitivity_score() with weighted metrics
- Add run_full_backtest() for complete backtesting
- Add optimize_sensitivity() with ProcessPoolExecutor
- Score: Profit(30%) + WinRate(25%) + Stability(25%) + DD(20%)
- Add progress callback support for SSE streaming
- Add compare_sensitivities(), get_score_breakdown()
- Add get_optimization_summary(), get_ai_resolution_info()
- Update version to 4.0.4
- Unit tests (65+ tests)

Chat #25: Dominant AI Resolution
```

---

## 🔜 NEXT CHAT

**Chat #26 — Dominant: 37 Presets DB**

Tasks:
- Create `presets` table in SQLite
- Migrate 37 presets from Pine Script
- API: GET /api/presets/list
- API: GET /api/presets/{id}
- Unit tests

---

*Updated: 27.12.2025*
