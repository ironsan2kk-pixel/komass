# Komas Trading Server v3 - Chat #16 Frontend Components

## 📦 Что включено

### Обновлённые страницы:

1. **`pages/Signals.jsx`** - Полная переработка
   - Таблица сигналов с детальными полями
   - Фильтры: symbol, direction, status, поиск
   - Real-time SSE обновления (автообновление при новых сигналах)
   - Пагинация (20 записей на страницу)
   - Экспорт в CSV/JSON
   - Статистика (total, active, win rate, PnL, wins/losses)
   - Закрытие активных сигналов

2. **`pages/Settings.jsx`** - Расширенная версия с 4 вкладками
   - **Пресеты** - управление пресетами настроек (сохранено из оригинала)
   - **API Ключи** - Binance, Bybit, OKX с тестом подключения
   - **Уведомления** - Telegram, Discord с настройками и тестом
   - **Система** - логирование, хранение данных, бэкапы

3. **`pages/Calendar.jsx`** - Исправленная версия
   - Исправлена кодировка кириллицы
   - Добавлена блокировка торговли во время новостей
   - Настройки: минут до/после события, минимальная важность
   - Индикатор статуса блокировки

4. **`App.jsx`** - Обновлённый роутинг
   - Иконки из lucide-react
   - Индикатор активности системы
   - Версия v3.5

5. **`api.js`** - Полный API клиент
   - Все endpoints для Data, Indicator, Signals, Settings
   - SSE поддержка для real-time обновлений
   - Calendar, Trades, Performance, Plugins, WebSocket API
   - Health check endpoints

### Дополнительные файлы:

- **`.gitignore`** - Игнорирует venv/, node_modules/, старые Master Plan
- **`install_frontend.bat`** - Установка frontend зависимостей

## 🔧 Установка

### 1. Скопировать файлы:

```
frontend/src/
├── api.js              → замените существующий
├── App.jsx             → замените существующий
└── pages/
    ├── Signals.jsx     → замените существующий
    ├── Settings.jsx    → замените существующий
    └── Calendar.jsx    → замените существующий
```

### 2. Обновить .gitignore в корне проекта

### 3. Установить зависимости (если не установлены):

```batch
cd frontend
npm install
```

### 4. Запустить:

```batch
npm run dev
```

## 📋 Зависимости (должны быть в package.json)

```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.x",
    "axios": "^1.x",
    "lucide-react": "^0.x",
    "react-hot-toast": "^2.x",
    "react-router-dom": "^6.x"
  }
}
```

## 🔌 API Endpoints (должны быть на backend)

### Signals API:
- `GET /api/signals/` - список с фильтрами
- `GET /api/signals/{id}` - детали
- `POST /api/signals/{id}/close` - закрытие
- `GET /api/signals/stats` - статистика
- `GET /api/signals/symbols` - список символов
- `POST /api/signals/export` - экспорт
- `GET /api/signals/sse/stream` - SSE стрим

### Settings API:
- `GET/POST /api/settings/api-keys` - API ключи
- `POST /api/settings/api-keys/{exchange}/test` - тест подключения
- `GET/POST /api/settings/notifications` - уведомления
- `POST /api/settings/notifications/{type}/test` - тест уведомления
- `GET/POST /api/settings/system` - системные настройки
- `GET /api/settings/system/info` - информация о системе

### Calendar API:
- `GET /api/calendar/events` - события
- `GET /api/calendar/high-impact-today` - важные события
- `POST /api/calendar/refresh` - обновить
- `GET /api/calendar/block-status` - статус блокировки

## ✅ Проверка работы

1. Signals → должны отображаться фильтры, таблица, статистика
2. Settings → 4 вкладки (Пресеты, API Ключи, Уведомления, Система)
3. Calendar → таблица событий + настройки блокировки

## 🐛 Известные ограничения

- SSE для Signals требует соответствующий endpoint на backend
- API ключи хранятся в SQLite (шифрование на стороне backend)
- Экспорт возвращает blob (backend должен отдавать файл)

---

**Git Commit Message:**
```
feat(frontend): Add complete Signals, Settings, Calendar pages

- Signals: Table with filters, SSE real-time, pagination, export, stats
- Settings: Tabs for presets, API keys, notifications, system
- Calendar: Fixed encoding, added trading block during news
- api.js: Complete API client with all endpoints
- App.jsx: Updated routing with icons
- Added .gitignore for venv, node_modules, old plans
```
