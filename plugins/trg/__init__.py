# -*- coding: utf-8 -*-
"""
TRG Plugin
==========
Complete TRG (Trend Range Grid) trading indicator plugin.

Version: 1.5.0 (UI Schema added)

Components:
- TRGIndicator: Core indicator calculations
- TRGSignalGenerator: Signal generation
- TRGTradingSystem: Trading logic (TP/SL)
- TRGFilterManager: Signal filters
- TRGOptimizer: Multi-core optimization
- TRGBacktest: Backtesting engine
- TRGUISchema: UI schema for frontend

Usage:
    from plugins.trg import (
        TRGIndicator,
        TRGSignalGenerator,
        TRGTradingSystem,
        TRGFilterManager,
        TRGOptimizer,
        TRGBacktest,
        get_ui_schema,
    )
"""

# Version
__version__ = "1.5.0"
__author__ = "Komas Team"

# =============================================================================
# LAZY IMPORTS
# =============================================================================

# Indicator
def _get_indicator():
    from .indicator import TRGIndicator, TRGParams, TRGResult
    return TRGIndicator, TRGParams, TRGResult

# Signals
def _get_signals():
    from .signals import TRGSignalGenerator, SignalType
    return TRGSignalGenerator, SignalType

# Trading
def _get_trading():
    from .trading import (
        TRGTradingSystem,
        TradingConfig,
        Position,
        Trade,
        TradeType,
        TradeResult,
    )
    return TRGTradingSystem, TradingConfig, Position, Trade, TradeType, TradeResult

# Filters
def _get_filters():
    from .filters import (
        TRGFilterManager,
        TRGFilterConfig,
        FILTER_PRESETS,
    )
    return TRGFilterManager, TRGFilterConfig, FILTER_PRESETS

# Optimizer
def _get_optimizer():
    from .optimizer import (
        TRGOptimizer,
        OptimizationMode,
        OptimizationConfig,
        OptimizationResult,
    )
    return TRGOptimizer, OptimizationMode, OptimizationConfig, OptimizationResult

# Backtest
def _get_backtest():
    from .backtest import (
        TRGBacktest,
        BacktestConfig,
        BacktestResult,
        MonthlyStats,
        TPStats,
    )
    return TRGBacktest, BacktestConfig, BacktestResult, MonthlyStats, TPStats

# UI Schema
def _get_ui_schema():
    from .ui_schema import (
        TRGUISchema,
        get_ui_schema,
        get_schema_dict,
        get_defaults,
        validate_settings,
        FieldType,
        SectionType,
        TabType,
    )
    return (
        TRGUISchema,
        get_ui_schema,
        get_schema_dict,
        get_defaults,
        validate_settings,
        FieldType,
        SectionType,
        TabType,
    )


# =============================================================================
# DIRECT EXPORTS (for common usage)
# =============================================================================

# These are imported when someone does: from plugins.trg import X
# They use lazy loading to avoid importing everything at once

class _LazyModule:
    """Lazy module loader for better import performance"""
    
    def __init__(self, loader_func, names):
        self._loader = loader_func
        self._names = names
        self._cache = None
    
    def _load(self):
        if self._cache is None:
            self._cache = self._loader()
        return self._cache
    
    def __getattr__(self, name):
        if name in self._names:
            items = self._load()
            return items[self._names.index(name)]
        raise AttributeError(f"module has no attribute '{name}'")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_plugin_info():
    """Get plugin metadata"""
    return {
        "id": "trg",
        "name": "TRG Indicator",
        "version": __version__,
        "author": __author__,
        "description": "Trend Range Grid indicator with full trading system",
        "components": [
            "TRGIndicator",
            "TRGSignalGenerator",
            "TRGTradingSystem",
            "TRGFilterManager",
            "TRGOptimizer",
            "TRGBacktest",
            "TRGUISchema",
        ],
    }


# Re-export ui_schema functions directly for easy access
from .ui_schema import (
    get_ui_schema,
    get_schema_dict,
    get_defaults,
    validate_settings,
)


# =============================================================================
# ALL EXPORTS
# =============================================================================

__all__ = [
    # Version
    "__version__",
    "__author__",
    
    # Plugin info
    "get_plugin_info",
    
    # UI Schema (direct exports)
    "get_ui_schema",
    "get_schema_dict",
    "get_defaults",
    "validate_settings",
    
    # Lazy loaded components (use: from plugins.trg.indicator import TRGIndicator)
    # - TRGIndicator, TRGParams, TRGResult
    # - TRGSignalGenerator, SignalType
    # - TRGTradingSystem, TradingConfig, Position, Trade, TradeType, TradeResult
    # - TRGFilterManager, TRGFilterConfig, FILTER_PRESETS
    # - TRGOptimizer, OptimizationMode, OptimizationConfig, OptimizationResult
    # - TRGBacktest, BacktestConfig, BacktestResult, MonthlyStats, TPStats
    # - TRGUISchema, FieldType, SectionType, TabType
]
