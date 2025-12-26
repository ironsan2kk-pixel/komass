# 📊 Komas Data Module

Модуль управления историческими данными.

## 📁 Структура

```
backend/app/
├── core/
│   └── data/
│       ├── __init__.py      # Экспорты модуля
│       ├── binance.py       # Binance API клиент (~300 строк)
│       ├── storage.py       # Работа с Parquet (~250 строк)
│       └── manager.py       # Фасад-менеджер (~300 строк)
└── api/
    └── data.py              # REST API (~200 строк)
```

## 🔧 Компоненты

### BinanceClient

Асинхронный клиент для загрузки данных с Binance.

```python
from app.core.data import BinanceClient

client = BinanceClient(source="spot")  # или "futures"

# Загрузка истории
candles = await client.download_history(
    symbol="BTCUSDT",
    timeframe="1h",
    on_progress=lambda p: print(f"{p.percent}%")
)

# Синхронизация
new_candles = await client.sync_latest("BTCUSDT", "1h", last_ts)

await client.close()
```

**Особенности:**
- Retry logic (5 попыток)
- Rate limiting (0.15с между запросами)
- Обработка 429/418 ошибок
- Checkpoint callbacks

### DataStorage

Хранение данных в Parquet файлах.

```python
from app.core.data import DataStorage

storage = DataStorage()

# Загрузить данные
df = storage.load("BTCUSDT", "1h")

# Сохранить
storage.save("BTCUSDT", "1h", df)

# Информация о файле
info = storage.get_info("BTCUSDT", "1h")
print(f"{info.rows} rows, {info.size_mb} MB")

# Список файлов
files = storage.list_files()

# Устаревшие файлы
outdated = storage.get_outdated_files(max_age_days=7)
```

### DataManager

Главный фасад модуля.

```python
from app.core.data import DataManager

manager = DataManager(source="spot")

# Запустить загрузку (в фоне)
task = await manager.download_async(
    symbols=["BTCUSDT", "ETHUSDT"],
    timeframe="1h"
)

# Отслеживание прогресса
progress = manager.get_progress(task.task_id)
print(f"{progress['completed']}/{progress['total']}")

# Синхронизация всех файлов
result = await manager.sync_all("1h")

# Получить данные
df = manager.load("BTCUSDT", "1h")
```

## 🌐 API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/data/symbols` | Список символов Binance |
| GET | `/api/data/timeframes` | Список таймфреймов |
| GET | `/api/data/available` | Загруженные файлы |
| GET | `/api/data/outdated` | Устаревшие файлы |
| POST | `/api/data/download` | Начать загрузку |
| GET | `/api/data/download/progress` | Прогресс загрузки |
| POST | `/api/data/download/cancel/{id}` | Отменить загрузку |
| POST | `/api/data/sync` | Синхронизация |
| POST | `/api/data/continue/{symbol}/{tf}` | Докачать символ |
| DELETE | `/api/data/file/{filename}` | Удалить файл |
| GET | `/api/data/debug` | Отладка |
| GET | `/api/data/info/{symbol}/{tf}` | Инфо о файле |

### Примеры запросов

**Загрузка:**
```bash
curl -X POST http://localhost:8000/api/data/download \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["BTCUSDT", "ETHUSDT"], "timeframe": "1h", "source": "spot"}'
```

**Прогресс:**
```bash
curl http://localhost:8000/api/data/download/progress
```

**Синхронизация:**
```bash
curl -X POST http://localhost:8000/api/data/sync \
  -H "Content-Type: application/json" \
  -d '{"timeframe": "1h"}'
```

## 📦 Формат данных

Файлы хранятся в формате **Parquet** с индексом `timestamp`:

```
data/
├── BTCUSDT_1h.parquet
├── ETHUSDT_1h.parquet
└── ...
```

**Колонки:**
- `timestamp` (index) — datetime
- `open` — float
- `high` — float
- `low` — float
- `close` — float
- `volume` — float

## ⚙️ Конфигурация

В `.env`:
```env
# Папка данных (опционально)
DATA_DIR=./data

# Источник по умолчанию
DEFAULT_DATA_SOURCE=spot
```

## 🔗 Интеграция

В `main.py`:
```python
from app.api import data

app.include_router(data.router)
```

При запуске появится в логах:
```
✓ Loaded: data routes
```

## 📊 Константы

**Таймфреймы:**
```python
TIMEFRAMES = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}
```

**Символы:** 100 топ пар Binance Futures

**Начальные даты:**
- Spot: 2017-08-01
- Futures: 2019-09-01

## 🛡️ Обработка ошибок

Все ошибки логируются через централизованный Logger:

```
14:32:15 | ERROR | [data.binance] Rate limited, waiting 60s...
14:33:17 | INFO  | [data.manager] ✓ BTCUSDT: 45,230 candles
```

---

*Модуль разработан в рамках Komas Trading System v3*
