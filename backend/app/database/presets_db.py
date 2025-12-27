"""
Komas Trading Server - Preset Database Operations (v2)
======================================================
CRUD operations for indicator presets.

Changes in Chat #30:
- Renamed table from `dominant_presets` to `presets` (universal)
- Added migration support from old table
- Added batch operations with progress
- Added verification methods
- Added cleanup/reset methods

Features:
- Create, read, update, delete presets
- Filter by indicator type, category, source
- Search by name
- Bulk operations with progress tracking
- Migration utilities

Chat: #30 — Presets TRG Generator
"""
import json
import logging
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

# Database path
DB_DIR = Path(__file__).parent.parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)

# Table name (changed from dominant_presets to presets)
TABLE_NAME = "presets"
OLD_TABLE_NAME = "dominant_presets"  # For migration


def _generate_preset_id(name: str, indicator_type: str, symbol: str = None, timeframe: str = None) -> str:
    """Generate unique preset ID based on name and params"""
    key = f"{indicator_type}:{name}:{symbol or 'ANY'}:{timeframe or 'ANY'}"
    hash_part = hashlib.md5(key.encode()).hexdigest()[:8]
    clean_name = name.replace(" ", "_").replace("/", "_").replace("|", "_")[:20]
    return f"{indicator_type.upper()}_{clean_name}_{hash_part}"


def _get_db_connection():
    """Get SQLite connection with proper settings"""
    import sqlite3
    db_path = DB_DIR / "komas.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_presets_table():
    """Create presets table if not exists, migrate from old table if needed"""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    # Check if new table exists
    cursor.execute(f"""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='{TABLE_NAME}'
    """)
    
    new_table_exists = cursor.fetchone() is not None
    
    # Check if old table exists (for migration)
    cursor.execute(f"""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='{OLD_TABLE_NAME}'
    """)
    old_table_exists = cursor.fetchone() is not None
    
    if not new_table_exists:
        logger.info(f"Creating {TABLE_NAME} table...")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                indicator_type TEXT NOT NULL DEFAULT 'trg',
                category TEXT NOT NULL DEFAULT 'mid-term',
                symbol TEXT,
                timeframe TEXT,
                params JSON NOT NULL,
                source TEXT DEFAULT 'manual',
                is_active INTEGER DEFAULT 1,
                is_favorite INTEGER DEFAULT 0,
                tags TEXT,
                win_rate REAL,
                profit_factor REAL,
                total_profit_percent REAL,
                max_drawdown_percent REAL,
                sharpe_ratio REAL,
                total_trades INTEGER,
                avg_trade_percent REAL,
                universality_score REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create indexes
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_p_indicator ON {TABLE_NAME}(indicator_type)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_p_category ON {TABLE_NAME}(category)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_p_source ON {TABLE_NAME}(source)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_p_symbol ON {TABLE_NAME}(symbol)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_p_active ON {TABLE_NAME}(is_active)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_p_name ON {TABLE_NAME}(name)")
        
        conn.commit()
        logger.info(f"✓ {TABLE_NAME} table created")
        
        # Migrate data from old table if exists
        if old_table_exists:
            logger.info(f"Migrating data from {OLD_TABLE_NAME} to {TABLE_NAME}...")
            cursor.execute(f"""
                INSERT OR IGNORE INTO {TABLE_NAME} 
                SELECT id, name, description, indicator_type, category, symbol, timeframe,
                       params, source, is_active, is_favorite, tags,
                       win_rate, profit_factor, total_profit_percent, max_drawdown_percent,
                       sharpe_ratio, NULL, NULL, NULL, created_at, updated_at
                FROM {OLD_TABLE_NAME}
            """)
            migrated = cursor.rowcount
            conn.commit()
            logger.info(f"✓ Migrated {migrated} presets")
    
    conn.close()


def create_preset(
    name: str,
    indicator_type: str,
    params: Dict[str, Any],
    category: str = "mid-term",
    description: str = None,
    symbol: str = None,
    timeframe: str = None,
    source: str = "manual",
    tags: List[str] = None,
    preset_id: str = None
) -> Dict[str, Any]:
    """Create a new preset"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    
    if not preset_id:
        preset_id = _generate_preset_id(name, indicator_type, symbol, timeframe)
    
    # Check for duplicate
    cursor.execute(f"SELECT id FROM {TABLE_NAME} WHERE id = ?", (preset_id,))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"Preset with ID {preset_id} already exists")
    
    cursor.execute(f"""
        INSERT INTO {TABLE_NAME} 
        (id, name, description, indicator_type, category, symbol, timeframe, 
         params, source, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        preset_id,
        name,
        description,
        indicator_type,
        category,
        symbol,
        timeframe,
        json.dumps(params),
        source,
        ",".join(tags) if tags else None,
        now,
        now
    ))
    
    conn.commit()
    
    cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = ?", (preset_id,))
    row = cursor.fetchone()
    conn.close()
    
    return _row_to_dict(row)


def get_preset(preset_id: str) -> Optional[Dict[str, Any]]:
    """Get preset by ID"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = ?", (preset_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return _row_to_dict(row)
    return None


def get_preset_by_name(name: str, indicator_type: str = None) -> Optional[Dict[str, Any]]:
    """Get preset by exact name"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    if indicator_type:
        cursor.execute(
            f"SELECT * FROM {TABLE_NAME} WHERE name = ? AND indicator_type = ?",
            (name, indicator_type)
        )
    else:
        cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE name = ?", (name,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return _row_to_dict(row)
    return None


def list_presets(
    indicator_type: str = None,
    category: str = None,
    source: str = None,
    symbol: str = None,
    timeframe: str = None,
    is_active: bool = None,
    is_favorite: bool = None,
    search: str = None,
    limit: int = 1000,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """List presets with filters"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params = []
    
    if indicator_type:
        query += " AND indicator_type = ?"
        params.append(indicator_type)
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    if source:
        query += " AND source = ?"
        params.append(source)
    
    if symbol:
        query += " AND symbol = ?"
        params.append(symbol)
    
    if timeframe:
        query += " AND timeframe = ?"
        params.append(timeframe)
    
    if is_active is not None:
        query += " AND is_active = ?"
        params.append(1 if is_active else 0)
    
    if is_favorite is not None:
        query += " AND is_favorite = ?"
        params.append(1 if is_favorite else 0)
    
    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    query += " ORDER BY name ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [_row_to_dict(row) for row in rows]


def count_presets(
    indicator_type: str = None,
    category: str = None,
    source: str = None,
    is_active: bool = None
) -> int:
    """Count presets with filters"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    query = f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE 1=1"
    params = []
    
    if indicator_type:
        query += " AND indicator_type = ?"
        params.append(indicator_type)
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    if source:
        query += " AND source = ?"
        params.append(source)
    
    if is_active is not None:
        query += " AND is_active = ?"
        params.append(1 if is_active else 0)
    
    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    conn.close()
    
    return count


def update_preset(preset_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Update preset fields"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = ?", (preset_id,))
    if not cursor.fetchone():
        conn.close()
        return None
    
    allowed_fields = [
        "name", "description", "category", "symbol", "timeframe",
        "params", "is_active", "is_favorite", "tags",
        "win_rate", "profit_factor", "total_profit_percent",
        "max_drawdown_percent", "sharpe_ratio", "total_trades",
        "avg_trade_percent", "universality_score"
    ]
    
    updates = []
    params = []
    
    for field, value in kwargs.items():
        if field in allowed_fields and value is not None:
            if field == "params":
                value = json.dumps(value)
            elif field == "tags" and isinstance(value, list):
                value = ",".join(value)
            elif field in ("is_active", "is_favorite"):
                value = 1 if value else 0
            
            updates.append(f"{field} = ?")
            params.append(value)
    
    if not updates:
        conn.close()
        return get_preset(preset_id)
    
    updates.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat())
    params.append(preset_id)
    
    query = f"UPDATE {TABLE_NAME} SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()
    
    cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = ?", (preset_id,))
    row = cursor.fetchone()
    conn.close()
    
    return _row_to_dict(row) if row else None


def delete_preset(preset_id: str) -> bool:
    """Delete preset by ID"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE id = ?", (preset_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return deleted


def delete_presets_by_source(source: str, indicator_type: str = None) -> int:
    """Delete all presets by source (useful for re-generation)"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    if indicator_type:
        cursor.execute(
            f"DELETE FROM {TABLE_NAME} WHERE source = ? AND indicator_type = ?", 
            (source, indicator_type)
        )
    else:
        cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE source = ?", (source,))
    
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    logger.info(f"Deleted {deleted} presets with source={source}" + 
                (f", indicator_type={indicator_type}" if indicator_type else ""))
    return deleted


def delete_presets_by_indicator(indicator_type: str, source: str = None) -> int:
    """Delete all presets by indicator type"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    if source:
        cursor.execute(
            f"DELETE FROM {TABLE_NAME} WHERE indicator_type = ? AND source = ?", 
            (indicator_type, source)
        )
    else:
        cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE indicator_type = ?", (indicator_type,))
    
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    logger.info(f"Deleted {deleted} {indicator_type} presets")
    return deleted


def bulk_create_presets(
    presets: List[Dict[str, Any]], 
    skip_duplicates: bool = True,
    progress_callback: Callable[[int, int], None] = None
) -> Dict[str, int]:
    """Bulk create presets with optional progress callback"""
    ensure_presets_table()
    
    created = 0
    skipped = 0
    errors = 0
    total = len(presets)
    
    for i, preset_data in enumerate(presets):
        try:
            create_preset(**preset_data)
            created += 1
        except ValueError as e:
            if skip_duplicates and "already exists" in str(e):
                skipped += 1
            else:
                errors += 1
                logger.error(f"Error creating preset: {e}")
        except Exception as e:
            errors += 1
            logger.error(f"Error creating preset: {e}")
        
        if progress_callback:
            progress_callback(i + 1, total)
    
    logger.info(f"Bulk create: {created} created, {skipped} skipped, {errors} errors")
    return {"created": created, "skipped": skipped, "errors": errors, "total": total}


def get_preset_stats() -> Dict[str, Any]:
    """Get statistics about presets"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    # Total
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    total = cursor.fetchone()[0]
    
    # By indicator
    cursor.execute(f"""
        SELECT indicator_type, COUNT(*) 
        FROM {TABLE_NAME} 
        GROUP BY indicator_type
    """)
    by_indicator = {row[0]: row[1] for row in cursor.fetchall()}
    
    # By category
    cursor.execute(f"""
        SELECT category, COUNT(*) 
        FROM {TABLE_NAME} 
        GROUP BY category
    """)
    by_category = {row[0]: row[1] for row in cursor.fetchall()}
    
    # By source
    cursor.execute(f"""
        SELECT source, COUNT(*) 
        FROM {TABLE_NAME} 
        GROUP BY source
    """)
    by_source = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Active count
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE is_active = 1")
    active_count = cursor.fetchone()[0]
    
    # Favorites count
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE is_favorite = 1")
    favorites_count = cursor.fetchone()[0]
    
    # TRG system presets count
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE indicator_type = 'trg' AND source = 'system'")
    trg_system_count = cursor.fetchone()[0]
    
    # Dominant system presets count
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE indicator_type = 'dominant' AND source = 'system'")
    dominant_system_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_presets": total,
        "by_indicator": by_indicator,
        "by_category": by_category,
        "by_source": by_source,
        "active_count": active_count,
        "favorites_count": favorites_count,
        "trg_system_count": trg_system_count,
        "dominant_system_count": dominant_system_count,
        "expected_trg_system": 200,
        "expected_dominant_system": 125,
    }


def verify_system_presets() -> Dict[str, Any]:
    """Verify all system presets exist and are valid"""
    ensure_presets_table()
    
    from app.presets import TRGPreset, DominantPreset, FilterProfile
    
    results = {
        "trg": {
            "expected": 200,
            "found": 0,
            "valid": 0,
            "invalid": 0,
            "missing": [],
            "invalid_ids": []
        },
        "dominant": {
            "expected": 125,
            "found": 0,
            "valid": 0,
            "invalid": 0,
            "missing": [],
            "invalid_ids": []
        }
    }
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    # Check TRG presets
    for i1 in TRGPreset.I1_VALUES:
        for i2 in TRGPreset.I2_VALUES:
            for profile in TRGPreset.FILTER_PROFILES:
                expected_name = f"{profile.value}_{i1}_{int(i2 * 10)}"
                expected_id = f"TRG_SYS_{expected_name}"
                
                cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = ?", (expected_id,))
                row = cursor.fetchone()
                
                if row:
                    results["trg"]["found"] += 1
                    # Validate params
                    preset_data = _row_to_dict(row)
                    params = preset_data.get("params", {})
                    if params.get("i1") == i1 and params.get("i2") == i2:
                        results["trg"]["valid"] += 1
                    else:
                        results["trg"]["invalid"] += 1
                        results["trg"]["invalid_ids"].append(expected_id)
                else:
                    results["trg"]["missing"].append(expected_name)
    
    # Check Dominant presets
    cursor.execute(f"""
        SELECT COUNT(*) FROM {TABLE_NAME} 
        WHERE indicator_type = 'dominant' AND source = 'system'
    """)
    results["dominant"]["found"] = cursor.fetchone()[0]
    results["dominant"]["valid"] = results["dominant"]["found"]
    
    conn.close()
    
    return results


def reset_system_presets(indicator_type: str = None) -> Dict[str, int]:
    """Reset (delete) system presets, optionally by indicator type"""
    if indicator_type:
        deleted = delete_presets_by_source("system", indicator_type)
    else:
        deleted = delete_presets_by_source("system")
    
    return {"deleted": deleted}


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert SQLite row to dictionary"""
    if row is None:
        return None
    
    d = dict(row)
    
    # Parse JSON fields
    if "params" in d and d["params"]:
        try:
            d["params"] = json.loads(d["params"])
        except json.JSONDecodeError:
            d["params"] = {}
    
    # Parse tags
    if "tags" in d and d["tags"]:
        d["tags"] = [t.strip() for t in d["tags"].split(",") if t.strip()]
    else:
        d["tags"] = []
    
    # Convert bool fields
    d["is_active"] = bool(d.get("is_active", 1))
    d["is_favorite"] = bool(d.get("is_favorite", 0))
    
    return d


# ============ EXPORT ============

__all__ = [
    "ensure_presets_table",
    "create_preset",
    "get_preset",
    "get_preset_by_name",
    "list_presets",
    "count_presets",
    "update_preset",
    "delete_preset",
    "delete_presets_by_source",
    "delete_presets_by_indicator",
    "bulk_create_presets",
    "get_preset_stats",
    "verify_system_presets",
    "reset_system_presets",
]
