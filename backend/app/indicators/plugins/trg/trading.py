"""
TRG Trading System
==================
Complete trading logic for TRG indicator plugin.
Handles entry/exit, position management, TP/SL tracking.

Author: Komas Trading System
Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class PositionType(str, Enum):
    """Position direction"""
    LONG = "long"
    SHORT = "short"


class TrailingMode(str, Enum):
    """Stop loss trailing modes"""
    FIXED = "fixed"        # SL stays at initial level
    BREAKEVEN = "breakeven"  # SL moves to entry after TP1
    CASCADE = "cascade"    # SL moves to previous TP level (also called "moving")
    
    @classmethod
    def from_string(cls, value: str) -> 'TrailingMode':
        """Convert string to TrailingMode"""
        mapping = {
            'no': cls.FIXED,
            'fixed': cls.FIXED,
            'breakeven': cls.BREAKEVEN,
            'be': cls.BREAKEVEN,
            'moving': cls.CASCADE,
            'cascade': cls.CASCADE,
            'trailing': cls.CASCADE,
        }
        return mapping.get(value.lower(), cls.FIXED)


class ExitReason(str, Enum):
    """Position exit reasons"""
    TP1 = "TP1"
    TP2 = "TP2"
    TP3 = "TP3"
    TP4 = "TP4"
    TP5 = "TP5"
    TP6 = "TP6"
    TP7 = "TP7"
    TP8 = "TP8"
    TP9 = "TP9"
    TP10 = "TP10"
    SL = "SL"
    REVERSE = "Reverse"
    MANUAL = "Manual"
    
    @classmethod
    def from_tp_index(cls, index: int) -> 'ExitReason':
        """Get ExitReason for TP index (1-based)"""
        tp_map = {
            1: cls.TP1, 2: cls.TP2, 3: cls.TP3, 4: cls.TP4, 5: cls.TP5,
            6: cls.TP6, 7: cls.TP7, 8: cls.TP8, 9: cls.TP9, 10: cls.TP10
        }
        return tp_map.get(index, cls.TP1)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TakeProfitLevel:
    """Single take profit level configuration"""
    index: int           # 1-based index
    percent: float       # Target percent from entry
    amount: float        # Percentage of position to close (0-100)
    price: float = 0.0   # Calculated price
    hit: bool = False    # Whether this TP was hit
    hit_time: Optional[datetime] = None
    
    def calculate_price(self, entry_price: float, is_long: bool) -> float:
        """Calculate TP price from entry"""
        if is_long:
            self.price = entry_price * (1 + self.percent / 100)
        else:
            self.price = entry_price * (1 - self.percent / 100)
        return self.price


@dataclass
class TRGTradingConfig:
    """Configuration for TRG Trading System"""
    
    # Take Profit levels (up to 10)
    tp_count: int = 4
    tp_percents: List[float] = field(default_factory=lambda: [
        1.05, 1.95, 3.75, 6.0, 8.0, 10.0, 12.0, 15.0, 18.0, 20.0
    ])
    tp_amounts: List[float] = field(default_factory=lambda: [
        50.0, 30.0, 15.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    ])
    
    # Stop Loss
    sl_percent: float = 6.0
    sl_trailing_mode: TrailingMode = TrailingMode.BREAKEVEN
    
    # Leverage & Commission
    leverage: float = 1.0
    use_commission: bool = False
    commission_percent: float = 0.1
    
    # Re-entry settings
    allow_reentry: bool = True
    reentry_after_sl: bool = True
    reentry_after_tp: bool = False
    
    # Capital
    initial_capital: float = 10000.0
    
    def get_tp_levels(self) -> List[TakeProfitLevel]:
        """Get list of active TP levels"""
        levels = []
        for i in range(self.tp_count):
            levels.append(TakeProfitLevel(
                index=i + 1,
                percent=self.tp_percents[i] if i < len(self.tp_percents) else 0,
                amount=self.tp_amounts[i] if i < len(self.tp_amounts) else 0
            ))
        return levels
    
    def normalize_tp_amounts(self) -> List[float]:
        """Normalize TP amounts to sum to 100%"""
        amounts = self.tp_amounts[:self.tp_count]
        total = sum(amounts)
        if total > 0:
            return [a / total * 100 for a in amounts]
        return amounts
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TRGTradingConfig':
        """Create config from dictionary"""
        config = cls()
        
        # TP settings
        config.tp_count = data.get('tp_count', 4)
        
        # Parse TP percents
        tp_percents = []
        for i in range(1, 11):
            key = f'tp{i}_percent'
            if key in data:
                tp_percents.append(float(data[key]))
            elif i <= len(config.tp_percents):
                tp_percents.append(config.tp_percents[i-1])
        config.tp_percents = tp_percents
        
        # Parse TP amounts
        tp_amounts = []
        for i in range(1, 11):
            key = f'tp{i}_amount'
            if key in data:
                tp_amounts.append(float(data[key]))
            elif i <= len(config.tp_amounts):
                tp_amounts.append(config.tp_amounts[i-1])
        config.tp_amounts = tp_amounts
        
        # SL settings
        config.sl_percent = float(data.get('sl_percent', 6.0))
        sl_mode = data.get('sl_trailing_mode', 'breakeven')
        config.sl_trailing_mode = TrailingMode.from_string(sl_mode)
        
        # Leverage & Commission
        config.leverage = float(data.get('leverage', 1.0))
        config.use_commission = bool(data.get('use_commission', False))
        config.commission_percent = float(data.get('commission_percent', 0.1))
        
        # Re-entry
        config.allow_reentry = bool(data.get('allow_reentry', True))
        config.reentry_after_sl = bool(data.get('reentry_after_sl', True))
        config.reentry_after_tp = bool(data.get('reentry_after_tp', False))
        
        # Capital
        config.initial_capital = float(data.get('initial_capital', 10000.0))
        
        return config


@dataclass
class Position:
    """Active trading position"""
    
    # Basic info
    type: PositionType
    entry_time: datetime
    entry_price: float
    entry_capital: float
    
    # TP/SL
    tp_levels: List[TakeProfitLevel] = field(default_factory=list)
    sl_price: float = 0.0
    sl_initial: float = 0.0  # Original SL before trailing
    
    # State tracking
    remaining_pct: float = 100.0  # Remaining position %
    realized_pnl: float = 0.0    # Total realized PnL
    unrealized_pnl: float = 0.0  # Current unrealized PnL
    commission_paid: float = 0.0
    
    # Price tracking (for trailing)
    highest_price: float = 0.0
    lowest_price: float = float('inf')
    
    # TP tracking
    tp_closed: List[int] = field(default_factory=list)  # Indices of closed TPs
    tp_hit: List[int] = field(default_factory=list)     # 1-based TP numbers hit
    
    # Metadata
    is_reentry: bool = False
    i1_used: int = 0
    i2_used: float = 0.0
    
    def __post_init__(self):
        """Initialize tracking prices"""
        if self.highest_price == 0.0:
            self.highest_price = self.entry_price
        if self.lowest_price == float('inf'):
            self.lowest_price = self.entry_price
    
    @property
    def is_long(self) -> bool:
        return self.type == PositionType.LONG
    
    @property
    def is_short(self) -> bool:
        return self.type == PositionType.SHORT
    
    @property
    def tp_prices(self) -> List[float]:
        """Get list of TP prices"""
        return [tp.price for tp in self.tp_levels]
    
    def update_trailing_prices(self, high: float, low: float):
        """Update highest/lowest prices for trailing calculations"""
        self.highest_price = max(self.highest_price, high)
        self.lowest_price = min(self.lowest_price, low)


@dataclass
class Trade:
    """Completed trade record"""
    
    id: int
    type: str  # "long" or "short"
    entry_time: str
    entry_price: float
    exit_time: str
    exit_price: float
    pnl: float  # PnL percentage
    pnl_amount: float  # PnL in currency
    exit_reason: str
    tp_hit: List[int]  # 1-based TP numbers hit
    tp_levels: List[float]  # TP prices
    sl_level: float
    is_reentry: bool = False
    partial_closes: int = 0
    params_used: Dict[str, Any] = field(default_factory=dict)
    leverage: float = 1.0
    commission: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "type": self.type,
            "entry_time": self.entry_time,
            "entry_price": self.entry_price,
            "exit_time": self.exit_time,
            "exit_price": self.exit_price,
            "pnl": round(self.pnl, 2),
            "pnl_amount": round(self.pnl_amount, 2),
            "exit_reason": self.exit_reason,
            "tp_hit": self.tp_hit,
            "tp_levels": self.tp_levels,
            "sl_level": self.sl_level,
            "is_reentry": self.is_reentry,
            "partial_closes": self.partial_closes,
            "params_used": self.params_used,
            "leverage": self.leverage,
            "commission": round(self.commission, 4)
        }


# ============================================================================
# TRG TRADING SYSTEM
# ============================================================================

class TRGTradingSystem:
    """
    Complete trading system for TRG indicator.
    
    Handles:
    - Position entry based on signals
    - Partial TP closes with proper amount tracking
    - Trailing stop loss (fixed, breakeven, cascade)
    - Re-entry after SL/TP
    - Leverage and commission calculations
    """
    
    def __init__(self, config: TRGTradingConfig):
        """
        Initialize trading system.
        
        Args:
            config: Trading configuration
        """
        self.config = config
        self.position: Optional[Position] = None
        self.trades: List[Trade] = []
        self.capital = config.initial_capital
        
        # State tracking
        self.last_exit_reason: Optional[str] = None
        self.last_exit_trend: Optional[int] = None
        self.total_commission_paid: float = 0.0
        
        # Normalized TP amounts
        self._tp_amounts = config.normalize_tp_amounts()
        
        logger.debug(f"TRGTradingSystem initialized: capital={config.initial_capital}, "
                    f"tp_count={config.tp_count}, sl={config.sl_percent}%")
    
    def reset(self):
        """Reset trading system state"""
        self.position = None
        self.trades = []
        self.capital = self.config.initial_capital
        self.last_exit_reason = None
        self.last_exit_trend = None
        self.total_commission_paid = 0.0
    
    # ========================================================================
    # ENTRY LOGIC
    # ========================================================================
    
    def check_entry(
        self,
        signal: int,
        current_trend: int,
        timestamp: datetime,
        close_price: float,
        i1: int = 0,
        i2: float = 0.0
    ) -> bool:
        """
        Check if we should enter a new position.
        
        Args:
            signal: Signal value (-1, 0, 1)
            current_trend: Current TRG trend direction
            timestamp: Current candle timestamp
            close_price: Current close price
            i1: ATR length parameter used
            i2: Multiplier parameter used
            
        Returns:
            True if position was opened
        """
        if self.position is not None:
            return False
        
        should_enter = False
        entry_type: Optional[PositionType] = None
        is_reentry = False
        
        # Check for new signal
        if signal != 0:
            should_enter = True
            entry_type = PositionType.LONG if signal == 1 else PositionType.SHORT
        
        # Check for re-entry
        elif self.config.allow_reentry and self.last_exit_reason and self.last_exit_trend:
            can_reentry = False
            
            # Re-entry after SL
            if self.last_exit_reason == ExitReason.SL.value and self.config.reentry_after_sl:
                if self.last_exit_trend == current_trend and current_trend != 0:
                    can_reentry = True
            
            # Re-entry after TP
            if self.last_exit_reason and self.last_exit_reason.startswith("TP"):
                if self.config.reentry_after_tp:
                    if self.last_exit_trend == current_trend and current_trend != 0:
                        can_reentry = True
            
            if can_reentry:
                should_enter = True
                entry_type = PositionType.LONG if current_trend == 1 else PositionType.SHORT
                is_reentry = True
                self.last_exit_reason = None
        
        # Open position
        if should_enter and entry_type:
            self._open_position(
                entry_type=entry_type,
                timestamp=timestamp,
                entry_price=close_price,
                is_reentry=is_reentry,
                i1=i1,
                i2=i2
            )
            return True
        
        return False
    
    def _open_position(
        self,
        entry_type: PositionType,
        timestamp: datetime,
        entry_price: float,
        is_reentry: bool = False,
        i1: int = 0,
        i2: float = 0.0
    ):
        """
        Open a new position.
        
        Args:
            entry_type: Position direction
            timestamp: Entry timestamp
            entry_price: Entry price
            is_reentry: Whether this is a re-entry
            i1: ATR length used
            i2: Multiplier used
        """
        entry_capital = self.capital
        
        # Calculate entry commission
        entry_commission = 0.0
        if self.config.use_commission:
            entry_commission = entry_capital * (self.config.commission_percent / 100)
        
        # Create TP levels
        tp_levels = self.config.get_tp_levels()
        is_long = entry_type == PositionType.LONG
        
        for tp in tp_levels:
            tp.calculate_price(entry_price, is_long)
        
        # Calculate SL price
        if is_long:
            sl_price = entry_price * (1 - self.config.sl_percent / 100)
        else:
            sl_price = entry_price * (1 + self.config.sl_percent / 100)
        
        # Create position
        self.position = Position(
            type=entry_type,
            entry_time=timestamp,
            entry_price=entry_price,
            entry_capital=entry_capital,
            tp_levels=tp_levels,
            sl_price=sl_price,
            sl_initial=sl_price,
            realized_pnl=-entry_commission,  # Start with negative (commission)
            commission_paid=entry_commission,
            is_reentry=is_reentry,
            i1_used=i1,
            i2_used=i2
        )
        
        logger.debug(f"Opened {entry_type.value} position at {entry_price}, "
                    f"SL={sl_price:.2f}, TPs={[tp.price for tp in tp_levels]}")
    
    # ========================================================================
    # EXIT LOGIC
    # ========================================================================
    
    def check_exit(
        self,
        high: float,
        low: float,
        close: float,
        signal: int,
        timestamp: datetime,
        current_trend: int
    ) -> Optional[Trade]:
        """
        Check exit conditions and close position if needed.
        
        Args:
            high: Current candle high
            low: Current candle low
            close: Current candle close
            signal: Current signal
            timestamp: Current timestamp
            current_trend: Current TRG trend
            
        Returns:
            Trade object if position was closed, None otherwise
        """
        if self.position is None:
            return None
        
        # Update trailing prices
        self.position.update_trailing_prices(high, low)
        
        # Check TP hits (partial closes)
        self._check_tp_hits(high, low)
        
        # Check if all TPs closed
        all_tp_closed = self.position.remaining_pct <= 0.01
        
        # Check SL hit
        sl_hit = self._check_sl_hit(high, low)
        
        # Check reverse signal
        reverse_signal = self._check_reverse_signal(signal)
        
        # Close position if any exit condition met
        if all_tp_closed or sl_hit or reverse_signal:
            return self._close_position(
                timestamp=timestamp,
                close_price=close,
                current_trend=current_trend,
                sl_hit=sl_hit,
                all_tp_closed=all_tp_closed
            )
        
        return None
    
    def _check_tp_hits(self, high: float, low: float):
        """Check and process take profit hits"""
        if self.position is None:
            return
        
        for i, tp in enumerate(self.position.tp_levels):
            if i in self.position.tp_closed:
                continue
            
            tp_hit = False
            if self.position.is_long and high >= tp.price:
                tp_hit = True
            elif self.position.is_short and low <= tp.price:
                tp_hit = True
            
            if tp_hit:
                self._process_tp_hit(i, tp)
    
    def _process_tp_hit(self, tp_idx: int, tp: TakeProfitLevel):
        """Process a single TP hit with partial close"""
        if self.position is None:
            return
        
        tp_amount_pct = self._tp_amounts[tp_idx] if tp_idx < len(self._tp_amounts) else 0
        portion_size = self.position.entry_capital * (tp_amount_pct / 100)
        
        # Calculate PnL for this portion
        portion_pnl_pct = tp.percent
        
        # Apply leverage
        portion_pnl_pct_leveraged = portion_pnl_pct * self.config.leverage
        
        # Calculate exit commission for this portion
        exit_commission = 0.0
        if self.config.use_commission:
            exit_commission = portion_size * (self.config.commission_percent / 100)
        
        # Calculate actual PnL
        portion_pnl = portion_size * (portion_pnl_pct_leveraged / 100) - exit_commission
        
        # Update position state
        self.position.commission_paid += exit_commission
        self.position.realized_pnl += portion_pnl
        self.position.remaining_pct -= tp_amount_pct
        self.position.tp_closed.append(tp_idx)
        self.position.tp_hit.append(tp_idx + 1)  # 1-based
        
        # Mark TP as hit
        tp.hit = True
        tp.hit_time = datetime.now()
        
        # Update trailing SL
        self._update_trailing_sl(tp_idx)
        
        logger.debug(f"TP{tp_idx + 1} hit: pnl={portion_pnl:.2f}, "
                    f"remaining={self.position.remaining_pct:.1f}%")
    
    def _update_trailing_sl(self, tp_idx: int):
        """Update stop loss based on trailing mode"""
        if self.position is None:
            return
        
        mode = self.config.sl_trailing_mode
        
        if mode == TrailingMode.BREAKEVEN:
            # Move to entry after first TP
            if len(self.position.tp_closed) == 1:
                self.position.sl_price = self.position.entry_price
                logger.debug(f"SL moved to breakeven: {self.position.sl_price:.2f}")
        
        elif mode == TrailingMode.CASCADE:
            # Move to previous TP level
            if len(self.position.tp_closed) > 1:
                prev_tp_idx = self.position.tp_closed[-2]
                self.position.sl_price = self.position.tp_levels[prev_tp_idx].price
            else:
                # After first TP, move to entry
                self.position.sl_price = self.position.entry_price
            logger.debug(f"SL cascaded to: {self.position.sl_price:.2f}")
    
    def _check_sl_hit(self, high: float, low: float) -> bool:
        """Check if stop loss was hit"""
        if self.position is None:
            return False
        
        if self.position.is_long and low <= self.position.sl_price:
            return True
        if self.position.is_short and high >= self.position.sl_price:
            return True
        
        return False
    
    def _check_reverse_signal(self, signal: int) -> bool:
        """Check if reverse signal occurred"""
        if self.position is None or signal == 0:
            return False
        
        if self.position.is_long and signal == -1:
            return True
        if self.position.is_short and signal == 1:
            return True
        
        return False
    
    def _close_position(
        self,
        timestamp: datetime,
        close_price: float,
        current_trend: int,
        sl_hit: bool,
        all_tp_closed: bool
    ) -> Trade:
        """
        Close position and create trade record.
        
        Args:
            timestamp: Exit timestamp
            close_price: Current close price
            current_trend: Current trend direction
            sl_hit: Whether SL was hit
            all_tp_closed: Whether all TPs were closed
            
        Returns:
            Completed trade record
        """
        pos = self.position
        assert pos is not None
        
        # Close remaining portion if any
        exit_price = close_price
        if pos.remaining_pct > 0.01:
            remaining_size = pos.entry_capital * (pos.remaining_pct / 100)
            
            if sl_hit:
                exit_price = pos.sl_price
            
            # Calculate remaining PnL
            if pos.is_long:
                remaining_pnl_pct = (exit_price - pos.entry_price) / pos.entry_price * 100
            else:
                remaining_pnl_pct = (pos.entry_price - exit_price) / pos.entry_price * 100
            
            # Apply leverage
            remaining_pnl_pct_leveraged = remaining_pnl_pct * self.config.leverage
            
            # Exit commission for remaining
            exit_commission = 0.0
            if self.config.use_commission:
                exit_commission = remaining_size * (self.config.commission_percent / 100)
            
            remaining_pnl = remaining_size * (remaining_pnl_pct_leveraged / 100) - exit_commission
            pos.commission_paid += exit_commission
            pos.realized_pnl += remaining_pnl
        
        # Determine exit reason
        if all_tp_closed:
            exit_reason = ExitReason.from_tp_index(len(pos.tp_closed)).value
        elif sl_hit:
            exit_reason = ExitReason.SL.value
        else:
            exit_reason = ExitReason.REVERSE.value
        
        # Calculate total PnL percentage
        total_pnl = pos.realized_pnl
        total_pnl_pct = (total_pnl / pos.entry_capital) * 100
        
        # Update capital
        self.capital += total_pnl
        self.total_commission_paid += pos.commission_paid
        
        # Create trade record
        trade = Trade(
            id=len(self.trades) + 1,
            type=pos.type.value,
            entry_time=pos.entry_time.isoformat() if isinstance(pos.entry_time, datetime) else str(pos.entry_time),
            entry_price=pos.entry_price,
            exit_time=timestamp.isoformat() if isinstance(timestamp, datetime) else str(timestamp),
            exit_price=exit_price if not all_tp_closed else pos.tp_levels[pos.tp_closed[-1]].price,
            pnl=round(total_pnl_pct, 2),
            pnl_amount=round(total_pnl, 2),
            exit_reason=exit_reason,
            tp_hit=pos.tp_hit.copy(),
            tp_levels=pos.tp_prices,
            sl_level=pos.sl_price,
            is_reentry=pos.is_reentry,
            partial_closes=len(pos.tp_closed),
            params_used={"i1": pos.i1_used, "i2": pos.i2_used},
            leverage=self.config.leverage,
            commission=pos.commission_paid
        )
        
        self.trades.append(trade)
        
        # Save exit state for re-entry logic
        self.last_exit_reason = exit_reason
        self.last_exit_trend = current_trend
        
        # Clear position
        self.position = None
        
        logger.debug(f"Closed {trade.type} trade: PnL={trade.pnl}%, reason={trade.exit_reason}")
        
        return trade
    
    # ========================================================================
    # PROCESS BAR
    # ========================================================================
    
    def process_bar(
        self,
        timestamp: datetime,
        open_price: float,
        high: float,
        low: float,
        close: float,
        signal: int,
        trend: int,
        i1: int = 0,
        i2: float = 0.0
    ) -> Tuple[Optional[Trade], float]:
        """
        Process a single bar through the trading system.
        
        Args:
            timestamp: Bar timestamp
            open_price: Open price
            high: High price
            low: Low price
            close: Close price
            signal: Entry signal (-1, 0, 1)
            trend: Current TRG trend
            i1: ATR length used
            i2: Multiplier used
            
        Returns:
            Tuple of (completed trade or None, current equity)
        """
        completed_trade = None
        
        # Check exit first (if in position)
        if self.position is not None:
            completed_trade = self.check_exit(
                high=high,
                low=low,
                close=close,
                signal=signal,
                timestamp=timestamp,
                current_trend=trend
            )
        
        # Check entry (if not in position)
        if self.position is None:
            self.check_entry(
                signal=signal,
                current_trend=trend,
                timestamp=timestamp,
                close_price=close,
                i1=i1,
                i2=i2
            )
        
        return completed_trade, self.capital
    
    # ========================================================================
    # GETTERS
    # ========================================================================
    
    def get_trades(self) -> List[Dict[str, Any]]:
        """Get list of completed trades as dictionaries"""
        return [t.to_dict() for t in self.trades]
    
    def get_position_info(self) -> Optional[Dict[str, Any]]:
        """Get current position information"""
        if self.position is None:
            return None
        
        pos = self.position
        return {
            "type": pos.type.value,
            "entry_time": pos.entry_time.isoformat() if isinstance(pos.entry_time, datetime) else str(pos.entry_time),
            "entry_price": pos.entry_price,
            "entry_capital": pos.entry_capital,
            "remaining_pct": round(pos.remaining_pct, 2),
            "realized_pnl": round(pos.realized_pnl, 2),
            "tp_prices": pos.tp_prices,
            "tp_hit": pos.tp_hit,
            "sl_price": pos.sl_price,
            "highest_price": pos.highest_price,
            "lowest_price": pos.lowest_price,
            "is_reentry": pos.is_reentry
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get trading summary statistics"""
        if not self.trades:
            return {
                "total_trades": 0,
                "capital": round(self.capital, 2),
                "pnl": 0,
                "pnl_pct": 0,
                "commission_paid": 0
            }
        
        wins = [t for t in self.trades if t.pnl > 0]
        losses = [t for t in self.trades if t.pnl < 0]
        
        return {
            "total_trades": len(self.trades),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate": round(len(wins) / len(self.trades) * 100, 2) if self.trades else 0,
            "capital": round(self.capital, 2),
            "pnl": round(self.capital - self.config.initial_capital, 2),
            "pnl_pct": round((self.capital / self.config.initial_capital - 1) * 100, 2),
            "commission_paid": round(self.total_commission_paid, 2),
            "avg_win": round(sum(t.pnl for t in wins) / len(wins), 2) if wins else 0,
            "avg_loss": round(sum(t.pnl for t in losses) / len(losses), 2) if losses else 0
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_trading_system(settings: Dict[str, Any]) -> TRGTradingSystem:
    """
    Create TRG Trading System from settings dictionary.
    
    Args:
        settings: Settings dictionary (from API request)
        
    Returns:
        Configured TRGTradingSystem instance
    """
    config = TRGTradingConfig.from_dict(settings)
    return TRGTradingSystem(config)


def run_trading_simulation(
    df: pd.DataFrame,
    settings: Dict[str, Any],
    signal_column: str = 'signal',
    trend_column: str = 'trg_trend'
) -> Tuple[List[Dict], List[Dict], Dict]:
    """
    Run trading simulation on DataFrame with signals.
    
    Args:
        df: DataFrame with OHLCV data and signals
        settings: Trading settings dictionary
        signal_column: Column name for signals
        trend_column: Column name for trend
        
    Returns:
        Tuple of (trades, equity_curve, summary)
    """
    system = create_trading_system(settings)
    
    # Get indicator parameters if present
    i1 = settings.get('trg_atr_length', 45)
    i2 = settings.get('trg_multiplier', 4.0)
    
    equity_curve = []
    
    for i in range(len(df)):
        row = df.iloc[i]
        timestamp = df.index[i]
        
        signal = int(row.get(signal_column, 0))
        trend = int(row.get(trend_column, 0))
        
        _, equity = system.process_bar(
            timestamp=timestamp,
            open_price=float(row['open']),
            high=float(row['high']),
            low=float(row['low']),
            close=float(row['close']),
            signal=signal,
            trend=trend,
            i1=i1,
            i2=i2
        )
        
        equity_curve.append({
            "time": timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
            "value": round(equity, 2)
        })
    
    return system.get_trades(), equity_curve, system.get_summary()


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    'PositionType',
    'TrailingMode',
    'ExitReason',
    
    # Data classes
    'TakeProfitLevel',
    'TRGTradingConfig',
    'Position',
    'Trade',
    
    # Main class
    'TRGTradingSystem',
    
    # Helper functions
    'create_trading_system',
    'run_trading_simulation',
]
