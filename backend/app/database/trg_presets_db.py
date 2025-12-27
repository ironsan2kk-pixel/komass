"""
Komas Trading Server - TRG Presets Database
============================================
CRUD operations for TRG indicator presets.

Separate table from Dominant presets.

Table: trg_presets (200 system presets)

Chat: #30 — Presets TRG Generator
"""
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path

logger = logging.getLogger(__name__)

# Database path
DB_DIR = Path(__file__).parent.parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)

TABLE_NAME = "trg_presets"


def _get_db_connection():
    """Get SQLite connection with proper settings"""
    import sqlite3
    db_path = DB_DIR / "komas.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def ensure_trg_presets_table():
    """Create trg_presets table if not exists"""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='{TABLE_NAME}'
    """)
    
    if not cursor.fetchone():
        logger.info(f"Creating {TABLE_NAME} table...")
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                category TEXT NOT NULL DEFAULT 'mid-term',
                params JSON NOT NULL,
                source TEXT DEFAULT 'system',
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
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_trg_category ON {TABLE_NAME}(category)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_trg_source ON {TABLE_NAME}(source)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_trg_active ON {TABLE_NAME}(is_active)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS idx_trg_name ON {TABLE_NAME}(name)")
        
        conn.commit()
        logger.info(f"✓ {TABLE_NAME} table created")
    
    conn.close()


def create_trg_preset(
    preset_id: str,
    name: str,
    params: Dict[str, Any],
    category: str = "mid-term",
    description: str = None,
    source: str = "system",
    tags: List[str] = None
) -> Dict[str, Any]:
    """Create a new TRG preset"""
    ensure_trg_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    
    # Check for duplicate
    cursor.execute(f"SELECT id FROM {TABLE_NAME} WHERE id = ?", (preset_id,))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"Preset with id '{preset_id}' already exists")
    
    cursor.execute(f"""
        INSERT INTO {TABLE_NAME} 
        (id, name, description, category, params, source, tags, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        preset_id,
        name,
        description,
        category,
        json.dumps(params),
        source,
        json.dumps(tags) if tags else None,
        now,
        now
    ))
    
    conn.commit()
    conn.close()
    
    return {
        "id": preset_id,
        "name": name,
        "description": description,
        "category": category,
        "params": params,
        "source": source,
        "tags": tags,
        "created_at": now,
        "updated_at": now
    }


def get_trg_preset(preset_id: str) -> Optional[Dict[str, Any]]:
    """Get a TRG preset by ID"""
    ensure_trg_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = ?", (preset_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return _row_to_dict(row)


def get_trg_preset_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get a TRG preset by name"""
    ensure_trg_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT * FROM {TABLE_NAME} WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
    
    return _row_to_dict(row)


def list_trg_presets(
    category: str = None,
    source: str = None,
    is_active: bool = None,
    is_favorite: bool = None,
    search: str = None,
    limit: int = None,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """List TRG presets with filters"""
    ensure_trg_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    query = f"SELECT * FROM {TABLE_NAME} WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    if source:
        query += " AND source = ?"
        params.append(source)
    
    if is_active is not None:
        query += " AND is_active = ?"
        params.append(1 if is_active else 0)
    
    if is_favorite is not None:
        query += " AND is_favorite = ?"
        params.append(1 if is_favorite else 0)
    
    if search:
        query += " AND (name LIKE ? OR description LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])
    
    query += " ORDER BY name"
    
    if limit:
        query += f" LIMIT {limit} OFFSET {offset}"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [_row_to_dict(row) for row in rows]


def count_trg_presets(source: str = None, category: str = None) -> int:
    """Count TRG presets"""
    ensure_trg_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    query = f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE 1=1"
    params = []
    
    if source:
        query += " AND source = ?"
        params.append(source)
    
    if category:
        query += " AND category = ?"
        params.append(category)
    
    cursor.execute(query, params)
    count = cursor.fetchone()[0]
    conn.close()
    
    return count


def update_trg_preset(
    preset_id: str,
    name: str = None,
    description: str = None,
    category: str = None,
    params: Dict[str, Any] = None,
    is_active: bool = None,
    is_favorite: bool = None,
    tags: List[str] = None
) -> Optional[Dict[str, Any]]:
    """Update a TRG preset"""
    ensure_trg_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    # Check exists
    cursor.execute(f"SELECT id FROM {TABLE_NAME} WHERE id = ?", (preset_id,))
    if not cursor.fetchone():
        conn.close()
        return None
    
    updates = []
    values = []
    
    if name is not None:
        updates.append("name = ?")
        values.append(name)
    
    if description is not None:
        updates.append("description = ?")
        values.append(description)
    
    if category is not None:
        updates.append("category = ?")
        values.append(category)
    
    if params is not None:
        updates.append("params = ?")
        values.append(json.dumps(params))
    
    if is_active is not None:
        updates.append("is_active = ?")
        values.append(1 if is_active else 0)
    
    if is_favorite is not None:
        updates.append("is_favorite = ?")
        values.append(1 if is_favorite else 0)
    
    if tags is not None:
        updates.append("tags = ?")
        values.append(json.dumps(tags))
    
    if updates:
        updates.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        values.append(preset_id)
        
        query = f"UPDATE {TABLE_NAME} SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()
    
    return get_trg_preset(preset_id)


def delete_trg_preset(preset_id: str) -> bool:
    """Delete a TRG preset"""
    ensure_trg_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE id = ?", (preset_id,))
    deleted = cursor.rowcount > 0
    
    conn.commit()
    conn.close()
    
    return deleted


def delete_trg_system_presets() -> int:
    """Delete all TRG system presets"""
    ensure_trg_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE source = 'system'")
    deleted = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    logger.info(f"Deleted {deleted} TRG system presets")
    return deleted


def bulk_create_trg_presets(
    presets: List[Dict[str, Any]],
    skip_duplicates: bool = True,
    progress_callback: Callable[[int, int], None] = None
) -> Dict[str, int]:
    """Bulk create TRG presets"""
    ensure_trg_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.utcnow().isoformat()
    
    created = 0
    skipped = 0
    errors = 0
    total = len(presets)
    
    for i, preset in enumerate(presets):
        try:
            preset_id = preset.get("id")
            name = preset.get("name")
            
            # Check duplicate
            cursor.execute(f"SELECT id FROM {TABLE_NAME} WHERE id = ?", (preset_id,))
            if cursor.fetchone():
                if skip_duplicates:
                    skipped += 1
                else:
                    # Update existing
                    cursor.execute(f"""
                        UPDATE {TABLE_NAME} 
                        SET name=?, description=?, category=?, params=?, 
                            source=?, tags=?, updated_at=?
                        WHERE id=?
                    """, (
                        name,
                        preset.get("description"),
                        preset.get("category", "mid-term"),
                        json.dumps(preset.get("params", {})),
                        preset.get("source", "system"),
                        json.dumps(preset.get("tags")) if preset.get("tags") else None,
                        now,
                        preset_id
                    ))
                    created += 1
            else:
                cursor.execute(f"""
                    INSERT INTO {TABLE_NAME} 
                    (id, name, description, category, params, source, tags, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    preset_id,
                    name,
                    preset.get("description"),
                    preset.get("category", "mid-term"),
                    json.dumps(preset.get("params", {})),
                    preset.get("source", "system"),
                    json.dumps(preset.get("tags")) if preset.get("tags") else None,
                    now,
                    now
                ))
                created += 1
        
        except Exception as e:
            logger.error(f"Error creating preset {preset.get('id')}: {e}")
            errors += 1
        
        if progress_callback and (i + 1) % 10 == 0:
            progress_callback(i + 1, total)
    
    conn.commit()
    conn.close()
    
    if progress_callback:
        progress_callback(total, total)
    
    return {
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "total": total
    }


def get_trg_preset_stats() -> Dict[str, Any]:
    """Get TRG preset statistics"""
    ensure_trg_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    # Total count
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    total = cursor.fetchone()[0]
    
    # By source
    cursor.execute(f"""
        SELECT source, COUNT(*) as count 
        FROM {TABLE_NAME} 
        GROUP BY source
    """)
    by_source = {row['source']: row['count'] for row in cursor.fetchall()}
    
    # By category
    cursor.execute(f"""
        SELECT category, COUNT(*) as count 
        FROM {TABLE_NAME} 
        GROUP BY category
    """)
    by_category = {row['category']: row['count'] for row in cursor.fetchall()}
    
    # Active/Favorites
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE is_active = 1")
    active = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE is_favorite = 1")
    favorites = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_presets": total,
        "expected_system": 200,
        "by_source": by_source,
        "by_category": by_category,
        "active_count": active,
        "favorites_count": favorites,
        "system_complete": by_source.get("system", 0) >= 200
    }


def verify_trg_system_presets() -> Dict[str, Any]:
    """Verify all 200 TRG system presets exist"""
    ensure_trg_presets_table()
    
    # Expected presets
    I1_VALUES = [14, 25, 40, 60, 80, 110, 150, 200]
    I2_VALUES = [2.0, 3.0, 4.0, 5.5, 7.5]
    FILTER_PROFILES = ['N', 'T', 'M', 'S', 'F']
    
    expected = set()
    for i1 in I1_VALUES:
        for i2 in I2_VALUES:
            for profile in FILTER_PROFILES:
                name = f"{profile}_{i1}_{int(i2 * 10)}"
                expected.add(name)
    
    # Get existing
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(f"SELECT name, params FROM {TABLE_NAME} WHERE source = 'system'")
    rows = cursor.fetchall()
    conn.close()
    
    existing = {}
    for row in rows:
        existing[row['name']] = json.loads(row['params'])
    
    # Compare
    missing = expected - set(existing.keys())
    extra = set(existing.keys()) - expected
    
    # Validate params
    invalid = []
    for name in expected & set(existing.keys()):
        params = existing[name]
        # Parse expected values from name
        parts = name.split('_')
        if len(parts) == 3:
            exp_i1 = int(parts[1])
            exp_i2 = int(parts[2]) / 10.0
            if params.get('i1') != exp_i1 or params.get('i2') != exp_i2:
                invalid.append(name)
    
    return {
        "expected": len(expected),
        "found": len(existing),
        "missing": list(missing)[:20],
        "missing_count": len(missing),
        "extra": list(extra)[:10],
        "extra_count": len(extra),
        "invalid": invalid[:10],
        "invalid_count": len(invalid),
        "is_valid": len(missing) == 0 and len(invalid) == 0
    }


def _row_to_dict(row) -> Dict[str, Any]:
    """Convert database row to dictionary"""
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "indicator_type": "trg",
        "category": row["category"],
        "params": json.loads(row["params"]) if row["params"] else {},
        "source": row["source"],
        "is_active": bool(row["is_active"]),
        "is_favorite": bool(row["is_favorite"]),
        "tags": json.loads(row["tags"]) if row["tags"] else [],
        "metrics": {
            "win_rate": row["win_rate"],
            "profit_factor": row["profit_factor"],
            "total_profit_percent": row["total_profit_percent"],
            "max_drawdown_percent": row["max_drawdown_percent"],
            "sharpe_ratio": row["sharpe_ratio"],
            "total_trades": row["total_trades"],
            "avg_trade_percent": row["avg_trade_percent"],
            "universality_score": row["universality_score"]
        },
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }


# ==================== EXPORTS ====================

__all__ = [
    "ensure_trg_presets_table",
    "create_trg_preset",
    "get_trg_preset",
    "get_trg_preset_by_name",
    "list_trg_presets",
    "count_trg_presets",
    "update_trg_preset",
    "delete_trg_preset",
    "delete_trg_system_presets",
    "bulk_create_trg_presets",
    "get_trg_preset_stats",
    "verify_trg_system_presets",
]
