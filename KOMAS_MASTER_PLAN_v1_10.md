# KOMAS TRADING SYSTEM — MASTER PLAN
> Версия: 1.10 | Дата: 2025-12-25 | Статус: В разработке

---

## 📊 ПРОГРЕСС

```
Общий прогресс: █████████░ 45%

Чат #00 - Планирование:  ██████████ 100% ✅
Чат #01 - Logger/Config: ██████████ 100% ✅
Чат #02 - Database:      ██████████ 100% ✅
Чат #03 - Data Manager:  ██████████ 100% ✅
Чат #04 - WebSocket:     ██████████ 100% ✅
Чат #05 - Base Classes:  ██████████ 100% ✅
Чат #06 - PluginLoader:  ██████████ 100% ✅
Чат #07 - TRG Core:      ██████████ 100% ✅ ← DONE

Этап 1  - Core:        ██████████ 100% ✅ [#01 ✅, #02 ✅]
Этап 2  - Data:        ██████████ 100% ✅ [#03 ✅, #04 ✅]
Этап 3  - Indicators:  ██████████ 100% ✅ [#05 ✅, #06 ✅]
Этап 4  - TRG Plugin:  ██░░░░░░░░ 20%    [#07 ✅, #08-#13] ← IN PROGRESS
Этап 5  - API:         ████░░░░░░ 40%    [#14]
Этап 6  - Frontend:    ██░░░░░░░░ 20%    [#15-#17]
Этап 7  - Presets:     ░░░░░░░░░░ 0%     [#18-#19]
Этап 8  - Bots:        ░░░░░░░░░░ 0%     [#20-#22]
Этап 9  - Telegram:    ░░░░░░░░░░ 0%     [#23]
Этап 10 - Analytics:   ░░░░░░░░░░ 0%     [#24]
```

---

## 📦 МОДУЛИ И СТАТУСЫ

### TRG PLUGIN — ЭТАП 4 (В РАБОТЕ)

| Модуль | Файл | Статус | Чат |
|--------|------|--------|-----|
| manifest.json | `plugins/trg/manifest.json` | 🟢 Готово | #06 ✅ |
| **Indicator Core** | `plugins/trg/indicator.py` | 🟢 Готово | **#07 ✅** |
| **Signals** | `plugins/trg/signals.py` | 🟢 Готово | **#07 ✅** |
| Trading System | `plugins/trg/trading.py` | 🔴 TODO | #08 |
| Entry/Exit | `plugins/trg/entry_exit.py` | 🔴 TODO | #08 |
| Take Profit | `plugins/trg/take_profit.py` | 🔴 TODO | #09 |
| Stop Loss | `plugins/trg/stop_loss.py` | 🔴 TODO | #09 |
| Re-entry | `plugins/trg/reentry.py` | 🔴 TODO | #09 |
| Filter: SuperTrend | `plugins/trg/filters/supertrend.py` | 🔴 TODO | #10 |
| Filter: RSI | `plugins/trg/filters/rsi.py` | 🔴 TODO | #10 |
| Filter: ADX | `plugins/trg/filters/adx.py` | 🔴 TODO | #10 |
| Filter: Volume | `plugins/trg/filters/volume.py` | 🔴 TODO | #10 |
| Optimizer Engine | `plugins/trg/optimizer.py` | 🔴 TODO | #11 |
| Heatmap | `plugins/trg/heatmap.py` | 🔴 TODO | #11 |
| Backtest Engine | `plugins/trg/backtest.py` | 🔴 TODO | #12 |
| Metrics | `plugins/trg/metrics.py` | 🔴 TODO | #12 |
| UI Schema | `plugins/trg/ui_schema.py` | 🔴 TODO | #13 |

---

## 📜 ИСТОРИЯ ДЕЙСТВИЙ

### Чат #07 — TRG: Indicator Core (2025-12-25) ✅

**Что сделали:**

1. ✅ Создали `plugins/trg/indicator.py` (~480 строк)
   - TRGIndicator — главный класс индикатора
   - TRGParameters — параметры с валидацией
   - TRGResult — результат расчёта
   - TrendDirection — enum направления тренда
   - calculate_trg() — функция совместимости со старым API
   - calculate_incremental() — инкрементальный расчёт для real-time

2. ✅ Создали `plugins/trg/signals.py` (~550 строк)
   - TRGSignalGenerator — генератор сигналов
   - SignalGeneratorConfig — конфигурация с фильтрами
   - Signal — dataclass сигнала
   - SignalResult — результат генерации
   - Встроенные фильтры: SuperTrend, RSI, ADX, Volume
   - generate_signals() — функция совместимости

3. ✅ Создали `plugins/trg/__init__.py`
   - Экспорты всех классов
   - get_plugin_info() для registry
   - get_indicator() / get_signal_generator() entry points

4. ✅ Обновили `plugins/trg/manifest.json`
   - Полная спецификация плагина
   - Параметры i1/i2
   - Конфигурация UI
   - Entry points

5. ✅ Создали `plugins/trg/tests.py` — тесты

6. ✅ Создали `test_trg_plugin.bat` — батник для тестирования

**Ключевые решения:**
- Backward compatibility со старым indicator_routes.py
- Incremental calculation для WebSocket real-time
- Встроенные фильтры в SignalGenerator (не отдельные файлы)
- Dataclasses для типизации результатов

**Тесты прошли:**
```
✓ TRGIndicator: create, calculate, validate
✓ TRGSignalGenerator: signals, filters
✓ Backward compatibility: calculate_trg, generate_signals
✓ Incremental: real-time updates
```

**Артефакт:** `komas_trg_v1.zip`

---

### Следующий чат:
- **#08** — TRG: Trading System (entry, exit, position management)

---

## 📝 ЗАМЕТКИ

### Структура TRG плагина после #07:

```
plugins/trg/
├── __init__.py          # Экспорты, entry points
├── manifest.json        # Метаданные плагина
├── indicator.py         # ✅ TRGIndicator (~480 строк)
├── signals.py           # ✅ TRGSignalGenerator (~550 строк)
├── tests.py             # ✅ Тесты
│
├── trading.py           # TODO #08
├── entry_exit.py        # TODO #08
├── take_profit.py       # TODO #09
├── stop_loss.py         # TODO #09
├── reentry.py           # TODO #09
├── filters/             # TODO #10
├── optimizer.py         # TODO #11
├── heatmap.py           # TODO #11
├── backtest.py          # TODO #12
├── metrics.py           # TODO #12
└── ui_schema.py         # TODO #13
```

### API для TRG:

```python
# Indicator
from plugins.trg import TRGIndicator
indicator = TRGIndicator(atr_length=45, multiplier=4.0)
result = indicator.calculate(df)

# Signals
from plugins.trg import TRGSignalGenerator
generator = TRGSignalGenerator(atr_length=45, multiplier=4.0)
signals = generator.generate(df)

# Backward compatible
from plugins.trg import calculate_trg, generate_signals
df = calculate_trg(df, 45, 4.0)
df = generate_signals(df, 45, 4.0)
```

---

## 🔄 ИСТОРИЯ ИЗМЕНЕНИЙ ДОКУМЕНТА

| Версия | Дата | Изменения |
|--------|------|-----------|
| 1.10 | 2025-12-25 | **Чат #07 завершён**, TRG Indicator Core готов |
| 1.9 | 2025-12-25 | Чат #06 завершён, Этап 3 (Indicators) ЗАВЕРШЁН |
| 1.8 | 2025-12-25 | Чат #05 завершён, базовые классы готовы |
| 1.7 | 2025-12-25 | Чат #04 завершён, Этап 2 (Data) ЗАВЕРШЁН |
| 1.6 | 2025-12-25 | Чат #03 завершён |
| 1.5 | 2025-12-25 | Чат #02 завершён, Этап 1 готов |
| 1.4 | 2025-12-25 | Чат #01 завершён |

---

*Документ обновляется после каждого завершённого чата*
