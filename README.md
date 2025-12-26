# KOMAS Settings & Calendar API v1.0

## New API Modules

### 1. Settings API (`backend/app/api/settings_routes.py`)

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings/api-keys` | Get API keys (masked) |
| POST | `/api/settings/api-keys/{exchange}` | Save API key |
| POST | `/api/settings/api-keys/{exchange}/test` | Test connection |
| GET | `/api/settings/notifications` | Get notification settings |
| POST | `/api/settings/notifications` | Save notification settings |
| POST | `/api/settings/notifications/{type}/test` | Send test notification |
| GET | `/api/settings/system` | Get system settings |
| POST | `/api/settings/system` | Save system settings |
| GET | `/api/settings/system/info` | Get system info (CPU, RAM, etc) |
| POST | `/api/settings/system/clear-cache` | Clear cache |
| GET | `/api/settings/calendar` | Get calendar settings |
| POST | `/api/settings/calendar` | Save calendar settings |

**Features:**
- API key encryption (using cryptography.Fernet)
- Binance/Bybit/OKX support with testnet mode
- Telegram/Discord notifications
- System monitoring (CPU, RAM, disk)

### 2. Calendar API (`backend/app/api/calendar_routes.py`)

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendar/events` | Get economic events |
| GET | `/api/calendar/high-impact-today` | High-impact events today |
| POST | `/api/calendar/refresh` | Force refresh calendar |
| GET | `/api/calendar/block-status` | Check trading block status |
| GET | `/api/calendar/upcoming` | Next N upcoming events |
| GET | `/api/calendar/currencies` | Available currencies |
| GET | `/api/calendar/stats` | Calendar statistics |

**Features:**
- Economic calendar with sample data
- Trading block during high-impact news
- Filtering by impact/currency/time
- Automatic cache refresh

---

## Installation

### Step 1: Extract Archive

Extract to your project root. Files will be placed in:
```
backend/
  app/
    main.py              # UPDATED with new routes
    api/
      settings_routes.py # NEW
      calendar_routes.py # NEW
  requirements.txt       # UPDATED with new dependencies
```

### Step 2: Install Dependencies

```batch
install_settings_deps.bat
```

Or manually:
```batch
pip install cryptography psutil
```

### Step 3: Run Tests

```batch
test_settings_calendar.bat
```

### Step 4: Start Server

```batch
start_backend.bat
```

---

## File Storage

Settings are stored in `data/settings/`:

```
data/
  settings/
    api_keys.json       # Encrypted API keys
    notifications.json  # Telegram/Discord settings
    system.json         # System settings
    calendar.json       # Calendar settings
    .encryption_key     # Fernet encryption key (auto-generated)
  calendar/
    events_cache.json   # Cached calendar events
```

---

## API Examples

### Test Binance Connection

```bash
curl -X POST http://localhost:8000/api/settings/api-keys/binance/test
```

### Get Block Status

```bash
curl http://localhost:8000/api/calendar/block-status
```

### Get High-Impact Events

```bash
curl "http://localhost:8000/api/calendar/events?hours_ahead=24&impact=high"
```

---

## Git Commit Message

```
feat(api): Add Settings and Calendar API modules

- settings_routes.py: API keys, notifications, system settings
- calendar_routes.py: Economic calendar with trading block
- main.py: Updated with new routes, version 3.5.2
- requirements.txt: Added cryptography, psutil
- Encrypted storage for sensitive data
- Binance/Bybit/OKX connection testing
- Telegram/Discord notification testing
- 19 new endpoints total
```
