"""
Unit Tests for Multi-TF Loader - KOMAS v4.0
==========================================

Tests for multi-timeframe data loading, aggregation, and trend detection.

Chat #35: Score Multi-TF
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import asyncio
from typing import Dict

# Import modules to test
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.multi_tf_loader import (
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

from app.services.signal_score import (
    SignalScorer,
    SignalScoreResult,
    score_trades,
    get_grade_from_score,
    get_grade_color,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_uptrend_df() -> pd.DataFrame:
    """Create sample DataFrame with uptrend"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1h')
    
    # Clear uptrend
    trend = np.cumsum(np.random.randn(200) * 50 + 20)  # Upward bias
    close = 45000 + trend
    high = close + np.abs(np.random.randn(200) * 100)
    low = close - np.abs(np.random.randn(200) * 100)
    open_ = close + np.random.randn(200) * 30
    volume = np.abs(np.random.randn(200) * 500000) + 100000
    
    df = pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
    }, index=dates)
    
    return df


@pytest.fixture
def sample_downtrend_df() -> pd.DataFrame:
    """Create sample DataFrame with downtrend"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1h')
    
    # Clear downtrend
    trend = np.cumsum(np.random.randn(200) * 50 - 20)  # Downward bias
    close = 45000 + trend
    high = close + np.abs(np.random.randn(200) * 100)
    low = close - np.abs(np.random.randn(200) * 100)
    open_ = close + np.random.randn(200) * 30
    volume = np.abs(np.random.randn(200) * 500000) + 100000
    
    df = pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
    }, index=dates)
    
    return df


@pytest.fixture
def sample_sideways_df() -> pd.DataFrame:
    """Create sample DataFrame with sideways movement"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1h')
    
    # Sideways - oscillating around mean
    close = 45000 + np.sin(np.linspace(0, 10, 200)) * 500 + np.random.randn(200) * 100
    high = close + np.abs(np.random.randn(200) * 50)
    low = close - np.abs(np.random.randn(200) * 50)
    open_ = close + np.random.randn(200) * 20
    volume = np.abs(np.random.randn(200) * 500000) + 100000
    
    df = pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
    }, index=dates)
    
    return df


@pytest.fixture
def sample_1h_df() -> pd.DataFrame:
    """Create sample 1h DataFrame for aggregation tests"""
    np.random.seed(123)
    dates = pd.date_range(start='2024-01-01', periods=500, freq='1h')
    
    close = 50000 + np.cumsum(np.random.randn(500) * 100)
    high = close + np.abs(np.random.randn(500) * 200)
    low = close - np.abs(np.random.randn(500) * 200)
    open_ = close + np.random.randn(500) * 50
    volume = np.abs(np.random.randn(500) * 1000000) + 100000
    
    df = pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
    }, index=dates)
    
    return df


# =============================================================================
# TREND DETECTION TESTS
# =============================================================================

class TestTrendDetectionEMA:
    """Tests for EMA-based trend detection"""
    
    def test_uptrend_detection(self, sample_uptrend_df):
        """Test EMA detects uptrend correctly"""
        direction, confidence, details = detect_trend_ema(sample_uptrend_df)
        
        assert direction == TrendDirection.UP
        assert confidence > 0
        assert 'ema_fast' in details
        assert 'ema_slow' in details
    
    def test_downtrend_detection(self, sample_downtrend_df):
        """Test EMA detects downtrend correctly"""
        direction, confidence, details = detect_trend_ema(sample_downtrend_df)
        
        assert direction == TrendDirection.DOWN
        assert confidence > 0
    
    def test_insufficient_data(self):
        """Test EMA handles insufficient data"""
        df = pd.DataFrame({
            'open': [100, 101],
            'high': [102, 103],
            'low': [99, 100],
            'close': [101, 102],
            'volume': [1000, 1000],
        })
        
        direction, confidence, details = detect_trend_ema(df)
        
        assert direction == TrendDirection.SIDEWAYS
        assert confidence == 0.0
    
    def test_custom_periods(self, sample_uptrend_df):
        """Test EMA with custom periods"""
        direction, confidence, details = detect_trend_ema(
            sample_uptrend_df,
            fast_period=5,
            slow_period=15
        )
        
        assert details['fast_period'] == 5
        assert details['slow_period'] == 15


class TestTrendDetectionSuperTrend:
    """Tests for SuperTrend-based trend detection"""
    
    def test_uptrend_detection(self, sample_uptrend_df):
        """Test SuperTrend detects uptrend correctly"""
        direction, confidence, details = detect_trend_supertrend(sample_uptrend_df)
        
        assert direction == TrendDirection.UP
        assert 'supertrend_direction' in details
        assert details['supertrend_direction'] == 1
    
    def test_downtrend_detection(self, sample_downtrend_df):
        """Test SuperTrend detects downtrend correctly"""
        direction, confidence, details = detect_trend_supertrend(sample_downtrend_df)
        
        assert direction == TrendDirection.DOWN
        assert details['supertrend_direction'] == -1
    
    def test_custom_parameters(self, sample_uptrend_df):
        """Test SuperTrend with custom parameters"""
        direction, confidence, details = detect_trend_supertrend(
            sample_uptrend_df,
            period=20,
            multiplier=2.0
        )
        
        assert details['period'] == 20
        assert details['multiplier'] == 2.0


class TestTrendDetectionADX:
    """Tests for ADX-based trend detection"""
    
    def test_uptrend_detection(self, sample_uptrend_df):
        """Test ADX detects uptrend with trend strength"""
        direction, confidence, details = detect_trend_adx(sample_uptrend_df)
        
        # Should detect trending market with direction
        assert 'adx' in details
        assert 'plus_di' in details
        assert 'minus_di' in details
    
    def test_sideways_detection(self, sample_sideways_df):
        """Test ADX detects low trend strength"""
        direction, confidence, details = detect_trend_adx(sample_sideways_df)
        
        # Low ADX should indicate sideways
        # Direction might still be determined, but confidence lower
        assert 'is_trending' in details
    
    def test_custom_threshold(self, sample_uptrend_df):
        """Test ADX with custom threshold"""
        direction, confidence, details = detect_trend_adx(
            sample_uptrend_df,
            period=20,
            threshold=30
        )
        
        assert details['threshold'] == 30


class TestTrendDetectionCombined:
    """Tests for combined trend detection"""
    
    def test_combined_uptrend(self, sample_uptrend_df):
        """Test combined method detects uptrend"""
        direction, confidence, details = detect_trend_combined(sample_uptrend_df)
        
        assert direction == TrendDirection.UP
        assert 'ema' in details
        assert 'supertrend' in details
        assert 'adx' in details
        assert 'up_score' in details
        assert 'down_score' in details
    
    def test_combined_downtrend(self, sample_downtrend_df):
        """Test combined method detects downtrend"""
        direction, confidence, details = detect_trend_combined(sample_downtrend_df)
        
        assert direction == TrendDirection.DOWN
    
    def test_custom_weights(self, sample_uptrend_df):
        """Test combined method with custom weights"""
        direction, confidence, details = detect_trend_combined(
            sample_uptrend_df,
            ema_weight=0.5,
            supertrend_weight=0.3,
            adx_weight=0.2
        )
        
        assert details['weights']['ema'] == 0.5
        assert details['weights']['supertrend'] == 0.3
        assert details['weights']['adx'] == 0.2


# =============================================================================
# AGGREGATION TESTS
# =============================================================================

class TestAggregation:
    """Tests for timeframe aggregation"""
    
    def test_1h_to_4h_aggregation(self, sample_1h_df):
        """Test 1h to 4h aggregation"""
        result = aggregate_to_higher_tf(sample_1h_df, '1h', '4h')
        
        assert result is not None
        assert len(result) > 0
        # 500 1h candles should give ~125 4h candles
        assert len(result) >= 100
        
        # Check OHLCV columns exist
        for col in ['open', 'high', 'low', 'close', 'volume']:
            assert col in result.columns
    
    def test_1h_to_1d_aggregation(self, sample_1h_df):
        """Test 1h to 1d aggregation"""
        result = aggregate_to_higher_tf(sample_1h_df, '1h', '1d')
        
        assert result is not None
        # 500 1h candles = ~21 days
        assert len(result) >= 15
    
    def test_invalid_aggregation(self, sample_1h_df):
        """Test invalid aggregation (lower to same/higher)"""
        # Can't aggregate to lower TF
        result = aggregate_to_higher_tf(sample_1h_df, '1h', '15m')
        assert result is None
        
        # Can't aggregate to same TF
        result = aggregate_to_higher_tf(sample_1h_df, '1h', '1h')
        assert result is None
    
    def test_unknown_timeframe(self, sample_1h_df):
        """Test unknown timeframe handling"""
        result = aggregate_to_higher_tf(sample_1h_df, '1h', 'invalid')
        assert result is None
    
    def test_ohlc_correctness(self, sample_1h_df):
        """Test OHLC values are correctly aggregated"""
        result = aggregate_to_higher_tf(sample_1h_df, '1h', '4h')
        
        # Open should be first of period
        # High should be max
        # Low should be min
        # Close should be last
        # Volume should be sum
        
        assert result is not None
        assert all(result['high'] >= result['open'])
        assert all(result['high'] >= result['close'])
        assert all(result['low'] <= result['open'])
        assert all(result['low'] <= result['close'])


# =============================================================================
# MULTI-TF LOADER TESTS
# =============================================================================

class TestMultiTFLoader:
    """Tests for MultiTFLoader class"""
    
    def test_initialization(self):
        """Test loader initialization"""
        loader = MultiTFLoader()
        
        assert loader.tf_weights == DEFAULT_TF_WEIGHTS
        assert loader.detection_method == TrendDetectionMethod.COMBINED
    
    def test_custom_initialization(self):
        """Test loader with custom settings"""
        custom_weights = {'4h': 15, '1d': 10}
        loader = MultiTFLoader(
            tf_weights=custom_weights,
            detection_method=TrendDetectionMethod.EMA,
            use_api_fallback=False,
        )
        
        assert loader.tf_weights == custom_weights
        assert loader.detection_method == TrendDetectionMethod.EMA
        assert loader.use_api_fallback == False
    
    def test_detect_trend_ema(self, sample_uptrend_df):
        """Test detect_trend with EMA method"""
        loader = MultiTFLoader(detection_method=TrendDetectionMethod.EMA)
        
        direction, confidence, details = loader.detect_trend(sample_uptrend_df)
        
        assert direction == TrendDirection.UP
    
    def test_detect_trend_supertrend(self, sample_uptrend_df):
        """Test detect_trend with SuperTrend method"""
        loader = MultiTFLoader(detection_method=TrendDetectionMethod.SUPERTREND)
        
        direction, confidence, details = loader.detect_trend(sample_uptrend_df)
        
        assert direction == TrendDirection.UP
    
    def test_calculate_score_sync_aligned(self, sample_uptrend_df):
        """Test synchronous score calculation with aligned TFs"""
        loader = MultiTFLoader()
        
        # Create higher TF data with same uptrend
        df_4h = aggregate_to_higher_tf(sample_uptrend_df, '1h', '4h')
        df_1d = aggregate_to_higher_tf(sample_uptrend_df, '1h', '1d')
        
        higher_tf_data = {'4h': df_4h, '1d': df_1d}
        
        score, details = loader.calculate_score_sync('long', higher_tf_data)
        
        # Should get high score for aligned TFs
        assert score > 0
        assert 'higher_tfs' in details
        assert 'alignments' in details
    
    def test_calculate_score_sync_misaligned(self, sample_downtrend_df):
        """Test synchronous score calculation with misaligned TFs"""
        loader = MultiTFLoader()
        
        # Create higher TF data with downtrend
        df_4h = aggregate_to_higher_tf(sample_downtrend_df, '1h', '4h')
        df_1d = aggregate_to_higher_tf(sample_downtrend_df, '1h', '1d')
        
        higher_tf_data = {'4h': df_4h, '1d': df_1d}
        
        # Long signal in downtrend should get low score
        score, details = loader.calculate_score_sync('long', higher_tf_data)
        
        assert 'misalignments' in details
    
    @pytest.mark.asyncio
    async def test_analyze_with_aggregation(self, sample_uptrend_df):
        """Test async analyze with aggregation fallback"""
        loader = MultiTFLoader(
            use_api_fallback=False,
            use_aggregation_fallback=True,
        )
        
        result = await loader.analyze(
            symbol='BTCUSDT',
            trading_tf='1h',
            signal_direction='long',
            trading_data=sample_uptrend_df,
        )
        
        assert isinstance(result, MultiTFResult)
        assert result.max_score == 25
        assert result.signal_direction == 'long'


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestSignalScorerIntegration:
    """Tests for SignalScorer with MultiTFLoader integration"""
    
    def test_scorer_with_higher_tf_data(self, sample_uptrend_df):
        """Test SignalScorer uses higher TF data correctly"""
        scorer = SignalScorer()
        
        # Create higher TF data
        df_4h = aggregate_to_higher_tf(sample_uptrend_df, '1h', '4h')
        df_1d = aggregate_to_higher_tf(sample_uptrend_df, '1h', '1d')
        
        higher_tf_data = {'4h': df_4h, '1d': df_1d}
        
        result = scorer.calculate_score(
            df=sample_uptrend_df,
            direction='long',
            entry_price=sample_uptrend_df['close'].iloc[-1],
            higher_tf_data=higher_tf_data,
        )
        
        assert isinstance(result, SignalScoreResult)
        assert result.total_score > 0
        assert result.components['multi_tf'] >= 0
        assert 'higher_tfs' in result.details.get('multi_tf', {})
    
    def test_scorer_without_higher_tf_data(self, sample_uptrend_df):
        """Test SignalScorer handles missing higher TF data"""
        scorer = SignalScorer()
        
        result = scorer.calculate_score(
            df=sample_uptrend_df,
            direction='long',
            entry_price=sample_uptrend_df['close'].iloc[-1],
        )
        
        # Should still work, giving partial points
        assert result.total_score > 0
        # Multi-TF should give partial score when no data
        assert result.components['multi_tf'] >= 0
    
    def test_scorer_custom_detection_method(self, sample_uptrend_df):
        """Test SignalScorer with custom trend detection method"""
        scorer = SignalScorer(params={
            'multi_tf_detection_method': 'ema',
        })
        
        df_4h = aggregate_to_higher_tf(sample_uptrend_df, '1h', '4h')
        higher_tf_data = {'4h': df_4h}
        
        result = scorer.calculate_score(
            df=sample_uptrend_df,
            direction='long',
            entry_price=sample_uptrend_df['close'].iloc[-1],
            higher_tf_data=higher_tf_data,
        )
        
        # Check method was used
        assert result.details['multi_tf']['method'] == 'ema'
    
    def test_batch_scoring_with_higher_tf(self, sample_uptrend_df):
        """Test batch trade scoring with higher TF data"""
        trades = [
            {'direction': 'long', 'entry_price': 50000, 'entry_idx': 50},
            {'direction': 'long', 'entry_price': 51000, 'entry_idx': 100},
            {'direction': 'short', 'entry_price': 52000, 'entry_idx': 150},
        ]
        
        df_4h = aggregate_to_higher_tf(sample_uptrend_df, '1h', '4h')
        higher_tf_data = {'4h': df_4h}
        
        scored_trades = score_trades(
            trades=trades,
            df=sample_uptrend_df,
            higher_tf_data=higher_tf_data,
        )
        
        assert len(scored_trades) == 3
        for trade in scored_trades:
            assert 'signal_score' in trade
            assert 'signal_grade' in trade
            assert 'score_components' in trade


# =============================================================================
# UTILITY TESTS
# =============================================================================

class TestUtilities:
    """Tests for utility functions"""
    
    def test_get_higher_tfs(self):
        """Test get_higher_tfs function"""
        assert get_higher_tfs('1h') == ['4h', '1d']
        assert get_higher_tfs('15m') == ['1h', '4h', '1d']
        assert get_higher_tfs('1d') == []
    
    def test_get_tf_weights(self):
        """Test get_tf_weights function"""
        # Default weights
        weights = get_tf_weights()
        assert weights == DEFAULT_TF_WEIGHTS
        
        # Custom weights
        custom = {'4h': 20, '1d': 5}
        weights = get_tf_weights(custom)
        assert weights['4h'] == 20
        assert weights['1d'] == 5
    
    def test_tf_hierarchy(self):
        """Test TF_HIERARCHY completeness"""
        expected_tfs = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d']
        
        for tf in expected_tfs:
            assert tf in TF_HIERARCHY
    
    def test_tf_minutes(self):
        """Test TF_MINUTES correctness"""
        assert TF_MINUTES['1m'] == 1
        assert TF_MINUTES['1h'] == 60
        assert TF_MINUTES['4h'] == 240
        assert TF_MINUTES['1d'] == 1440
    
    def test_grade_from_score(self):
        """Test grade calculation"""
        assert get_grade_from_score(95) == 'A'
        assert get_grade_from_score(75) == 'B'
        assert get_grade_from_score(60) == 'C'
        assert get_grade_from_score(45) == 'D'
        assert get_grade_from_score(20) == 'F'
    
    def test_grade_colors(self):
        """Test grade colors"""
        assert get_grade_color('A') == '#22c55e'
        assert get_grade_color('F') == '#ef4444'
        assert get_grade_color('X') == '#6b7280'  # Unknown grade


# =============================================================================
# EDGE CASES
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame"""
        df = pd.DataFrame()
        
        direction, confidence, details = detect_trend_ema(df)
        assert direction == TrendDirection.SIDEWAYS
        assert confidence == 0.0
    
    def test_nan_values(self, sample_uptrend_df):
        """Test handling of NaN values"""
        df = sample_uptrend_df.copy()
        df.iloc[50:60, df.columns.get_loc('close')] = np.nan
        
        # Should still work, handling NaN gracefully
        direction, confidence, details = detect_trend_ema(df)
        # May have reduced confidence but shouldn't crash
    
    def test_single_candle(self):
        """Test handling of single candle"""
        df = pd.DataFrame({
            'open': [100],
            'high': [102],
            'low': [99],
            'close': [101],
            'volume': [1000],
        })
        
        direction, confidence, details = detect_trend_ema(df)
        assert direction == TrendDirection.SIDEWAYS
    
    def test_aggregation_insufficient_data(self):
        """Test aggregation with insufficient data"""
        df = pd.DataFrame({
            'open': [100, 101, 102],
            'high': [102, 103, 104],
            'low': [99, 100, 101],
            'close': [101, 102, 103],
            'volume': [1000, 1000, 1000],
        }, index=pd.date_range('2024-01-01', periods=3, freq='1h'))
        
        # 3 1h candles can't make enough 4h candles
        result = aggregate_to_higher_tf(df, '1h', '4h')
        # Might return None or very short DataFrame
        assert result is None or len(result) < 10


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
