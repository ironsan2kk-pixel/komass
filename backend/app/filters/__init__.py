"""
KOMAS v4.0 — Bot Filters Package
=================================

Modular filter system for controlling trade execution.

Filter Categories:
- TIME: Session, Weekday, Cooldown
- VOLATILITY: ATR, Volume, Extreme
- TREND: BTC trend, Multi-TF, Regime (future)
- PORTFOLIO: Correlation, Direction, Sector (future)
- PROTECTION: Equity Curve, DD, Streak, Recovery (future)

Usage:
    from app.filters import (
        # Chain and registry
        FilterChain,
        FilterRegistry,
        
        # Time filters
        SessionFilter,
        WeekdayFilter,
        CooldownFilter,
        
        # Volatility filters
        ATRFilter,
        VolumeFilter,
        ExtremeFilter,
        
        # Core classes
        Signal,
        SignalContext,
    )
    
    # Create filters
    session_filter = SessionFilter({"sessions": ["europe", "us"]})
    atr_filter = ATRFilter({"min_atr": 1.0, "max_atr": 5.0, "use_atr_percent": True})
    volume_filter = VolumeFilter({"min_volume_ratio": 1.5})
    extreme_filter = ExtremeFilter({"atr_multiplier": 3.0, "pause_minutes": 60})
    
    # Create chain
    chain = FilterChain([session_filter, atr_filter, volume_filter, extreme_filter])
    
    # Apply to signal
    signal = Signal(symbol="BTCUSDT", direction="long", entry_price=50000, ...)
    context = SignalContext(current_time=datetime.now(), atr=1500, volume=1000000, ...)
    result = chain.apply(signal, context)
    
    if result.is_passed:
        # Execute trade
        pass

Chat #37: Filters Architecture
Chat #38: Time Filters
Chat #39: Filters Volatility
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

# Volatility filters
from .volatility_filters import (
    ATRFilter,
    VolumeFilter,
    ExtremeFilter,
    
    # Constants
    DEFAULT_ATR_PERIOD,
    DEFAULT_ATR_MULTIPLIER,
    DEFAULT_VOLUME_MA_PERIOD,
    DEFAULT_MIN_VOLUME_RATIO,
    DEFAULT_EXTREME_ATR_MULTIPLIER,
    DEFAULT_EXTREME_VOLUME_MULTIPLIER,
    DEFAULT_EXTREME_PAUSE_MINUTES,
    
    # Helpers
    calculate_atr_percent,
    calculate_volume_ratio,
    is_extreme_atr,
    is_extreme_volume,
    format_atr_value,
    get_volatility_state,
    get_volatility_filter_summary,
    create_volatility_filter_chain,
    create_volatility_profile,
    validate_volatility_config,
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
    
    # Time constants
    "TRADING_SESSIONS",
    "SESSION_OVERLAPS",
    "WEEKDAY_NAMES",
    
    # Time helpers
    "get_current_sessions",
    "is_in_session",
    "get_session_overlap",
    "get_time_filter_summary",
    "create_time_filter_chain",
    
    # Volatility filters
    "ATRFilter",
    "VolumeFilter",
    "ExtremeFilter",
    
    # Volatility constants
    "DEFAULT_ATR_PERIOD",
    "DEFAULT_ATR_MULTIPLIER",
    "DEFAULT_VOLUME_MA_PERIOD",
    "DEFAULT_MIN_VOLUME_RATIO",
    "DEFAULT_EXTREME_ATR_MULTIPLIER",
    "DEFAULT_EXTREME_VOLUME_MULTIPLIER",
    "DEFAULT_EXTREME_PAUSE_MINUTES",
    
    # Volatility helpers
    "calculate_atr_percent",
    "calculate_volume_ratio",
    "is_extreme_atr",
    "is_extreme_volume",
    "format_atr_value",
    "get_volatility_state",
    "get_volatility_filter_summary",
    "create_volatility_filter_chain",
    "create_volatility_profile",
    "validate_volatility_config",
]

# Version
__version__ = "4.0.0"
