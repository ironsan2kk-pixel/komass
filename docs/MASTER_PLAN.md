# KOMAS v4 — Master Plan

> **Всего чатов:** 98 (включая 15 QA Checkpoints)  
> **Старт:** Chat #15  
> **Финиш:** Chat #98 — v4.0 Release

---

## 🎯 ЦЕЛЬ v4.0

Трансформация KOMAS из single-pair indicator tool в полноценную trading bot platform:

- **2 индикатора:** TRG + Dominant
- **237 пресетов:** 200 TRG + 37 Dominant
- **Signal Score:** 0-100 баллов, грейды A-F
- **Модульные фильтры:** 5 категорий
- **Bot Configuration:** Multi-pair portfolios
- **Live Trading:** Real-time signals
- **Telegram:** 2 бота, N каналов, Cornix format

---

## 📋 ПОЛНЫЙ ПЛАН

### Фаза 1: Стабилизация (#15-19) — 5 чатов

| # | Название | Описание |
|---|----------|----------|
| 15 | ✅ Bugfixes UI | MonthlyPanel, StatsPanel, UTF-8 |
| 16 | ✅ Bugfixes Backend | Timestamps, mojibake, imports |
| 17 | ✅ Data Futures Only | Удалён Spot |
| 18 | ⬜ Data Period Selection | DatePicker, фильтрация периода |
| 19 | ⬜ QA Checkpoint #1 | Проверка Фазы 1 |

---

### Фаза 2: Dominant Indicator (#20-28) — 9 чатов

| # | Название | Описание |
|---|----------|----------|
| 20 | Dominant: Core | Channel + Fibonacci levels |
| 21 | Dominant: Signals | can_long, can_short, close on reverse |
| 22 | Dominant: Filters | 5 filter types (None, ATR, RSI, ATR+RSI, Volatility) |
| 23 | Dominant: SL Modes | 5 modes (No SL, After TP1/2/3, Cascade) |
| 24 | QA Checkpoint #2 | Проверка |
| 25 | Dominant: AI Resolution | Scoring, auto-optimize sensitivity |
| 26 | Dominant: Presets DB | 37 пресетов из Pine Script |
| 27 | Dominant: UI Integration | Selector TRG/Dominant |
| 28 | Dominant: Verification | Сверка с TradingView |

---

### Фаза 3: Preset System (#29-36) — 8 чатов

| # | Название | Описание |
|---|----------|----------|
| 29 | QA Checkpoint #3 | Проверка |
| 30 | Presets: Architecture | PresetBase, Registry |
| 31 | Presets: TRG Generator | 200 пресетов (8×5×5) |
| 32 | Presets: Storage | SQLite, lazy loading |
| 33 | Presets: User CRUD | Create, edit, delete, clone |
| 34 | QA Checkpoint #4 | Проверка |
| 35 | Presets: Import/Export | JSON, validation |
| 36 | Presets: UI Library | Cards, search, filters |

---

### Фаза 4: Signal Score (#37-40) — 4 чата

| # | Название | Описание |
|---|----------|----------|
| 37 | Score: Core | 4 компонента × 25 баллов |
| 38 | Score: Multi-TF | Alignment с 4H, 1D |
| 39 | QA Checkpoint #5 | Проверка |
| 40 | Score: UI Badges | Грейды A-F, breakdown |

**Компоненты Score:**
- Confluence (25): Совпадение индикаторов
- Multi-TF (25): Higher TF alignment
- Market Context (25): Trend + volatility
- Tech Levels (25): S/R proximity

---

### Фаза 5: General Filters (#41-49) — 9 чатов

| # | Название | Описание |
|---|----------|----------|
| 41 | Filters: Architecture | FilterBase, FilterChain |
| 42 | Filters: Time | Session, Weekday, Cooldown |
| 43 | Filters: Volatility | ATR, Volume, Extreme |
| 44 | QA Checkpoint #6 | Проверка |
| 45 | Filters: Trend | BTC Trend, Multi-TF, Regime |
| 46 | Filters: Portfolio | Correlation, Direction, Sector |
| 47 | Filters: Protection | Equity Curve, Max DD, Streak |
| 48 | Filters: Integration | FilterManager, logging |
| 49 | QA Checkpoint #7 | Проверка |

---

### Фаза 6: Preset Optimization (#50-54) — 5 чатов

| # | Название | Описание |
|---|----------|----------|
| 50 | Preset Optimizer: Core | Multi-pair backtest |
| 51 | Preset Optimizer: Modes | Quick, Standard, Smart, Full |
| 52 | Preset Optimizer: Results | Heatmap preset × pair |
| 53 | Preset Optimizer: Validation | Walk-forward, Monte Carlo |
| 54 | QA Checkpoint #8 | Проверка |

---

### Фаза 7: Bot Configuration (#55-59) — 5 чатов

| # | Название | Описание |
|---|----------|----------|
| 55 | Bot: Config Structure | BotConfig, Risk Management |
| 56 | Bot: Pair Selection | Multi-pair, statistics |
| 57 | Bot: Filter Integration | All filters config |
| 58 | Bot: UI | Page Bots, create form |
| 59 | QA Checkpoint #9 | Проверка |

**Bot Config:**
- deposit, risk_per_trade (1-5%)
- max_positions (1-10), leverage (1-125x)
- daily_dd_limit

---

### Фаза 8: Bot Backtest (#60-66) — 7 чатов

| # | Название | Описание |
|---|----------|----------|
| 60 | Bot Backtest: Core | Multi-pair engine |
| 61 | Bot Backtest: RM | Risk Management integration |
| 62 | Bot Backtest: Filters | Apply all filters |
| 63 | Bot Backtest: Stats | Portfolio statistics |
| 64 | QA Checkpoint #10 | Проверка |
| 65 | Bot Backtest: Equity | Portfolio equity curve |
| 66 | Bot Backtest: UI | Interface, export |

---

### Фаза 9: Bot Optimization (#67-71) — 5 чатов

| # | Название | Описание |
|---|----------|----------|
| 67 | Bot Optimizer: Core | БЕЗ изменения RM |
| 68 | Bot Optimizer: Pairs | Correlation, diversification |
| 69 | QA Checkpoint #11 | Проверка |
| 70 | Bot Optimizer: Filters | Filter parameters |
| 71 | Bot Optimizer: Validation | Walk-forward |

---

### Фаза 10: Live Engine (#72-78) — 7 чатов

| # | Название | Описание |
|---|----------|----------|
| 72 | Live: Data Fetcher | APScheduler, background |
| 73 | Live: WebSocket | Real-time prices |
| 74 | QA Checkpoint #12 | Проверка |
| 75 | Live: Signal Generator | Monitor for signals |
| 76 | Live: Position Tracker | Virtual positions |
| 77 | Live: Dashboard | Real-time stats |
| 78 | Live: UI | Start/Stop, activity log |

---

### Фаза 11: Telegram (#79-86) — 8 чатов

| # | Название | Описание |
|---|----------|----------|
| 79 | QA Checkpoint #13 | Проверка |
| 80 | Telegram: Bot Core | 2 бота setup |
| 81 | Telegram: Channels | N каналов, chat_id |
| 82 | Telegram: Cornix | Cornix format |
| 83 | Telegram: Router | Signal routing rules |
| 84 | QA Checkpoint #14 | Проверка |
| 85 | Telegram: Notifications | TP/SL hits, daily summary |
| 86 | Telegram: UI | Settings, test send |

**Cornix Format:**
```
#BTCUSDT
LONG
Entry: 45000
TP1: 45500 (50%)
TP2: 46000 (30%)
SL: 44000
Leverage: 10x
```

---

### Фаза 12: UI Redesign (#87-91) — 5 чатов

| # | Название | Описание |
|---|----------|----------|
| 87 | Design: System | Colors, typography, spacing |
| 88 | Design: Components | Buttons, cards, inputs |
| 89 | QA Checkpoint #15 | Проверка |
| 90 | Design: Pages | All pages redesign |
| 91 | Design: Mobile | Responsive, touch |

---

### Фаза 13: Final QA (#92-95) — 4 чата

| # | Название | Описание |
|---|----------|----------|
| 92 | QA: Full E2E | Complete user journeys |
| 93 | QA: Performance | Load testing, optimization |
| 94 | QA: Security | Input validation, auth |
| 95 | QA: Final Fixes | Last bug fixes |

---

### Фаза 14: Release (#96-98) — 3 чата

| # | Название | Описание |
|---|----------|----------|
| 96 | Deploy: Batfiles | install, start, stop, update |
| 97 | Deploy: GitHub | Release, tags, docs |
| 98 | v4.0 RELEASE 🎉 | Final package |

---

## 📊 СТАТИСТИКА

| Метрика | Значение |
|---------|----------|
| Всего чатов | 98 |
| QA Checkpoints | 15 |
| Фаз | 14 |
| Завершено | 3 |
| Осталось | 95 |

---

*Документ создан 27.12.2025*
