# Komas Trading System — Indicators Base Classes

## Обзор

Модуль `indicators` предоставляет базовые классы для системы плагинов индикаторов.

### Архитектура

```
indicators/
├── __init__.py           # Главные экспорты
└── base/
    ├── __init__.py       # Экспорты базовых классов
    ├── indicator.py      # BaseIndicator — расчёт индикаторов
    ├── trading.py        # BaseTradingSystem — управление позициями
    ├── filter.py         # BaseFilter — фильтры сигналов
    ├── optimizer.py      # BaseOptimizer — оптимизация параметров
    └── backtest.py       # BaseBacktest — бэктестинг
```

---

## 📊 BaseIndicator

Абстрактный класс для всех торговых индикаторов.

### Обязательные методы

```python
from app.indicators import BaseIndicator, IndicatorParameter

class MyIndicator(BaseIndicator):
    def get_id(self) -> str:
        return "my_indicator"
    
    def get_name(self) -> str:
        return "My Custom Indicator"
    
    def get_parameters(self) -> List[IndicatorParameter]:
        return [
            IndicatorParameter("period", "Period", "int", 14, 1, 200, 1),
            IndicatorParameter("multiplier", "Multiplier", "float", 2.0, 0.1, 10.0, 0.1),
        ]
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        # Расчёт индикатора
        period = self.get_param("period")
        df['my_value'] = df['close'].rolling(period).mean()
        return df
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        # Генерация сигналов
        df['signal'] = 0
        df.loc[df['close'] > df['my_value'], 'signal'] = 1
        df.loc[df['close'] < df['my_value'], 'signal'] = -1
        return df
```

### Использование

```python
indicator = MyIndicator({"period": 20, "multiplier": 3.0})
result = indicator.run(df)

print(result.signals)  # Series с сигналами
print(result.values)   # Dict с рассчитанными значениями
```

---

## 💼 BaseTradingSystem

Управление позициями, TP/SL, trailing.

### Конфигурация

```python
from app.indicators import TradingConfig, TrailingMode

config = TradingConfig(
    tp_count=4,
    tp_percents=[1.0, 2.0, 3.5, 5.0],
    tp_amounts=[50, 30, 15, 5],
    sl_percent=5.0,
    sl_trailing_mode=TrailingMode.BREAKEVEN,
    leverage=10.0,
    use_commission=True,
    commission_percent=0.04,
    initial_capital=10000.0
)
```

### Trailing Modes

- `FIXED` — SL не двигается
- `BREAKEVEN` — После TP1 SL = Entry Price
- `CASCADE` — После каждого TP SL = предыдущий TP
- `MOVING` — Трейлинг по цене

---

## 🔍 BaseFilter

Фильтры для сигналов входа.

### Готовые фильтры

```python
from app.indicators import SuperTrendFilter, RSIFilter, ADXFilter, VolumeFilter, FilterChain

# Создание фильтров
st_filter = SuperTrendFilter({"period": 10, "multiplier": 3.0})
rsi_filter = RSIFilter({"period": 14, "overbought": 70, "oversold": 30})
adx_filter = ADXFilter({"period": 14, "threshold": 25})

# Цепочка фильтров
chain = FilterChain([st_filter, rsi_filter, adx_filter])

# Применение
df = chain.calculate_all(df)
filtered_signals = chain.filter_all_signals(df)
```

### Создание своего фильтра

```python
from app.indicators import BaseFilter, FilterResult, FilterOutput

class MyFilter(BaseFilter):
    def get_id(self) -> str:
        return "my_filter"
    
    def get_name(self) -> str:
        return "My Custom Filter"
    
    def get_parameters(self) -> List[IndicatorParameter]:
        return [
            IndicatorParameter("threshold", "Threshold", "float", 0.5, 0, 1, 0.1),
        ]
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        # Расчёт значений фильтра
        return df
    
    def check(self, df: pd.DataFrame, index: int, signal: int) -> FilterOutput:
        # Проверка сигнала
        if some_condition:
            return FilterOutput(FilterResult.ALLOW, "Условие выполнено")
        return FilterOutput(FilterResult.BLOCK, "Условие не выполнено")
```

---

## ⚡ BaseOptimizer

Оптимизация параметров с поддержкой параллельности.

### Режимы оптимизации

- `INDICATOR` — только параметры индикатора (i1, i2)
- `TP` — только Take Profit уровни
- `SL` — только Stop Loss
- `FILTERS` — параметры фильтров
- `FULL` — все параметры
- `ADAPTIVE` — walk-forward оптимизация

### Методы поиска

- `GRID` — полный перебор
- `RANDOM` — случайная выборка
- `BAYESIAN` — байесовская оптимизация (planned)

### Использование

```python
from app.indicators import (
    BaseOptimizer, OptimizationConfig, OptimizationMode,
    OptimizationMetric, ParameterRange
)

class MyOptimizer(BaseOptimizer):
    def get_parameter_ranges(self, mode: OptimizationMode) -> List[ParameterRange]:
        return [
            ParameterRange("i1", 20, 100, 5, "int"),
            ParameterRange("i2", 1.0, 10.0, 0.5, "float"),
        ]
    
    def run_single_test(self, params, df):
        # Запуск бэктеста
        return trades, equity
    
    def calculate_score(self, trades, equity, metric):
        # Расчёт скора
        return score, metrics

# Оптимизация
optimizer = MyOptimizer(OptimizationConfig(
    mode=OptimizationMode.INDICATOR,
    metric=OptimizationMetric.ADVANCED,
    parallel_workers=0  # Auto (все ядра)
))

best = optimizer.optimize(df)
print(f"Best params: {best.params}")
print(f"Score: {best.score}")
```

### SSE Streaming

```python
# Для real-time progress
for event in optimizer.optimize_stream(df):
    yield f"data: {json.dumps(event)}\n\n"
```

---

## 📈 BaseBacktest

Движок бэктестинга.

### Использование

```python
from app.indicators import BaseBacktest, BacktestConfig, TradingConfig

class MyBacktest(BaseBacktest):
    def create_indicator(self, params):
        return MyIndicator(params)
    
    def create_trading_system(self, config):
        return SimpleTradingSystem(config)
    
    def create_filters(self, params):
        return FilterChain([
            SuperTrendFilter(params),
            RSIFilter(params)
        ])

# Запуск
backtest = MyBacktest(BacktestConfig(
    initial_capital=10000,
    calculate_monthly=True
))

result = backtest.run(
    df,
    indicator_params={"i1": 45, "i2": 4.0},
    filter_params={"period": 10}
)

print(result.stats)
print(result.trades)
```

---

## 📦 Структура Position

```python
@dataclass
class Position:
    id: int
    type: PositionType           # LONG / SHORT
    entry_time: datetime
    entry_price: float
    entry_capital: float
    
    tp_levels: List[TakeProfitLevel]
    sl_percent: float
    sl_price: float
    sl_trailing_mode: TrailingMode
    
    status: PositionStatus       # OPEN / CLOSED / PARTIAL
    remaining_percent: float     # Оставшаяся часть позиции
    realized_pnl: float          # Реализованная прибыль
    
    highest_price: float         # Для trailing
    lowest_price: float
    
    leverage: float
    commission_paid: float
```

---

## 📊 Метрики

### calculate_advanced_score()

Комплексная оценка результатов:

- **Profit %** (30%) — общая прибыль
- **Win Rate** (15%) — процент выигрышных сделок
- **Profit Factor** (15%) — отношение прибыли к убыткам
- **TP1 Hit Rate** (10%) — важно для BE стратегии
- **Sharpe Ratio** (10%) — риск-adjusted return
- **Consistency** (10%) — стабильность результатов
- **Max Drawdown** (10%) — штраф за просадку

---

## 🔧 Хелперы

```python
from app.indicators import calculate_atr, calculate_ema, crossover, crossunder

# ATR (Wilder's smoothing)
atr = calculate_atr(df, period=14)

# EMA
ema = calculate_ema(df['close'], period=20)

# Пересечения
cross_up = crossover(fast_ma, slow_ma)
cross_down = crossunder(fast_ma, slow_ma)
```

---

## 📁 Файлы

| Файл | Строк | Описание |
|------|-------|----------|
| `indicator.py` | ~380 | BaseIndicator + хелперы |
| `trading.py` | ~500 | BaseTradingSystem + Position |
| `filter.py` | ~480 | BaseFilter + готовые фильтры |
| `optimizer.py` | ~520 | BaseOptimizer + streaming |
| `backtest.py` | ~450 | BaseBacktest + результаты |

---

## Следующий шаг

**Чат #06** — Plugin Loader и Registry:
- `indicators/loader.py` — загрузка плагинов
- `indicators/registry.py` — регистрация индикаторов

---

*Komas Trading System v3 — Indicators Base Classes*
