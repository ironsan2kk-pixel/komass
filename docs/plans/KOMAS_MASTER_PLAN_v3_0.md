# KOMAS MASTER PLAN v3.0

> **Последнее обновление:** 2025-12-26
> **Статус:** В разработке
> **Прогресс:** 91%
> **GitHub:** https://github.com/ironsan2kk-pixel/komass

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
│  ├── core/ (config, logger, database, notifications)   │
│  ├── api/ (routes для всех модулей)                     │
│  ├── indicators/ (base classes, loader, registry)       │
│  └── plugins/ (TRG и другие индикаторы)                 │
├─────────────────────────────────────────────────────────┤
│  Notifications Layer                                     │
│  ├── Telegram Bot (python-telegram-bot)                 │
│  ├── Message Formatters (Simple/Cornix/Custom)          │
│  └── Discord Webhook (planned)                          │
├─────────────────────────────────────────────────────────┤
│  Data Layer                                              │
│  ├── Binance API (REST + WebSocket)                     │
│  ├── Parquet storage                                     │
│  └── SQLite (settings, signals, results)                │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 МОДУЛИ И СТАТУСЫ

### Легенда:
- 🔴 Не начато
- 🟡 В процессе
- 🟢 Готово

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
| Модуль | Статус | Тесты |
|--------|--------|-------|
| Indicator | 🟢 | 4/4 ✅ |
| Signals | 🟢 | ✅ |
| Trading | 🟢 | 28/28 ✅ |
| Filters | 🟢 | 11/11 ✅ |
| Optimizer | 🟢 | 14/14 ✅ |
| Backtest | 🟢 | 23/23 ✅ |
| UI Schema | 🟢 | ✅ |

### Этап 5 — API (100% ✅) 🎉
| Модуль | Статус | Тесты |
|--------|--------|-------|
| Data API | 🟢 | ✅ |
| WebSocket API | 🟢 | ✅ |
| Database API | 🟢 | ✅ |
| Plugins API | 🟢 | ✅ |
| Indicator API | 🟢 | 10/10 ✅ |
| Signals API | 🟢 | 28/28 ✅ |

### Этап 6 — Frontend (100% ✅) 🎉
| Модуль | Статус | Файлы |
|--------|--------|-------|
| App Layout | 🟢 | `App.jsx` |
| Data Page | 🟢 | `pages/Data.jsx` |
| Indicator Page | 🟢 | `pages/Indicator.jsx` |
| Indicator Components | 🟢 | `components/Indicator/*` |
| Signals Page | 🟢 | `pages/Signals.jsx` |
| Settings Page | 🟢 | `pages/Settings.jsx` |
| Calendar Page | 🟢 | `pages/Calendar.jsx` |
| API Client | 🟢 | `api.js` |

### Этап 7 — Notifications (50%) 🎉 NEW!
| Модуль | Статус | Файлы |
|--------|--------|-------|
| Telegram Bot | 🟢 | `core/notifications/telegram.py` |
| Message Formatters | 🟢 | `core/notifications/formatters.py` |
| Notifications API | 🟢 | `api/notifications_routes.py` |
| Settings UI | 🟢 | `pages/Settings.jsx` (Notifications tab) |
| Discord Webhook | 🔴 | Chat #18 |

### Этапы 8-11 (0%)
| Этап | Чаты | Статус |
|------|------|--------|
| Discord Integration | #18 | 🔴 |
| Bots System | #19 | 🔴 |
| Calendar Integration | #20 | 🔴 |
| Deploy Scripts | #21 | 🔴 |
| Documentation | #22 | 🔴 |

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
| #15 | ✅ | komas_frontend_indicator_v1.zip |
| #16 | ✅ | komas_frontend_components_v1.zip |
| #17 | ✅ | **komas_telegram_v1.zip** 🎉 |
| #18-#22 | 🔴 | — |

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
7. При выгрузке ZIP указывать текст для Git commit на английском

---

## 🔌 API КОНТРАКТЫ

### Data API (`/api/data/`)
```
GET  /symbols              - Список пар
GET  /timeframes           - Таймфреймы
POST /download             - Загрузка данных
GET  /available            - Загруженные файлы
```

### Indicator API (`/api/indicator/`)
```
POST /calculate            - Расчёт индикатора + бэктест
GET  /auto-optimize-stream - SSE оптимизация
POST /heatmap              - Генерация heatmap
GET  /ui-schema            - UI схема
GET  /presets              - Пресеты настроек
```

### Signals API (`/api/signals/`)
```
GET  /                     - Список сигналов
POST /                     - Создать сигнал
GET  /active               - Активные сигналы
GET  /stats                - Статистика
POST /export               - Экспорт CSV/JSON
GET  /sse/stream           - SSE уведомления
```

### Notifications API (`/api/notifications/`) 🆕
```
GET  /settings             - Получить настройки
POST /settings             - Обновить настройки
POST /validate-bot         - Проверить токен бота
POST /test                 - Тестовое сообщение
GET  /stats                - Статистика уведомлений
POST /send/signal          - Отправить сигнал
POST /send/tp-hit          - Отправить TP уведомление
POST /send/sl-hit          - Отправить SL уведомление
POST /send/closed          - Отправить закрытие
GET  /formats              - Доступные форматы
GET  /preview/{format}     - Превью формата
POST /enable               - Включить уведомления
POST /disable              - Выключить уведомления
```

---

## 📈 ПРОГРЕСС

```
Общий прогресс: ██████████████████░░ 91%

Этап 1 - Core:        ██████████ 100% ✅ [#01 ✅, #02 ✅]
Этап 2 - Data:        ██████████ 100% ✅ [#03 ✅, #04 ✅]
Этап 3 - Indicators:  ██████████ 100% ✅ [#05 ✅, #06 ✅]
Этап 4 - TRG Plugin:  ██████████ 100% ✅ [#07-#12 ✅] 🎉
Этап 5 - API:         ██████████ 100% ✅ [#13 ✅, #14 ✅] 🎉
Этап 6 - Frontend:    ██████████ 100% ✅ [#15 ✅, #16 ✅] 🎉
Этап 7 - Notifications:█████░░░░░  50% 🟡 [#17 ✅, #18 TODO]
Этапы 8-11:           ░░░░░░░░░░   0%    [#19-#22 TODO]
```

---

## 📝 ДЕТАЛЬНАЯ ИСТОРИЯ ДЕЙСТВИЙ

### Чат #17 — Notifications: Telegram (2025-12-26) ✅ **NEW!**

**Что сделали:**

1. **Core Notifications Module:**
   - `models.py` — Pydantic модели (TelegramSettings, SignalData, TPHitData, etc.)
   - `formatters.py` — Форматтеры сообщений (Simple, Cornix, Custom)
   - `telegram.py` — TelegramNotifier клиент с python-telegram-bot
   - `__init__.py` — Экспорт всех классов

2. **API Routes (`notifications_routes.py`):**
   - 20+ endpoints для управления уведомлениями
   - Settings CRUD
   - Bot validation
   - Test notifications
   - Send signal/TP/SL/closed notifications
   - Message format preview

3. **Frontend (`Settings.jsx`):**
   - 3 вкладки: Presets / Notifications / API Keys
   - Полная настройка Telegram:
     - Bot Token с валидацией
     - Chat ID
     - Message format selection
     - Trigger toggles
     - Display options
   - Preview форматов сообщений
   - Test notification button

4. **API Client (`api.js`):**
   - notificationsApi с всеми endpoints

5. **Tests (`test_notifications.py`):**
   - 25+ тестов покрывающих все модули
   - Models, Formatters, Notifier

**Артефакт:** `komas_telegram_v1.zip`

---

### Чат #16 — Frontend: Components (2025-12-26) ✅

- Signals Page с фильтрами и SSE
- Settings Page с вкладками
- Calendar Page исправления
- API Client обновления

---

### Чаты #00-#15 (2025-12-25/26) ✅

Все завершены — Core, Data, Indicators, TRG Plugin, API, Frontend готовы.

---

## 🔄 ИСТОРИЯ ИЗМЕНЕНИЙ ДОКУМЕНТА

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.0-2.9 | 2025-12-25/26 | Чаты #00-#16 |
| 3.0 | 2025-12-26 | **Чат #17 завершён**, Telegram Notifications ✅, прогресс 91% |

---

## 📊 СВОДКА ПО ЗАВЕРШЁННЫМ ЧАТАМ

| Этап | Чаты | Статус |
|------|------|--------|
| Core | #01, #02 | ✅ 100% |
| Data | #03, #04 | ✅ 100% |
| Indicators | #05, #06 | ✅ 100% |
| TRG Plugin | #07-#12 | ✅ 100% |
| API | #13, #14 | ✅ 100% |
| Frontend | #15, #16 | ✅ 100% |
| Notifications | #17 | ✅ 50% (Telegram done) |
| **ВСЕГО** | **18/22** | **91%** |

---

## 🎉 MILESTONE: TELEGRAM NOTIFICATIONS COMPLETE!

**Этап 7 — Notifications (Telegram) полностью завершён!**

Функционал:
1. ✅ TelegramNotifier client
2. ✅ Message formatters (Simple/Cornix/Custom)
3. ✅ 20+ API endpoints
4. ✅ Settings UI with 3 tabs
5. ✅ Bot commands (/start, /status, /signals, /stop)
6. ✅ 25+ tests

**Следующий этап:** Discord Integration (#18)

---

## 🎯 СЛЕДУЮЩИЙ: Komas #18 — Notifications: Discord

**Что будет создано:**

### Backend:
- `core/notifications/discord.py` — Discord Webhook клиент
- Обновление `notifications_routes.py` с Discord endpoints

### Функционал:
1. **Discord Webhook:**
   - Отправка сигналов через webhook
   - Rich embeds для красивых сообщений
   - Цветовая кодировка (зелёный/красный)
   
2. **Настройки:**
   - Webhook URL
   - Enable/Disable
   - Message format

---

*Документ хранится в Project Knowledge и обновляется после каждого завершённого чата*
