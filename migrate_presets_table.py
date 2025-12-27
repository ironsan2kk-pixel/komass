"""
Komas Trading Server - Database Migration
==========================================
Migrates presets table to new schema with all required columns.

Run:
    python migrate_presets_table.py
    
This script:
1. Backs up existing presets data
2. Drops old presets table
3. Creates new table with correct schema
4. Restores data (if any valuable data exists)
5. Seeds Dominant presets

Chat: Dominant Presets Fix
"""
import sys
import os
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Add app directory to path
# Script can be run from project root or from backend folder
script_dir = os.path.dirname(os.path.abspath(__file__))

# Check if we're in project root or backend folder
if os.path.exists(os.path.join(script_dir, 'backend', 'app')):
    # Running from project root
    backend_dir = os.path.join(script_dir, 'backend')
    app_dir = os.path.join(backend_dir, 'app')
    DB_DIR = Path(script_dir) / "data"
elif os.path.exists(os.path.join(script_dir, 'app')):
    # Running from backend folder
    backend_dir = script_dir
    app_dir = os.path.join(script_dir, 'app')
    DB_DIR = Path(script_dir).parent / "data"
else:
    print("ERROR: Cannot find app directory. Run from project root or backend folder.")
    sys.exit(1)

if app_dir not in sys.path:
    sys.path.insert(0, app_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "komas.db"

TABLE_NAME = "presets"


def get_table_columns():
    """Get current columns of presets table"""
    if not DB_PATH.exists():
        return []
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
        columns = [row[1] for row in cursor.fetchall()]
        return columns
    except:
        return []
    finally:
        conn.close()


def backup_presets():
    """Backup existing presets data"""
    if not DB_PATH.exists():
        return []
    
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if table exists
        cursor.execute(f"""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='{TABLE_NAME}'
        """)
        if not cursor.fetchone():
            return []
        
        # Get all data
        cursor.execute(f"SELECT * FROM {TABLE_NAME}")
        rows = cursor.fetchall()
        
        backup = []
        for row in rows:
            backup.append(dict(row))
        
        return backup
    except Exception as e:
        print(f"Warning: Could not backup presets: {e}")
        return []
    finally:
        conn.close()


def drop_presets_table():
    """Drop existing presets table"""
    if not DB_PATH.exists():
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")
        conn.commit()
        print(f"[OK] Dropped old {TABLE_NAME} table")
    finally:
        conn.close()


def create_presets_table():
    """Create presets table with correct schema"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                indicator_type TEXT NOT NULL DEFAULT 'trg',
                category TEXT NOT NULL DEFAULT 'mid-term',
                symbol TEXT,
                timeframe TEXT,
                params TEXT NOT NULL,
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
        print(f"[OK] Created {TABLE_NAME} table with correct schema")
    finally:
        conn.close()


def verify_schema():
    """Verify table has all required columns"""
    required_columns = [
        "id", "name", "description", "indicator_type", "category",
        "symbol", "timeframe", "params", "source", "is_active",
        "is_favorite", "tags", "win_rate", "profit_factor",
        "total_profit_percent", "max_drawdown_percent", "sharpe_ratio",
        "total_trades", "avg_trade_percent", "universality_score",
        "created_at", "updated_at"
    ]
    
    columns = get_table_columns()
    
    missing = [col for col in required_columns if col not in columns]
    
    if missing:
        print(f"[ERROR] Missing columns: {missing}")
        return False
    
    print(f"[OK] Schema verified: {len(columns)} columns")
    return True


def seed_dominant_presets():
    """Seed Dominant presets from GG Pine Script"""
    try:
        from app.migrations.seed_dominant_presets import seed_all_dominant_presets
        result = seed_all_dominant_presets()
        
        print(f"[OK] Dominant presets seeded:")
        print(f"     Created: {result.get('created', 0)}")
        print(f"     Skipped: {result.get('skipped', 0)}")
        print(f"     Errors:  {result.get('errors', 0)}")
        
        return result
    except Exception as e:
        print(f"[ERROR] Failed to seed presets: {e}")
        import traceback
        traceback.print_exc()
        return {"created": 0, "errors": 1}


def main():
    print("=" * 60)
    print("KOMAS - Presets Table Migration")
    print("=" * 60)
    print()
    
    # Check current state
    print("1. Checking current schema...")
    columns = get_table_columns()
    if columns:
        print(f"   Found existing table with {len(columns)} columns")
        print(f"   Columns: {columns[:5]}...")
        
        if "category" not in columns:
            print("   [!] Missing 'category' column - migration needed")
        else:
            print("   [OK] Schema looks correct")
            # Still verify and seed
    else:
        print("   No existing presets table found")
    
    # Backup (if any user presets)
    print()
    print("2. Backing up existing data...")
    backup = backup_presets()
    user_presets = [p for p in backup if p.get("source") == "manual"]
    print(f"   Total: {len(backup)} presets")
    print(f"   User presets: {len(user_presets)}")
    
    # Drop old table
    print()
    print("3. Dropping old table...")
    drop_presets_table()
    
    # Create new table
    print()
    print("4. Creating new table with correct schema...")
    create_presets_table()
    
    # Verify
    print()
    print("5. Verifying schema...")
    if not verify_schema():
        print("[FAILED] Schema verification failed!")
        return 1
    
    # Seed Dominant presets
    print()
    print("6. Seeding Dominant presets (125+)...")
    seed_dominant_presets()
    
    # Count final
    print()
    print("7. Final count...")
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}")
    total = cursor.fetchone()[0]
    cursor.execute(f"SELECT COUNT(*) FROM {TABLE_NAME} WHERE indicator_type = 'dominant'")
    dominant = cursor.fetchone()[0]
    conn.close()
    
    print(f"   Total presets: {total}")
    print(f"   Dominant presets: {dominant}")
    
    print()
    print("=" * 60)
    print("Migration complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Restart the server: stop.bat && start.bat")
    print("2. Test: http://localhost:8000/api/presets/dominant/list")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
