# KOMAS v4 — Трекер прогресса

> **Обновляется после каждого чата**  
> **Последнее обновление:** 27.12.2025, Chat #17

---

## 📊 ОБЩИЙ ПРОГРЕСС

```
Версия:     v3.5 → v4.0
Прогресс:   ███░░░░░░░░░░░░░░░░░ 3/90 чатов (3.3%)
Фаза:       1 — Стабилизация (3/5)
```

---

## 🎯 ТЕКУЩАЯ ФАЗА

### Фаза 1: Стабилизация (#15-#19)

| # | Чат | Статус | Коммит |
|---|-----|--------|--------|
| 15 | Bugfixes UI | ✅ | `df09cee` |
| 16 | Bugfixes Backend | ✅ | `de6cd90` |
| 17 | Data Futures Only | ✅ | — |
| **18** | **Data Period Selection** | **⏳ NEXT** | — |
| 19 | QA Checkpoint #1 | ⬜ | — |

---

## ⏭️ СЛЕДУЮЩИЙ ЧАТ

### Chat #18: Data Period Selection

**Задачи:**
- [ ] DatePicker компоненты в SettingsSidebar
- [ ] start_date, end_date параметры
- [ ] Фильтрация данных по периоду в бэктесте
- [ ] Валидация: end > start
- [ ] Обновить /api/indicator/calculate

**Файлы:**
```
frontend/src/components/Indicator/SettingsSidebar.jsx
backend/app/api/indicator_routes.py
```

**Критерии завершения:**
- [ ] Можно выбрать период дат
- [ ] Бэктест работает на выбранном периоде
- [ ] ZIP готов
- [ ] Git commit написан
- [ ] docs/ обновлены

---

## 📅 ПОЛНЫЙ ПЛАН С QA CHECKPOINTS

### Фаза 1: Стабилизация (#15-19) — 5 чатов
```
#15 ✅ Bugfixes UI
#16 ✅ Bugfixes Backend
#17 ✅ Data Futures Only
#18 ⬜ Data Period Selection
#19 ⬜ QA Checkpoint #1
```

### Фаза 2: Dominant Indicator (#20-28) — 9 чатов
```
#20 ⬜ Dominant: Core (channel + fib)
#21 ⬜ Dominant: Signals
#22 ⬜ Dominant: Filters (5 types)
#23 ⬜ Dominant: SL Modes (5 modes)
#24 ⬜ QA Checkpoint #2
#25 ⬜ Dominant: AI Resolution
#26 ⬜ Dominant: 37 Presets DB
#27 ⬜ Dominant: UI Integration
#28 ⬜ Dominant: TradingView Verification
```

### Фаза 3: Preset System (#29-35) — 7 чатов
```
#29 ⬜ QA Checkpoint #3
#30 ⬜ Presets: Architecture
#31 ⬜ Presets: TRG Generator (200)
#32 ⬜ Presets: Storage
#33 ⬜ Presets: User CRUD
#34 ⬜ QA Checkpoint #4
#35 ⬜ Presets: Import/Export
#36 ⬜ Presets: UI Library
```

### Фаза 4: Signal Score (#37-40) — 4 чата
```
#37 ⬜ Score: Core (4×25 points)
#38 ⬜ Score: Multi-TF
#39 ⬜ QA Checkpoint #5
#40 ⬜ Score: UI Badges
```

### Фаза 5: General Filters (#41-49) — 9 чатов
```
#41 ⬜ Filters: Architecture
#42 ⬜ Filters: Time
#43 ⬜ Filters: Volatility
#44 ⬜ QA Checkpoint #6
#45 ⬜ Filters: Trend
#46 ⬜ Filters: Portfolio
#47 ⬜ Filters: Protection
#48 ⬜ Filters: Integration
#49 ⬜ QA Checkpoint #7
```

### Фаза 6: Preset Optimization (#50-54) — 5 чатов
```
#50 ⬜ Preset Optimizer: Core
#51 ⬜ Preset Optimizer: Modes
#52 ⬜ Preset Optimizer: Results
#53 ⬜ Preset Optimizer: Validation
#54 ⬜ QA Checkpoint #8
```

### Фаза 7: Bot Configuration (#55-59) — 5 чатов
```
#55 ⬜ Bot: Config Structure
#56 ⬜ Bot: Pair Selection
#57 ⬜ Bot: Filter Integration
#58 ⬜ Bot: UI
#59 ⬜ QA Checkpoint #9
```

### Фаза 8: Bot Backtest (#60-66) — 7 чатов
```
#60 ⬜ Bot Backtest: Core
#61 ⬜ Bot Backtest: RM Integration
#62 ⬜ Bot Backtest: Filters
#63 ⬜ Bot Backtest: Stats
#64 ⬜ QA Checkpoint #10
#65 ⬜ Bot Backtest: Equity
#66 ⬜ Bot Backtest: UI
```

### Фаза 9: Bot Optimization (#67-71) — 5 чатов
```
#67 ⬜ Bot Optimizer: Core
#68 ⬜ Bot Optimizer: Pairs
#69 ⬜ QA Checkpoint #11
#70 ⬜ Bot Optimizer: Filters
#71 ⬜ Bot Optimizer: Validation
```

### Фаза 10: Live Engine (#72-78) — 7 чатов
```
#72 ⬜ Live: Data Fetcher
#73 ⬜ Live: WebSocket
#74 ⬜ QA Checkpoint #12
#75 ⬜ Live: Signal Generator
#76 ⬜ Live: Position Tracker
#77 ⬜ Live: Dashboard
#78 ⬜ Live: UI
```

### Фаза 11: Telegram (#79-85) — 7 чатов
```
#79 ⬜ QA Checkpoint #13
#80 ⬜ Telegram: Bot Core
#81 ⬜ Telegram: Channel Manager
#82 ⬜ Telegram: Cornix Formatter
#83 ⬜ Telegram: Signal Router
#84 ⬜ QA Checkpoint #14
#85 ⬜ Telegram: Notifications
#86 ⬜ Telegram: UI
```

### Фаза 12: UI Redesign (#87-91) — 5 чатов
```
#87 ⬜ Design: System
#88 ⬜ Design: Components
#89 ⬜ QA Checkpoint #15
#90 ⬜ Design: Pages
#91 ⬜ Design: Mobile
```

### Фаза 13: Final QA (#92-95) — 4 чата
```
#92 ⬜ QA: Full E2E Testing
#93 ⬜ QA: Performance
#94 ⬜ QA: Security
#95 ⬜ QA: Final Fixes
```

### Фаза 14: Release (#96-98) — 3 чата
```
#96 ⬜ Deploy: Batfiles & Docs
#97 ⬜ Deploy: GitHub Release
#98 ⬜ v4.0 RELEASE 🎉
```

---

## 📊 СВОДКА

| Фаза | Чаты | Прогресс |
|------|------|----------|
| 1. Стабилизация | #15-19 | ███░░ 60% |
| 2. Dominant | #20-28 | ░░░░░ 0% |
| 3. Presets | #29-36 | ░░░░░ 0% |
| 4. Signal Score | #37-40 | ░░░░░ 0% |
| 5. Filters | #41-49 | ░░░░░ 0% |
| 6. Preset Optimizer | #50-54 | ░░░░░ 0% |
| 7. Bot Config | #55-59 | ░░░░░ 0% |
| 8. Bot Backtest | #60-66 | ░░░░░ 0% |
| 9. Bot Optimizer | #67-71 | ░░░░░ 0% |
| 10. Live Engine | #72-78 | ░░░░░ 0% |
| 11. Telegram | #79-86 | ░░░░░ 0% |
| 12. UI Redesign | #87-91 | ░░░░░ 0% |
| 13. Final QA | #92-95 | ░░░░░ 0% |
| 14. Release | #96-98 | ░░░░░ 0% |

**Всего:** 98 чатов (включая 15 QA Checkpoints)

---

## ✅ ЗАВЕРШЁННЫЕ ЧАТЫ

| # | Название | Коммит | Что сделали |
|---|----------|--------|-------------|
| 15 | Bugfixes UI | `df09cee` | MonthlyPanel, StatsPanel, UTF-8 |
| 16 | Bugfixes Backend | `de6cd90` | Duplicate timestamps, mojibake |
| 17 | Data Futures Only | — | Удалён Spot, только Futures |

---

## 🐛 ИЗВЕСТНЫЕ БАГИ

| Баг | Статус | Чат |
|-----|--------|-----|
| Duplicate timestamps | ✅ Fixed | #16 |
| Mojibake UI | ✅ Fixed | #15 |
| Mojibake Backend | ✅ Fixed | #16 |
| MonthlyPanel crash | ✅ Fixed | #15 |

---

*Обновляется после каждого чата*
