"""
KOMAS Indicators Module
v4.0.1

This module contains technical indicators for the KOMAS trading system.

Available Indicators:
    - Dominant: Channel + Fibonacci levels with signal generation

Usage:
    from indicators import calculate_dominant, generate_signals
    
    # Calculate indicator levels only
    result = calculate_dominant(df, sensitivity=21)
    
    # Calculate with signal generation
    result = generate_signals(df, sensitivity=21)
"""

from .dominant import (
    # Main calculation functions
    calculate_dominant,
    generate_signals,
    
    # Analysis functions
    get_signal_summary,
    get_latest_signal,
    extract_signal_entries,
    
    # Helper functions
    get_current_levels,
    get_indicator_info,
    get_plot_levels,
    
    # Utility functions
    validate_sensitivity,
    validate_dataframe,
    calculate_with_multiple_sensitivities,
    
    # Constants
    SENSITIVITY_MIN,
    SENSITIVITY_MAX,
    SENSITIVITY_DEFAULT,
    FIB_LEVELS,
    SIGNAL_LONG,
    SIGNAL_SHORT,
    SIGNAL_NONE,
)

__all__ = [
    # Main functions
    'calculate_dominant',
    'generate_signals',
    
    # Analysis
    'get_signal_summary',
    'get_latest_signal',
    'extract_signal_entries',
    
    # Helpers
    'get_current_levels',
    'get_indicator_info',
    'get_plot_levels',
    
    # Utilities
    'validate_sensitivity',
    'validate_dataframe',
    'calculate_with_multiple_sensitivities',
    
    # Constants
    'SENSITIVITY_MIN',
    'SENSITIVITY_MAX',
    'SENSITIVITY_DEFAULT',
    'FIB_LEVELS',
    'SIGNAL_LONG',
    'SIGNAL_SHORT',
    'SIGNAL_NONE',
]

__version__ = '4.0.1'
