# KOMAS Fix #3 - API Paths

## Проблема:
Frontend использовал неверные пути к API endpoints, что вызывало 404 ошибки:
```
ERR GET /api/indicator/presets - 404
ERR GET /api/data/status - 404
```

## Что исправлено:

### `frontend/src/api.js`

| Было (неверно) | Стало (правильно) |
|----------------|-------------------|
| `/indicator/presets` | `/db/presets` |
| `/indicator/presets/{id}` | `/db/presets/{id}` |
| `/database/*` | `/db/*` |
| `/settings` | `/db/settings` |
| `/data/status` | Удалено (не существует) |
| `/data/info/{s}/{t}` | Удалено (не существует) |

### Добавлены новые API:
- `logsApi` - работа с логами сервера
- `healthApi` - проверка здоровья сервера
- `databaseApi` - кэш и информация БД

### Исправлены SSE endpoints:
- `/signals/stream` → `/signals/sse/stream`
- WebSocket SSE endpoints

---

## Как применить:

1. Замени файл:
   ```
   frontend/src/api.js
   ```

2. Frontend перезагрузится автоматически (hot reload)

3. Проверь — 404 ошибки должны исчезнуть

---

## Git commit:
```
Fix: Correct API paths in frontend api.js

- Change /indicator/presets to /db/presets
- Change /database to /db
- Remove non-existent endpoints
- Add logsApi and healthApi
```
