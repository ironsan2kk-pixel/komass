"""
Komas Trading Server - Signals API Tests
=========================================
Comprehensive test suite for Signals API

Run: python -m pytest tests/test_signals_api.py -v
"""

import os
import sys
import json
import pytest
import sqlite3
import gc
from datetime import datetime, timedelta
from pathlib import Path
from io import StringIO

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test database path
TEST_DB = Path(__file__).parent / "test_signals.db"

# Global connection tracker for cleanup
_open_connections = []


def get_test_db_connection():
    """Get SQLite connection with tracking for cleanup"""
    conn = sqlite3.connect(str(TEST_DB), timeout=30)
    conn.row_factory = sqlite3.Row
    _open_connections.append(conn)
    return conn


def close_all_connections():
    """Close all tracked connections"""
    global _open_connections
    for conn in _open_connections:
        try:
            conn.close()
        except:
            pass
    _open_connections = []
    gc.collect()  # Force garbage collection


# ============ FIXTURES ============

@pytest.fixture(scope="function")
def clean_db():
    """Clean database before each test"""
    # Close any existing connections
    close_all_connections()
    
    # Remove old test DB
    if TEST_DB.exists():
        try:
            TEST_DB.unlink()
        except PermissionError:
            pass  # Will be overwritten anyway
    
    # Patch DB_FILE in signals module
    import backend.app.api.signals as signals_module
    signals_module.DB_FILE = TEST_DB
    
    # Override get_db_connection to use our tracked version
    original_get_db = signals_module.get_db_connection
    signals_module.get_db_connection = get_test_db_connection
    
    signals_module.init_database()
    
    yield signals_module
    
    # Cleanup after test
    close_all_connections()
    signals_module.get_db_connection = original_get_db
    
    if TEST_DB.exists():
        try:
            TEST_DB.unlink()
        except PermissionError:
            pass  # Windows may still have it locked


@pytest.fixture
def sample_signal():
    """Sample signal data"""
    return {
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "type": "long",
        "source": "trg",
        "entry_price": 42000.0,
        "stop_loss": 40000.0,
        "tp1": 43000.0,
        "tp2": 44000.0,
        "tp3": 45000.0,
        "leverage": 10.0,
        "position_size": 1000.0,
        "notes": "Test signal",
        "tags": ["test", "btc"]
    }


@pytest.fixture
def create_test_signals(clean_db):
    """Create multiple test signals"""
    conn = get_test_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now()
    
    signals = [
        # Active long signals (PnL not counted - not closed)
        ("BTCUSDT", "1h", "long", "trg", "active", 42000, 40000, 100.5, 2.5),
        ("ETHUSDT", "4h", "long", "supertrend", "active", 2200, 2000, 50.0, 2.2),
        
        # Closed signals (PnL counted)
        ("BTCUSDT", "1h", "short", "trg", "closed", 43000, 45000, -80.0, -1.8),
        ("SOLUSDT", "1h", "long", "rsi", "closed", 100, 90, 150.0, 15.0),
        
        # Pending signals
        ("DOGEUSDT", "15m", "long", "manual", "pending", 0.08, 0.07, None, None),
        
        # Cancelled signals
        ("XRPUSDT", "4h", "short", "bot", "cancelled", 0.5, 0.6, None, None),
    ]
    
    for i, (symbol, tf, type_, source, status, entry, sl, pnl, pnl_pct) in enumerate(signals):
        created = (now - timedelta(days=i)).isoformat()
        cursor.execute("""
            INSERT INTO signals (
                symbol, timeframe, type, source, status,
                entry_price, stop_loss, realized_pnl, realized_pnl_percent,
                tp1, tp2, tp3, leverage,
                created_at, updated_at, activated_at, closed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            symbol, tf, type_, source, status,
            entry, sl, pnl, pnl_pct,
            entry * 1.02, entry * 1.04, entry * 1.06, 10,
            created, created,
            created if status in ('active', 'closed') else None,
            created if status in ('closed', 'cancelled') else None
        ))
    
    conn.commit()
    conn.close()
    _open_connections.remove(conn)
    
    return len(signals)


# ============ DATABASE TESTS ============

class TestDatabase:
    """Database initialization tests"""
    
    def test_init_database(self, clean_db):
        """Test database initialization"""
        assert TEST_DB.exists()
        
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        # Check table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='signals'")
        assert cursor.fetchone() is not None
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_indexes_created(self, clean_db):
        """Test that indexes are created"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_signals_%'")
        indexes = cursor.fetchall()
        
        assert len(indexes) >= 5  # At least 5 indexes
        
        conn.close()
        _open_connections.remove(conn)


# ============ CRUD TESTS ============

class TestCRUD:
    """CRUD operation tests"""
    
    def test_create_signal(self, clean_db, sample_signal):
        """Test creating a signal"""
        from backend.app.api.signals import SignalCreate
        
        signal = SignalCreate(**sample_signal)
        
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO signals (
                symbol, timeframe, type, source, status,
                entry_price, stop_loss, tp1, tp2, tp3,
                leverage, position_size, notes, tags,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal.symbol, signal.timeframe, signal.type.value, signal.source.value,
            signal.entry_price, signal.stop_loss, signal.tp1, signal.tp2, signal.tp3,
            signal.leverage, signal.position_size, signal.notes,
            json.dumps(signal.tags), now, now
        ))
        
        signal_id = cursor.lastrowid
        conn.commit()
        
        # Verify
        cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
        row = cursor.fetchone()
        
        assert row is not None
        assert row['symbol'] == 'BTCUSDT'
        assert row['type'] == 'long'
        assert row['entry_price'] == 42000.0
        assert row['status'] == 'pending'
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_read_signal(self, clean_db, create_test_signals):
        """Test reading a signal"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM signals WHERE id = 1")
        row = cursor.fetchone()
        
        assert row is not None
        assert row['symbol'] == 'BTCUSDT'
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_update_signal(self, clean_db, create_test_signals):
        """Test updating a signal"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute("""
            UPDATE signals SET 
                status = 'closed',
                exit_price = 44000,
                realized_pnl = 200,
                updated_at = ?
            WHERE id = 1
        """, (now,))
        
        conn.commit()
        
        cursor.execute("SELECT * FROM signals WHERE id = 1")
        row = cursor.fetchone()
        
        assert row['status'] == 'closed'
        assert row['exit_price'] == 44000
        assert row['realized_pnl'] == 200
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_delete_signal(self, clean_db, create_test_signals):
        """Test deleting a signal"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM signals WHERE id = 1")
        conn.commit()
        
        cursor.execute("SELECT * FROM signals WHERE id = 1")
        row = cursor.fetchone()
        
        assert row is None
        
        conn.close()
        _open_connections.remove(conn)


# ============ QUERY TESTS ============

class TestQueries:
    """Query and filter tests"""
    
    def test_list_signals(self, clean_db, create_test_signals):
        """Test listing signals"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM signals ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        assert len(rows) == create_test_signals
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_filter_by_symbol(self, clean_db, create_test_signals):
        """Test filtering by symbol"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM signals WHERE symbol = 'BTCUSDT'")
        rows = cursor.fetchall()
        
        assert len(rows) == 2  # 2 BTC signals
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_filter_by_status(self, clean_db, create_test_signals):
        """Test filtering by status"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM signals WHERE status = 'active'")
        rows = cursor.fetchall()
        
        assert len(rows) == 2  # 2 active signals
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_filter_by_type(self, clean_db, create_test_signals):
        """Test filtering by type"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM signals WHERE type = 'long'")
        rows = cursor.fetchall()
        
        assert len(rows) == 4  # 4 long signals
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_filter_by_source(self, clean_db, create_test_signals):
        """Test filtering by source"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM signals WHERE source = 'trg'")
        rows = cursor.fetchall()
        
        assert len(rows) == 2  # 2 TRG signals
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_active_signals(self, clean_db, create_test_signals):
        """Test getting active signals"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM signals WHERE status IN ('active', 'pending')")
        rows = cursor.fetchall()
        
        assert len(rows) == 3  # 2 active + 1 pending
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_history_signals(self, clean_db, create_test_signals):
        """Test getting historical signals"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM signals WHERE status IN ('closed', 'cancelled', 'expired')")
        rows = cursor.fetchall()
        
        assert len(rows) == 3  # 2 closed + 1 cancelled
        
        conn.close()
        _open_connections.remove(conn)


# ============ STATISTICS TESTS ============

class TestStatistics:
    """Statistics calculation tests"""
    
    def test_count_by_status(self, clean_db, create_test_signals):
        """Test counting by status"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled
            FROM signals
        """)
        
        row = cursor.fetchone()
        
        assert row['active'] == 2
        assert row['closed'] == 2
        assert row['pending'] == 1
        assert row['cancelled'] == 1
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_pnl_statistics(self, clean_db, create_test_signals):
        """Test PnL statistics"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                SUM(realized_pnl) as total_pnl,
                AVG(realized_pnl) as avg_pnl,
                COUNT(CASE WHEN realized_pnl > 0 THEN 1 END) as win_count,
                COUNT(CASE WHEN realized_pnl < 0 THEN 1 END) as loss_count
            FROM signals 
            WHERE status = 'closed' AND realized_pnl IS NOT NULL
        """)
        
        row = cursor.fetchone()
        
        # Only CLOSED signals: -80 + 150 = 70
        assert row['total_pnl'] == 70.0
        assert row['win_count'] == 1  # SOL +150
        assert row['loss_count'] == 1  # BTC -80
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_win_rate(self, clean_db, create_test_signals):
        """Test win rate calculation"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN realized_pnl > 0 THEN 1 END) as wins,
                COUNT(CASE WHEN realized_pnl < 0 THEN 1 END) as losses
            FROM signals 
            WHERE status = 'closed' AND realized_pnl IS NOT NULL
        """)
        
        row = cursor.fetchone()
        wins = row['wins']
        losses = row['losses']
        
        win_rate = wins / (wins + losses) * 100 if (wins + losses) > 0 else 0
        
        # 1 win, 1 loss = 50%
        assert win_rate == 50.0
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_by_symbol_stats(self, clean_db, create_test_signals):
        """Test statistics by symbol"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                symbol,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed
            FROM signals
            GROUP BY symbol
        """)
        
        results = {row['symbol']: row['total'] for row in cursor.fetchall()}
        
        assert results['BTCUSDT'] == 2
        assert results['ETHUSDT'] == 1
        assert 'SOLUSDT' in results
        
        conn.close()
        _open_connections.remove(conn)


# ============ BATCH OPERATIONS TESTS ============

class TestBatchOperations:
    """Batch operation tests"""
    
    def test_batch_delete(self, clean_db, create_test_signals):
        """Test batch delete"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        # Delete signals 1 and 2
        cursor.execute("DELETE FROM signals WHERE id IN (1, 2)")
        deleted = cursor.rowcount
        conn.commit()
        
        assert deleted == 2
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM signals")
        remaining = cursor.fetchone()[0]
        
        assert remaining == create_test_signals - 2
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_batch_status_update(self, clean_db, create_test_signals):
        """Test batch status update"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # Close pending signals
        cursor.execute("""
            UPDATE signals SET status = 'cancelled', updated_at = ?
            WHERE status = 'pending'
        """, (now,))
        
        updated = cursor.rowcount
        conn.commit()
        
        assert updated == 1
        
        # Verify no pending signals
        cursor.execute("SELECT COUNT(*) FROM signals WHERE status = 'pending'")
        pending = cursor.fetchone()[0]
        
        assert pending == 0
        
        conn.close()
        _open_connections.remove(conn)


# ============ EXPORT TESTS ============

class TestExport:
    """Export tests"""
    
    def test_export_json(self, clean_db, create_test_signals):
        """Test JSON export"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM signals")
        rows = cursor.fetchall()
        
        conn.close()
        _open_connections.remove(conn)
        
        data = [dict(row) for row in rows]
        json_output = json.dumps(data, indent=2, default=str)
        
        assert 'BTCUSDT' in json_output
        assert 'created_at' in json_output
    
    def test_export_csv(self, clean_db, create_test_signals):
        """Test CSV export"""
        import csv
        
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM signals")
        rows = cursor.fetchall()
        
        conn.close()
        _open_connections.remove(conn)
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=dict(rows[0]).keys())
        writer.writeheader()
        
        for row in rows:
            writer.writerow(dict(row))
        
        csv_content = output.getvalue()
        
        assert 'symbol' in csv_content
        assert 'BTCUSDT' in csv_content


# ============ VALIDATION TESTS ============

class TestValidation:
    """Input validation tests"""
    
    def test_signal_create_validation(self, clean_db):
        """Test signal creation validation"""
        from backend.app.api.signals import SignalCreate
        from pydantic import ValidationError
        
        # Valid signal
        signal = SignalCreate(
            symbol="btcusdt",  # Should be uppercased
            timeframe="1h",
            type="long",
            entry_price=42000,
        )
        
        assert signal.symbol == "BTCUSDT"
        
        # Invalid - missing required fields
        with pytest.raises(ValidationError):
            SignalCreate(symbol="BTC", type="long")  # Missing entry_price
        
        # Invalid - negative entry_price
        with pytest.raises(ValidationError):
            SignalCreate(
                symbol="BTC",
                timeframe="1h",
                type="long",
                entry_price=-100
            )
    
    def test_signal_type_enum(self, clean_db):
        """Test signal type enum validation"""
        from backend.app.api.signals import SignalType
        
        assert SignalType.LONG.value == "long"
        assert SignalType.SHORT.value == "short"
    
    def test_signal_status_enum(self, clean_db):
        """Test signal status enum validation"""
        from backend.app.api.signals import SignalStatus
        
        assert SignalStatus.PENDING.value == "pending"
        assert SignalStatus.ACTIVE.value == "active"
        assert SignalStatus.CLOSED.value == "closed"
        assert SignalStatus.CANCELLED.value == "cancelled"
        assert SignalStatus.EXPIRED.value == "expired"


# ============ EDGE CASES ============

class TestEdgeCases:
    """Edge case tests"""
    
    def test_empty_database(self, clean_db):
        """Test queries on empty database"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM signals")
        count = cursor.fetchone()[0]
        
        assert count == 0
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_signal_with_all_tps(self, clean_db):
        """Test signal with all 10 TPs"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO signals (
                symbol, timeframe, type, source, status,
                entry_price, stop_loss,
                tp1, tp2, tp3, tp4, tp5, tp6, tp7, tp8, tp9, tp10,
                leverage, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "BTCUSDT", "1h", "long", "trg", "pending",
            42000, 40000,
            42500, 43000, 43500, 44000, 44500, 45000, 45500, 46000, 46500, 47000,
            10, now, now
        ))
        
        conn.commit()
        
        cursor.execute("SELECT * FROM signals WHERE id = ?", (cursor.lastrowid,))
        row = cursor.fetchone()
        
        assert row['tp1'] == 42500
        assert row['tp10'] == 47000
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_signal_with_json_fields(self, clean_db):
        """Test signal with JSON fields"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        indicator_values = {"rsi": 45, "adx": 32, "supertrend_dir": 1}
        tags = ["high-volume", "breakout", "confirmed"]
        tp_hit = [1, 2]
        
        cursor.execute("""
            INSERT INTO signals (
                symbol, timeframe, type, source, status,
                entry_price, indicator_values, tags, tp_hit,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "BTCUSDT", "1h", "long", "trg", "closed",
            42000, json.dumps(indicator_values), json.dumps(tags), json.dumps(tp_hit),
            now, now
        ))
        
        conn.commit()
        
        cursor.execute("SELECT * FROM signals WHERE id = ?", (cursor.lastrowid,))
        row = cursor.fetchone()
        
        assert json.loads(row['indicator_values']) == indicator_values
        assert json.loads(row['tags']) == tags
        assert json.loads(row['tp_hit']) == [1, 2]
        
        conn.close()
        _open_connections.remove(conn)
    
    def test_duplicate_signals(self, clean_db):
        """Test creating duplicate signals (allowed)"""
        conn = get_test_db_connection()
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        
        # Create two identical signals
        for _ in range(2):
            cursor.execute("""
                INSERT INTO signals (
                    symbol, timeframe, type, source, status,
                    entry_price, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ("BTCUSDT", "1h", "long", "trg", "pending", 42000, now, now))
        
        conn.commit()
        
        cursor.execute("SELECT COUNT(*) FROM signals WHERE symbol = 'BTCUSDT'")
        count = cursor.fetchone()[0]
        
        assert count == 2
        
        conn.close()
        _open_connections.remove(conn)


# ============ RUN TESTS ============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
