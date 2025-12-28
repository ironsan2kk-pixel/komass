"""
KOMAS v4.0 — Time Filters
==========================

Time-based filters for controlling when trades can be executed.

Filters:
- SessionFilter: Control trading by market session (Asia/Europe/US)
- WeekdayFilter: Control trading by day of week
- CooldownFilter: Enforce waiting period between trades

Chat #38: Filters Time
Author: KOMAS Team
Version: 4.0
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any
import logging

try:
    import pytz
    HAS_PYTZ = True
except ImportError:
    HAS_PYTZ = False

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

# Trading sessions in UTC
TRADING_SESSIONS = {
    "asia": {
        "name": "Asia",
        "start_hour": 0,   # 00:00 UTC
        "end_hour": 8,     # 08:00 UTC
        "description": "Tokyo, Hong Kong, Singapore markets"
    },
    "europe": {
        "name": "Europe", 
        "start_hour": 8,   # 08:00 UTC
        "end_hour": 16,    # 16:00 UTC
        "description": "London, Frankfurt markets"
    },
    "us": {
        "name": "US",
        "start_hour": 13,  # 13:00 UTC (NYSE opens at 14:30)
        "end_hour": 22,    # 22:00 UTC
        "description": "New York markets"
    }
}

# Session overlaps
SESSION_OVERLAPS = {
    "asia_europe": {
        "name": "Asia-Europe Overlap",
        "start_hour": 8,
        "end_hour": 9,
        "sessions": ["asia", "europe"],
        "description": "High liquidity period"
    },
    "europe_us": {
        "name": "Europe-US Overlap",
        "start_hour": 13,
        "end_hour": 16,
        "sessions": ["europe", "us"],
        "description": "Highest liquidity period"
    }
}

# Day names
WEEKDAY_NAMES = {
    0: "Monday",
    1: "Tuesday",
    2: "Wednesday",
    3: "Thursday",
    4: "Friday",
    5: "Saturday",
    6: "Sunday"
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_utc_now() -> datetime:
    """Get current UTC time"""
    return datetime.now(timezone.utc)


def to_utc(dt: datetime, tz_name: str = "UTC") -> datetime:
    """
    Convert datetime to UTC.
    
    Args:
        dt: Input datetime
        tz_name: Timezone name (e.g., "UTC", "US/Eastern")
        
    Returns:
        UTC datetime
    """
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc)
    
    if tz_name == "UTC":
        return dt.replace(tzinfo=timezone.utc)
    
    if HAS_PYTZ:
        try:
            tz = pytz.timezone(tz_name)
            localized = tz.localize(dt)
            return localized.astimezone(timezone.utc)
        except Exception as e:
            logger.warning(f"Failed to convert timezone {tz_name}: {e}")
            return dt.replace(tzinfo=timezone.utc)
    
    # Fallback to UTC if pytz not available
    return dt.replace(tzinfo=timezone.utc)


def get_current_sessions(dt: datetime) -> List[str]:
    """
    Get list of active sessions for given UTC time.
    
    Args:
        dt: UTC datetime
        
    Returns:
        List of active session names
    """
    hour = dt.hour
    active = []
    
    for session_id, session in TRADING_SESSIONS.items():
        start = session["start_hour"]
        end = session["end_hour"]
        
        if start <= hour < end:
            active.append(session_id)
    
    return active


def is_in_session(dt: datetime, session: str) -> bool:
    """
    Check if datetime is within a trading session.
    
    Args:
        dt: UTC datetime
        session: Session name (asia/europe/us)
        
    Returns:
        True if in session
    """
    session = session.lower()
    if session not in TRADING_SESSIONS:
        logger.warning(f"Unknown session: {session}")
        return False
    
    hour = dt.hour
    start = TRADING_SESSIONS[session]["start_hour"]
    end = TRADING_SESSIONS[session]["end_hour"]
    
    return start <= hour < end


def get_session_overlap(dt: datetime) -> Optional[str]:
    """
    Get current session overlap if any.
    
    Args:
        dt: UTC datetime
        
    Returns:
        Overlap name or None
    """
    hour = dt.hour
    
    for overlap_id, overlap in SESSION_OVERLAPS.items():
        if overlap["start_hour"] <= hour < overlap["end_hour"]:
            return overlap_id
    
    return None


# =============================================================================
# SESSION FILTER
# =============================================================================

@register_filter
class SessionFilter(BaseFilter):
    """
    Filter trades by trading session.
    
    Allows trading only during specified market sessions:
    - ASIA: 00:00 - 08:00 UTC
    - EUROPE: 08:00 - 16:00 UTC
    - US: 13:00 - 22:00 UTC
    
    Config:
        sessions: List of allowed sessions (default: all)
        timezone: Timezone for time calculation (default: UTC)
        include_overlaps: Whether to allow during overlaps (default: True)
    """
    
    name = "session_filter"
    description = "Filter trades by trading session (Asia/Europe/US)"
    category = FilterCategory.TIME
    priority = FilterPriority.HIGH
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable session filtering"
            },
            "sessions": {
                "type": "list",
                "default": ["asia", "europe", "us"],
                "options": ["asia", "europe", "us"],
                "description": "Allowed trading sessions"
            },
            "timezone": {
                "type": "str",
                "default": "UTC",
                "description": "Timezone for time calculation"
            },
            "include_overlaps": {
                "type": "bool",
                "default": True,
                "description": "Allow trading during session overlaps"
            }
        }
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """
        Check if current time is within allowed trading sessions.
        """
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        # Get configured sessions
        allowed_sessions = self.config.get("sessions", ["asia", "europe", "us"])
        if not allowed_sessions:
            return create_pass_decision(self.name, "No session restrictions")
        
        # Normalize session names
        allowed_sessions = [s.lower() for s in allowed_sessions]
        
        # Check for "all" - meaning all sessions allowed
        if "all" in allowed_sessions:
            return create_pass_decision(self.name, "All sessions allowed")
        
        # Get current time in UTC
        tz_name = self.config.get("timezone", "UTC")
        current_time = to_utc(context.current_time, tz_name)
        
        # Get active sessions
        active_sessions = get_current_sessions(current_time)
        
        # Check overlap
        include_overlaps = self.config.get("include_overlaps", True)
        overlap = get_session_overlap(current_time)
        
        # Check if any allowed session is active
        for session in allowed_sessions:
            if session in active_sessions:
                return create_pass_decision(
                    self.name,
                    f"Trading allowed in {session.upper()} session",
                    active_sessions=active_sessions,
                    current_hour=current_time.hour,
                    overlap=overlap
                )
        
        # Check overlap condition
        if include_overlaps and overlap:
            overlap_info = SESSION_OVERLAPS.get(overlap, {})
            overlap_sessions = overlap_info.get("sessions", [])
            
            # Check if any overlap session is in allowed list
            for os in overlap_sessions:
                if os in allowed_sessions:
                    return create_pass_decision(
                        self.name,
                        f"Trading allowed during {overlap_info.get('name', overlap)} overlap",
                        overlap=overlap,
                        current_hour=current_time.hour
                    )
        
        # Not in any allowed session
        return create_block_decision(
            self.name,
            f"Outside allowed sessions ({', '.join(s.upper() for s in allowed_sessions)})",
            current_hour=current_time.hour,
            active_sessions=active_sessions,
            allowed_sessions=allowed_sessions
        )


# =============================================================================
# WEEKDAY FILTER
# =============================================================================

@register_filter
class WeekdayFilter(BaseFilter):
    """
    Filter trades by day of week.
    
    Config:
        allowed_days: List of allowed weekday numbers (0=Monday, 6=Sunday)
        timezone: Timezone for day calculation
    """
    
    name = "weekday_filter"
    description = "Filter trades by day of week"
    category = FilterCategory.TIME
    priority = FilterPriority.HIGH
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable weekday filtering"
            },
            "allowed_days": {
                "type": "list",
                "default": [0, 1, 2, 3, 4],  # Monday to Friday
                "options": [0, 1, 2, 3, 4, 5, 6],
                "description": "Allowed weekdays (0=Monday, 6=Sunday)"
            },
            "timezone": {
                "type": "str",
                "default": "UTC",
                "description": "Timezone for day calculation"
            }
        }
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """
        Check if current day is in allowed weekdays.
        """
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        # Get configured days
        allowed_days = self.config.get("allowed_days", [0, 1, 2, 3, 4])
        if not allowed_days:
            return create_pass_decision(self.name, "No day restrictions")
        
        # Get current time
        tz_name = self.config.get("timezone", "UTC")
        current_time = to_utc(context.current_time, tz_name)
        current_weekday = current_time.weekday()  # 0 = Monday
        
        day_name = WEEKDAY_NAMES.get(current_weekday, f"Day {current_weekday}")
        
        if current_weekday in allowed_days:
            return create_pass_decision(
                self.name,
                f"Trading allowed on {day_name}",
                current_weekday=current_weekday,
                day_name=day_name
            )
        
        # Create list of allowed day names
        allowed_names = [WEEKDAY_NAMES.get(d, str(d)) for d in sorted(allowed_days)]
        
        return create_block_decision(
            self.name,
            f"Trading not allowed on {day_name} (allowed: {', '.join(allowed_names)})",
            current_weekday=current_weekday,
            day_name=day_name,
            allowed_days=allowed_days
        )


# =============================================================================
# COOLDOWN FILTER
# =============================================================================

@register_filter
class CooldownFilter(BaseFilter):
    """
    Enforce waiting period between trades.
    
    Different cooldowns based on last trade result:
    - after_win_cooldown: Shorter wait after winning trade
    - cooldown_minutes: Default wait time
    - after_loss_cooldown: Longer wait after losing trade
    
    Config:
        cooldown_minutes: Default cooldown in minutes (default: 60)
        after_win_cooldown: Cooldown after winning trade (default: 30)
        after_loss_cooldown: Cooldown after losing trade (default: 120)
        per_symbol: Apply cooldown per symbol or globally (default: True)
    """
    
    name = "cooldown_filter"
    description = "Enforce waiting period between trades"
    category = FilterCategory.TIME
    priority = FilterPriority.HIGH
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # Track last trade time per symbol
        self._last_trades: Dict[str, Dict] = {}
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable cooldown filtering"
            },
            "cooldown_minutes": {
                "type": "int",
                "default": 60,
                "min": 0,
                "max": 1440,  # 24 hours
                "description": "Default cooldown in minutes"
            },
            "after_win_cooldown": {
                "type": "int",
                "default": 30,
                "min": 0,
                "max": 1440,
                "description": "Cooldown after winning trade (minutes)"
            },
            "after_loss_cooldown": {
                "type": "int",
                "default": 120,
                "min": 0,
                "max": 1440,
                "description": "Cooldown after losing trade (minutes)"
            },
            "per_symbol": {
                "type": "bool",
                "default": True,
                "description": "Apply cooldown per symbol (vs globally)"
            }
        }
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """
        Check if enough time has passed since last trade.
        """
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        # Get cooldown settings
        default_cooldown = self.config.get("cooldown_minutes", 60)
        after_win = self.config.get("after_win_cooldown", 30)
        after_loss = self.config.get("after_loss_cooldown", 120)
        per_symbol = self.config.get("per_symbol", True)
        
        # Check if we have recent trades in context
        recent_trades = context.recent_trades
        if not recent_trades:
            # No recent trades, check internal tracking
            last_trade = self._get_last_trade(signal.symbol if per_symbol else "__global__")
            if not last_trade:
                return create_pass_decision(
                    self.name,
                    "No previous trades, cooldown not applicable"
                )
            recent_trades = [last_trade]
        
        # Find the most recent relevant trade
        if per_symbol:
            # Filter trades for this symbol
            symbol_trades = [t for t in recent_trades if t.get("symbol") == signal.symbol]
            if not symbol_trades:
                return create_pass_decision(
                    self.name,
                    f"No previous trades for {signal.symbol}"
                )
            last_trade = symbol_trades[-1]
        else:
            # Use most recent trade overall
            last_trade = recent_trades[-1]
        
        # Get last trade time
        exit_time = last_trade.get("exit_time")
        if exit_time is None:
            return create_pass_decision(self.name, "Last trade has no exit time")
        
        # Ensure exit_time is datetime
        if isinstance(exit_time, str):
            try:
                exit_time = datetime.fromisoformat(exit_time.replace('Z', '+00:00'))
            except ValueError:
                return create_pass_decision(self.name, "Invalid exit time format")
        
        # Calculate time since last trade
        current_time = context.current_time
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        if exit_time.tzinfo is None:
            exit_time = exit_time.replace(tzinfo=timezone.utc)
        
        time_since = (current_time - exit_time).total_seconds() / 60  # minutes
        
        # Determine required cooldown based on last trade result
        pnl = last_trade.get("pnl", last_trade.get("pnl_percent", 0))
        if pnl > 0:
            required_cooldown = after_win
            trade_result = "win"
        elif pnl < 0:
            required_cooldown = after_loss
            trade_result = "loss"
        else:
            required_cooldown = default_cooldown
            trade_result = "breakeven"
        
        # Check if cooldown has passed
        if time_since >= required_cooldown:
            return create_pass_decision(
                self.name,
                f"Cooldown passed ({time_since:.1f} min since last {trade_result})",
                time_since_minutes=time_since,
                required_cooldown=required_cooldown,
                trade_result=trade_result
            )
        
        remaining = required_cooldown - time_since
        return create_block_decision(
            self.name,
            f"Cooldown active: {remaining:.1f} min remaining (after {trade_result})",
            time_since_minutes=time_since,
            required_cooldown=required_cooldown,
            remaining_minutes=remaining,
            trade_result=trade_result
        )
    
    def on_trade_complete(self, trade_result: Dict[str, Any]) -> None:
        """
        Track completed trade for cooldown calculation.
        """
        symbol = trade_result.get("symbol", "__global__")
        self._last_trades[symbol] = trade_result
        self._last_trades["__global__"] = trade_result
    
    def _get_last_trade(self, symbol: str) -> Optional[Dict]:
        """Get last trade for symbol"""
        return self._last_trades.get(symbol)
    
    def reset(self) -> None:
        """Reset internal state"""
        self._last_trades.clear()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_time_filter_summary(
    current_time: datetime,
    session_config: Dict[str, Any] = None,
    weekday_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Get summary of current time filter status.
    
    Args:
        current_time: Current datetime
        session_config: SessionFilter config (optional)
        weekday_config: WeekdayFilter config (optional)
        
    Returns:
        Dict with current status
    """
    utc_time = to_utc(current_time)
    
    return {
        "current_time_utc": utc_time.isoformat(),
        "current_hour": utc_time.hour,
        "current_weekday": utc_time.weekday(),
        "weekday_name": WEEKDAY_NAMES.get(utc_time.weekday()),
        "active_sessions": get_current_sessions(utc_time),
        "current_overlap": get_session_overlap(utc_time),
        "available_sessions": list(TRADING_SESSIONS.keys()),
        "session_details": TRADING_SESSIONS,
        "overlap_details": SESSION_OVERLAPS
    }


def create_time_filter_chain(
    session_enabled: bool = True,
    sessions: List[str] = None,
    weekday_enabled: bool = True,
    allowed_days: List[int] = None,
    cooldown_enabled: bool = True,
    cooldown_minutes: int = 60
) -> List[BaseFilter]:
    """
    Create a list of time filters with common configurations.
    
    Args:
        session_enabled: Enable session filter
        sessions: Allowed sessions
        weekday_enabled: Enable weekday filter  
        allowed_days: Allowed weekday numbers
        cooldown_enabled: Enable cooldown filter
        cooldown_minutes: Default cooldown
        
    Returns:
        List of configured filter instances
    """
    filters = []
    
    if session_enabled:
        session_config = {
            "enabled": True,
            "sessions": sessions or ["asia", "europe", "us"]
        }
        filters.append(SessionFilter(session_config))
    
    if weekday_enabled:
        weekday_config = {
            "enabled": True,
            "allowed_days": allowed_days if allowed_days is not None else [0, 1, 2, 3, 4]
        }
        filters.append(WeekdayFilter(weekday_config))
    
    if cooldown_enabled:
        cooldown_config = {
            "enabled": True,
            "cooldown_minutes": cooldown_minutes
        }
        filters.append(CooldownFilter(cooldown_config))
    
    return filters
