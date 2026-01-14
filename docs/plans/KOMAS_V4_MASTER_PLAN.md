# KOMAS v4.0 — MASTER DEVELOPMENT PLAN (Updated)

> **Дата обновления:** 27.12.2024  
> **Статус:** Финализирован + Dominant  
> **Текущая версия:** v3.5  
> **Целевая версия:** v4.0 → v5.0 (Live)

---

## 📋 СВОДКА ПРОЕКТА

| Параметр | Значение |
|----------|----------|
| **Название** | KOMAS Trading Server |
| **Стек** | Python FastAPI + React + SQLite |
| **Деплой** | Windows Server (без Docker) |
| **Биржа данных** | Binance Futures ONLY (без спот) |
| **Таймфреймы** | 1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d |
| **Telegram** | 2 бота для отправки, N каналов по chat_id |
| **Индикаторы** | TRG + Dominant |

---

## 🎯 КЛЮЧЕВЫЕ КОМПОНЕНТЫ v4

### 1. Два индикатора
- **TRG** — ATR-based trend detection (i1/i2)
- **Dominant** — Channel + Fibonacci levels (sensitivity)

### 2. Система пресетов
- 200 системных пресетов TRG (8×5×5)
- 125 системных пресетов Dominant (из GG strategies)
- Пользовательские пресеты (CRUD)
- Import/Export JSON

### 3. Signal Score (0-100)
- Confluence (25 pts)
- Multi-TF Alignment (25 pts)
- Market Context (25 pts)
- Technical Levels (25 pts)
- Grades: A/B/C/D/F

### 4. Модульные фильтры
- **TRG фильтры:** SuperTrend, RSI, ADX, Volume
- **Dominant фильтры:** ATR Condition, RSI, ATR+RSI, Volatility
- **Time:** Session, Weekday, Cooldown
- **Volatility:** ATR, Volume, Extreme
- **Trend:** BTC trend, Multi-TF, Regime
- **Portfolio:** Correlation, Direction, Sector
- **Protection:** Equity Curve, DD, Streak, Recovery

### 5. Bot Backtest
- Multi-pair portfolio бэктест
- Интеграция всех фильтров
- Portfolio equity curve
- Risk Management limits

### 6. Bot Optimizer
- Оптимизация БЕЗ изменения РМ
- Оптимизация набора пар
- Оптимизация фильтров
- Walk-forward + Monte Carlo validation

### 7. Live Engine
- Фоновая подкачка данных (APScheduler)
- WebSocket real-time
- Signal generation
- Position tracking

### 8. Telegram Module
- 2 бота для отправки
- N каналов (по chat_id в UI)
- Cornix формат сообщений
- Routing rules

---

## 📊 ПОЛНЫЙ ПЛАН ПО ЧАТАМ (83 чата)

### 🔧 ФАЗА 1: Стабилизация и база (5 чатов)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 15 | #15 | Bugfixes UI | Monthly белый экран, Stats баги |
| 16 | #16 | Bugfixes Backend | Проверка endpoints, ошибки 500 |
| 17 | #17 | Data Futures Only | Убрать спот, только фьючерсы Binance |
| 18 | #18 | Data Period Selection | Выбор периода (вся история / с даты / до даты) |
| 19 | #19 | Data Caching | Кэширование для ускорения |

**Результат фазы:** Стабильная база, только фьючерсы, выбор периода

---

### 🎯 ФАЗА 2: Dominant Indicator (8 чатов)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 20 | #20 | Dominant Core | `indicators/dominant.py`, расчёт channel + fib levels |
| 21 | #21 | Dominant Signals | Генерация сигналов can_long/can_short |
| 22 | #22 | Dominant Filters | 5 типов фильтров (0-4): ATR, RSI, Combined, Volatility |
| 23 | #23 | Dominant SL Modes | 5 режимов: no, after_tp1/2/3, cascade |
| 24 | #24 | Dominant AI Resolution | Scoring + авто-оптимизация sensitivity |
| 25 | #25 | Dominant Presets DB | Таблица presets + миграция 125 пресетов |
| 26 | #26 | Dominant UI Integration | Селектор индикатора, выбор пресета |
| 27 | #27 | Dominant Verification | Сверка результатов с TradingView |

**Результат фазы:** Полноценный индикатор Dominant с 125 пресетами

---

### 🎛️ ФАЗА 3: Система пресетов (6 чатов)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 28 | #28 | Presets Architecture | base.py, registry, интерфейсы (для обоих индикаторов) |
| 29 | #29 | Presets TRG Generator | Генератор 200 пресетов (8×5×5) |
| 30 | #30 | Presets TRG Storage | Хранение системных пресетов TRG |
| 31 | #31 | Presets User CRUD | Создание/редактирование своих (TRG + Dominant) |
| 32 | #32 | Presets Import/Export | JSON импорт/экспорт |
| 33 | #33 | Presets UI | Библиотека, поиск, создание |

**Результат фазы:** 200 TRG + 125 Dominant + пользовательские пресеты

---

### 📊 ФАЗА 4: Signal Score (3 чата)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 34 | #34 | Score Core | 4 компонента, расчёт 0-100, grades |
| 35 | #35 | Score Multi-TF | Загрузка старших ТФ, alignment |
| 36 | #36 | Score UI | Badge, breakdown, filter by score |

**Результат фазы:** Система оценки качества сигналов

---

### 🔍 ФАЗА 5: Общие фильтры (8 чатов)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 37 | #37 | Filters Architecture | base.py, registry, chain |
| 38 | #38 | Filters Time | Session, Weekday, Cooldown |
| 39 | #39 | Filters Volatility | ATR, Volume, Extreme |
| 40 | #40 | Filters Trend | BTC trend, Multi-TF, Regime |
| 41 | #41 | Filters Portfolio | Correlation, Direction, Sector |
| 42 | #42 | Filters Protection | Equity Curve, DD, Streak, Recovery |
| 43 | #43 | Filters Integration | FilterManager, chain of filters |
| 44 | #44 | Filters UI | Полный UI настройки фильтров |

**Результат фазы:** Модульная система фильтров

---

### ⚡ ФАЗА 6: Оптимизация пресетов (5 чатов)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 45 | #45 | Optimizer Multi-Pair Core | Multi-pair бэктест движок |
| 46 | #46 | Optimizer Modes | Quick/Standard/Smart/Full |
| 47 | #47 | Optimizer Results | Ranking, metrics, export |
| 48 | #48 | Optimizer Heatmap | 200×N matrix visualization |
| 49 | #49 | Optimizer UI | Полный UI оптимизации пресетов |

**Результат фазы:** Multi-pair оптимизация пресетов

---

### 🤖 ФАЗА 7: Конфигурация бота (4 чата)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 50 | #50 | Bot Config Model | BotConfig, RiskManagement структуры |
| 51 | #51 | Bot Config Storage | SQLite CRUD для ботов |
| 52 | #52 | Bot Config UI | Форма создания/редактирования |
| 53 | #53 | Bot Pairs Selection | Мультивыбор пар, группы |

**Результат фазы:** Конфигурация бота с РМ

---

### 📈 ФАЗА 8: Bot Backtest (6 чатов)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 54 | #54 | Bot Backtest Core | Portfolio бэктест движок |
| 55 | #55 | Bot Backtest Positions | Управление позициями, TP/SL |
| 56 | #56 | Bot Backtest Filters | Интеграция всех фильтров |
| 57 | #57 | Bot Backtest Equity | Portfolio equity curve |
| 58 | #58 | Bot Backtest Stats | Sharpe, Calmar, Monthly, per-pair |
| 59 | #59 | Bot Backtest UI | UI бэктеста бота |

**Результат фазы:** Полноценный portfolio бэктест

---

### ⚙️ ФАЗА 9: Оптимизация бота (5 чатов)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 60 | #60 | Bot Optimizer Core | Движок оптимизации (без РМ!) |
| 61 | #61 | Bot Optimizer Pairs | Оптимизация набора пар |
| 62 | #62 | Bot Optimizer Filters | Оптимизация настроек фильтров |
| 63 | #63 | Bot Optimizer Validation | Walk-forward, Monte Carlo |
| 64 | #64 | Bot Optimizer UI | UI оптимизации бота |

**Результат фазы:** Оптимизированный бот готовый к live

---

### 🔴 ФАЗА 10: Live Engine (6 чатов)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 65 | #65 | Live Data Fetcher | APScheduler, фоновая подкачка |
| 66 | #66 | Live WebSocket | WebSocket к Binance, reconnect |
| 67 | #67 | Live Signal Engine | Генерация сигналов real-time |
| 68 | #68 | Live Position Tracker | TP/SL мониторинг, PnL |
| 69 | #69 | Live State Manager | Persist state, recovery |
| 70 | #70 | Live UI Dashboard | Status, positions, signals |

**Результат фазы:** 24/7 мониторинг и сигналы

---

### 📲 ФАЗА 11: Telegram (6 чатов)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 71 | #71 | TG Bot Manager | 2 бота, базовая отправка |
| 72 | #72 | TG Channel Manager | N каналов по chat_id |
| 73 | #73 | TG Cornix Formatter | Формат для Cornix (TRG + Dominant) |
| 74 | #74 | TG Signal Router | Маршрутизация, правила |
| 75 | #75 | TG Notifications | TP/SL/Update уведомления |
| 76 | #76 | TG UI | Настройка в UI |

**Результат фазы:** Telegram интеграция

---

### 🎨 ФАЗА 12: Дизайн (4 чата)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 77 | #77 | Design System | Цвета, типографика, spacing |
| 78 | #78 | Design Components | Button, Card, Input, Modal |
| 79 | #79 | Design Pages | Редизайн всех страниц |
| 80 | #80 | Design Mobile | Адаптивность |

**Результат фазы:** Новый современный UI

---

### ✅ ФАЗА 13: QA и тестирование (8 чатов)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 81 | #81 | QA: Data Module | Чек-лист данных |
| 82 | #82 | QA: Indicators | Чек-лист TRG + Dominant |
| 83 | #83 | QA: Presets Module | Чек-лист пресетов |
| 84 | #84 | QA: Filters Module | Чек-лист фильтров |
| 85 | #85 | QA: Bot Backtest | Чек-лист бэктеста |
| 86 | #86 | QA: Live Module | Чек-лист live |
| 87 | #87 | QA: Telegram Module | Чек-лист Telegram |
| 88 | #88 | QA: Full Integration | E2E тестирование |

**Результат фазы:** Полностью протестированная система

---

### 📦 ФАЗА 14: GitHub и деплой (6 чатов)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 89 | #89 | Git: Structure | .gitignore, README, structure |
| 90 | #90 | Git: Branches | Branch strategy, PR flow |
| 91 | #91 | Git: CI/CD | GitHub Actions |
| 92 | #92 | Deploy: Batfiles | Все батники |
| 93 | #93 | Deploy: Documentation | Полная документация |
| 94 | #94 | Deploy: Final Package | ZIP release |

**Результат фазы:** Production-ready пакет

---

### 🚀 ФАЗА 15: Финализация (3 чата)

| # | Чат | Название | Задачи |
|---|-----|----------|--------|
| 95 | #95 | Final: Review | Полный обзор проекта |
| 96 | #96 | Final: Polish | Финальная полировка |
| 97 | #97 | Final: Release | Релиз v4.0 |

**Результат фазы:** KOMAS v4.0 Released! 🎉

---

## 📊 СВОДНАЯ ТАБЛИЦА

| Фаза | Название | Чаты | Кол-во |
|------|----------|------|--------|
| 1 | Стабилизация | #15-19 | 5 |
| **2** | **Dominant Indicator** | **#20-27** | **8** |
| 3 | Пресеты | #28-33 | 6 |
| 4 | Signal Score | #34-36 | 3 |
| 5 | Общие фильтры | #37-44 | 8 |
| 6 | Опт. пресетов | #45-49 | 5 |
| 7 | Конфиг бота | #50-53 | 4 |
| 8 | Bot Backtest | #54-59 | 6 |
| 9 | Опт. бота | #60-64 | 5 |
| 10 | Live Engine | #65-70 | 6 |
| 11 | Telegram | #71-76 | 6 |
| 12 | Дизайн | #77-80 | 4 |
| 13 | QA | #81-88 | 8 |
| 14 | GitHub/Deploy | #89-94 | 6 |
| 15 | Финализация | #95-97 | 3 |
| **ИТОГО** | | | **83** |

---

## 📁 СТРУКТУРА МОДУЛЕЙ

```
backend/app/
├── indicators/
│   ├── __init__.py
│   ├── base.py              # BaseIndicator (абстрактный класс)
│   ├── trg.py               # TRG индикатор
│   └── dominant.py          # Dominant индикатор
│
├── filters/
│   ├── __init__.py
│   ├── base.py              # BaseFilter
│   ├── supertrend.py        # TRG: SuperTrend
│   ├── rsi.py               # Общий RSI
│   ├── adx.py               # TRG: ADX
│   ├── volume.py            # TRG: Volume
│   ├── atr_condition.py     # Dominant: filter_type=1
│   ├── volatility.py        # Dominant: filter_type=4
│   ├── time_filters.py      # Session, Weekday, Cooldown
│   ├── trend_filters.py     # BTC trend, Multi-TF, Regime
│   ├── portfolio_filters.py # Correlation, Direction, Sector
│   └── protection_filters.py # Equity Curve, DD, Streak
│
├── presets/
│   ├── __init__.py
│   ├── manager.py           # PresetManager (CRUD)
│   ├── trg_generator.py     # Генератор 200 TRG пресетов
│   └── migrations/
│       ├── seed_trg.py      # 200 TRG пресетов
│       └── seed_dominant.py # 125 Dominant пресетов
│
├── alerts/
│   ├── __init__.py
│   ├── formatter.py         # Cornix format
│   └── telegram.py          # Отправка
│
├── bot/
│   ├── __init__.py
│   ├── config.py            # BotConfig model
│   ├── backtest.py          # Portfolio backtest
│   ├── optimizer.py         # Bot optimizer
│   └── live.py              # Live engine
│
└── api/
    ├── indicator_routes.py  # Расчёт + бэктест
    ├── preset_routes.py     # API пресетов
    ├── filter_routes.py     # API фильтров
    ├── bot_routes.py        # API ботов
    ├── live_routes.py       # API live
    └── alert_routes.py      # API алертов
```

---

## 🗄️ СХЕМА БД (дополнения)

```sql
-- Таблица пресетов
CREATE TABLE presets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    indicator TEXT NOT NULL CHECK(indicator IN ('trg', 'dominant')),
    symbol TEXT,                    -- NULL = универсальный
    timeframe TEXT,                 -- NULL = любой
    category TEXT CHECK(category IN ('scalp', 'short-term', 'mid-term', 'swing', 'long-term', 'special')),
    params JSON NOT NULL,
    source TEXT DEFAULT 'manual',   -- 'pine_script', 'optimizer', 'manual', 'system'
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы
CREATE INDEX idx_presets_indicator ON presets(indicator);
CREATE INDEX idx_presets_category ON presets(category);
CREATE INDEX idx_presets_symbol ON presets(symbol);
```

---

## 📋 ДЕТАЛИЗАЦИЯ ФАЗЫ 2: Dominant Indicator

### Чат #20: Dominant Core

**Задачи:**
- [ ] Создать `indicators/base.py` — абстрактный BaseIndicator
- [ ] Создать `indicators/dominant.py` — расчёт уровней
- [ ] Channel: `high_line`, `low_line`, `channel_range`
- [ ] Fibonacci: `fib_236`, `fib_786`, `imba_trend_line` (fib_5)
- [ ] Параметры: `sensitivity` (12-60)
- [ ] Unit тесты

### Чат #21: Dominant Signals

**Задачи:**
- [ ] Условия `can_long`: close >= imba_trend_line AND close >= fib_236 AND close > open
- [ ] Условия `can_short`: close <= imba_trend_line AND close <= fib_786 AND close < open
- [ ] Трекинг тренда: `is_long_trend`, `is_short_trend`
- [ ] Close on reverse signal
- [ ] Unit тесты

### Чат #22: Dominant Filters

**Задачи:**
- [ ] Filter Type 0: Без фильтра
- [ ] Filter Type 1: ATR Condition (volume spike)
- [ ] Filter Type 2: RSI Condition (overbought/oversold)
- [ ] Filter Type 3: ATR + RSI Combined
- [ ] Filter Type 4: Volatility Condition
- [ ] Unit тесты каждого фильтра

### Чат #23: Dominant SL Modes

**Задачи:**
- [ ] Mode: No Breakeven (фиксированный SL)
- [ ] Mode: After 1st TP (SL → Entry после TP1)
- [ ] Mode: After 2nd TP (SL → Entry после TP2)
- [ ] Mode: After 3rd TP (SL → Entry после TP3)
- [ ] Mode: Cascade (SL двигается за каждым TP)
- [ ] Unit тесты

### Чат #24: Dominant AI Resolution

**Задачи:**
- [ ] Scoring функция `calculate_sensitivity_score()`
- [ ] Метрики: profit, winrate, stability, drawdown
- [ ] Авто-оптимизация sensitivity (12-60)
- [ ] Интеграция с ProcessPoolExecutor
- [ ] Unit тесты

### Чат #25: Dominant Presets DB

**Задачи:**
- [ ] Создать таблицу `presets` в SQLite
- [ ] Миграция всех 125 пресетов из GG Pine Script
- [ ] API: GET /api/presets/list
- [ ] API: GET /api/presets/{id}
- [ ] Unit тесты

### Чат #26: Dominant UI Integration

**Задачи:**
- [ ] Селектор индикатора в SettingsSidebar (TRG / Dominant)
- [ ] Динамические параметры (i1/i2 для TRG, sensitivity для Dominant)
- [ ] Выбор пресета с категориями
- [ ] Автоподстановка параметров из пресета
- [ ] Тесты UI

### Чат #27: Dominant Verification

**Задачи:**
- [ ] Сверка сигналов с TradingView (минимум 3 пары)
- [ ] Сверка статистики (Win Rate, PnL)
- [ ] Исправление расхождений
- [ ] Документация различий
- [ ] Финальный чек-лист

---

## 📊 СРАВНЕНИЕ ИНДИКАТОРОВ

| Параметр | TRG | Dominant |
|----------|-----|----------|
| **Основа** | ATR + Multiplier | Channel + Fibonacci |
| **Главные параметры** | i1 (10-200), i2 (1-10) | sensitivity (12-60) |
| **TP уровней** | 10 | 4 |
| **TP расчёт** | % от цены | % от цены (Resolution/Adaptive/Default) |
| **SL режимы** | fixed, breakeven, cascade | no, after_tp1/2/3, cascade |
| **Фильтры** | SuperTrend, RSI, ADX, Volume | 5 типов (0-4) |
| **AI оптимизация** | ❌ (наша многоядерная) | ✅ AI Resolution v5 |
| **Пресеты** | 200 (автогенерация) | 125 (GG strategies) |
| **Cornix алерты** | ✅ | ✅ |

---

## 🚀 СТАРТ

**Первый чат:** `Komas v4 Chat #15: Bugfixes UI`

**После Фазы 1 переходим к:**
`Komas v4 Chat #20: Dominant Core`

---

*План обновлён: 27.12.2024*
*GitHub: https://github.com/ironsan2kk-pixel/komass*
