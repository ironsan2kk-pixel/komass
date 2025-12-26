# KOMAS Fix #2 - Chart Time Format

## Проблема:
```
Uncaught Error: Invalid date string=2025-01-06T15:00:00, expected format=yyyy-mm-dd
```

lightweight-charts требует время в формате **Unix timestamp (секунды)**, а бэкенд возвращает ISO строки.

## Что исправлено:

### `frontend/src/pages/Indicator.jsx`

1. **Добавлена helper функция `toTimestamp()`** - конвертирует любой формат времени в Unix timestamp

2. **Исправлена загрузка свечей** (строка ~276):
   ```js
   time: toTimestamp(c.time)  // было: c.time
   ```

3. **Исправлены маркеры сделок** (entry и exit):
   ```js
   time: toTimestamp(trade.entry_time)  // было: trade.entry_time
   time: toTimestamp(trade.exit_time)   // было: trade.exit_time
   ```

4. **Убрана ошибка 404 для presets** - теперь не показывает ошибку в консоли

---

## Как применить:

1. Замени файл:
   ```
   frontend/src/pages/Indicator.jsx
   ```

2. Перезапусти frontend:
   ```
   npm run dev
   ```

3. Проверь - график должен работать!
