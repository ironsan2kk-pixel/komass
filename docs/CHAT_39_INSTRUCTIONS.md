# Chat #39 — Filters Volatility

> **Phase:** 5 — Общие фильтры  
> **Previous:** #38 Filters Time ✅  
> **Next:** #40 Filters Trend

---

## 🎯 GOAL

Создать фильтры волатильности для бота:
- ATRFilter — фильтр по ATR (мин/макс границы)
- VolumeFilter — фильтр по объёму
- ExtremeFilter — блокировка при экстремальной волатильности

---

## 📋 TASKS

- [ ] `filters/volatility_filters.py` — три фильтра волатильности

### ATRFilter
```python
class ATRFilter(BaseFilter):
    name = "atr_filter"
    category = FilterCategory.VOLATILITY
    priority = FilterPriority.MEDIUM
    
    Config params:
    - min_atr: Optional[float]   # Minimum ATR value
    - max_atr: Optional[float]   # Maximum ATR value
    - atr_period: int = 14       # ATR calculation period
    - use_atr_percent: bool = True  # ATR as % of price
```

### VolumeFilter
```python
class VolumeFilter(BaseFilter):
    name = "volume_filter"
    category = FilterCategory.VOLATILITY
    priority = FilterPriority.MEDIUM
    
    Config params:
    - min_volume_ratio: float = 1.0  # Min volume vs MA
    - volume_ma_period: int = 20     # Volume MA period
    - require_above_average: bool = True
```

### ExtremeFilter
```python
class ExtremeFilter(BaseFilter):
    name = "extreme_filter"
    category = FilterCategory.VOLATILITY
    priority = FilterPriority.CRITICAL
    
    Config params:
    - atr_multiplier: float = 3.0  # ATR spike threshold
    - volume_multiplier: float = 5.0  # Volume spike threshold
    - pause_minutes: int = 60  # Pause after extreme
```

- [ ] Update registry.py imports
- [ ] Update __init__.py exports
- [ ] Unit тесты (25+ тестов)
- [ ] run_volatility_filter_tests.bat

---

## 📁 FILES

```
backend/app/filters/
├── __init__.py           # Update exports
├── base.py               # (no changes)
├── registry.py           # Update imports
├── chain.py              # (no changes)
├── time_filters.py       # (no changes)
└── volatility_filters.py # NEW

tests/
├── test_time_filters.py
└── test_volatility_filters.py  # NEW
```

---

## 📝 GIT COMMIT

```
feat: Add volatility-based filters

- Add ATRFilter for ATR range filtering
- Add VolumeFilter for volume threshold filtering
- Add ExtremeFilter for volatility spike protection
- Add ATR/volume calculation helpers
- Add 25+ unit tests

Chat #39: Filters Volatility
```

---

**Next chat:** #40 — Filters Trend
