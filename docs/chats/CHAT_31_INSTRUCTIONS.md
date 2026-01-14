# Chat #31 — Presets Storage

> **Phase:** 3 — Preset System  
> **Previous:** #30 Presets TRG Generator ✅  
> **Next:** #32 Presets User CRUD

---

## 🎯 GOAL

Enhance preset storage layer with versioning, backup/restore, and batch import/export capabilities.

---

## 📋 TASKS

- [ ] Preset versioning (history of changes)
- [ ] Backup presets to JSON file
- [ ] Restore presets from backup
- [ ] Export multiple presets to single JSON file
- [ ] Import presets from batch JSON file
- [ ] Data integrity checks (validate all presets)
- [ ] Cleanup orphaned/invalid presets
- [ ] Statistics and analytics endpoints

---

## 🔧 FEATURES TO IMPLEMENT

### 1. Versioning Table

```sql
CREATE TABLE preset_history (
    id INTEGER PRIMARY KEY,
    preset_id TEXT NOT NULL,
    version INTEGER NOT NULL,
    params JSON NOT NULL,
    changed_by TEXT,  -- 'user', 'optimizer', 'system'
    change_reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (preset_id) REFERENCES presets(id)
);
```

### 2. Backup/Restore API

```
POST /api/presets/backup              — Create backup
POST /api/presets/restore             — Restore from backup
GET  /api/presets/backups             — List backups
DELETE /api/presets/backups/{id}      — Delete backup
```

### 3. Batch Import/Export

```
POST /api/presets/export/batch        — Export multiple presets
POST /api/presets/import/batch        — Import multiple presets
```

### 4. Data Integrity

```
GET  /api/presets/integrity           — Check all presets
POST /api/presets/cleanup             — Remove invalid presets
```

---

## 📁 FILES

```
backend/app/database/
├── presets_db.py            # Add versioning methods
└── preset_history.py        # History tracking

backend/app/api/
└── preset_routes_v3.py      # Add backup/restore endpoints

tests/
└── test_preset_storage.py   # Storage tests
```

---

## 📊 GIT COMMIT

```
feat(presets): Add versioning and backup/restore

- Add preset_history table for versioning
- Add backup/restore endpoints
- Add batch import/export
- Add data integrity checks
- Add cleanup utilities

Chat #31: Presets Storage
```

---

**Next chat:** #32 — Presets User CRUD
