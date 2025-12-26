# KOMAS TRADING SYSTEM — MASTER PLAN
> Версия: 2.2 | Дата: 2025-12-25 | Статус: В разработке

---

## 📋 ОГЛАВЛЕНИЕ

1. [Цель проекта](#-цель-проекта)
2. [Архитектура](#-архитектура)
3. [Модули и статусы](#-модули-и-статусы)
4. [Структура файлов](#-структура-файлов)
5. [Чаты разработки](#-чаты-разработки)
6. [Правила разработки](#-правила-разработки)
7. [API Контракты](#-api-контракты)
8. [Прогресс](#-прогресс)
9. [История действий](#-история-действий)

---

## 🎯 ЦЕЛЬ ПРОЕКТА

**Komas Trading System** — комплексная платформа для автоматизированной торговли криптовалютами.

### Ключевые возможности:
1. **Порт индикаторов Pine Script → Python** с сохранением всей логики
2. **Модульная система плагинов** — каждый индикатор полностью изолирован
3. **Полный функционал TradingView** — оптимизация, бэктест, heatmap
4. **Real-time данные** — WebSocket стриминг с Binance
5. **Боты 24/7** — автоматические сигналы в Telegram (Cornix формат)
6. **Гибкая архитектура** — легко добавлять новые индикаторы

### Принципы:
- **Модульность** — каждый компонент независим, файлы < 500 строк
- **Расширяемость** — плагинная система индикаторов
- **Надёжность** — централизованное логирование, обработка ошибок
- **Простота деплоя** — Windows Server, без Docker, батники

---

## 📦 МОДУЛИ И СТАТУСЫ

### Легенда:
- 🔴 TODO — не начато
- 🟡 Частично — есть код, нужно доработать
- 🟢 Готово — завершено и протестировано

### CORE (Ядро) ✅ ЭТАП 1 ЗАВЕРШЁН

| Модуль | Файл | Статус | Чат |
|--------|------|--------|-----|
| Logger | `core/logger.py` | 🟢 | #01 ✅ |
| Config | `core/config.py` | 🟢 | #01 ✅ |
| Database | `core/database.py` | 🟢 | #02 ✅ |

### DATA (Данные) ✅ ЭТАП 2 ЗАВЕРШЁН

| Модуль | Файл | Статус | Чат |
|--------|------|--------|-----|
| Binance API | `core/data/binance.py` | 🟢 | #03 ✅ |
| Storage | `core/data/storage.py` | 🟢 | #03 ✅ |
| Manager | `core/data/manager.py` | 🟢 | #03 ✅ |
| WebSocket | `core/data/websocket.py` | 🟢 | #04 ✅ |
| WS API | `api/ws.py` | 🟢 | #04 ✅ |

### INDICATORS (Система плагинов) ✅ ЭТАП 3 ЗАВЕРШЁН

| Модуль | Файл | Статус | Чат |
|--------|------|--------|-----|
| BaseIndicator | `indicators/base/indicator.py` | 🟢 | #05 ✅ |
| BaseTradingSystem | `indicators/base/trading.py` | 🟢 | #05 ✅ |
| BaseFilter | `indicators/base/filter.py` | 🟢 | #05 ✅ |
| BaseOptimizer | `indicators/base/optimizer.py` | 🟢 | #05 ✅ |
| BaseBacktest | `indicators/base/backtest.py` | 🟢 | #05 ✅ |
| PluginLoader | `indicators/loader.py` | 🟢 | #06 ✅ |
| Registry | `indicators/registry.py` | 🟢 | #06 ✅ |
| Plugins API | `api/plugins.py` | 🟢 | #06 ✅ |

### TRG PLUGIN 🔄 ЭТАП 4 В РАБОТЕ (50%)

| Модуль | Файл | Статус | Чат |
|--------|------|--------|-----|
| manifest.json | `plugins/trg/manifest.json` | 🟢 | #06 ✅ |
| **Indicator Core** | `plugins/trg/indicator.py` | 🟢 | #07 ✅ |
| **Signals** | `plugins/trg/signals.py` | 🟢 | #07 ✅ |
| **Trading System** | `plugins/trg/trading.py` | 🟢 | #08 ✅ |
| Take Profit | (в trading.py) | 🟢 | #08 ✅ |
| Stop Loss | (в trading.py) | 🟢 | #08 ✅ |
| Re-entry | (в trading.py) | 🟢 | #08 ✅ |
| **Filters** | `plugins/trg/filters/` | 🟢 | #09 ✅ |
| Optimizer | `plugins/trg/optimizer.py` | 🔴 | #10 |
| Backtest | `plugins/trg/backtest.py` | 🔴 | #11 |
| UI Schema | `plugins/trg/ui_schema.py` | 🔴 | #12 |

### API (REST)

| Модуль | Файл | Статус | Чат |
|--------|------|--------|-----|
| Data API | `api/data.py` | 🟢 | #03 ✅ |
| WebSocket API | `api/ws.py` | 🟢 | #04 ✅ |
| Database API | `api/database.py` | 🟢 | #02 ✅ |
| Plugins API | `api/plugins.py` | 🟢 | #06 ✅ |
| Indicators API | `api/indicators.py` | 🔴 | #13 |

### FRONTEND / PRESETS / BOTS / TELEGRAM — TODO

---

## 📁 СТРУКТУРА ФАЙЛОВ

```
komas/
├── backend/
│   ├── app/
│   │   ├── main.py                    # FastAPI (v3.7) ✅
│   │   │
│   │   ├── core/                      # ═══ ЯДРО ═══ ✅
│   │   │   ├── config.py              # Pydantic Settings
│   │   │   ├── logger.py              # Логирование
│   │   │   ├── database.py            # SQLite
│   │   │   └── data/                  # Данные ✅
│   │   │       ├── binance.py
│   │   │       ├── storage.py
│   │   │       ├── manager.py
│   │   │       └── websocket.py
│   │   │
│   │   ├── indicators/                # ═══ ИНДИКАТОРЫ ═══ ✅
│   │   │   ├── registry.py            # Реестр (~581 строк)
│   │   │   ├── loader.py              # Загрузчик (~710 строк)
│   │   │   ├── base/                  # Базовые классы ✅
│   │   │   │   ├── indicator.py       # (~380 строк)
│   │   │   │   ├── trading.py         # (~500 строк)
│   │   │   │   ├── filter.py          # (~480 строк)
│   │   │   │   ├── optimizer.py       # (~520 строк)
│   │   │   │   └── backtest.py        # (~450 строк)
│   │   │   │
│   │   │   └── plugins/
│   │   │       └── trg/               # TRG Plugin 🔄 50%
│   │   │           ├── manifest.json  # ✅ v1.2.0
│   │   │           ├── __init__.py    # ✅
│   │   │           ├── indicator.py   # ✅ (~420 строк)
│   │   │           ├── signals.py     # ✅ (~380 строк)
│   │   │           ├── trading.py     # ✅ (~580 строк)
│   │   │           ├── filters/       # ✅ NEW! (~1200 строк)
│   │   │           │   ├── __init__.py
│   │   │           │   ├── config.py
│   │   │           │   ├── manager.py
│   │   │           │   ├── supertrend.py
│   │   │           │   ├── rsi.py
│   │   │           │   ├── adx.py
│   │   │           │   └── volume.py
│   │   │           ├── optimizer.py   # ← #10
│   │   │           ├── backtest.py    # ← #11
│   │   │           └── ui_schema.py   # ← #12
│   │   │
│   │   └── api/                       # ═══ REST API ═══
│   │       ├── data.py                # ✅
│   │       ├── ws.py                  # ✅
│   │       ├── database.py            # ✅
│   │       ├── plugins.py             # ✅
│   │       └── indicator_routes.py    # (legacy)
│   │
│   ├── data/                          # Parquet файлы
│   ├── logs/                          # Логи
│   └── requirements.txt
│
├── frontend/                          # React (legacy)
│
├── install.bat
├── install_trg_deps.bat               # ✅
├── test_trg_filters.bat               # ✅ NEW!
├── start.bat
└── stop.bat
```

---

## 💬 ЧАТЫ РАЗРАБОТКИ

### ЭТАП 1: CORE ✅ ЗАВЕРШЁН
| # | Название | Статус |
|---|----------|--------|
| 01 | `Komas #01 — Core: Logger и Config` | ✅ |
| 02 | `Komas #02 — Core: Database` | ✅ |

### ЭТАП 2: DATA ✅ ЗАВЕРШЁН
| # | Название | Статус |
|---|----------|--------|
| 03 | `Komas #03 — Data: Manager и Binance` | ✅ |
| 04 | `Komas #04 — Data: WebSocket Live` | ✅ |

### ЭТАП 3: INDICATORS ✅ ЗАВЕРШЁН
| # | Название | Статус |
|---|----------|--------|
| 05 | `Komas #05 — Indicators: Базовые классы` | ✅ |
| 06 | `Komas #06 — Indicators: PluginLoader` | ✅ |

### ЭТАП 4: TRG PLUGIN 🔄 В РАБОТЕ
| # | Название | Статус |
|---|----------|--------|
| 07 | `Komas #07 — TRG: Indicator Core` | ✅ |
| 08 | `Komas #08 — TRG: Trading System` | ✅ |
| 09 | `Komas #09 — TRG: Filters` | ✅ **DONE** |
| 10 | `Komas #10 — TRG: Optimizer` | ⏳ **NEXT** |
| 11 | `Komas #11 — TRG: Backtest` | ⏳ |
| 12 | `Komas #12 — TRG: UI Schema` | ⏳ |

### ЭТАП 5+: API, Frontend, Bots, Telegram
| # | Название | Статус |
|---|----------|--------|
| 13 | `Komas #13 — API: Indicators` | ⏳ |
| 14-16 | Frontend | ⏳ |
| 17-18 | Presets | ⏳ |
| 19-21 | Bots | ⏳ |
| 22 | Telegram | ⏳ |

---

## ⚠️ ПРАВИЛА РАЗРАБОТКИ

### 🚫 ЗАПРЕЩЕНО:
1. Урезать функционал без разрешения
2. Удалять компоненты без спроса
3. Выгружать код текстом (только ZIP!)
4. **НИКАКИХ заглушек** — всегда полная реализация

### ✅ ОБЯЗАТЕЛЬНО:
1. Выгрузка кода ТОЛЬКО в ZIP
2. Создавать .bat для pip/npm install
3. Самостоятельно добавлять интеграции в main.py
4. Исправлять ошибки немедленно
5. **КОДИРОВКА:** `encoding='utf-8'` при `open()` на Windows

---

## 📊 ПРОГРЕСС

```
Этап 1 - Core:        ██████████ 100% ✅
Этап 2 - Data:        ██████████ 100% ✅
Этап 3 - Indicators:  ██████████ 100% ✅
Этап 4 - TRG Plugin:  █████░░░░░ 50%  [#07-#09 ✅, #10-#12]
```

### Завершённые чаты (10):

| Чат | Название | Артефакт |
|-----|----------|----------|
| #00 | Планирование | Master Plan |
| #01 | Core: Logger и Config | komas_core_v1.zip |
| #02 | Core: Database | database.py + API |
| #03 | Data: Manager и Binance | komas_data_v1.zip |
| #04 | Data: WebSocket Live | komas_ws_v1.zip |
| #05 | Indicators: Base Classes | komas_indicators_v1.zip |
| #06 | Indicators: PluginLoader | komas_plugins_v1.zip |
| #07 | TRG: Indicator Core | komas_trg_v1.zip |
| #08 | TRG: Trading System | komas_trg_trading_v1.zip |
| #09 | **TRG: Filters** | komas_trg_filters_v1.zip |

---

## 📜 ИСТОРИЯ ДЕЙСТВИЙ

### Чат #09 — TRG: Filters (2025-12-25) ✅

**Что сделали:**

1. ✅ Создали `plugins/trg/filters/` (~1200 строк)
   - `__init__.py` — экспорты
   - `config.py` (~220 строк) — TRGFilterConfig, пресеты
   - `manager.py` (~350 строк) — TRGFilterManager
   - `supertrend.py` (~280 строк) — SuperTrend фильтр
   - `rsi.py` (~260 строк) — RSI фильтр
   - `adx.py` (~290 строк) — ADX фильтр
   - `volume.py` (~250 строк) — Volume фильтр

2. ✅ Создали `test_filters.py` (~500 строк)
   - 11 тестов для всех компонентов

3. ✅ Создали `test_trg_filters.bat`

4. ✅ Создали `FILTERS_README.md`

**Тесты прошли:**
```
✅ SuperTrend Filter: PASSED
✅ RSI Filter: PASSED
✅ ADX Filter: PASSED
✅ Volume Filter: PASSED
✅ TRGFilterConfig: PASSED
✅ Filter Presets: PASSED
✅ TRGFilterManager: PASSED
✅ generate_filter_configs: PASSED
✅ apply_filter_config: PASSED
✅ generate_signals_with_filters: PASSED
✅ Full Integration: PASSED
🎉 ALL 11 TESTS PASSED!
```

**Артефакт:** `komas_trg_filters_v1.zip`

**Функционал фильтров:**
- SuperTrend — фильтрация по направлению тренда
- RSI — блокировка при перекупленности/перепроданности
- ADX — блокировка при слабом тренде (флэт)
- Volume — блокировка при низком объёме
- 11 пресетов (none, supertrend_only, all, conservative, aggressive, etc.)
- 45 конфигураций для оптимизации
- Полная совместимость с legacy API

---

### Чат #08 — TRG: Trading System (2025-12-25) ✅

**Что сделали:**

1. ✅ Создали `plugins/trg/trading.py` (~580 строк)
   - TRGTradingConfig — конфигурация TP/SL/Re-entry
   - TRGPosition — состояние позиции
   - TRGTradingSystem — полная торговая система
   - Partial TP closes (до 10 уровней)
   - Trailing SL (fixed/breakeven/cascade)
   - Re-entry после SL/TP
   - Leverage и commission

2. ✅ Создали `test_trading.py` (~400 строк)
   - 28 тестов для всех компонентов

**Артефакт:** `komas_trg_trading_v1.zip`

---

### Чат #07 — TRG: Indicator Core (2025-12-25) ✅

**Создано:**
- `plugins/trg/indicator.py` (~420 строк) — TRGIndicator
- `plugins/trg/signals.py` (~380 строк) — TRGSignalGenerator

**Артефакт:** `komas_trg_v1.zip`

---

## 🔌 API КОНТРАКТЫ

### Data API ✅

```
GET    /api/data/symbols              # Список пар Binance
GET    /api/data/available            # Загруженные файлы
POST   /api/data/download             # Запуск загрузки
GET    /api/data/download/progress    # Прогресс
POST   /api/data/download/cancel/{id} # Отмена
POST   /api/data/sync                 # Синхронизация
DELETE /api/data/file/{name}          # Удаление
POST   /api/data/continue/{s}/{tf}    # Докачка
```

### WebSocket API ✅

```
GET    /api/ws/status                 # Статус
POST   /api/ws/connect                # Подключиться
POST   /api/ws/subscribe              # Подписаться
GET    /api/ws/prices                 # Кэш цен

# SSE
GET    /api/ws/sse/prices             # Стрим цен
GET    /api/ws/sse/klines             # Стрим свечей
GET    /api/ws/sse/trades             # Стрим сделок
```

### Database API ✅

```
GET    /api/db/info                   # Информация
GET    /api/db/settings               # Настройки
POST   /api/db/settings               # Создать
GET    /api/db/presets                # Пресеты
POST   /api/db/presets                # Создать пресет
```

### Plugins API ✅

```
GET    /api/plugins/list              # Список
GET    /api/plugins/{id}              # Информация
GET    /api/plugins/{id}/schema       # UI схема
POST   /api/plugins/{id}/calculate    # Расчёт
POST   /api/plugins/{id}/backtest     # Бэктест
POST   /api/plugins/{id}/optimize     # Оптимизация (SSE)
POST   /api/plugins/reload            # Перезагрузка
```

---

## 📋 РЕФЕРЕНСЫ

### Что портируем из indicator_routes.py (2000+ строк):
- ✅ calculate_trg → indicator.py
- ✅ generate_signals → signals.py
- ✅ run_backtest → trading.py
- ✅ calculate_supertrend → filters/supertrend.py
- ✅ calculate_rsi → filters/rsi.py
- ✅ calculate_adx → filters/adx.py
- ✅ calculate_volume → filters/volume.py
- ✅ generate_filter_configs → filters/manager.py
- 🔴 auto_optimize → optimizer.py
- 🔴 generate_heatmap → optimizer.py

### Технические решения:
- **База:** SQLite + SQLAlchemy async
- **Данные:** Parquet (сжатие, быстрый доступ)
- **WebSocket:** Auto-reconnect, exponential backoff
- **Плагины:** manifest.json + динамический импорт
- **Кодировка:** UTF-8 везде (Windows!)

---

*Документ обновляется после каждого завершённого чата*
