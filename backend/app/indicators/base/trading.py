"""
Komas Trading System - Base Trading System
==========================================
Abstract base class for trading system logic.
Handles position management, take profits, stop losses, and trailing.

Version: 1.0
Author: Komas Team
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import pandas as pd
import numpy as np


class PositionType(Enum):
    """Position type"""
    LONG = "long"
    SHORT = "short"


class PositionStatus(Enum):
    """Position status"""
    OPEN = "open"
    CLOSED = "closed"
    PARTIAL = "partial"


class TrailingMode(Enum):
    """Stop loss trailing mode"""
    FIXED = "fixed"          # Fixed SL, no trailing
    BREAKEVEN = "breakeven"  # Move to entry after TP1
    CASCADE = "cascade"      # Move to previous TP after each hit
    MOVING = "moving"        # Trail based on price movement


class ExitReason(Enum):
    """Reason for position exit"""
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
    STOP_LOSS = "SL"
    REVERSE = "Reverse"
    MANUAL = "Manual"
    TIME = "Time"


@dataclass
class TakeProfitLevel:
    """Take profit level configuration"""
    level: int           # TP number (1-10)
    percent: float       # Distance from entry in %
    amount: float        # Portion of position to close in %
    price: float = 0.0   # Calculated TP price
    hit: bool = False    # Whether this TP was hit
    hit_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "level": self.level,
            "percent": self.percent,
            "amount": self.amount,
            "price": self.price,
            "hit": self.hit,
            "hit_time": self.hit_time.isoformat() if self.hit_time else None
        }


@dataclass
class Position:
    """
    Trading position with all state.
    Tracks entry, exits, TP/SL levels, and PnL.
    """
    id: int
    type: PositionType
    entry_time: datetime
    entry_price: float
    entry_capital: float
    
    # TP/SL configuration
    tp_levels: List[TakeProfitLevel] = field(default_factory=list)
    sl_percent: float = 6.0
    sl_price: float = 0.0
    sl_trailing_mode: TrailingMode = TrailingMode.BREAKEVEN
    
    # State tracking
    status: PositionStatus = PositionStatus.OPEN
    remaining_percent: float = 100.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    
    # Price tracking for trailing
    highest_price: float = 0.0
    lowest_price: float = float('inf')
    
    # Exit info
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[ExitReason] = None
    
    # Flags
    is_reentry: bool = False
    
    # Leverage & commission
    leverage: float = 1.0
    commission_paid: float = 0.0
    
    # Indicator params used (for adaptive optimization)
    params_used: Dict[str, Any] = field(default_factory=dict)
    
    def calculate_tp_sl_prices(self):
        """Calculate TP and SL prices based on entry and settings"""
        for tp in self.tp_levels:
            if self.type == PositionType.LONG:
                tp.price = self.entry_price * (1 + tp.percent / 100)
            else:
                tp.price = self.entry_price * (1 - tp.percent / 100)
        
        if self.type == PositionType.LONG:
            self.sl_price = self.entry_price * (1 - self.sl_percent / 100)
        else:
            self.sl_price = self.entry_price * (1 + self.sl_percent / 100)
        
        self.highest_price = self.entry_price
        self.lowest_price = self.entry_price
    
    def get_tp_hits(self) -> List[int]:
        """Get list of hit TP levels"""
        return [tp.level for tp in self.tp_levels if tp.hit]
    
    def get_next_tp(self) -> Optional[TakeProfitLevel]:
        """Get next unhit TP level"""
        for tp in self.tp_levels:
            if not tp.hit:
                return tp
        return None
    
    def total_pnl_percent(self) -> float:
        """Calculate total PnL as percentage of entry capital"""
        return (self.realized_pnl / self.entry_capital * 100) if self.entry_capital > 0 else 0
    
    def to_dict(self) -> Dict:
        """Convert position to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "entry_time": self.entry_time.isoformat(),
            "entry_price": self.entry_price,
            "entry_capital": self.entry_capital,
            "tp_levels": [tp.to_dict() for tp in self.tp_levels],
            "sl_percent": self.sl_percent,
            "sl_price": self.sl_price,
            "sl_trailing_mode": self.sl_trailing_mode.value,
            "status": self.status.value,
            "remaining_percent": self.remaining_percent,
            "realized_pnl": round(self.realized_pnl, 4),
            "unrealized_pnl": round(self.unrealized_pnl, 4),
            "highest_price": self.highest_price,
            "lowest_price": self.lowest_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason.value if self.exit_reason else None,
            "is_reentry": self.is_reentry,
            "leverage": self.leverage,
            "commission_paid": round(self.commission_paid, 4),
            "params_used": self.params_used
        }


@dataclass
class Trade:
    """
    Completed trade record.
    Created when position is fully closed.
    """
    id: int
    type: str  # "long" or "short"
    entry_time: str
    entry_price: float
    exit_time: str
    exit_price: float
    pnl: float        # PnL as percentage
    pnl_amount: float  # PnL in currency
    exit_reason: str
    tp_hit: List[int]  # List of hit TP levels
    tp_levels: List[float]  # TP prices
    sl_level: float
    is_reentry: bool
    partial_closes: int
    leverage: float
    commission: float
    params_used: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
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
            "leverage": self.leverage,
            "commission": round(self.commission, 4),
            "params_used": self.params_used
        }


@dataclass
class TradingConfig:
    """
    Trading system configuration.
    Contains all settings for position management.
    """
    # Take profits (up to 10 levels)
    tp_count: int = 4
    tp_percents: List[float] = field(default_factory=lambda: [1.05, 1.95, 3.75, 6.0, 8.0, 10.0, 12.0, 15.0, 18.0, 20.0])
    tp_amounts: List[float] = field(default_factory=lambda: [50.0, 30.0, 15.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    
    # Stop loss
    sl_percent: float = 6.0
    sl_trailing_mode: TrailingMode = TrailingMode.BREAKEVEN
    
    # Leverage and commission
    leverage: float = 1.0
    use_commission: bool = False
    commission_percent: float = 0.1
    
    # Re-entry settings
    allow_reentry: bool = True
    reentry_after_sl: bool = True
    reentry_after_tp: bool = False
    
    # Capital
    initial_capital: float = 10000.0
    
    def get_active_tps(self) -> List[Tuple[float, float]]:
        """Get list of active TP levels as (percent, amount) tuples"""
        result = []
        total_amount = sum(self.tp_amounts[:self.tp_count])
        
        for i in range(self.tp_count):
            pct = self.tp_percents[i] if i < len(self.tp_percents) else 0
            amt = self.tp_amounts[i] if i < len(self.tp_amounts) else 0
            
            # Normalize amount to sum to 100%
            if total_amount > 0:
                amt = amt / total_amount * 100
            
            result.append((pct, amt))
        
        return result
    
    def to_dict(self) -> Dict:
        return {
            "tp_count": self.tp_count,
            "tp_percents": self.tp_percents[:self.tp_count],
            "tp_amounts": self.tp_amounts[:self.tp_count],
            "sl_percent": self.sl_percent,
            "sl_trailing_mode": self.sl_trailing_mode.value,
            "leverage": self.leverage,
            "use_commission": self.use_commission,
            "commission_percent": self.commission_percent,
            "allow_reentry": self.allow_reentry,
            "reentry_after_sl": self.reentry_after_sl,
            "reentry_after_tp": self.reentry_after_tp,
            "initial_capital": self.initial_capital
        }


class BaseTradingSystem(ABC):
    """
    Abstract base class for trading system.
    Manages positions, TP/SL logic, and trade execution.
    
    Subclasses must implement:
    - process_bar(): Handle price bar update
    - should_open_position(): Check entry conditions
    - should_close_position(): Check exit conditions
    
    Optional overrides:
    - on_position_opened(): Called when position opens
    - on_tp_hit(): Called when TP is hit
    - on_sl_hit(): Called when SL is hit
    - on_position_closed(): Called when position closes
    """
    
    def __init__(self, config: TradingConfig):
        self.config = config
        self.capital = config.initial_capital
        self.position: Optional[Position] = None
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []
        self.trade_counter = 0
        
        # State tracking
        self.last_exit_reason: Optional[ExitReason] = None
        self.last_exit_trend: int = 0
    
    # ==================== ABSTRACT METHODS ====================
    
    @abstractmethod
    def process_bar(self, bar: pd.Series, timestamp: datetime, signal: int, trend: int) -> None:
        """
        Process a single price bar.
        Updates position state, checks TP/SL, handles entries/exits.
        
        Args:
            bar: Price bar with open, high, low, close, volume
            timestamp: Bar timestamp
            signal: Entry signal (0=none, 1=long, -1=short)
            trend: Current trend direction
        """
        pass
    
    @abstractmethod
    def should_open_position(self, bar: pd.Series, signal: int, trend: int) -> Optional[PositionType]:
        """
        Check if new position should be opened.
        
        Args:
            bar: Current price bar
            signal: Entry signal
            trend: Current trend
        
        Returns:
            PositionType if should open, None otherwise
        """
        pass
    
    @abstractmethod
    def should_close_position(self, bar: pd.Series, signal: int, trend: int) -> Optional[ExitReason]:
        """
        Check if current position should be closed.
        
        Args:
            bar: Current price bar
            signal: Entry signal (may trigger reverse)
            trend: Current trend
        
        Returns:
            ExitReason if should close, None otherwise
        """
        pass
    
    # ==================== POSITION MANAGEMENT ====================
    
    def open_position(
        self,
        pos_type: PositionType,
        entry_price: float,
        entry_time: datetime,
        is_reentry: bool = False,
        params_used: Optional[Dict] = None
    ) -> Position:
        """
        Open new position.
        
        Args:
            pos_type: Long or short
            entry_price: Entry price
            entry_time: Entry timestamp
            is_reentry: Whether this is a re-entry trade
            params_used: Indicator params used (for adaptive mode)
        
        Returns:
            Created Position object
        """
        self.trade_counter += 1
        
        # Calculate entry capital (after commission)
        entry_capital = self.capital
        commission = 0.0
        
        if self.config.use_commission:
            commission = entry_capital * (self.config.commission_percent / 100)
            entry_capital -= commission
        
        # Create TP levels
        tp_levels = []
        active_tps = self.config.get_active_tps()
        
        for i, (pct, amt) in enumerate(active_tps):
            tp_levels.append(TakeProfitLevel(
                level=i + 1,
                percent=pct,
                amount=amt
            ))
        
        # Create position
        position = Position(
            id=self.trade_counter,
            type=pos_type,
            entry_time=entry_time,
            entry_price=entry_price,
            entry_capital=entry_capital,
            tp_levels=tp_levels,
            sl_percent=self.config.sl_percent,
            sl_trailing_mode=self.config.sl_trailing_mode,
            is_reentry=is_reentry,
            leverage=self.config.leverage,
            commission_paid=commission,
            params_used=params_used or {}
        )
        
        # Calculate TP/SL prices
        position.calculate_tp_sl_prices()
        
        self.position = position
        self.on_position_opened(position)
        
        return position
    
    def close_position(
        self,
        exit_price: float,
        exit_time: datetime,
        exit_reason: ExitReason
    ) -> Trade:
        """
        Close current position entirely.
        
        Args:
            exit_price: Exit price
            exit_time: Exit timestamp
            exit_reason: Reason for closing
        
        Returns:
            Created Trade record
        """
        if not self.position:
            raise ValueError("No position to close")
        
        pos = self.position
        
        # Close any remaining portion
        if pos.remaining_percent > 0.01:
            self._close_portion(
                pos,
                pos.remaining_percent,
                exit_price,
                exit_time
            )
        
        # Update position state
        pos.status = PositionStatus.CLOSED
        pos.exit_time = exit_time
        pos.exit_price = exit_price
        pos.exit_reason = exit_reason
        
        # Calculate final PnL
        total_pnl = pos.realized_pnl
        total_pnl_pct = (total_pnl / pos.entry_capital * 100) if pos.entry_capital > 0 else 0
        
        # Update capital
        self.capital += total_pnl
        
        # Record equity
        self.equity_curve.append({
            "time": exit_time.isoformat(),
            "value": round(self.capital, 2),
            "trade_id": pos.id
        })
        
        # Create trade record
        trade = Trade(
            id=pos.id,
            type=pos.type.value,
            entry_time=pos.entry_time.isoformat(),
            entry_price=pos.entry_price,
            exit_time=exit_time.isoformat(),
            exit_price=exit_price,
            pnl=round(total_pnl_pct, 2),
            pnl_amount=round(total_pnl, 2),
            exit_reason=exit_reason.value,
            tp_hit=pos.get_tp_hits(),
            tp_levels=[tp.price for tp in pos.tp_levels],
            sl_level=pos.sl_price,
            is_reentry=pos.is_reentry,
            partial_closes=len([tp for tp in pos.tp_levels if tp.hit]),
            leverage=pos.leverage,
            commission=pos.commission_paid,
            params_used=pos.params_used
        )
        
        self.trades.append(trade)
        self.last_exit_reason = exit_reason
        self.on_position_closed(trade)
        
        self.position = None
        
        return trade
    
    def _close_portion(
        self,
        pos: Position,
        portion_pct: float,
        price: float,
        timestamp: datetime
    ) -> float:
        """
        Close portion of position.
        
        Args:
            pos: Position to close portion of
            portion_pct: Percentage of original position to close
            price: Close price
            timestamp: Close time
        
        Returns:
            PnL amount for this portion
        """
        portion_size = pos.entry_capital * (portion_pct / 100)
        
        # Calculate PnL percentage
        if pos.type == PositionType.LONG:
            pnl_pct = (price - pos.entry_price) / pos.entry_price * 100
        else:
            pnl_pct = (pos.entry_price - price) / pos.entry_price * 100
        
        # Apply leverage
        pnl_pct_leveraged = pnl_pct * pos.leverage
        
        # Calculate commission
        commission = 0.0
        if self.config.use_commission:
            commission = portion_size * (self.config.commission_percent / 100)
            pos.commission_paid += commission
        
        # Calculate PnL
        pnl_amount = portion_size * (pnl_pct_leveraged / 100) - commission
        
        # Update position
        pos.realized_pnl += pnl_amount
        pos.remaining_percent -= portion_pct
        
        if pos.remaining_percent <= 0.01:
            pos.status = PositionStatus.CLOSED
        else:
            pos.status = PositionStatus.PARTIAL
        
        return pnl_amount
    
    def check_tp_hit(self, pos: Position, high: float, low: float, timestamp: datetime) -> bool:
        """
        Check and process TP hits.
        
        Args:
            pos: Current position
            high: Bar high price
            low: Bar low price
            timestamp: Bar timestamp
        
        Returns:
            True if any TP was hit
        """
        any_hit = False
        
        for tp in pos.tp_levels:
            if tp.hit:
                continue
            
            hit = False
            if pos.type == PositionType.LONG and high >= tp.price:
                hit = True
            elif pos.type == PositionType.SHORT and low <= tp.price:
                hit = True
            
            if hit:
                tp.hit = True
                tp.hit_time = timestamp
                any_hit = True
                
                # Close portion at TP price
                self._close_portion(pos, tp.amount, tp.price, timestamp)
                
                # Update trailing SL
                self._update_trailing_sl(pos, tp.level)
                
                self.on_tp_hit(pos, tp)
        
        return any_hit
    
    def check_sl_hit(self, pos: Position, high: float, low: float) -> bool:
        """
        Check if SL was hit.
        
        Args:
            pos: Current position
            high: Bar high price
            low: Bar low price
        
        Returns:
            True if SL was hit
        """
        if pos.type == PositionType.LONG:
            return low <= pos.sl_price
        else:
            return high >= pos.sl_price
    
    def _update_trailing_sl(self, pos: Position, tp_level: int) -> None:
        """Update trailing SL after TP hit"""
        mode = pos.sl_trailing_mode
        
        if mode == TrailingMode.BREAKEVEN:
            # Move to breakeven after first TP
            if tp_level == 1:
                pos.sl_price = pos.entry_price
        
        elif mode == TrailingMode.CASCADE:
            # Move to previous TP level
            if tp_level > 1:
                prev_tp = next((tp for tp in pos.tp_levels if tp.level == tp_level - 1), None)
                if prev_tp:
                    pos.sl_price = prev_tp.price
            else:
                pos.sl_price = pos.entry_price
        
        elif mode == TrailingMode.MOVING:
            # Trailing based on price
            atr_factor = 0.02  # Could be configurable
            if pos.type == PositionType.LONG:
                new_sl = pos.highest_price * (1 - atr_factor)
                pos.sl_price = max(pos.sl_price, new_sl)
            else:
                new_sl = pos.lowest_price * (1 + atr_factor)
                pos.sl_price = min(pos.sl_price, new_sl)
    
    def update_price_tracking(self, pos: Position, high: float, low: float) -> None:
        """Update highest/lowest price tracking for position"""
        if pos.type == PositionType.LONG:
            pos.highest_price = max(pos.highest_price, high)
        else:
            pos.lowest_price = min(pos.lowest_price, low)
    
    # ==================== CALLBACKS ====================
    
    def on_position_opened(self, position: Position) -> None:
        """Called when position is opened. Override for custom logic."""
        pass
    
    def on_tp_hit(self, position: Position, tp: TakeProfitLevel) -> None:
        """Called when TP level is hit. Override for custom logic."""
        pass
    
    def on_sl_hit(self, position: Position) -> None:
        """Called when SL is hit. Override for custom logic."""
        pass
    
    def on_position_closed(self, trade: Trade) -> None:
        """Called when position is fully closed. Override for custom logic."""
        pass
    
    # ==================== GETTERS ====================
    
    def get_trades(self) -> List[Dict]:
        """Get all trades as dictionaries"""
        return [t.to_dict() for t in self.trades]
    
    def get_equity_curve(self) -> List[Dict]:
        """Get equity curve"""
        return self.equity_curve.copy()
    
    def get_current_position(self) -> Optional[Dict]:
        """Get current position as dictionary"""
        return self.position.to_dict() if self.position else None
    
    def get_statistics(self) -> Dict:
        """Calculate and return trading statistics"""
        if not self.trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "total_pnl": 0,
                "max_drawdown": 0
            }
        
        pnls = [t.pnl for t in self.trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        total_trades = len(self.trades)
        win_count = len(wins)
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        total_wins = sum(wins) if wins else 0
        total_losses = abs(sum(losses)) if losses else 0
        profit_factor = (total_wins / total_losses) if total_losses > 0 else 999
        
        total_pnl = sum(pnls)
        
        # Max drawdown
        max_dd = 0
        peak = self.config.initial_capital
        for eq in self.equity_curve:
            value = eq['value']
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd
        
        return {
            "total_trades": total_trades,
            "winning_trades": win_count,
            "losing_trades": len(losses),
            "win_rate": round(win_rate, 2),
            "avg_win": round(sum(wins) / len(wins), 2) if wins else 0,
            "avg_loss": round(sum(losses) / len(losses), 2) if losses else 0,
            "profit_factor": round(min(profit_factor, 999), 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_amount": round(self.capital - self.config.initial_capital, 2),
            "max_drawdown": round(max_dd, 2),
            "initial_capital": self.config.initial_capital,
            "final_capital": round(self.capital, 2)
        }
    
    def reset(self) -> None:
        """Reset trading system state"""
        self.capital = self.config.initial_capital
        self.position = None
        self.trades = []
        self.equity_curve = []
        self.trade_counter = 0
        self.last_exit_reason = None
        self.last_exit_trend = 0
