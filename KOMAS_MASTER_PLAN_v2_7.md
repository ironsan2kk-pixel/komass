# KOMAS MASTER PLAN v2.7

> **Последнее обновление:** 2025-12-26
> **Статус:** В разработке
> **Прогресс:** 78%

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
├── ui_schema.py       # TRGUISchema
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
| UI Schema | 🟢 | `plugins/trg/ui_schema.py` | ✅ |

### Этап 5 — API (100% ✅) 🎉
| Модуль | Статус | Файлы | Тесты |
|--------|--------|-------|-------|
| Data API | 🟢 | `api/data.py` | ✅ |
| WebSocket API | 🟢 | `api/ws.py` | ✅ |
| Database API | 🟢 | `api/database.py` | ✅ |
| Plugins API | 🟢 | `api/plugins.py` | ✅ |
| Indicator API | 🟢 | `api/indicator.py` | 10/10 ✅ |
| Signals API | 🟢 | `api/signals.py` | 20/20 ✅ |

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
│       │   ├── plugins.py
│       │   ├── indicator.py
│       │   └── signals.py         ← NEW!
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
│               ├── ui_schema.py
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
| #12 | ✅ | komas_ui_schema_v1.zip |
| #13 | ✅ | komas_indicator_api_v1.zip |
| #14 | ✅ | komas_signals_api_v1.zip |
| #15-#22 | 🔴 | — |

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

### Indicator API (`/api/indicator/`)
```
POST /calculate            - Расчёт индикатора + бэктест
POST /backtest             - Полный бэктест
GET  /auto-optimize-stream - SSE оптимизация
POST /heatmap              - Генерация heatmap
GET  /ui-schema            - UI схема
GET  /presets              - Пресеты настроек
POST /replay               - Replay mode
GET  /stats                - Статистика
POST /export               - Экспорт результатов
GET  /symbols              - Доступные символы
```

### Signals API (`/api/signals/`) ← NEW!
```
GET  /                     - Список сигналов с фильтрацией
GET  /{id}                 - Детали сигнала
POST /                     - Создать сигнал
PUT  /{id}                 - Обновить сигнал
DELETE /{id}               - Удалить сигнал
GET  /active               - Активные сигналы
GET  /history              - История сигналов
POST /batch                - Batch операции
GET  /stats                - Статистика сигналов
POST /export               - Экспорт в CSV/JSON
GET  /sse/stream           - SSE real-time стрим
GET  /symbols              - Символы с сигналами
GET  /timeframes           - Таймфреймы с сигналами
DELETE /all                - Удалить все (с подтверждением)
POST /check-expired        - Проверить истёкшие сигналы
```

---

## 📈 ПРОГРЕСС

```
Общий прогресс: ███████████████░░░░░ 78%

Этап 1 - Core:        ██████████ 100% ✅ [#01 ✅, #02 ✅]
Этап 2 - Data:        ██████████ 100% ✅ [#03 ✅, #04 ✅]
Этап 3 - Indicators:  ██████████ 100% ✅ [#05 ✅, #06 ✅]
Этап 4 - TRG Plugin:  ██████████ 100% ✅ [#07-#12 ✅] 🎉
Этап 5 - API:         ██████████ 100% ✅ [#13 ✅, #14 ✅] 🎉
Этап 6 - Frontend:    ██░░░░░░░░  20%    [#15-#16 TODO]
Этапы 7-11:           ░░░░░░░░░░   0%    [#17-#22 TODO]
```

---

## 📝 ДЕТАЛЬНАЯ ИСТОРИЯ ДЕЙСТВИЙ

### Чат #14 — API: Signals Routes (2025-12-26) ✅ **NEW!**

**Что сделали:**
- `api/signals.py` — полный Signals API (~900 строк)
- 14 эндпоинтов для управления сигналами
- SQLite интеграция с таблицей signals
- SSE real-time уведомления

**Эндпоинты:**
- `GET /` — список сигналов с фильтрацией и пагинацией
- `GET /{id}` — детали сигнала по ID
- `POST /` — создание нового сигнала
- `PUT /{id}` — обновление сигнала
- `DELETE /{id}` — удаление сигнала
- `GET /active` — активные сигналы
- `GET /history` — история сигналов
- `POST /batch` — batch операции (delete, update_status, close)
- `GET /stats` — полная статистика
- `POST /export` — экспорт в CSV/JSON
- `GET /sse/stream` — SSE real-time стрим
- `GET /symbols` — символы с сигналами
- `GET /timeframes` — таймфреймы с сигналами
- `DELETE /all` — удаление всех (с подтверждением)
- `POST /check-expired` — проверка истёкших сигналов

**Функционал:**
- Полный CRUD для сигналов
- Pydantic модели с валидацией
- 10 уровней Take Profit
- Типы: long/short
- Статусы: pending/active/closed/cancelled/expired
- Источники: trg/supertrend/rsi/manual/bot/external
- Причины закрытия: tp1-tp10/sl/manual/expired/reversal
- Фильтрация по символу, таймфрейму, типу, статусу, источнику, датам
- Пагинация с сортировкой
- Статистика по символам, таймфреймам, источникам
- Win rate, profit factor, PnL
- Batch операции
- Экспорт в CSV и JSON
- SSE стриминг уведомлений

**Тесты: 20/20 ✅**
- TestDatabase: 2/2
- TestCRUD: 4/4
- TestQueries: 6/6
- TestStatistics: 4/4
- TestBatchOperations: 2/2
- TestExport: 2/2
- TestValidation: 3/3
- TestEdgeCases: 4/4

**Файлы:**
- `backend/app/api/signals.py` — основной API
- `backend/app/main.py` — обновлён для signals routes
- `tests/test_signals_api.py` — полные тесты
- `backend/requirements.txt` — обновлён
- `install.bat`, `start.bat`, `stop.bat`, `reinstall.bat`, `run_tests.bat`

---

### Чат #13 — API: Indicator Routes (2025-12-25) ✅

**Что сделали:**
- `api/indicator.py` — полный Indicator API (~1800 строк)
- 10 эндпоинтов для работы с TRG Plugin
- Интеграция с TRGIndicator, TRGBacktest, TRGOptimizer

**Эндпоинты:**
- `POST /calculate` — расчёт индикатора + бэктест
- `POST /backtest` — полный бэктест с настройками
- `GET /auto-optimize-stream` — SSE streaming оптимизации
- `POST /heatmap` — генерация тепловой карты i1/i2
- `GET /ui-schema` — схема UI для фронтенда
- `GET /presets` — пресеты настроек
- `POST /replay` — replay mode для анализа
- `GET /stats` — статистика
- `POST /export` — экспорт результатов
- `GET /symbols` — доступные символы

**Функционал:**
- Pydantic модели для request/response
- Fallback функции расчёта (ATR, SuperTrend, RSI, ADX)
- Полный бэктест с TP/SL management
- Parallel processing для оптимизации
- Совместимость с legacy indicator_routes.py

**Тесты: 10/10 ✅**

---

### Чаты #00-#12 (2025-12-25) ✅

Все завершены — Core, Data, Indicators Base, PluginLoader, TRG Plugin (Indicator, Trading, Filters, Optimizer, Backtest, UI Schema) готовы.

---

## 🔄 ИСТОРИЯ ИЗМЕНЕНИЙ ДОКУМЕНТА

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0-2.5 | 2025-12-25 | Чаты #00-#12 |
| 2.6 | 2025-12-26 | Чат #13 завершён |
| 2.7 | 2025-12-26 | **Чат #14 завершён**, API 100%, прогресс 78% |

---

## 📊 СВОДКА ПО ЗАВЕРШЁННЫМ ЧАТАМ

| Этап | Чаты | Статус |
|------|------|--------|
| Core | #01, #02 | ✅ 100% |
| Data | #03, #04 | ✅ 100% |
| Indicators | #05, #06 | ✅ 100% |
| TRG Plugin | #07-#12 | ✅ 100% |
| API | #13, #14 | ✅ 100% |
| **ВСЕГО** | **15/22** | **78%** |

---

## 🎯 СЛЕДУЮЩИЙ: Komas #15 — Frontend: Indicator Page

**Что будет создано:**
- Обновление `pages/Indicator.jsx`
- Интеграция с новым Indicator API
- 6 вкладок: График, Статистика, Сделки, Месяцы, Оптимизация, Heatmap
- Компоненты в `/components/Indicator/`

---

*Документ хранится в Project Knowledge и обновляется после каждого завершённого чата*
