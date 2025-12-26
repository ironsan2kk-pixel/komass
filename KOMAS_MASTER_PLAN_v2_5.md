# KOMAS MASTER PLAN v2.5

> **Последнее обновление:** 2025-12-25
> **Статус:** В разработке
> **Прогресс:** 68%

---

## 🎯 ЦЕЛЬ ПРОЕКТА

Комплексная система для автоматизированной торговли криптовалютами:
- Порт Pine Script стратегии на Python
- Веб-интерфейс для управления
- Работа 24/7 на Windows Server
- Модульная архитектура с плагинами

---

## 🏗️ АРХИТЕКТУРА

```
┌─────────────────────────────────────────────────────────┐
│                    KOMAS TRADING SERVER                  │
├─────────────────────────────────────────────────────────┤
│  Frontend (React + Vite + TailwindCSS)                  │
│  ├── Dashboard, Indicator, Data, Signals                │
│  ├── Calendar, Settings, Performance                    │
│  └── lightweight-charts для графиков                    │
├─────────────────────────────────────────────────────────┤
│  Backend (FastAPI + SQLite + APScheduler)               │
│  ├── core/ (config, logger, database)                   │
│  ├── api/ (routes для всех модулей)                     │
│  ├── indicators/ (base classes, loader, registry)       │
│  └── plugins/ (TRG и другие индикаторы)                 │
├─────────────────────────────────────────────────────────┤
│  Data Layer                                              │
│  ├── Binance API (REST + WebSocket)                     │
│  ├── Parquet storage                                     │
│  └── SQLite (settings, signals, results)                │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 КОНЦЕПЦИЯ ПЛАГИНОВ

Каждый индикатор = отдельный плагин в `plugins/`:

```
plugins/trg/
├── manifest.json      # Метаданные плагина (v1.5.0)
├── __init__.py        # Экспорты
├── indicator.py       # TRGIndicator (расчёт)
├── signals.py         # TRGSignalGenerator
├── trading.py         # TRGTradingSystem (TP/SL/re-entry)
├── optimizer.py       # TRGOptimizer (многоядерный)
├── backtest.py        # TRGBacktest
├── ui_schema.py       # UI Schema для фронтенда ✅ NEW!
└── filters/           # Модуль фильтров
    ├── __init__.py
    ├── config.py      # TRGFilterConfig + 11 пресетов
    ├── manager.py     # TRGFilterManager + 45 конфигов
    ├── supertrend.py
    ├── rsi.py
    ├── adx.py
    └── volume.py
```

---

## 📊 МОДУЛИ И СТАТУСЫ

### Легенда:
- 🔴 Не начато
- 🟡 В процессе
- 🟢 Готово
- 🔄 Требует обновления

### Этап 1 — Core (100% ✅)
| Модуль | Статус | Файлы |
|--------|--------|-------|
| Config | 🟢 | `core/config.py` |
| Logger | 🟢 | `core/logger.py` |
| Database | 🟢 | `core/database.py` |

### Этап 2 — Data (100% ✅)
| Модуль | Статус | Файлы |
|--------|--------|-------|
| Binance Client | 🟢 | `core/data/binance.py` |
| Storage | 🟢 | `core/data/storage.py` |
| Manager | 🟢 | `core/data/manager.py` |
| WebSocket | 🟢 | `core/data/websocket.py` |
| API | 🟢 | `api/data.py`, `api/ws.py` |

### Этап 3 — Indicators Base (100% ✅)
| Модуль | Статус | Файлы |
|--------|--------|-------|
| BaseIndicator | 🟢 | `indicators/base/indicator.py` |
| BaseTradingSystem | 🟢 | `indicators/base/trading.py` |
| BaseFilter | 🟢 | `indicators/base/filter.py` |
| BaseOptimizer | 🟢 | `indicators/base/optimizer.py` |
| BaseBacktest | 🟢 | `indicators/base/backtest.py` |
| PluginLoader | 🟢 | `indicators/loader.py` |
| Registry | 🟢 | `indicators/registry.py` |

### Этап 4 — TRG Plugin (100% ✅) 🎉
| Модуль | Статус | Файлы | Тесты |
|--------|--------|-------|-------|
| Indicator | 🟢 | `plugins/trg/indicator.py` | 4/4 ✅ |
| Signals | 🟢 | `plugins/trg/signals.py` | ✅ |
| Trading | 🟢 | `plugins/trg/trading.py` | 28/28 ✅ |
| Filters | 🟢 | `plugins/trg/filters/` | 11/11 ✅ |
| Optimizer | 🟢 | `plugins/trg/optimizer.py` | 14/14 ✅ |
| Backtest | 🟢 | `plugins/trg/backtest.py` | 23/23 ✅ |
| UI Schema | 🟢 | `plugins/trg/ui_schema.py` | 10/10 ✅ |

### Этап 5 — API (40%)
| Модуль | Статус | Файлы |
|--------|--------|-------|
| Data API | 🟢 | `api/data.py` |
| WebSocket API | 🟢 | `api/ws.py` |
| Database API | 🟢 | `api/database.py` |
| Plugins API | 🟢 | `api/plugins.py` |
| Indicator API | 🔴 | `api/indicator.py` |
| Signals API | 🔴 | `api/signals.py` |

### Этап 6 — Frontend (20%)
| Модуль | Статус | Файлы |
|--------|--------|-------|
| App Layout | 🟢 | `App.jsx` |
| Data Page | 🟢 | `pages/Data.jsx` |
| Indicator Page | 🔄 | `pages/Indicator.jsx` |
| Signals Page | 🔴 | `pages/Signals.jsx` |
| Settings Page | 🔴 | `pages/Settings.jsx` |

### Этапы 7-11 (0%)
- Notifications (Telegram, Discord)
- Bots System
- Calendar Integration
- Deployment Scripts
- Documentation

---

## 📁 СТРУКТУРА ФАЙЛОВ

```
komas_indicator/
├── backend/
│   └── app/
│       ├── main.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── logger.py
│       │   ├── database.py
│       │   └── data/
│       │       ├── __init__.py
│       │       ├── binance.py
│       │       ├── storage.py
│       │       ├── manager.py
│       │       └── websocket.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── data.py
│       │   ├── ws.py
│       │   ├── database.py
│       │   └── plugins.py
│       ├── indicators/
│       │   ├── __init__.py
│       │   ├── loader.py
│       │   ├── registry.py
│       │   └── base/
│       │       ├── __init__.py
│       │       ├── indicator.py
│       │       ├── trading.py
│       │       ├── filter.py
│       │       ├── optimizer.py
│       │       └── backtest.py
│       └── plugins/
│           └── trg/
│               ├── manifest.json (v1.5.0)
│               ├── __init__.py
│               ├── indicator.py
│               ├── signals.py
│               ├── trading.py
│               ├── optimizer.py
│               ├── backtest.py
│               ├── ui_schema.py     ← NEW!
│               └── filters/
│                   ├── __init__.py
│                   ├── config.py
│                   ├── manager.py
│                   ├── supertrend.py
│                   ├── rsi.py
│                   ├── adx.py
│                   └── volume.py
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── main.jsx
│       ├── index.css
│       ├── api.js
│       ├── pages/
│       │   ├── Indicator.jsx
│       │   ├── Data.jsx
│       │   ├── Signals.jsx
│       │   ├── Calendar.jsx
│       │   └── Settings.jsx
│       └── components/
│           └── Indicator/
│               ├── index.js
│               ├── LogsPanel.jsx
│               ├── SettingsSidebar.jsx
│               ├── StatsPanel.jsx
│               ├── MonthlyPanel.jsx
│               ├── TradesTable.jsx
│               ├── HeatmapPanel.jsx
│               └── AutoOptimizePanel.jsx
├── install.bat
├── start.bat
├── stop.bat
└── reinstall.bat
```

---

## 💬 ЧАТЫ РАЗРАБОТКИ

### Названия для копирования:

```
Komas #00 — Планирование
Komas #01 — Core: Logger и Config
Komas #02 — Core: Database
Komas #03 — Data: Manager и Binance
Komas #04 — Data: WebSocket Live
Komas #05 — Indicators: Base Classes
Komas #06 — Indicators: PluginLoader
Komas #07 — TRG: Indicator Core
Komas #08 — TRG: Trading System
Komas #09 — TRG: Filters
Komas #10 — TRG: Optimizer
Komas #11 — TRG: Backtest
Komas #12 — TRG: UI Schema
Komas #13 — API: Indicator Routes
Komas #14 — API: Signals Routes
Komas #15 — Frontend: Indicator Page
Komas #16 — Frontend: Components
Komas #17 — Notifications: Telegram
Komas #18 — Notifications: Discord
Komas #19 — Bots: System
Komas #20 — Calendar: Integration
Komas #21 — Deploy: Scripts
Komas #22 — Docs: Final
```

### Статусы:
| Чат | Статус | Артефакт |
|-----|--------|----------|
| #00 | ✅ | Master Plan v1.0 |
| #01 | ✅ | komas_core_v1.zip |
| #02 | ✅ | database.py |
| #03 | ✅ | komas_data_v1.zip |
| #04 | ✅ | komas_ws_v1.zip |
| #05 | ✅ | komas_indicators_v1.zip |
| #06 | ✅ | komas_plugins_v1.zip |
| #07 | ✅ | komas_trg_v1.zip |
| #08 | ✅ | komas_trg_trading_v1.zip |
| #09 | ✅ | komas_trg_filters_v1.zip |
| #10 | ✅ | komas_trg_optimizer_v1.zip |
| #11 | ✅ | komas_trg_backtest_v1.zip |
| #12 | ✅ | komas_trg_ui_schema_v1.zip |
| #13-#22 | 🔴 | — |

---

## ⚠️ ПРАВИЛА РАЗРАБОТКИ

### 🚫 ЗАПРЕЩЕНО:
1. Урезать функционал без явного разрешения пользователя
2. Удалять компоненты, страницы, функции
3. Убирать настройки из интерфейса
4. Выгружать код в чат текстом (только архивы!)
5. Создавать заглушки (stubs) — всегда полная реализация

### ✅ ОБЯЗАТЕЛЬНО:
1. Выгрузка кода ТОЛЬКО в ZIP архивах
2. Сохранять ВСЕ существующие функции при изменениях
3. Создавать .bat для pip/npm install, тестов, консольных команд
4. Самостоятельно добавлять интеграции в main.py, requirements.txt
5. Исправлять ошибки немедленно
6. КОДИРОВКА: encoding='utf-8' при open() на Windows

---

## 🔌 API КОНТРАКТЫ

### Data API (`/api/data/`)
```
GET  /symbols              - Список пар
GET  /timeframes           - Таймфреймы
POST /download             - Загрузка данных
GET  /download/progress    - Прогресс
GET  /available            - Загруженные файлы
POST /sync                 - Синхронизация
```

### WebSocket API (`/api/ws/`)
```
GET  /status               - Статус подключения
POST /connect              - Подключиться
POST /subscribe            - Подписаться на стрим
GET  /prices               - Кэшированные цены
GET  /sse/prices           - SSE стрим цен
GET  /sse/klines           - SSE стрим свечей
```

### Database API (`/api/db/`)
```
GET  /info                 - Информация о БД
GET  /settings             - Список настроек
POST /settings             - Создать настройку
GET  /presets              - Список пресетов
POST /presets              - Создать пресет
```

### Plugins API (`/api/plugins/`)
```
GET  /                     - Список плагинов
GET  /{id}                 - Информация о плагине
GET  /{id}/parameters      - Параметры
GET  /{id}/ui-schema       - UI схема
POST /reload               - Перезагрузить плагины
```

---

## 📈 ПРОГРЕСС

```
Общий прогресс: ██████████████░░░░░░ 68%

Этап 1 - Core:        ██████████ 100% ✅ [#01 ✅, #02 ✅]
Этап 2 - Data:        ██████████ 100% ✅ [#03 ✅, #04 ✅]
Этап 3 - Indicators:  ██████████ 100% ✅ [#05 ✅, #06 ✅]
Этап 4 - TRG Plugin:  ██████████ 100% ✅ [#07-#12 ✅] 🎉
Этап 5 - API:         ████░░░░░░  40%    (частично)
Этап 6 - Frontend:    ██░░░░░░░░  20%    (старый код)
Этапы 7-11:           ░░░░░░░░░░   0%    (TODO)
```

---

## 📝 ДЕТАЛЬНАЯ ИСТОРИЯ ДЕЙСТВИЙ

### Чат #12 — TRG: UI Schema (2025-12-25) ✅ **NEW!**

**Что сделали:**
- `plugins/trg/ui_schema.py` — TRGUISchema (~900 строк)
- `test_ui_schema.py` — 35+ тестов
- manifest.json обновлён до v1.5.0

**Функционал:**
- FieldType, SectionType, TabType enums
- UIField, UISection, UITab dataclasses
- 9 sidebar секций:
  - data (2 fields)
  - indicator (2 fields)
  - take_profit (21 fields - 10 TP levels)
  - stop_loss (4 fields)
  - leverage (3 fields)
  - filters (13 fields)
  - reentry (4 fields)
  - adaptive (3 fields)
  - capital (3 fields)
- 6 tabs: chart, stats, trades, monthly, optimizer, heatmap
- 55 default values
- Field validation system
- depends_on/depends_value для условных полей
- get_filter_presets() — 5 пресетов фильтров
- get_tp_presets() — 5 пресетов TP
- get_optimization_ranges() — ranges для оптимизации
- JSON export (35KB)
- Singleton pattern

**Тесты (10/10 ✅):**
- Schema creation
- Defaults (55 fields)
- Validation (valid/invalid)
- Section/Field getters
- JSON export
- Presets
- Optimization ranges

---

### Чат #11 — TRG: Backtest (2025-12-25) ✅

**Что сделали:**
- `plugins/trg/backtest.py` — TRGBacktest (~1000 строк)
- `test_backtest.py` — 23 теста (~600 строк)
- manifest.json обновлён до v1.4.0

**Функционал:**
- BacktestConfig — конфигурация бэктеста
- BacktestResult — полный результат с метриками
- Интеграция TRGIndicator + TRGSignalGenerator + TRGTradingSystem
- Monthly stats tracking
- Equity curve генерация
- TP accuracy статистика
- Parallel backtest для оптимизации
- Score calculation (profit, winrate, sharpe, profit_factor, advanced)
- UI helpers: prepare_candles, prepare_indicators, prepare_trade_markers

**Тесты (23/23 ✅)**

---

### Чат #10 — TRG: Optimizer (2025-12-25) ✅

**Что сделали:**
- `plugins/trg/optimizer.py` — TRGOptimizer (~600 строк)
- `test_optimizer.py` — 14 тестов (~500 строк)
- Многоядерная оптимизация через ProcessPoolExecutor
- 5 режимов: indicator, tp, sl, filters, full
- SSE streaming прогресса в реальном времени
- Heatmap генерация (i1/i2 матрица)
- Интеграция с filters/manager.py (45 конфигов)
- Экспорт результатов в DataFrame

**Тесты (14/14 ✅)**

---

### Чат #09 — TRG: Filters (2025-12-25) ✅

**Что сделали:**
- `plugins/trg/filters/` — модуль фильтров (~1200 строк)
- 4 фильтра: SuperTrend, RSI, ADX, Volume
- TRGFilterConfig + 11 пресетов
- TRGFilterManager + 45 конфигов для оптимизации
- `test_filters.py` — 11 тестов

---

### Чат #08 — TRG: Trading System (2025-12-25) ✅

**Что сделали:**
- `plugins/trg/trading.py` (~580 строк)
- `test_trading.py` — 28 тестов (~400 строк)
- 10 TP levels с partial closes
- 3 SL modes: fixed, breakeven, cascade trailing
- Re-entry после SL/TP
- Leverage до 125x + commission tracking

---

### Чат #07 — TRG: Indicator Core (2025-12-25) ✅

**Что сделали:**
- `plugins/trg/indicator.py` — TRGIndicator (~420 строк)
- `plugins/trg/signals.py` — TRGSignalGenerator (~380 строк)
- `plugins/trg/__init__.py` — backward compatibility

---

### Чаты #00-#06 — Core, Data, Indicators Base ✅

Описаны в предыдущих версиях документа.

---

## 🔄 ИСТОРИЯ ИЗМЕНЕНИЙ ДОКУМЕНТА

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0 | 2025-12-25 | Первая версия |
| 1.1-1.9 | 2025-12-25 | Чаты #01-#06 |
| 2.0-2.1 | 2025-12-25 | Чаты #07-#09 |
| 2.2 | 2025-12-25 | Обновлена структура |
| 2.3 | 2025-12-25 | Чат #10 завершён |
| 2.4 | 2025-12-25 | Чат #11 завершён |
| 2.5 | 2025-12-25 | **Чат #12 завершён**, прогресс 68%, TRG 100% 🎉 |

---

## 📊 СВОДКА ПО ТЕСТАМ TRG PLUGIN

| Модуль | Тесты | Статус |
|--------|-------|--------|
| Indicator Core | 4/4 | ✅ |
| Trading System | 28/28 | ✅ |
| Filters | 11/11 | ✅ |
| Optimizer | 14/14 | ✅ |
| Backtest | 23/23 | ✅ |
| UI Schema | 10/10 | ✅ |
| **ВСЕГО** | **90/90** | **✅** |

---

## 🎯 СЛЕДУЮЩИЙ ЧАТ

**Komas #13 — API: Indicator Routes**

Задачи:
- `api/indicator.py` — новые API endpoints для TRG
- Интеграция с ui_schema для динамической генерации форм
- SSE streaming для оптимизации
- Эндпоинты для бэктеста

---

*Документ хранится в Project Knowledge и обновляется после каждого завершённого чата*
