# KOMAS — Справочник по чатам

> **Обновляется после каждого чата**  
> **Последнее обновление:** 27.12.2025

---

## 📊 СВОДКА

| Эра | Чаты | Статус |
|-----|------|--------|
| Эра 1: Плагины | #00-#14 | ✅ Эксперимент (не в prod) |
| Эра 2: Стабилизация | #15-#19 | ✅ ЗАВЕРШЕНА |
| Эра 3: v4.0 | #20-#98 | ⏳ В разработке |

---

## 🎯 ФАЗА 2: DOMINANT INDICATOR (В ПРОЦЕССЕ)

### Chat #21: Dominant — Signals ✅
**Коммит:** _pending_

| Сделано | Описание |
|---------|----------|
| generate_signals() | Основная функция генерации сигналов |
| can_long | close >= mid AND close >= fib_236 AND bullish |
| can_short | close <= mid AND close <= fib_236_high AND bearish |
| is_long_trend | Трекинг лонг тренда |
| is_short_trend | Трекинг шорт тренда |
| Close on reverse | Тренд меняется при обратном сигнале |
| entry_price | Цена входа при сигнале |
| get_signal_summary() | Сводка по сигналам |
| get_latest_signal() | Последний сигнал |
| extract_signal_entries() | Только точки входа |
| Unit tests | 40+ тестов |

**Обновлённые файлы:**
- `backend/app/indicators/dominant.py` (~500 строк, +200 новых)
- `backend/app/indicators/__init__.py` (новые экспорты)
- `tests/test_dominant.py` (~800 строк, +400 новых тестов)
- `run_tests.py` (test runner)
- `test_dominant.bat` (Windows runner)

**Новые API функции:**
```python
generate_signals(df, sensitivity=21, require_confirmation=True) -> DataFrame
get_signal_summary(df) -> Dict[str, Any]
get_latest_signal(df) -> Dict[str, Any]
extract_signal_entries(df) -> DataFrame

# Constants
SIGNAL_LONG = 1
SIGNAL_SHORT = -1
SIGNAL_NONE = 0
```

**Сигнальные колонки:**
```python
'can_long'        # bool
'can_short'       # bool
'signal'          # int: 1, -1, 0
'is_long_trend'   # bool
'is_short_trend'  # bool
'entry_price'     # float
'signal_type'     # str: 'LONG', 'SHORT', 'NONE'
```

---

### Chat #20: Dominant — Core ✅
**Коммит:** `b7d4b12`

| Сделано | Описание |
|---------|----------|
| indicators module | Создан `backend/app/indicators/` |
| dominant.py | Channel + Fibonacci calculation |
| Channel | high_channel, low_channel, mid_channel |
| Fibonacci | 0.236, 0.382, 0.500, 0.618 от low и high |
| Validation | sensitivity 12-60, DataFrame validation |
| Helpers | get_current_levels, get_indicator_info |
| Unit tests | 8 тестов, все проходят |

**Новые файлы:**
- `backend/app/indicators/__init__.py`
- `backend/app/indicators/dominant.py`
- `tests/test_dominant.py`
- `test_dominant.bat`

**API функции:**
```python
calculate_dominant(df, sensitivity=21) -> DataFrame
get_current_levels(df) -> Dict[str, float]
get_indicator_info() -> Dict[str, Any]
validate_sensitivity(value) -> int
```

---

## ✅ ФАЗА 1: СТАБИЛИЗАЦИЯ (ЗАВЕРШЕНА)

### Chat #19: Data Caching ✅
**Коммит:** `11074d0`

| Сделано | Описание |
|---------|----------|
| LRU Cache | 100 записей max, TTL 5 мин |
| Cache endpoints | GET /cache-stats, POST /cache-clear |
| Force Recalculate | Кнопка в UI |
| Cache status | В header и StatsPanel |
| Bug fix | includes undefined error |

**Файлы:** `indicator_routes.py`, `Indicator.jsx`, `SettingsSidebar.jsx`, `StatsPanel.jsx`

---

### Chat #18: Data Period Selection ✅
**Коммит:** `c852b5c`

| Сделано | Описание |
|---------|----------|
| DatePicker | start_date, end_date в sidebar |
| Quick presets | Всё, 1 год, 6 мес, 3 мес, 1 мес |
| data_range | API возвращает диапазон |
| Period display | В header и StatsPanel |

**Файлы:** `indicator_routes.py`, `Indicator.jsx`, `SettingsSidebar.jsx`, `StatsPanel.jsx`

---

### Chat #17: Data Futures Only ✅
**Коммит:** `fba2865`

| Сделано | Описание |
|---------|----------|
| Removed Spot | Удалён BINANCE_SPOT_URL |
| Futures only | Только BINANCE_FUTURES_URL |
| UI update | Убран переключатель источника |

**Файлы:** `data_routes.py`, `Data.jsx`

---

### Chat #16: Bugfixes Backend ✅
**Коммит:** `de6cd90`

| Проблема | Решение |
|----------|---------|
| Duplicate timestamps | Дедупликация данных |
| Mojibake логов | English logs |
| ProcessPoolExecutor | Imports в начале файла |

**Файлы:** `indicator_routes.py`, `data_routes.py`

---

### Chat #15: Bugfixes UI ✅
**Коммит:** `df09cee`

| Проблема | Решение |
|----------|---------|
| MonthlyPanel crash | Null checks, optional chaining |
| StatsPanel crash | Default values, safe access |
| UTF-8 encoding | encoding='utf-8' везде |

**Файлы:** Все компоненты в `components/Indicator/`

---

## 📂 ТЕКУЩАЯ СТРУКТУРА

```
komass/
├── docs/
│   ├── TRACKER.md           # Прогресс
│   └── CHAT_REFERENCE.md    # Этот файл
│
├── backend/app/
│   ├── main.py
│   ├── api/
│   │   ├── indicator_routes.py  # TRG (2000+ строк)
│   │   └── data_routes.py       # Binance Futures
│   └── indicators/              # NEW v4
│       ├── __init__.py
│       └── dominant.py          # ~500 строк
│
├── frontend/src/
│   ├── App.jsx
│   ├── pages/
│   └── components/Indicator/
│
├── tests/
│   └── test_dominant.py         # ~800 строк
│
└── *.bat
```

---

## 🔗 ССЫЛКИ

- **GitHub:** https://github.com/ironsan2kk-pixel/komass
- **API:** http://localhost:8000/docs
- **Frontend:** http://localhost:5173

---

*Обновлено: 27.12.2025*
