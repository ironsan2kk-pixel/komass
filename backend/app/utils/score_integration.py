"""
Signal Score Integration for Indicator Routes
==============================================

Adds signal scoring capability to backtest results.

Usage in indicator_routes.py:
    from app.utils.score_integration import add_signal_scores_to_trades

    # After calculating trades in calculate_indicator:
    trades = add_signal_scores_to_trades(trades, df, settings)

Chat #36: Score UI - Backend Integration
"""

import logging
from typing import List, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def add_signal_scores_to_trades(
    trades: List[Dict[str, Any]],
    df: pd.DataFrame,
    settings: Any = None,
    auto_load_higher_tfs: bool = False,
) -> List[Dict[str, Any]]:
    """
    Add signal scores to a list of trades.
    
    Args:
        trades: List of trade dictionaries
        df: OHLCV DataFrame used for the backtest
        settings: Optional settings object with filter configuration
        auto_load_higher_tfs: Whether to load higher TF data (slower but more accurate)
        
    Returns:
        List of trades with signal_score, signal_grade, and score_components added
    """
    if not trades or len(trades) == 0:
        return trades
    
    if len(df) < 20:
        logger.warning("Insufficient data for signal scoring (< 20 candles)")
        return trades
    
    try:
        # Import signal scoring module
        from app.services.signal_score import SignalScorer, score_trades, get_grade_from_score
    except ImportError as e:
        logger.warning(f"Signal Score module not available: {e}")
        return trades
    
    # Build filter configuration from settings
    filters = {}
    if settings:
        filters = {
            'supertrend_enabled': getattr(settings, 'use_supertrend', True),
            'rsi_enabled': getattr(settings, 'use_rsi_filter', True),
            'adx_enabled': getattr(settings, 'use_adx_filter', True),
            'volume_enabled': getattr(settings, 'use_volume_filter', True),
        }
    
    try:
        # Score all trades using batch function
        scored_trades = score_trades(
            trades=trades,
            df=df,
            filters=filters,
            higher_tf_data=None,  # Could load if auto_load_higher_tfs is True
        )
        
        logger.info(f"Added signal scores to {len(scored_trades)} trades")
        return scored_trades
        
    except Exception as e:
        logger.error(f"Error scoring trades: {e}")
        return trades


def get_grade_statistics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics by signal grade.
    
    Args:
        trades: List of trades with signal_score/signal_grade
        
    Returns:
        Dictionary with statistics per grade
    """
    try:
        from app.services.signal_score import get_grade_from_score
    except ImportError:
        return {}
    
    if not trades:
        return {}
    
    # Initialize stats
    stats = {
        'A': {'count': 0, 'wins': 0, 'total_pnl': 0},
        'B': {'count': 0, 'wins': 0, 'total_pnl': 0},
        'C': {'count': 0, 'wins': 0, 'total_pnl': 0},
        'D': {'count': 0, 'wins': 0, 'total_pnl': 0},
        'F': {'count': 0, 'wins': 0, 'total_pnl': 0},
    }
    
    for trade in trades:
        grade = trade.get('signal_grade')
        if not grade:
            score = trade.get('signal_score')
            if score is not None:
                grade = get_grade_from_score(score)
        
        if grade and grade in stats:
            stats[grade]['count'] += 1
            pnl = trade.get('pnl', 0) or 0
            stats[grade]['total_pnl'] += pnl
            if pnl > 0:
                stats[grade]['wins'] += 1
    
    # Calculate percentages
    total = sum(s['count'] for s in stats.values())
    
    result = {}
    for grade, s in stats.items():
        result[grade] = {
            'count': s['count'],
            'percentage': round((s['count'] / total * 100), 1) if total > 0 else 0,
            'win_rate': round((s['wins'] / s['count'] * 100), 1) if s['count'] > 0 else 0,
            'avg_pnl': round(s['total_pnl'] / s['count'], 2) if s['count'] > 0 else 0,
            'total_pnl': round(s['total_pnl'], 2),
        }
    
    return result


# Example integration code for indicator_routes.py
INTEGRATION_EXAMPLE = """
# Add to imports at top of indicator_routes.py:
from app.utils.score_integration import add_signal_scores_to_trades, get_grade_statistics

# After calculating trades in calculate_indicator() function:
# Add signal scores to trades
if settings.include_signal_scores:
    trades = add_signal_scores_to_trades(trades, df, settings)
    
    # Optionally add grade statistics to result
    grade_stats = get_grade_statistics(trades)

# Include in response:
return {
    "trades": trades,
    "grade_statistics": grade_stats,
    ...
}
"""


__all__ = [
    'add_signal_scores_to_trades',
    'get_grade_statistics',
]
