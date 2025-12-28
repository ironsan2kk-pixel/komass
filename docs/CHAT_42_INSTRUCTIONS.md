# Chat #42 — Filters Protection

> **Phase:** 5 — General Filters  
> **Previous:** #41 Filters Portfolio ✅  
> **Next:** #43 Filters Integration

---

## 🎯 GOAL

Create protection filters that guard against drawdowns and losing streaks:
- EquityCurveFilter — trade only when equity above MA
- MaxDDFilter — stop trading at max drawdown threshold
- StreakFilter — pause after N consecutive losses
- RecoveryFilter — reduce position size during recovery

---

## 📋 TASKS

- [ ] `filters/protection_filters.py` — four protection filters

### EquityCurveFilter
```python
class EquityCurveFilter(BaseFilter):
    name = "equity_curve_filter"
    category = FilterCategory.PROTECTION
    priority = FilterPriority.CRITICAL
    
    Config params:
    - ma_period: int = 20  # Moving average period
    - mode: str = "above"  # "above", "below", "both"
    - pause_on_below: bool = True  # Pause when below MA
```

### MaxDDFilter
```python
class MaxDDFilter(BaseFilter):
    name = "max_dd_filter"
    category = FilterCategory.PROTECTION
    priority = FilterPriority.CRITICAL
    
    Config params:
    - max_daily_dd: float = 5.0  # Max daily drawdown %
    - max_total_dd: float = 15.0  # Max total drawdown %
    - cooldown_hours: int = 24  # Hours before resuming
```

### StreakFilter
```python
class StreakFilter(BaseFilter):
    name = "streak_filter"
    category = FilterCategory.PROTECTION
    priority = FilterPriority.CRITICAL
    
    Config params:
    - max_consecutive_losses: int = 3
    - pause_trades: int = 5  # Skip next N signals
    - reset_on_win: bool = True
```

### RecoveryFilter
```python
class RecoveryFilter(BaseFilter):
    name = "recovery_filter"
    category = FilterCategory.PROTECTION
    priority = FilterPriority.CRITICAL
    
    Config params:
    - dd_threshold: float = 10.0  # DD % to trigger
    - scale_factor: float = 0.5  # Reduce to 50%
    - recovery_target: float = 5.0  # DD % to resume normal
```

- [ ] Equity curve calculation helpers
- [ ] Drawdown tracking helpers
- [ ] Update registry.py imports
- [ ] Update __init__.py exports
- [ ] Unit tests (35+ tests)
- [ ] run_protection_filter_tests.bat

---

## 📁 FILES

```
backend/app/filters/
├── __init__.py            # Update exports
├── base.py                # (no changes)
├── registry.py            # Update imports
├── chain.py               # (no changes)
├── time_filters.py        # (no changes)
├── volatility_filters.py  # (no changes)
├── trend_filters.py       # (no changes)
├── portfolio_filters.py   # (no changes)
└── protection_filters.py  # NEW

tests/
└── test_protection_filters.py  # NEW
```

---

## 📝 GIT COMMIT

```
feat: Add protection-based filters

- Add EquityCurveFilter for equity curve trading
- Add MaxDDFilter for drawdown limits
- Add StreakFilter for loss streak protection
- Add RecoveryFilter for recovery mode
- Add equity and drawdown helpers
- Add 35+ unit tests

Chat #42: Filters Protection
```

---

**Next chat:** #43 — Filters Integration
