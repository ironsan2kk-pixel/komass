# Chat #41 — Filters Portfolio

> **Phase:** 5 — Общие фильтры  
> **Previous:** #40 Filters Trend ✅  
> **Next:** #42 Filters Protection

---

## 🎯 GOAL

Создать портфельные фильтры для бота:
- CorrelationFilter — лимит коррелированных позиций
- DirectionFilter — лимит Long/Short позиций
- SectorFilter — диверсификация по секторам

---

## 📋 TASKS

- [ ] `filters/portfolio_filters.py` — три портфельных фильтра

### CorrelationFilter
```python
class CorrelationFilter(BaseFilter):
    name = "correlation_filter"
    category = FilterCategory.PORTFOLIO
    priority = FilterPriority.LOW
    
    Config params:
    - max_correlated_positions: int = 2  # Max positions with high correlation
    - correlation_threshold: float = 0.7  # Above this = correlated
    - correlation_pairs: Dict[str, List[str]]  # Known correlations
    - use_dynamic_correlation: bool = False  # Calculate on-the-fly
```

### DirectionFilter
```python
class DirectionFilter(BaseFilter):
    name = "direction_filter"
    category = FilterCategory.PORTFOLIO
    priority = FilterPriority.LOW
    
    Config params:
    - max_long_positions: int = 5
    - max_short_positions: int = 5
    - allow_both_directions: bool = True
    - net_exposure_limit: int = 3  # Max difference (longs - shorts)
```

### SectorFilter
```python
class SectorFilter(BaseFilter):
    name = "sector_filter"
    category = FilterCategory.PORTFOLIO
    priority = FilterPriority.LOW
    
    Config params:
    - max_per_sector: int = 2  # Max positions per sector
    - sector_mapping: Dict[str, str]  # symbol -> sector
    - sectors: ["layer1", "defi", "meme", "ai", "gaming", ...]
```

- [ ] Correlation calculation helpers
- [ ] Sector classification data
- [ ] Update registry.py imports
- [ ] Update __init__.py exports
- [ ] Unit тесты (30+ тестов)
- [ ] run_portfolio_filter_tests.bat

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
└── portfolio_filters.py   # NEW

tests/
├── test_time_filters.py
├── test_volatility_filters.py
├── test_trend_filters.py
└── test_portfolio_filters.py  # NEW
```

---

## 📊 SECTOR MAPPING

Suggested sector classifications:
```python
SECTOR_MAPPING = {
    # Layer 1
    "BTCUSDT": "layer1",
    "ETHUSDT": "layer1",
    "SOLUSDT": "layer1",
    "AVAXUSDT": "layer1",
    
    # DeFi
    "UNIUSDT": "defi",
    "AAVEUSDT": "defi",
    "LINKUSDT": "defi",
    
    # Meme
    "DOGEUSDT": "meme",
    "SHIBUSDT": "meme",
    "PEPEUSDT": "meme",
    
    # AI
    "FETUSDT": "ai",
    "AGIXUSDT": "ai",
    "OCEANUSDT": "ai",
    
    # Gaming
    "AXSUSDT": "gaming",
    "SANDUSDT": "gaming",
    "MANAUSDT": "gaming",
}
```

---

## 📝 GIT COMMIT

```
feat: Add portfolio-based filters

- Add CorrelationFilter for correlated position limits
- Add DirectionFilter for long/short position limits
- Add SectorFilter for sector diversification
- Add correlation calculation helpers
- Add sector classification data
- Add 30+ unit tests

Chat #41: Filters Portfolio
```

---

**Next chat:** #42 — Filters Protection
