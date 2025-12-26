# Komas Trading Server - Telegram Notifications

## Chat #17 — Telegram Integration

### 📦 Содержимое

```
komas_telegram/
├── backend/
│   └── app/
│       ├── main.py                    # Обновлённый main с notifications
│       ├── api/
│       │   └── notifications_routes.py # API endpoints (20+)
│       └── core/
│           └── notifications/
│               ├── __init__.py
│               ├── models.py          # Pydantic модели
│               ├── formatters.py      # Simple/Cornix/Custom
│               └── telegram.py        # TelegramNotifier клиент
├── frontend/
│   └── src/
│       ├── pages/
│       │   └── Settings.jsx           # 3 вкладки: Presets/Notifications/API Keys
│       └── services/
│           └── api.js                 # notificationsApi
├── tests/
│   └── test_notifications.py          # 25+ тестов
├── install.bat
├── run_tests.bat
└── README.md
```

### 🚀 Установка

```batch
install.bat
```

### 🔧 Интеграция

#### 1. Скопировать файлы:

```
backend/app/core/notifications/ → komas_indicator/backend/app/core/notifications/
backend/app/api/notifications_routes.py → komas_indicator/backend/app/api/
frontend/src/pages/Settings.jsx → komas_indicator/frontend/src/pages/
frontend/src/services/api.js → komas_indicator/frontend/src/services/
```

#### 2. Обновить main.py:

Добавить в секцию импорта роутеров:

```python
# NEW: Notifications routes
try:
    from app.api.notifications_routes import router as notifications_router
    app.include_router(notifications_router)
    logger.info("✓ Loaded: notifications routes")
except ImportError as e:
    logger.warning(f"✗ Failed to load notifications routes: {e}")
```

### 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications/settings` | Get settings |
| POST | `/api/notifications/settings` | Update settings |
| POST | `/api/notifications/validate-bot` | Validate bot token |
| POST | `/api/notifications/test` | Send test message |
| GET | `/api/notifications/stats` | Get statistics |
| POST | `/api/notifications/send/signal` | Send signal notification |
| POST | `/api/notifications/send/tp-hit` | Send TP hit notification |
| POST | `/api/notifications/send/sl-hit` | Send SL hit notification |
| POST | `/api/notifications/send/closed` | Send closed notification |
| GET | `/api/notifications/formats` | Get available formats |
| GET | `/api/notifications/preview/{format}` | Preview format |
| POST | `/api/notifications/enable` | Enable notifications |
| POST | `/api/notifications/disable` | Disable notifications |

### 💬 Форматы сообщений

#### Simple (по умолчанию):
```
📈 NEW SIGNAL 📈

🟢 LONG BTCUSDT

📍 Entry Zone: 42000.0000 - 42500.0000

🎯 Targets:
  TP1: 43500.0000 (+2.35%) [50%]
  TP2: 44500.0000 (+4.71%) [30%]
  TP3: 46000.0000 (+8.24%) [15%]
  TP4: 48000.0000 (+12.94%) [5%]

🛑 Stop Loss: 41000.0000 (-3.53%)
⚡ Leverage: 10x

📊 TRG | 4h | BINANCE
```

#### Cornix:
```
📈 LONG BTCUSDT

Entry: 42000.0000 - 42500.0000

Targets:
1) 43500.0000
2) 44500.0000
3) 46000.0000
4) 48000.0000

SL: 41000.0000

Leverage: 10x

Exchange: BINANCE
```

### 🤖 Команды бота

| Команда | Описание |
|---------|----------|
| /start | Приветствие, сохранение chat ID |
| /status | Статус системы и статистика |
| /signals | Активные сигналы |
| /stop | Приостановить уведомления |

### ⚙️ Настройки

Доступны через Settings → Notifications:

- **Bot Token** — токен от @BotFather
- **Chat ID** — ID чата/канала (@channel или -1001234567890)
- **Message Format** — Simple / Cornix / Custom
- **Triggers** — какие события отправлять:
  - Новый сигнал
  - TP достигнут
  - SL сработал
  - Сигнал закрыт
  - Ошибки системы
- **Display Options**:
  - Показывать зону входа
  - Показывать плечо
  - Все таргеты / только первые 4
  - Ссылка на график

### 🧪 Тесты

```batch
run_tests.bat
```

Покрытие:
- ✅ Models (5 tests)
- ✅ SimpleFormatter (5 tests)
- ✅ CornixFormatter (2 tests)
- ✅ CustomFormatter (2 tests)
- ✅ FormatterFactory (3 tests)
- ✅ UtilityFormatters (2 tests)
- ✅ TelegramNotifier (6 tests)

### 📝 Git Commit

```
feat(notifications): add Telegram integration

- Add TelegramNotifier client with python-telegram-bot
- Add message formatters (Simple, Cornix, Custom)
- Add notifications API routes (20+ endpoints)
- Add Settings page with Notifications tab
- Add comprehensive test suite (25+ tests)
- Support for signals, TP hits, SL hits, closed signals
- Bot commands: /start, /status, /signals, /stop
```

---

**Version:** 1.0.0  
**Chat:** #17  
**Date:** 2025-12-26
