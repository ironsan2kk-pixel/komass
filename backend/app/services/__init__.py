"""
KOMAS Services Module
=====================

Provides core services for the trading system.

Modules:
- signal_score: Signal quality evaluation (0-100 scale, A-F grades)
"""

from .signal_score import (
    SignalScorer,
    SignalScoreResult,
    Grade,
    score_trades,
    get_grade_from_score,
    get_grade_color,
    calculate_atr,
    calculate_rsi,
    calculate_adx,
    calculate_supertrend,
    calculate_support_resistance,
    calculate_volatility_percentile,
)

__all__ = [
    # Main classes
    'SignalScorer',
    'SignalScoreResult',
    'Grade',
    
    # Functions
    'score_trades',
    'get_grade_from_score',
    'get_grade_color',
    
    # Technical indicators
    'calculate_atr',
    'calculate_rsi',
    'calculate_adx',
    'calculate_supertrend',
    'calculate_support_resistance',
    'calculate_volatility_percentile',
]
