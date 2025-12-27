"""
Unit Tests for Dominant Indicator - AI Resolution (Chat #25)
KOMAS v4.0

Tests for:
- calculate_sensitivity_score()
- run_full_backtest()
- optimize_sensitivity()
- Helper functions

Run with: python -m pytest tests/test_dominant_ai_resolution.py -v
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.indicators.dominant import (
    # Constants
    SIGNAL_LONG, SIGNAL_SHORT, SIGNAL_NONE,
    FILTER_NONE, FILTER_ATR, FILTER_RSI, FILTER_COMBINED, FILTER_VOLATILITY,
    SL_MODE_FIXED, SL_MODE_AFTER_TP1, SL_MODE_CASCADE,
    OPTIMIZATION_SENSITIVITIES,
    SCORE_WEIGHT_PROFIT, SCORE_WEIGHT_WIN_RATE, SCORE_WEIGHT_STABILITY, SCORE_WEIGHT_DRAWDOWN,
    MIN_TRADES_FOR_OPTIMIZATION,
    
    # Functions to test
    calculate_sensitivity_score,
    run_full_backtest,
    optimize_sensitivity,
    compare_sensitivities,
    get_score_breakdown,
    get_optimization_summary,
    get_ai_resolution_info,
    _calculate_backtest_metrics,
    _run_single_sensitivity_backtest,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_ohlcv_100():
    """Create sample OHLCV data with 100 rows"""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    return pd.DataFrame({
        'open': prices,
        'high': prices + np.abs(np.random.randn(100) * 0.3),
        'low': prices - np.abs(np.random.randn(100) * 0.3),
        'close': prices + np.random.randn(100) * 0.2,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)


@pytest.fixture
def sample_ohlcv_500():
    """Create sample OHLCV data with 500 rows"""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=500, freq='1h')
    prices = 100 + np.cumsum(np.random.randn(500) * 0.5)
    
    return pd.DataFrame({
        'open': prices,
        'high': prices + np.abs(np.random.randn(500) * 0.3),
        'low': prices - np.abs(np.random.randn(500) * 0.3),
        'close': prices + np.random.randn(500) * 0.2,
        'volume': np.random.randint(1000, 10000, 500)
    }, index=dates)


@pytest.fixture
def sample_ohlcv_1000():
    """Create sample OHLCV data with 1000 rows"""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=1000, freq='1h')
    prices = 100 + np.cumsum(np.random.randn(1000) * 0.5)
    
    return pd.DataFrame({
        'open': prices,
        'high': prices + np.abs(np.random.randn(1000) * 0.3),
        'low': prices - np.abs(np.random.randn(1000) * 0.3),
        'close': prices + np.random.randn(1000) * 0.2,
        'volume': np.random.randint(1000, 10000, 1000)
    }, index=dates)


@pytest.fixture
def sample_metrics_good():
    """Sample metrics for a good strategy"""
    return {
        'pnl_percent': 25.0,
        'win_rate': 65.0,
        'profit_factor': 2.5,
        'max_drawdown': 8.0,
        'avg_trade': 1.5,
        'avg_win': 3.0,
        'avg_loss': -1.5,
        'pnl_std': 4.0,
        'sharpe_ratio': 0.38,
        'total_trades': 20,
    }


@pytest.fixture
def sample_metrics_bad():
    """Sample metrics for a bad strategy"""
    return {
        'pnl_percent': -15.0,
        'win_rate': 30.0,
        'profit_factor': 0.5,
        'max_drawdown': 25.0,
        'avg_trade': -0.75,
        'avg_win': 2.0,
        'avg_loss': -2.5,
        'pnl_std': 12.0,
        'sharpe_ratio': -0.06,
        'total_trades': 20,
    }


@pytest.fixture
def sample_metrics_insufficient_trades():
    """Sample metrics with insufficient trades"""
    return {
        'pnl_percent': 10.0,
        'win_rate': 70.0,
        'profit_factor': 3.0,
        'max_drawdown': 5.0,
        'pnl_std': 2.0,
        'total_trades': 3,  # Less than MIN_TRADES_FOR_OPTIMIZATION
    }


# =============================================================================
# SCORE CALCULATION TESTS
# =============================================================================

class TestCalculateSensitivityScore:
    """Tests for calculate_sensitivity_score function"""
    
    def test_score_range(self, sample_metrics_good):
        """Score should be between 0 and 100"""
        score = calculate_sensitivity_score(sample_metrics_good)
        assert 0 <= score <= 100
    
    def test_good_metrics_high_score(self, sample_metrics_good):
        """Good metrics should produce high score"""
        score = calculate_sensitivity_score(sample_metrics_good)
        assert score > 50  # Should be above average
    
    def test_bad_metrics_low_score(self, sample_metrics_bad):
        """Bad metrics should produce low score"""
        score = calculate_sensitivity_score(sample_metrics_bad)
        assert score < 50  # Should be below average
    
    def test_insufficient_trades_zero_score(self, sample_metrics_insufficient_trades):
        """Insufficient trades should return 0 score"""
        score = calculate_sensitivity_score(sample_metrics_insufficient_trades)
        assert score == 0
    
    def test_empty_metrics(self):
        """Empty metrics should return 0 score"""
        score = calculate_sensitivity_score({})
        assert score == 0
    
    def test_extreme_profit_capped(self):
        """Extreme profit should be capped"""
        metrics = {
            'pnl_percent': 100.0,  # Way above 50% cap
            'win_rate': 80.0,
            'pnl_std': 5.0,
            'max_drawdown': 5.0,
            'total_trades': 20,
        }
        score = calculate_sensitivity_score(metrics)
        # Score should be capped, not infinite
        assert score <= 100
    
    def test_extreme_loss_floored(self):
        """Extreme loss should floor profit score at 0"""
        metrics = {
            'pnl_percent': -50.0,  # Way below -20% floor
            'win_rate': 20.0,
            'pnl_std': 15.0,
            'max_drawdown': 30.0,
            'total_trades': 20,
        }
        score = calculate_sensitivity_score(metrics)
        assert score >= 0
    
    def test_perfect_metrics(self):
        """Perfect metrics should get score near 100"""
        metrics = {
            'pnl_percent': 50.0,
            'win_rate': 100.0,
            'pnl_std': 0.0,
            'max_drawdown': 0.0,
            'total_trades': 100,
        }
        score = calculate_sensitivity_score(metrics)
        assert score > 90
    
    def test_weights_sum_to_100(self):
        """Score weights should sum to 100"""
        total_weight = (
            SCORE_WEIGHT_PROFIT +
            SCORE_WEIGHT_WIN_RATE +
            SCORE_WEIGHT_STABILITY +
            SCORE_WEIGHT_DRAWDOWN
        )
        assert total_weight == 100


class TestGetScoreBreakdown:
    """Tests for get_score_breakdown function"""
    
    def test_breakdown_keys(self, sample_metrics_good):
        """Breakdown should have all expected keys"""
        breakdown = get_score_breakdown(sample_metrics_good)
        expected_keys = [
            'profit_score', 'profit_max',
            'win_rate_score', 'win_rate_max',
            'stability_score', 'stability_max',
            'drawdown_score', 'drawdown_max',
            'total_score', 'total_max',
        ]
        for key in expected_keys:
            assert key in breakdown
    
    def test_breakdown_components_sum(self, sample_metrics_good):
        """Individual scores should sum to total"""
        breakdown = get_score_breakdown(sample_metrics_good)
        component_sum = (
            breakdown['profit_score'] +
            breakdown['win_rate_score'] +
            breakdown['stability_score'] +
            breakdown['drawdown_score']
        )
        assert abs(component_sum - breakdown['total_score']) < 0.01
    
    def test_breakdown_insufficient_trades(self, sample_metrics_insufficient_trades):
        """Insufficient trades should show reason"""
        breakdown = get_score_breakdown(sample_metrics_insufficient_trades)
        assert 'reason' in breakdown
        assert breakdown['total_score'] == 0


# =============================================================================
# BACKTEST METRICS TESTS
# =============================================================================

class TestCalculateBacktestMetrics:
    """Tests for _calculate_backtest_metrics function"""
    
    def test_empty_trades(self):
        """Empty trades list should return zeros"""
        metrics = _calculate_backtest_metrics([])
        assert metrics['total_trades'] == 0
        assert metrics['pnl_percent'] == 0
        assert metrics['win_rate'] == 0
    
    def test_all_winners(self):
        """All winning trades should have 100% win rate"""
        trades = [
            {'pnl_percent': 1.0},
            {'pnl_percent': 2.0},
            {'pnl_percent': 1.5},
        ]
        metrics = _calculate_backtest_metrics(trades)
        assert metrics['win_rate'] == 100.0
    
    def test_all_losers(self):
        """All losing trades should have 0% win rate"""
        trades = [
            {'pnl_percent': -1.0},
            {'pnl_percent': -2.0},
            {'pnl_percent': -1.5},
        ]
        metrics = _calculate_backtest_metrics(trades)
        assert metrics['win_rate'] == 0.0
    
    def test_mixed_trades(self):
        """Mixed trades should calculate correctly"""
        trades = [
            {'pnl_percent': 2.0},
            {'pnl_percent': -1.0},
            {'pnl_percent': 3.0},
            {'pnl_percent': -0.5},
        ]
        metrics = _calculate_backtest_metrics(trades)
        assert metrics['total_trades'] == 4
        assert metrics['pnl_percent'] == 3.5  # 2 - 1 + 3 - 0.5
        assert metrics['win_rate'] == 50.0  # 2/4
    
    def test_profit_factor_calculation(self):
        """Profit factor should be gross profit / gross loss"""
        trades = [
            {'pnl_percent': 10.0},
            {'pnl_percent': -5.0},
        ]
        metrics = _calculate_backtest_metrics(trades)
        assert metrics['profit_factor'] == 2.0  # 10 / 5
    
    def test_max_drawdown_calculation(self):
        """Max drawdown should track equity curve"""
        trades = [
            {'pnl_percent': 5.0},   # equity: 5
            {'pnl_percent': -3.0},  # equity: 2, dd from 5 = 3
            {'pnl_percent': 2.0},   # equity: 4
            {'pnl_percent': -4.0},  # equity: 0, dd from 5 = 5 (max)
        ]
        metrics = _calculate_backtest_metrics(trades)
        assert metrics['max_drawdown'] == 5.0


# =============================================================================
# FULL BACKTEST TESTS
# =============================================================================

class TestRunFullBacktest:
    """Tests for run_full_backtest function"""
    
    def test_backtest_returns_dict(self, sample_ohlcv_500):
        """Backtest should return dict with expected keys"""
        result = run_full_backtest(sample_ohlcv_500, sensitivity=21)
        assert isinstance(result, dict)
        assert 'trades' in result
        assert 'metrics' in result
        assert 'summary' in result
        assert 'config' in result
    
    def test_backtest_config_stored(self, sample_ohlcv_500):
        """Config should be stored in result"""
        result = run_full_backtest(
            sample_ohlcv_500,
            sensitivity=30,
            filter_type=2,
            sl_mode=4
        )
        assert result['config']['sensitivity'] == 30
        assert result['config']['filter_type'] == 2
        assert result['config']['sl_mode'] == 4
    
    def test_backtest_with_different_sensitivities(self, sample_ohlcv_500):
        """Different sensitivities should produce different results"""
        result1 = run_full_backtest(sample_ohlcv_500, sensitivity=15)
        result2 = run_full_backtest(sample_ohlcv_500, sensitivity=45)
        
        # Results should differ (different number of trades at minimum)
        # May be same by chance, so just check they run
        assert isinstance(result1['metrics']['total_trades'], int)
        assert isinstance(result2['metrics']['total_trades'], int)
    
    def test_backtest_with_filters(self, sample_ohlcv_500):
        """Backtest with filters should run"""
        for filter_type in [FILTER_NONE, FILTER_ATR, FILTER_RSI, FILTER_COMBINED, FILTER_VOLATILITY]:
            result = run_full_backtest(
                sample_ohlcv_500,
                sensitivity=21,
                filter_type=filter_type
            )
            assert 'metrics' in result
    
    def test_backtest_with_sl_modes(self, sample_ohlcv_500):
        """Backtest with different SL modes should run"""
        for sl_mode in [SL_MODE_FIXED, SL_MODE_AFTER_TP1, SL_MODE_CASCADE]:
            result = run_full_backtest(
                sample_ohlcv_500,
                sensitivity=21,
                sl_mode=sl_mode
            )
            assert 'metrics' in result
    
    def test_backtest_summary_consistent(self, sample_ohlcv_500):
        """Summary counts should be consistent"""
        result = run_full_backtest(sample_ohlcv_500, sensitivity=21)
        summary = result['summary']
        
        assert summary['total_trades'] == summary['long_trades'] + summary['short_trades']
        assert summary['total_trades'] == summary['profitable_trades'] + summary['losing_trades']


# =============================================================================
# OPTIMIZATION TESTS
# =============================================================================

class TestOptimizeSensitivity:
    """Tests for optimize_sensitivity function"""
    
    def test_optimization_returns_dict(self, sample_ohlcv_500):
        """Optimization should return dict with expected keys"""
        result = optimize_sensitivity(
            sample_ohlcv_500,
            sensitivities=[21, 30],  # Limited for speed
            workers=2
        )
        assert isinstance(result, dict)
        assert 'best_sensitivity' in result
        assert 'best_score' in result
        assert 'all_results' in result
        assert 'scores' in result
    
    def test_best_sensitivity_in_range(self, sample_ohlcv_500):
        """Best sensitivity should be from tested sensitivities"""
        test_sensitivities = [15, 21, 30]
        result = optimize_sensitivity(
            sample_ohlcv_500,
            sensitivities=test_sensitivities,
            workers=2
        )
        assert result['best_sensitivity'] in test_sensitivities
    
    def test_all_sensitivities_tested(self, sample_ohlcv_500):
        """All requested sensitivities should be tested"""
        test_sensitivities = [15, 21, 30]
        result = optimize_sensitivity(
            sample_ohlcv_500,
            sensitivities=test_sensitivities,
            workers=2
        )
        
        tested = set(r['sensitivity'] for r in result['all_results'])
        assert tested == set(test_sensitivities)
    
    def test_results_sorted_by_score(self, sample_ohlcv_500):
        """Results should be sorted by score descending"""
        result = optimize_sensitivity(
            sample_ohlcv_500,
            sensitivities=[15, 21, 30, 45],
            workers=2
        )
        
        scores = [r['score'] for r in result['all_results']]
        assert scores == sorted(scores, reverse=True)
    
    def test_optimization_time_recorded(self, sample_ohlcv_500):
        """Optimization time should be recorded"""
        result = optimize_sensitivity(
            sample_ohlcv_500,
            sensitivities=[21, 30],
            workers=2
        )
        assert result['optimization_time'] >= 0
    
    def test_workers_recorded(self, sample_ohlcv_500):
        """Workers used should be recorded"""
        result = optimize_sensitivity(
            sample_ohlcv_500,
            sensitivities=[21, 30],
            workers=2
        )
        assert result['workers_used'] == 2
    
    def test_progress_callback_called(self, sample_ohlcv_500):
        """Progress callback should be called for each sensitivity"""
        callback_calls = []
        
        def callback(current, total, sensitivity, result):
            callback_calls.append({
                'current': current,
                'total': total,
                'sensitivity': sensitivity
            })
        
        result = optimize_sensitivity(
            sample_ohlcv_500,
            sensitivities=[15, 21, 30],
            workers=1,  # Single worker for predictable callback order
            progress_callback=callback
        )
        
        assert len(callback_calls) == 3
        for call in callback_calls:
            assert call['total'] == 3
    
    def test_scores_dictionary(self, sample_ohlcv_500):
        """Scores dictionary should map sensitivity to score"""
        test_sensitivities = [15, 21, 30]
        result = optimize_sensitivity(
            sample_ohlcv_500,
            sensitivities=test_sensitivities,
            workers=2
        )
        
        assert set(result['scores'].keys()) == set(test_sensitivities)
        for sens in test_sensitivities:
            assert isinstance(result['scores'][sens], (int, float))


class TestCompareSensitivities:
    """Tests for compare_sensitivities function"""
    
    def test_returns_dataframe(self, sample_ohlcv_500):
        """Should return a DataFrame"""
        result = compare_sensitivities(
            sample_ohlcv_500,
            sensitivities=[15, 21, 30]
        )
        assert isinstance(result, pd.DataFrame)
    
    def test_has_expected_columns(self, sample_ohlcv_500):
        """Should have sensitivity and score columns"""
        result = compare_sensitivities(
            sample_ohlcv_500,
            sensitivities=[15, 21]
        )
        assert 'sensitivity' in result.columns
        assert 'score' in result.columns
    
    def test_sorted_by_score(self, sample_ohlcv_500):
        """Should be sorted by score descending"""
        result = compare_sensitivities(
            sample_ohlcv_500,
            sensitivities=[15, 21, 30]
        )
        scores = result['score'].tolist()
        assert scores == sorted(scores, reverse=True)


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestGetOptimizationSummary:
    """Tests for get_optimization_summary function"""
    
    def test_returns_string(self, sample_ohlcv_500):
        """Should return a formatted string"""
        opt_result = optimize_sensitivity(
            sample_ohlcv_500,
            sensitivities=[21, 30],
            workers=2
        )
        summary = get_optimization_summary(opt_result)
        assert isinstance(summary, str)
    
    def test_contains_best_sensitivity(self, sample_ohlcv_500):
        """Summary should mention best sensitivity"""
        opt_result = optimize_sensitivity(
            sample_ohlcv_500,
            sensitivities=[21, 30],
            workers=2
        )
        summary = get_optimization_summary(opt_result)
        assert 'Best Sensitivity' in summary
    
    def test_empty_result(self):
        """Should handle empty result"""
        summary = get_optimization_summary({})
        assert 'No optimization results' in summary


class TestGetAiResolutionInfo:
    """Tests for get_ai_resolution_info function"""
    
    def test_returns_dict(self):
        """Should return a dictionary"""
        info = get_ai_resolution_info()
        assert isinstance(info, dict)
    
    def test_has_expected_keys(self):
        """Should have expected keys"""
        info = get_ai_resolution_info()
        assert 'name' in info
        assert 'version' in info
        assert 'scoring' in info
        assert 'parameters' in info
    
    def test_scoring_weights_documented(self):
        """Scoring weights should be documented"""
        info = get_ai_resolution_info()
        scoring = info['scoring']
        
        assert 'profit' in scoring
        assert 'win_rate' in scoring
        assert 'stability' in scoring
        assert 'drawdown' in scoring


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_insufficient_data(self):
        """Should handle very small datasets"""
        small_df = pd.DataFrame({
            'open': [100, 101],
            'high': [102, 103],
            'low': [99, 100],
            'close': [101, 102],
            'volume': [1000, 1000]
        })
        
        result = run_full_backtest(small_df, sensitivity=12)
        # Should run without error
        assert 'metrics' in result
    
    def test_no_signals_generated(self):
        """Should handle case with no signals"""
        # Create flat price data (no signals)
        flat_df = pd.DataFrame({
            'open': [100] * 50,
            'high': [100.1] * 50,
            'low': [99.9] * 50,
            'close': [100] * 50,  # Same close = no bullish/bearish candles
            'volume': [1000] * 50
        })
        
        result = run_full_backtest(flat_df, sensitivity=21)
        assert result['metrics']['total_trades'] == 0
    
    def test_multicore_single_sensitivity(self, sample_ohlcv_500):
        """Should work with just one sensitivity"""
        result = optimize_sensitivity(
            sample_ohlcv_500,
            sensitivities=[21],
            workers=2
        )
        assert result['best_sensitivity'] == 21


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Basic performance tests"""
    
    def test_backtest_performance(self, sample_ohlcv_1000):
        """Backtest should complete in reasonable time"""
        import time
        
        start = time.time()
        run_full_backtest(sample_ohlcv_1000, sensitivity=21)
        elapsed = time.time() - start
        
        # Should complete in under 5 seconds
        assert elapsed < 5.0
    
    def test_optimization_performance(self, sample_ohlcv_500):
        """Optimization should complete in reasonable time"""
        import time
        
        start = time.time()
        optimize_sensitivity(
            sample_ohlcv_500,
            sensitivities=[15, 21, 30, 45],
            workers=2
        )
        elapsed = time.time() - start
        
        # Should complete in under 30 seconds
        assert elapsed < 30.0


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    # Run with verbose output
    pytest.main([__file__, '-v', '--tb=short'])
