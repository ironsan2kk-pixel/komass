# Komas Indicators - Plugin System

## Обзор

Модуль `indicators` предоставляет систему плагинов для индикаторов.

## Структура

```
backend/app/
├── indicators/              # Система плагинов
│   ├── __init__.py         # Главные экспорты
│   ├── registry.py         # Реестр плагинов (~500 строк)
│   ├── loader.py           # Загрузчик плагинов (~550 строк)
│   └── base/               # Базовые классы (из чата #05)
│       ├── __init__.py
│       ├── indicator.py    # BaseIndicator
│       ├── trading.py      # BaseTradingSystem
│       ├── filter.py       # BaseFilter
│       ├── optimizer.py    # BaseOptimizer
│       └── backtest.py     # BaseBacktest
│
├── plugins/                 # Папка плагинов
│   └── trg/                # TRG индикатор
│       ├── manifest.json   # Манифест плагина
│       ├── indicator/      # Индикатор
│       ├── trading/        # Торговая система
│       ├── filters/        # Фильтры
│       ├── optimizer/      # Оптимизатор
│       └── backtest/       # Бэктест
│
└── api/
    └── plugins.py          # REST API (~350 строк)
```

## Компоненты

### Registry (registry.py)

Глобальный реестр для всех плагинов:

```python
from app.indicators import registry

# Регистрация через декоратор
@register_indicator("my_indicator", "My Indicator", version="1.0.0")
class MyIndicator(BaseIndicator):
    ...

# Получение плагина
IndicatorClass = registry.indicators.get("my_indicator")

# Статистика
stats = registry.get_stats()
```

### PluginLoader (loader.py)

Загрузчик плагинов из manifest.json:

```python
from app.indicators import get_loader, discover_plugins

# Загрузка одного плагина
loader = get_loader()
result = loader.load_from_manifest("plugins/trg/manifest.json")

# Автодискавери
results = discover_plugins("./plugins")
```

### manifest.json

Формат манифеста плагина:

```json
{
    "id": "trg",
    "name": "TRG Indicator",
    "version": "1.0.0",
    "description": "...",
    "author": "Komas Team",
    
    "entry_points": {
        "indicator": "indicator.core:TRGIndicator",
        "trading_system": "trading.system:TRGTradingSystem",
        "filters": [
            "filters.supertrend:SuperTrendFilter"
        ],
        "optimizer": "optimizer.main:TRGOptimizer",
        "backtest": "backtest.engine:TRGBacktest"
    },
    
    "dependencies": [],
    "settings": {}
}
```

## REST API

### Endpoints

| Method | Endpoint | Описание |
|--------|----------|----------|
| GET | `/api/plugins/` | Список плагинов |
| GET | `/api/plugins/{id}` | Инфо о плагине |
| GET | `/api/plugins/registry` | Статистика реестра |
| POST | `/api/plugins/load` | Загрузить плагин |
| POST | `/api/plugins/unload` | Выгрузить плагин |
| POST | `/api/plugins/reload` | Перезагрузить |
| POST | `/api/plugins/discover` | Автодискавери |
| GET | `/api/plugins/indicators/list` | Список индикаторов |
| GET | `/api/plugins/filters/list` | Список фильтров |

### Примеры

```bash
# Список плагинов
curl http://localhost:8000/api/plugins/

# Загрузка плагина
curl -X POST http://localhost:8000/api/plugins/load \
  -H "Content-Type: application/json" \
  -d '{"manifest_path": "./plugins/trg/manifest.json"}'

# Автодискавери
curl -X POST http://localhost:8000/api/plugins/discover \
  -H "Content-Type: application/json" \
  -d '{"plugins_dir": "./plugins"}'

# Статистика реестра
curl http://localhost:8000/api/plugins/registry
```

## Создание плагина

1. Создать папку в `plugins/`
2. Создать `manifest.json`
3. Реализовать классы наследуя от базовых
4. Загрузить через API или автодискавери

Пример минимального плагина:

```
plugins/my_indicator/
├── manifest.json
├── __init__.py
└── indicator/
    ├── __init__.py
    └── core.py          # class MyIndicator(BaseIndicator)
```

## Интеграция в main.py

```python
from fastapi import FastAPI
from app.api.plugins import router as plugins_router
from app.indicators import discover_plugins

app = FastAPI()
app.include_router(plugins_router)

@app.on_event("startup")
async def startup():
    # Автозагрузка плагинов
    discover_plugins("./plugins")
```

## Версии

- **v1.0.0** - Чат #06: Registry и PluginLoader
- База: Чат #05 (BaseIndicator, BaseTradingSystem и др.)

---

*Чат #06 — Indicators: PluginLoader (2025-12-25)*
