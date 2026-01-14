# KOMAS v4.0 — Полный Master Plan

> **Версия:** 4.2 FINAL  
> **Дата:** 27.12.2025  
> **GitHub:** https://github.com/ironsan2kk-pixel/komass  
> **Всего чатов:** 98 (включая 15 QA Checkpoints)

---

## 📋 СОДЕРЖАНИЕ

1. [Обзор проекта](#1-обзор-проекта)
2. [Архитектура системы](#2-архитектура-системы)
3. [Индикаторы](#3-индикаторы)
4. [Система пресетов](#4-система-пресетов)
5. [Signal Score](#5-signal-score)
6. [Модульные фильтры](#6-модульные-фильтры)
7. [Bot Configuration](#7-bot-configuration)
8. [Live Trading Engine](#8-live-trading-engine)
9. [Telegram Integration](#9-telegram-integration)
10. [API Endpoints](#10-api-endpoints)
11. [Database Schema](#11-database-schema)
12. [Frontend Structure](#12-frontend-structure)
13. [Полный план чатов](#13-полный-план-чатов)
14. [Правила разработки](#14-правила-разработки)

---

## 1. ОБЗОР ПРОЕКТА

### Что такое KOMAS?

**KOMAS (Komas Algorithmic Trading System)** — комплексная система для автоматизированной торговли криптовалютами на Binance Futures.

### Эволюция версий

| Версия | Описание |
|--------|----------|
| v1.0-v2.0 | Pine Script на TradingView |
| v3.0 | Python порт, веб-интерфейс |
| v3.5 | Стабильная версия (текущая) |
| **v4.0** | Multi-indicator, presets, bots, live trading |
| v5.0 | Production live trading |

### Стек технологий

| Компонент | Технологии |
|-----------|------------|
| **Backend** | Python 3.11+, FastAPI, SQLite, APScheduler |
| **Frontend** | React 18, Vite, TailwindCSS, lightweight-charts |
| **Деплой** | Windows Server (БЕЗ Docker), батники |
| **Оптимизация** | ProcessPoolExecutor (многоядерность) |
| **Биржа** | **Binance Futures ONLY** |
| **Notifications** | Telegram (2 бота, Cornix format) |

### Ключевые принципы v4.0

1. **Universal Presets** — не pair-specific overfitting
2. **Signal-based Trading** — unified deposit, risk per trade
3. **Modular Filters** — plugin architecture
4. **QA Checkpoints** — каждые 4 чата проверка

---

## 2. АРХИТЕКТУРА СИСТЕМЫ

### Высокоуровневая схема

```
┌─────────────────────────────────────────────────────────────┐
│                        KOMAS v4.0                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │    TRG      │  │  Dominant   │  │   Preset Library    │ │
│  │  Indicator  │  │  Indicator  │  │  200 TRG + 125 Dom  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
│         │                │                     │            │
│         └────────┬───────┴─────────────────────┘            │
│                  ▼                                          │
│         ┌────────────────┐                                  │
│         │  Signal Score  │  ← 0-100 points, A-F grades     │
│         │  (4 × 25 pts)  │                                  │
│         └───────┬────────┘                                  │
│                 ▼                                           │
│         ┌────────────────┐                                  │
│         │ Filter Chain   │  ← 5 categories                 │
│         │ Time/Vol/Trend │                                  │
│         └───────┬────────┘                                  │
│                 ▼                                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                  Bot Configuration                    │  │
│  │  • Risk Management (deposit, risk%, max positions)   │  │
│  │  • Multi-pair portfolio                              │  │
│  │  • Filter profiles                                   │  │
│  └──────────────────────────────────────────────────────┘  │
│                 │                                           │
│     ┌───────────┴───────────┐                              │
│     ▼                       ▼                              │
│ ┌─────────┐           ┌──────────┐                         │
│ │Backtest │           │  Live    │                         │
│ │ Engine  │           │ Trading  │                         │
│ └────┬────┘           └────┬─────┘                         │
│      │                     │                               │
│      └──────────┬──────────┘                               │
│                 ▼                                          │
│         ┌──────────────┐                                   │
│         │   Telegram   │  ← 2 bots, N channels            │
│         │  Cornix fmt  │                                   │
│         └──────────────┘                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Структура проекта

```
komass/
├── docs/                           # Документация (GitHub)
│   ├── TRACKER.md                  # Прогресс
│   ├── CHAT_REFERENCE.md           # История чатов
│   └── MASTER_PLAN.md              # План
│
├── backend/
│   └── app/
│       ├── main.py                 # FastAPI entry point
│       ├── api/
│       │   ├── indicator_routes.py # ⭐ TRG логика (2000+ строк)
│       │   ├── data_routes.py      # Binance Futures API
│       │   ├── preset_routes.py    # [v4] Пресеты
│       │   ├── bot_routes.py       # [v4] Bot config
│       │   ├── live_routes.py      # [v5] Live trading
│       │   └── telegram_routes.py  # [v5] Telegram
│       ├── indicators/
│       │   ├── trg.py              # [v4] TRG модуль
│       │   └── dominant.py         # [v4] Dominant модуль
│       ├── filters/                # [v4] Модульные фильтры
│       │   ├── base.py
│       │   ├── time.py
│       │   ├── volatility.py
│       │   ├── trend.py
│       │   ├── portfolio.py
│       │   └── protection.py
│       └── services/
│           ├── backtest.py         # Бэктест движок
│           ├── optimizer.py        # Оптимизатор
│           ├── scorer.py           # [v4] Signal Score
│           └── live_engine.py      # [v5] Live trading
│
├── frontend/
│   └── src/
│       ├── App.jsx                 # Навигация
│       ├── api.js                  # API клиент
│       ├── pages/
│       │   ├── Indicator.jsx       # Главная (6 вкладок)
│       │   ├── Data.jsx            # Управление данными
│       │   ├── Presets.jsx         # [v4] Библиотека пресетов
│       │   ├── Bots.jsx            # [v4] Bot configuration
│       │   ├── Live.jsx            # [v5] Live dashboard
│       │   ├── Signals.jsx         # Сигналы
│       │   └── Settings.jsx        # Настройки + Telegram
│       └── components/
│           └── Indicator/
│               ├── SettingsSidebar.jsx
│               ├── StatsPanel.jsx
│               ├── MonthlyPanel.jsx
│               ├── TradesTable.jsx
│               ├── HeatmapPanel.jsx
│               ├── AutoOptimizePanel.jsx
│               └── LogsPanel.jsx
│
├── data/                           # Данные свечей (parquet/csv)
├── logs/                           # Логи приложения
├── requirements.txt
├── package.json
└── *.bat                           # Windows батники
```

---

## 3. ИНДИКАТОРЫ

### 3.1 TRG Indicator (текущий)

**Тип:** ATR-based trend detection

**Параметры:**

| Параметр | Диапазон | Default | Описание |
|----------|----------|---------|----------|
| i1 (ATR Length) | 10-200 | 45 | Период ATR |
| i2 (Multiplier) | 1.0-10.0 | 4.0 | Множитель |

**Take Profits (10 уровней):**

| TP | Default % | Default Amount |
|----|-----------|----------------|
| TP1 | 1.05% | 50% |
| TP2 | 1.95% | 30% |
| TP3 | 3.75% | 15% |
| TP4 | 6.00% | 5% |
| TP5-10 | Custom | Custom |

**Stop Loss режимы:**

| Режим | Описание |
|-------|----------|
| Fixed | SL остаётся на месте |
| Breakeven | SL → Entry после TP1 |
| Cascade | SL двигается за каждым TP |

**Фильтры TRG:**

| Фильтр | Параметры |
|--------|-----------|
| SuperTrend | period, multiplier |
| RSI | period, overbought, oversold |
| ADX | period, threshold |
| Volume | min_volume |

---

### 3.2 Dominant Indicator (v4.0)

**Тип:** Channel + Fibonacci levels

**Параметры:**

| Параметр | Диапазон | Default | Описание |
|----------|----------|---------|----------|
| sensitivity | 12-60 | 21 | Чувствительность канала |

**Алгоритм:**
```python
# Channel calculation
high_channel = highest(high, sensitivity)
low_channel = lowest(low, sensitivity)
mid = (high_channel + low_channel) / 2

# Fibonacci levels for TP
fib_levels = [0.236, 0.382, 0.5, 0.618]

# Signals
can_long = close > mid and confirmation
can_short = close < mid and confirmation
```

**Take Profits (4 уровня):**
- TP1: Fib 0.236
- TP2: Fib 0.382
- TP3: Fib 0.5
- TP4: Fib 0.618

**Stop Loss режимы (5):**

| # | Режим | Описание |
|---|-------|----------|
| 0 | No SL | Без стоп-лосса |
| 1 | After TP1 | SL → Entry после TP1 |
| 2 | After TP2 | SL → Entry после TP2 |
| 3 | After TP3 | SL → Entry после TP3 |
| 4 | Cascade | SL двигается за каждым TP |

**Filter Types (5):**

| # | Тип | Описание |
|---|-----|----------|
| 0 | None | Без фильтров |
| 1 | ATR | ATR condition |
| 2 | RSI | RSI filter |
| 3 | ATR + RSI | Комбинация |
| 4 | Volatility | Volatility filter |

---

## 4. СИСТЕМА ПРЕСЕТОВ

### Философия

> **Universal solutions, not pair-specific overfitting**

Один пресет должен работать на ВСЕХ парах. Если пресет хорош только на BTCUSDT — он плохой.

### Типы пресетов

| Тип | Количество | Источник |
|-----|------------|----------|
| TRG System | 200 | Автогенерация |
| Dominant System | 125 | GG Pine Script |
| User Custom | ∞ | Пользователь |

### TRG: 200 пресетов (8 × 5 × 5)

**Оси генерации:**

```
i1 (ATR Length): 14, 25, 40, 60, 80, 110, 150, 200  → 8 значений
i2 (Multiplier): 2.0, 3.0, 4.0, 5.5, 7.5            → 5 значений
Filter Profile: N, T, M, S, F                       → 5 профилей
```

**Filter Profiles:**

| Code | Name | Описание |
|------|------|----------|
| N | None | Без фильтров |
| T | Trend | SuperTrend only |
| M | Momentum | RSI only |
| S | Strength | ADX only |
| F | Full | Все фильтры |

**Naming Convention:**
```
{FILTER}_{i1}_{i2*10}

Примеры:
- N_45_40   → None, i1=45, i2=4.0
- T_60_55   → Trend, i1=60, i2=5.5
- F_80_30   → Full, i1=80, i2=3.0
```

### Dominant: 125 пресетов (из GG strategies)

Импортируются из оригинального Pine Script. Различные комбинации:
- sensitivity (12-60)
- filter_type (0-4)
- sl_mode (0-4)

### User Presets

| Операция | Описание |
|----------|----------|
| Create | Создать свой пресет |
| Clone | Клонировать системный |
| Edit | Редактировать свой |
| Delete | Удалить свой |
| Import | Импорт из JSON |
| Export | Экспорт в JSON |

---

## 5. SIGNAL SCORE

### Концепция

Каждый сигнал получает оценку 0-100 баллов и грейд A-F.

### Компоненты (4 × 25 = 100)

| Компонент | Max | Описание |
|-----------|-----|----------|
| Confluence | 25 | Совпадение нескольких индикаторов |
| Multi-TF Alignment | 25 | Подтверждение на старших ТФ (4H, 1D) |
| Market Context | 25 | Тренд + волатильность рынка |
| Technical Levels | 25 | Близость к S/R уровням |

### Грейды

| Score | Grade | Описание |
|-------|-------|----------|
| 85-100 | A | Excellent |
| 70-84 | B | Good |
| 55-69 | C | Average |
| 40-54 | D | Below Average |
| 0-39 | F | Poor |

### Использование

- Фильтрация сигналов (min_score)
- Размер позиции (score-based sizing)
- Статистика (win rate by grade)

---

## 6. МОДУЛЬНЫЕ ФИЛЬТРЫ

### Архитектура

```python
class FilterBase(ABC):
    @abstractmethod
    def should_allow(self, signal, context) -> bool:
        pass
    
    @abstractmethod
    def get_config_schema(self) -> dict:
        pass

class FilterChain:
    def __init__(self, filters: List[FilterBase]):
        self.filters = filters
    
    def apply(self, signal, context) -> Tuple[bool, List[str]]:
        """Returns (allowed, rejection_reasons)"""
        pass
```

### 5 Категорий фильтров

#### 6.1 Time Filters

| Фильтр | Параметры | Описание |
|--------|-----------|----------|
| SessionFilter | sessions[] | Asia/Europe/US |
| WeekdayFilter | days[] | Mon-Sun |
| CooldownFilter | minutes | Мин. время между сделками |

#### 6.2 Volatility Filters

| Фильтр | Параметры | Описание |
|--------|-----------|----------|
| ATRFilter | min_atr, max_atr | Диапазон ATR |
| VolumeFilter | min_volume | Минимальный объём |
| ExtremeFilter | threshold | Блокировка при экстремах |

#### 6.3 Trend Filters

| Фильтр | Параметры | Описание |
|--------|-----------|----------|
| BTCTrendFilter | enabled | Торговля по тренду BTC |
| MultiTFFilter | timeframes[] | Совпадение на старших ТФ |
| RegimeFilter | type | Trending/Ranging market |

#### 6.4 Portfolio Filters

| Фильтр | Параметры | Описание |
|--------|-----------|----------|
| CorrelationFilter | max_corr | Блокировка коррелированных |
| DirectionFilter | max_long, max_short | Лимит направлений |
| SectorFilter | max_per_sector | Диверсификация |

#### 6.5 Protection Filters

| Фильтр | Параметры | Описание |
|--------|-----------|----------|
| EquityCurveFilter | ma_period | Торговля при растущем equity |
| MaxDDFilter | max_dd% | Остановка при drawdown |
| StreakFilter | max_losses | После серии лоссов |
| RecoveryFilter | scale_factor | Уменьшение размера |

---

## 7. BOT CONFIGURATION

### BotConfig Structure

```python
@dataclass
class BotConfig:
    # Identification
    id: str
    name: str
    
    # Indicator
    indicator_type: str  # 'trg' | 'dominant'
    preset_id: str
    
    # Risk Management (НЕ оптимизируется)
    deposit: float
    risk_per_trade: float  # 1-5%
    max_positions: int     # 1-10
    leverage: int          # 1-125
    daily_dd_limit: float  # %
    
    # Pairs
    pairs: List[str]
    
    # Filters
    filter_config: FilterConfig
    
    # Status
    is_active: bool
    created_at: datetime
```

### Risk Management

| Параметр | Диапазон | Описание |
|----------|----------|----------|
| deposit | 100-∞ USDT | Начальный депозит |
| risk_per_trade | 1-5% | Риск на сделку |
| max_positions | 1-10 | Макс. одновременных позиций |
| leverage | 1-125x | Плечо |
| daily_dd_limit | 5-20% | Дневной лимит просадки |

### Bot Optimization

**Что оптимизируется:**
- Набор торговых пар
- Параметры фильтров
- Выбор пресета

**Что НЕ оптимизируется:**
- risk_per_trade (фиксирован)
- max_positions (фиксирован)
- leverage (фиксирован)

---

## 8. LIVE TRADING ENGINE

### Компоненты

```
┌─────────────────────────────────────────┐
│           Live Trading Engine           │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌────────────────┐ │
│  │    Data     │    │    Signal      │ │
│  │   Fetcher   │───▶│   Generator    │ │
│  │ (APScheduler)│    │                │ │
│  └─────────────┘    └───────┬────────┘ │
│                             │          │
│  ┌─────────────┐    ┌───────▼────────┐ │
│  │  WebSocket  │    │    Filter      │ │
│  │   Client    │    │    Chain       │ │
│  └─────────────┘    └───────┬────────┘ │
│                             │          │
│                     ┌───────▼────────┐ │
│                     │   Position     │ │
│                     │   Tracker      │ │
│                     └───────┬────────┘ │
│                             │          │
│                     ┌───────▼────────┐ │
│                     │   Telegram     │ │
│                     │   Notifier     │ │
│                     └────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

### Data Fetcher

- APScheduler для фоновых задач
- Подкачка свечей каждую минуту
- Обработка ошибок API
- Retry с exponential backoff

### Signal Generator

- Мониторинг на новые сигналы
- Расчёт Signal Score
- Применение Filter Chain

### Position Tracker

- Виртуальные позиции (без реального исполнения в v4)
- TP/SL monitoring
- P&L calculation
- Equity curve

---

## 9. TELEGRAM INTEGRATION

### Архитектура

```
┌─────────────────────────────────────────┐
│          Telegram Integration           │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────┐         ┌─────────┐       │
│  │  Bot 1  │         │  Bot 2  │       │
│  └────┬────┘         └────┬────┘       │
│       │                   │            │
│       └─────────┬─────────┘            │
│                 │                      │
│         ┌───────▼───────┐              │
│         │ Signal Router │              │
│         └───────┬───────┘              │
│                 │                      │
│    ┌────────────┼────────────┐         │
│    ▼            ▼            ▼         │
│ ┌──────┐   ┌──────┐     ┌──────┐      │
│ │ Ch 1 │   │ Ch 2 │ ... │ Ch N │      │
│ └──────┘   └──────┘     └──────┘      │
│                                         │
└─────────────────────────────────────────┘
```

### Cornix Format

```
#BTCUSDT
LONG

Entry: 45000

Take Profits:
TP1: 45500 (50%)
TP2: 46000 (30%)
TP3: 46500 (15%)
TP4: 47000 (5%)

Stop Loss: 44000

Leverage: 10x
```

### Signal Router

| Правило | Описание |
|---------|----------|
| By Indicator | TRG → Bot1, Dominant → Bot2 |
| By Score | A/B → Premium, C/D → Free |
| By Pair | BTC/ETH → Channel1, Alts → Channel2 |

### Notifications

| Тип | Когда |
|-----|-------|
| Signal | Новый сигнал |
| TP Hit | Достигнут TP |
| SL Hit | Достигнут SL |
| Daily Summary | Ежедневно в 00:00 UTC |
| Weekly Report | Воскресенье |

---

## 10. API ENDPOINTS

### Data API

```
GET    /api/data/symbols              # Список пар
GET    /api/data/timeframes           # Таймфреймы
POST   /api/data/download             # Загрузка с Binance
GET    /api/data/status               # Статус данных
POST   /api/data/sync                 # Синхронизация
DELETE /api/data/{symbol}/{tf}        # Удаление
```

### Indicator API

```
POST   /api/indicator/calculate       # Расчёт + бэктест
GET    /api/indicator/auto-optimize-stream  # SSE оптимизация
POST   /api/indicator/heatmap         # Heatmap i1/i2
GET    /api/indicator/replay/{id}     # Replay mode
```

### Preset API (v4)

```
GET    /api/presets/list              # Все пресеты
GET    /api/presets/{id}              # Один пресет
POST   /api/presets/create            # Создать
PUT    /api/presets/{id}              # Обновить
DELETE /api/presets/{id}              # Удалить
POST   /api/presets/import            # Импорт JSON
GET    /api/presets/export/{id}       # Экспорт JSON
POST   /api/presets/generate          # Генерация 200 TRG
```

### Bot API (v4)

```
GET    /api/bots/list                 # Все боты
GET    /api/bots/{id}                 # Один бот
POST   /api/bots/create               # Создать
PUT    /api/bots/{id}                 # Обновить
DELETE /api/bots/{id}                 # Удалить
POST   /api/bots/{id}/backtest        # Бэктест
GET    /api/bots/{id}/backtest-stream # SSE бэктест
POST   /api/bots/{id}/optimize        # Оптимизация
```

### Live API (v5)

```
GET    /api/live/status               # Статус движка
POST   /api/live/start                # Запуск
POST   /api/live/stop                 # Остановка
GET    /api/live/signals              # Активные сигналы
GET    /api/live/positions            # Открытые позиции
GET    /api/live/stats                # Статистика
WS     /api/live/ws                   # WebSocket
```

### Telegram API (v5)

```
GET    /api/telegram/bots             # Список ботов
POST   /api/telegram/bots             # Добавить бота
GET    /api/telegram/channels         # Список каналов
POST   /api/telegram/channels         # Добавить канал
POST   /api/telegram/test             # Тест отправки
```

---

## 11. DATABASE SCHEMA

### SQLite Tables

```sql
-- Свечные данные
CREATE TABLE candles (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    UNIQUE(symbol, timeframe, timestamp)
);

-- Пресеты
CREATE TABLE presets (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    indicator_type TEXT NOT NULL,  -- 'trg' | 'dominant'
    category TEXT NOT NULL,        -- 'system' | 'user'
    config JSON NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Боты
CREATE TABLE bots (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    preset_id TEXT REFERENCES presets(id),
    deposit REAL,
    risk_per_trade REAL,
    max_positions INTEGER,
    leverage INTEGER,
    daily_dd_limit REAL,
    pairs JSON,
    filter_config JSON,
    is_active BOOLEAN,
    created_at TIMESTAMP
);

-- Сделки (бэктест)
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    bot_id TEXT REFERENCES bots(id),
    symbol TEXT,
    direction TEXT,  -- 'long' | 'short'
    entry_time TIMESTAMP,
    entry_price REAL,
    exit_time TIMESTAMP,
    exit_price REAL,
    pnl_percent REAL,
    pnl_absolute REAL,
    exit_reason TEXT,  -- 'tp1' | 'tp2' | ... | 'sl'
    signal_score INTEGER
);

-- Telegram боты
CREATE TABLE telegram_bots (
    id TEXT PRIMARY KEY,
    name TEXT,
    token TEXT NOT NULL,
    is_active BOOLEAN
);

-- Telegram каналы
CREATE TABLE telegram_channels (
    id TEXT PRIMARY KEY,
    bot_id TEXT REFERENCES telegram_bots(id),
    chat_id TEXT NOT NULL,
    name TEXT,
    routing_rules JSON
);

-- Настройки
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value JSON
);
```

---

## 12. FRONTEND STRUCTURE

### Страницы

| Страница | Описание | Статус |
|----------|----------|--------|
| Indicator | TRG (6 вкладок) | ✅ v3.5 |
| Data | Управление данными | ✅ v3.5 |
| Presets | Библиотека пресетов | ⬜ v4 |
| Bots | Конфигурация ботов | ⬜ v4 |
| Live | Live dashboard | ⬜ v5 |
| Signals | История сигналов | ✅ v3.5 |
| Settings | Настройки + Telegram | ⬜ v4/v5 |

### Indicator Page (6 вкладок)

| Вкладка | Компонент | Описание |
|---------|-----------|----------|
| 📈 График | Chart | Свечи + Equity Curve |
| 📊 Статистика | StatsPanel | Win Rate, PF, DD |
| 📋 Сделки | TradesTable | Таблица с фильтрами |
| 📅 Месяцы | MonthlyPanel | Помесячный PnL |
| 🔥 Оптимизация | AutoOptimizePanel | 5 режимов SSE |
| 🗺️ Heatmap | HeatmapPanel | Тепловая карта i1/i2 |

---

## 13. ПОЛНЫЙ ПЛАН ЧАТОВ

### Сводка

| Метрика | Значение |
|---------|----------|
| Всего чатов | 98 |
| QA Checkpoints | 15 |
| Фаз | 14 |
| Завершено | 3 (#15-17) |

### Фаза 1: Стабилизация (#15-19)

| # | Название | Статус |
|---|----------|--------|
| 15 | Bugfixes UI | ✅ |
| 16 | Bugfixes Backend | ✅ |
| 17 | Data Futures Only | ✅ |
| **18** | **Data Period Selection** | **⏳ NEXT** |
| 19 | QA Checkpoint #1 | ⬜ |

### Фаза 2: Dominant Indicator (#20-28)

| # | Название |
|---|----------|
| 20 | Dominant: Core |
| 21 | Dominant: Signals |
| 22 | Dominant: Filters |
| 23 | Dominant: SL Modes |
| 24 | QA Checkpoint #2 |
| 25 | Dominant: AI Resolution |
| 26 | Dominant: 125 Presets DB |
| 27 | Dominant: UI Integration |
| 28 | Dominant: Verification |

### Фаза 3: Preset System (#29-36)

| # | Название |
|---|----------|
| 29 | QA Checkpoint #3 |
| 30 | Presets: Architecture |
| 31 | Presets: TRG Generator |
| 32 | Presets: Storage |
| 33 | Presets: User CRUD |
| 34 | QA Checkpoint #4 |
| 35 | Presets: Import/Export |
| 36 | Presets: UI Library |

### Фаза 4: Signal Score (#37-40)

| # | Название |
|---|----------|
| 37 | Score: Core |
| 38 | Score: Multi-TF |
| 39 | QA Checkpoint #5 |
| 40 | Score: UI Badges |

### Фаза 5: General Filters (#41-49)

| # | Название |
|---|----------|
| 41 | Filters: Architecture |
| 42 | Filters: Time |
| 43 | Filters: Volatility |
| 44 | QA Checkpoint #6 |
| 45 | Filters: Trend |
| 46 | Filters: Portfolio |
| 47 | Filters: Protection |
| 48 | Filters: Integration |
| 49 | QA Checkpoint #7 |

### Фаза 6: Preset Optimization (#50-54)

| # | Название |
|---|----------|
| 50 | Preset Optimizer: Core |
| 51 | Preset Optimizer: Modes |
| 52 | Preset Optimizer: Results |
| 53 | Preset Optimizer: Validation |
| 54 | QA Checkpoint #8 |

### Фаза 7: Bot Configuration (#55-59)

| # | Название |
|---|----------|
| 55 | Bot: Config Structure |
| 56 | Bot: Pair Selection |
| 57 | Bot: Filter Integration |
| 58 | Bot: UI |
| 59 | QA Checkpoint #9 |

### Фаза 8: Bot Backtest (#60-66)

| # | Название |
|---|----------|
| 60 | Bot Backtest: Core |
| 61 | Bot Backtest: RM |
| 62 | Bot Backtest: Filters |
| 63 | Bot Backtest: Stats |
| 64 | QA Checkpoint #10 |
| 65 | Bot Backtest: Equity |
| 66 | Bot Backtest: UI |

### Фаза 9: Bot Optimization (#67-71)

| # | Название |
|---|----------|
| 67 | Bot Optimizer: Core |
| 68 | Bot Optimizer: Pairs |
| 69 | QA Checkpoint #11 |
| 70 | Bot Optimizer: Filters |
| 71 | Bot Optimizer: Validation |

### Фаза 10: Live Engine (#72-78)

| # | Название |
|---|----------|
| 72 | Live: Data Fetcher |
| 73 | Live: WebSocket |
| 74 | QA Checkpoint #12 |
| 75 | Live: Signal Generator |
| 76 | Live: Position Tracker |
| 77 | Live: Dashboard |
| 78 | Live: UI |

### Фаза 11: Telegram (#79-86)

| # | Название |
|---|----------|
| 79 | QA Checkpoint #13 |
| 80 | Telegram: Bot Core |
| 81 | Telegram: Channels |
| 82 | Telegram: Cornix |
| 83 | Telegram: Router |
| 84 | QA Checkpoint #14 |
| 85 | Telegram: Notifications |
| 86 | Telegram: UI |

### Фаза 12: UI Redesign (#87-91)

| # | Название |
|---|----------|
| 87 | Design: System |
| 88 | Design: Components |
| 89 | QA Checkpoint #15 |
| 90 | Design: Pages |
| 91 | Design: Mobile |

### Фаза 13: Final QA (#92-95)

| # | Название |
|---|----------|
| 92 | QA: Full E2E |
| 93 | QA: Performance |
| 94 | QA: Security |
| 95 | QA: Final Fixes |

### Фаза 14: Release (#96-98)

| # | Название |
|---|----------|
| 96 | Deploy: Batfiles |
| 97 | Deploy: GitHub |
| 98 | v4.0 RELEASE 🎉 |

---

## 14. ПРАВИЛА РАЗРАБОТКИ

### ⛔ ЗАПРЕЩЕНО

1. Урезать функционал без разрешения
2. Удалять компоненты/функции
3. Код текстом в чат (только ZIP!)
4. Заглушки (stubs)
5. Русский в .bat файлах

### ✅ ОБЯЗАТЕЛЬНО

1. **ZIP архивы** для кода
2. `encoding='utf-8'` для Windows
3. **Git commit на АНГЛИЙСКОМ**
4. Обновлять docs/TRACKER.md
5. Обновлять docs/CHAT_REFERENCE.md
6. **Писать:** "Следующий чат: #XX — Название"

### QA Checkpoints

Каждые 4 чата — QA Checkpoint:
- Проверка логов
- Тестирование функций
- Фикс найденных багов

---

*Документ для Project Knowledge — статичный*  
*Динамичная информация — на GitHub в docs/*
