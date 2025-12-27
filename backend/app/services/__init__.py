"""
KOMAS v4.0 Services
===================

Service modules for signal scoring and multi-TF analysis.

Modules:
- signal_score: Signal quality evaluation (0-100 scale, A-F grades)
- multi_tf_loader: Higher timeframe data loading and trend detection
"""

from app.services.signal_score import (
    SignalScorer,
    SignalScoreResult,
    score_trades,
    get_grade_from_score,
    get_grade_color,
)

from app.services.multi_tf_loader import (
    MultiTFLoader,
    MultiTFResult,
    TrendDetectionMethod,
    TrendDirection,
    aggregate_to_higher_tf,
    get_higher_tfs,
    DEFAULT_TF_WEIGHTS,
    TF_HIERARCHY,
)

__all__ = [
    # Signal Score
    'SignalScorer',
    'SignalScoreResult',
    'score_trades',
    'get_grade_from_score',
    'get_grade_color',
    
    # Multi-TF
    'MultiTFLoader',
    'MultiTFResult',
    'TrendDetectionMethod',
    'TrendDirection',
    'aggregate_to_higher_tf',
    'get_higher_tfs',
    'DEFAULT_TF_WEIGHTS',
    'TF_HIERARCHY',
]
