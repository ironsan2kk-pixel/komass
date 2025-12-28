# 📚 KOMAS v4.0 — CHAT REFERENCE

> **Last updated:** 28.12.2025  
> **Current version:** v4.0  
> **GitHub:** https://github.com/ironsan2kk-pixel/komass

---

## Phase 5: General Filters

### Chat #37: Filters Architecture ✅
**Date:** 27.12.2025  
**Focus:** Base classes for modular filter system

**Created:**
- `filters/base.py` — BaseFilter, Signal, SignalContext, FilterDecision
- `filters/registry.py` — FilterRegistry with decorator
- `filters/chain.py` — FilterChain for sequential execution

---

### Chat #38: Filters Time ✅
**Date:** 27.12.2025  
**Focus:** Time-based filters

**Created:**
- `filters/time_filters.py` — SessionFilter, WeekdayFilter, CooldownFilter
- 48 unit tests

---

### Chat #39: Filters Volatility ✅
**Date:** 28.12.2025  
**Focus:** Volatility-based filters

**Created:**
- `filters/volatility_filters.py` — ATRFilter, VolumeFilter, ExtremeFilter
- 40+ unit tests

---

### Chat #40: Filters Trend ✅
**Date:** 28.12.2025  
**Focus:** Trend-based filters

**Created:**
- `filters/trend_filters.py` — BTCTrendFilter, MultiTFFilter, RegimeFilter
- 35+ unit tests

---

### Chat #41: Filters Portfolio ✅
**Date:** 28.12.2025  
**Focus:** Portfolio-based filters

**Created:**
- `filters/portfolio_filters.py` — CorrelationFilter, DirectionFilter, SectorFilter
- Sector classification (11 sectors, 60+ symbols)
- Correlation groups (9 predefined groups)
- 45+ unit tests

---

### Chat #42: Filters Protection ✅
**Date:** 28.12.2025  
**Focus:** Protection-based filters

**Created:**
- `filters/protection_filters.py` — EquityCurveFilter, MaxDDFilter, StreakFilter, RecoveryFilter
- 35+ unit tests

---

### Chat #43: Filters Integration ✅
**Date:** 28.12.2025  
**Focus:** FilterManager for unified filter management

**Created:**
- `filters/manager.py` — FilterManager, FilterStats, DecisionLog
- `api/filter_routes.py` — Filter config API endpoints
- Database schema for bot_filter_configs
- Filter profiles (minimal/conservative/balanced/aggressive)
- 60+ unit tests

**Key Features:**
- Load/save filter configs to database
- Apply filter chain to signals
- Track filter statistics
- Log filter decisions for debugging
- Filter validation

---

### Chat #44: Filters UI ⏳
**Date:** TBD  
**Focus:** UI for filter configuration

**Planned:**
- Filter settings section in bot config
- Category grouping
- Toggle switches with parameters
- Profile selector
- Statistics display

---

## Previous Phases

### Phase 1-4: Completed
- Stabilization & Base (#15-19)
- Dominant Indicator (#20-27)
- Preset System (#28-33)
- Signal Score (#34-36)

---

*See TRACKER.md for detailed task lists*
