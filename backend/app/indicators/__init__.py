"""
KOMAS v4.0 Indicators Module

This module contains all trading indicators for the KOMAS system.

Available Indicators:
- TRG (Trend Range Grid) - ATR-based trend detection (in indicator_routes.py)
- Dominant - Channel + Fibonacci levels

Usage:
    from app.indicators.dominant import calculate_dominant, get_current_levels
"""

from .dominant import (
    calculate_dominant,
    get_current_levels,
    validate_sensitivity,
    SENSITIVITY_MIN,
    SENSITIVITY_MAX,
    SENSITIVITY_DEFAULT,
)

__all__ = [
    'calculate_dominant',
    'get_current_levels',
    'validate_sensitivity',
    'SENSITIVITY_MIN',
    'SENSITIVITY_MAX',
    'SENSITIVITY_DEFAULT',
]

__version__ = '4.0.0'
