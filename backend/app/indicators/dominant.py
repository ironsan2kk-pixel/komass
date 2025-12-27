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

Filter Types (Chat #22):
- Filter 0: None (no filtering)
- Filter 1: ATR Condition (volume spike)
- Filter 2: RSI Condition (overbought/oversold)
- Filter 3: ATR + RSI Combined
- Filter 4: Volatility Condition

Author: KOMAS Team
Version: 4.0.2
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
# FILTER CONSTANTS (Chat #22)
# =============================================================================

FILTER_NONE = 0
FILTER_ATR = 1
FILTER_RSI = 2
FILTER_COMBINED = 3
FILTER_VOLATILITY = 4

FILTER_NAMES = {
    FILTER_NONE: 'None',
    FILTER_ATR: 'ATR Condition',
    FILTER_RSI: 'RSI Condition',
    FILTER_COMBINED: 'ATR + RSI Combined',
    FILTER_VOLATILITY: 'Volatility Condition',
}

# Default filter parameters
FILTER_DEFAULTS = {
    'atr_period': 14,
    'atr_multiplier': 1.5,
    'rsi_period': 14,
    'rsi_overbought': 70,
    'rsi_oversold': 30,
    'volatility_period': 20,
    'volatility_max_mult': 2.0,
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


def validate_filter_type(filter_type: int) -> int:
    """
    Validate filter type is in valid range [0, 4]
    
    Args:
        filter_type: Input filter type
        
    Returns:
        Valid filter type (clamped to range)
    """
    if not isinstance(filter_type, (int, float)):
        return FILTER_NONE
    return max(FILTER_NONE, min(FILTER_VOLATILITY, int(filter_type)))


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
# FILTER FUNCTIONS (Chat #22)
# =============================================================================

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate RSI (Relative Strength Index) indicator
    
    RSI = 100 - (100 / (1 + RS))
    RS = Average Gain / Average Loss
    
    Args:
        series: Price series (typically close prices)
        period: RSI period (default 14)
        
    Returns:
        Series with RSI values (0-100)
    """
    if period < 1:
        period = 14
        
    # Calculate price changes
    delta = series.diff()
    
    # Separate gains and losses
    gains = delta.where(delta > 0, 0.0)
    losses = (-delta).where(delta < 0, 0.0)
    
    # Calculate exponential moving averages
    avg_gain = gains.ewm(span=period, adjust=False).mean()
    avg_loss = losses.ewm(span=period, adjust=False).mean()
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # Handle division by zero (when avg_loss is 0)
    rsi = rsi.fillna(50)  # Default to neutral if undefined
    
    return rsi


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate ATR (Average True Range) indicator
    
    True Range = max(high-low, abs(high-prev_close), abs(low-prev_close))
    ATR = EMA of True Range
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ATR period (default 14)
        
    Returns:
        Series with ATR values
    """
    if period < 1:
        period = 14
        
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)
    
    # True Range calculation
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # ATR is EMA of True Range
    atr = true_range.ewm(span=period, adjust=False).mean()
    
    return atr


def apply_filter(
    df: pd.DataFrame,
    filter_type: int = FILTER_NONE,
    atr_period: int = FILTER_DEFAULTS['atr_period'],
    atr_multiplier: float = FILTER_DEFAULTS['atr_multiplier'],
    rsi_period: int = FILTER_DEFAULTS['rsi_period'],
    rsi_overbought: int = FILTER_DEFAULTS['rsi_overbought'],
    rsi_oversold: int = FILTER_DEFAULTS['rsi_oversold'],
    volatility_period: int = FILTER_DEFAULTS['volatility_period'],
    volatility_max_mult: float = FILTER_DEFAULTS['volatility_max_mult']
) -> pd.DataFrame:
    """
    Apply filter to signals based on filter type
    
    This function adds filter columns to the DataFrame that can be used
    to filter trading signals. Original signals are NOT modified.
    
    Args:
        df: DataFrame with signal columns from generate_signals()
            Required: 'can_long', 'can_short', 'close', 'high', 'low'
        filter_type: 0-4 (None, ATR, RSI, Combined, Volatility)
        atr_period: Period for ATR calculation (default 14)
        atr_multiplier: ATR threshold multiplier (default 1.5)
            Signal passes if current ATR > ATR_MA * multiplier
        rsi_period: Period for RSI calculation (default 14)
        rsi_overbought: RSI overbought level (default 70)
            Long blocked when RSI > overbought
        rsi_oversold: RSI oversold level (default 30)
            Short blocked when RSI < oversold
        volatility_period: Period for volatility calculation (default 20)
        volatility_max_mult: Max volatility multiplier (default 2.0)
            Signals blocked when volatility > MA * multiplier
    
    Returns:
        DataFrame with filter columns added:
        - filter_pass_long: bool - Whether long signal passes filter
        - filter_pass_short: bool - Whether short signal passes filter
        - filtered_can_long: bool - can_long AND filter_pass_long
        - filtered_can_short: bool - can_short AND filter_pass_short
        - filter_type: int - Applied filter type
        - Additional columns based on filter type (atr, rsi, etc.)
    
    Example:
        >>> df = generate_signals(df, sensitivity=21)
        >>> filtered = apply_filter(df, filter_type=2, rsi_overbought=70)
        >>> trades = filtered[filtered['filtered_can_long'] | filtered['filtered_can_short']]
    """
    # Validate inputs
    validate_dataframe(df)
    filter_type = validate_filter_type(filter_type)
    
    # Create copy to avoid modifying original
    result = df.copy()
    
    # Ensure signal columns exist (initialize if missing)
    if 'can_long' not in result.columns:
        result['can_long'] = False
    if 'can_short' not in result.columns:
        result['can_short'] = False
    
    # Store filter type
    result['filter_type_applied'] = filter_type
    
    # Initialize filter pass columns (default: all pass)
    result['filter_pass_long'] = True
    result['filter_pass_short'] = True
    
    # ==========================================================================
    # FILTER TYPE 0: None (no filtering)
    # ==========================================================================
    if filter_type == FILTER_NONE:
        # All signals pass through
        pass
    
    # ==========================================================================
    # FILTER TYPE 1: ATR Condition (Volume Spike / High Volatility Entry)
    # ==========================================================================
    elif filter_type == FILTER_ATR:
        # Calculate ATR
        result['filter_atr'] = calculate_atr(result, period=atr_period)
        result['filter_atr_ma'] = result['filter_atr'].rolling(
            window=atr_period, 
            min_periods=1
        ).mean()
        
        # Signal passes when ATR is above average * multiplier
        # This filters for high volatility moments (volume spike)
        atr_condition = result['filter_atr'] > result['filter_atr_ma'] * atr_multiplier
        
        result['filter_pass_long'] = atr_condition
        result['filter_pass_short'] = atr_condition
    
    # ==========================================================================
    # FILTER TYPE 2: RSI Condition (Overbought/Oversold)
    # ==========================================================================
    elif filter_type == FILTER_RSI:
        # Calculate RSI
        result['filter_rsi'] = calculate_rsi(result['close'], period=rsi_period)
        
        # Long blocked when overbought (RSI > threshold)
        # Short blocked when oversold (RSI < threshold)
        result['filter_pass_long'] = result['filter_rsi'] < rsi_overbought
        result['filter_pass_short'] = result['filter_rsi'] > rsi_oversold
    
    # ==========================================================================
    # FILTER TYPE 3: ATR + RSI Combined
    # ==========================================================================
    elif filter_type == FILTER_COMBINED:
        # Calculate both indicators
        result['filter_atr'] = calculate_atr(result, period=atr_period)
        result['filter_atr_ma'] = result['filter_atr'].rolling(
            window=atr_period, 
            min_periods=1
        ).mean()
        result['filter_rsi'] = calculate_rsi(result['close'], period=rsi_period)
        
        # ATR condition (same as filter type 1)
        atr_condition = result['filter_atr'] > result['filter_atr_ma'] * atr_multiplier
        
        # RSI conditions (same as filter type 2)
        rsi_long_ok = result['filter_rsi'] < rsi_overbought
        rsi_short_ok = result['filter_rsi'] > rsi_oversold
        
        # Both must pass
        result['filter_pass_long'] = atr_condition & rsi_long_ok
        result['filter_pass_short'] = atr_condition & rsi_short_ok
    
    # ==========================================================================
    # FILTER TYPE 4: Volatility Condition (Avoid Extreme Volatility)
    # ==========================================================================
    elif filter_type == FILTER_VOLATILITY:
        # Calculate price returns volatility
        result['filter_returns'] = result['close'].pct_change()
        result['filter_volatility'] = result['filter_returns'].rolling(
            window=volatility_period,
            min_periods=1
        ).std()
        result['filter_volatility_ma'] = result['filter_volatility'].rolling(
            window=volatility_period,
            min_periods=1
        ).mean()
        
        # Signal passes when volatility is NOT too extreme
        # Block signals during crazy market moves
        volatility_ok = result['filter_volatility'] < result['filter_volatility_ma'] * volatility_max_mult
        
        result['filter_pass_long'] = volatility_ok
        result['filter_pass_short'] = volatility_ok
    
    # ==========================================================================
    # CREATE FILTERED SIGNAL COLUMNS
    # ==========================================================================
    
    # Original signals combined with filter
    result['filtered_can_long'] = result['can_long'] & result['filter_pass_long']
    result['filtered_can_short'] = result['can_short'] & result['filter_pass_short']
    
    # Create filtered signal column
    result['filtered_signal'] = np.where(
        result['filtered_can_long'], SIGNAL_LONG,
        np.where(result['filtered_can_short'], SIGNAL_SHORT, SIGNAL_NONE)
    )
    
    return result


def get_filter_info(filter_type: int = None) -> Dict[str, Any]:
    """
    Get information about filter types
    
    Args:
        filter_type: Specific filter type to get info for (None = all)
        
    Returns:
        Dictionary with filter information
    """
    all_filters = {
        FILTER_NONE: {
            'name': 'None',
            'description': 'No filtering, all signals pass through',
            'parameters': [],
        },
        FILTER_ATR: {
            'name': 'ATR Condition',
            'description': 'Entry only when volatility is above average (volume spike)',
            'parameters': ['atr_period', 'atr_multiplier'],
            'logic': 'ATR > ATR_MA * multiplier',
        },
        FILTER_RSI: {
            'name': 'RSI Condition',
            'description': 'Avoid overbought/oversold zones',
            'parameters': ['rsi_period', 'rsi_overbought', 'rsi_oversold'],
            'logic': 'Long: RSI < overbought, Short: RSI > oversold',
        },
        FILTER_COMBINED: {
            'name': 'ATR + RSI Combined',
            'description': 'Both ATR and RSI conditions must be met',
            'parameters': ['atr_period', 'atr_multiplier', 'rsi_period', 'rsi_overbought', 'rsi_oversold'],
            'logic': 'ATR condition AND RSI condition',
        },
        FILTER_VOLATILITY: {
            'name': 'Volatility Condition',
            'description': 'Block signals during extreme volatility',
            'parameters': ['volatility_period', 'volatility_max_mult'],
            'logic': 'Volatility < Volatility_MA * max_multiplier',
        },
    }
    
    if filter_type is not None:
        filter_type = validate_filter_type(filter_type)
        return all_filters.get(filter_type, all_filters[FILTER_NONE])
    
    return all_filters


def get_filter_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get statistics about filter effect on signals
    
    Args:
        df: DataFrame after apply_filter()
        
    Returns:
        Dictionary with filter statistics
    """
    if 'can_long' not in df.columns or 'filtered_can_long' not in df.columns:
        return {'error': 'No filter columns found. Run apply_filter() first.'}
    
    # Original signal counts
    original_long = df['can_long'].sum()
    original_short = df['can_short'].sum()
    original_total = original_long + original_short
    
    # Filtered signal counts
    filtered_long = df['filtered_can_long'].sum()
    filtered_short = df['filtered_can_short'].sum()
    filtered_total = filtered_long + filtered_short
    
    # Blocked counts
    blocked_long = original_long - filtered_long
    blocked_short = original_short - filtered_short
    blocked_total = blocked_long + blocked_short
    
    # Filter pass rates
    long_pass_rate = (filtered_long / original_long * 100) if original_long > 0 else 100.0
    short_pass_rate = (filtered_short / original_short * 100) if original_short > 0 else 100.0
    total_pass_rate = (filtered_total / original_total * 100) if original_total > 0 else 100.0
    
    return {
        'filter_type': int(df['filter_type_applied'].iloc[0]) if 'filter_type_applied' in df.columns else FILTER_NONE,
        'filter_name': FILTER_NAMES.get(int(df['filter_type_applied'].iloc[0]) if 'filter_type_applied' in df.columns else 0, 'Unknown'),
        'original_signals': {
            'long': int(original_long),
            'short': int(original_short),
            'total': int(original_total),
        },
        'filtered_signals': {
            'long': int(filtered_long),
            'short': int(filtered_short),
            'total': int(filtered_total),
        },
        'blocked_signals': {
            'long': int(blocked_long),
            'short': int(blocked_short),
            'total': int(blocked_total),
        },
        'pass_rates': {
            'long': round(long_pass_rate, 2),
            'short': round(short_pass_rate, 2),
            'total': round(total_pass_rate, 2),
        },
    }


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


def generate_signals_with_filter(
    df: pd.DataFrame,
    sensitivity: int = SENSITIVITY_DEFAULT,
    require_confirmation: bool = True,
    filter_type: int = FILTER_NONE,
    **filter_kwargs
) -> pd.DataFrame:
    """
    Generate signals and apply filter in one call
    
    Convenience function that combines generate_signals() and apply_filter().
    
    Args:
        df: DataFrame with OHLCV data
        sensitivity: Channel period (12-60, default 21)
        require_confirmation: Require candle confirmation
        filter_type: 0-4 (None, ATR, RSI, Combined, Volatility)
        **filter_kwargs: Additional filter parameters (atr_period, rsi_overbought, etc.)
    
    Returns:
        DataFrame with both signal and filter columns
    
    Example:
        >>> result = generate_signals_with_filter(
        ...     df, 
        ...     sensitivity=21,
        ...     filter_type=2,
        ...     rsi_overbought=70,
        ...     rsi_oversold=30
        ... )
        >>> filtered_longs = result[result['filtered_can_long']]
    """
    # First generate signals
    result = generate_signals(df, sensitivity, require_confirmation)
    
    # Then apply filter
    result = apply_filter(result, filter_type=filter_type, **filter_kwargs)
    
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
    
    # Add filter info if available
    if 'filter_pass_long' in df.columns:
        levels['filter_pass_long'] = bool(last_row.get('filter_pass_long', True))
        levels['filter_pass_short'] = bool(last_row.get('filter_pass_short', True))
        levels['filtered_can_long'] = bool(last_row.get('filtered_can_long', False))
        levels['filtered_can_short'] = bool(last_row.get('filtered_can_short', False))
    
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
        'version': '4.0.2',
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
        'filters': {
            'types': FILTER_NAMES,
            'defaults': FILTER_DEFAULTS,
        },
        'outputs': {
            'channel': ['high_channel', 'low_channel', 'mid_channel', 'channel_range'],
            'fibonacci_long': ['fib_236', 'fib_382', 'fib_500', 'fib_618'],
            'fibonacci_short': ['fib_236_high', 'fib_382_high', 'fib_500_high', 'fib_618_high'],
            'derived': ['channel_width_pct', 'price_position'],
            'signals': ['can_long', 'can_short', 'signal', 'is_long_trend', 'is_short_trend', 'entry_price', 'signal_type'],
            'filters': ['filter_pass_long', 'filter_pass_short', 'filtered_can_long', 'filtered_can_short', 'filtered_signal']
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
    
    # Add filtered signal markers if available
    if 'filtered_can_long' in df.columns:
        plot_data['filtered_long_signals'] = df[df['filtered_can_long']].index.tolist()
        plot_data['filtered_long_prices'] = df.loc[df['filtered_can_long'], 'close'].tolist()
    
    if 'filtered_can_short' in df.columns:
        plot_data['filtered_short_signals'] = df[df['filtered_can_short']].index.tolist()
        plot_data['filtered_short_prices'] = df.loc[df['filtered_can_short'], 'close'].tolist()
    
    return plot_data


# =============================================================================
# MODULE TEST
# =============================================================================

if __name__ == '__main__':
    # Quick test
    print("Testing Dominant Indicator with Filters...")
    
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
    
    # Test all filter types
    for filter_type in range(5):
        print(f"\n--- Filter Type {filter_type}: {FILTER_NAMES[filter_type]} ---")
        
        result = generate_signals_with_filter(df, sensitivity=21, filter_type=filter_type)
        stats = get_filter_statistics(result)
        
        print(f"Original signals: {stats['original_signals']['total']}")
        print(f"Filtered signals: {stats['filtered_signals']['total']}")
        print(f"Pass rate: {stats['pass_rates']['total']}%")
    
    print("\n✅ Dominant indicator with filters test passed!")
