# Chat #40 — Filters Trend

> **Phase:** 5 — Общие фильтры  
> **Previous:** #39 Filters Volatility ✅  
> **Next:** #41 Filters Portfolio

---

## 🎯 GOAL

Создать трендовые фильтры для бота:
- BTCTrendFilter — торговля по тренду BTC
- MultiTFFilter — согласованность таймфреймов
- RegimeFilter — trending/ranging market detection

---

## 📋 TASKS

- [ ] `filters/trend_filters.py` — три трендовых фильтра

### BTCTrendFilter
```python
class BTCTrendFilter(BaseFilter):
    name = "btc_trend_filter"
    category = FilterCategory.TREND
    priority = FilterPriority.MEDIUM
    
    Config params:
    - follow_btc_trend: bool = True  # Trade only in BTC direction
    - btc_trend_method: str = "ma"   # "ma", "supertrend", "ema"
    - btc_trend_period: int = 20     # Period for trend calculation
    - allow_neutral: bool = True     # Allow trades when BTC neutral
```

### MultiTFFilter
```python
class MultiTFFilter(BaseFilter):
    name = "multi_tf_filter"
    category = FilterCategory.TREND
    priority = FilterPriority.MEDIUM
    
    Config params:
    - required_timeframes: List[str] = ["4h", "1d"]
    - require_all_aligned: bool = True
    - min_aligned_count: int = 1
```

### RegimeFilter
```python
class RegimeFilter(BaseFilter):
    name = "regime_filter"
    category = FilterCategory.TREND
    priority = FilterPriority.MEDIUM
    
    Config params:
    - allowed_regimes: List[str] = ["trending"]  # "trending", "ranging"
    - regime_detection_method: str = "adx"  # "adx", "atr_ratio", "bb_width"
    - adx_threshold: int = 25  # ADX > threshold = trending
```

- [ ] Update registry.py imports
- [ ] Update __init__.py exports
- [ ] Unit тесты (25+ тестов)
- [ ] run_trend_filter_tests.bat

---

## 📁 FILES

```
backend/app/filters/
├── __init__.py           # Update exports
├── base.py               # (no changes)
├── registry.py           # Update imports
├── chain.py              # (no changes)
├── time_filters.py       # (no changes)
├── volatility_filters.py # (no changes)
└── trend_filters.py      # NEW

tests/
├── test_time_filters.py
├── test_volatility_filters.py
└── test_trend_filters.py  # NEW
```

---

## 📝 GIT COMMIT

```
feat: Add trend-based filters

- Add BTCTrendFilter for BTC trend following
- Add MultiTFFilter for multi-timeframe alignment
- Add RegimeFilter for market regime detection
- Add trend detection helpers (MA, SuperTrend, ADX)
- Add 25+ unit tests

Chat #40: Filters Trend
```

---

**Next chat:** #41 — Filters Portfolio
