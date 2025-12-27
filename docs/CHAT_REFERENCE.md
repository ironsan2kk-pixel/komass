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

### Chat #20: Dominant — Core ✅
**Коммит:** _pending_

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

**Уроки:** `encoding='utf-8'`, импорты в начале файла

---

### Chat #15: Bugfixes UI ✅
**Коммит:** `df09cee`

| Проблема | Решение |
|----------|---------|
| Monthly белый экран | `data?.results ?? []` |
| StatsPanel ошибки | Null checks |
| TradesTable краш | Optional chaining |
| HeatmapPanel пустой | Empty state handling |

**Файлы:** Все компоненты в `components/Indicator/`

**Уроки:** Всегда `data?.field ?? default`

---

## 🔍 БЫСТРЫЙ ПОИСК

### По теме:
| Тема | Чаты |
|------|------|
| UI/Frontend | #15, #18, #19 |
| Backend | #16, #19, #20 |
| Data/API | #17, #18 |
| Indicators | #20 |
| Caching | #19 |
| Dominant | #20 |

### По файлу:
| Файл | Чаты |
|------|------|
| indicator_routes.py | #16, #18, #19 |
| data_routes.py | #16, #17 |
| Indicator.jsx | #15, #18, #19 |
| SettingsSidebar.jsx | #18, #19 |
| StatsPanel.jsx | #15, #18, #19 |
| dominant.py | #20 |

---

## 📝 СТАНДАРТЫ КОДА

### Python (Backend)
```python
# Encoding для файлов
with open(path, 'w', encoding='utf-8') as f:
    ...

# Imports в начале для ProcessPoolExecutor
import pandas as pd  # Первые строки!

# Валидация параметров
def validate_param(value: int) -> int:
    return max(MIN, min(MAX, int(value)))
```

### JavaScript (Frontend)
```javascript
// Null-safe access
const value = data?.field ?? defaultValue;

// Array check
const items = Array.isArray(data) ? data : [];

// Conditional rendering
{data && data.length > 0 && <Component />}
```

---

*Обновлено: 27.12.2025 (Chat #20)*
