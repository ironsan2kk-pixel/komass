"""
Komas Trading Server - Bots Models
==================================
Pydantic models for trading bots system
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid


# ============ ENUMS ============

class BotStatus(str, Enum):
    """Bot running status"""
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class SignalDirection(str, Enum):
    """Trading signal direction"""
    LONG = "long"
    SHORT = "short"
    CLOSE = "close"


class PositionStatus(str, Enum):
    """Position status"""
    OPEN = "open"
    CLOSED = "closed"
    PARTIALLY_CLOSED = "partially_closed"


class TakeProfitMode(str, Enum):
    """Take profit handling mode"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


class StopLossMode(str, Enum):
    """Stop loss mode"""
    FIXED = "fixed"
    BREAKEVEN = "breakeven"
    CASCADE = "cascade"


# ============ STRATEGY CONFIGURATION ============

class TakeProfitLevel(BaseModel):
    """Single take profit level configuration"""
    level: int = Field(..., ge=1, le=10, description="TP level number (1-10)")
    percent: float = Field(..., gt=0, le=100, description="TP percent from entry")
    amount: float = Field(..., gt=0, le=100, description="% of position to close")


class StrategyConfig(BaseModel):
    """Strategy configuration for a bot"""
    # TRG Indicator
    indicator: str = Field(default="trg", description="Indicator name")
    atr_length: int = Field(default=45, ge=10, le=200)
    multiplier: float = Field(default=4.0, ge=1.0, le=10.0)
    
    # Take Profits
    tp_count: int = Field(default=4, ge=1, le=10)
    tp_mode: TakeProfitMode = Field(default=TakeProfitMode.SEQUENTIAL)
    take_profits: List[TakeProfitLevel] = Field(default_factory=list)
    
    # Stop Loss
    sl_percent: float = Field(default=2.0, ge=0.1, le=50.0)
    sl_mode: StopLossMode = Field(default=StopLossMode.FIXED)
    
    # Filters
    use_supertrend: bool = Field(default=False)
    supertrend_period: int = Field(default=10)
    supertrend_multiplier: float = Field(default=3.0)
    
    use_rsi: bool = Field(default=False)
    rsi_period: int = Field(default=14)
    rsi_overbought: int = Field(default=70)
    rsi_oversold: int = Field(default=30)
    
    use_adx: bool = Field(default=False)
    adx_period: int = Field(default=14)
    adx_threshold: int = Field(default=25)
    
    use_volume: bool = Field(default=False)
    volume_multiplier: float = Field(default=1.5)
    
    # Re-entry
    allow_reentry: bool = Field(default=True)
    reentry_after_sl: bool = Field(default=True)
    reentry_after_tp: bool = Field(default=True)
    
    def model_post_init(self, __context):
        """Initialize default take profits if not provided"""
        if not self.take_profits:
            defaults = [
                (1, 1.05, 50), (2, 1.95, 30), (3, 3.75, 15), (4, 6.0, 5),
                (5, 8.0, 0), (6, 10.0, 0), (7, 12.0, 0), (8, 15.0, 0),
                (9, 18.0, 0), (10, 20.0, 0)
            ]
            self.take_profits = [
                TakeProfitLevel(level=d[0], percent=d[1], amount=d[2])
                for d in defaults[:self.tp_count]
            ]


# ============ BOT CONFIGURATION ============

class BotSymbolConfig(BaseModel):
    """Configuration for a symbol within a bot"""
    symbol: str = Field(..., description="Trading pair, e.g., BTCUSDT")
    timeframe: str = Field(default="1h", description="Candle timeframe")
    enabled: bool = Field(default=True)
    allocation_percent: float = Field(default=100.0, ge=0, le=100)


class BotConfig(BaseModel):
    """Full bot configuration"""
    # Basic
    name: str = Field(..., min_length=1, max_length=50, description="Bot name")
    description: str = Field(default="", max_length=200)
    
    # Capital
    initial_capital: float = Field(default=10000.0, gt=0, description="Starting capital USD")
    leverage: int = Field(default=1, ge=1, le=125)
    commission_percent: float = Field(default=0.075, ge=0, le=1)
    
    # Symbols (multi-symbol support)
    symbols: List[BotSymbolConfig] = Field(default_factory=list, min_length=1, max_length=20)
    
    # Strategy
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    
    # Notifications
    notify_signals: bool = Field(default=True)
    notify_tp_hit: bool = Field(default=True)
    notify_sl_hit: bool = Field(default=True)
    
    # Schedule
    active_hours_start: int = Field(default=0, ge=0, le=23)
    active_hours_end: int = Field(default=23, ge=0, le=23)
    active_days: List[int] = Field(default=[0, 1, 2, 3, 4, 5, 6])  # 0=Monday
    
    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, v):
        if not v:
            raise ValueError("At least one symbol required")
        return v


# ============ POSITION ============

class Position(BaseModel):
    """Trading position"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bot_id: str
    symbol: str
    direction: SignalDirection
    status: PositionStatus = Field(default=PositionStatus.OPEN)
    
    # Entry
    entry_price: float
    entry_time: datetime
    entry_size: float  # Position size in base currency
    entry_value: float  # Position value in USD
    
    # Current state
    current_price: Optional[float] = None
    unrealized_pnl: float = Field(default=0.0)
    unrealized_pnl_percent: float = Field(default=0.0)
    
    # Take profits
    tp_levels_hit: List[int] = Field(default_factory=list)
    remaining_size: float = Field(default=0.0)
    
    # Exit
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[str] = None  # tp1, tp2, sl, signal_change, manual
    
    # Results
    realized_pnl: float = Field(default=0.0)
    realized_pnl_percent: float = Field(default=0.0)
    commission_paid: float = Field(default=0.0)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def model_post_init(self, __context):
        self.remaining_size = self.entry_size


# ============ BOT STATISTICS ============

class BotStatistics(BaseModel):
    """Bot performance statistics"""
    bot_id: str
    
    # Totals
    total_trades: int = Field(default=0)
    winning_trades: int = Field(default=0)
    losing_trades: int = Field(default=0)
    
    # PnL
    total_pnl: float = Field(default=0.0)
    total_pnl_percent: float = Field(default=0.0)
    
    # Averages
    avg_win: float = Field(default=0.0)
    avg_loss: float = Field(default=0.0)
    avg_trade_duration_minutes: float = Field(default=0.0)
    
    # Ratios
    win_rate: float = Field(default=0.0)
    profit_factor: float = Field(default=0.0)
    risk_reward_ratio: float = Field(default=0.0)
    
    # Drawdown
    max_drawdown: float = Field(default=0.0)
    max_drawdown_percent: float = Field(default=0.0)
    current_drawdown: float = Field(default=0.0)
    
    # Take profits
    tp1_hits: int = Field(default=0)
    tp2_hits: int = Field(default=0)
    tp3_hits: int = Field(default=0)
    tp4_hits: int = Field(default=0)
    sl_hits: int = Field(default=0)
    
    # Time-based
    best_day_pnl: float = Field(default=0.0)
    worst_day_pnl: float = Field(default=0.0)
    consecutive_wins: int = Field(default=0)
    consecutive_losses: int = Field(default=0)
    max_consecutive_wins: int = Field(default=0)
    max_consecutive_losses: int = Field(default=0)
    
    # Current state
    current_capital: float = Field(default=0.0)
    equity_peak: float = Field(default=0.0)
    
    updated_at: datetime = Field(default_factory=datetime.now)


# ============ BOT ============

class Bot(BaseModel):
    """Trading bot entity"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    config: BotConfig
    status: BotStatus = Field(default=BotStatus.STOPPED)
    
    # State
    current_capital: float = Field(default=0.0)
    open_positions: List[Position] = Field(default_factory=list)
    closed_positions: List[Position] = Field(default_factory=list)
    statistics: Optional[BotStatistics] = None
    
    # Runtime info
    last_signal_time: Optional[datetime] = None
    last_trade_time: Optional[datetime] = None
    last_error: Optional[str] = None
    error_count: int = Field(default=0)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    
    def model_post_init(self, __context):
        if self.current_capital == 0:
            self.current_capital = self.config.initial_capital
        if self.statistics is None:
            self.statistics = BotStatistics(
                bot_id=self.id,
                current_capital=self.current_capital,
                equity_peak=self.current_capital
            )


# ============ API MODELS ============

class BotCreate(BaseModel):
    """Request model for creating a bot"""
    config: BotConfig


class BotUpdate(BaseModel):
    """Request model for updating a bot"""
    name: Optional[str] = None
    description: Optional[str] = None
    symbols: Optional[List[BotSymbolConfig]] = None
    strategy: Optional[StrategyConfig] = None
    notify_signals: Optional[bool] = None
    notify_tp_hit: Optional[bool] = None
    notify_sl_hit: Optional[bool] = None


class BotResponse(BaseModel):
    """Response model for bot"""
    id: str
    name: str
    description: str
    status: BotStatus
    symbols: List[str]
    current_capital: float
    initial_capital: float
    total_pnl: float
    total_pnl_percent: float
    win_rate: float
    total_trades: int
    open_positions_count: int
    created_at: datetime
    started_at: Optional[datetime]
    
    @classmethod
    def from_bot(cls, bot: Bot) -> "BotResponse":
        stats = bot.statistics or BotStatistics(bot_id=bot.id)
        return cls(
            id=bot.id,
            name=bot.config.name,
            description=bot.config.description,
            status=bot.status,
            symbols=[s.symbol for s in bot.config.symbols],
            current_capital=bot.current_capital,
            initial_capital=bot.config.initial_capital,
            total_pnl=stats.total_pnl,
            total_pnl_percent=stats.total_pnl_percent,
            win_rate=stats.win_rate,
            total_trades=stats.total_trades,
            open_positions_count=len(bot.open_positions),
            created_at=bot.created_at,
            started_at=bot.started_at
        )


class BotDetailResponse(BaseModel):
    """Detailed bot response with full statistics"""
    bot: Bot
    statistics: BotStatistics
    recent_positions: List[Position]


class SignalEvent(BaseModel):
    """Trading signal event from indicator"""
    bot_id: str
    symbol: str
    timeframe: str
    direction: SignalDirection
    price: float
    indicator_values: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class PositionCloseRequest(BaseModel):
    """Request to manually close a position"""
    position_id: str
    reason: str = Field(default="manual")
    partial_percent: Optional[float] = Field(default=None, ge=1, le=100)


# ============ EQUITY CURVE ============

class EquityPoint(BaseModel):
    """Single point on equity curve"""
    timestamp: datetime
    equity: float
    drawdown: float = Field(default=0.0)
    position_count: int = Field(default=0)


class EquityCurve(BaseModel):
    """Bot equity curve"""
    bot_id: str
    points: List[EquityPoint] = Field(default_factory=list)
    
    def add_point(self, equity: float, position_count: int = 0):
        if self.points:
            peak = max(p.equity for p in self.points)
            drawdown = (peak - equity) / peak * 100 if peak > 0 else 0
        else:
            drawdown = 0
        
        self.points.append(EquityPoint(
            timestamp=datetime.now(),
            equity=equity,
            drawdown=drawdown,
            position_count=position_count
        ))


# ============ LOG ENTRY ============

class BotLogEntry(BaseModel):
    """Bot activity log entry"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    bot_id: str
    level: str = Field(default="info")  # info, warning, error, trade
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
