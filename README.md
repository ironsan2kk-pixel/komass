# KOMAS Fix #4 - Missing calendarApi Export

## Проблема:
```
Uncaught SyntaxError: The requested module '/src/api.js' 
does not provide an export named 'calendarApi' (at Calendar.jsx:8:10)
```

Calendar.jsx импортирует `calendarApi`, но его не было в api.js.

## Решение:
Добавлен `calendarApi` в api.js:

```javascript
export const calendarApi = {
  getEvents: (params) => api.get('/calendar/events', { params }),
  refresh: () => api.post('/calendar/refresh'),
  getSettings: () => api.get('/calendar/settings'),
  saveSettings: (params) => api.post('/calendar/settings', params),
};
```

## Как применить:

1. Замени файл:
   ```
   frontend/src/api.js
   ```

2. Обнови страницу браузера (F5)

---

## Git commit:
```
Fix: Add missing calendarApi export to api.js

- Add calendarApi with events, refresh, settings endpoints
- Fixes white screen caused by import error in Calendar.jsx
```
