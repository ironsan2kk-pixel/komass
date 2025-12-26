"""
Komas Trading Server - Notification Models
==========================================
Pydantic models for Telegram notifications
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class NotificationFormat(str, Enum):
    """Supported message formats"""
    SIMPLE = "simple"
    CORNIX = "cornix"
    CUSTOM = "custom"


class NotificationTrigger(str, Enum):
    """Notification trigger events"""
    NEW_SIGNAL = "new_signal"
    TP_HIT = "tp_hit"
    SL_HIT = "sl_hit"
    SIGNAL_CLOSED = "signal_closed"
    POSITION_UPDATE = "position_update"
    ERROR = "error"


class TelegramSettings(BaseModel):
    """Telegram bot configuration"""
    enabled: bool = False
    bot_token: str = ""
    chat_id: str = ""  # Can be channel ID (e.g., @channel) or numeric ID
    message_format: NotificationFormat = NotificationFormat.SIMPLE
    
    # Trigger settings
    notify_new_signal: bool = True
    notify_tp_hit: bool = True
    notify_sl_hit: bool = True
    notify_signal_closed: bool = True
    notify_errors: bool = False
    
    # Formatting options
    include_chart_link: bool = False
    include_entry_zone: bool = True
    include_leverage: bool = True
    show_all_targets: bool = True
    
    # Custom template (for CUSTOM format)
    custom_template: str = ""


class SignalData(BaseModel):
    """Signal data for notification"""
    id: Optional[int] = None
    symbol: str
    direction: str  # LONG or SHORT
    entry_price: float
    entry_zone_low: Optional[float] = None
    entry_zone_high: Optional[float] = None
    
    # Take profits
    tp_targets: List[float] = []
    tp_amounts: List[float] = []  # Percentage of position for each TP
    
    # Stop loss
    sl_price: float
    sl_percent: Optional[float] = None
    sl_mode: str = "fixed"  # fixed, breakeven, cascade
    
    # Additional info
    leverage: int = 1
    timeframe: str = "1h"
    exchange: str = "binance"
    indicator_name: str = "TRG"
    winrate: Optional[float] = None  # Win rate percentage (e.g., 79)
    
    # Timestamps
    created_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class TPHitData(BaseModel):
    """Take Profit hit notification data"""
    signal_id: int
    symbol: str
    direction: str
    tp_level: int  # 1-10
    tp_price: float
    entry_price: float
    profit_percent: float
    amount_closed: float  # Percentage of position closed
    remaining_position: float  # Remaining position percentage
    timestamp: Optional[datetime] = None


class SLHitData(BaseModel):
    """Stop Loss hit notification data"""
    signal_id: int
    symbol: str
    direction: str
    sl_price: float
    entry_price: float
    loss_percent: float
    sl_mode: str
    timestamp: Optional[datetime] = None


class SignalClosedData(BaseModel):
    """Signal closed notification data"""
    signal_id: int
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    pnl_percent: float
    pnl_usd: Optional[float] = None
    duration_hours: Optional[float] = None
    close_reason: str  # tp_all, sl_hit, manual, signal_reversed
    tp_hits: List[int] = []  # Which TPs were hit
    timestamp: Optional[datetime] = None


class NotificationMessage(BaseModel):
    """Formatted notification message"""
    trigger: NotificationTrigger
    title: str
    body: str
    emoji: str = ""
    parse_mode: Optional[str] = "HTML"  # HTML, Markdown, or None for plain text
    raw_data: Dict[str, Any] = {}


class NotificationResult(BaseModel):
    """Result of sending notification"""
    success: bool
    message_id: Optional[int] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class NotificationTestRequest(BaseModel):
    """Request to test notification"""
    bot_token: str
    chat_id: str
    message_format: NotificationFormat = NotificationFormat.SIMPLE


class NotificationTestResponse(BaseModel):
    """Response from test notification"""
    success: bool
    message: str
    message_id: Optional[int] = None
    bot_info: Optional[Dict[str, Any]] = None


class TelegramBotInfo(BaseModel):
    """Telegram bot information"""
    id: int
    username: str
    first_name: str
    can_join_groups: bool = False
    can_read_all_group_messages: bool = False
    supports_inline_queries: bool = False


class NotificationStats(BaseModel):
    """Notification statistics"""
    total_sent: int = 0
    successful: int = 0
    failed: int = 0
    last_sent: Optional[datetime] = None
    last_error: Optional[str] = None
    
    by_trigger: Dict[str, int] = {
        "new_signal": 0,
        "tp_hit": 0,
        "sl_hit": 0,
        "signal_closed": 0,
        "error": 0
    }
