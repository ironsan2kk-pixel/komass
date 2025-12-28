# 📚 KOMAS v4.0 — Chat Reference

> **Последнее обновление:** 28.12.2025  
> **GitHub:** https://github.com/ironsan2kk-pixel/komass

---

## 🗂️ ОГЛАВЛЕНИЕ

- [Фаза 1: Стабилизация](#фаза-1-стабилизация-15-19)
- [Фаза 2: Dominant Indicator](#фаза-2-dominant-indicator-20-27)
- [Фаза 3: Система пресетов](#фаза-3-система-пресетов-28-33)
- [Фаза 4: Signal Score](#фаза-4-signal-score-34-36)
- [Фаза 5: Общие фильтры](#фаза-5-общие-фильтры-37-44)

---

## Фаза 1: Стабилизация (#15-19)

### #15 — Bugfixes UI ✅
- Monthly Panel белый экран fix
- Stats Panel ошибки fix
- UTF-8 encoding fix
- LogsPanel авто-скролл

### #16 — Bugfixes Backend ✅
- Network Error duplicate timestamps fix
- Endpoints validation
- Error logging

### #17 — Data Futures Only ✅
- Убрали spot торговлю
- Только Binance Futures
- Обновлён список символов

### #18 — Data Period Selection ✅
- UI выбора периода
- Datepicker компоненты
- API start_date/end_date

### #19 — Data Caching ✅
- LRU кэш для OHLCV
- Метрики hit/miss

---

## Фаза 2: Dominant Indicator (#20-27)

### #20 — Dominant Core ✅
- indicators/dominant.py
- Channel calculation
- Fibonacci levels

### #21 — Dominant Signals ✅
- can_long / can_short
- Trend tracking

### #22 — Dominant Filters ✅
- 5 filter types (0-4)

### #23 — Dominant SL Modes ✅
- 5 SL modes

### #24 — Dominant AI Resolution ✅
- Scoring function
- Auto-optimization

### #25 — Dominant Presets DB ✅
- SQLite table
- 125 presets migration

### #26 — Dominant UI Integration ✅
- Indicator selector
- Preset dropdown

### #27 — Dominant Verification ✅
- TradingView comparison
- Signal accuracy check

---

## Фаза 3: Система пресетов (#28-33)

### #28 — Presets Architecture ✅
- Base classes
- Registry pattern

### #29 — Presets TRG Generator ✅
- 200 presets (8×5×5)
- Naming convention

### #30 — Presets TRG Storage ✅
- SQLite storage
- API endpoints

### #31 — Presets User CRUD ✅
- Create/Edit/Delete
- Clone from system

### #32 — Presets Import/Export ✅
- JSON format
- Batch export

### #33 — Presets UI ✅
- Library page
- Search & filters
- Categories

---

## Фаза 4: Signal Score (#34-36)

### #34 — Score Core ✅
- 4 components × 25 points
- Grades A-F
- scoring/signal_score.py

### #35 — Score Multi-TF ✅
- Higher TF loading
- Alignment calculation

### #36 — Score UI ✅
- Badge component
- Score breakdown tooltip
- Filter by grade

---

## Фаза 5: Общие фильтры (#37-44)

### #37 — Filters Architecture ✅
- BaseFilter class
- FilterRegistry
- FilterChain
- 33 unit tests

### #38 — Filters Time ✅
- SessionFilter (Asia/Europe/US)
- WeekdayFilter (Mon-Sun)
- CooldownFilter (win/loss cooldowns)
- Timezone support
- 48 unit tests

### #39 — Filters Volatility ✅
- ATRFilter (min/max ATR range, % or absolute)
- VolumeFilter (ratio vs MA, absolute minimum)
- ExtremeFilter (ATR/volume spike detection, pause period)
- Volatility profiles (conservative/balanced/aggressive)
- Config validation
- 40+ unit tests

### #40 — Filters Trend ⏳
- BTCTrendFilter
- MultiTFFilter
- RegimeFilter

### #41 — Filters Portfolio ⬜
- CorrelationFilter
- DirectionFilter
- SectorFilter

### #42 — Filters Protection ⬜
- EquityCurveFilter
- DrawdownFilter
- StreakFilter
- RecoveryFilter

### #43 — Filters Integration ⬜
- FilterManager
- DB config loading
- Chain application

### #44 — Filters UI ⬜
- Filter settings section
- Category grouping
- Filter presets

---

## 📊 Статистика

| Метрика | Значение |
|---------|----------|
| Всего чатов | 75 |
| Завершено | 25 |
| Прогресс | 33.3% |
| Unit тестов | 150+ |

---

*Обновлено: 28.12.2025*
