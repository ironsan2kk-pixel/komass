# Komas Indicator API v1.0.0

Модульный API для расчёта индикаторов, бэктестинга и оптимизации.

## 📁 Файлы

```
backend/app/api/
├── __init__.py           # Экспорты API
├── indicator.py          # Основной API индикатора (~1800 строк)
└── test_indicator_api.py # Тесты

test_indicator_api.bat    # Запуск тестов
```

## 🔌 API Endpoints

### Основные операции

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/api/indicator/calculate` | Расчёт индикатора + бэктест |
| GET | `/api/indicator/candles/{symbol}/{timeframe}` | Получить свечи для графика |
| POST | `/api/indicator/replay` | Режим воспроизведения (step-by-step) |
| POST | `/api/indicator/heatmap` | Генерация тепловой карты i1/i2 |
| POST | `/api/indicator/auto-optimize-stream` | SSE оптимизация |

### Plugin API

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/indicator/{plugin_id}/ui-schema` | UI схема плагина |
| GET | `/api/indicator/{plugin_id}/defaults` | Дефолтные настройки |
| POST | `/api/indicator/{plugin_id}/validate` | Валидация настроек |
| GET | `/api/indicator/plugins` | Список плагинов |
| GET | `/api/indicator/health` | Health check |

## 📊 Модели данных

### IndicatorSettings

```python
{
    # Data
    "symbol": "BTCUSDT",
    "timeframe": "1h",
    "start_date": null,
    "end_date": null,
    
    # TRG Indicator
    "trg_atr_length": 45,      # i1: 5-500
    "trg_multiplier": 4.0,     # i2: 0.5-20.0
    
    # Take Profits (10 levels)
    "tp_count": 4,
    "tp1_percent": 1.05,
    "tp1_amount": 50.0,
    # ... tp2-tp10
    
    # Stop Loss
    "sl_percent": 6.0,
    "sl_trailing_mode": "breakeven",  # fixed/breakeven/cascade
    
    # Position
    "leverage": 1.0,
    "use_commission": false,
    "commission_percent": 0.1,
    "initial_capital": 10000.0,
    
    # Filters
    "use_supertrend": false,
    "use_rsi_filter": false,
    "use_adx_filter": false,
    "use_volume_filter": false,
    
    # Re-entry
    "allow_reentry": true,
    "reentry_after_sl": true,
    "reentry_after_tp": false,
    
    # Adaptive
    "adaptive_mode": null  # null/indicator/tp/all
}
```

## 🧮 Функции расчёта

### Индикаторы

```python
# ATR (Average True Range)
atr = calculate_atr(df, period=14)

# TRG Indicator
df = calculate_trg(df, atr_length=45, multiplier=4.0)
# Добавляет: trg_atr, trg_upper, trg_lower, trg_line, trg_trend

# SuperTrend
df = calculate_supertrend(df, period=10, multiplier=3.0)
# Добавляет: supertrend, st_trend, st_upper, st_lower

# RSI
df = calculate_rsi(df, period=14)
# Добавляет: rsi

# ADX
df = calculate_adx(df, period=14)
# Добавляет: adx, plus_di, minus_di
```

### Сигналы и бэктест

```python
# Генерация сигналов
df = generate_signals(df, settings)
# Добавляет: signal (1=long, -1=short, 0=none)

# Бэктест
trades, equity_curve, tp_stats, monthly_stats, param_changes = run_backtest(df, settings)

# Статистика
stats = calculate_statistics(trades, equity_curve, settings, monthly_stats)
```

## 🚀 Оптимизация

### SSE Streaming

```javascript
const response = await fetch('/api/indicator/auto-optimize-stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        settings: { symbol: 'BTCUSDT', timeframe: '1h' },
        mode: 'indicator',  // indicator/tp/sl/filters/full
        metric: 'combined'  // profit/winrate/sharpe/combined
    })
});

const reader = response.body.getReader();
while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    const text = new TextDecoder().decode(value);
    const data = JSON.parse(text.replace('data: ', ''));
    
    // data.type: 'progress' | 'start' | 'test' | 'complete' | 'error'
    console.log(data);
}
```

### Режимы оптимизации

| Режим | Описание | Комбинаций |
|-------|----------|------------|
| `indicator` | Оптимизация i1/i2 | ~144 |
| `tp` | Оптимизация Take Profits | ~16 |
| `sl` | Оптимизация Stop Loss | ~30 |
| `filters` | Оптимизация фильтров | ~10 |
| `full` | Полная оптимизация | ~270 |

### Heatmap

```python
POST /api/indicator/heatmap
{
    "settings": {...},
    "i1_min": 20,
    "i1_max": 80,
    "i1_step": 5,
    "i2_min": 2.0,
    "i2_max": 8.0,
    "i2_step": 0.5,
    "metric": "profit"
}
```

## 🔧 Параллельная обработка

API использует `ProcessPoolExecutor` для многоядерной оптимизации:

```python
NUM_WORKERS = os.cpu_count() or 4
```

При оптимизации и генерации heatmap задачи распределяются по всем ядрам.

## 📈 Пример использования

### Frontend (React)

```javascript
// Расчёт индикатора
const result = await fetch('/api/indicator/calculate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        symbol: 'BTCUSDT',
        timeframe: '1h',
        trg_atr_length: 45,
        trg_multiplier: 4.0,
        tp_count: 4,
        sl_percent: 6.0
    })
}).then(r => r.json());

// result.candles - свечи для графика
// result.indicators - данные индикаторов
// result.trades - список сделок
// result.stats - статистика
// result.equity_curve - кривая капитала
```

### Python (requests)

```python
import requests

# Расчёт
response = requests.post('http://localhost:8000/api/indicator/calculate', json={
    'symbol': 'BTCUSDT',
    'timeframe': '1h',
    'trg_atr_length': 45,
    'trg_multiplier': 4.0
})
data = response.json()

print(f"Trades: {data['stats']['total_trades']}")
print(f"Win Rate: {data['stats']['win_rate']}%")
print(f"Profit: {data['stats']['total_pnl_pct']}%")
```

## ✅ Тестирование

```batch
test_indicator_api.bat
```

Тесты проверяют:
1. Import API module
2. Pydantic Models
3. Indicator Calculations (ATR, TRG, SuperTrend, RSI, ADX)
4. Signal Generation
5. Backtest Engine
6. Data Helpers
7. Optimization Score
8. API Router endpoints

## 📝 Интеграция с main.py

```python
# main.py
from app.api.indicator import router as indicator_router
app.include_router(indicator_router)
```

---

**Version:** 1.0.0  
**Author:** Komas Team  
**Date:** 2025-12-26
