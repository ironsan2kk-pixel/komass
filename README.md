# KOMAS Settings API v1.0

## Settings API (`backend/app/api/settings_routes.py`)

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

**Features:**
- API key encryption (using cryptography.Fernet)
- Binance/Bybit/OKX support with testnet mode
- Telegram/Discord notifications
- System monitoring (CPU, RAM, disk)

---

## Installation

### Step 1: Extract Archive

Extract to your project root. Files will be placed in:
```
backend/
  app/
    main.py              # UPDATED with settings route
    api/
      settings_routes.py # NEW
  requirements.txt       # UPDATED with new dependencies
```

### Step 2: Install Dependencies

```batch
install_settings_deps.bat
```

### Step 3: Run Tests

```batch
test_settings.bat
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
    .encryption_key     # Fernet encryption key (auto-generated)
```

---

## API Examples

### Test Binance Connection

```bash
curl -X POST http://localhost:8000/api/settings/api-keys/binance/test
```

### Get System Info

```bash
curl http://localhost:8000/api/settings/system/info
```

### Save Telegram Settings

```bash
curl -X POST http://localhost:8000/api/settings/notifications \
  -H "Content-Type: application/json" \
  -d '{"telegram_enabled": true, "telegram_bot_token": "123:ABC", "telegram_chat_id": "456"}'
```

---

## Git Commit Message

```
feat(api): Add Settings API module

- settings_routes.py: API keys, notifications, system settings
- main.py: Updated with settings route, version 3.5.2
- requirements.txt: Added cryptography, psutil
- Encrypted storage for sensitive data
- Binance/Bybit/OKX connection testing
- Telegram/Discord notification testing
- 12 new endpoints
```
