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
    get_current_levels,
    validate_sensitivity,
    get_indicator_info,
    calculate_with_multiple_sensitivities,
    SENSITIVITY_MIN,
    SENSITIVITY_MAX,
    SENSITIVITY_DEFAULT,
    FIB_LEVELS,
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
    
    def test_get_current_levels_empty_df(self):
        """Test get_current_levels with empty DataFrame"""
        empty_df = pd.DataFrame()
        levels = get_current_levels(empty_df)
        assert levels == {}
    
    def test_get_indicator_info(self):
        """Test get_indicator_info returns valid metadata"""
        info = get_indicator_info()
        
        assert info['name'] == 'Dominant'
        assert 'parameters' in info
        assert 'sensitivity' in info['parameters']
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
