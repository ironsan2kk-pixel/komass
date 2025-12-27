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
| MonthlyPanel crash | null checks |
| StatsPanel undefined | default values |
| Mojibake | UTF-8 encoding |

**Файлы:** `Indicator.jsx`, `MonthlyPanel.jsx`, `StatsPanel.jsx`, и др.

---

## ⏳ ФАЗА 2: DOMINANT INDICATOR

### Chat #20: Dominant — Core
**Статус:** NEXT

| Задача | Файл |
|--------|------|
| Channel calculation | dominant.py |
| Fibonacci levels | dominant.py |
| sensitivity param | dominant.py |
| Unit tests | test_dominant.py |

---

### Chat #21: Dominant — Signals
**Статус:** ⬜

| Задача |
|--------|
| can_long conditions |
| can_short conditions |
| Close on reverse |

---

### Chat #22: Dominant — Filters
**Статус:** ⬜

| Filter Type | Description |
|-------------|-------------|
| 0 | None |
| 1 | ATR Condition |
| 2 | RSI |
| 3 | ATR + RSI |
| 4 | Volatility |

---

### Chat #23: Dominant — SL Modes
**Статус:** ⬜

| Mode | Description |
|------|-------------|
| 0 | No SL movement |
| 1 | After TP1 → Entry |
| 2 | After TP2 → Entry |
| 3 | After TP3 → Entry |
| 4 | Cascade trailing |

---

### Chat #24: QA Checkpoint #2
**Статус:** ⬜

| Проверка |
|----------|
| Backend логи |
| Frontend DevTools |
| Dominant расчёты |
| TRG не сломан |

---

## 🔍 ИНДЕКСЫ

### По файлу:

| Файл | Чаты |
|------|------|
| indicator_routes.py | #16, #18, #19 |
| data_routes.py | #16, #17 |
| Indicator.jsx | #15, #18, #19 |
| SettingsSidebar.jsx | #15, #18, #19 |
| StatsPanel.jsx | #15, #18, #19 |
| MonthlyPanel.jsx | #15 |
| Data.jsx | #17 |
| dominant.py | #20 (planned) |

### По проблеме:

| Проблема | Чат | Решение |
|----------|-----|---------|
| Белый экран | #15 | null checks |
| Mojibake | #15, #16 | UTF-8 |
| Network Error | #16 | Дедупликация |
| ProcessPoolExecutor | #16 | Imports top |
| includes undefined | #19 | null check |

### По типу:

| Тип | Чаты |
|-----|------|
| Bugfix | #15, #16, #19 |
| Refactor | #17 |
| Feature | #18, #19 |
| New Indicator | #20-#28 |
| QA Checkpoint | #24, #29... |

---

## 📦 ЭРА 1: ПЛАГИНЫ (#00-#14)

> ⚠️ **Экспериментальный код — НЕ в production**

| # | Чат | Создано |
|---|-----|---------|
| 00 | Планирование | Master Plan |
| 01 | Core: Logger | config.py, logger.py |
| 02 | Core: Database | database.py, models.py |
| 03 | Data: Manager | binance.py, storage.py |
| 04 | Data: WebSocket | websocket.py |
| 05 | Indicators: Base | 5 классов (~2300 строк) |
| 06 | PluginLoader | registry.py, loader.py |
| 07 | TRG: Core | indicator.py, signals.py |
| 08 | TRG: Trading | trading.py |
| 09 | TRG: Filters | 4 фильтра |
| 10 | TRG: Optimizer | optimizer.py |
| 11 | TRG: Backtest | backtest.py |
| 12 | TRG: UI Schema | ui_schema.py |
| 13 | API: Indicator | indicator.py |
| 14 | Frontend | App, Data, Settings |

**Расположение:** `backend/app/core/`, `backend/app/indicators/`, `backend/app/plugins/`

**Статус:** Не трогать, может пригодиться позже

---

*Обновлено: 27.12.2025 после Chat #19*
