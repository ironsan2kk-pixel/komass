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

Signal Generation (Chat #21):
- can_long: Price above mid_channel, above fib_236, bullish candle
- can_short: Price below mid_channel, below fib_236_high, bearish candle
- Trend tracking: is_long_trend, is_short_trend
- Close position on reverse signal

Author: KOMAS Team
Version: 4.0.1
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Any, List

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

# Signal constants
SIGNAL_LONG = 1
SIGNAL_SHORT = -1
SIGNAL_NONE = 0


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
# SIGNAL GENERATION (Chat #21)
# =============================================================================

def generate_signals(
    df: pd.DataFrame,
    sensitivity: int = SENSITIVITY_DEFAULT,
    require_confirmation: bool = True
) -> pd.DataFrame:
    """
    Generate trading signals based on Dominant indicator
    
    This function calculates the indicator levels and then generates
    trading signals based on price position relative to channel and
    Fibonacci levels.
    
    Args:
        df: DataFrame with OHLCV data
        sensitivity: Channel period (12-60, default 21)
        require_confirmation: If True, require bullish/bearish candle confirmation
            For long: close > open (bullish candle)
            For short: close < open (bearish candle)
    
    Returns:
        DataFrame with all indicator columns plus signal columns:
        - can_long: Boolean, True when long entry conditions are met
        - can_short: Boolean, True when short entry conditions are met
        - signal: Integer signal (1=Long, -1=Short, 0=None)
        - is_long_trend: Boolean, True when in long trend
        - is_short_trend: Boolean, True when in short trend
        - entry_price: Float, entry price when signal fires
        - signal_type: String description of signal
    
    Signal Logic:
        Long Entry (can_long = True):
            - close >= mid_channel (price in upper half)
            - close >= fib_236 (above first support)
            - close > open (bullish candle, if confirmation required)
        
        Short Entry (can_short = True):
            - close <= mid_channel (price in lower half)
            - close <= fib_236_high (below first resistance from high)
            - close < open (bearish candle, if confirmation required)
    
    Trend Tracking:
        - is_long_trend becomes True when can_long fires
        - is_short_trend becomes True when can_short fires
        - Trend flips on reverse signal (close on reverse)
    
    Example:
        >>> df = load_ohlcv_data('BTCUSDT', '1h')
        >>> result = generate_signals(df, sensitivity=21)
        >>> long_signals = result[result['can_long']]
    """
    # First, calculate all indicator levels
    result = calculate_dominant(df, sensitivity)
    
    # ==========================================================================
    # BASIC SIGNAL CONDITIONS
    # ==========================================================================
    
    close = result['close']
    open_price = result['open']
    mid_channel = result['mid_channel']
    fib_236 = result['fib_236']
    fib_236_high = result['fib_236_high']
    
    # Candle direction
    is_bullish = close > open_price
    is_bearish = close < open_price
    
    # ==========================================================================
    # LONG SIGNAL CONDITIONS
    # ==========================================================================
    
    # Base conditions for long
    long_price_condition = (
        (close >= mid_channel) &  # Price in upper half of channel
        (close >= fib_236)        # Above first Fibonacci support
    )
    
    # With or without confirmation
    if require_confirmation:
        result['can_long'] = long_price_condition & is_bullish
    else:
        result['can_long'] = long_price_condition
    
    # ==========================================================================
    # SHORT SIGNAL CONDITIONS
    # ==========================================================================
    
    # Base conditions for short
    short_price_condition = (
        (close <= mid_channel) &     # Price in lower half of channel
        (close <= fib_236_high)      # Below first Fibonacci resistance from high
    )
    
    # With or without confirmation
    if require_confirmation:
        result['can_short'] = short_price_condition & is_bearish
    else:
        result['can_short'] = short_price_condition
    
    # ==========================================================================
    # SIGNAL COLUMN
    # ==========================================================================
    
    # Create integer signal column
    # 1 = Long, -1 = Short, 0 = None
    result['signal'] = np.where(
        result['can_long'], SIGNAL_LONG,
        np.where(result['can_short'], SIGNAL_SHORT, SIGNAL_NONE)
    )
    
    # ==========================================================================
    # TREND TRACKING (with close on reverse)
    # ==========================================================================
    
    result = _track_trends(result)
    
    # ==========================================================================
    # ENTRY PRICE
    # ==========================================================================
    
    # Entry price is close price when signal fires
    result['entry_price'] = np.where(
        result['signal'] != SIGNAL_NONE,
        result['close'],
        np.nan
    )
    
    # ==========================================================================
    # SIGNAL TYPE (human-readable)
    # ==========================================================================
    
    result['signal_type'] = np.where(
        result['can_long'], 'LONG',
        np.where(result['can_short'], 'SHORT', 'NONE')
    )
    
    return result


def _track_trends(df: pd.DataFrame) -> pd.DataFrame:
    """
    Track trend state with close on reverse logic
    
    When a long signal fires:
        - is_long_trend becomes True
        - is_short_trend becomes False (close short position)
    
    When a short signal fires:
        - is_short_trend becomes True
        - is_long_trend becomes False (close long position)
    
    Trend persists until reverse signal.
    
    Args:
        df: DataFrame with 'can_long' and 'can_short' columns
    
    Returns:
        DataFrame with 'is_long_trend' and 'is_short_trend' columns added
    """
    n = len(df)
    is_long_trend = np.zeros(n, dtype=bool)
    is_short_trend = np.zeros(n, dtype=bool)
    
    # Get signal columns as arrays for faster iteration
    can_long = df['can_long'].values
    can_short = df['can_short'].values
    
    # Track current state
    current_long = False
    current_short = False
    
    for i in range(n):
        if can_long[i]:
            # Long signal: start long trend, close short
            current_long = True
            current_short = False
        elif can_short[i]:
            # Short signal: start short trend, close long
            current_short = True
            current_long = False
        
        # Record state
        is_long_trend[i] = current_long
        is_short_trend[i] = current_short
    
    df['is_long_trend'] = is_long_trend
    df['is_short_trend'] = is_short_trend
    
    return df


# =============================================================================
# SIGNAL ANALYSIS FUNCTIONS
# =============================================================================

def get_signal_summary(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get summary statistics about signals in the DataFrame
    
    Args:
        df: DataFrame with signal columns from generate_signals()
    
    Returns:
        Dictionary with signal statistics
    """
    if 'can_long' not in df.columns or 'can_short' not in df.columns:
        return {'error': 'No signal columns found. Run generate_signals() first.'}
    
    total_rows = len(df)
    long_signals = df['can_long'].sum()
    short_signals = df['can_short'].sum()
    total_signals = long_signals + short_signals
    
    # Calculate time in trend
    time_in_long = df['is_long_trend'].sum() if 'is_long_trend' in df.columns else 0
    time_in_short = df['is_short_trend'].sum() if 'is_short_trend' in df.columns else 0
    time_no_trend = total_rows - time_in_long - time_in_short
    
    return {
        'total_rows': total_rows,
        'long_signals': int(long_signals),
        'short_signals': int(short_signals),
        'total_signals': int(total_signals),
        'signal_frequency': round(total_signals / total_rows * 100, 2) if total_rows > 0 else 0,
        'long_ratio': round(long_signals / total_signals * 100, 2) if total_signals > 0 else 0,
        'short_ratio': round(short_signals / total_signals * 100, 2) if total_signals > 0 else 0,
        'time_in_long_pct': round(time_in_long / total_rows * 100, 2) if total_rows > 0 else 0,
        'time_in_short_pct': round(time_in_short / total_rows * 100, 2) if total_rows > 0 else 0,
        'time_no_trend_pct': round(time_no_trend / total_rows * 100, 2) if total_rows > 0 else 0,
    }


def get_latest_signal(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get the most recent signal from the DataFrame
    
    Args:
        df: DataFrame with signal columns
    
    Returns:
        Dictionary with latest signal information
    """
    if df is None or len(df) == 0:
        return {'signal': 'NONE', 'error': 'Empty DataFrame'}
    
    if 'signal' not in df.columns:
        return {'signal': 'NONE', 'error': 'No signal column. Run generate_signals() first.'}
    
    # Find last row with a signal
    signals_df = df[df['signal'] != SIGNAL_NONE]
    
    if len(signals_df) == 0:
        return {
            'signal': 'NONE',
            'message': 'No signals in data'
        }
    
    last_signal_row = signals_df.iloc[-1]
    
    return {
        'signal': 'LONG' if last_signal_row['signal'] == SIGNAL_LONG else 'SHORT',
        'entry_price': float(last_signal_row['close']),
        'timestamp': last_signal_row.name if isinstance(last_signal_row.name, pd.Timestamp) else None,
        'mid_channel': float(last_signal_row['mid_channel']),
        'fib_236': float(last_signal_row['fib_236']),
        'fib_236_high': float(last_signal_row['fib_236_high']),
        'is_long_trend': bool(last_signal_row.get('is_long_trend', False)),
        'is_short_trend': bool(last_signal_row.get('is_short_trend', False)),
    }


def extract_signal_entries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract only the rows where new signals occur
    
    This is useful for analyzing entry points and creating trade lists.
    
    Args:
        df: DataFrame with signal columns
    
    Returns:
        DataFrame with only signal entry rows
    """
    if 'signal' not in df.columns:
        raise ValueError("No signal column. Run generate_signals() first.")
    
    # Filter to only rows with signals
    entries = df[df['signal'] != SIGNAL_NONE].copy()
    
    # Add signal number for tracking
    entries['signal_num'] = range(1, len(entries) + 1)
    
    return entries


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
    
    # Add signal info if available
    if 'signal' in df.columns:
        levels['signal'] = int(last_row.get('signal', 0))
        levels['can_long'] = bool(last_row.get('can_long', False))
        levels['can_short'] = bool(last_row.get('can_short', False))
        levels['is_long_trend'] = bool(last_row.get('is_long_trend', False))
        levels['is_short_trend'] = bool(last_row.get('is_short_trend', False))
    
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
        'version': '4.0.1',
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
            },
            'require_confirmation': {
                'type': 'bool',
                'default': True,
                'description': 'Require candle confirmation (bullish for long, bearish for short)'
            }
        },
        'outputs': {
            'channel': ['high_channel', 'low_channel', 'mid_channel', 'channel_range'],
            'fibonacci_long': ['fib_236', 'fib_382', 'fib_500', 'fib_618'],
            'fibonacci_short': ['fib_236_high', 'fib_382_high', 'fib_500_high', 'fib_618_high'],
            'derived': ['channel_width_pct', 'price_position'],
            'signals': ['can_long', 'can_short', 'signal', 'is_long_trend', 'is_short_trend', 'entry_price', 'signal_type']
        },
        'signal_logic': {
            'long': 'close >= mid_channel AND close >= fib_236 AND close > open (bullish)',
            'short': 'close <= mid_channel AND close <= fib_236_high AND close < open (bearish)'
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
    
    plot_data = {
        'timestamps': df.index.tolist() if isinstance(df.index, pd.DatetimeIndex) else list(range(len(df))),
        'high_channel': df['high_channel'].tolist(),
        'low_channel': df['low_channel'].tolist(),
        'mid_channel': df['mid_channel'].tolist(),
        'fib_236': df['fib_236'].tolist(),
        'fib_382': df['fib_382'].tolist(),
        'fib_500': df['fib_500'].tolist(),
        'fib_618': df['fib_618'].tolist(),
    }
    
    # Add signal markers if available
    if 'can_long' in df.columns:
        plot_data['long_signals'] = df[df['can_long']].index.tolist()
        plot_data['long_prices'] = df.loc[df['can_long'], 'close'].tolist()
    
    if 'can_short' in df.columns:
        plot_data['short_signals'] = df[df['can_short']].index.tolist()
        plot_data['short_prices'] = df.loc[df['can_short'], 'close'].tolist()
    
    return plot_data


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == '__main__':
    # Quick test
    print("Testing Dominant Indicator with Signals...")
    
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
    
    # Calculate with signals
    result = generate_signals(df, sensitivity=21)
    
    # Print results
    print(f"\nDataFrame shape: {result.shape}")
    print(f"\nSignal columns: {[c for c in result.columns if 'signal' in c.lower() or 'long' in c.lower() or 'short' in c.lower()]}")
    
    # Signal summary
    summary = get_signal_summary(result)
    print(f"\nSignal Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    # Latest signal
    latest = get_latest_signal(result)
    print(f"\nLatest Signal: {latest.get('signal')}")
    if latest.get('entry_price'):
        print(f"  Entry Price: {latest['entry_price']:.2f}")
    
    print("\n✅ Dominant indicator with signals test passed!")
