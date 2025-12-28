"""
KOMAS Trading System - Filters Module
=====================================

Modular filter system for trading signal validation.

Architecture:
- BaseFilter: Abstract base class for all filters
- FilterRegistry: Centralized filter management
- FilterChain: Sequential filter application
- FilterResult/ChainResult: Decision data structures

Categories:
- TIME: Session, weekday, cooldown filters
- VOLATILITY: ATR, volume, extreme condition filters
- TREND: BTC trend, multi-TF, market regime filters
- PORTFOLIO: Correlation, direction, sector filters
- PROTECTION: Equity curve, drawdown, streak filters

Usage:
    from app.filters import FilterChain, get_registry, SignalContext
    
    # Register custom filter
    from app.filters import register_filter, BaseFilter
    
    @register_filter
    class MyFilter(BaseFilter):
        name = "my_filter"
        ...
    
    # Create filter chain
    chain = FilterChain()
    chain.add_by_name("session_filter", {"sessions": ["london"]})
    chain.add_by_name("atr_filter", {"min_atr": 0.5})
    
    # Apply to signal
    context = SignalContext(signal=signal, symbol="BTCUSDT", ...)
    result = chain.apply(context)
    
    if result.allowed:
        # Execute trade
    else:
        print(f"Blocked: {result.primary_rejection.reason}")

Chat #37: Filters Architecture
Author: KOMAS Team
Version: 4.0
"""

# =============================================================================
# IMPORTS
# =============================================================================

# Base classes and data structures
from .base import (
    # Enums
    FilterCategory,
    FilterPriority,
    # Data classes
    FilterResult,
    FilterConfig,
    SignalContext,
    # Base class
    BaseFilter,
    # Test filters
    AlwaysAllowFilter,
    AlwaysBlockFilter,
)

# Registry
from .registry import (
    FilterRegistry,
    get_registry,
    register_filter,
)

# Filter chain
from .chain import (
    ChainResult,
    FilterChain,
    FilterChainBuilder,
)


# =============================================================================
# REGISTER BUILT-IN TEST FILTERS
# =============================================================================

def _register_builtin_filters() -> None:
    """Register built-in filters on module import"""
    registry = get_registry()
    
    # Register test filters
    try:
        registry.register(AlwaysAllowFilter)
        registry.register(AlwaysBlockFilter)
    except ValueError:
        # Already registered
        pass


# Register on import
_register_builtin_filters()


# =============================================================================
# VERSION
# =============================================================================

__version__ = "4.0.0"
__author__ = "KOMAS Team"


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Version
    "__version__",
    "__author__",
    # Enums
    "FilterCategory",
    "FilterPriority",
    # Data classes
    "FilterResult",
    "FilterConfig",
    "SignalContext",
    "ChainResult",
    # Base class
    "BaseFilter",
    # Registry
    "FilterRegistry",
    "get_registry",
    "register_filter",
    # Chain
    "FilterChain",
    "FilterChainBuilder",
    # Test filters
    "AlwaysAllowFilter",
    "AlwaysBlockFilter",
]
