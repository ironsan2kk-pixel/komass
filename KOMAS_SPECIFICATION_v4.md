# KOMAS Trading System — Полная спецификация v4.0

> **Дата создания:** 27.12.2024  
> **Автор:** Alex + Claude  
> **Статус:** Планирование  
> **GitHub:** https://github.com/ironsan2kk-pixel/komass

---

## 1. Обзор проекта

### 1.1 Цель
Комплексная система для автоматизированной торговли криптовалютами на фьючерсах Binance с отправкой сигналов в Telegram для копирования через Cornix.

### 1.2 Ключевые особенности
- **Мульти-индикаторная архитектура** — плагинная система для N индикаторов
- **200+ системных пресетов** — автогенерация + пользовательские
- **Оптимизация на 3 уровнях** — индикатор → пресеты → бот
- **Live режим 24/7** — фоновая подкачка данных + мониторинг сигналов
- **Telegram интеграция** — 2 бота × N каналов с маршрутизацией
- **Валидация** — Walk-forward, Monte Carlo, Stress test

### 1.3 Бренд
**KOMAS** (Комас)

---

## 2. Технический стек

### 2.1 Backend
| Компонент | Технология |
|-----------|------------|
| Язык | Python 3.11+ |
| Framework | FastAPI |
| Database | SQLite |
| Scheduler | APScheduler |
| Параллелизация | ProcessPoolExecutor |
| WebSocket | websockets / aiohttp |

### 2.2 Frontend
| Компонент | Технология |
|-----------|------------|
| Framework | React 18 |
| Build | Vite |
| CSS | TailwindCSS |
| Charts | lightweight-charts |
| State | React Context / Zustand |

### 2.3 Деплой
- **OS:** Windows Server (без Docker)
- **Управление:** Batch файлы (.bat)
- **Кодировка:** UTF-8 везде

---

## 3. Источники данных

### 3.1 Binance Futures API
- **Тип:** USDT-M Perpetual Futures ТОЛЬКО
- **Spot:** НЕ поддерживается (убрать из системы)

### 3.2 Поддерживаемые таймфреймы
```
Binance API:  1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M

Для KOMAS:    1m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d

ПРИМЕЧАНИЕ: 45m и 5h НЕ поддерживаются Binance напрямую.
Опционально можно синтезировать из младших ТФ.
```

### 3.3 Пары
- Динамический список с Binance Futures API
- Пользователь выбирает из доступных
- Формат: BTCUSDT, ETHUSDT, etc.

---

## 4. Архитектура индикаторов (плагины)

### 4.1 Базовый класс
```python
class BaseIndicator:
    name: str
    version: str
    
    def get_ui_schema(self) -> dict
    def get_system_presets(self) -> List[Preset]
    def calculate(self, df, settings) -> dict
    def backtest(self, df, settings) -> dict
    def check_signal(self, df, settings) -> Optional[Signal]
```

### 4.2 Текущие индикаторы
| # | Название | Статус |
|---|----------|--------|
| 1 | TRG (Trend Range Grid) | ✅ Готов |
| 2 | Индикатор 2 (Pine Script) | 🔜 Будет добавлен |
| 3 | Индикатор 3 (Pine Script) | 🔜 Будет добавлен |

### 4.3 TRG параметры
```
Indicator:
├── i1 (ATR Length): 10-200
├── i2 (Multiplier): 1-10

Take Profits (1-10 уровней):
├── percent: 0.5% - 50%
└── amount: 1% - 100%

Stop Loss:
├── percent: 1% - 50%
└── mode: fixed / breakeven / cascade

Filters:
├── SuperTrend (period, multiplier)
├── RSI (period, overbought, oversold)
├── ADX (period, threshold)
└── Volume (multiplier)
```

---

## 5. Система пресетов

### 5.1 Структура
```
ПРЕСЕТЫ
├── 📁 Системные (200)
│   ├── Генерация: 8 × 5 × 5 = 200
│   ├── i1: [14, 25, 40, 60, 80, 110, 150, 200]
│   ├── i2: [2.0, 3.0, 4.0, 5.5, 7.5]
│   └── Фильтры: [N, T, M, S, F]
│
├── ⭐ Топ-10 (результат оптимизации)
│
└── 💾 Пользовательские
    ├── Создание через UI
    ├── Импорт JSON
    └── Клонирование системных
```

### 5.2 Профили фильтров
| Код | Название | Фильтры |
|-----|----------|---------|
| N | None | — |
| T | Trend | SuperTrend |
| M | Momentum | SuperTrend + RSI |
| S | Strength | SuperTrend + ADX |
| F | Full | SuperTrend + RSI + ADX + Volume |

### 5.3 Naming Convention
```
{FILTER}_{i1}_{i2*10}

Примеры:
├── N_14_20  = None, i1=14, i2=2.0
├── T_40_40  = Trend, i1=40, i2=4.0
├── M_60_55  = Momentum, i1=60, i2=5.5
└── F_200_75 = Full, i1=200, i2=7.5
```

### 5.4 Автогенерация TP/SL
```python
# TP count по i1
if i1 <= 25: tp_count = 4
elif i1 <= 80: tp_count = 5
else: tp_count = 6

# Масштабирование по i2
tp_percent = base_tp * (i2 / 4.0)
sl_percent = base_sl * (i2 / 4.0)

# SL mode по i1
if i1 <= 25: sl_mode = "fixed"
elif i1 <= 110: sl_mode = "breakeven"
else: sl_mode = "cascade"
```

---

## 6. Три уровня оптимизации

### 6.1 Уровень 1: Индикатор
- **Что:** i1, i2, TP, SL, фильтры
- **Для:** одной пары
- **Результат:** оптимальные параметры
- **Статус:** ✅ Готов

### 6.2 Уровень 2: Пресеты
- **Что:** поиск универсального пресета для N пар
- **Режимы:** Quick / Standard / Smart / Full
- **Результат:** топ-10 универсальных пресетов
- **Статус:** 🔜 Планируется

### 6.3 Уровень 3: Бот
- **Что:** комбинация настроек для минимизации DD
- **Цель:** минимум просадки БЕЗ изменения РМ
- **Результат:** готовая конфигурация бота
- **Статус:** 🔜 Планируется

---

## 7. Фильтры бота (модульные)

### 7.1 Временные фильтры
```
├── Торговые сессии (Asia/Europe/US/All)
├── Дни недели (Пн-Пт / включая выходные)
├── Cooldown после убытка (0-60 мин)
└── Cooldown между сделками (глобальный)
```

### 7.2 Фильтры волатильности
```
├── ATR фильтр (мин/макс границы)
├── Volume фильтр (мин объём для входа)
└── Extreme volatility pause (ATR > X × average)
```

### 7.3 Трендовые фильтры
```
├── BTC Trend Filter (не против BTC)
├── Multi-TF confirmation (сигнал на младшем + старшем)
└── Market regime detection (trending/ranging)
```

### 7.4 Портфельные фильтры
```
├── Correlation filter (не открывать похожие)
├── Max positions per direction (Long/Short лимит)
└── Sector exposure limit (макс N токенов одного сектора)
```

### 7.5 Защитные фильтры (Equity-based)
```
├── Equity curve stop (пауза если equity < MA20)
├── Daily DD limit (стоп на день)
├── Losing streak pause (после N убытков подряд)
└── Recovery mode (уменьшить размер после DD)
```

---

## 8. Риск-менеджмент бота

### 8.1 Параметры (задаёт пользователь)
| Параметр | Описание | Диапазон |
|----------|----------|----------|
| Депозит | Стартовый капитал | $100 - $1M |
| Риск на сделку | % от депозита | 0.5% - 5% |
| Макс позиций | Одновременно открытых | 1 - 10 |
| Leverage | Плечо | 1x - 125x |
| Дневной лимит DD | Стоп торговли на день | 3% - 10% |
| Общий лимит DD | Стоп бота | 10% - 30% |

### 8.2 Расчёт размера позиции
```
Пример:
├── Депозит: $10,000
├── Риск: 1% = $100
├── SL пресета: 2.5%
├── Leverage: 10x
└── Размер позиции = ($100 / 2.5%) × 10 = $40,000
```

---

## 9. Live Engine

### 9.1 Data Fetcher (APScheduler)
```
├── Каждые 1 мин: обновление 1m свечей
├── Каждые 5 мин: обновление 5m, 15m
├── Каждый час: обновление 1h, 4h
└── Каждый день: обновление 1d
```

### 9.2 Signal Engine
```
├── После обновления данных → проверка сигналов
├── Новый сигнал → запись в БД + Telegram
├── TP/SL hit → уведомление в Telegram
└── Position tracking (виртуальные позиции)
```

### 9.3 WebSocket (опционально)
```
├── Real-time цены для активных позиций
├── Мгновенные уведомления о TP/SL
└── Live обновление dashboard
```

---

## 10. Telegram интеграция

### 10.1 Структура
```
🤖 БОТЫ (2 штуки)
├── Bot 1: token_1 (основной)
└── Bot 2: token_2 (резервный/VIP)

📢 КАНАЛЫ (N штук, настраиваются в UI)
├── Channel A: chat_id_1
├── Channel B: chat_id_2
└── ... (неограниченно)

🔗 МАРШРУТИЗАЦИЯ
├── Bot → Channels (многие-ко-многим)
├── Фильтры на канал (пары, направление, score)
└── Задержка отправки (0/5/15 мин)
```

### 10.2 Формат сообщения (Cornix)
```
🟢 LONG BTC/USDT

Entry: 97500
Targets: 
├── TP1: 98500 (50%)
├── TP2: 99500 (30%)
├── TP3: 101000 (15%)
└── TP4: 103000 (5%)

SL: 95000
Leverage: 10x
Risk: 1%

#BTC #LONG #KOMAS
```

### 10.3 Настройка в UI
```
┌─────────────────────────────────────────────────────────┐
│  📲 TELEGRAM SETTINGS                                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  🤖 BOT 1                                               │
│  Token: [********************************]               │
│  Status: 🟢 Connected                                   │
│                                                          │
│  📢 CHANNELS                                            │
│  ┌──────────────────────────────────────────────────┐   │
│  │ # │ Chat ID      │ Name     │ Filters │ Actions │   │
│  ├───┼──────────────┼──────────┼─────────┼─────────┤   │
│  │ 1 │ -1001234567  │ Main     │ ALL     │ ✏️ 🗑️   │   │
│  │ 2 │ -1009876543  │ BTC Only │ BTC     │ ✏️ 🗑️   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  [+ Добавить канал]                                     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 11. Валидация стратегий

### 11.1 Walk-Forward Test
```
├── Split: 70% train / 30% test
├── Оптимизация на train
├── Проверка на test (out-of-sample)
└── Метрика: OOS Sharpe / OOS PnL
```

### 11.2 Monte Carlo Simulation
```
├── 1000 симуляций
├── Случайная перестановка сделок
├── Распределение результатов
└── Confidence intervals (95%)
```

### 11.3 Stress Test
```
├── COVID crash (март 2020)
├── FTX collapse (ноябрь 2022)
├── Altcoin massacre periods
└── Максимальная просадка в каждом
```

---

## 12. Структура проекта (финальная)

```
komas_v4/
├── backend/
│   └── app/
│       ├── main.py
│       ├── core/
│       │   ├── config.py
│       │   ├── database.py
│       │   └── scheduler.py
│       │
│       ├── api/
│       │   ├── data_routes.py
│       │   ├── indicator_routes.py
│       │   ├── presets_routes.py
│       │   ├── bots_routes.py
│       │   ├── signals_routes.py
│       │   ├── optimizer_routes.py
│       │   └── telegram_routes.py
│       │
│       ├── indicators/
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── trg/
│       │   │   ├── __init__.py
│       │   │   ├── calculator.py
│       │   │   ├── backtest.py
│       │   │   └── presets.py
│       │   ├── indicator_2/
│       │   └── indicator_3/
│       │
│       ├── presets/
│       │   ├── base.py
│       │   ├── registry.py
│       │   ├── sources/
│       │   │   ├── system_trg.py
│       │   │   ├── user_presets.py
│       │   │   └── imported.py
│       │   └── generators/
│       │       └── trg_generator.py
│       │
│       ├── bots/
│       │   ├── config.py
│       │   ├── risk_manager.py
│       │   ├── position_tracker.py
│       │   └── optimizer.py
│       │
│       ├── filters/
│       │   ├── base.py
│       │   ├── time_filters.py
│       │   ├── volatility_filters.py
│       │   ├── trend_filters.py
│       │   ├── portfolio_filters.py
│       │   └── protection_filters.py
│       │
│       ├── live/
│       │   ├── data_fetcher.py
│       │   ├── signal_engine.py
│       │   └── websocket_manager.py
│       │
│       ├── telegram/
│       │   ├── bot_manager.py
│       │   ├── channel_manager.py
│       │   └── formatters/
│       │       ├── cornix.py
│       │       └── standard.py
│       │
│       └── validation/
│           ├── walk_forward.py
│           ├── monte_carlo.py
│           └── stress_test.py
│
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── styles/
│       │   └── komas-theme.css
│       │
│       ├── pages/
│       │   ├── Dashboard.jsx
│       │   ├── Indicators/
│       │   │   ├── TRG.jsx
│       │   │   └── ...
│       │   ├── Presets.jsx
│       │   ├── Optimizer.jsx
│       │   ├── Bots.jsx
│       │   ├── Signals.jsx
│       │   ├── Telegram.jsx
│       │   ├── Data.jsx
│       │   └── Settings.jsx
│       │
│       └── components/
│           ├── common/
│           ├── charts/
│           ├── presets/
│           ├── optimizer/
│           ├── bots/
│           └── telegram/
│
├── install.bat
├── start.bat
├── stop.bat
└── reinstall.bat
```

---

## 13. План разработки по чатам

### Фаза 1: Исправления и базовые улучшения
| Чат | Модуль | Описание | Оценка |
|-----|--------|----------|--------|
| #15 | Bugfixes | Monthly белый экран, Stats баги | 1 сессия |
| #16 | Data v2 | Только фьючерсы, убрать спот, период | 1 сессия |
| #17 | Data Cache | Кэширование данных для оптимизации | 1 сессия |

### Фаза 2: Система пресетов
| Чат | Модуль | Описание | Оценка |
|-----|--------|----------|--------|
| #18 | Presets Core | Архитектура, базовый класс, registry | 1 сессия |
| #19 | Presets Generator | Генерация 200 системных TRG | 1 сессия |
| #20 | Presets User | Пользовательские пресеты + UI | 1 сессия |
| #21 | Presets Storage | SQLite хранение + импорт/экспорт | 1 сессия |

### Фаза 3: Оптимизация пресетов
| Чат | Модуль | Описание | Оценка |
|-----|--------|----------|--------|
| #22 | Optimizer Core | Multi-pair бэктест, матрица | 1 сессия |
| #23 | Optimizer Modes | Quick/Standard/Smart/Full режимы | 1 сессия |
| #24 | Optimizer UI | Интерфейс оптимизации пресетов | 1 сессия |
| #25 | Optimizer Results | Результаты, heatmap, сравнение | 1 сессия |

### Фаза 4: Конфигурация бота
| Чат | Модуль | Описание | Оценка |
|-----|--------|----------|--------|
| #26 | Bot Config | Структура бота, РМ параметры | 1 сессия |
| #27 | Bot Filters 1 | Временные + волатильность фильтры | 1 сессия |
| #28 | Bot Filters 2 | Трендовые + портфельные фильтры | 1 сессия |
| #29 | Bot Filters 3 | Защитные фильтры (equity-based) | 1 сессия |
| #30 | Bot UI | Интерфейс настройки бота | 1 сессия |

### Фаза 5: Оптимизация бота
| Чат | Модуль | Описание | Оценка |
|-----|--------|----------|--------|
| #31 | Bot Optimizer Core | Алгоритм оптимизации бота | 2 сессии |
| #32 | Validation | Walk-forward, Monte Carlo | 1 сессия |
| #33 | Stress Test | Тест на исторических кризисах | 1 сессия |

### Фаза 6: Live Engine
| Чат | Модуль | Описание | Оценка |
|-----|--------|----------|--------|
| #34 | Data Fetcher | APScheduler + фоновая подкачка | 1 сессия |
| #35 | Signal Engine | Мониторинг + генерация сигналов | 2 сессии |
| #36 | Position Tracker | Отслеживание виртуальных позиций | 1 сессия |
| #37 | Live Dashboard | Real-time статистика | 1 сессия |

### Фаза 7: Telegram интеграция
| Чат | Модуль | Описание | Оценка |
|-----|--------|----------|--------|
| #38 | TG Bot Core | python-telegram-bot, 2 бота | 1 сессия |
| #39 | TG Channels | Управление N каналами | 1 сессия |
| #40 | TG Formatters | Cornix формат + стандартный | 1 сессия |
| #41 | TG Routing | Маршрутизация + фильтры | 1 сессия |
| #42 | TG UI | Интерфейс настройки TG | 1 сессия |

### Фаза 8: Дизайн и полировка
| Чат | Модуль | Описание | Оценка |
|-----|--------|----------|--------|
| #43 | Design System | Новая тема, компоненты | 1 сессия |
| #44 | Dashboard | Главная страница с обзором | 1 сессия |
| #45 | Polish | Финальная полировка UI | 1 сессия |

### Фаза 9: Дополнительные индикаторы
| Чат | Модуль | Описание | Оценка |
|-----|--------|----------|--------|
| #46 | Indicator 2 | Портирование с Pine Script | 2 сессии |
| #47 | Indicator 3 | Портирование с Pine Script | 2 сессии |

---

## 14. Итого

- **Общее количество чатов:** ~35-40
- **Примерное время:** 2-3 месяца при активной разработке
- **Версия после завершения:** v5.0

---

## 15. Что НЕ делаем

- ❌ Автоподгон параметров под каждую пару (overfitting)
- ❌ Распределение капитала между парами (веса)
- ❌ Сложные условные переключения пресетов
- ❌ Spot торговля (только Futures)
- ❌ Экономический календарь (не нужен)
- ❌ Docker (Windows Server напрямую)

---

## 16. Референсы

- **GitHub:** https://github.com/ironsan2kk-pixel/komass
- **Концепция пресетов:** PRESETS_BOT_CONCEPT_v4.md
- **Master Plan v3:** KOMAS_MASTER_PLAN_v3_0.md
- **Предыдущие чаты:** #01-#14 (завершены)
