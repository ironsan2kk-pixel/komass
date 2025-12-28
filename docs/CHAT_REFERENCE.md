# KOMAS v4.0 — Chat Reference

> **Last updated:** 28.12.2025

---

## Phase 5: General Filters

### Chat #41 — Filters Portfolio ✅
**Date:** 28.12.2025  
**Focus:** Portfolio-based filters for position diversity and risk distribution

**Implemented:**
- **CorrelationFilter** — Limits positions in correlated assets
  - Uses predefined correlation groups (BTC, ETH ecosystem, meme coins, AI, etc.)
  - Configurable max correlated positions and threshold
  - Supports custom correlation groups
  
- **DirectionFilter** — Controls long/short position balance
  - Separate limits for long and short positions
  - Net exposure limit (max difference between longs and shorts)
  - Option to allow/disallow both directions simultaneously
  
- **SectorFilter** — Enforces diversification across sectors
  - 11 sectors: layer1, layer2, defi, meme, ai, gaming, infrastructure, exchange, privacy, oracle, rwa
  - 60+ symbols classified by sector
  - Configurable max positions per sector
  - Sector exclusion support

**Files:**
- `backend/app/filters/portfolio_filters.py` — Main filter implementations
- `backend/app/filters/__init__.py` — Updated exports
- `backend/app/filters/registry.py` — Updated imports
- `tests/test_portfolio_filters.py` — 45+ unit tests
- `run_portfolio_filter_tests.py` — Test runner
- `run_portfolio_filter_tests.bat` — Windows batch file

---

### Chat #40 — Filters Trend ✅
**Date:** 28.12.2025  
**Focus:** Trend-based filters

**Implemented:**
- BTCTrendFilter — Trade with BTC trend direction
- MultiTFFilter — Multi-timeframe confirmation
- RegimeFilter — Market regime detection (trending/ranging)

---

### Chat #39 — Filters Volatility ✅
**Date:** 28.12.2025  
**Focus:** Volatility-based filters

**Implemented:**
- ATRFilter — ATR range filtering
- VolumeFilter — Volume threshold filtering
- ExtremeFilter — Volatility spike protection

---

### Chat #38 — Filters Time ✅
**Date:** 27.12.2025  
**Focus:** Time-based filters

**Implemented:**
- SessionFilter — Trading session control
- WeekdayFilter — Day-of-week filtering
- CooldownFilter — Post-trade pause

---

### Chat #37 — Filters Architecture ✅
**Date:** 27.12.2025  
**Focus:** Filter system foundation

**Implemented:**
- BaseFilter abstract class
- FilterRegistry with decorator
- FilterChain for sequential execution
- Signal and SignalContext classes

---

## Previous Phases

### Phase 1-4: Completed
- Stabilization & Base (#15-19)
- Dominant Indicator (#20-27)
- Preset System (#28-33)
- Signal Score (#34-36)

---

*See TRACKER.md for detailed task lists*
