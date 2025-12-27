"""
KOMAS v4.0 Indicators Package

This package contains trading indicators for the KOMAS trading system.

Available Indicators:
- Dominant: Channel + Fibonacci levels indicator

Modules:
- dominant: Full implementation of the Dominant indicator
"""

# =============================================================================
# DOMINANT INDICATOR EXPORTS
# =============================================================================

from .dominant import (
    # Constants
    SENSITIVITY_MIN,
    SENSITIVITY_MAX,
    SENSITIVITY_DEFAULT,
    FIB_LEVELS,
    SIGNAL_LONG,
    SIGNAL_SHORT,
    SIGNAL_NONE,
    
    # Filter Constants (Chat #22)
    FILTER_NONE,
    FILTER_ATR,
    FILTER_RSI,
    FILTER_COMBINED,
    FILTER_VOLATILITY,
    FILTER_NAMES,
    FILTER_DEFAULTS,
    
    # SL Mode Constants (Chat #23)
    SL_MODE_FIXED,
    SL_MODE_AFTER_TP1,
    SL_MODE_AFTER_TP2,
    SL_MODE_AFTER_TP3,
    SL_MODE_CASCADE,
    SL_MODE_NAMES,
    SL_MODE_DESCRIPTIONS,
    SL_DEFAULTS,
    
    # Validation
    validate_sensitivity,
    validate_dataframe,
    validate_filter_type,
    validate_sl_mode,
    
    # Main Calculation
    calculate_dominant,
    
    # Filter Functions (Chat #22)
    calculate_rsi,
    calculate_atr,
    apply_filter,
    get_filter_info,
    get_filter_statistics,
    
    # SL Mode Functions (Chat #23)
    calculate_tp_levels,
    calculate_initial_sl,
    calculate_sl_level,
    track_position,
    get_sl_mode_info,
    get_sl_mode_statistics,
    
    # Signal Generation (Chat #21)
    generate_signals,
    generate_signals_with_filter,
    
    # Signal Analysis
    get_signal_summary,
    get_latest_signal,
    extract_signal_entries,
    
    # Helper Functions
    get_current_levels,
    get_indicator_info,
    calculate_with_multiple_sensitivities,
    
    # Visualization
    get_plot_levels,
)

# =============================================================================
# MODULE INFO
# =============================================================================

__version__ = '4.0.3'
__all__ = [
    # Constants
    'SENSITIVITY_MIN',
    'SENSITIVITY_MAX',
    'SENSITIVITY_DEFAULT',
    'FIB_LEVELS',
    'SIGNAL_LONG',
    'SIGNAL_SHORT',
    'SIGNAL_NONE',
    
    # Filter Constants
    'FILTER_NONE',
    'FILTER_ATR',
    'FILTER_RSI',
    'FILTER_COMBINED',
    'FILTER_VOLATILITY',
    'FILTER_NAMES',
    'FILTER_DEFAULTS',
    
    # SL Mode Constants
    'SL_MODE_FIXED',
    'SL_MODE_AFTER_TP1',
    'SL_MODE_AFTER_TP2',
    'SL_MODE_AFTER_TP3',
    'SL_MODE_CASCADE',
    'SL_MODE_NAMES',
    'SL_MODE_DESCRIPTIONS',
    'SL_DEFAULTS',
    
    # Validation
    'validate_sensitivity',
    'validate_dataframe',
    'validate_filter_type',
    'validate_sl_mode',
    
    # Main Calculation
    'calculate_dominant',
    
    # Filter Functions
    'calculate_rsi',
    'calculate_atr',
    'apply_filter',
    'get_filter_info',
    'get_filter_statistics',
    
    # SL Mode Functions
    'calculate_tp_levels',
    'calculate_initial_sl',
    'calculate_sl_level',
    'track_position',
    'get_sl_mode_info',
    'get_sl_mode_statistics',
    
    # Signal Generation
    'generate_signals',
    'generate_signals_with_filter',
    
    # Signal Analysis
    'get_signal_summary',
    'get_latest_signal',
    'extract_signal_entries',
    
    # Helper Functions
    'get_current_levels',
    'get_indicator_info',
    'calculate_with_multiple_sensitivities',
    
    # Visualization
    'get_plot_levels',
]
