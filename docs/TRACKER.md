# KOMAS v4 — Трекер прогресса

> **Обновляется после каждого чата**  
> **Последнее обновление:** 27.12.2025, Chat #21

---

## 📊 ОБЩИЙ ПРОГРЕСС

```
Версия:     v3.5 → v4.0
Прогресс:   ███████░░░░░░░░░░░░░ 7/98 чатов (7.1%)
Фаза:       2 — Dominant Indicator (2/9)
```

---

## ✅ ЗАВЕРШЁННЫЕ ФАЗЫ

### Фаза 1: Стабилизация (#15-#19) — COMPLETE ✅

| # | Чат | Статус | Коммит |
|---|-----|--------|--------|
| 15 | Bugfixes UI | ✅ | `df09cee` |
| 16 | Bugfixes Backend | ✅ | `de6cd90` |
| 17 | Data Futures Only | ✅ | `fba2865` |
| 18 | Data Period Selection | ✅ | `c852b5c` |
| 19 | Data Caching | ✅ | `11074d0` |

**Результаты Фазы 1:**
- ✅ UI стабилен (null checks, UTF-8)
- ✅ Backend без ошибок (timestamps, imports)
- ✅ Только Binance Futures
- ✅ Выбор периода дат для бэктеста
- ✅ LRU кэш с TTL 5 мин

---

## 🎯 ТЕКУЩАЯ ФАЗА

### Фаза 2: Dominant Indicator (#20-#28) — 9 чатов

| # | Чат | Статус | Описание |
|---|-----|--------|----------|
| 20 | Dominant: Core | ✅ | Channel + Fibonacci |
| 21 | Dominant: Signals | ✅ | can_long, can_short, trend tracking |
| **22** | **Dominant: Filters** | **⏳ NEXT** | 5 filter types |
| 23 | Dominant: SL Modes | ⬜ | 5 SL modes |
| 24 | QA Checkpoint #2 | ⬜ | Проверка |
| 25 | Dominant: AI Resolution | ⬜ | Auto-optimize |
| 26 | Dominant: Presets DB | ⬜ | 37 presets |
| 27 | Dominant: UI Integration | ⬜ | Selector |
| 28 | Dominant: Verification | ⬜ | TradingView сверка |

---

## ✅ ЗАВЕРШЁННЫЙ ЧАТ #21

### Chat #21: Dominant — Signals ✅

**Цель:** Добавить генерацию торговых сигналов

**Выполнено:**
- [x] Функция `generate_signals(df, sensitivity, require_confirmation)`
- [x] Условие `can_long`: close >= mid_channel AND close >= fib_236 AND bullish candle
- [x] Условие `can_short`: close <= mid_channel AND close <= fib_236_high AND bearish candle
- [x] Трекинг тренда: `is_long_trend`, `is_short_trend`
- [x] Close on reverse signal (trend flip)
- [x] Entry price calculation
- [x] Signal columns: signal, signal_type
- [x] Helper functions: get_signal_summary, get_latest_signal, extract_signal_entries
- [x] Mutual exclusion: can_long and can_short never both True
- [x] Trend exclusion: is_long_trend and is_short_trend never both True
- [x] Unit тесты (40+ тестов)
- [x] ZIP архив готов

**Добавленные колонки:**
```python
'can_long'        # bool - Long entry signal fires
'can_short'       # bool - Short entry signal fires
'signal'          # int - 1=Long, -1=Short, 0=None
'is_long_trend'   # bool - Currently in long trend
'is_short_trend'  # bool - Currently in short trend
'entry_price'     # float - Entry price when signal fires
'signal_type'     # str - 'LONG', 'SHORT', 'NONE'
```

**Логика сигналов:**
```python
# Long signal
can_long = (
    (close >= mid_channel) &     # Upper half of channel
    (close >= fib_236) &         # Above first support
    (close > open)               # Bullish candle (if confirmation required)
)

# Short signal
can_short = (
    (close <= mid_channel) &     # Lower half of channel
    (close <= fib_236_high) &    # Below first resistance from high
    (close < open)               # Bearish candle (if confirmation required)
)

# Trend tracking with close on reverse
# Long fires → is_long_trend=True, is_short_trend=False
# Short fires → is_short_trend=True, is_long_trend=False
```

**Новые API функции:**
```python
generate_signals(df, sensitivity=21, require_confirmation=True) -> DataFrame
get_signal_summary(df) -> Dict
get_latest_signal(df) -> Dict
extract_signal_entries(df) -> DataFrame
```

**Constants:**
```python
SIGNAL_LONG = 1
SIGNAL_SHORT = -1
SIGNAL_NONE = 0
```

---

## ⏭️ СЛЕДУЮЩИЙ ЧАТ

### Chat #22: Dominant — Filters

**Цель:** Добавить 5 типов фильтров для сигналов

**Задачи:**
- [ ] Filter Type 0: None (без фильтров)
- [ ] Filter Type 1: ATR Condition (volume spike)
- [ ] Filter Type 2: RSI Condition (overbought/oversold)
- [ ] Filter Type 3: ATR + RSI Combined
- [ ] Filter Type 4: Volatility Condition
- [ ] Функция `apply_filter(df, filter_type, params)`
- [ ] Интеграция с generate_signals
- [ ] Unit тесты

**Логика фильтров:**
```python
# Filter Type 1: ATR Condition
atr = df['high'] - df['low']
atr_ma = atr.rolling(14).mean()
filter_pass = atr > atr_ma * 1.5  # Volume spike

# Filter Type 2: RSI Condition
rsi_14 = calculate_rsi(df['close'], 14)
long_filter = rsi_14 < 70  # Not overbought
short_filter = rsi_14 > 30  # Not oversold

# Filter Type 3: Combined
pass_filter = atr_condition & rsi_condition

# Filter Type 4: Volatility
volatility = df['close'].pct_change().rolling(20).std()
filter_pass = volatility < threshold
```

---

## 📈 СТАТИСТИКА

| Метрика | Значение |
|---------|----------|
| Чатов завершено | 7 |
| Чатов осталось | 91 |
| Фаз завершено | 1 |
| Фаз всего | 14 |
| QA checkpoints | 0/15 |

---

## 🔗 ССЫЛКИ

- **GitHub:** https://github.com/ironsan2kk-pixel/komass
- **Документация:** /docs
- **API:** http://localhost:8000/docs

---

*Обновлено: 27.12.2025*
