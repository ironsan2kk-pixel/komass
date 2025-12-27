"""
KOMAS v4.0 Services Module
==========================

This module exports the main service classes for signal scoring
and multi-timeframe analysis.

Chat #35: Score Multi-TF
"""

# Use try/except for flexible imports
try:
    # When running as part of app
    from .signal_score import (
        SignalScorer,
        SignalScoreResult,
        score_trades,
        get_grade_from_score,
        get_grade_color,
    )
except ImportError:
    # When running standalone
    from signal_score import (
        SignalScorer,
        SignalScoreResult,
        score_trades,
        get_grade_from_score,
        get_grade_color,
    )

try:
    from .multi_tf_loader import (
        MultiTFLoader,
        MultiTFResult,
        TFAnalysisResult,
        TrendDetectionMethod,
        TrendDirection,
        detect_trend_ema,
        detect_trend_supertrend,
        detect_trend_adx,
        detect_trend_combined,
        aggregate_to_higher_tf,
        get_higher_tfs,
        get_tf_weights,
        TF_HIERARCHY,
        TF_MINUTES,
        DEFAULT_TF_WEIGHTS,
    )
except ImportError:
    from multi_tf_loader import (
        MultiTFLoader,
        MultiTFResult,
        TFAnalysisResult,
        TrendDetectionMethod,
        TrendDirection,
        detect_trend_ema,
        detect_trend_supertrend,
        detect_trend_adx,
        detect_trend_combined,
        aggregate_to_higher_tf,
        get_higher_tfs,
        get_tf_weights,
        TF_HIERARCHY,
        TF_MINUTES,
        DEFAULT_TF_WEIGHTS,
    )

__all__ = [
    # Signal Score
    'SignalScorer',
    'SignalScoreResult',
    'score_trades',
    'get_grade_from_score',
    'get_grade_color',
    # Multi-TF Loader
    'MultiTFLoader',
    'MultiTFResult',
    'TFAnalysisResult',
    'TrendDetectionMethod',
    'TrendDirection',
    'detect_trend_ema',
    'detect_trend_supertrend',
    'detect_trend_adx',
    'detect_trend_combined',
    'aggregate_to_higher_tf',
    'get_higher_tfs',
    'get_tf_weights',
    'TF_HIERARCHY',
    'TF_MINUTES',
    'DEFAULT_TF_WEIGHTS',
]
