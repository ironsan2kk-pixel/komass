# Komas Core Module

## Обзор

Core модуль предоставляет централизованную инфраструктуру для всего Komas Trading Server:

- **Config** - конфигурация через Pydantic Settings + .env файлы
- **Logger** - продвинутое логирование с цветами, ротацией, структурированным выводом

## Структура

```
backend/app/core/
├── __init__.py     # Экспорты модуля
├── config.py       # Конфигурация (Settings)
└── logger.py       # Логирование (Logger)
```

## Использование

### Config

```python
from app.core import settings

# Доступ к настройкам
print(settings.server.port)           # 8000
print(settings.trading.leverage)      # 10
print(settings.optimization.workers)  # auto (CPU-1)

# Пути
print(settings.data_dir)              # Path to data/
print(settings.logs_dir)              # Path to logs/

# Проверки
if settings.is_production():
    # Production mode
    pass
```

### Logger

```python
from app.core import logger

# Стандартные методы
logger.info("Server started")
logger.warning("Low memory")
logger.error("Connection failed", exc_info=True)

# Кастомные типы логов
logger.trade("BUY BTCUSDT @ 50000")
logger.signal("LONG signal generated")
logger.optimization("Testing i1=45, i2=4.0")
logger.backtest("Win Rate: 65%")
logger.data("Downloaded 1000 candles")

# Специальные
logger.success("Optimization complete!")
logger.fail("Connection timeout")
logger.progress(50, 100, "Processing")

# Startup/Shutdown баннеры
logger.startup("Komas Trading Server v3.5")
logger.shutdown("Server stopped")
```

### Получение отдельного логгера

```python
from app.core import get_logger

# Для модуля
log = get_logger(__name__)
log.info("Module loaded")
```

## Конфигурация через .env

Скопируйте `.env.example` в `.env` и настройте:

```bash
cp .env.example .env
```

### Основные переменные

| Переменная | Описание | Default |
|------------|----------|---------|
| `KOMAS_ENVIRONMENT` | development/production/testing | development |
| `KOMAS_PORT` | Порт сервера | 8000 |
| `KOMAS_LOG_LEVEL` | DEBUG/INFO/WARNING/ERROR | INFO |
| `KOMAS_OPT_MAX_WORKERS` | Воркеры (пусто = auto) | CPU-1 |

### Секции конфигурации

- **Server** - хост, порт, CORS
- **Database** - путь к SQLite
- **Trading** - дефолты стратегии (TRG, TP, SL)
- **Optimization** - воркеры, диапазоны, GA параметры
- **Notifications** - Telegram, Discord
- **Exchange** - API ключи бирж
- **Logging** - уровень, формат, ротация

## Логи

Логи автоматически пишутся в `backend/logs/`:

- `komas_YYYY-MM-DD.log` - все логи
- `errors_YYYY-MM-DD.log` - только ошибки

### API эндпоинты для логов

```
GET  /api/logs/list           # Список файлов
GET  /api/logs/today          # Сегодняшний лог
GET  /api/logs/errors         # Только ошибки
GET  /api/logs/read/{file}    # Конкретный файл
GET  /api/logs/download/{file}# Скачать файл
DELETE /api/logs/clear        # Очистить старые
```

## Цветной вывод в консоль

```
12:34:56 │ ℹ️  INFO     │ komas                │ Server started
12:34:57 │ 📈 INFO     │ komas                │ TRADE │ BUY BTCUSDT @ 50000
12:34:58 │ ⚠️  WARNING  │ komas                │ Low memory
12:34:59 │ ❌ ERROR    │ komas                │ Connection failed
```

## Форматы логов

### Text (default)
```
2025-01-15 12:34:56.789 │ INFO     │ app.api.indicator_routes  │ calculate      │ L145 │ Processing BTCUSDT
```

### JSON (для ELK/Grafana)
```json
{"timestamp":"2025-01-15T12:34:56.789","level":"INFO","logger":"app.api.indicator_routes","function":"calculate","line":145,"message":"Processing BTCUSDT"}
```

Включить JSON формат:
```env
KOMAS_LOG_FORMAT=json
```

## Интеграция с main.py

```python
from app.core import settings, logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.startup(f"{settings.app_name} v{settings.app_version}")
    yield
    logger.shutdown("Server stopped")
```
