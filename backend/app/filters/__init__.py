"""
KOMAS v4.0 — Bot Filters Package
=================================

Modular filter system for controlling trade execution.

Filter Categories:
- TIME: Session, Weekday, Cooldown
- VOLATILITY: ATR, Volume, Extreme (future)
- TREND: BTC trend, Multi-TF, Regime (future)
- PORTFOLIO: Correlation, Direction, Sector (future)
- PROTECTION: Equity Curve, DD, Streak, Recovery (future)

Usage:
    from app.filters import (
        FilterChain,
        SessionFilter,
        WeekdayFilter,
        CooldownFilter,
        Signal,
        SignalContext,
        FilterRegistry
    )
    
    # Create filters
    session_filter = SessionFilter({"sessions": ["europe", "us"]})
    weekday_filter = WeekdayFilter({"allowed_days": [0, 1, 2, 3, 4]})
    cooldown_filter = CooldownFilter({"cooldown_minutes": 60})
    
    # Create chain
    chain = FilterChain([session_filter, weekday_filter, cooldown_filter])
    
    # Apply to signal
    signal = Signal(symbol="BTCUSDT", direction="long", entry_price=50000, ...)
    context = SignalContext(current_time=datetime.now(), ...)
    result = chain.apply(signal, context)
    
    if result.is_passed:
        # Execute trade
        pass

Chat #37: Filters Architecture
Chat #38: Time Filters
Author: KOMAS Team
Version: 4.0
"""

# Base classes
from .base import (
    # Enums
    FilterCategory,
    FilterPriority,
    FilterResult,
    
    # Data classes
    Signal,
    SignalContext,
    FilterDecision,
    FilterConfig,
    
    # Base class
    BaseFilter,
    
    # Helper functions
    create_pass_decision,
    create_block_decision,
    create_skip_decision,
    
    # Test filter classes
    AlwaysAllowFilter,
    AlwaysBlockFilter,
    ConditionalFilter,
)

# Registry
from .registry import (
    FilterRegistry,
    register_filter,
    discover_filters,
)

# Chain
from .chain import (
    FilterChain,
    ChainResult,
    create_chain_from_config,
)

# Time filters
from .time_filters import (
    SessionFilter,
    WeekdayFilter,
    CooldownFilter,
    
    # Constants
    TRADING_SESSIONS,
    SESSION_OVERLAPS,
    WEEKDAY_NAMES,
    
    # Helpers
    get_current_sessions,
    is_in_session,
    get_session_overlap,
    get_time_filter_summary,
    create_time_filter_chain,
)

# All exports
__all__ = [
    # Enums
    "FilterCategory",
    "FilterPriority",
    "FilterResult",
    
    # Data classes
    "Signal",
    "SignalContext",
    "FilterDecision",
    "FilterConfig",
    
    # Base class
    "BaseFilter",
    
    # Helpers
    "create_pass_decision",
    "create_block_decision",
    "create_skip_decision",
    
    # Test filter classes
    "AlwaysAllowFilter",
    "AlwaysBlockFilter",
    "ConditionalFilter",
    
    # Registry
    "FilterRegistry",
    "register_filter",
    "discover_filters",
    
    # Chain
    "FilterChain",
    "ChainResult",
    "create_chain_from_config",
    
    # Time filters
    "SessionFilter",
    "WeekdayFilter",
    "CooldownFilter",
    
    # Constants
    "TRADING_SESSIONS",
    "SESSION_OVERLAPS",
    "WEEKDAY_NAMES",
    
    # Time helpers
    "get_current_sessions",
    "is_in_session",
    "get_session_overlap",
    "get_time_filter_summary",
    "create_time_filter_chain",
]

# Version
__version__ = "4.0.0"
