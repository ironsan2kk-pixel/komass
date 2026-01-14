"""
Komas Trading Server - Position Risk Manager
=============================================
Advanced risk management for trading bots
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum
import logging

from .models import (
    BotConfig,
    SignalDirection,
    PositionStatus
)

logger = logging.getLogger("komas.bots.risk")


class RiskViolation(str, Enum):
    """Risk violation types"""
    MAX_POSITIONS = "max_positions"
    MAX_POSITION_SIZE = "max_position_size"
    MAX_DRAWDOWN = "max_drawdown"
    MAX_DAILY_LOSS = "max_daily_loss"
    MAX_SYMBOL_EXPOSURE = "max_symbol_exposure"
    INSUFFICIENT_CAPITAL = "insufficient_capital"
    MAX_CORRELATION = "max_correlation"


@dataclass
class RiskLimits:
    """Risk management limits"""
    # Position limits
    max_positions: int = 5
    max_position_size_percent: float = 20.0  # % of capital per position

    # Drawdown limits
    max_drawdown_percent: float = 15.0  # Max portfolio drawdown
    max_daily_loss_percent: float = 5.0  # Max loss per day

    # Symbol limits
    max_symbol_exposure_percent: float = 30.0  # Max % in one symbol
    max_correlated_positions: int = 3  # Max positions in correlated symbols

    # Capital limits
    min_capital_reserve_percent: float = 10.0  # Keep 10% reserve

    # Trading limits
    max_trades_per_day: int = 50
    max_trades_per_symbol: int = 10


@dataclass
class PositionInfo:
    """Position information for risk calculation"""
    symbol: str
    direction: SignalDirection
    size: float
    entry_price: float
    current_price: float
    pnl: float
    pnl_percent: float
    timestamp: datetime


class PositionRiskManager:
    """
    Position Risk Manager

    Manages risk limits for trading bot positions:
    - Position count and size limits
    - Drawdown monitoring
    - Symbol exposure limits
    - Capital management
    - Daily loss limits
    """

    def __init__(
        self,
        bot_config: BotConfig,
        risk_limits: Optional[RiskLimits] = None
    ):
        """Initialize risk manager"""
        self.bot_config = bot_config
        self.limits = risk_limits or RiskLimits()

        # State tracking
        self.initial_capital = bot_config.initial_capital
        self.current_capital = bot_config.initial_capital
        self.peak_capital = bot_config.initial_capital

        # Daily tracking
        self.daily_pnl: Dict[str, float] = {}  # date -> pnl
        self.daily_trades: Dict[str, int] = {}  # date -> count
        self.symbol_trades: Dict[str, Dict[str, int]] = {}  # date -> {symbol: count}

        # Active positions tracking
        self.active_positions: List[PositionInfo] = []

        logger.info(f"Risk Manager initialized: {self.limits}")

    def can_open_position(
        self,
        symbol: str,
        direction: SignalDirection,
        position_size: float,
        current_price: float
    ) -> Tuple[bool, Optional[RiskViolation], str]:
        """
        Check if new position can be opened

        Returns:
            (can_open, violation_type, message)
        """
        # Check 1: Max positions
        if len(self.active_positions) >= self.limits.max_positions:
            return False, RiskViolation.MAX_POSITIONS, \
                f"Max positions reached ({self.limits.max_positions})"

        # Check 2: Position size limit
        position_value = position_size * current_price
        max_position_value = self.current_capital * (self.limits.max_position_size_percent / 100)

        if position_value > max_position_value:
            return False, RiskViolation.MAX_POSITION_SIZE, \
                f"Position size {position_value:.2f} exceeds limit {max_position_value:.2f}"

        # Check 3: Symbol exposure
        symbol_exposure = self._get_symbol_exposure(symbol)
        new_exposure = symbol_exposure + position_value
        max_exposure = self.current_capital * (self.limits.max_symbol_exposure_percent / 100)

        if new_exposure > max_exposure:
            return False, RiskViolation.MAX_SYMBOL_EXPOSURE, \
                f"Symbol exposure {new_exposure:.2f} exceeds limit {max_exposure:.2f}"

        # Check 4: Capital reserve
        required_capital = position_value
        min_reserve = self.initial_capital * (self.limits.min_capital_reserve_percent / 100)
        available_capital = self.current_capital - self._get_total_exposure()

        if available_capital - required_capital < min_reserve:
            return False, RiskViolation.INSUFFICIENT_CAPITAL, \
                f"Insufficient capital. Reserve: {min_reserve:.2f}, Available: {available_capital:.2f}"

        # Check 5: Daily loss limit
        today = datetime.now().strftime("%Y-%m-%d")
        daily_loss = abs(min(0, self.daily_pnl.get(today, 0)))
        max_daily_loss = self.initial_capital * (self.limits.max_daily_loss_percent / 100)

        if daily_loss >= max_daily_loss:
            return False, RiskViolation.MAX_DAILY_LOSS, \
                f"Daily loss limit reached: {daily_loss:.2f} / {max_daily_loss:.2f}"

        # Check 6: Daily trades limit
        trades_today = self.daily_trades.get(today, 0)
        if trades_today >= self.limits.max_trades_per_day:
            return False, RiskViolation.MAX_DAILY_LOSS, \
                f"Daily trades limit reached: {trades_today} / {self.limits.max_trades_per_day}"

        # Check 7: Symbol trades limit
        symbol_trades_today = self.symbol_trades.get(today, {}).get(symbol, 0)
        if symbol_trades_today >= self.limits.max_trades_per_symbol:
            return False, RiskViolation.MAX_SYMBOL_EXPOSURE, \
                f"Symbol trades limit reached: {symbol_trades_today} / {self.limits.max_trades_per_symbol}"

        # All checks passed
        return True, None, "OK"

    def add_position(
        self,
        symbol: str,
        direction: SignalDirection,
        size: float,
        entry_price: float,
        timestamp: Optional[datetime] = None
    ):
        """Add new position to tracking"""
        position = PositionInfo(
            symbol=symbol,
            direction=direction,
            size=size,
            entry_price=entry_price,
            current_price=entry_price,
            pnl=0.0,
            pnl_percent=0.0,
            timestamp=timestamp or datetime.now()
        )

        self.active_positions.append(position)

        # Update daily trades
        today = position.timestamp.strftime("%Y-%m-%d")
        self.daily_trades[today] = self.daily_trades.get(today, 0) + 1

        if today not in self.symbol_trades:
            self.symbol_trades[today] = {}
        self.symbol_trades[today][symbol] = self.symbol_trades[today].get(symbol, 0) + 1

        logger.info(f"Added position: {symbol} {direction.value} {size:.4f} @ {entry_price}")

    def remove_position(
        self,
        symbol: str,
        close_price: float,
        pnl: float
    ):
        """Remove position and update capital"""
        # Find and remove position
        for i, pos in enumerate(self.active_positions):
            if pos.symbol == symbol:
                self.active_positions.pop(i)
                break

        # Update capital
        self.current_capital += pnl

        # Update peak
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

        # Update daily P&L
        today = datetime.now().strftime("%Y-%m-%d")
        self.daily_pnl[today] = self.daily_pnl.get(today, 0) + pnl

        logger.info(f"Closed position: {symbol} @ {close_price}, PnL: {pnl:.2f}")

    def update_position_prices(self, symbol: str, current_price: float):
        """Update current prices for positions"""
        for pos in self.active_positions:
            if pos.symbol == symbol:
                pos.current_price = current_price

                # Calculate unrealized P&L
                if pos.direction == SignalDirection.LONG:
                    pos.pnl = (current_price - pos.entry_price) * pos.size
                else:
                    pos.pnl = (pos.entry_price - current_price) * pos.size

                pos.pnl_percent = (pos.pnl / (pos.entry_price * pos.size)) * 100

    def check_drawdown(self) -> Tuple[bool, float]:
        """
        Check if drawdown limit exceeded

        Returns:
            (is_violated, current_drawdown_percent)
        """
        drawdown = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100
        is_violated = drawdown > self.limits.max_drawdown_percent

        if is_violated:
            logger.warning(f"Drawdown limit exceeded: {drawdown:.2f}% > {self.limits.max_drawdown_percent}%")

        return is_violated, drawdown

    def get_portfolio_status(self) -> Dict:
        """Get current portfolio risk status"""
        total_exposure = self._get_total_exposure()
        unrealized_pnl = sum(pos.pnl for pos in self.active_positions)

        # Calculate drawdown
        drawdown = 0.0
        if self.peak_capital > 0:
            drawdown = ((self.peak_capital - self.current_capital) / self.peak_capital) * 100

        # Daily stats
        today = datetime.now().strftime("%Y-%m-%d")
        daily_pnl = self.daily_pnl.get(today, 0)
        daily_trades = self.daily_trades.get(today, 0)

        return {
            "capital": {
                "initial": self.initial_capital,
                "current": self.current_capital,
                "peak": self.peak_capital,
                "unrealized_pnl": unrealized_pnl,
                "total_value": self.current_capital + unrealized_pnl
            },
            "positions": {
                "count": len(self.active_positions),
                "max": self.limits.max_positions,
                "total_exposure": total_exposure,
                "exposure_percent": (total_exposure / self.current_capital * 100) if self.current_capital > 0 else 0
            },
            "risk": {
                "drawdown_percent": drawdown,
                "max_drawdown": self.limits.max_drawdown_percent,
                "daily_pnl": daily_pnl,
                "daily_loss_limit": self.initial_capital * (self.limits.max_daily_loss_percent / 100)
            },
            "daily": {
                "pnl": daily_pnl,
                "trades": daily_trades,
                "max_trades": self.limits.max_trades_per_day
            }
        }

    def _get_symbol_exposure(self, symbol: str) -> float:
        """Get total exposure for a symbol"""
        return sum(
            pos.size * pos.current_price
            for pos in self.active_positions
            if pos.symbol == symbol
        )

    def _get_total_exposure(self) -> float:
        """Get total portfolio exposure"""
        return sum(
            pos.size * pos.current_price
            for pos in self.active_positions
        )

    def reset_daily_stats(self):
        """Reset daily statistics (call at day start)"""
        today = datetime.now().strftime("%Y-%m-%d")

        # Clean old daily data (keep last 30 days)
        cutoff_days = 30
        dates_to_remove = [
            date for date in self.daily_pnl.keys()
            if (datetime.now() - datetime.strptime(date, "%Y-%m-%d")).days > cutoff_days
        ]

        for date in dates_to_remove:
            self.daily_pnl.pop(date, None)
            self.daily_trades.pop(date, None)
            self.symbol_trades.pop(date, None)

        logger.info(f"Daily stats cleanup: removed {len(dates_to_remove)} old days")
