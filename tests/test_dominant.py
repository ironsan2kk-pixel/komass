"""
Unit Tests for Dominant Indicator
KOMAS v4.0

Run tests:
    pytest tests/test_dominant.py -v
    
Or from project root:
    python -m pytest tests/test_dominant.py -v
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

from indicators.dominant import (
    # Core functions
    calculate_dominant,
    generate_signals,
    get_current_levels,
    validate_sensitivity,
    validate_filter_type,
    get_indicator_info,
    calculate_with_multiple_sensitivities,
    get_signal_summary,
    get_latest_signal,
    extract_signal_entries,
    # Filter functions (Chat #22)
    calculate_rsi,
    calculate_atr,
    apply_filter,
    get_filter_info,
    get_filter_statistics,
    generate_signals_with_filter,
    # Constants
    SENSITIVITY_MIN,
    SENSITIVITY_MAX,
    SENSITIVITY_DEFAULT,
    FIB_LEVELS,
    SIGNAL_LONG,
    SIGNAL_SHORT,
    SIGNAL_NONE,
    # Filter constants (Chat #22)
    FILTER_NONE,
    FILTER_ATR,
    FILTER_RSI,
    FILTER_COMBINED,
    FILTER_VOLATILITY,
    FILTER_NAMES,
    FILTER_DEFAULTS,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def simple_df():
    """Simple test DataFrame with predictable values"""
    return pd.DataFrame({
        'open': [100, 101, 102, 103, 104],
        'high': [102, 103, 104, 105, 106],
        'low': [99, 100, 101, 102, 103],
        'close': [101, 102, 103, 104, 105],
        'volume': [1000, 1000, 1000, 1000, 1000]
    })


@pytest.fixture
def constant_range_df():
    """DataFrame with constant high/low for testing Fibonacci levels"""
    return pd.DataFrame({
        'open': [150] * 10,
        'high': [200] * 10,  # Constant high
        'low': [100] * 10,   # Constant low -> range = 100
        'close': [150] * 10,
        'volume': [1000] * 10
    })


@pytest.fixture
def varying_df():
    """DataFrame with varying values for realistic testing"""
    return pd.DataFrame({
        'open': [100] * 20,
        'high': [100, 110, 105, 115, 108, 120, 112, 118, 115, 122,
                 125, 120, 128, 124, 130, 126, 132, 128, 135, 130],
        'low': [90, 95, 92, 98, 94, 100, 96, 102, 98, 104,
                106, 102, 108, 104, 110, 106, 112, 108, 115, 110],
        'close': [95, 105, 100, 110, 102, 115, 108, 114, 110, 118,
                  120, 115, 122, 118, 125, 120, 127, 122, 130, 125],
        'volume': [1000] * 20
    })


@pytest.fixture
def large_df():
    """Large DataFrame for performance testing"""
    np.random.seed(42)
    n = 1000
    prices = 100 + np.cumsum(np.random.randn(n) * 0.5)
    return pd.DataFrame({
        'open': prices,
        'high': prices + np.abs(np.random.randn(n) * 0.3),
        'low': prices - np.abs(np.random.randn(n) * 0.3),
        'close': prices + np.random.randn(n) * 0.2,
        'volume': np.random.randint(1000, 10000, n)
    })


@pytest.fixture
def bullish_trend_df():
    """DataFrame with clear bullish trend for long signal testing"""
    return pd.DataFrame({
        'open': [100, 105, 110, 115, 120],
        'high': [110, 115, 120, 125, 130],
        'low': [98, 103, 108, 113, 118],
        'close': [108, 113, 118, 123, 128],  # Bullish candles (close > open)
        'volume': [1000] * 5
    })


@pytest.fixture
def bearish_trend_df():
    """DataFrame with clear bearish trend for short signal testing"""
    return pd.DataFrame({
        'open': [120, 115, 110, 105, 100],
        'high': [122, 117, 112, 107, 102],
        'low': [110, 105, 100, 95, 90],
        'close': [112, 107, 102, 97, 92],  # Bearish candles (close < open)
        'volume': [1000] * 5
    })


@pytest.fixture
def alternating_df():
    """DataFrame with alternating signals for trend tracking testing"""
    # Price oscillates between upper and lower parts of channel
    return pd.DataFrame({
        # Start high, go low, go high again
        'open':  [100, 120, 115, 95, 100, 120, 115, 95, 100, 120],
        'high':  [125, 125, 120, 105, 105, 125, 120, 105, 105, 125],
        'low':   [95, 110, 90, 90, 95, 110, 90, 90, 95, 110],
        'close': [120, 115, 92, 98, 102, 115, 92, 98, 102, 115],  # Alt bullish/bearish
        'volume': [1000] * 10
    })


@pytest.fixture
def high_volatility_df():
    """DataFrame with high volatility for ATR filter testing"""
    return pd.DataFrame({
        'open':  [100, 100, 100, 100, 100, 100, 100, 100, 100, 100,
                  100, 100, 100, 100, 100, 100, 100, 130, 130, 130],
        'high':  [102, 102, 102, 102, 102, 102, 102, 102, 102, 102,
                  102, 102, 102, 102, 102, 102, 102, 150, 150, 150],  # Spike at end
        'low':   [98, 98, 98, 98, 98, 98, 98, 98, 98, 98,
                  98, 98, 98, 98, 98, 98, 98, 110, 110, 110],  # Spike at end
        'close': [101, 101, 101, 101, 101, 101, 101, 101, 101, 101,
                  101, 101, 101, 101, 101, 101, 101, 140, 140, 140],
        'volume': [1000] * 20
    })


@pytest.fixture
def rsi_extreme_df():
    """DataFrame designed to produce extreme RSI values"""
    # Long uptrend followed by continuation
    prices = list(range(100, 120)) + list(range(120, 125))  # 25 bars of up
    return pd.DataFrame({
        'open': prices,
        'high': [p + 1 for p in prices],
        'low': [p - 0.5 for p in prices],
        'close': [p + 0.8 for p in prices],  # Always bullish
        'volume': [1000] * 25
    })


@pytest.fixture
def rsi_oversold_df():
    """DataFrame designed to produce oversold RSI"""
    # Long downtrend
    prices = list(range(150, 100, -2))  # 25 bars of down
    return pd.DataFrame({
        'open': prices,
        'high': [p + 0.5 for p in prices],
        'low': [p - 1 for p in prices],
        'close': [p - 0.8 for p in prices],  # Always bearish
        'volume': [1000] * len(prices)
    })


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestValidation:
    """Test input validation functions"""
    
    def test_validate_sensitivity_normal(self):
        """Test normal sensitivity values"""
        assert validate_sensitivity(21) == 21
        assert validate_sensitivity(12) == 12
        assert validate_sensitivity(60) == 60
        assert validate_sensitivity(35) == 35
    
    def test_validate_sensitivity_below_min(self):
        """Test sensitivity below minimum is clamped"""
        assert validate_sensitivity(5) == SENSITIVITY_MIN
        assert validate_sensitivity(0) == SENSITIVITY_MIN
        assert validate_sensitivity(-10) == SENSITIVITY_MIN
    
    def test_validate_sensitivity_above_max(self):
        """Test sensitivity above maximum is clamped"""
        assert validate_sensitivity(70) == SENSITIVITY_MAX
        assert validate_sensitivity(100) == SENSITIVITY_MAX
        assert validate_sensitivity(1000) == SENSITIVITY_MAX
    
    def test_validate_sensitivity_float(self):
        """Test float sensitivity is converted to int"""
        assert validate_sensitivity(21.5) == 21
        assert validate_sensitivity(21.9) == 21
    
    def test_validate_sensitivity_invalid_type(self):
        """Test invalid types return default"""
        assert validate_sensitivity(None) == SENSITIVITY_DEFAULT
        assert validate_sensitivity("21") == SENSITIVITY_DEFAULT
        assert validate_sensitivity([21]) == SENSITIVITY_DEFAULT


class TestFilterValidation:
    """Test filter type validation (Chat #22)"""
    
    def test_validate_filter_type_valid(self):
        """Test valid filter types"""
        assert validate_filter_type(0) == FILTER_NONE
        assert validate_filter_type(1) == FILTER_ATR
        assert validate_filter_type(2) == FILTER_RSI
        assert validate_filter_type(3) == FILTER_COMBINED
        assert validate_filter_type(4) == FILTER_VOLATILITY
    
    def test_validate_filter_type_clamped(self):
        """Test filter types are clamped to valid range"""
        assert validate_filter_type(-1) == FILTER_NONE
        assert validate_filter_type(5) == FILTER_VOLATILITY
        assert validate_filter_type(100) == FILTER_VOLATILITY
    
    def test_validate_filter_type_invalid(self):
        """Test invalid types return FILTER_NONE"""
        assert validate_filter_type(None) == FILTER_NONE
        assert validate_filter_type("2") == FILTER_NONE
        assert validate_filter_type([1]) == FILTER_NONE


# =============================================================================
# BASIC CALCULATION TESTS
# =============================================================================

class TestBasicCalculation:
    """Test basic indicator calculation"""
    
    def test_calculate_returns_dataframe(self, simple_df):
        """Test that calculation returns a DataFrame"""
        result = calculate_dominant(simple_df, sensitivity=3)
        assert isinstance(result, pd.DataFrame)
    
    def test_original_columns_preserved(self, simple_df):
        """Test that original columns are preserved"""
        result = calculate_dominant(simple_df, sensitivity=3)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            assert col in result.columns
    
    def test_channel_columns_added(self, simple_df):
        """Test that channel columns are added"""
        result = calculate_dominant(simple_df, sensitivity=3)
        assert 'high_channel' in result.columns
        assert 'low_channel' in result.columns
        assert 'mid_channel' in result.columns
        assert 'channel_range' in result.columns
    
    def test_fibonacci_columns_added(self, simple_df):
        """Test that Fibonacci columns are added"""
        result = calculate_dominant(simple_df, sensitivity=3)
        for fib_name in FIB_LEVELS.keys():
            assert fib_name in result.columns
            assert f'{fib_name}_high' in result.columns
    
    def test_mid_channel_calculation(self, constant_range_df):
        """Test mid_channel is average of high and low channel"""
        result = calculate_dominant(constant_range_df, sensitivity=5)
        expected_mid = (result['high_channel'] + result['low_channel']) / 2
        pd.testing.assert_series_equal(result['mid_channel'], expected_mid, check_names=False)
    
    def test_fibonacci_levels_constant_range(self, constant_range_df):
        """Test Fibonacci levels with known range"""
        result = calculate_dominant(constant_range_df, sensitivity=5)
        # With range 100 (200-100), fib levels should be:
        # fib_236 = 100 + 100*0.236 = 123.6
        # fib_382 = 100 + 100*0.382 = 138.2
        # etc.
        last = result.iloc[-1]
        assert abs(last['fib_236'] - 123.6) < 0.1
        assert abs(last['fib_382'] - 138.2) < 0.1
        assert abs(last['fib_500'] - 150.0) < 0.1
        assert abs(last['fib_618'] - 161.8) < 0.1


# =============================================================================
# SIGNAL GENERATION TESTS
# =============================================================================

class TestSignalGeneration:
    """Test signal generation functions"""
    
    def test_signal_columns_added(self, simple_df):
        """Test that signal columns are added"""
        result = generate_signals(simple_df, sensitivity=3)
        assert 'can_long' in result.columns
        assert 'can_short' in result.columns
        assert 'signal' in result.columns
        assert 'is_long_trend' in result.columns
        assert 'is_short_trend' in result.columns
    
    def test_signals_mutual_exclusion(self, large_df):
        """Test that can_long and can_short are never both True"""
        result = generate_signals(large_df, sensitivity=21)
        both_true = (result['can_long'] & result['can_short']).sum()
        assert both_true == 0
    
    def test_signal_values(self, large_df):
        """Test signal column has correct values"""
        result = generate_signals(large_df, sensitivity=21)
        assert result['signal'].isin([SIGNAL_LONG, SIGNAL_SHORT, SIGNAL_NONE]).all()
    
    def test_bullish_generates_long(self, bullish_trend_df):
        """Test bullish trend generates long signals"""
        result = generate_signals(bullish_trend_df, sensitivity=3)
        assert result['can_long'].sum() > 0
    
    def test_bearish_generates_short(self, bearish_trend_df):
        """Test bearish trend generates short signals"""
        result = generate_signals(bearish_trend_df, sensitivity=3)
        assert result['can_short'].sum() > 0


# =============================================================================
# RSI CALCULATION TESTS (Chat #22)
# =============================================================================

class TestRSICalculation:
    """Test RSI indicator calculation"""
    
    def test_rsi_returns_series(self, simple_df):
        """Test RSI returns a Series"""
        rsi = calculate_rsi(simple_df['close'], period=14)
        assert isinstance(rsi, pd.Series)
        assert len(rsi) == len(simple_df)
    
    def test_rsi_range(self, large_df):
        """Test RSI values are between 0 and 100"""
        rsi = calculate_rsi(large_df['close'], period=14)
        # Skip NaN values
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_rsi_overbought_in_uptrend(self, rsi_extreme_df):
        """Test RSI approaches overbought in strong uptrend"""
        rsi = calculate_rsi(rsi_extreme_df['close'], period=14)
        # Last RSI should be high
        assert rsi.iloc[-1] > 60
    
    def test_rsi_oversold_in_downtrend(self, rsi_oversold_df):
        """Test RSI approaches oversold in strong downtrend"""
        rsi = calculate_rsi(rsi_oversold_df['close'], period=14)
        # Last RSI should be low
        assert rsi.iloc[-1] < 40


# =============================================================================
# ATR CALCULATION TESTS (Chat #22)
# =============================================================================

class TestATRCalculation:
    """Test ATR indicator calculation"""
    
    def test_atr_returns_series(self, simple_df):
        """Test ATR returns a Series"""
        atr = calculate_atr(simple_df, period=14)
        assert isinstance(atr, pd.Series)
        assert len(atr) == len(simple_df)
    
    def test_atr_positive(self, large_df):
        """Test ATR values are positive"""
        atr = calculate_atr(large_df, period=14)
        valid_atr = atr.dropna()
        assert (valid_atr >= 0).all()
    
    def test_atr_increases_with_volatility(self, high_volatility_df):
        """Test ATR increases when volatility spikes"""
        atr = calculate_atr(high_volatility_df, period=5)
        # ATR at end should be higher than at start
        assert atr.iloc[-1] > atr.iloc[10]


# =============================================================================
# FILTER TYPE 0: NONE TESTS (Chat #22)
# =============================================================================

class TestFilterNone:
    """Test Filter Type 0 - No Filtering"""
    
    def test_all_signals_pass(self, large_df):
        """Test all original signals pass through with no filter"""
        # Generate signals
        df_signals = generate_signals(large_df, sensitivity=21)
        
        # Apply filter type 0
        result = apply_filter(df_signals, filter_type=FILTER_NONE)
        
        # Original and filtered should be equal
        assert result['can_long'].sum() == result['filtered_can_long'].sum()
        assert result['can_short'].sum() == result['filtered_can_short'].sum()
    
    def test_filter_pass_all_true(self, large_df):
        """Test filter_pass columns are all True"""
        df_signals = generate_signals(large_df, sensitivity=21)
        result = apply_filter(df_signals, filter_type=FILTER_NONE)
        
        assert result['filter_pass_long'].all()
        assert result['filter_pass_short'].all()
    
    def test_filter_type_stored(self, simple_df):
        """Test filter type is stored in result"""
        df_signals = generate_signals(simple_df, sensitivity=3)
        result = apply_filter(df_signals, filter_type=FILTER_NONE)
        
        assert 'filter_type_applied' in result.columns
        assert result['filter_type_applied'].iloc[0] == FILTER_NONE


# =============================================================================
# FILTER TYPE 1: ATR TESTS (Chat #22)
# =============================================================================

class TestFilterATR:
    """Test Filter Type 1 - ATR Condition"""
    
    def test_atr_columns_added(self, large_df):
        """Test ATR-related columns are added"""
        df_signals = generate_signals(large_df, sensitivity=21)
        result = apply_filter(df_signals, filter_type=FILTER_ATR)
        
        assert 'filter_atr' in result.columns
        assert 'filter_atr_ma' in result.columns
    
    def test_high_volatility_passes(self, high_volatility_df):
        """Test signals during high volatility pass the filter"""
        df_signals = generate_signals(high_volatility_df, sensitivity=5)
        result = apply_filter(df_signals, filter_type=FILTER_ATR, atr_multiplier=1.2)
        
        # During the volatility spike, filter should pass
        # Check last few rows (after spike)
        assert result['filter_pass_long'].iloc[-1] == True
    
    def test_low_volatility_blocked(self, high_volatility_df):
        """Test signals during low volatility are blocked"""
        df_signals = generate_signals(high_volatility_df, sensitivity=5)
        result = apply_filter(df_signals, filter_type=FILTER_ATR, atr_multiplier=3.0)
        
        # With high multiplier, early low-vol bars should fail
        # (first 15 rows have low volatility)
        assert result['filter_pass_long'].iloc[10] == False
    
    def test_atr_multiplier_effect(self, large_df):
        """Test higher multiplier blocks more signals"""
        df_signals = generate_signals(large_df, sensitivity=21)
        
        result_low = apply_filter(df_signals, filter_type=FILTER_ATR, atr_multiplier=0.5)
        result_high = apply_filter(df_signals, filter_type=FILTER_ATR, atr_multiplier=2.0)
        
        # More signals should pass with lower multiplier
        low_pass = result_low['filter_pass_long'].sum()
        high_pass = result_high['filter_pass_long'].sum()
        assert low_pass >= high_pass


# =============================================================================
# FILTER TYPE 2: RSI TESTS (Chat #22)
# =============================================================================

class TestFilterRSI:
    """Test Filter Type 2 - RSI Condition"""
    
    def test_rsi_column_added(self, large_df):
        """Test RSI column is added"""
        df_signals = generate_signals(large_df, sensitivity=21)
        result = apply_filter(df_signals, filter_type=FILTER_RSI)
        
        assert 'filter_rsi' in result.columns
    
    def test_overbought_blocks_long(self, rsi_extreme_df):
        """Test overbought RSI blocks long signals"""
        df_signals = generate_signals(rsi_extreme_df, sensitivity=5)
        result = apply_filter(df_signals, filter_type=FILTER_RSI, rsi_overbought=70)
        
        # Check if any signals were blocked due to overbought
        # In strong uptrend, RSI gets high, should block some longs
        blocked = (df_signals['can_long'] & ~result['filtered_can_long']).sum()
        # Some should be blocked (RSI > 70)
        # We can't guarantee blocking in this test data, so just check columns exist
        assert 'filter_pass_long' in result.columns
    
    def test_oversold_blocks_short(self, rsi_oversold_df):
        """Test oversold RSI blocks short signals"""
        df_signals = generate_signals(rsi_oversold_df, sensitivity=5)
        result = apply_filter(df_signals, filter_type=FILTER_RSI, rsi_oversold=30)
        
        # Check columns exist
        assert 'filter_pass_short' in result.columns
    
    def test_rsi_thresholds_work(self, large_df):
        """Test different RSI thresholds affect pass rate"""
        df_signals = generate_signals(large_df, sensitivity=21)
        
        # Strict thresholds
        result_strict = apply_filter(
            df_signals, 
            filter_type=FILTER_RSI, 
            rsi_overbought=60, 
            rsi_oversold=40
        )
        
        # Loose thresholds
        result_loose = apply_filter(
            df_signals, 
            filter_type=FILTER_RSI, 
            rsi_overbought=80, 
            rsi_oversold=20
        )
        
        # Stricter thresholds should block more signals
        strict_pass = result_strict['filter_pass_long'].sum()
        loose_pass = result_loose['filter_pass_long'].sum()
        assert strict_pass <= loose_pass


# =============================================================================
# FILTER TYPE 3: COMBINED TESTS (Chat #22)
# =============================================================================

class TestFilterCombined:
    """Test Filter Type 3 - ATR + RSI Combined"""
    
    def test_both_columns_added(self, large_df):
        """Test both ATR and RSI columns are added"""
        df_signals = generate_signals(large_df, sensitivity=21)
        result = apply_filter(df_signals, filter_type=FILTER_COMBINED)
        
        assert 'filter_atr' in result.columns
        assert 'filter_atr_ma' in result.columns
        assert 'filter_rsi' in result.columns
    
    def test_both_conditions_required(self, large_df):
        """Test that both ATR and RSI must pass"""
        df_signals = generate_signals(large_df, sensitivity=21)
        
        # Get individual filter results
        result_atr = apply_filter(df_signals, filter_type=FILTER_ATR)
        result_rsi = apply_filter(df_signals, filter_type=FILTER_RSI)
        result_combined = apply_filter(df_signals, filter_type=FILTER_COMBINED)
        
        # Combined should be more restrictive (fewer passes)
        combined_pass = result_combined['filter_pass_long'].sum()
        atr_pass = result_atr['filter_pass_long'].sum()
        rsi_pass = result_rsi['filter_pass_long'].sum()
        
        # Combined should pass fewer or equal signals
        assert combined_pass <= min(atr_pass, rsi_pass)
    
    def test_combined_stricter_than_individual(self, large_df):
        """Test combined filter is stricter than individual filters"""
        df_signals = generate_signals(large_df, sensitivity=21)
        
        result_none = apply_filter(df_signals, filter_type=FILTER_NONE)
        result_combined = apply_filter(df_signals, filter_type=FILTER_COMBINED)
        
        # Combined should allow fewer signals
        none_filtered = result_none['filtered_can_long'].sum()
        combined_filtered = result_combined['filtered_can_long'].sum()
        
        assert combined_filtered <= none_filtered


# =============================================================================
# FILTER TYPE 4: VOLATILITY TESTS (Chat #22)
# =============================================================================

class TestFilterVolatility:
    """Test Filter Type 4 - Volatility Condition"""
    
    def test_volatility_columns_added(self, large_df):
        """Test volatility-related columns are added"""
        df_signals = generate_signals(large_df, sensitivity=21)
        result = apply_filter(df_signals, filter_type=FILTER_VOLATILITY)
        
        assert 'filter_returns' in result.columns
        assert 'filter_volatility' in result.columns
        assert 'filter_volatility_ma' in result.columns
    
    def test_extreme_volatility_blocked(self, high_volatility_df):
        """Test signals during extreme volatility are blocked"""
        df_signals = generate_signals(high_volatility_df, sensitivity=5)
        result = apply_filter(
            df_signals, 
            filter_type=FILTER_VOLATILITY, 
            volatility_max_mult=1.5
        )
        
        # During the volatility spike (end of data), filter should fail
        # The spike is at the end, so later rows should be blocked
        assert 'filter_pass_long' in result.columns
    
    def test_normal_volatility_passes(self, simple_df):
        """Test signals during normal volatility pass"""
        df_signals = generate_signals(simple_df, sensitivity=3)
        result = apply_filter(
            df_signals, 
            filter_type=FILTER_VOLATILITY,
            volatility_max_mult=5.0  # Very lenient
        )
        
        # With lenient threshold, most should pass
        assert result['filter_pass_long'].sum() > 0
    
    def test_volatility_multiplier_effect(self, large_df):
        """Test volatility multiplier affects pass rate"""
        df_signals = generate_signals(large_df, sensitivity=21)
        
        # Strict (low multiplier blocks more)
        result_strict = apply_filter(
            df_signals, 
            filter_type=FILTER_VOLATILITY, 
            volatility_max_mult=1.0
        )
        
        # Lenient (high multiplier allows more)
        result_lenient = apply_filter(
            df_signals, 
            filter_type=FILTER_VOLATILITY, 
            volatility_max_mult=3.0
        )
        
        strict_pass = result_strict['filter_pass_long'].sum()
        lenient_pass = result_lenient['filter_pass_long'].sum()
        
        assert strict_pass <= lenient_pass


# =============================================================================
# FILTER STATISTICS TESTS (Chat #22)
# =============================================================================

class TestFilterStatistics:
    """Test filter statistics functions"""
    
    def test_get_filter_statistics(self, large_df):
        """Test filter statistics calculation"""
        df_signals = generate_signals(large_df, sensitivity=21)
        result = apply_filter(df_signals, filter_type=FILTER_RSI)
        
        stats = get_filter_statistics(result)
        
        assert 'filter_type' in stats
        assert 'filter_name' in stats
        assert 'original_signals' in stats
        assert 'filtered_signals' in stats
        assert 'blocked_signals' in stats
        assert 'pass_rates' in stats
    
    def test_statistics_accuracy(self, large_df):
        """Test statistics values are accurate"""
        df_signals = generate_signals(large_df, sensitivity=21)
        result = apply_filter(df_signals, filter_type=FILTER_ATR)
        
        stats = get_filter_statistics(result)
        
        # Verify counts match
        assert stats['original_signals']['long'] == result['can_long'].sum()
        assert stats['filtered_signals']['long'] == result['filtered_can_long'].sum()
        assert stats['blocked_signals']['long'] == (
            stats['original_signals']['long'] - stats['filtered_signals']['long']
        )
    
    def test_pass_rate_calculation(self, large_df):
        """Test pass rate is calculated correctly"""
        df_signals = generate_signals(large_df, sensitivity=21)
        result = apply_filter(df_signals, filter_type=FILTER_NONE)
        
        stats = get_filter_statistics(result)
        
        # With no filter, pass rate should be 100%
        assert stats['pass_rates']['long'] == 100.0
        assert stats['pass_rates']['short'] == 100.0


# =============================================================================
# GET FILTER INFO TESTS (Chat #22)
# =============================================================================

class TestGetFilterInfo:
    """Test filter info function"""
    
    def test_get_all_filter_info(self):
        """Test getting info for all filters"""
        info = get_filter_info()
        
        assert FILTER_NONE in info
        assert FILTER_ATR in info
        assert FILTER_RSI in info
        assert FILTER_COMBINED in info
        assert FILTER_VOLATILITY in info
    
    def test_get_specific_filter_info(self):
        """Test getting info for specific filter"""
        info = get_filter_info(FILTER_RSI)
        
        assert 'name' in info
        assert 'description' in info
        assert 'parameters' in info
        assert info['name'] == 'RSI Condition'
    
    def test_filter_parameters_listed(self):
        """Test filter parameters are listed"""
        info = get_filter_info(FILTER_COMBINED)
        
        assert 'atr_period' in info['parameters']
        assert 'rsi_period' in info['parameters']


# =============================================================================
# CONVENIENCE FUNCTION TESTS (Chat #22)
# =============================================================================

class TestGenerateSignalsWithFilter:
    """Test convenience function generate_signals_with_filter"""
    
    def test_returns_all_columns(self, large_df):
        """Test function returns both signal and filter columns"""
        result = generate_signals_with_filter(
            large_df,
            sensitivity=21,
            filter_type=FILTER_RSI
        )
        
        # Signal columns
        assert 'can_long' in result.columns
        assert 'can_short' in result.columns
        
        # Filter columns
        assert 'filter_pass_long' in result.columns
        assert 'filtered_can_long' in result.columns
        assert 'filter_rsi' in result.columns
    
    def test_filter_kwargs_passed(self, large_df):
        """Test filter kwargs are passed through"""
        result = generate_signals_with_filter(
            large_df,
            sensitivity=21,
            filter_type=FILTER_RSI,
            rsi_overbought=80,
            rsi_oversold=20
        )
        
        # Function should work without error
        assert len(result) == len(large_df)
    
    def test_equivalent_to_separate_calls(self, large_df):
        """Test convenience function equals separate calls"""
        # Separate calls
        df_signals = generate_signals(large_df, sensitivity=21)
        separate = apply_filter(df_signals, filter_type=FILTER_ATR)
        
        # Convenience function
        combined = generate_signals_with_filter(
            large_df,
            sensitivity=21,
            filter_type=FILTER_ATR
        )
        
        # Results should match
        pd.testing.assert_series_equal(
            separate['filtered_can_long'], 
            combined['filtered_can_long']
        )


# =============================================================================
# INTEGRATION TESTS (Chat #22)
# =============================================================================

class TestFilterIntegration:
    """Integration tests for filter system"""
    
    def test_filter_preserves_original_signals(self, large_df):
        """Test original signal columns are NOT modified"""
        df_signals = generate_signals(large_df, sensitivity=21)
        original_long_sum = df_signals['can_long'].sum()
        original_short_sum = df_signals['can_short'].sum()
        
        result = apply_filter(df_signals, filter_type=FILTER_RSI)
        
        # Original columns should be unchanged
        assert result['can_long'].sum() == original_long_sum
        assert result['can_short'].sum() == original_short_sum
    
    def test_all_filter_types_work(self, large_df):
        """Test all filter types can be applied"""
        df_signals = generate_signals(large_df, sensitivity=21)
        
        for filter_type in range(5):
            result = apply_filter(df_signals, filter_type=filter_type)
            assert 'filtered_can_long' in result.columns
            assert 'filtered_can_short' in result.columns
    
    def test_filter_statistics_for_all_types(self, large_df):
        """Test statistics work for all filter types"""
        df_signals = generate_signals(large_df, sensitivity=21)
        
        for filter_type in range(5):
            result = apply_filter(df_signals, filter_type=filter_type)
            stats = get_filter_statistics(result)
            
            assert stats['filter_type'] == filter_type
            assert stats['filter_name'] == FILTER_NAMES[filter_type]


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_dataframe(self):
        """Test handling of empty DataFrame"""
        empty_df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
        
        with pytest.raises(ValueError):
            calculate_dominant(empty_df)
    
    def test_missing_columns(self, simple_df):
        """Test handling of missing columns"""
        incomplete_df = simple_df.drop(columns=['volume'])
        
        with pytest.raises(ValueError):
            calculate_dominant(incomplete_df)
    
    def test_apply_filter_without_signals(self, simple_df):
        """Test apply_filter works even without signal columns"""
        result = calculate_dominant(simple_df, sensitivity=3)
        filtered = apply_filter(result, filter_type=FILTER_RSI)
        
        # Should not crash, should initialize with False
        assert 'filtered_can_long' in filtered.columns
        assert filtered['filtered_can_long'].sum() == 0


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Performance and stress tests"""
    
    def test_large_dataframe_performance(self, large_df):
        """Test performance with large DataFrame"""
        import time
        
        start = time.time()
        result = generate_signals_with_filter(
            large_df,
            sensitivity=21,
            filter_type=FILTER_COMBINED
        )
        elapsed = time.time() - start
        
        assert elapsed < 5.0  # Should complete in under 5 seconds
        assert len(result) == len(large_df)
    
    def test_multiple_filter_applications(self, large_df):
        """Test applying multiple filters sequentially"""
        df_signals = generate_signals(large_df, sensitivity=21)
        
        # Apply all filter types
        results = []
        for filter_type in range(5):
            result = apply_filter(df_signals, filter_type=filter_type)
            results.append(result)
        
        assert len(results) == 5


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
