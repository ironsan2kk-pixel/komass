"""
KOMAS v4.0 — Protection Filters
=================================

Protection-based filters for guarding against drawdowns and losing streaks.

Filters:
- EquityCurveFilter: Trade only when equity above/below moving average
- MaxDDFilter: Stop trading at maximum drawdown threshold
- StreakFilter: Pause after N consecutive losses
- RecoveryFilter: Reduce position size during drawdown recovery

Chat #42: Filters Protection
Author: KOMAS Team
Version: 4.0
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging

from .base import (
    BaseFilter,
    Signal,
    SignalContext,
    FilterDecision,
    FilterResult,
    FilterCategory,
    FilterPriority,
    create_pass_decision,
    create_block_decision,
    create_skip_decision
)
from .registry import register_filter

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# EquityCurveFilter defaults
DEFAULT_EQUITY_MA_PERIOD = 20
DEFAULT_EQUITY_MODE = "above"  # "above", "below", "both"
DEFAULT_PAUSE_ON_BELOW = True

# MaxDDFilter defaults
DEFAULT_MAX_DAILY_DD = 5.0  # 5% daily drawdown limit
DEFAULT_MAX_TOTAL_DD = 15.0  # 15% total drawdown limit
DEFAULT_DD_COOLDOWN_HOURS = 24  # Resume after 24 hours

# StreakFilter defaults
DEFAULT_MAX_CONSECUTIVE_LOSSES = 3
DEFAULT_PAUSE_TRADES = 5  # Skip next N signals
DEFAULT_RESET_ON_WIN = True

# RecoveryFilter defaults
DEFAULT_DD_THRESHOLD = 10.0  # Trigger at 10% DD
DEFAULT_SCALE_FACTOR = 0.5  # Reduce to 50%
DEFAULT_RECOVERY_TARGET = 5.0  # Resume normal at 5% DD


# =============================================================================
# ENUMS
# =============================================================================

class EquityCurveMode(Enum):
    """Mode for equity curve trading"""
    ABOVE = "above"   # Trade only when equity above MA
    BELOW = "below"   # Trade only when equity below MA (contrarian)
    BOTH = "both"     # Track both, configurable behavior


class DDType(Enum):
    """Type of drawdown"""
    DAILY = "daily"
    TOTAL = "total"
    BOTH = "both"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_simple_ma(data: List[float], period: int) -> Optional[float]:
    """
    Calculate simple moving average.
    
    Args:
        data: List of values
        period: MA period
        
    Returns:
        MA value or None if insufficient data
    """
    if not data or len(data) < period:
        return None
    return sum(data[-period:]) / period


def calculate_ema(data: List[float], period: int) -> Optional[float]:
    """
    Calculate exponential moving average.
    
    Args:
        data: List of values
        period: MA period
        
    Returns:
        EMA value or None if insufficient data
    """
    if not data or len(data) < period:
        return None
    
    multiplier = 2 / (period + 1)
    ema = sum(data[:period]) / period  # Start with SMA
    
    for value in data[period:]:
        ema = (value * multiplier) + (ema * (1 - multiplier))
    
    return ema


def calculate_equity_ma(equity_curve: List[float], period: int, 
                       use_ema: bool = False) -> Optional[float]:
    """
    Calculate moving average of equity curve.
    
    Args:
        equity_curve: List of equity values
        period: MA period
        use_ema: Use EMA instead of SMA
        
    Returns:
        MA value or None if insufficient data
    """
    if use_ema:
        return calculate_ema(equity_curve, period)
    return calculate_simple_ma(equity_curve, period)


def calculate_drawdown(current_equity: float, peak_equity: float) -> float:
    """
    Calculate drawdown percentage.
    
    Args:
        current_equity: Current equity value
        peak_equity: Peak equity value
        
    Returns:
        Drawdown as percentage (e.g., 10.0 for 10% DD)
    """
    if peak_equity <= 0:
        return 0.0
    if current_equity >= peak_equity:
        return 0.0
    return ((peak_equity - current_equity) / peak_equity) * 100


def calculate_daily_drawdown(equity_curve: List[float], 
                            trades_today: List[Dict]) -> float:
    """
    Calculate today's drawdown from day start.
    
    Args:
        equity_curve: Full equity curve
        trades_today: Trades from today
        
    Returns:
        Daily drawdown percentage
    """
    if not equity_curve:
        return 0.0
    
    # Get start of day equity
    if not trades_today:
        # No trades today, no daily DD
        return 0.0
    
    # Find peak equity today
    today_equity = [equity_curve[-1]]  # Current
    for trade in trades_today:
        if "equity_after" in trade:
            today_equity.append(trade["equity_after"])
    
    if not today_equity:
        return 0.0
    
    peak = max(today_equity)
    current = today_equity[-1] if today_equity else peak
    
    return calculate_drawdown(current, peak)


def get_equity_curve_peak(equity_curve: List[float]) -> float:
    """Get peak equity from curve"""
    if not equity_curve:
        return 0.0
    return max(equity_curve)


def count_consecutive_losses(recent_trades: List[Dict]) -> int:
    """
    Count consecutive losses from most recent trade backwards.
    
    Args:
        recent_trades: List of trade dicts with 'pnl' field
        
    Returns:
        Number of consecutive losses
    """
    if not recent_trades:
        return 0
    
    count = 0
    # Sort by exit_time descending (most recent first)
    sorted_trades = sorted(
        recent_trades,
        key=lambda t: t.get("exit_time", datetime.min),
        reverse=True
    )
    
    for trade in sorted_trades:
        pnl = trade.get("pnl", 0)
        if pnl < 0:
            count += 1
        else:
            break  # Stop on first win
    
    return count


def count_consecutive_wins(recent_trades: List[Dict]) -> int:
    """
    Count consecutive wins from most recent trade backwards.
    
    Args:
        recent_trades: List of trade dicts with 'pnl' field
        
    Returns:
        Number of consecutive wins
    """
    if not recent_trades:
        return 0
    
    count = 0
    sorted_trades = sorted(
        recent_trades,
        key=lambda t: t.get("exit_time", datetime.min),
        reverse=True
    )
    
    for trade in sorted_trades:
        pnl = trade.get("pnl", 0)
        if pnl >= 0:
            count += 1
        else:
            break
    
    return count


def get_trades_today(recent_trades: List[Dict], current_time: datetime) -> List[Dict]:
    """
    Get trades from today.
    
    Args:
        recent_trades: List of trade dicts with 'entry_time' field
        current_time: Current datetime
        
    Returns:
        List of trades from today
    """
    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    
    trades_today = []
    for trade in recent_trades:
        entry_time = trade.get("entry_time")
        if entry_time and entry_time >= today_start:
            trades_today.append(trade)
    
    return trades_today


def calculate_recovery_progress(current_dd: float, trigger_dd: float, 
                                target_dd: float) -> float:
    """
    Calculate recovery progress as percentage.
    
    Args:
        current_dd: Current drawdown %
        trigger_dd: DD % that triggered recovery mode
        target_dd: Target DD % to exit recovery mode
        
    Returns:
        Recovery progress 0-100%
    """
    if trigger_dd <= target_dd:
        return 100.0  # Already recovered
    
    if current_dd >= trigger_dd:
        return 0.0  # Not started
    
    if current_dd <= target_dd:
        return 100.0  # Fully recovered
    
    total_recovery_needed = trigger_dd - target_dd
    recovery_so_far = trigger_dd - current_dd
    
    return min(100.0, (recovery_so_far / total_recovery_needed) * 100)


def get_protection_state(context: SignalContext) -> Dict[str, Any]:
    """
    Get comprehensive protection state from context.
    
    Args:
        context: Signal context
        
    Returns:
        Dict with protection metrics
    """
    equity_curve = context.equity_curve
    current_equity = context.current_equity
    starting_equity = context.starting_equity
    recent_trades = context.recent_trades
    
    # Calculate peak and drawdown
    peak = get_equity_curve_peak(equity_curve) if equity_curve else starting_equity
    current_dd = calculate_drawdown(current_equity, peak) if peak > 0 else 0.0
    
    # Calculate daily DD
    trades_today = get_trades_today(recent_trades, context.current_time)
    daily_dd = calculate_daily_drawdown(equity_curve, trades_today)
    
    # Count streaks
    consecutive_losses = count_consecutive_losses(recent_trades)
    consecutive_wins = count_consecutive_wins(recent_trades)
    
    return {
        "current_equity": current_equity,
        "peak_equity": peak,
        "starting_equity": starting_equity,
        "current_dd_percent": current_dd,
        "daily_dd_percent": daily_dd,
        "consecutive_losses": consecutive_losses,
        "consecutive_wins": consecutive_wins,
        "total_trades": len(recent_trades),
        "trades_today": len(trades_today),
        "equity_curve_length": len(equity_curve),
    }


def validate_protection_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate protection filter configuration.
    
    Args:
        config: Configuration dict
        
    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []
    
    # Equity curve validation
    if "ma_period" in config:
        period = config["ma_period"]
        if not isinstance(period, int) or period < 2:
            errors.append(f"ma_period must be integer >= 2, got {period}")
    
    if "mode" in config:
        mode = config["mode"]
        if mode not in ["above", "below", "both"]:
            errors.append(f"mode must be 'above', 'below', or 'both', got {mode}")
    
    # DD validation
    if "max_daily_dd" in config:
        dd = config["max_daily_dd"]
        if not isinstance(dd, (int, float)) or dd <= 0:
            errors.append(f"max_daily_dd must be positive number, got {dd}")
    
    if "max_total_dd" in config:
        dd = config["max_total_dd"]
        if not isinstance(dd, (int, float)) or dd <= 0:
            errors.append(f"max_total_dd must be positive number, got {dd}")
    
    if "cooldown_hours" in config:
        hours = config["cooldown_hours"]
        if not isinstance(hours, int) or hours < 0:
            errors.append(f"cooldown_hours must be non-negative integer, got {hours}")
    
    # Streak validation
    if "max_consecutive_losses" in config:
        losses = config["max_consecutive_losses"]
        if not isinstance(losses, int) or losses < 1:
            errors.append(f"max_consecutive_losses must be positive integer, got {losses}")
    
    if "pause_trades" in config:
        pause = config["pause_trades"]
        if not isinstance(pause, int) or pause < 0:
            errors.append(f"pause_trades must be non-negative integer, got {pause}")
    
    # Recovery validation
    if "dd_threshold" in config:
        threshold = config["dd_threshold"]
        if not isinstance(threshold, (int, float)) or threshold <= 0:
            errors.append(f"dd_threshold must be positive number, got {threshold}")
    
    if "scale_factor" in config:
        factor = config["scale_factor"]
        if not isinstance(factor, (int, float)) or not (0 < factor <= 1):
            errors.append(f"scale_factor must be between 0 and 1, got {factor}")
    
    if "recovery_target" in config:
        target = config["recovery_target"]
        if not isinstance(target, (int, float)) or target < 0:
            errors.append(f"recovery_target must be non-negative number, got {target}")
    
    return len(errors) == 0, errors


def get_protection_filter_summary(filters: List["BaseFilter"]) -> Dict[str, Any]:
    """
    Get summary of active protection filters.
    
    Args:
        filters: List of filter instances
        
    Returns:
        Summary dict
    """
    protection_filters = [
        f for f in filters 
        if f.category == FilterCategory.PROTECTION
    ]
    
    summary = {
        "total_filters": len(protection_filters),
        "active_filters": [f.name for f in protection_filters if f.enabled],
        "filters": {}
    }
    
    for f in protection_filters:
        summary["filters"][f.name] = {
            "enabled": f.enabled,
            "config": f.config,
        }
    
    return summary


def create_protection_filter_chain(
    equity_curve: bool = True,
    max_dd: bool = True,
    streak: bool = True,
    recovery: bool = True,
    equity_config: Optional[Dict] = None,
    dd_config: Optional[Dict] = None,
    streak_config: Optional[Dict] = None,
    recovery_config: Optional[Dict] = None,
) -> List["BaseFilter"]:
    """
    Create a protection filter chain with common configurations.
    
    Args:
        equity_curve: Enable equity curve filter
        max_dd: Enable max drawdown filter
        streak: Enable streak filter
        recovery: Enable recovery filter
        equity_config: Config for equity curve filter
        dd_config: Config for DD filter
        streak_config: Config for streak filter
        recovery_config: Config for recovery filter
        
    Returns:
        List of filter instances
    """
    filters = []
    
    if equity_curve:
        config = equity_config or {}
        filters.append(EquityCurveFilter(config))
    
    if max_dd:
        config = dd_config or {}
        filters.append(MaxDDFilter(config))
    
    if streak:
        config = streak_config or {}
        filters.append(StreakFilter(config))
    
    if recovery:
        config = recovery_config or {}
        filters.append(RecoveryFilter(config))
    
    return filters


def create_protection_profile(profile: str = "balanced") -> Dict[str, Dict]:
    """
    Create a protection profile with predefined settings.
    
    Args:
        profile: Profile name ("conservative", "balanced", "aggressive")
        
    Returns:
        Dict of filter_name -> config
    """
    profiles = {
        "conservative": {
            "equity_curve_filter": {
                "enabled": True,
                "ma_period": 20,
                "mode": "above",
                "pause_on_below": True,
            },
            "max_dd_filter": {
                "enabled": True,
                "max_daily_dd": 3.0,
                "max_total_dd": 10.0,
                "cooldown_hours": 24,
            },
            "streak_filter": {
                "enabled": True,
                "max_consecutive_losses": 2,
                "pause_trades": 10,
                "reset_on_win": True,
            },
            "recovery_filter": {
                "enabled": True,
                "dd_threshold": 5.0,
                "scale_factor": 0.25,
                "recovery_target": 2.0,
            },
        },
        "balanced": {
            "equity_curve_filter": {
                "enabled": True,
                "ma_period": 20,
                "mode": "above",
                "pause_on_below": True,
            },
            "max_dd_filter": {
                "enabled": True,
                "max_daily_dd": 5.0,
                "max_total_dd": 15.0,
                "cooldown_hours": 24,
            },
            "streak_filter": {
                "enabled": True,
                "max_consecutive_losses": 3,
                "pause_trades": 5,
                "reset_on_win": True,
            },
            "recovery_filter": {
                "enabled": True,
                "dd_threshold": 10.0,
                "scale_factor": 0.5,
                "recovery_target": 5.0,
            },
        },
        "aggressive": {
            "equity_curve_filter": {
                "enabled": True,
                "ma_period": 10,
                "mode": "above",
                "pause_on_below": True,
            },
            "max_dd_filter": {
                "enabled": True,
                "max_daily_dd": 8.0,
                "max_total_dd": 25.0,
                "cooldown_hours": 12,
            },
            "streak_filter": {
                "enabled": True,
                "max_consecutive_losses": 5,
                "pause_trades": 3,
                "reset_on_win": True,
            },
            "recovery_filter": {
                "enabled": True,
                "dd_threshold": 15.0,
                "scale_factor": 0.75,
                "recovery_target": 10.0,
            },
        },
        "disabled": {
            "equity_curve_filter": {"enabled": False},
            "max_dd_filter": {"enabled": False},
            "streak_filter": {"enabled": False},
            "recovery_filter": {"enabled": False},
        },
    }
    
    if profile not in profiles:
        logger.warning(f"Unknown profile '{profile}', using 'balanced'")
        profile = "balanced"
    
    return profiles[profile]


# =============================================================================
# EQUITY CURVE FILTER
# =============================================================================

@register_filter
class EquityCurveFilter(BaseFilter):
    """
    Filter based on equity curve position relative to moving average.
    
    Trade only when equity is above/below its moving average.
    This helps avoid trading during drawdown periods.
    
    Modes:
    - "above": Trade only when equity > MA (default)
    - "below": Trade only when equity < MA (contrarian)
    - "both": Trade in both conditions with different behavior
    
    Example:
        # Trade only when equity is above 20-period MA
        filter = EquityCurveFilter({
            "ma_period": 20,
            "mode": "above",
            "pause_on_below": True
        })
    """
    
    name = "equity_curve_filter"
    description = "Trade based on equity curve position vs moving average"
    category = FilterCategory.PROTECTION
    priority = FilterPriority.CRITICAL
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        # Set defaults
        config.setdefault("ma_period", DEFAULT_EQUITY_MA_PERIOD)
        config.setdefault("mode", DEFAULT_EQUITY_MODE)
        config.setdefault("pause_on_below", DEFAULT_PAUSE_ON_BELOW)
        config.setdefault("use_ema", False)
        config.setdefault("buffer_percent", 0.0)  # Buffer zone around MA
        
        super().__init__(config)
        
        self.ma_period = self.config["ma_period"]
        self.mode = self.config["mode"]
        self.pause_on_below = self.config["pause_on_below"]
        self.use_ema = self.config["use_ema"]
        self.buffer_percent = self.config["buffer_percent"]
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """Check if equity curve allows trading"""
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        equity_curve = context.equity_curve
        current_equity = context.current_equity
        
        # Need enough data for MA calculation
        if len(equity_curve) < self.ma_period:
            return create_pass_decision(
                self.name,
                f"Insufficient data for MA calculation (have {len(equity_curve)}, need {self.ma_period})",
                equity_curve_length=len(equity_curve),
                ma_period=self.ma_period
            )
        
        # Calculate MA
        ma_value = calculate_equity_ma(equity_curve, self.ma_period, self.use_ema)
        
        if ma_value is None:
            return create_pass_decision(
                self.name,
                "Could not calculate MA",
                equity_curve_length=len(equity_curve)
            )
        
        # Calculate buffer zone
        buffer = ma_value * (self.buffer_percent / 100)
        upper_band = ma_value + buffer
        lower_band = ma_value - buffer
        
        # Determine position
        is_above = current_equity > upper_band
        is_below = current_equity < lower_band
        is_in_buffer = not is_above and not is_below
        
        details = {
            "current_equity": current_equity,
            "ma_value": round(ma_value, 2),
            "ma_period": self.ma_period,
            "upper_band": round(upper_band, 2),
            "lower_band": round(lower_band, 2),
            "position": "above" if is_above else ("below" if is_below else "buffer"),
            "mode": self.mode,
        }
        
        # Apply mode logic
        if self.mode == "above":
            if is_above or is_in_buffer:
                return create_pass_decision(
                    self.name,
                    f"Equity ${current_equity:.2f} >= MA ${ma_value:.2f}",
                    **details
                )
            else:
                if self.pause_on_below:
                    return create_block_decision(
                        self.name,
                        f"Equity ${current_equity:.2f} < MA ${ma_value:.2f} (paused)",
                        **details
                    )
                return create_pass_decision(
                    self.name,
                    f"Equity below MA but not paused",
                    **details
                )
        
        elif self.mode == "below":
            # Contrarian: trade when below MA
            if is_below or is_in_buffer:
                return create_pass_decision(
                    self.name,
                    f"Equity ${current_equity:.2f} <= MA ${ma_value:.2f}",
                    **details
                )
            else:
                if self.pause_on_below:  # In this mode, pause_on_below means pause_on_above
                    return create_block_decision(
                        self.name,
                        f"Equity ${current_equity:.2f} > MA ${ma_value:.2f} (paused)",
                        **details
                    )
                return create_pass_decision(
                    self.name,
                    f"Equity above MA but not paused",
                    **details
                )
        
        else:  # both
            # Allow both, just track position
            return create_pass_decision(
                self.name,
                f"Equity ${current_equity:.2f} vs MA ${ma_value:.2f} (both mode)",
                **details
            )
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable equity curve filter"
            },
            "ma_period": {
                "type": "int",
                "default": DEFAULT_EQUITY_MA_PERIOD,
                "min": 2,
                "max": 200,
                "description": "Moving average period"
            },
            "mode": {
                "type": "str",
                "default": DEFAULT_EQUITY_MODE,
                "options": ["above", "below", "both"],
                "description": "Trading mode relative to MA"
            },
            "pause_on_below": {
                "type": "bool",
                "default": DEFAULT_PAUSE_ON_BELOW,
                "description": "Pause trading when condition not met"
            },
            "use_ema": {
                "type": "bool",
                "default": False,
                "description": "Use EMA instead of SMA"
            },
            "buffer_percent": {
                "type": "float",
                "default": 0.0,
                "min": 0.0,
                "max": 10.0,
                "description": "Buffer zone around MA (%)"
            },
        }


# =============================================================================
# MAX DRAWDOWN FILTER
# =============================================================================

@register_filter
class MaxDDFilter(BaseFilter):
    """
    Filter based on maximum drawdown limits.
    
    Stop trading when drawdown exceeds daily or total limits.
    Optionally resume after cooldown period.
    
    Example:
        # Stop at 5% daily DD or 15% total DD
        filter = MaxDDFilter({
            "max_daily_dd": 5.0,
            "max_total_dd": 15.0,
            "cooldown_hours": 24
        })
    """
    
    name = "max_dd_filter"
    description = "Stop trading at maximum drawdown threshold"
    category = FilterCategory.PROTECTION
    priority = FilterPriority.CRITICAL
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        # Set defaults
        config.setdefault("max_daily_dd", DEFAULT_MAX_DAILY_DD)
        config.setdefault("max_total_dd", DEFAULT_MAX_TOTAL_DD)
        config.setdefault("cooldown_hours", DEFAULT_DD_COOLDOWN_HOURS)
        config.setdefault("check_daily", True)
        config.setdefault("check_total", True)
        
        super().__init__(config)
        
        self.max_daily_dd = self.config["max_daily_dd"]
        self.max_total_dd = self.config["max_total_dd"]
        self.cooldown_hours = self.config["cooldown_hours"]
        self.check_daily = self.config["check_daily"]
        self.check_total = self.config["check_total"]
        
        # Track when DD limit was hit
        self._dd_hit_time: Optional[datetime] = None
        self._dd_hit_type: Optional[str] = None
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """Check if drawdown allows trading"""
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        current_time = context.current_time
        
        # Check if in cooldown period
        if self._dd_hit_time is not None:
            cooldown_end = self._dd_hit_time + timedelta(hours=self.cooldown_hours)
            if current_time < cooldown_end:
                remaining = (cooldown_end - current_time).total_seconds() / 3600
                return create_block_decision(
                    self.name,
                    f"In cooldown after {self._dd_hit_type} DD hit ({remaining:.1f}h remaining)",
                    dd_hit_time=self._dd_hit_time.isoformat(),
                    cooldown_end=cooldown_end.isoformat(),
                    remaining_hours=round(remaining, 2)
                )
            else:
                # Cooldown ended, reset
                self._dd_hit_time = None
                self._dd_hit_type = None
        
        # Calculate current drawdowns
        equity_curve = context.equity_curve
        current_equity = context.current_equity
        starting_equity = context.starting_equity
        recent_trades = context.recent_trades
        
        # Total DD
        peak = get_equity_curve_peak(equity_curve) if equity_curve else starting_equity
        total_dd = calculate_drawdown(current_equity, peak)
        
        # Daily DD
        trades_today = get_trades_today(recent_trades, current_time)
        daily_dd = calculate_daily_drawdown(equity_curve, trades_today)
        
        details = {
            "current_equity": current_equity,
            "peak_equity": round(peak, 2),
            "total_dd_percent": round(total_dd, 2),
            "daily_dd_percent": round(daily_dd, 2),
            "max_daily_dd": self.max_daily_dd,
            "max_total_dd": self.max_total_dd,
        }
        
        # Check daily DD
        if self.check_daily and daily_dd >= self.max_daily_dd:
            self._dd_hit_time = current_time
            self._dd_hit_type = "daily"
            return create_block_decision(
                self.name,
                f"Daily DD {daily_dd:.2f}% >= limit {self.max_daily_dd}%",
                **details
            )
        
        # Check total DD
        if self.check_total and total_dd >= self.max_total_dd:
            self._dd_hit_time = current_time
            self._dd_hit_type = "total"
            return create_block_decision(
                self.name,
                f"Total DD {total_dd:.2f}% >= limit {self.max_total_dd}%",
                **details
            )
        
        return create_pass_decision(
            self.name,
            f"DD within limits (daily: {daily_dd:.2f}%, total: {total_dd:.2f}%)",
            **details
        )
    
    def reset(self) -> None:
        """Reset DD tracking state"""
        self._dd_hit_time = None
        self._dd_hit_type = None
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable max DD filter"
            },
            "max_daily_dd": {
                "type": "float",
                "default": DEFAULT_MAX_DAILY_DD,
                "min": 0.5,
                "max": 50.0,
                "description": "Maximum daily drawdown (%)"
            },
            "max_total_dd": {
                "type": "float",
                "default": DEFAULT_MAX_TOTAL_DD,
                "min": 1.0,
                "max": 100.0,
                "description": "Maximum total drawdown (%)"
            },
            "cooldown_hours": {
                "type": "int",
                "default": DEFAULT_DD_COOLDOWN_HOURS,
                "min": 0,
                "max": 168,
                "description": "Hours before resuming after DD hit"
            },
            "check_daily": {
                "type": "bool",
                "default": True,
                "description": "Check daily drawdown"
            },
            "check_total": {
                "type": "bool",
                "default": True,
                "description": "Check total drawdown"
            },
        }


# =============================================================================
# STREAK FILTER
# =============================================================================

@register_filter
class StreakFilter(BaseFilter):
    """
    Filter based on losing/winning streaks.
    
    Pause trading after N consecutive losses.
    Optionally reset pause counter on next win.
    
    Example:
        # Pause after 3 consecutive losses, skip 5 signals
        filter = StreakFilter({
            "max_consecutive_losses": 3,
            "pause_trades": 5,
            "reset_on_win": True
        })
    """
    
    name = "streak_filter"
    description = "Pause after consecutive losses"
    category = FilterCategory.PROTECTION
    priority = FilterPriority.CRITICAL
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        # Set defaults
        config.setdefault("max_consecutive_losses", DEFAULT_MAX_CONSECUTIVE_LOSSES)
        config.setdefault("pause_trades", DEFAULT_PAUSE_TRADES)
        config.setdefault("reset_on_win", DEFAULT_RESET_ON_WIN)
        config.setdefault("track_wins_too", False)  # Also track winning streaks
        config.setdefault("max_consecutive_wins", 10)  # For win streak tracking
        
        super().__init__(config)
        
        self.max_consecutive_losses = self.config["max_consecutive_losses"]
        self.pause_trades = self.config["pause_trades"]
        self.reset_on_win = self.config["reset_on_win"]
        self.track_wins_too = self.config["track_wins_too"]
        self.max_consecutive_wins = self.config["max_consecutive_wins"]
        
        # Track pause state
        self._signals_to_skip = 0
        self._last_consecutive_losses = 0
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """Check if streak allows trading"""
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        recent_trades = context.recent_trades
        
        # Count consecutive losses
        consecutive_losses = count_consecutive_losses(recent_trades)
        consecutive_wins = count_consecutive_wins(recent_trades)
        
        details = {
            "consecutive_losses": consecutive_losses,
            "consecutive_wins": consecutive_wins,
            "max_consecutive_losses": self.max_consecutive_losses,
            "signals_to_skip": self._signals_to_skip,
            "pause_trades": self.pause_trades,
        }
        
        # Check if we need to pause (loss streak detected)
        if consecutive_losses >= self.max_consecutive_losses:
            # Check if this is a new streak
            if consecutive_losses > self._last_consecutive_losses:
                self._signals_to_skip = self.pause_trades
                self._last_consecutive_losses = consecutive_losses
        
        # Reset on win if configured
        if self.reset_on_win and consecutive_wins > 0 and self._last_consecutive_losses > 0:
            self._signals_to_skip = 0
            self._last_consecutive_losses = 0
        
        # Check if still in pause mode
        if self._signals_to_skip > 0:
            self._signals_to_skip -= 1
            return create_block_decision(
                self.name,
                f"Paused after {consecutive_losses} consecutive losses ({self._signals_to_skip + 1} signals remaining)",
                **details
            )
        
        # Optionally track winning streaks
        if self.track_wins_too and consecutive_wins >= self.max_consecutive_wins:
            return create_block_decision(
                self.name,
                f"Paused after {consecutive_wins} consecutive wins (cooling off)",
                **details
            )
        
        return create_pass_decision(
            self.name,
            f"Streak OK (losses: {consecutive_losses}, wins: {consecutive_wins})",
            **details
        )
    
    def on_trade_complete(self, trade_result: Dict[str, Any]) -> None:
        """Update state after trade completes"""
        pnl = trade_result.get("pnl", 0)
        
        if pnl >= 0 and self.reset_on_win:
            # Reset pause on win
            self._signals_to_skip = 0
            self._last_consecutive_losses = 0
    
    def reset(self) -> None:
        """Reset streak tracking state"""
        self._signals_to_skip = 0
        self._last_consecutive_losses = 0
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable streak filter"
            },
            "max_consecutive_losses": {
                "type": "int",
                "default": DEFAULT_MAX_CONSECUTIVE_LOSSES,
                "min": 1,
                "max": 20,
                "description": "Max consecutive losses before pause"
            },
            "pause_trades": {
                "type": "int",
                "default": DEFAULT_PAUSE_TRADES,
                "min": 0,
                "max": 50,
                "description": "Number of signals to skip"
            },
            "reset_on_win": {
                "type": "bool",
                "default": DEFAULT_RESET_ON_WIN,
                "description": "Reset pause counter on win"
            },
            "track_wins_too": {
                "type": "bool",
                "default": False,
                "description": "Also track winning streaks"
            },
            "max_consecutive_wins": {
                "type": "int",
                "default": 10,
                "min": 1,
                "max": 50,
                "description": "Max consecutive wins before pause (if tracking)"
            },
        }


# =============================================================================
# RECOVERY FILTER
# =============================================================================

@register_filter
class RecoveryFilter(BaseFilter):
    """
    Filter that modifies position sizing during drawdown recovery.
    
    When drawdown exceeds threshold:
    - Scale down position size by factor
    - Gradually return to normal sizing as recovery progresses
    
    This filter doesn't block signals, but adds metadata for position sizing.
    
    Example:
        # At 10% DD, reduce to 50% size until recovery to 5% DD
        filter = RecoveryFilter({
            "dd_threshold": 10.0,
            "scale_factor": 0.5,
            "recovery_target": 5.0
        })
    """
    
    name = "recovery_filter"
    description = "Reduce position size during drawdown recovery"
    category = FilterCategory.PROTECTION
    priority = FilterPriority.CRITICAL
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        config = config or {}
        
        # Set defaults
        config.setdefault("dd_threshold", DEFAULT_DD_THRESHOLD)
        config.setdefault("scale_factor", DEFAULT_SCALE_FACTOR)
        config.setdefault("recovery_target", DEFAULT_RECOVERY_TARGET)
        config.setdefault("gradual_recovery", True)  # Gradually increase size
        config.setdefault("block_on_extreme_dd", False)  # Block signals entirely
        config.setdefault("extreme_dd_threshold", 25.0)  # DD % for blocking
        
        super().__init__(config)
        
        self.dd_threshold = self.config["dd_threshold"]
        self.scale_factor = self.config["scale_factor"]
        self.recovery_target = self.config["recovery_target"]
        self.gradual_recovery = self.config["gradual_recovery"]
        self.block_on_extreme = self.config["block_on_extreme_dd"]
        self.extreme_dd_threshold = self.config["extreme_dd_threshold"]
        
        # Track if we're in recovery mode
        self._in_recovery = False
        self._recovery_started_dd = 0.0
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """Check DD and calculate scale factor"""
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        # Calculate current DD
        equity_curve = context.equity_curve
        current_equity = context.current_equity
        starting_equity = context.starting_equity
        
        peak = get_equity_curve_peak(equity_curve) if equity_curve else starting_equity
        current_dd = calculate_drawdown(current_equity, peak)
        
        details = {
            "current_equity": current_equity,
            "peak_equity": round(peak, 2),
            "current_dd_percent": round(current_dd, 2),
            "dd_threshold": self.dd_threshold,
            "recovery_target": self.recovery_target,
            "in_recovery": self._in_recovery,
        }
        
        # Check for extreme DD (block)
        if self.block_on_extreme and current_dd >= self.extreme_dd_threshold:
            return create_block_decision(
                self.name,
                f"Extreme DD {current_dd:.2f}% >= {self.extreme_dd_threshold}% (blocked)",
                **details
            )
        
        # Check if entering recovery mode
        if current_dd >= self.dd_threshold and not self._in_recovery:
            self._in_recovery = True
            self._recovery_started_dd = current_dd
        
        # Check if exiting recovery mode
        if self._in_recovery and current_dd <= self.recovery_target:
            self._in_recovery = False
            self._recovery_started_dd = 0.0
        
        # Calculate effective scale factor
        if self._in_recovery:
            if self.gradual_recovery:
                # Gradually increase scale as we recover
                recovery_progress = calculate_recovery_progress(
                    current_dd, self._recovery_started_dd, self.recovery_target
                )
                # Scale from scale_factor to 1.0 based on progress
                effective_scale = self.scale_factor + (
                    (1.0 - self.scale_factor) * (recovery_progress / 100)
                )
            else:
                effective_scale = self.scale_factor
            
            # Add scale factor to signal metadata
            if not hasattr(signal, 'metadata'):
                signal.metadata = {}
            signal.metadata["recovery_scale_factor"] = effective_scale
            
            details["effective_scale"] = round(effective_scale, 3)
            details["recovery_progress"] = round(
                calculate_recovery_progress(current_dd, self._recovery_started_dd, self.recovery_target), 1
            )
            
            return create_pass_decision(
                self.name,
                f"Recovery mode: scale={effective_scale:.2f}x (DD: {current_dd:.2f}%)",
                **details
            )
        
        return create_pass_decision(
            self.name,
            f"Normal mode (DD: {current_dd:.2f}% < threshold {self.dd_threshold}%)",
            **details
        )
    
    def reset(self) -> None:
        """Reset recovery state"""
        self._in_recovery = False
        self._recovery_started_dd = 0.0
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable recovery filter"
            },
            "dd_threshold": {
                "type": "float",
                "default": DEFAULT_DD_THRESHOLD,
                "min": 1.0,
                "max": 50.0,
                "description": "DD % to trigger recovery mode"
            },
            "scale_factor": {
                "type": "float",
                "default": DEFAULT_SCALE_FACTOR,
                "min": 0.1,
                "max": 1.0,
                "description": "Position size multiplier in recovery"
            },
            "recovery_target": {
                "type": "float",
                "default": DEFAULT_RECOVERY_TARGET,
                "min": 0.0,
                "max": 49.0,
                "description": "DD % to exit recovery mode"
            },
            "gradual_recovery": {
                "type": "bool",
                "default": True,
                "description": "Gradually increase size during recovery"
            },
            "block_on_extreme_dd": {
                "type": "bool",
                "default": False,
                "description": "Block signals entirely at extreme DD"
            },
            "extreme_dd_threshold": {
                "type": "float",
                "default": 25.0,
                "min": 10.0,
                "max": 100.0,
                "description": "DD % for blocking signals"
            },
        }
