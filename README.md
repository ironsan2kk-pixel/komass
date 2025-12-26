# KOMAS Fix #5 - Complete API Exports

## Проблемы:
1. `Calendar.jsx:8` - не было `calendarApi`
2. `Settings.jsx:9` - не было `symbolsApi`

## Решение:
Добавлены ВСЕ недостающие API экспорты:

### calendarApi
```javascript
export const calendarApi = {
  getEvents: (params) => api.get('/calendar/events', { params }),
  refresh: () => api.post('/calendar/refresh'),
  getSettings: () => api.get('/calendar/settings'),
  saveSettings: (params) => api.post('/calendar/settings', params),
};
```

### symbolsApi
```javascript
export const symbolsApi = {
  getAll: () => api.get('/data/symbols'),
  getFavorites: () => api.get('/data/symbols/favorites'),
  addFavorite: (symbol) => api.post(`/data/symbols/favorites/${symbol}`),
  removeFavorite: (symbol) => api.delete(`/data/symbols/favorites/${symbol}`),
};
```

## Полный список API в api.js:
- ✅ dataApi
- ✅ indicatorApi  
- ✅ presetsApi
- ✅ signalsApi
- ✅ calendarApi (NEW)
- ✅ settingsApi
- ✅ databaseApi
- ✅ pluginsApi
- ✅ wsApi
- ✅ logsApi
- ✅ healthApi
- ✅ symbolsApi (NEW)

## Как применить:

1. Замени файл:
   ```
   frontend/src/api.js
   ```

2. Обнови страницу браузера (F5)

---

## Git commit:
```
Fix: Add missing calendarApi and symbolsApi exports

- Add calendarApi for Calendar.jsx
- Add symbolsApi for Settings.jsx  
- Fixes white screen caused by missing exports
```
