"""
Dominant Indicator - Channel + Fibonacci Levels
KOMAS v4.0

The Dominant indicator uses a price channel based on rolling high/low
with Fibonacci retracement levels for entry signals and take profits.

Channel Calculation:
- high_channel: Rolling maximum of high prices over sensitivity period
- low_channel: Rolling minimum of low prices over sensitivity period
- mid_channel: Midpoint between high and low channel

Fibonacci Levels:
- Calculated from both low_channel (for longs) and high_channel (for shorts)
- Levels: 0.236, 0.382, 0.500, 0.618

Author: KOMAS Team
Version: 4.0.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Any

# =============================================================================
# CONSTANTS
# =============================================================================

SENSITIVITY_MIN = 12
SENSITIVITY_MAX = 60
SENSITIVITY_DEFAULT = 21

# Fibonacci ratios
FIB_LEVELS = {
    'fib_236': 0.236,
    'fib_382': 0.382,
    'fib_500': 0.500,
    'fib_618': 0.618,
}


# =============================================================================
# VALIDATION
# =============================================================================

def validate_sensitivity(sensitivity: int) -> int:
    """
    Validate and clamp sensitivity to valid range [12, 60]
    
    Args:
        sensitivity: Input sensitivity value
        
    Returns:
        Clamped sensitivity value within valid range
    """
    if not isinstance(sensitivity, (int, float)):
        return SENSITIVITY_DEFAULT
    return max(SENSITIVITY_MIN, min(SENSITIVITY_MAX, int(sensitivity)))


def validate_dataframe(df: pd.DataFrame) -> bool:
    """
    Validate that DataFrame has required OHLCV columns
    
    Args:
        df: Input DataFrame
        
    Returns:
        True if valid, raises ValueError if not
    """
    required_columns = ['open', 'high', 'low', 'close', 'volume']
    missing = [col for col in required_columns if col not in df.columns]
    
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    if len(df) == 0:
        raise ValueError("DataFrame is empty")
    
    return True


# =============================================================================
# MAIN CALCULATION
# =============================================================================

def calculate_dominant(
    df: pd.DataFrame,
    sensitivity: int = SENSITIVITY_DEFAULT
) -> pd.DataFrame:
    """
    Calculate Dominant indicator levels
    
    This function calculates channel boundaries and Fibonacci levels
    for the Dominant trading strategy.
    
    Args:
        df: DataFrame with OHLCV data
            Required columns: open, high, low, close, volume
        sensitivity: Channel period (12-60, default 21)
            - 12-20: Fast channel, more signals, more noise
            - 21-35: Balanced (recommended)
            - 36-60: Slow channel, fewer signals, more reliable
    
    Returns:
        DataFrame with original data plus added columns:
        - high_channel: Rolling max of high prices
        - low_channel: Rolling min of low prices
        - mid_channel: (high_channel + low_channel) / 2
        - channel_range: high_channel - low_channel
        - fib_236, fib_382, fib_500, fib_618: Fibonacci levels from low
        - fib_236_high, fib_382_high, fib_500_high, fib_618_high: From high
    
    Example:
        >>> df = pd.DataFrame({
        ...     'open': [100, 101, 102],
        ...     'high': [102, 103, 104],
        ...     'low': [99, 100, 101],
        ...     'close': [101, 102, 103],
        ...     'volume': [1000, 1000, 1000]
        ... })
        >>> result = calculate_dominant(df, sensitivity=21)
    """
    # Validate inputs
    validate_dataframe(df)
    sensitivity = validate_sensitivity(sensitivity)
    
    # Create copy to avoid modifying original
    result = df.copy()
    
    # ==========================================================================
    # CHANNEL CALCULATION
    # ==========================================================================
    
    # Rolling window for channel
    result['high_channel'] = df['high'].rolling(
        window=sensitivity, 
        min_periods=1
    ).max()
    
    result['low_channel'] = df['low'].rolling(
        window=sensitivity, 
        min_periods=1
    ).min()
    
    # Channel midpoint and range
    result['mid_channel'] = (result['high_channel'] + result['low_channel']) / 2
    result['channel_range'] = result['high_channel'] - result['low_channel']
    
    # ==========================================================================
    # FIBONACCI LEVELS (FROM LOW CHANNEL - FOR LONG ENTRIES)
    # ==========================================================================
    
    # Levels measured from low_channel going up
    # fib_236 = low + range * 0.236 (first resistance)
    # fib_382 = low + range * 0.382 (second resistance)
    # fib_500 = low + range * 0.500 (mid - key level)
    # fib_618 = low + range * 0.618 (golden ratio)
    
    for name, ratio in FIB_LEVELS.items():
        result[name] = result['low_channel'] + result['channel_range'] * ratio
    
    # ==========================================================================
    # FIBONACCI LEVELS (FROM HIGH CHANNEL - FOR SHORT ENTRIES)
    # ==========================================================================
    
    # Levels measured from high_channel going down
    # fib_236_high = high - range * 0.236 (first support)
    # fib_382_high = high - range * 0.382 (second support)
    # fib_500_high = high - range * 0.500 (mid - same as mid_channel)
    # fib_618_high = high - range * 0.618 (golden ratio)
    
    for name, ratio in FIB_LEVELS.items():
        result[f'{name}_high'] = result['high_channel'] - result['channel_range'] * ratio
    
    # ==========================================================================
    # ADDITIONAL DERIVED COLUMNS
    # ==========================================================================
    
    # Channel width as percentage of mid price (useful for volatility filtering)
    result['channel_width_pct'] = (result['channel_range'] / result['mid_channel']) * 100
    
    # Price position within channel (0 = at low, 1 = at high)
    result['price_position'] = np.where(
        result['channel_range'] > 0,
        (df['close'] - result['low_channel']) / result['channel_range'],
        0.5  # Default to middle if no range
    )
    
    return result


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_current_levels(df: pd.DataFrame) -> Dict[str, float]:
    """
    Get current (last) indicator levels for display
    
    Args:
        df: DataFrame with calculated Dominant indicator columns
        
    Returns:
        Dictionary with current values of all indicator levels
        
    Example:
        >>> result = calculate_dominant(df, sensitivity=21)
        >>> levels = get_current_levels(result)
        >>> print(levels['high_channel'])
    """
    if df is None or len(df) == 0:
        return {}
    
    last_row = df.iloc[-1]
    
    levels = {
        'high_channel': _safe_float(last_row.get('high_channel')),
        'low_channel': _safe_float(last_row.get('low_channel')),
        'mid_channel': _safe_float(last_row.get('mid_channel')),
        'channel_range': _safe_float(last_row.get('channel_range')),
        'channel_width_pct': _safe_float(last_row.get('channel_width_pct')),
        'price_position': _safe_float(last_row.get('price_position')),
    }
    
    # Add Fibonacci levels
    for name in FIB_LEVELS.keys():
        levels[name] = _safe_float(last_row.get(name))
        levels[f'{name}_high'] = _safe_float(last_row.get(f'{name}_high'))
    
    # Add current price for reference
    levels['close'] = _safe_float(last_row.get('close'))
    
    return levels


def _safe_float(value: Any) -> Optional[float]:
    """Convert value to float safely, return None if not possible"""
    if value is None:
        return None
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def get_indicator_info() -> Dict[str, Any]:
    """
    Get indicator metadata and parameter descriptions
    
    Returns:
        Dictionary with indicator information for UI/documentation
    """
    return {
        'name': 'Dominant',
        'version': '4.0.0',
        'description': 'Channel + Fibonacci levels indicator for trend trading',
        'parameters': {
            'sensitivity': {
                'type': 'int',
                'min': SENSITIVITY_MIN,
                'max': SENSITIVITY_MAX,
                'default': SENSITIVITY_DEFAULT,
                'description': 'Channel period (rolling window for high/low)',
                'categories': {
                    'fast': (12, 20),
                    'balanced': (21, 35),
                    'slow': (36, 60),
                }
            }
        },
        'outputs': {
            'channel': ['high_channel', 'low_channel', 'mid_channel', 'channel_range'],
            'fibonacci_long': ['fib_236', 'fib_382', 'fib_500', 'fib_618'],
            'fibonacci_short': ['fib_236_high', 'fib_382_high', 'fib_500_high', 'fib_618_high'],
            'derived': ['channel_width_pct', 'price_position']
        }
    }


def calculate_with_multiple_sensitivities(
    df: pd.DataFrame,
    sensitivities: list = None
) -> Dict[int, pd.DataFrame]:
    """
    Calculate Dominant indicator for multiple sensitivity values
    Useful for optimization and comparison
    
    Args:
        df: DataFrame with OHLCV data
        sensitivities: List of sensitivity values to test
            Default: [12, 21, 34, 55] (Fibonacci-like sequence)
    
    Returns:
        Dictionary mapping sensitivity -> calculated DataFrame
    """
    if sensitivities is None:
        sensitivities = [12, 21, 34, 55]
    
    results = {}
    for sens in sensitivities:
        sens = validate_sensitivity(sens)
        results[sens] = calculate_dominant(df, sensitivity=sens)
    
    return results


# =============================================================================
# VISUALIZATION HELPERS
# =============================================================================

def get_plot_levels(df: pd.DataFrame, last_n: int = None) -> Dict[str, list]:
    """
    Get indicator levels formatted for plotting
    
    Args:
        df: DataFrame with calculated Dominant indicator columns
        last_n: Only return last N values (None = all)
    
    Returns:
        Dictionary with arrays ready for charting libraries
    """
    if df is None or len(df) == 0:
        return {}
    
    if last_n is not None:
        df = df.tail(last_n)
    
    return {
        'timestamps': df.index.tolist() if isinstance(df.index, pd.DatetimeIndex) else list(range(len(df))),
        'high_channel': df['high_channel'].tolist(),
        'low_channel': df['low_channel'].tolist(),
        'mid_channel': df['mid_channel'].tolist(),
        'fib_236': df['fib_236'].tolist(),
        'fib_382': df['fib_382'].tolist(),
        'fib_500': df['fib_500'].tolist(),
        'fib_618': df['fib_618'].tolist(),
    }


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == '__main__':
    # Quick test
    print("Testing Dominant Indicator...")
    
    # Create sample data
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='1h')
    prices = 100 + np.cumsum(np.random.randn(100) * 0.5)
    
    df = pd.DataFrame({
        'open': prices,
        'high': prices + np.abs(np.random.randn(100) * 0.3),
        'low': prices - np.abs(np.random.randn(100) * 0.3),
        'close': prices + np.random.randn(100) * 0.2,
        'volume': np.random.randint(1000, 10000, 100)
    }, index=dates)
    
    # Calculate
    result = calculate_dominant(df, sensitivity=21)
    
    # Print results
    print(f"\nDataFrame shape: {result.shape}")
    print(f"\nNew columns added: {[c for c in result.columns if c not in df.columns]}")
    print(f"\nCurrent levels:")
    
    levels = get_current_levels(result)
    for key, value in levels.items():
        if value is not None:
            print(f"  {key}: {value:.4f}")
    
    print("\n✅ Dominant indicator test passed!")
