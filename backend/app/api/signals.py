"""
Komas Trading Server - Signals API
===================================
Complete signal management with CRUD, filtering, pagination, and export.

Endpoints:
- GET  /api/signals/            - List signals with filters
- GET  /api/signals/{id}        - Get signal details
- POST /api/signals/            - Create new signal
- PUT  /api/signals/{id}        - Update signal
- DELETE /api/signals/{id}      - Delete signal
- GET  /api/signals/active      - Get active signals
- GET  /api/signals/history     - Get signal history
- POST /api/signals/batch       - Batch operations
- GET  /api/signals/stats       - Signal statistics
- POST /api/signals/export      - Export to CSV/JSON
- GET  /api/signals/sse/stream  - SSE real-time stream

Author: Komas Trading Team
Version: 1.0.0
"""

import os
import json
import csv
import asyncio
import logging
import sqlite3
from io import StringIO
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Literal
from pathlib import Path
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, field_validator, ConfigDict

# ============ CONFIGURATION ============

router = APIRouter(prefix="/api/signals", tags=["Signals Management"])
logger = logging.getLogger(__name__)

# Database path
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_FILE = DB_DIR / "komas_signals.db"

# Active signal subscribers for SSE
signal_subscribers: List[asyncio.Queue] = []


# ============ ENUMS ============

class SignalType(str, Enum):
    LONG = "long"
    SHORT = "short"


class SignalStatus(str, Enum):
    PENDING = "pending"        # Signal generated, not yet acted on
    ACTIVE = "active"          # Signal is active (position opened)
    CLOSED = "closed"          # Signal closed (TP/SL hit or manual)
    CANCELLED = "cancelled"    # Signal cancelled before activation
    EXPIRED = "expired"        # Signal expired (time limit reached)


class SignalSource(str, Enum):
    TRG = "trg"                # TRG Indicator
    SUPERTREND = "supertrend"  # SuperTrend filter
    RSI = "rsi"                # RSI filter
    MANUAL = "manual"          # Manual signal
    BOT = "bot"                # Trading bot
    EXTERNAL = "external"      # External source (Telegram, etc.)


class CloseReason(str, Enum):
    TP1 = "tp1"
    TP2 = "tp2"
    TP3 = "tp3"
    TP4 = "tp4"
    TP5 = "tp5"
    TP6 = "tp6"
    TP7 = "tp7"
    TP8 = "tp8"
    TP9 = "tp9"
    TP10 = "tp10"
    SL = "sl"
    MANUAL = "manual"
    EXPIRED = "expired"
    REVERSAL = "reversal"


class ExportFormat(str, Enum):
    CSV = "csv"
    JSON = "json"


class BatchOperation(str, Enum):
    DELETE = "delete"
    UPDATE_STATUS = "update_status"
    CLOSE = "close"


# ============ PYDANTIC MODELS ============

class SignalCreate(BaseModel):
    """Model for creating a new signal"""
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading pair (e.g., BTCUSDT)")
    timeframe: str = Field(..., min_length=2, max_length=5, description="Timeframe (e.g., 1h, 4h)")
    type: SignalType = Field(..., description="Signal type: long or short")
    source: SignalSource = Field(default=SignalSource.TRG, description="Signal source")
    
    entry_price: float = Field(..., gt=0, description="Entry price")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
    
    # Take profit levels (up to 10)
    tp1: Optional[float] = Field(None, gt=0)
    tp2: Optional[float] = Field(None, gt=0)
    tp3: Optional[float] = Field(None, gt=0)
    tp4: Optional[float] = Field(None, gt=0)
    tp5: Optional[float] = Field(None, gt=0)
    tp6: Optional[float] = Field(None, gt=0)
    tp7: Optional[float] = Field(None, gt=0)
    tp8: Optional[float] = Field(None, gt=0)
    tp9: Optional[float] = Field(None, gt=0)
    tp10: Optional[float] = Field(None, gt=0)
    
    # Position sizing
    leverage: float = Field(default=1.0, ge=1, le=125, description="Leverage (1-125)")
    position_size: Optional[float] = Field(None, gt=0, description="Position size in USDT")
    risk_percent: Optional[float] = Field(None, gt=0, le=100, description="Risk percent of portfolio")
    
    # Metadata
    indicator_values: Optional[Dict[str, Any]] = Field(None, description="Indicator values at signal time")
    notes: Optional[str] = Field(None, max_length=1000, description="Additional notes")
    tags: Optional[List[str]] = Field(None, description="Tags for filtering")
    expires_at: Optional[str] = Field(None, description="Expiration time (ISO format)")
    
    @field_validator('symbol')
    @classmethod
    def symbol_upper(cls, v):
        return v.upper()
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "type": "long",
                "source": "trg",
                "entry_price": 42000.0,
                "stop_loss": 40000.0,
                "tp1": 43000.0,
                "tp2": 44000.0,
                "tp3": 45000.0,
                "leverage": 10,
                "position_size": 1000.0,
                "notes": "TRG crossover with strong volume"
            }
        }
    )


class SignalUpdate(BaseModel):
    """Model for updating a signal"""
    status: Optional[SignalStatus] = None
    entry_price: Optional[float] = Field(None, gt=0)
    stop_loss: Optional[float] = Field(None, gt=0)
    tp1: Optional[float] = Field(None, gt=0)
    tp2: Optional[float] = Field(None, gt=0)
    tp3: Optional[float] = Field(None, gt=0)
    tp4: Optional[float] = Field(None, gt=0)
    tp5: Optional[float] = Field(None, gt=0)
    tp6: Optional[float] = Field(None, gt=0)
    tp7: Optional[float] = Field(None, gt=0)
    tp8: Optional[float] = Field(None, gt=0)
    tp9: Optional[float] = Field(None, gt=0)
    tp10: Optional[float] = Field(None, gt=0)
    exit_price: Optional[float] = Field(None, gt=0)
    close_reason: Optional[CloseReason] = None
    realized_pnl: Optional[float] = None
    realized_pnl_percent: Optional[float] = None
    notes: Optional[str] = Field(None, max_length=1000)
    tags: Optional[List[str]] = None


class SignalResponse(BaseModel):
    """Response model for a signal"""
    id: int
    symbol: str
    timeframe: str
    type: str
    source: str
    status: str
    
    entry_price: float
    stop_loss: Optional[float]
    exit_price: Optional[float]
    
    tp1: Optional[float]
    tp2: Optional[float]
    tp3: Optional[float]
    tp4: Optional[float]
    tp5: Optional[float]
    tp6: Optional[float]
    tp7: Optional[float]
    tp8: Optional[float]
    tp9: Optional[float]
    tp10: Optional[float]
    
    tp_hit: Optional[List[int]]  # List of hit TP levels
    close_reason: Optional[str]
    
    leverage: float
    position_size: Optional[float]
    risk_percent: Optional[float]
    
    realized_pnl: Optional[float]
    realized_pnl_percent: Optional[float]
    
    indicator_values: Optional[Dict[str, Any]]
    notes: Optional[str]
    tags: Optional[List[str]]
    
    created_at: str
    updated_at: str
    activated_at: Optional[str]
    closed_at: Optional[str]
    expires_at: Optional[str]


class SignalListResponse(BaseModel):
    """Response model for signal list"""
    success: bool = True
    total: int
    page: int
    per_page: int
    total_pages: int
    signals: List[SignalResponse]


class SignalStatsResponse(BaseModel):
    """Response model for signal statistics"""
    success: bool = True
    total_signals: int
    active_signals: int
    closed_signals: int
    pending_signals: int
    cancelled_signals: int
    expired_signals: int
    
    # Performance
    total_pnl: float
    avg_pnl: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    
    # By type
    long_signals: int
    short_signals: int
    long_win_rate: float
    short_win_rate: float
    
    # By symbol
    symbols_stats: Dict[str, Dict[str, Any]]
    
    # By timeframe
    timeframe_stats: Dict[str, Dict[str, Any]]
    
    # By source
    source_stats: Dict[str, Dict[str, Any]]
    
    # Time-based
    today_signals: int
    week_signals: int
    month_signals: int


class BatchRequest(BaseModel):
    """Request model for batch operations"""
    operation: BatchOperation
    signal_ids: List[int]
    update_data: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operation": "delete",
                "signal_ids": [1, 2, 3]
            }
        }
    )


class ExportRequest(BaseModel):
    """Request model for export"""
    format: ExportFormat = ExportFormat.CSV
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    symbols: Optional[List[str]] = None
    types: Optional[List[SignalType]] = None
    statuses: Optional[List[SignalStatus]] = None
    sources: Optional[List[SignalSource]] = None
    include_fields: Optional[List[str]] = None


# ============ DATABASE FUNCTIONS ============

def get_db_connection():
    """Get SQLite connection with row factory"""
    conn = sqlite3.connect(str(DB_FILE), timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize signals database table"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            type TEXT NOT NULL,
            source TEXT NOT NULL DEFAULT 'trg',
            status TEXT NOT NULL DEFAULT 'pending',
            
            entry_price REAL NOT NULL,
            stop_loss REAL,
            exit_price REAL,
            
            tp1 REAL, tp2 REAL, tp3 REAL, tp4 REAL, tp5 REAL,
            tp6 REAL, tp7 REAL, tp8 REAL, tp9 REAL, tp10 REAL,
            
            tp_hit TEXT,  -- JSON list of hit TP levels
            close_reason TEXT,
            
            leverage REAL DEFAULT 1.0,
            position_size REAL,
            risk_percent REAL,
            
            realized_pnl REAL,
            realized_pnl_percent REAL,
            
            indicator_values TEXT,  -- JSON
            notes TEXT,
            tags TEXT,  -- JSON list
            
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            activated_at TEXT,
            closed_at TEXT,
            expires_at TEXT
        )
    """)
    
    # Create indexes for faster queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_status ON signals(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_type ON signals(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_source ON signals(source)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_timeframe ON signals(timeframe)")
    
    conn.commit()
    conn.close()
    
    logger.info(f"Database initialized: {DB_FILE}")


def row_to_signal(row: sqlite3.Row) -> SignalResponse:
    """Convert database row to SignalResponse"""
    data = dict(row)
    
    # Parse JSON fields
    if data.get('tp_hit'):
        try:
            data['tp_hit'] = json.loads(data['tp_hit'])
        except:
            data['tp_hit'] = None
    
    if data.get('indicator_values'):
        try:
            data['indicator_values'] = json.loads(data['indicator_values'])
        except:
            data['indicator_values'] = None
    
    if data.get('tags'):
        try:
            data['tags'] = json.loads(data['tags'])
        except:
            data['tags'] = None
    
    return SignalResponse(**data)


# Initialize database on module load
init_database()


# ============ NOTIFICATION HELPERS ============

async def notify_signal_event(event_type: str, signal: SignalResponse):
    """Notify all SSE subscribers about signal event"""
    message = {
        "event": event_type,
        "signal": signal.dict(),
        "timestamp": datetime.now().isoformat()
    }
    
    dead_subscribers = []
    for queue in signal_subscribers:
        try:
            await queue.put(message)
        except:
            dead_subscribers.append(queue)
    
    # Clean up dead subscribers
    for queue in dead_subscribers:
        signal_subscribers.remove(queue)


async def check_expired_signals():
    """Background task to check and update expired signals"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute("""
        UPDATE signals 
        SET status = 'expired', updated_at = ?, closed_at = ?
        WHERE status IN ('pending', 'active') 
        AND expires_at IS NOT NULL 
        AND expires_at < ?
    """, (now, now, now))
    
    expired_count = cursor.rowcount
    conn.commit()
    conn.close()
    
    if expired_count > 0:
        logger.info(f"Expired {expired_count} signals")
    
    return expired_count


# ============ CRUD ENDPOINTS ============

@router.get("/", response_model=SignalListResponse)
async def list_signals(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe"),
    type: Optional[SignalType] = Query(None, description="Filter by signal type"),
    status: Optional[SignalStatus] = Query(None, description="Filter by status"),
    source: Optional[SignalSource] = Query(None, description="Filter by source"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
):
    """
    List signals with filtering and pagination.
    
    - **page**: Page number (1-based)
    - **per_page**: Number of items per page (1-100)
    - **symbol**: Filter by trading pair
    - **timeframe**: Filter by timeframe (1h, 4h, etc.)
    - **type**: Filter by signal type (long/short)
    - **status**: Filter by status (pending/active/closed/cancelled/expired)
    - **source**: Filter by source (trg/supertrend/rsi/manual/bot/external)
    - **start_date**: Filter signals created after this date
    - **end_date**: Filter signals created before this date
    - **sort_by**: Field to sort by
    - **sort_order**: Sort direction (asc/desc)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build query
    where_clauses = []
    params = []
    
    if symbol:
        where_clauses.append("symbol = ?")
        params.append(symbol.upper())
    
    if timeframe:
        where_clauses.append("timeframe = ?")
        params.append(timeframe)
    
    if type:
        where_clauses.append("type = ?")
        params.append(type.value)
    
    if status:
        where_clauses.append("status = ?")
        params.append(status.value)
    
    if source:
        where_clauses.append("source = ?")
        params.append(source.value)
    
    if start_date:
        where_clauses.append("created_at >= ?")
        params.append(start_date)
    
    if end_date:
        where_clauses.append("created_at <= ?")
        params.append(end_date)
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    # Validate sort field
    valid_sort_fields = [
        "id", "symbol", "timeframe", "type", "status", "source",
        "entry_price", "realized_pnl", "created_at", "updated_at"
    ]
    if sort_by not in valid_sort_fields:
        sort_by = "created_at"
    
    if sort_order.lower() not in ("asc", "desc"):
        sort_order = "desc"
    
    # Count total
    cursor.execute(f"SELECT COUNT(*) FROM signals WHERE {where_sql}", params)
    total = cursor.fetchone()[0]
    
    # Calculate pagination
    total_pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page
    
    # Fetch page
    query = f"""
        SELECT * FROM signals 
        WHERE {where_sql}
        ORDER BY {sort_by} {sort_order}
        LIMIT ? OFFSET ?
    """
    cursor.execute(query, params + [per_page, offset])
    rows = cursor.fetchall()
    conn.close()
    
    signals = [row_to_signal(row) for row in rows]
    
    return SignalListResponse(
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        signals=signals
    )


@router.get("/active", response_model=SignalListResponse)
async def get_active_signals(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
):
    """
    Get all active signals (status = 'active' or 'pending').
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if symbol:
        cursor.execute(
            "SELECT * FROM signals WHERE status IN ('active', 'pending') AND symbol = ? ORDER BY created_at DESC",
            (symbol.upper(),)
        )
    else:
        cursor.execute(
            "SELECT * FROM signals WHERE status IN ('active', 'pending') ORDER BY created_at DESC"
        )
    
    rows = cursor.fetchall()
    conn.close()
    
    signals = [row_to_signal(row) for row in rows]
    
    return SignalListResponse(
        total=len(signals),
        page=1,
        per_page=len(signals),
        total_pages=1,
        signals=signals
    )


@router.get("/history", response_model=SignalListResponse)
async def get_signal_history(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    """
    Get signal history (closed, cancelled, expired signals).
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days)).isoformat()
    
    where_clauses = [
        "status IN ('closed', 'cancelled', 'expired')",
        "created_at >= ?"
    ]
    params = [start_date]
    
    if symbol:
        where_clauses.append("symbol = ?")
        params.append(symbol.upper())
    
    where_sql = " AND ".join(where_clauses)
    
    # Count
    cursor.execute(f"SELECT COUNT(*) FROM signals WHERE {where_sql}", params)
    total = cursor.fetchone()[0]
    
    total_pages = max(1, (total + per_page - 1) // per_page)
    offset = (page - 1) * per_page
    
    cursor.execute(
        f"SELECT * FROM signals WHERE {where_sql} ORDER BY closed_at DESC LIMIT ? OFFSET ?",
        params + [per_page, offset]
    )
    rows = cursor.fetchall()
    conn.close()
    
    signals = [row_to_signal(row) for row in rows]
    
    return SignalListResponse(
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        signals=signals
    )


@router.get("/stats", response_model=SignalStatsResponse)
async def get_signal_stats(
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
):
    """
    Get comprehensive signal statistics.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    start_date = (datetime.now() - timedelta(days=days)).isoformat()
    today = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    month_ago = (datetime.now() - timedelta(days=30)).isoformat()
    
    base_where = "created_at >= ?"
    params = [start_date]
    
    if symbol:
        base_where += " AND symbol = ?"
        params.append(symbol.upper())
    
    # Total counts by status
    cursor.execute(f"""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
            SUM(CASE WHEN status = 'expired' THEN 1 ELSE 0 END) as expired
        FROM signals WHERE {base_where}
    """, params)
    
    status_row = cursor.fetchone()
    total = status_row['total'] or 0
    active = status_row['active'] or 0
    closed = status_row['closed'] or 0
    pending = status_row['pending'] or 0
    cancelled = status_row['cancelled'] or 0
    expired = status_row['expired'] or 0
    
    # PnL stats for closed signals
    cursor.execute(f"""
        SELECT 
            COALESCE(SUM(realized_pnl), 0) as total_pnl,
            COALESCE(AVG(realized_pnl), 0) as avg_pnl,
            COALESCE(SUM(CASE WHEN realized_pnl > 0 THEN realized_pnl ELSE 0 END), 0) as total_wins,
            COALESCE(SUM(CASE WHEN realized_pnl < 0 THEN realized_pnl ELSE 0 END), 0) as total_losses,
            COUNT(CASE WHEN realized_pnl > 0 THEN 1 END) as win_count,
            COUNT(CASE WHEN realized_pnl < 0 THEN 1 END) as loss_count,
            COALESCE(AVG(CASE WHEN realized_pnl > 0 THEN realized_pnl END), 0) as avg_win,
            COALESCE(AVG(CASE WHEN realized_pnl < 0 THEN realized_pnl END), 0) as avg_loss
        FROM signals 
        WHERE {base_where} AND status = 'closed' AND realized_pnl IS NOT NULL
    """, params)
    
    pnl_row = cursor.fetchone()
    total_pnl = pnl_row['total_pnl'] or 0
    avg_pnl = pnl_row['avg_pnl'] or 0
    total_wins = pnl_row['total_wins'] or 0
    total_losses = abs(pnl_row['total_losses'] or 0)
    win_count = pnl_row['win_count'] or 0
    loss_count = pnl_row['loss_count'] or 0
    avg_win = pnl_row['avg_win'] or 0
    avg_loss = pnl_row['avg_loss'] or 0
    
    win_rate = (win_count / (win_count + loss_count) * 100) if (win_count + loss_count) > 0 else 0
    profit_factor = (total_wins / total_losses) if total_losses > 0 else 999
    
    # By type
    cursor.execute(f"""
        SELECT 
            SUM(CASE WHEN type = 'long' THEN 1 ELSE 0 END) as long_count,
            SUM(CASE WHEN type = 'short' THEN 1 ELSE 0 END) as short_count,
            SUM(CASE WHEN type = 'long' AND status = 'closed' AND realized_pnl > 0 THEN 1 ELSE 0 END) as long_wins,
            SUM(CASE WHEN type = 'long' AND status = 'closed' THEN 1 ELSE 0 END) as long_closed,
            SUM(CASE WHEN type = 'short' AND status = 'closed' AND realized_pnl > 0 THEN 1 ELSE 0 END) as short_wins,
            SUM(CASE WHEN type = 'short' AND status = 'closed' THEN 1 ELSE 0 END) as short_closed
        FROM signals WHERE {base_where}
    """, params)
    
    type_row = cursor.fetchone()
    long_signals = type_row['long_count'] or 0
    short_signals = type_row['short_count'] or 0
    long_wins = type_row['long_wins'] or 0
    long_closed = type_row['long_closed'] or 0
    short_wins = type_row['short_wins'] or 0
    short_closed = type_row['short_closed'] or 0
    
    long_win_rate = (long_wins / long_closed * 100) if long_closed > 0 else 0
    short_win_rate = (short_wins / short_closed * 100) if short_closed > 0 else 0
    
    # By symbol
    cursor.execute(f"""
        SELECT 
            symbol,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'closed' AND realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed,
            COALESCE(SUM(realized_pnl), 0) as pnl
        FROM signals 
        WHERE {base_where}
        GROUP BY symbol
    """, params)
    
    symbols_stats = {}
    for row in cursor.fetchall():
        sym = row['symbol']
        symbols_stats[sym] = {
            "total": row['total'],
            "closed": row['closed'],
            "win_rate": (row['wins'] / row['closed'] * 100) if row['closed'] > 0 else 0,
            "pnl": row['pnl']
        }
    
    # By timeframe
    cursor.execute(f"""
        SELECT 
            timeframe,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'closed' AND realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed,
            COALESCE(SUM(realized_pnl), 0) as pnl
        FROM signals 
        WHERE {base_where}
        GROUP BY timeframe
    """, params)
    
    timeframe_stats = {}
    for row in cursor.fetchall():
        tf = row['timeframe']
        timeframe_stats[tf] = {
            "total": row['total'],
            "closed": row['closed'],
            "win_rate": (row['wins'] / row['closed'] * 100) if row['closed'] > 0 else 0,
            "pnl": row['pnl']
        }
    
    # By source
    cursor.execute(f"""
        SELECT 
            source,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'closed' AND realized_pnl > 0 THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed,
            COALESCE(SUM(realized_pnl), 0) as pnl
        FROM signals 
        WHERE {base_where}
        GROUP BY source
    """, params)
    
    source_stats = {}
    for row in cursor.fetchall():
        src = row['source']
        source_stats[src] = {
            "total": row['total'],
            "closed": row['closed'],
            "win_rate": (row['wins'] / row['closed'] * 100) if row['closed'] > 0 else 0,
            "pnl": row['pnl']
        }
    
    # Time-based counts
    cursor.execute(f"""
        SELECT 
            SUM(CASE WHEN created_at >= ? THEN 1 ELSE 0 END) as today,
            SUM(CASE WHEN created_at >= ? THEN 1 ELSE 0 END) as week,
            SUM(CASE WHEN created_at >= ? THEN 1 ELSE 0 END) as month
        FROM signals WHERE {base_where}
    """, params + [today, week_ago, month_ago])
    
    time_row = cursor.fetchone()
    today_signals = time_row['today'] or 0
    week_signals = time_row['week'] or 0
    month_signals = time_row['month'] or 0
    
    conn.close()
    
    return SignalStatsResponse(
        total_signals=total,
        active_signals=active,
        closed_signals=closed,
        pending_signals=pending,
        cancelled_signals=cancelled,
        expired_signals=expired,
        total_pnl=round(total_pnl, 2),
        avg_pnl=round(avg_pnl, 2),
        win_rate=round(win_rate, 2),
        profit_factor=round(profit_factor, 2),
        avg_win=round(avg_win, 2),
        avg_loss=round(avg_loss, 2),
        long_signals=long_signals,
        short_signals=short_signals,
        long_win_rate=round(long_win_rate, 2),
        short_win_rate=round(short_win_rate, 2),
        symbols_stats=symbols_stats,
        timeframe_stats=timeframe_stats,
        source_stats=source_stats,
        today_signals=today_signals,
        week_signals=week_signals,
        month_signals=month_signals
    )


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: int):
    """
    Get signal by ID.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
    
    return row_to_signal(row)


@router.post("/", response_model=SignalResponse, status_code=201)
async def create_signal(
    signal: SignalCreate,
    background_tasks: BackgroundTasks,
):
    """
    Create a new signal.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Prepare JSON fields
    indicator_values_json = json.dumps(signal.indicator_values) if signal.indicator_values else None
    tags_json = json.dumps(signal.tags) if signal.tags else None
    
    cursor.execute("""
        INSERT INTO signals (
            symbol, timeframe, type, source, status,
            entry_price, stop_loss,
            tp1, tp2, tp3, tp4, tp5, tp6, tp7, tp8, tp9, tp10,
            leverage, position_size, risk_percent,
            indicator_values, notes, tags,
            created_at, updated_at, expires_at
        ) VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        signal.symbol.upper(),
        signal.timeframe,
        signal.type.value,
        signal.source.value,
        signal.entry_price,
        signal.stop_loss,
        signal.tp1, signal.tp2, signal.tp3, signal.tp4, signal.tp5,
        signal.tp6, signal.tp7, signal.tp8, signal.tp9, signal.tp10,
        signal.leverage,
        signal.position_size,
        signal.risk_percent,
        indicator_values_json,
        signal.notes,
        tags_json,
        now,
        now,
        signal.expires_at
    ))
    
    signal_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
    row = cursor.fetchone()
    conn.close()
    
    created_signal = row_to_signal(row)
    
    # Notify subscribers
    background_tasks.add_task(notify_signal_event, "created", created_signal)
    
    logger.info(f"Created signal #{signal_id}: {signal.symbol} {signal.type.value}")
    
    return created_signal


@router.put("/{signal_id}", response_model=SignalResponse)
async def update_signal(
    signal_id: int,
    update: SignalUpdate,
    background_tasks: BackgroundTasks,
):
    """
    Update a signal.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check exists
    cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
    
    # Build update query
    update_fields = []
    update_values = []
    
    now = datetime.now().isoformat()
    
    if update.status is not None:
        update_fields.append("status = ?")
        update_values.append(update.status.value)
        
        # Set activated_at if becoming active
        if update.status == SignalStatus.ACTIVE and not row['activated_at']:
            update_fields.append("activated_at = ?")
            update_values.append(now)
        
        # Set closed_at if closing
        if update.status in (SignalStatus.CLOSED, SignalStatus.CANCELLED, SignalStatus.EXPIRED):
            update_fields.append("closed_at = ?")
            update_values.append(now)
    
    for field in ['entry_price', 'stop_loss', 'exit_price',
                  'tp1', 'tp2', 'tp3', 'tp4', 'tp5', 'tp6', 'tp7', 'tp8', 'tp9', 'tp10',
                  'realized_pnl', 'realized_pnl_percent', 'notes']:
        value = getattr(update, field, None)
        if value is not None:
            update_fields.append(f"{field} = ?")
            update_values.append(value)
    
    if update.close_reason is not None:
        update_fields.append("close_reason = ?")
        update_values.append(update.close_reason.value)
    
    if update.tags is not None:
        update_fields.append("tags = ?")
        update_values.append(json.dumps(update.tags))
    
    if not update_fields:
        conn.close()
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_fields.append("updated_at = ?")
    update_values.append(now)
    
    update_values.append(signal_id)
    
    query = f"UPDATE signals SET {', '.join(update_fields)} WHERE id = ?"
    cursor.execute(query, update_values)
    conn.commit()
    
    cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
    row = cursor.fetchone()
    conn.close()
    
    updated_signal = row_to_signal(row)
    
    # Notify subscribers
    background_tasks.add_task(notify_signal_event, "updated", updated_signal)
    
    logger.info(f"Updated signal #{signal_id}")
    
    return updated_signal


@router.delete("/{signal_id}")
async def delete_signal(
    signal_id: int,
    background_tasks: BackgroundTasks,
):
    """
    Delete a signal.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM signals WHERE id = ?", (signal_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found")
    
    deleted_signal = row_to_signal(row)
    
    cursor.execute("DELETE FROM signals WHERE id = ?", (signal_id,))
    conn.commit()
    conn.close()
    
    # Notify subscribers
    background_tasks.add_task(notify_signal_event, "deleted", deleted_signal)
    
    logger.info(f"Deleted signal #{signal_id}")
    
    return {"success": True, "message": f"Signal {signal_id} deleted"}


# ============ BATCH OPERATIONS ============

@router.post("/batch")
async def batch_operation(
    request: BatchRequest,
    background_tasks: BackgroundTasks,
):
    """
    Perform batch operations on multiple signals.
    
    Operations:
    - **delete**: Delete multiple signals
    - **update_status**: Update status of multiple signals
    - **close**: Close multiple signals with specified reason
    """
    if not request.signal_ids:
        raise HTTPException(status_code=400, detail="No signal IDs provided")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    results = {"success": [], "errors": []}
    
    if request.operation == BatchOperation.DELETE:
        for signal_id in request.signal_ids:
            try:
                cursor.execute("DELETE FROM signals WHERE id = ?", (signal_id,))
                if cursor.rowcount > 0:
                    results["success"].append(signal_id)
                else:
                    results["errors"].append({"id": signal_id, "error": "Not found"})
            except Exception as e:
                results["errors"].append({"id": signal_id, "error": str(e)})
    
    elif request.operation == BatchOperation.UPDATE_STATUS:
        new_status = request.update_data.get("status") if request.update_data else None
        if not new_status:
            conn.close()
            raise HTTPException(status_code=400, detail="Status not provided in update_data")
        
        for signal_id in request.signal_ids:
            try:
                update_sql = "UPDATE signals SET status = ?, updated_at = ?"
                params = [new_status, now]
                
                if new_status == "active":
                    update_sql += ", activated_at = ?"
                    params.append(now)
                elif new_status in ("closed", "cancelled", "expired"):
                    update_sql += ", closed_at = ?"
                    params.append(now)
                
                update_sql += " WHERE id = ?"
                params.append(signal_id)
                
                cursor.execute(update_sql, params)
                if cursor.rowcount > 0:
                    results["success"].append(signal_id)
                else:
                    results["errors"].append({"id": signal_id, "error": "Not found"})
            except Exception as e:
                results["errors"].append({"id": signal_id, "error": str(e)})
    
    elif request.operation == BatchOperation.CLOSE:
        close_reason = request.update_data.get("close_reason", "manual") if request.update_data else "manual"
        exit_price = request.update_data.get("exit_price") if request.update_data else None
        
        for signal_id in request.signal_ids:
            try:
                update_sql = """
                    UPDATE signals SET 
                        status = 'closed',
                        close_reason = ?,
                        closed_at = ?,
                        updated_at = ?
                """
                params = [close_reason, now, now]
                
                if exit_price:
                    update_sql += ", exit_price = ?"
                    params.append(exit_price)
                
                update_sql += " WHERE id = ?"
                params.append(signal_id)
                
                cursor.execute(update_sql, params)
                if cursor.rowcount > 0:
                    results["success"].append(signal_id)
                else:
                    results["errors"].append({"id": signal_id, "error": "Not found"})
            except Exception as e:
                results["errors"].append({"id": signal_id, "error": str(e)})
    
    conn.commit()
    conn.close()
    
    logger.info(f"Batch {request.operation.value}: {len(results['success'])} success, {len(results['errors'])} errors")
    
    return {
        "success": True,
        "operation": request.operation.value,
        "results": results
    }


# ============ EXPORT ============

@router.post("/export")
async def export_signals(request: ExportRequest):
    """
    Export signals to CSV or JSON.
    
    - **format**: Export format (csv or json)
    - **start_date**: Filter by start date
    - **end_date**: Filter by end date
    - **symbols**: Filter by symbols
    - **types**: Filter by signal types
    - **statuses**: Filter by statuses
    - **sources**: Filter by sources
    - **include_fields**: List of fields to include (all if not specified)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Build query
    where_clauses = []
    params = []
    
    if request.start_date:
        where_clauses.append("created_at >= ?")
        params.append(request.start_date)
    
    if request.end_date:
        where_clauses.append("created_at <= ?")
        params.append(request.end_date)
    
    if request.symbols:
        placeholders = ",".join(["?" for _ in request.symbols])
        where_clauses.append(f"symbol IN ({placeholders})")
        params.extend([s.upper() for s in request.symbols])
    
    if request.types:
        placeholders = ",".join(["?" for _ in request.types])
        where_clauses.append(f"type IN ({placeholders})")
        params.extend([t.value for t in request.types])
    
    if request.statuses:
        placeholders = ",".join(["?" for _ in request.statuses])
        where_clauses.append(f"status IN ({placeholders})")
        params.extend([s.value for s in request.statuses])
    
    if request.sources:
        placeholders = ",".join(["?" for _ in request.sources])
        where_clauses.append(f"source IN ({placeholders})")
        params.extend([s.value for s in request.sources])
    
    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    cursor.execute(f"SELECT * FROM signals WHERE {where_sql} ORDER BY created_at DESC", params)
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No signals found matching criteria")
    
    # Convert to list of dicts
    signals_data = []
    for row in rows:
        data = dict(row)
        
        # Parse JSON fields
        if data.get('tp_hit'):
            try:
                data['tp_hit'] = json.loads(data['tp_hit'])
            except:
                pass
        if data.get('indicator_values'):
            try:
                data['indicator_values'] = json.loads(data['indicator_values'])
            except:
                pass
        if data.get('tags'):
            try:
                data['tags'] = json.loads(data['tags'])
            except:
                pass
        
        # Filter fields if specified
        if request.include_fields:
            data = {k: v for k, v in data.items() if k in request.include_fields}
        
        signals_data.append(data)
    
    # Generate export
    if request.format == ExportFormat.JSON:
        content = json.dumps(signals_data, indent=2, ensure_ascii=False, default=str)
        media_type = "application/json"
        filename = f"signals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    else:  # CSV
        if not signals_data:
            raise HTTPException(status_code=404, detail="No data to export")
        
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=signals_data[0].keys())
        writer.writeheader()
        
        for signal in signals_data:
            # Flatten complex fields for CSV
            row = {}
            for k, v in signal.items():
                if isinstance(v, (list, dict)):
                    row[k] = json.dumps(v)
                else:
                    row[k] = v
            writer.writerow(row)
        
        content = output.getvalue()
        media_type = "text/csv"
        filename = f"signals_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    
    return Response(
        content=content,
        media_type=media_type,
        headers=headers
    )


# ============ SSE STREAMING ============

@router.get("/sse/stream")
async def signal_stream():
    """
    Server-Sent Events stream for real-time signal updates.
    
    Events:
    - **created**: New signal created
    - **updated**: Signal updated
    - **deleted**: Signal deleted
    - **ping**: Keep-alive ping
    """
    queue = asyncio.Queue()
    signal_subscribers.append(queue)
    
    async def event_generator():
        try:
            while True:
                try:
                    # Wait for message with timeout for ping
                    message = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"event: {message['event']}\n"
                    yield f"data: {json.dumps(message)}\n\n"
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    yield f"event: ping\n"
                    yield f"data: {json.dumps({'timestamp': datetime.now().isoformat()})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            if queue in signal_subscribers:
                signal_subscribers.remove(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============ UTILITY ENDPOINTS ============

@router.post("/check-expired")
async def trigger_expire_check():
    """
    Manually trigger check for expired signals.
    """
    expired = await check_expired_signals()
    return {"success": True, "expired_count": expired}


@router.get("/symbols")
async def get_available_symbols():
    """
    Get list of symbols with signals.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT symbol, COUNT(*) as count, MAX(created_at) as last_signal
        FROM signals
        GROUP BY symbol
        ORDER BY count DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    symbols = [
        {
            "symbol": row['symbol'],
            "count": row['count'],
            "last_signal": row['last_signal']
        }
        for row in rows
    ]
    
    return {"success": True, "symbols": symbols}


@router.get("/timeframes")
async def get_available_timeframes():
    """
    Get list of timeframes with signals.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT timeframe, COUNT(*) as count
        FROM signals
        GROUP BY timeframe
        ORDER BY count DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    timeframes = [
        {"timeframe": row['timeframe'], "count": row['count']}
        for row in rows
    ]
    
    return {"success": True, "timeframes": timeframes}


@router.delete("/all")
async def delete_all_signals(confirm: bool = Query(False, description="Must be true to confirm")):
    """
    Delete ALL signals (requires confirmation).
    
    ⚠️ This action is irreversible!
    """
    if not confirm:
        raise HTTPException(
            status_code=400, 
            detail="Must pass confirm=true to delete all signals"
        )
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM signals")
    count = cursor.fetchone()[0]
    
    cursor.execute("DELETE FROM signals")
    conn.commit()
    conn.close()
    
    logger.warning(f"Deleted ALL {count} signals")
    
    return {"success": True, "deleted_count": count}
