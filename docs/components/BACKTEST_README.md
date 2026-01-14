# TRG Backtest Engine

Полный движок бэктестинга для TRG индикатора.

## Версия: 1.0.0

## Возможности

### Основной бэктест
- Полная симуляция торговли с equity curve
- 10 уровней Take Profit с partial closes
- 3 режима Stop Loss: fixed, breakeven, cascade
- Re-entry после SL/TP
- Leverage до 125x с расчётом комиссий
- Monthly статистика
- TP/SL tracking per trade

### Адаптивная оптимизация
- Режимы: indicator, tp, all
- Переоптимизация каждые N сделок
- Lookback период для обучения

### Quick backtest (для оптимизатора)
- Упрощённая симуляция
- Быстрый расчёт score
- Параллельно-безопасное выполнение

### UI хелперы
- prepare_candles() - данные для графика
- prepare_indicators() - TRG линии
- prepare_trade_markers() - маркеры входов/выходов
- get_current_signal() - текущий сигнал

## Компоненты

### BacktestConfig
```python
config = BacktestConfig()
config.symbol = "BTCUSDT"
config.timeframe = "1h"
config.trg_atr_length = 45
config.trg_multiplier = 4.0
config.tp_count = 4
config.sl_percent = 6.0
config.sl_trailing_mode = "breakeven"
config.leverage = 10.0
config.use_commission = True
```

### TRGBacktest
```python
from backtest import TRGBacktest, BacktestConfig

# Создание
config = BacktestConfig()
backtest = TRGBacktest(config)

# Запуск
result = backtest.run(df)

# Результаты
print(f"Trades: {result.total_trades}")
print(f"Win Rate: {result.win_rate}%")
print(f"Profit: {result.profit_pct}%")
print(f"Max DD: {result.max_drawdown}%")
```

### BacktestResult
```python
result = backtest.run(df)

# Статистика
result.total_trades      # Всего сделок
result.winning_trades    # Выигрышных
result.losing_trades     # Проигрышных
result.win_rate          # Win Rate %
result.profit_pct        # Прибыль %
result.max_drawdown      # Макс просадка %
result.profit_factor     # Profit Factor
result.sharpe_ratio      # Sharpe Ratio

# Данные
result.trades            # Список сделок
result.equity_curve      # Equity curve
result.monthly_stats     # По месяцам
result.accuracy          # Точность по TP
```

## Структура файлов

```
plugins/trg/
├── backtest.py      # 🆕 Движок бэктеста (~1000 строк)
├── indicator.py     # TRG индикатор
├── signals.py       # Генератор сигналов
├── trading.py       # Торговая система
├── filters/         # Фильтры
├── optimizer.py     # Оптимизатор
├── manifest.json    # v1.4.0
└── __init__.py      # Экспорты
```

## API для фронтенда

### Полный бэктест
```python
@router.post("/api/plugins/trg/backtest")
async def run_backtest(settings: dict):
    config = BacktestConfig.from_dict(settings)
    backtest = TRGBacktest(config)
    result = backtest.run(df)
    
    return {
        "success": True,
        "candles": prepare_candles(df),
        "indicators": prepare_indicators(df, config),
        "trades": result.trades,
        "trade_markers": prepare_trade_markers(result.trades),
        "equity_curve": result.equity_curve,
        "stats": result.to_dict(),
        "monthly": {k: v.to_dict() for k, v in result.monthly_stats.items()},
    }
```

### Параллельный бэктест
```python
from backtest import run_parallel_backtest

params = {
    'df': df,
    'config': config.to_dict(),
    'metric': 'advanced'
}

result = run_parallel_backtest(params)
# {"score": 45.2, "profit": 15.5, "win_rate": 55.3, "trades": 42}
```

## Тесты

23 теста покрывают:
- BacktestConfig создание и сериализация
- MonthlyStats и TPStats
- Расчёт индикаторов (ATR, TRG, SuperTrend, RSI, ADX)
- Генерация сигналов с фильтрами
- Основной бэктест
- Бэктест с фильтрами
- Leverage и комиссии
- Re-entry
- Trailing SL (все 3 режима)
- Quick backtest
- UI хелперы
- Параллельный бэктест
- Расчёт score

Запуск:
```batch
test_backtest.bat
```

## Changelog

### v1.4.0 (2025-12-25)
- TRGBacktest engine
- BacktestConfig с полной конфигурацией
- BacktestResult с детальной статистикой
- UI хелперы для графиков
- Parallel backtest для оптимизатора
- 23 теста
