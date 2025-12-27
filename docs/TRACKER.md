# KOMAS v4 — Трекер прогресса

> **Обновляется после каждого чата**  
> **Последнее обновление:** 27.12.2025, Chat #19

---

## 📊 ОБЩИЙ ПРОГРЕСС

```
Версия:     v3.5 → v4.0
Прогресс:   █████░░░░░░░░░░░░░░░ 5/98 чатов (5.1%)
Фаза:       1 — Стабилизация ✅ ЗАВЕРШЕНА
```

---

## ✅ ЗАВЕРШЁННАЯ ФАЗА

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
| **20** | **Dominant: Core** | **⏳ NEXT** | Channel + Fibonacci |
| 21 | Dominant: Signals | ⬜ | can_long, can_short |
| 22 | Dominant: Filters | ⬜ | 5 filter types |
| 23 | Dominant: SL Modes | ⬜ | 5 SL modes |
| 24 | QA Checkpoint #2 | ⬜ | Проверка |
| 25 | Dominant: AI Resolution | ⬜ | Auto-optimize |
| 26 | Dominant: Presets DB | ⬜ | 37 presets |
| 27 | Dominant: UI Integration | ⬜ | Selector |
| 28 | Dominant: Verification | ⬜ | TradingView сверка |

---

## ⏭️ СЛЕДУЮЩИЙ ЧАТ

### Chat #20: Dominant — Core

**Цель:** Создать базовый расчёт индикатора Dominant

**Задачи:**
- [ ] Создать `backend/app/indicators/dominant.py`
- [ ] Расчёт Channel: high_channel, low_channel, mid
- [ ] Расчёт Fibonacci levels: 0.236, 0.382, 0.5, 0.618
- [ ] Параметр `sensitivity` (12-60, default 21)
- [ ] Функция `calculate_dominant(df, sensitivity)`
- [ ] Unit тесты

**Файлы:**
```
backend/app/indicators/
├── __init__.py      # NEW
└── dominant.py      # NEW (~200 строк)
```

**Алгоритм:**
```python
# Channel
high_channel = df['high'].rolling(sensitivity).max()
low_channel = df['low'].rolling(sensitivity).min()
mid = (high_channel + low_channel) / 2
channel_range = high_channel - low_channel

# Fibonacci levels (from low_channel)
fib_236 = low_channel + channel_range * 0.236
fib_382 = low_channel + channel_range * 0.382
fib_500 = low_channel + channel_range * 0.500
fib_618 = low_channel + channel_range * 0.618
```

**Критерии завершения:**
- [ ] dominant.py создан и работает
- [ ] Все уровни рассчитываются корректно
- [ ] Unit тесты проходят
- [ ] ZIP архив готов
- [ ] Git commit написан

---

## 📅 ПЛАН ФАЗ

| Фаза | Чаты | Прогресс |
|------|------|----------|
| 1. Стабилизация | #15-19 | ██████ 100% ✅ |
| 2. Dominant | #20-28 | ░░░░░░ 0% |
| 3. Presets | #29-36 | ░░░░░░ 0% |
| 4. Signal Score | #37-40 | ░░░░░░ 0% |
| 5. Filters | #41-49 | ░░░░░░ 0% |
| 6. Preset Optimizer | #50-54 | ░░░░░░ 0% |
| 7. Bot Config | #55-59 | ░░░░░░ 0% |
| 8. Bot Backtest | #60-66 | ░░░░░░ 0% |
| 9. Bot Optimizer | #67-71 | ░░░░░░ 0% |
| 10. Live Engine | #72-78 | ░░░░░░ 0% |
| 11. Telegram | #79-86 | ░░░░░░ 0% |
| 12. UI Redesign | #87-91 | ░░░░░░ 0% |
| 13. Final QA | #92-95 | ░░░░░░ 0% |
| 14. Release | #96-98 | ░░░░░░ 0% |

**Всего:** 98 чатов (включая 15 QA Checkpoints)

---

## 🐛 ИЗВЕСТНЫЕ БАГИ

| Баг | Статус | Чат |
|-----|--------|-----|
| Duplicate timestamps | ✅ Fixed | #16 |
| Mojibake UI | ✅ Fixed | #15 |
| Mojibake Backend | ✅ Fixed | #16 |
| MonthlyPanel crash | ✅ Fixed | #15 |
| includes undefined | ✅ Fixed | #19 |

---

*Обновлено: 27.12.2025 после Chat #19*
