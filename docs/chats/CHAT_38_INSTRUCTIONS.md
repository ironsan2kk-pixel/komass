# Chat #38 — Filters Time

> **Phase:** 5 — Общие фильтры  
> **Previous:** #37 Filters Architecture ✅  
> **Next:** #39 Filters Volatility

---

## 🎯 GOAL

Создать временные фильтры для бота:
- SessionFilter — фильтр по торговым сессиям
- WeekdayFilter — фильтр по дням недели
- CooldownFilter — пауза после сделки

---

## 📋 TASKS

- [ ] `filters/time_filters.py` — три временных фильтра

### SessionFilter
```python
class SessionFilter(BaseFilter):
    name = "session_filter"
    category = FilterCategory.TIME
    priority = FilterPriority.HIGH
    
    # Sessions (UTC times):
    # - ASIA: 00:00 - 08:00
    # - EUROPE: 08:00 - 16:00
    # - US: 13:00 - 22:00
    # - ALL: always allowed
    
    Config params:
    - sessions: List[str] = ["asia", "europe", "us"]
    - timezone: str = "UTC"
```

### WeekdayFilter
```python
class WeekdayFilter(BaseFilter):
    name = "weekday_filter"
    category = FilterCategory.TIME
    priority = FilterPriority.HIGH
    
    Config params:
    - allowed_days: List[int] = [0,1,2,3,4]  # Mon-Fri
    - timezone: str = "UTC"
```

### CooldownFilter
```python
class CooldownFilter(BaseFilter):
    name = "cooldown_filter"
    category = FilterCategory.TIME
    priority = FilterPriority.HIGH
    
    Config params:
    - cooldown_minutes: int = 60
    - after_loss_cooldown: int = 120  # extra cooldown after loss
    - after_win_cooldown: int = 30    # less cooldown after win
```

- [ ] Регистрация фильтров через @register_filter
- [ ] Unit тесты (25+ тестов)
- [ ] run_time_filter_tests.bat

---

## 📁 FILES

```
backend/app/filters/
├── __init__.py           # Update exports
├── base.py               # (no changes)
├── registry.py           # (no changes)
├── chain.py              # (no changes)
└── time_filters.py       # NEW: Session, Weekday, Cooldown

tests/
└── test_time_filters.py  # NEW: 25+ tests
```

---

## 🔧 IMPLEMENTATION DETAILS

### Session Times (UTC)

| Session | Start | End | Overlap |
|---------|-------|-----|---------|
| ASIA | 00:00 | 08:00 | - |
| EUROPE | 08:00 | 16:00 | ASIA-EU: 08:00-09:00 |
| US | 13:00 | 22:00 | EU-US: 13:00-16:00 |

### SignalContext.recent_trades usage

```python
# CooldownFilter checks recent_trades
last_trade = context.recent_trades[-1] if context.recent_trades else None
if last_trade:
    last_trade_time = last_trade["exit_time"]
    time_since = (context.current_time - last_trade_time).total_seconds() / 60
    
    cooldown = self.config.get("cooldown_minutes", 60)
    if last_trade["pnl"] < 0:
        cooldown = self.config.get("after_loss_cooldown", 120)
```

---

## 📝 GIT COMMIT

```
feat: Add time-based filters

- Add SessionFilter for trading session control (Asia/Europe/US)
- Add WeekdayFilter for day-of-week filtering
- Add CooldownFilter with win/loss-based cooldowns
- Add timezone support (UTC/local)
- Add session overlap detection
- Add 25+ unit tests

Chat #38: Filters Time
```

---

**Next chat:** #39 — Filters Volatility
