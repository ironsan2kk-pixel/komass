# Komas TRG Plugin — Indicator Core (#07)

## Обзор

TRG (Trend Range Gate) — пользовательский трендовый индикатор на основе ATR.
Определяет направление тренда и генерирует торговые сигналы при смене тренда.

## Структура

```
plugins/trg/
├── __init__.py          # Экспорты плагина
├── manifest.json        # Метаданные плагина
├── indicator.py         # TRGIndicator (~480 строк)
├── signals.py           # TRGSignalGenerator (~550 строк)
└── tests.py             # Тесты
```

## Использование

### TRG Indicator

```python
from app.indicators.plugins.trg import TRGIndicator

# Создание
indicator = TRGIndicator(atr_length=45, multiplier=4.0)

# Расчёт
result = indicator.calculate(df)

# Результат
print(f"Trend changes: {result.trend_changes}")
print(f"Current trend: {result.last_trend}")  # 1=LONG, -1=SHORT

# DataFrame с колонками:
# - trg_upper: верхняя граница канала
# - trg_lower: нижняя граница канала
# - trg_line: активная линия тренда
# - trg_trend: направление (-1, 0, 1)
# - trg_atr: значение ATR
```

### Signal Generator

```python
from app.indicators.plugins.trg import TRGSignalGenerator, SignalGeneratorConfig

# Без фильтров
generator = TRGSignalGenerator(atr_length=45, multiplier=4.0)
result = generator.generate(df)

# С фильтрами
config = SignalGeneratorConfig(
    atr_length=45,
    multiplier=4.0,
    use_supertrend=True,
    supertrend_period=10,
    supertrend_multiplier=3.0,
    use_rsi_filter=True,
    rsi_period=14,
    rsi_overbought=70,
    rsi_oversold=30,
)
generator = TRGSignalGenerator.from_config(config)
result = generator.generate(df)

# Сигналы
print(f"Total signals: {result.total_signals}")
print(f"Long signals: {result.long_signals}")
print(f"Short signals: {result.short_signals}")
print(f"Filtered out: {result.filtered_signals}")
```

### Backward Compatibility

```python
# Старый API (совместим с indicator_routes.py)
from app.indicators.plugins.trg import calculate_trg, generate_signals

df = calculate_trg(df, atr_length=45, multiplier=4.0)
df = generate_signals(df, atr_length=45, multiplier=4.0,
                      use_supertrend=True, use_rsi_filter=True)
```

## Параметры

### TRG Indicator

| Параметр | Тип | Default | Min | Max | Описание |
|----------|-----|---------|-----|-----|----------|
| atr_length (i1) | int | 45 | 10 | 200 | Период ATR |
| multiplier (i2) | float | 4.0 | 1.0 | 10.0 | Множитель ATR |

### Signal Filters

| Фильтр | Параметры | Описание |
|--------|-----------|----------|
| SuperTrend | period, multiplier | Подтверждение направления тренда |
| RSI | period, overbought, oversold | Фильтр перекупленности/перепроданности |
| ADX | period, threshold | Фильтр силы тренда |
| Volume | ma_period, threshold | Фильтр объёма |

## Логика индикатора

1. **ATR Calculation**: Wilder's smoothing (RMA)
   ```
   TR = max(high - low, |high - prev_close|, |low - prev_close|)
   ATR = RMA(TR, atr_length)
   ```

2. **Channel Bands**:
   ```
   hl2 = (high + low) / 2
   upper = hl2 + (multiplier * atr)
   lower = hl2 - (multiplier * atr)
   ```

3. **Trend Detection**:
   ```
   if close > prev_upper: trend = LONG (1)
   elif close < prev_lower: trend = SHORT (-1)
   else: trend = prev_trend
   ```

4. **TRG Line**:
   ```
   if trend == LONG: line = lower (support)
   else: line = upper (resistance)
   ```

## Логика сигналов

1. **LONG Signal**: Тренд изменился с SHORT на LONG
2. **SHORT Signal**: Тренд изменился с LONG на SHORT
3. **Фильтрация**: Применяются выбранные фильтры

## Тестирование

```batch
test_trg_plugin.bat
```

Или:

```bash
cd backend
python -m app.indicators.plugins.trg.tests
```

## Зависимости

- numpy
- pandas

## Версия

- v1.0.0 — Initial release (2025-12-25)

## Следующие чаты

- **#08** — Trading System (entry/exit)
- **#09** — Take Profit / Stop Loss / Re-entry
- **#10** — Filters (SuperTrend, RSI, ADX, Volume)
