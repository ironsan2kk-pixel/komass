# KOMAS — Справочник по чатам

> **Обновляется после каждого чата**  
> **Последнее обновление:** 27.12.2025

---

## 📊 СВОДКА

| Эра | Чаты | Статус |
|-----|------|--------|
| Эра 1: Плагины | #00-#14 | ✅ Эксперимент (не в prod) |
| Эра 2: Стабилизация | #15-#17 | ✅ Production v3.5 |
| Эра 3: v4.0 | #18-#98 | ⏳ В разработке |

---

## ✅ ЗАВЕРШЁННЫЕ ЧАТЫ

### Chat #17: Data Futures Only
**Коммит:** TBD

| Сделано | Файлы |
|---------|-------|
| Удалён BINANCE_SPOT_URL | data_routes.py |
| Только Futures | Data.jsx |
| Убран параметр source | — |

---

### Chat #16: Bugfixes Backend
**Коммит:** `de6cd90`

| Проблема | Решение | Файл |
|----------|---------|------|
| Duplicate timestamps | Дедупликация | indicator_routes.py |
| Mojibake логов | English logs | indicator_routes.py |
| ProcessPoolExecutor | Imports top | indicator_routes.py |

**Уроки:** `encoding='utf-8'`, импорты в начале файла

---

### Chat #15: Bugfixes UI
**Коммит:** `df09cee`

| Проблема | Решение | Файл |
|----------|---------|------|
| MonthlyPanel crash | null checks | MonthlyPanel.jsx |
| StatsPanel undefined | default values | StatsPanel.jsx |
| Mojibake | UTF-8 | Все компоненты |

---

## ⏳ ЗАПЛАНИРОВАННЫЕ ЧАТЫ

### Chat #18: Data Period Selection
**Статус:** NEXT

| Задача | Файл |
|--------|------|
| DatePicker UI | SettingsSidebar.jsx |
| start_date, end_date | indicator_routes.py |
| Фильтрация периода | indicator_routes.py |

---

### Chat #19: QA Checkpoint #1
**Тип:** QA

| Проверка |
|----------|
| Backend логи |
| Frontend DevTools |
| Все основные функции |
| Фиксы найденных багов |

---

## 📋 ШАБЛОН QA CHECKPOINT

```markdown
### QA Checkpoint #X

**Дата:** ДД.ММ.ГГГГ

**Логи проверены:**
- [ ] Backend консоль
- [ ] Frontend DevTools Console
- [ ] Network tab — failed requests

**Функции протестированы:**
- [ ] Data: загрузка с Binance
- [ ] Indicator: расчёт TRG
- [ ] Optimizer: 5 режимов
- [ ] Heatmap: генерация
- [ ] Tabs: все 6 открываются

**Найдено:**
| Баг | Severity | Исправлен? |
|-----|----------|------------|
| ... | High/Med/Low | ✅/⬜ |

**Не исправлено (backlog):**
- Issue #1: описание
```

---

## 🔍 ИНДЕКСЫ

### По файлу:

| Файл | Чаты |
|------|------|
| indicator_routes.py | #16, #18 |
| data_routes.py | #16, #17 |
| Indicator.jsx | #15 |
| MonthlyPanel.jsx | #15 |
| StatsPanel.jsx | #15 |
| SettingsSidebar.jsx | #15, #18 |
| Data.jsx | #17 |

### По проблеме:

| Проблема | Чат | Решение |
|----------|-----|---------|
| Белый экран | #15 | null checks |
| Mojibake | #15, #16 | UTF-8 |
| Network Error | #16 | Дедупликация |
| ProcessPoolExecutor | #16 | Imports top |

### По типу:

| Тип | Чаты |
|-----|------|
| Bugfix | #15, #16 |
| Refactor | #17 |
| Feature | #18+ |
| QA Checkpoint | #19, #24, #29... |

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

*Обновляется после каждого чата*
