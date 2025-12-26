# Komas TRG Filters

> Модуль фильтров для TRG индикатора

## 📋 Обзор

Фильтры используются для улучшения качества сигналов TRG индикатора путём отсеивания ложных входов.

### Доступные фильтры:

| Фильтр | Описание | Логика |
|--------|----------|--------|
| **SuperTrend** | Направление тренда | Long только при UP, Short только при DOWN |
| **RSI** | Перекупленность/перепроданность | Long блокируется при RSI > overbought |
| **ADX** | Сила тренда | Блокирует входы при ADX < threshold (флэт) |
| **Volume** | Объём торгов | Блокирует при низком объёме |

## 🚀 Использование

### Базовый пример

```python
from filters import TRGFilterConfig, TRGFilterManager

# 1. Создаём конфигурацию
config = TRGFilterConfig(
    use_supertrend=True,
    supertrend_period=10,
    supertrend_multiplier=3.0,
    use_rsi=True,
    rsi_period=14,
    rsi_overbought=70,
    rsi_oversold=30,
)

# 2. Создаём менеджер
manager = TRGFilterManager(config)

# 3. Рассчитываем фильтры
df = manager.calculate_all(df)

# 4. Проверяем сигнал
result = manager.check_signal(row, 'long')
if result.allow:
    # Сигнал разрешён
    execute_trade()
else:
    print(f"Blocked by: {result.blocked_by}")
```

### Использование отдельных фильтров

```python
from filters import SuperTrendFilter, RSIFilter

# SuperTrend
st = SuperTrendFilter(period=10, multiplier=3.0)
df = st.calculate(df)
decision = st.check(row, 'long')

# RSI
rsi = RSIFilter(period=14, overbought=70, oversold=30)
df = rsi.calculate(df)
decision = rsi.check(row, 'short')
```

### Оптимизация фильтров

```python
from filters import generate_filter_configs, apply_filter_config

# Генерируем конфигурации для тестирования
configs = generate_filter_configs()
print(f"Всего конфигураций: {len(configs)}")

# Тестируем каждую
for cfg in configs:
    df_test, manager = apply_filter_config(df.copy(), cfg)
    # ... backtest ...
```

## ⚙️ Параметры фильтров

### SuperTrend
| Параметр | Default | Описание |
|----------|---------|----------|
| period | 10 | Период ATR |
| multiplier | 3.0 | Множитель ATR |

### RSI
| Параметр | Default | Описание |
|----------|---------|----------|
| period | 14 | Период RSI |
| overbought | 70 | Уровень перекупленности |
| oversold | 30 | Уровень перепроданности |

### ADX
| Параметр | Default | Описание |
|----------|---------|----------|
| period | 14 | Период ADX |
| threshold | 25 | Минимальный ADX для входа |

### Volume
| Параметр | Default | Описание |
|----------|---------|----------|
| ma_period | 20 | Период MA объёма |
| threshold | 1.5 | Множитель (Volume > MA * threshold) |

## 📊 Пресеты

```python
from filters.config import get_preset, list_presets

# Список пресетов
print(list_presets())
# ['none', 'supertrend_only', 'rsi_only', 'adx_only', 'volume_only',
#  'supertrend_rsi', 'supertrend_adx', 'rsi_adx', 'all', 'conservative', 'aggressive']

# Получить пресет
config = get_preset('conservative')
```

| Пресет | Фильтры |
|--------|---------|
| none | Без фильтров |
| supertrend_only | ST(10,3.0) |
| rsi_only | RSI(14, 70/30) |
| adx_only | ADX(14, 25) |
| volume_only | Vol(20, 1.5x) |
| supertrend_rsi | ST + RSI |
| supertrend_adx | ST + ADX |
| rsi_adx | RSI + ADX |
| all | Все фильтры |
| conservative | ST + ADX(30) + Vol |
| aggressive | ST(7,2) + ADX(20) |

## 📁 Структура файлов

```
filters/
├── __init__.py          # Экспорты
├── config.py            # TRGFilterConfig, пресеты
├── manager.py           # TRGFilterManager
├── supertrend.py        # SuperTrend фильтр
├── rsi.py               # RSI фильтр
├── adx.py               # ADX фильтр
├── volume.py            # Volume фильтр
├── test_filters.py      # Тесты
└── FILTERS_README.md    # Документация
```

## 🧪 Тестирование

```bash
cd backend/app/indicators/plugins/trg/filters
python test_filters.py
```

Или через батник:
```bash
test_trg_filters.bat
```

## 🔧 API Reference

### TRGFilterConfig

```python
@dataclass
class TRGFilterConfig:
    # SuperTrend
    use_supertrend: bool = False
    supertrend_period: int = 10
    supertrend_multiplier: float = 3.0
    
    # RSI
    use_rsi: bool = False
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    
    # ADX
    use_adx: bool = False
    adx_period: int = 14
    adx_threshold: float = 25.0
    
    # Volume
    use_volume: bool = False
    volume_ma_period: int = 20
    volume_threshold: float = 1.5
```

### TRGFilterManager

```python
class TRGFilterManager:
    def __init__(self, config: TRGFilterConfig)
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame
    def check_signal(self, row: pd.Series, signal_type: str) -> FilterCheckResult
    def check_signal_df(self, df: pd.DataFrame, signal_type: str) -> pd.Series
    
    def get_active_filters(self) -> List[str]
    def enable_filter(self, name: str, enabled: bool)
    def disable_all()
    def enable_all()
```

### FilterCheckResult

```python
@dataclass
class FilterCheckResult:
    allow: bool                      # Итоговое решение
    blocked_by: List[str]            # Кто заблокировал
    filter_values: Dict[str, Any]    # Значения фильтров
    reasons: List[str]               # Причины блокировки
```

## 📈 Совместимость

Фильтры совместимы с legacy API из `indicator_routes.py`:

```python
# Legacy функции
from filters.supertrend import calculate_supertrend
from filters.rsi import calculate_rsi
from filters.adx import calculate_adx

df = calculate_supertrend(df, period=10, multiplier=3.0)
df = calculate_rsi(df, period=14)
df = calculate_adx(df, period=14)
```

---

*Версия: 1.0.0 | Чат #09*
