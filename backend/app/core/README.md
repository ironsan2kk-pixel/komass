# Komas Core: Database Module

## Обзор

Модуль базы данных для Komas Trading Server. Использует SQLite + SQLAlchemy с async поддержкой.

## Установка

```bash
pip install sqlalchemy aiosqlite
```

## Модели данных

### Settings
Глобальные настройки приложения (key-value хранилище с типизацией)

```python
from app.core import SettingsManager

# Set
await SettingsManager.set("app.name", "Komas", "Application name")
await SettingsManager.set("optimization.workers", 4)
await SettingsManager.set("features.enabled", {"live": True, "paper": True})

# Get
name = await SettingsManager.get("app.name")
workers = await SettingsManager.get("optimization.workers", default=0)

# Get all
all_settings = await SettingsManager.get_all()
```

### Preset
Сохранённые настройки индикатора

```python
from app.core import PresetManager

# Create
preset = await PresetManager.create(
    name="TRG Aggressive",
    description="High risk, high reward",
    settings={
        "trg_atr_length": 30,
        "trg_multiplier": 3.0,
        "tp_count": 4,
    },
    tags=["aggressive", "btc"]
)

# Get
preset = await PresetManager.get(preset_id)
preset = await PresetManager.get_by_name("TRG Aggressive")

# List
presets = await PresetManager.list_all(favorites_only=True)

# Update performance after backtest
await PresetManager.update_performance(
    preset_id,
    win_rate=75.5,
    profit_factor=2.3,
    total_profit_percent=156.7
)

# Delete
await PresetManager.delete(preset_id)
```

### Bot
Конфигурации торговых ботов

```python
from app.core import BotManager

# Create
bot = await BotManager.create(
    name="BTC Scalper",
    symbol="BTCUSDT",
    timeframe="5m",
    preset_id=1,
    telegram_enabled=True
)

# Activate/Deactivate
await BotManager.activate(bot_id)
await BotManager.deactivate(bot_id)

# List active bots
active_bots = await BotManager.list_all(active_only=True)

# Update stats after trade
await BotManager.increment_stats(bot_id, is_win=True, pnl=52.5)
```

### Signal
Торговые сигналы

```python
from app.core import SignalManager

# Create
signal = await SignalManager.create(
    bot_id=1,
    symbol="BTCUSDT",
    timeframe="1h",
    direction="long",
    entry_price=50000.0,
    stop_loss=48000.0,
    take_profits=[
        {"percent": 1.05, "amount": 50, "price": 50525.0},
        {"percent": 1.95, "amount": 30, "price": 50975.0},
    ]
)

# Close
await SignalManager.close(
    signal_id,
    exit_price=50525.0,
    exit_reason="tp1",
    pnl_percent=1.05
)

# Get active for bot
active = await SignalManager.get_active_by_bot(bot_id)
```

### DataCacheInfo
Метаданные кэшированных файлов данных

```python
from app.core import DataCacheManager

# Upsert (create or update)
cache = await DataCacheManager.upsert(
    symbol="BTCUSDT",
    timeframe="1h",
    source="binance",
    candles_count=8760,
    is_complete=True
)

# Get
cache = await DataCacheManager.get("BTCUSDT", "1h", "binance")

# List all
caches = await DataCacheManager.list_all(source="binance")
```

## API Endpoints

### Database Info
```
GET /api/db/info
```

### Settings
```
GET  /api/db/settings           - List all settings
GET  /api/db/settings/{key}     - Get setting
POST /api/db/settings           - Set setting
DELETE /api/db/settings/{key}   - Delete setting
```

### Presets
```
GET    /api/db/presets                      - List presets
GET    /api/db/presets/{id}                 - Get preset
POST   /api/db/presets                      - Create preset
PUT    /api/db/presets/{id}                 - Update preset
PUT    /api/db/presets/{id}/performance     - Update metrics
POST   /api/db/presets/{id}/favorite        - Toggle favorite
DELETE /api/db/presets/{id}                 - Delete preset
```

### Data Cache
```
GET    /api/db/cache                        - List all cached data
GET    /api/db/cache/{symbol}/{timeframe}   - Get cache info
DELETE /api/db/cache/{symbol}/{timeframe}   - Delete cache info
```

## Инициализация

В `main.py`:

```python
from app.core.database import init_db, close_db, create_default_settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    await create_default_settings()
    
    yield
    
    # Shutdown
    await close_db()
```

## Тестирование

```bash
cd backend
python -m app.core.test_database
```

## Файлы

```
backend/app/core/
├── __init__.py          # Exports
├── database.py          # Models + Managers (700+ строк)
└── test_database.py     # Tests

backend/app/api/
└── db_routes.py         # REST API endpoints
```

## База данных

Файл: `data/komas.db`

SQLite с включёнными:
- Foreign keys
- WAL mode (для производительности)
- Async операции через aiosqlite
