"""
Komas Trading Server - Preset Database Operations
=================================================
CRUD operations for indicator presets.

Features:
- Create, read, update, delete presets
- Filter by indicator type, category, source
- Search by name
- Bulk operations for migrations
"""
import json
import logging
import hashlib
from datetime import datetime
from typing import Optional, List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Database path
DB_DIR = Path(__file__).parent.parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)


def _generate_preset_id(name: str, indicator_type: str, symbol: str = None, timeframe: str = None) -> str:
    """Generate unique preset ID based on name and params"""
    # Create hash from name + indicator + symbol + timeframe
    key = f"{indicator_type}:{name}:{symbol or 'ANY'}:{timeframe or 'ANY'}"
    hash_part = hashlib.md5(key.encode()).hexdigest()[:8]
    
    # Clean name for ID
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
    """Create presets table if not exists (enhanced for Dominant)"""
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='dominant_presets'
    """)
    
    if not cursor.fetchone():
        logger.info("Creating dominant_presets table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dominant_presets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                indicator_type TEXT NOT NULL DEFAULT 'dominant',
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
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dp_indicator ON dominant_presets(indicator_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dp_category ON dominant_presets(category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dp_source ON dominant_presets(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dp_symbol ON dominant_presets(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_dp_active ON dominant_presets(is_active)")
        
        conn.commit()
        logger.info("✓ dominant_presets table created")
    
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
    
    # Generate ID if not provided
    if not preset_id:
        preset_id = _generate_preset_id(name, indicator_type, symbol, timeframe)
    
    # Check for duplicate
    cursor.execute("SELECT id FROM dominant_presets WHERE id = ?", (preset_id,))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"Preset with ID {preset_id} already exists")
    
    # Insert
    cursor.execute("""
        INSERT INTO dominant_presets 
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
    
    # Fetch created preset
    cursor.execute("SELECT * FROM dominant_presets WHERE id = ?", (preset_id,))
    row = cursor.fetchone()
    conn.close()
    
    return _row_to_dict(row)


def get_preset(preset_id: str) -> Optional[Dict[str, Any]]:
    """Get preset by ID"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM dominant_presets WHERE id = ?", (preset_id,))
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
            "SELECT * FROM dominant_presets WHERE name = ? AND indicator_type = ?",
            (name, indicator_type)
        )
    else:
        cursor.execute("SELECT * FROM dominant_presets WHERE name = ?", (name,))
    
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
    
    # Build query
    query = "SELECT * FROM dominant_presets WHERE 1=1"
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
    
    query = "SELECT COUNT(*) FROM dominant_presets WHERE 1=1"
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
    
    # Check exists
    cursor.execute("SELECT * FROM dominant_presets WHERE id = ?", (preset_id,))
    if not cursor.fetchone():
        conn.close()
        return None
    
    # Build update
    allowed_fields = [
        "name", "description", "category", "symbol", "timeframe",
        "params", "is_active", "is_favorite", "tags",
        "win_rate", "profit_factor", "total_profit_percent",
        "max_drawdown_percent", "sharpe_ratio"
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
    
    # Add updated_at
    updates.append("updated_at = ?")
    params.append(datetime.utcnow().isoformat())
    
    # Add preset_id for WHERE
    params.append(preset_id)
    
    query = f"UPDATE dominant_presets SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(query, params)
    conn.commit()
    
    # Fetch updated
    cursor.execute("SELECT * FROM dominant_presets WHERE id = ?", (preset_id,))
    row = cursor.fetchone()
    conn.close()
    
    return _row_to_dict(row) if row else None


def delete_preset(preset_id: str) -> bool:
    """Delete preset by ID"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM dominant_presets WHERE id = ?", (preset_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return deleted


def delete_presets_by_source(source: str) -> int:
    """Delete all presets by source (useful for re-migration)"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM dominant_presets WHERE source = ?", (source,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    logger.info(f"Deleted {deleted} presets with source={source}")
    return deleted


def bulk_create_presets(presets: List[Dict[str, Any]], skip_duplicates: bool = True) -> Dict[str, int]:
    """Bulk create presets"""
    ensure_presets_table()
    
    created = 0
    skipped = 0
    errors = 0
    
    for preset_data in presets:
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
    
    logger.info(f"Bulk create: {created} created, {skipped} skipped, {errors} errors")
    return {"created": created, "skipped": skipped, "errors": errors}


def get_preset_stats() -> Dict[str, Any]:
    """Get statistics about presets"""
    ensure_presets_table()
    
    conn = _get_db_connection()
    cursor = conn.cursor()
    
    # Total
    cursor.execute("SELECT COUNT(*) FROM dominant_presets")
    total = cursor.fetchone()[0]
    
    # By indicator
    cursor.execute("""
        SELECT indicator_type, COUNT(*) 
        FROM dominant_presets 
        GROUP BY indicator_type
    """)
    by_indicator = {row[0]: row[1] for row in cursor.fetchall()}
    
    # By category
    cursor.execute("""
        SELECT category, COUNT(*) 
        FROM dominant_presets 
        GROUP BY category
    """)
    by_category = {row[0]: row[1] for row in cursor.fetchall()}
    
    # By source
    cursor.execute("""
        SELECT source, COUNT(*) 
        FROM dominant_presets 
        GROUP BY source
    """)
    by_source = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Active count
    cursor.execute("SELECT COUNT(*) FROM dominant_presets WHERE is_active = 1")
    active_count = cursor.fetchone()[0]
    
    # Favorites count
    cursor.execute("SELECT COUNT(*) FROM dominant_presets WHERE is_favorite = 1")
    favorites_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "total_presets": total,
        "by_indicator": by_indicator,
        "by_category": by_category,
        "by_source": by_source,
        "active_count": active_count,
        "favorites_count": favorites_count
    }


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
    "bulk_create_presets",
    "get_preset_stats",
]
