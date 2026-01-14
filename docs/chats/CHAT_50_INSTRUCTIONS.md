# Chat #50 — Bot Config Core

> **Phase:** 7 — Bot Configuration  
> **Previous:** #49 Optimizer UI ✅  
> **Next:** #51 Bot Pairs Selection

---

## 🎯 GOAL

Create the core bot configuration system with database storage and CRUD API.

---

## 📋 TASKS

- [ ] Create BotConfig model with all parameters
- [ ] Create SQLite table for bots
- [ ] Implement CRUD API endpoints
- [ ] Add validation for all parameters
- [ ] Unit tests

---

## 📊 BOT PARAMETERS

### Identification
| Parameter | Type | Description |
|-----------|------|-------------|
| id | UUID | Unique identifier |
| name | string | Bot name |
| description | string | Optional description |

### Indicator Settings
| Parameter | Type | Description |
|-----------|------|-------------|
| indicator_type | enum | 'trg' or 'dominant' |
| preset_id | UUID | Selected preset ID |

### Risk Management (User-defined, NOT optimized)
| Parameter | Type | Range | Default |
|-----------|------|-------|---------|
| deposit | float | 100 - 1,000,000 | 10,000 |
| risk_per_trade | float | 0.5% - 5% | 1% |
| max_positions | int | 1 - 10 | 3 |
| leverage | int | 1 - 125 | 10 |
| daily_dd_limit | float | 3% - 20% | 5% |
| total_dd_limit | float | 10% - 50% | 20% |

### Trading Settings
| Parameter | Type | Description |
|-----------|------|-------------|
| pairs | list | Selected trading pairs |
| timeframe | string | Trading timeframe |
| is_active | bool | Bot status |

### Timestamps
| Parameter | Type | Description |
|-----------|------|-------------|
| created_at | datetime | Creation time |
| updated_at | datetime | Last update time |

---

## 🔌 API ENDPOINTS

```
GET    /api/bots/list              # List all bots
GET    /api/bots/{id}              # Get single bot
POST   /api/bots/create            # Create new bot
PUT    /api/bots/{id}              # Update bot
DELETE /api/bots/{id}              # Delete bot
POST   /api/bots/{id}/clone        # Clone existing bot
PATCH  /api/bots/{id}/status       # Toggle active status
```

---

## 📁 FILES

```
backend/app/
├── models/
│   └── bot.py              # BotConfig dataclass
├── db/
│   └── bot_db.py           # SQLite operations
├── api/
│   └── bot_routes.py       # CRUD endpoints
└── main.py                 # Router registration

tests/
└── test_bot_config.py      # Unit tests
```

---

## 💾 DATABASE SCHEMA

```sql
CREATE TABLE bots (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    
    -- Indicator
    indicator_type TEXT NOT NULL CHECK(indicator_type IN ('trg', 'dominant')),
    preset_id TEXT,
    
    -- Risk Management
    deposit REAL NOT NULL DEFAULT 10000,
    risk_per_trade REAL NOT NULL DEFAULT 1.0,
    max_positions INTEGER NOT NULL DEFAULT 3,
    leverage INTEGER NOT NULL DEFAULT 10,
    daily_dd_limit REAL NOT NULL DEFAULT 5.0,
    total_dd_limit REAL NOT NULL DEFAULT 20.0,
    
    -- Trading
    pairs TEXT NOT NULL DEFAULT '[]',  -- JSON array
    timeframe TEXT NOT NULL DEFAULT '1h',
    is_active BOOLEAN NOT NULL DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bots_indicator ON bots(indicator_type);
CREATE INDEX idx_bots_active ON bots(is_active);
```

---

## ✅ CHECKLIST

- [ ] BotConfig model with all fields
- [ ] Validation for each parameter
- [ ] SQLite table creation
- [ ] CRUD operations (create, read, update, delete)
- [ ] Clone functionality
- [ ] Status toggle
- [ ] List with filtering
- [ ] Unit tests (20+)
- [ ] Integration with main.py

---

## 📝 GIT COMMIT

```
feat: add bot configuration system with CRUD API

- Add BotConfig model with all RM parameters
- Add SQLite storage for bots
- Add CRUD API endpoints
- Add validation for all parameters
- Add clone functionality
- Add status toggle
- Add 20+ unit tests

Chat #50: Bot Config Core
```

---

**Next chat:** #51 — Bot Pairs Selection
