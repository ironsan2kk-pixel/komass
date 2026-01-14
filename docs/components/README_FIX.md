# KOMAS Fix: Dominant Presets Not Visible

## Problems Fixed

### Problem 1: Router not registered
`preset_routes.py` was not imported in `main.py`, so `/api/presets/dominant/list` returned 404.

### Problem 2: Database schema outdated
The `presets` table was created with an old schema missing the `category` column.

---

## Quick Fix (Recommended)

### Step 1: Stop the server
```
stop.bat
```

### Step 2: Replace main.py
Copy `backend/app/main.py` from this archive to:
```
YOUR_PROJECT/backend/app/main.py
```

### Step 3: Run database migration
```
migrate_presets.bat
```
This will:
- Drop the old presets table
- Create new table with correct schema
- Seed 125+ Dominant presets

### Step 4: Start the server
```
start.bat
```

### Step 5: Verify
Open in browser:
```
http://localhost:8000/api/presets/dominant/list
```
Should show 125+ presets in JSON.

---

## Manual Fix (Alternative)

### Option A: Delete database and reseed
```
1. Stop server
2. Delete data/komas.db
3. Copy main.py from this archive
4. Start server
5. Call: POST http://localhost:8000/api/presets/dominant/seed
```

### Option B: Just fix the table
Run in Python:
```python
import sqlite3
conn = sqlite3.connect("data/komas.db")
conn.execute("DROP TABLE IF EXISTS presets")
conn.commit()
conn.close()
```
Then restart server and call seed endpoint.

---

## Files in This Archive

```
komas_dominant_presets_fix.zip
├── backend/
│   └── app/
│       └── main.py         # Fixed main.py with preset_routes
├── migrate_presets_table.py # Python migration script
├── migrate_presets.bat      # Batch file to run migration
└── README_FIX.md           # This file
```

---

## What Changed in main.py

Added this code block around line 207:

```python
# ============ DOMINANT PRESETS ROUTER (FIX) ============
try:
    from app.api.preset_routes import router as preset_router
    app.include_router(preset_router)
    logger.info("✔ Loaded: Dominant preset routes (/api/presets/*)")
except ImportError as e:
    logger.warning(f"✗ Failed to load preset routes: {e}")
```

---

## API Endpoints Now Available

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/presets/list` | GET | All presets |
| `/api/presets/dominant/list` | GET | Dominant presets only |
| `/api/presets/dominant/seed` | POST | Seed 125+ presets |
| `/api/presets/dominant/clear` | DELETE | Clear Dominant presets |
| `/api/presets/{id}` | GET | Single preset |
| `/api/presets/stats` | GET | Preset statistics |

---

## Expected Result

After fix, calling `/api/presets/dominant/list` should return:
```json
{
  "total": 125,
  "presets": [
    {
      "id": "DOMINANT_ETH_USDT_5m_Scal_a1b2c3d4",
      "name": "ETH/USDT 5m Scalp",
      "category": "scalp",
      "params": {
        "sensitivity": 48.8,
        "tp1_percent": 0.3,
        ...
      },
      ...
    },
    ...
  ]
}
```

In UI, selecting "Dominant" indicator should show preset selector with categories:
- Scalp (5m)
- Short-Term (15m)
- Mid-Term (30m, 1h)
- Long-Term (3h, 4h)

---

## Troubleshooting

### "No presets found"
Run: `POST http://localhost:8000/api/presets/dominant/seed`

### "Failed to load preset routes"
Check that `backend/app/api/preset_routes.py` exists.

### Migration errors
Delete `data/komas.db` and restart server, then seed.

---

**Fix Date:** 28.12.2025  
**Chat:** Dominant Presets Fix
