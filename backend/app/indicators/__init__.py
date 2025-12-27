"""
KOMAS Indicators Module
v4.0

This module contains all trading indicators for the KOMAS system.

Available Indicators:
- Dominant: Channel + Fibonacci levels indicator

Usage:
    from indicators.dominant import (
        calculate_dominant,
        generate_signals,
        apply_filter,
        FILTER_NONE,
        FILTER_ATR,
        FILTER_RSI,
        FILTER_COMBINED,
        FILTER_VOLATILITY,
    )
"""

from .dominant import (
    # Core functions
    calculate_dominant,
    generate_signals,
    generate_signals_with_filter,
    
    # Filter functions
    apply_filter,
    calculate_rsi,
    calculate_atr,
    get_filter_info,
    get_filter_statistics,
    
    # Helper functions
    get_current_levels,
    get_signal_summary,
    get_latest_signal,
    extract_signal_entries,
    get_indicator_info,
    calculate_with_multiple_sensitivities,
    get_plot_levels,
    
    # Validation
    validate_sensitivity,
    validate_dataframe,
    validate_filter_type,
    
    # Constants
    SENSITIVITY_MIN,
    SENSITIVITY_MAX,
    SENSITIVITY_DEFAULT,
    FIB_LEVELS,
    SIGNAL_LONG,
    SIGNAL_SHORT,
    SIGNAL_NONE,
    
    # Filter constants
    FILTER_NONE,
    FILTER_ATR,
    FILTER_RSI,
    FILTER_COMBINED,
    FILTER_VOLATILITY,
    FILTER_NAMES,
    FILTER_DEFAULTS,
)

__version__ = '4.0.2'
__all__ = [
    # Core
    'calculate_dominant',
    'generate_signals',
    'generate_signals_with_filter',
    
    # Filters
    'apply_filter',
    'calculate_rsi',
    'calculate_atr',
    'get_filter_info',
    'get_filter_statistics',
    
    # Helpers
    'get_current_levels',
    'get_signal_summary',
    'get_latest_signal',
    'extract_signal_entries',
    'get_indicator_info',
    'calculate_with_multiple_sensitivities',
    'get_plot_levels',
    
    # Validation
    'validate_sensitivity',
    'validate_dataframe',
    'validate_filter_type',
    
    # Constants
    'SENSITIVITY_MIN',
    'SENSITIVITY_MAX',
    'SENSITIVITY_DEFAULT',
    'FIB_LEVELS',
    'SIGNAL_LONG',
    'SIGNAL_SHORT',
    'SIGNAL_NONE',
    'FILTER_NONE',
    'FILTER_ATR',
    'FILTER_RSI',
    'FILTER_COMBINED',
    'FILTER_VOLATILITY',
    'FILTER_NAMES',
    'FILTER_DEFAULTS',
]
