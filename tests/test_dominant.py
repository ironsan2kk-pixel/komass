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
    calculate_dominant,
    generate_signals,
    get_current_levels,
    validate_sensitivity,
    get_indicator_info,
    calculate_with_multiple_sensitivities,
    get_signal_summary,
    get_latest_signal,
    extract_signal_entries,
    SENSITIVITY_MIN,
    SENSITIVITY_MAX,
    SENSITIVITY_DEFAULT,
    FIB_LEVELS,
    SIGNAL_LONG,
    SIGNAL_SHORT,
    SIGNAL_NONE,
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
        # From low
        assert 'fib_236' in result.columns
        assert 'fib_382' in result.columns
        assert 'fib_500' in result.columns
        assert 'fib_618' in result.columns
        # From high
        assert 'fib_236_high' in result.columns
        assert 'fib_382_high' in result.columns
        assert 'fib_500_high' in result.columns
        assert 'fib_618_high' in result.columns
    
    def test_derived_columns_added(self, simple_df):
        """Test that derived columns are added"""
        result = calculate_dominant(simple_df, sensitivity=3)
        assert 'channel_width_pct' in result.columns
        assert 'price_position' in result.columns
    
    def test_row_count_unchanged(self, simple_df):
        """Test that row count is unchanged"""
        result = calculate_dominant(simple_df, sensitivity=3)
        assert len(result) == len(simple_df)


# =============================================================================
# CHANNEL CALCULATION TESTS
# =============================================================================

class TestChannelCalculation:
    """Test channel boundary calculations"""
    
    def test_high_channel_is_rolling_max(self, varying_df):
        """Test high_channel is rolling maximum of high prices"""
        result = calculate_dominant(varying_df, sensitivity=5)
        
        # At index 4 (first full window)
        # high values [0:5] = [100, 110, 105, 115, 108]
        # max = 115
        assert result['high_channel'].iloc[4] == 115
    
    def test_low_channel_is_rolling_min(self, varying_df):
        """Test low_channel is rolling minimum of low prices"""
        result = calculate_dominant(varying_df, sensitivity=5)
        
        # At index 4 (first full window)
        # low values [0:5] = [90, 95, 92, 98, 94]
        # min = 90
        assert result['low_channel'].iloc[4] == 90
    
    def test_mid_channel_is_average(self, constant_range_df):
        """Test mid_channel is average of high and low channel"""
        result = calculate_dominant(constant_range_df, sensitivity=3)
        
        # high_channel = 200, low_channel = 100
        # mid = (200 + 100) / 2 = 150
        assert result['mid_channel'].iloc[-1] == 150
    
    def test_channel_range_is_difference(self, constant_range_df):
        """Test channel_range is high - low channel"""
        result = calculate_dominant(constant_range_df, sensitivity=3)
        
        # range = 200 - 100 = 100
        assert result['channel_range'].iloc[-1] == 100
    
    def test_channel_with_min_periods(self, simple_df):
        """Test that channel works with min_periods=1"""
        result = calculate_dominant(simple_df, sensitivity=10)
        
        # Even with sensitivity > data length, should have values
        assert not result['high_channel'].isna().all()
        assert not result['low_channel'].isna().all()


# =============================================================================
# FIBONACCI LEVEL TESTS
# =============================================================================

class TestFibonacciLevels:
    """Test Fibonacci level calculations"""
    
    def test_fibonacci_from_low(self, constant_range_df):
        """Test Fibonacci levels calculated from low channel"""
        result = calculate_dominant(constant_range_df, sensitivity=3)
        
        # low_channel = 100, range = 100
        # fib_236 = 100 + 100 * 0.236 = 123.6
        # fib_382 = 100 + 100 * 0.382 = 138.2
        # fib_500 = 100 + 100 * 0.500 = 150.0
        # fib_618 = 100 + 100 * 0.618 = 161.8
        
        assert abs(result['fib_236'].iloc[-1] - 123.6) < 0.01
        assert abs(result['fib_382'].iloc[-1] - 138.2) < 0.01
        assert abs(result['fib_500'].iloc[-1] - 150.0) < 0.01
        assert abs(result['fib_618'].iloc[-1] - 161.8) < 0.01
    
    def test_fibonacci_from_high(self, constant_range_df):
        """Test Fibonacci levels calculated from high channel"""
        result = calculate_dominant(constant_range_df, sensitivity=3)
        
        # high_channel = 200, range = 100
        # fib_236_high = 200 - 100 * 0.236 = 176.4
        # fib_382_high = 200 - 100 * 0.382 = 161.8
        # fib_500_high = 200 - 100 * 0.500 = 150.0
        # fib_618_high = 200 - 100 * 0.618 = 138.2
        
        assert abs(result['fib_236_high'].iloc[-1] - 176.4) < 0.01
        assert abs(result['fib_382_high'].iloc[-1] - 161.8) < 0.01
        assert abs(result['fib_500_high'].iloc[-1] - 150.0) < 0.01
        assert abs(result['fib_618_high'].iloc[-1] - 138.2) < 0.01
    
    def test_mid_equals_fib_500(self, constant_range_df):
        """Test that mid_channel equals fib_500 and fib_500_high"""
        result = calculate_dominant(constant_range_df, sensitivity=3)
        
        mid = result['mid_channel'].iloc[-1]
        fib_500 = result['fib_500'].iloc[-1]
        fib_500_high = result['fib_500_high'].iloc[-1]
        
        assert abs(mid - fib_500) < 0.01
        assert abs(mid - fib_500_high) < 0.01
    
    def test_fib_levels_ordering(self, constant_range_df):
        """Test Fibonacci levels are in correct order"""
        result = calculate_dominant(constant_range_df, sensitivity=3)
        
        # From low: low < fib_236 < fib_382 < fib_500 < fib_618 < high
        low = result['low_channel'].iloc[-1]
        high = result['high_channel'].iloc[-1]
        
        assert low < result['fib_236'].iloc[-1]
        assert result['fib_236'].iloc[-1] < result['fib_382'].iloc[-1]
        assert result['fib_382'].iloc[-1] < result['fib_500'].iloc[-1]
        assert result['fib_500'].iloc[-1] < result['fib_618'].iloc[-1]
        assert result['fib_618'].iloc[-1] < high


# =============================================================================
# SIGNAL GENERATION TESTS (Chat #21)
# =============================================================================

class TestSignalGeneration:
    """Test signal generation functionality"""
    
    def test_signal_columns_added(self, simple_df):
        """Test that all signal columns are added"""
        result = generate_signals(simple_df, sensitivity=3)
        
        assert 'can_long' in result.columns
        assert 'can_short' in result.columns
        assert 'signal' in result.columns
        assert 'is_long_trend' in result.columns
        assert 'is_short_trend' in result.columns
        assert 'entry_price' in result.columns
        assert 'signal_type' in result.columns
    
    def test_signal_column_types(self, simple_df):
        """Test signal column data types"""
        result = generate_signals(simple_df, sensitivity=3)
        
        assert result['can_long'].dtype == bool
        assert result['can_short'].dtype == bool
        # signal is int-like (1, -1, 0)
        assert result['signal'].isin([SIGNAL_LONG, SIGNAL_SHORT, SIGNAL_NONE]).all()
        assert result['is_long_trend'].dtype == bool
        assert result['is_short_trend'].dtype == bool
    
    def test_signal_constants(self):
        """Test signal constant values"""
        assert SIGNAL_LONG == 1
        assert SIGNAL_SHORT == -1
        assert SIGNAL_NONE == 0


class TestLongSignal:
    """Test long signal generation"""
    
    def test_long_signal_conditions(self, bullish_trend_df):
        """Test long signal fires when conditions met"""
        result = generate_signals(bullish_trend_df, sensitivity=3)
        
        # In bullish trend, should have at least one long signal
        assert result['can_long'].any(), "Expected at least one long signal in bullish trend"
    
    def test_long_signal_requires_bullish_candle(self):
        """Test long signal requires bullish candle when confirmation enabled"""
        # Create scenario: price in right zone but bearish candle
        df = pd.DataFrame({
            'open': [170, 175, 180],  # Close < Open = bearish
            'high': [180, 185, 190],
            'low': [100, 100, 100],
            'close': [160, 165, 170],  # Below open = bearish candles
            'volume': [1000, 1000, 1000]
        })
        
        result = generate_signals(df, sensitivity=3, require_confirmation=True)
        
        # Even if price above mid, bearish candle should block long signal
        # mid = (190 + 100) / 2 = 145
        # close = 170 > 145 (above mid)
        # But close < open (bearish)
        assert not result['can_long'].iloc[-1], "Long should not fire with bearish candle"
    
    def test_long_signal_without_confirmation(self):
        """Test long signal without candle confirmation"""
        df = pd.DataFrame({
            'open': [170, 175, 180],  # Bearish candles
            'high': [180, 185, 190],
            'low': [100, 100, 100],
            'close': [160, 165, 170],  # Below open but in upper zone
            'volume': [1000, 1000, 1000]
        })
        
        result = generate_signals(df, sensitivity=3, require_confirmation=False)
        
        # Without confirmation, should fire based on price position only
        # Price is above mid (145) and above fib_236
        assert result['can_long'].iloc[-1], "Long should fire without confirmation requirement"


class TestShortSignal:
    """Test short signal generation"""
    
    def test_short_signal_conditions(self, bearish_trend_df):
        """Test short signal fires when conditions met"""
        result = generate_signals(bearish_trend_df, sensitivity=3)
        
        # In bearish trend, should have at least one short signal
        assert result['can_short'].any(), "Expected at least one short signal in bearish trend"
    
    def test_short_signal_requires_bearish_candle(self):
        """Test short signal requires bearish candle when confirmation enabled"""
        # Create scenario: price in right zone but bullish candle
        df = pd.DataFrame({
            'open': [110, 115, 120],  # Open < Close = bullish
            'high': [200, 200, 200],
            'low': [100, 105, 110],
            'close': [120, 125, 130],  # Above open = bullish candles
            'volume': [1000, 1000, 1000]
        })
        
        result = generate_signals(df, sensitivity=3, require_confirmation=True)
        
        # Price below mid but bullish candle should block short
        # mid = (200 + 100) / 2 = 150
        # close = 130 < 150 (below mid)
        # But close > open (bullish)
        assert not result['can_short'].iloc[-1], "Short should not fire with bullish candle"
    
    def test_short_signal_without_confirmation(self):
        """Test short signal without candle confirmation"""
        df = pd.DataFrame({
            'open': [110, 115, 120],  # Bullish candles
            'high': [200, 200, 200],
            'low': [100, 105, 110],
            'close': [120, 125, 130],  # Above open but in lower zone
            'volume': [1000, 1000, 1000]
        })
        
        result = generate_signals(df, sensitivity=3, require_confirmation=False)
        
        # Without confirmation, should fire based on price position
        assert result['can_short'].iloc[-1], "Short should fire without confirmation requirement"


class TestNoSignal:
    """Test scenarios where no signal should fire"""
    
    def test_no_signal_in_middle(self, constant_range_df):
        """Test no signal when price in middle of channel"""
        # Price at exactly mid_channel (150) with small movement
        result = generate_signals(constant_range_df, sensitivity=3)
        
        # Mid channel = 150, price = 150
        # Not clearly above or below, signals depend on exact conditions
        # At minimum, we shouldn't have BOTH signals on same candle
        same_candle_both = (result['can_long'] & result['can_short']).any()
        assert not same_candle_both, "Cannot have both long and short on same candle"
    
    def test_mutual_exclusion(self, large_df):
        """Test that can_long and can_short are mutually exclusive"""
        result = generate_signals(large_df, sensitivity=21)
        
        # No candle should have both signals
        both_signals = (result['can_long'] & result['can_short']).sum()
        assert both_signals == 0, f"Found {both_signals} candles with both signals"


class TestTrendTracking:
    """Test trend state tracking"""
    
    def test_long_trend_starts_on_long_signal(self):
        """Test is_long_trend becomes True when can_long fires"""
        df = pd.DataFrame({
            'open': [100, 105, 110, 115, 120],
            'high': [110, 115, 120, 125, 130],
            'low': [95, 100, 105, 110, 115],
            'close': [108, 113, 118, 123, 128],  # Bullish candles
            'volume': [1000] * 5
        })
        
        result = generate_signals(df, sensitivity=3)
        
        # Find first long signal
        long_idx = result[result['can_long']].index
        if len(long_idx) > 0:
            first_long = long_idx[0]
            # After long signal, should be in long trend
            assert result.loc[first_long, 'is_long_trend'], "Should be in long trend after long signal"
    
    def test_short_trend_starts_on_short_signal(self):
        """Test is_short_trend becomes True when can_short fires"""
        df = pd.DataFrame({
            'open': [120, 115, 110, 105, 100],
            'high': [125, 120, 115, 110, 105],
            'low': [110, 105, 100, 95, 90],
            'close': [112, 107, 102, 97, 92],  # Bearish candles
            'volume': [1000] * 5
        })
        
        result = generate_signals(df, sensitivity=3)
        
        # Find first short signal
        short_idx = result[result['can_short']].index
        if len(short_idx) > 0:
            first_short = short_idx[0]
            # After short signal, should be in short trend
            assert result.loc[first_short, 'is_short_trend'], "Should be in short trend after short signal"
    
    def test_trend_flips_on_reverse(self, alternating_df):
        """Test trend flips when reverse signal fires"""
        result = generate_signals(alternating_df, sensitivity=3)
        
        # After a flip, previous trend should be False
        for i in range(1, len(result)):
            if result['can_long'].iloc[i]:
                # Long signal: short trend should be False
                assert not result['is_short_trend'].iloc[i], "Short trend should end on long signal"
            elif result['can_short'].iloc[i]:
                # Short signal: long trend should be False
                assert not result['is_long_trend'].iloc[i], "Long trend should end on short signal"
    
    def test_only_one_trend_active(self, large_df):
        """Test that only one trend can be active at a time"""
        result = generate_signals(large_df, sensitivity=21)
        
        # Both trends can't be True simultaneously
        both_trends = (result['is_long_trend'] & result['is_short_trend']).sum()
        assert both_trends == 0, f"Found {both_trends} rows with both trends active"
    
    def test_trend_persists_without_signal(self):
        """Test that trend persists until reverse signal"""
        # Create scenario: long signal, then neutral bars, then short
        df = pd.DataFrame({
            'open':  [100, 110, 150, 150, 150, 140, 130],
            'high':  [115, 120, 155, 155, 155, 145, 135],
            'low':   [95, 100, 145, 145, 145, 125, 120],
            'close': [112, 118, 152, 152, 152, 128, 122],
            'volume': [1000] * 7
        })
        
        result = generate_signals(df, sensitivity=3)
        
        # Trend should persist through neutral bars
        if result['can_long'].any():
            first_long_idx = result[result['can_long']].index[0]
            
            # Check that trend persists after first long until short
            for i in range(first_long_idx + 1, len(result)):
                if result['can_short'].iloc[i]:
                    break
                # Should still be in long trend
                if not result['can_long'].iloc[i]:  # On non-signal bars
                    assert result['is_long_trend'].iloc[i], f"Long trend should persist at index {i}"


class TestEntryPrice:
    """Test entry price calculation"""
    
    def test_entry_price_on_signal(self, bullish_trend_df):
        """Test entry_price equals close when signal fires"""
        result = generate_signals(bullish_trend_df, sensitivity=3)
        
        # On signal candles, entry_price should equal close
        signal_rows = result[result['signal'] != SIGNAL_NONE]
        
        for idx in signal_rows.index:
            assert result.loc[idx, 'entry_price'] == result.loc[idx, 'close'], \
                f"Entry price should equal close at index {idx}"
    
    def test_entry_price_nan_without_signal(self, constant_range_df):
        """Test entry_price is NaN when no signal"""
        result = generate_signals(constant_range_df, sensitivity=3)
        
        # On non-signal candles, entry_price should be NaN
        no_signal_rows = result[result['signal'] == SIGNAL_NONE]
        
        if len(no_signal_rows) > 0:
            # At least some should be NaN
            assert no_signal_rows['entry_price'].isna().any(), \
                "Entry price should be NaN on non-signal bars"


class TestSignalOnReverse:
    """Test close on reverse signal logic"""
    
    def test_close_long_on_short(self):
        """Test long position closes when short signal fires"""
        # Create: long signal, then short signal
        df = pd.DataFrame({
            'open':  [100, 110, 120, 110, 100],
            'high':  [115, 125, 130, 115, 105],
            'low':   [95, 105, 115, 95, 85],
            'close': [112, 122, 125, 98, 88],  # First bullish, then bearish
            'volume': [1000] * 5
        })
        
        result = generate_signals(df, sensitivity=3)
        
        # Find if we have long then short
        long_found = False
        for i in range(len(result)):
            if result['can_long'].iloc[i]:
                long_found = True
            if long_found and result['can_short'].iloc[i]:
                # On short signal, long trend should be False
                assert not result['is_long_trend'].iloc[i], \
                    "Long trend should end when short signal fires"
                break
    
    def test_close_short_on_long(self):
        """Test short position closes when long signal fires"""
        # Create: short signal, then long signal
        df = pd.DataFrame({
            'open':  [120, 110, 100, 110, 120],
            'high':  [125, 115, 105, 125, 135],
            'low':   [105, 95, 85, 105, 115],
            'close': [108, 98, 88, 122, 132],  # First bearish, then bullish
            'volume': [1000] * 5
        })
        
        result = generate_signals(df, sensitivity=3)
        
        # Find if we have short then long
        short_found = False
        for i in range(len(result)):
            if result['can_short'].iloc[i]:
                short_found = True
            if short_found and result['can_long'].iloc[i]:
                # On long signal, short trend should be False
                assert not result['is_short_trend'].iloc[i], \
                    "Short trend should end when long signal fires"
                break


# =============================================================================
# SIGNAL ANALYSIS TESTS
# =============================================================================

class TestSignalSummary:
    """Test signal summary function"""
    
    def test_signal_summary_structure(self, large_df):
        """Test get_signal_summary returns correct structure"""
        result = generate_signals(large_df, sensitivity=21)
        summary = get_signal_summary(result)
        
        expected_keys = [
            'total_rows', 'long_signals', 'short_signals', 'total_signals',
            'signal_frequency', 'long_ratio', 'short_ratio',
            'time_in_long_pct', 'time_in_short_pct', 'time_no_trend_pct'
        ]
        
        for key in expected_keys:
            assert key in summary, f"Missing key: {key}"
    
    def test_signal_summary_counts(self, bullish_trend_df):
        """Test signal counts are correct"""
        result = generate_signals(bullish_trend_df, sensitivity=3)
        summary = get_signal_summary(result)
        
        # Manual count
        actual_longs = result['can_long'].sum()
        actual_shorts = result['can_short'].sum()
        
        assert summary['long_signals'] == actual_longs
        assert summary['short_signals'] == actual_shorts
        assert summary['total_signals'] == actual_longs + actual_shorts
    
    def test_signal_summary_without_signals(self, simple_df):
        """Test summary returns error for DataFrame without signal columns"""
        # Just calculate, don't generate signals
        result = calculate_dominant(simple_df, sensitivity=3)
        summary = get_signal_summary(result)
        
        assert 'error' in summary


class TestLatestSignal:
    """Test latest signal function"""
    
    def test_latest_signal_found(self, bullish_trend_df):
        """Test get_latest_signal returns correct signal"""
        result = generate_signals(bullish_trend_df, sensitivity=3)
        latest = get_latest_signal(result)
        
        # Should have signal info
        assert 'signal' in latest
        assert latest['signal'] in ['LONG', 'SHORT', 'NONE']
    
    def test_latest_signal_with_price(self, bullish_trend_df):
        """Test latest signal includes entry price"""
        result = generate_signals(bullish_trend_df, sensitivity=3)
        latest = get_latest_signal(result)
        
        if latest['signal'] != 'NONE':
            assert 'entry_price' in latest
            assert latest['entry_price'] is not None
    
    def test_latest_signal_empty_df(self):
        """Test latest signal with empty DataFrame"""
        latest = get_latest_signal(pd.DataFrame())
        
        assert latest['signal'] == 'NONE'
        assert 'error' in latest


class TestExtractSignalEntries:
    """Test signal entry extraction"""
    
    def test_extract_only_signals(self, large_df):
        """Test extract_signal_entries returns only signal rows"""
        result = generate_signals(large_df, sensitivity=21)
        entries = extract_signal_entries(result)
        
        # All rows should have signal
        assert (entries['signal'] != SIGNAL_NONE).all()
    
    def test_extract_with_numbering(self, large_df):
        """Test extracted entries have signal numbers"""
        result = generate_signals(large_df, sensitivity=21)
        entries = extract_signal_entries(result)
        
        if len(entries) > 0:
            assert 'signal_num' in entries.columns
            assert entries['signal_num'].iloc[0] == 1
            assert entries['signal_num'].iloc[-1] == len(entries)
    
    def test_extract_raises_without_signals(self, simple_df):
        """Test extract raises error without signal column"""
        result = calculate_dominant(simple_df, sensitivity=3)
        
        with pytest.raises(ValueError, match="No signal column"):
            extract_signal_entries(result)


# =============================================================================
# SENSITIVITY RANGE TESTS
# =============================================================================

class TestSensitivityRange:
    """Test different sensitivity values"""
    
    def test_minimum_sensitivity(self, large_df):
        """Test with minimum sensitivity value"""
        result = calculate_dominant(large_df, sensitivity=SENSITIVITY_MIN)
        assert result is not None
        assert len(result) == len(large_df)
    
    def test_maximum_sensitivity(self, large_df):
        """Test with maximum sensitivity value"""
        result = calculate_dominant(large_df, sensitivity=SENSITIVITY_MAX)
        assert result is not None
        assert len(result) == len(large_df)
    
    def test_default_sensitivity(self, large_df):
        """Test with default sensitivity value"""
        result = calculate_dominant(large_df, sensitivity=SENSITIVITY_DEFAULT)
        assert result is not None
        assert len(result) == len(large_df)
    
    def test_sensitivity_affects_smoothness(self, large_df):
        """Test that higher sensitivity produces smoother channels"""
        result_fast = calculate_dominant(large_df, sensitivity=12)
        result_slow = calculate_dominant(large_df, sensitivity=60)
        
        # Standard deviation of channel should be lower with higher sensitivity
        std_fast = result_fast['high_channel'].std()
        std_slow = result_slow['high_channel'].std()
        
        # Slow should be smoother (lower std)
        assert std_slow < std_fast


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestHelperFunctions:
    """Test helper functions"""
    
    def test_get_current_levels(self, constant_range_df):
        """Test get_current_levels returns correct values"""
        result = calculate_dominant(constant_range_df, sensitivity=3)
        levels = get_current_levels(result)
        
        assert levels is not None
        assert levels['high_channel'] == 200
        assert levels['low_channel'] == 100
        assert levels['mid_channel'] == 150
        assert abs(levels['fib_500'] - 150) < 0.01
    
    def test_get_current_levels_with_signals(self, bullish_trend_df):
        """Test get_current_levels includes signal info"""
        result = generate_signals(bullish_trend_df, sensitivity=3)
        levels = get_current_levels(result)
        
        # Should have signal-related keys
        assert 'signal' in levels
        assert 'can_long' in levels
        assert 'can_short' in levels
        assert 'is_long_trend' in levels
        assert 'is_short_trend' in levels
    
    def test_get_current_levels_empty_df(self):
        """Test get_current_levels with empty DataFrame"""
        empty_df = pd.DataFrame()
        levels = get_current_levels(empty_df)
        assert levels == {}
    
    def test_get_indicator_info(self):
        """Test get_indicator_info returns valid metadata"""
        info = get_indicator_info()
        
        assert info['name'] == 'Dominant'
        assert info['version'] == '4.0.1'
        assert 'parameters' in info
        assert 'sensitivity' in info['parameters']
        assert 'require_confirmation' in info['parameters']
        assert 'signals' in info['outputs']
        assert info['parameters']['sensitivity']['min'] == SENSITIVITY_MIN
        assert info['parameters']['sensitivity']['max'] == SENSITIVITY_MAX
    
    def test_calculate_with_multiple_sensitivities(self, simple_df):
        """Test calculation with multiple sensitivity values"""
        results = calculate_with_multiple_sensitivities(simple_df, [12, 21, 34])
        
        assert len(results) == 3
        assert 12 in results
        assert 21 in results
        assert 34 in results


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_missing_columns_raises_error(self):
        """Test that missing columns raise ValueError"""
        df = pd.DataFrame({'open': [100], 'high': [110]})  # Missing low, close, volume
        
        with pytest.raises(ValueError, match="Missing required columns"):
            calculate_dominant(df)
    
    def test_empty_dataframe_raises_error(self):
        """Test that empty DataFrame raises ValueError"""
        df = pd.DataFrame(columns=['open', 'high', 'low', 'close', 'volume'])
        
        with pytest.raises(ValueError, match="DataFrame is empty"):
            calculate_dominant(df)
    
    def test_single_row_dataframe(self):
        """Test with single row DataFrame"""
        df = pd.DataFrame({
            'open': [100],
            'high': [110],
            'low': [90],
            'close': [105],
            'volume': [1000]
        })
        
        result = calculate_dominant(df, sensitivity=21)
        assert len(result) == 1
        # With single row, high_channel should equal high
        assert result['high_channel'].iloc[0] == 110
        assert result['low_channel'].iloc[0] == 90
    
    def test_zero_range_handling(self):
        """Test handling of zero channel range"""
        df = pd.DataFrame({
            'open': [100] * 5,
            'high': [100] * 5,  # Same as low = zero range
            'low': [100] * 5,
            'close': [100] * 5,
            'volume': [1000] * 5
        })
        
        result = calculate_dominant(df, sensitivity=3)
        
        # Range should be 0
        assert result['channel_range'].iloc[-1] == 0
        
        # price_position should default to 0.5 when range is 0
        assert result['price_position'].iloc[-1] == 0.5
    
    def test_nan_values_in_input(self):
        """Test handling of NaN values in input"""
        df = pd.DataFrame({
            'open': [100, np.nan, 102, 103, 104],
            'high': [102, 103, np.nan, 105, 106],
            'low': [99, 100, 101, np.nan, 103],
            'close': [101, 102, 103, 104, np.nan],
            'volume': [1000] * 5
        })
        
        # Should not raise, but NaN will propagate
        result = calculate_dominant(df, sensitivity=3)
        assert result is not None


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================

class TestPerformance:
    """Test performance with large datasets"""
    
    def test_large_dataset_performance(self, large_df):
        """Test that calculation completes in reasonable time"""
        import time
        
        start = time.time()
        result = calculate_dominant(large_df, sensitivity=21)
        elapsed = time.time() - start
        
        # Should complete in less than 1 second for 1000 rows
        assert elapsed < 1.0
        assert len(result) == len(large_df)
    
    def test_signal_generation_performance(self, large_df):
        """Test signal generation performance"""
        import time
        
        start = time.time()
        result = generate_signals(large_df, sensitivity=21)
        elapsed = time.time() - start
        
        # Should complete in less than 2 seconds for 1000 rows
        assert elapsed < 2.0
        assert len(result) == len(large_df)
    
    def test_original_df_unchanged(self, simple_df):
        """Test that original DataFrame is not modified"""
        original_columns = simple_df.columns.tolist()
        original_values = simple_df.values.copy()
        
        _ = calculate_dominant(simple_df, sensitivity=3)
        
        assert simple_df.columns.tolist() == original_columns
        assert np.array_equal(simple_df.values, original_values)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
