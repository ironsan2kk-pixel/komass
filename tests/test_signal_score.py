"""
Unit Tests for Signal Score System
===================================

Tests for SignalScorer class and related functions.

Chat #34: Signal Score Core
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Import modules to test
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.services.signal_score import (
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
    GRADE_THRESHOLDS,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_df():
    """Create sample OHLCV DataFrame for testing"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
    
    # Create trending price data
    base_price = 45000
    trend = np.cumsum(np.random.randn(100) * 50)
    close = base_price + trend
    
    high = close + np.abs(np.random.randn(100) * 100)
    low = close - np.abs(np.random.randn(100) * 100)
    open_ = close + np.random.randn(100) * 30
    volume = 1000000 + np.random.rand(100) * 500000
    
    df = pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
    }, index=dates)
    
    return df


@pytest.fixture
def uptrend_df():
    """Create uptrending DataFrame"""
    np.random.seed(123)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
    
    base_price = 40000
    close = base_price + np.arange(100) * 100 + np.random.randn(100) * 50
    high = close + np.abs(np.random.randn(100) * 80)
    low = close - np.abs(np.random.randn(100) * 80)
    open_ = close - np.random.rand(100) * 50  # Open below close for bullish candles
    volume = 1000000 + np.random.rand(100) * 500000
    
    df = pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
    }, index=dates)
    
    return df


@pytest.fixture
def downtrend_df():
    """Create downtrending DataFrame"""
    np.random.seed(456)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
    
    base_price = 50000
    close = base_price - np.arange(100) * 100 + np.random.randn(100) * 50
    high = close + np.abs(np.random.randn(100) * 80)
    low = close - np.abs(np.random.randn(100) * 80)
    open_ = close + np.random.rand(100) * 50  # Open above close for bearish candles
    volume = 1000000 + np.random.rand(100) * 500000
    
    df = pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
    }, index=dates)
    
    return df


@pytest.fixture
def scorer():
    """Create SignalScorer instance"""
    return SignalScorer()


# =============================================================================
# TEST: TECHNICAL INDICATORS
# =============================================================================

class TestTechnicalIndicators:
    """Tests for technical indicator calculations"""
    
    def test_calculate_atr(self, sample_df):
        """Test ATR calculation"""
        atr = calculate_atr(sample_df, period=14)
        
        assert len(atr) == len(sample_df)
        assert atr.iloc[-1] > 0
        assert not atr.isna().all()
    
    def test_calculate_rsi(self, sample_df):
        """Test RSI calculation"""
        rsi = calculate_rsi(sample_df, period=14)
        
        assert len(rsi) == len(sample_df)
        assert 0 <= rsi.iloc[-1] <= 100
        assert not rsi.isna().all()
    
    def test_calculate_adx(self, sample_df):
        """Test ADX calculation"""
        adx = calculate_adx(sample_df, period=14)
        
        assert len(adx) == len(sample_df)
        assert adx.iloc[-1] >= 0
        assert not adx.isna().all()
    
    def test_calculate_supertrend(self, sample_df):
        """Test SuperTrend calculation"""
        direction, line = calculate_supertrend(sample_df, period=10, multiplier=3.0)
        
        assert len(direction) == len(sample_df)
        assert len(line) == len(sample_df)
        assert direction.iloc[-1] in [1, -1]
    
    def test_calculate_support_resistance(self, sample_df):
        """Test S/R calculation"""
        support, resistance = calculate_support_resistance(sample_df, lookback=50)
        
        current_price = sample_df['close'].iloc[-1]
        
        assert support < current_price
        assert resistance > current_price
        assert support > 0
        assert resistance > support
    
    def test_calculate_volatility_percentile(self, sample_df):
        """Test volatility percentile calculation"""
        percentile = calculate_volatility_percentile(sample_df, atr_period=14, lookback=100)
        
        assert 0 <= percentile <= 100


# =============================================================================
# TEST: GRADE FUNCTIONS
# =============================================================================

class TestGradeFunctions:
    """Tests for grade-related functions"""
    
    def test_get_grade_from_score(self):
        """Test grade determination from score"""
        assert get_grade_from_score(100) == 'A'
        assert get_grade_from_score(85) == 'A'
        assert get_grade_from_score(84) == 'B'
        assert get_grade_from_score(70) == 'B'
        assert get_grade_from_score(69) == 'C'
        assert get_grade_from_score(55) == 'C'
        assert get_grade_from_score(54) == 'D'
        assert get_grade_from_score(40) == 'D'
        assert get_grade_from_score(39) == 'F'
        assert get_grade_from_score(0) == 'F'
    
    def test_get_grade_color(self):
        """Test grade color mapping"""
        assert get_grade_color('A') == '#22c55e'
        assert get_grade_color('B') == '#84cc16'
        assert get_grade_color('C') == '#eab308'
        assert get_grade_color('D') == '#f97316'
        assert get_grade_color('F') == '#ef4444'
        assert get_grade_color('X') == '#6b7280'  # Unknown grade


# =============================================================================
# TEST: SIGNAL SCORER CLASS
# =============================================================================

class TestSignalScorer:
    """Tests for SignalScorer class"""
    
    def test_scorer_initialization(self, scorer):
        """Test scorer initializes with default params"""
        assert scorer.params is not None
        assert 'atr_period' in scorer.params
        assert 'rsi_period' in scorer.params
    
    def test_scorer_custom_params(self):
        """Test scorer with custom parameters"""
        custom_params = {'atr_period': 20, 'rsi_period': 7}
        scorer = SignalScorer(params=custom_params)
        
        assert scorer.params['atr_period'] == 20
        assert scorer.params['rsi_period'] == 7
    
    def test_calculate_score_long(self, scorer, sample_df):
        """Test score calculation for long signal"""
        entry_price = sample_df['close'].iloc[-1]
        
        result = scorer.calculate_score(
            df=sample_df,
            direction='long',
            entry_price=entry_price,
        )
        
        assert isinstance(result, SignalScoreResult)
        assert 0 <= result.total_score <= 100
        assert result.grade in ['A', 'B', 'C', 'D', 'F']
        assert 'confluence' in result.components
        assert 'multi_tf' in result.components
        assert 'market_context' in result.components
        assert 'technical_levels' in result.components
    
    def test_calculate_score_short(self, scorer, sample_df):
        """Test score calculation for short signal"""
        entry_price = sample_df['close'].iloc[-1]
        
        result = scorer.calculate_score(
            df=sample_df,
            direction='short',
            entry_price=entry_price,
        )
        
        assert isinstance(result, SignalScoreResult)
        assert 0 <= result.total_score <= 100
        assert result.grade in ['A', 'B', 'C', 'D', 'F']
    
    def test_uptrend_long_score_higher(self, scorer, uptrend_df):
        """Test that long signal in uptrend has higher confluence"""
        entry_price = uptrend_df['close'].iloc[-1]
        
        long_result = scorer.calculate_score(
            df=uptrend_df,
            direction='long',
            entry_price=entry_price,
        )
        
        # In an uptrend, SuperTrend should agree with long
        assert long_result.details['confluence']['supertrend_agrees'] == True
    
    def test_downtrend_short_score_higher(self, scorer, downtrend_df):
        """Test that short signal in downtrend has higher confluence"""
        entry_price = downtrend_df['close'].iloc[-1]
        
        short_result = scorer.calculate_score(
            df=downtrend_df,
            direction='short',
            entry_price=entry_price,
        )
        
        # In a downtrend, SuperTrend should agree with short
        assert short_result.details['confluence']['supertrend_agrees'] == True
    
    def test_insufficient_data(self, scorer):
        """Test handling of insufficient data"""
        small_df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [102, 103, 104],
            'low': [99, 100, 101],
            'close': [101, 102, 103],
            'volume': [1000, 1000, 1000],
        })
        
        result = scorer.calculate_score(
            df=small_df,
            direction='long',
            entry_price=103,
        )
        
        assert result.total_score == 0
        assert result.grade == 'F'
        assert 'error' in result.details
    
    def test_component_scores_sum_correctly(self, scorer, sample_df):
        """Test that component scores sum to total"""
        entry_price = sample_df['close'].iloc[-1]
        
        result = scorer.calculate_score(
            df=sample_df,
            direction='long',
            entry_price=entry_price,
        )
        
        component_sum = sum(result.components.values())
        assert abs(component_sum - result.total_score) <= 1  # Allow for rounding
    
    def test_recommendations_generated(self, scorer, sample_df):
        """Test that recommendations are generated"""
        entry_price = sample_df['close'].iloc[-1]
        
        result = scorer.calculate_score(
            df=sample_df,
            direction='long',
            entry_price=entry_price,
        )
        
        assert isinstance(result.recommendations, list)
        assert len(result.recommendations) > 0
    
    def test_to_dict_method(self, scorer, sample_df):
        """Test SignalScoreResult.to_dict method"""
        entry_price = sample_df['close'].iloc[-1]
        
        result = scorer.calculate_score(
            df=sample_df,
            direction='long',
            entry_price=entry_price,
        )
        
        result_dict = result.to_dict()
        
        assert isinstance(result_dict, dict)
        assert 'total_score' in result_dict
        assert 'grade' in result_dict
        assert 'components' in result_dict
        assert 'details' in result_dict


# =============================================================================
# TEST: MULTI-TF ALIGNMENT
# =============================================================================

class TestMultiTFAlignment:
    """Tests for multi-timeframe alignment scoring"""
    
    def test_with_higher_tf_data(self, scorer, uptrend_df):
        """Test score with higher TF data provided"""
        entry_price = uptrend_df['close'].iloc[-1]
        
        higher_tf_data = {
            '4h': uptrend_df.copy(),  # Same uptrend
            '1d': uptrend_df.copy(),
        }
        
        result = scorer.calculate_score(
            df=uptrend_df,
            direction='long',
            entry_price=entry_price,
            higher_tf_data=higher_tf_data,
        )
        
        # Should have good multi-TF score with aligned trends
        assert result.components['multi_tf'] > 0
        assert '4h' in result.details['multi_tf']['higher_tfs']
        assert '1d' in result.details['multi_tf']['higher_tfs']
    
    def test_without_higher_tf_data(self, scorer, sample_df):
        """Test score without higher TF data (partial points)"""
        entry_price = sample_df['close'].iloc[-1]
        
        result = scorer.calculate_score(
            df=sample_df,
            direction='long',
            entry_price=entry_price,
            higher_tf_data=None,
        )
        
        # Should get partial multi-TF score
        assert result.components['multi_tf'] > 0
        assert result.details['multi_tf']['higher_tfs']['4h'] == 'unavailable'


# =============================================================================
# TEST: BATCH SCORING
# =============================================================================

class TestBatchScoring:
    """Tests for batch trade scoring"""
    
    def test_score_trades(self, sample_df):
        """Test batch scoring of trades"""
        trades = [
            {'direction': 'long', 'entry_price': 45000, 'entry_idx': 50},
            {'direction': 'short', 'entry_price': 46000, 'entry_idx': 60},
            {'direction': 'long', 'entry_price': 44500, 'entry_idx': 70},
        ]
        
        scored_trades = score_trades(trades, sample_df)
        
        assert len(scored_trades) == 3
        for trade in scored_trades:
            assert 'signal_score' in trade
            assert 'signal_grade' in trade
            assert 0 <= trade['signal_score'] <= 100
    
    def test_score_trades_with_int_direction(self, sample_df):
        """Test batch scoring with integer direction"""
        trades = [
            {'direction': 1, 'entry_price': 45000, 'entry_idx': 50},
            {'direction': -1, 'entry_price': 46000, 'entry_idx': 60},
        ]
        
        scored_trades = score_trades(trades, sample_df)
        
        assert len(scored_trades) == 2
        assert scored_trades[0]['signal_grade'] in ['A', 'B', 'C', 'D', 'F']
    
    def test_score_trades_preserves_original(self, sample_df):
        """Test that batch scoring preserves original trade data"""
        trades = [
            {'direction': 'long', 'entry_price': 45000, 'entry_idx': 50, 'custom_field': 'test'},
        ]
        
        scored_trades = score_trades(trades, sample_df)
        
        assert scored_trades[0]['custom_field'] == 'test'


# =============================================================================
# TEST: MARKET CONTEXT
# =============================================================================

class TestMarketContext:
    """Tests for market context scoring"""
    
    def test_high_volatility_detection(self, scorer):
        """Test detection of high volatility"""
        np.random.seed(789)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        
        # Create high volatility data (large ATR)
        close = 45000 + np.cumsum(np.random.randn(100) * 500)  # High volatility
        high = close + np.abs(np.random.randn(100) * 300)
        low = close - np.abs(np.random.randn(100) * 300)
        
        df = pd.DataFrame({
            'open': close + np.random.randn(100) * 50,
            'high': high,
            'low': low,
            'close': close,
            'volume': 1000000 + np.random.rand(100) * 500000,
        }, index=dates)
        
        result = scorer.calculate_score(
            df=df,
            direction='long',
            entry_price=close[-1],
        )
        
        # Should detect trend status
        assert 'trend_strength' in result.details['market_context']


# =============================================================================
# TEST: EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_direction_normalization(self, scorer, sample_df):
        """Test direction string normalization"""
        entry_price = sample_df['close'].iloc[-1]
        
        # Test uppercase
        result1 = scorer.calculate_score(sample_df, 'LONG', entry_price)
        result2 = scorer.calculate_score(sample_df, 'long', entry_price)
        
        assert result1.total_score == result2.total_score
    
    def test_numeric_direction(self, scorer, sample_df):
        """Test numeric direction (1/-1)"""
        entry_price = sample_df['close'].iloc[-1]
        
        result = scorer.calculate_score(sample_df, '1', entry_price)
        
        assert result.total_score >= 0
    
    def test_zero_volume(self, scorer):
        """Test handling of zero volume data"""
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1h')
        
        df = pd.DataFrame({
            'open': np.linspace(100, 150, 50),
            'high': np.linspace(105, 155, 50),
            'low': np.linspace(95, 145, 50),
            'close': np.linspace(102, 152, 50),
            'volume': np.zeros(50),
        }, index=dates)
        
        result = scorer.calculate_score(df, 'long', 152)
        
        # Should handle gracefully
        assert result.total_score >= 0


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
