"""
KOMAS v4.0 — Bot Filters Package
=================================

Modular filter system for controlling trade execution.

Filter Categories:
- TIME: Session, Weekday, Cooldown
- VOLATILITY: ATR, Volume, Extreme
- TREND: BTC trend, Multi-TF, Regime
- PORTFOLIO: Correlation, Direction, Sector
- PROTECTION: Equity Curve, DD, Streak, Recovery

Usage:
    from app.filters import (
        # Manager (primary interface)
        FilterManager,
        create_filter_manager,
        get_filter_profiles,
        
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
        
        # Portfolio filters
        CorrelationFilter,
        DirectionFilter,
        SectorFilter,
        
        # Protection filters (if available)
        # EquityCurveFilter,
        # MaxDDFilter,
        # StreakFilter,
        # RecoveryFilter,
        
        # Core classes
        Signal,
        SignalContext,
    )
    
    # Create filter manager for a bot
    manager = FilterManager("my_bot")
    manager.apply_profile("balanced")
    
    # Or load from database
    manager.load_config("data/komas.db")
    
    # Apply to signal
    signal = Signal(symbol="BTCUSDT", direction="long", entry_price=50000, ...)
    context = SignalContext(current_time=datetime.now(), ...)
    result = manager.apply_filters(signal, context)
    
    if result.is_passed:
        # Execute trade
        pass

Chat #37: Filters Architecture
Chat #38: Time Filters
Chat #39: Filters Volatility
Chat #41: Filters Portfolio
Chat #43: Filters Integration
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

# Manager
from .manager import (
    FilterManager,
    FilterStats,
    DecisionLog,
    DecisionLogEntry,
    get_filter_profiles,
    create_filter_manager,
    validate_filter_config,
    get_filter_categories,
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

# Portfolio filters
from .portfolio_filters import (
    CorrelationFilter,
    DirectionFilter,
    SectorFilter,
    
    # Constants
    DEFAULT_MAX_CORRELATED_POSITIONS,
    DEFAULT_CORRELATION_THRESHOLD,
    DEFAULT_MAX_LONG_POSITIONS,
    DEFAULT_MAX_SHORT_POSITIONS,
    DEFAULT_NET_EXPOSURE_LIMIT,
    DEFAULT_MAX_PER_SECTOR,
    
    # Sector data
    SECTOR_MAPPING,
    AVAILABLE_SECTORS,
    CORRELATION_GROUPS,
    
    # Helpers
    get_sector,
    get_correlation_groups_for_symbol,
    are_correlated,
    count_correlated_positions,
    count_positions_by_direction,
    count_positions_by_sector,
    get_positions_in_sector,
    calculate_net_exposure,
    get_portfolio_summary,
    get_portfolio_filter_summary,
    create_portfolio_filter_chain,
    validate_portfolio_config,
    create_portfolio_profile,
)

# Try to import trend filters (may not exist yet)
try:
    from .trend_filters import (
        BTCTrendFilter,
        MultiTFFilter,
        RegimeFilter,
    )
    _HAS_TREND_FILTERS = True
except ImportError:
    _HAS_TREND_FILTERS = False

# Try to import protection filters (may not exist yet)
try:
    from .protection_filters import (
        EquityCurveFilter,
        MaxDDFilter,
        StreakFilter,
        RecoveryFilter,
    )
    _HAS_PROTECTION_FILTERS = True
except ImportError:
    _HAS_PROTECTION_FILTERS = False


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
    
    # Manager
    "FilterManager",
    "FilterStats",
    "DecisionLog",
    "DecisionLogEntry",
    "get_filter_profiles",
    "create_filter_manager",
    "validate_filter_config",
    "get_filter_categories",
    
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
    
    # Portfolio filters
    "CorrelationFilter",
    "DirectionFilter",
    "SectorFilter",
    
    # Portfolio constants
    "DEFAULT_MAX_CORRELATED_POSITIONS",
    "DEFAULT_CORRELATION_THRESHOLD",
    "DEFAULT_MAX_LONG_POSITIONS",
    "DEFAULT_MAX_SHORT_POSITIONS",
    "DEFAULT_NET_EXPOSURE_LIMIT",
    "DEFAULT_MAX_PER_SECTOR",
    
    # Sector data
    "SECTOR_MAPPING",
    "AVAILABLE_SECTORS",
    "CORRELATION_GROUPS",
    
    # Portfolio helpers
    "get_sector",
    "get_correlation_groups_for_symbol",
    "are_correlated",
    "count_correlated_positions",
    "count_positions_by_direction",
    "count_positions_by_sector",
    "get_positions_in_sector",
    "calculate_net_exposure",
    "get_portfolio_summary",
    "get_portfolio_filter_summary",
    "create_portfolio_filter_chain",
    "validate_portfolio_config",
    "create_portfolio_profile",
]

# Conditionally add trend filters
if _HAS_TREND_FILTERS:
    __all__.extend([
        "BTCTrendFilter",
        "MultiTFFilter",
        "RegimeFilter",
    ])

# Conditionally add protection filters
if _HAS_PROTECTION_FILTERS:
    __all__.extend([
        "EquityCurveFilter",
        "MaxDDFilter",
        "StreakFilter",
        "RecoveryFilter",
    ])


# Version
__version__ = "4.0.0"
