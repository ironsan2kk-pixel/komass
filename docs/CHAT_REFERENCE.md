# KOMAS v4.0 — CHAT REFERENCE

> **Последнее обновление:** 28.12.2025  
> **Текущий чат:** #37 — Filters Architecture ✅  
> **GitHub:** https://github.com/ironsan2kk-pixel/komass

---

## 🔍 Фаза 5: Общие фильтры

### Chat #37 — Filters Architecture ✅
**Статус:** Завершён  
**Дата:** 28.12.2025

**Выполнено:**
- ✅ `filters/base.py` — BaseFilter абстрактный класс
- ✅ `filters/registry.py` — FilterRegistry (Singleton pattern)
- ✅ `filters/chain.py` — FilterChain с short-circuit
- ✅ `filters/__init__.py` — экспорты модуля
- ✅ 35+ unit тестов

**Ключевые компоненты:**

```python
# Enums
FilterCategory: TIME, VOLATILITY, TREND, PORTFOLIO, PROTECTION
FilterPriority: CRITICAL, HIGH, NORMAL, LOW

# Data Classes
FilterResult(allowed, reason, filter_name, category, details)
FilterConfig(name, enabled, params, priority)
SignalContext(signal, symbol, timeframe, current_price, ...)

# Main Classes
BaseFilter — abstract base class
├── name, display_name, description
├── category, priority, enabled
├── can_trade(context) -> FilterResult
└── get_config_schema() -> dict

FilterRegistry — Singleton for filter management
├── register(cls), unregister(name)
├── get(name) -> FilterClass
├── create(name, config) -> Filter
└── list_all(), list_by_category()

FilterChain — Apply filters sequentially
├── add(filter), remove(name)
├── apply(context) -> ChainResult
├── check(context) -> (bool, reason)
└── enable/disable filters

FilterChainBuilder — Fluent API
├── add(name, **params)
├── with_short_circuit(bool)
└── build() -> FilterChain
```

**Пример использования:**

```python
from app.filters import (
    FilterChain, get_registry, SignalContext,
    register_filter, BaseFilter, FilterCategory
)

# Register custom filter
@register_filter
class MaxPositionsFilter(BaseFilter):
    name = "max_positions"
    category = FilterCategory.PORTFOLIO
    
    def can_trade(self, context):
        if context.position_count >= self.config.get("max_positions", 3):
            return FilterResult.block("Max positions reached")
        return FilterResult.allow()
    
    def get_config_schema(self):
        return {"type": "object", "properties": {...}}

# Create chain
chain = FilterChain()
chain.add_by_name("max_positions", {"max_positions": 3})

# Apply to signal
context = SignalContext(signal=signal, symbol="BTCUSDT", ...)
result = chain.apply(context)

if result.allowed:
    print("Execute trade")
else:
    print(f"Blocked: {result.primary_rejection.reason}")
```

**Файлы созданы:**
- `backend/app/filters/__init__.py`
- `backend/app/filters/base.py`
- `backend/app/filters/registry.py`
- `backend/app/filters/chain.py`
- `tests/test_filters_architecture.py`
- `run_filter_tests.bat`

**Git Commit:**
```
feat: Add filters module architecture

- Add BaseFilter abstract class with can_trade interface
- Add FilterRegistry for filter management (Singleton)
- Add FilterChain for applying multiple filters
- Add FilterResult and ChainResult dataclasses
- Add SignalContext for complete signal context
- Add FilterCategory and FilterPriority enums
- Add JSON schema support for filter configs
- Add AlwaysAllowFilter and AlwaysBlockFilter for testing
- Add FilterChainBuilder for fluent API
- Add 35+ unit tests

Chat #37: Filters Architecture
```

---

### Chat #38 — Filters Time ⏳
**Статус:** Следующий

**Задачи:**
- [ ] SessionFilter — торговые сессии (Asia/Europe/US)
- [ ] WeekdayFilter — дни недели
- [ ] CooldownFilter — пауза после сделки
- [ ] Timezone support
- [ ] Unit тесты

**Планируемые файлы:**
- `backend/app/filters/time_filters.py`
- `tests/test_time_filters.py`

---

## 📋 Полный список чатов Фазы 5

| # | Название | Статус | Описание |
|---|----------|--------|----------|
| 37 | Filters Architecture | ✅ | BaseFilter, Registry, Chain |
| 38 | Filters Time | ⏳ | Session, Weekday, Cooldown |
| 39 | Filters Volatility | ⬜ | ATR, Volume, Extreme |
| 40 | Filters Trend | ⬜ | BTC Trend, Multi-TF, Regime |
| 41 | Filters Portfolio | ⬜ | Correlation, Direction, Sector |
| 42 | Filters Protection | ⬜ | Equity Curve, DD, Streak |
| 43 | Filters Integration | ⬜ | FilterManager, API, DB |
| 44 | Filters UI | ⬜ | Frontend components |

---

## 🔗 Навигация

| Предыдущий | Текущий | Следующий |
|------------|---------|-----------|
| #36 Score UI | **#37 Filters Architecture** | #38 Filters Time |

---

## 📊 Фаза 4: Signal Score ✅ ЗАВЕРШЕНА

### Chat #34 — Signal Score Core ✅
**Дата:** 27.12.2025

### Chat #35 — Score Multi-TF ✅
**Дата:** 28.12.2025

### Chat #36 — Score UI ✅
**Дата:** 28.12.2025

---

*Обновлено: 28.12.2025*
