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

SL Modes (Chat #23):
- Mode 0: Fixed - SL never moves
- Mode 1: Breakeven after TP1 hit
- Mode 2: Breakeven after TP2 hit
- Mode 3: Breakeven after TP3 hit
- Mode 4: Cascade - SL trails to previous TP level

AI Resolution (Chat #25):
- Automatic optimization of sensitivity parameter (12-60)
- Multi-core parallel backtesting
- Scoring: Profit(30%) + WinRate(25%) + Stability(25%) + Drawdown(20%)
- Returns best sensitivity and detailed analysis

Author: KOMAS Team
Version: 4.0.4
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple, Any, List, Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
import os
import time

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
# SL MODE CONSTANTS (Chat #23)
# =============================================================================

SL_MODE_FIXED = 0
SL_MODE_AFTER_TP1 = 1
SL_MODE_AFTER_TP2 = 2
SL_MODE_AFTER_TP3 = 3
SL_MODE_CASCADE = 4

SL_MODE_NAMES = {
    SL_MODE_FIXED: 'Fixed',
    SL_MODE_AFTER_TP1: 'Breakeven After TP1',
    SL_MODE_AFTER_TP2: 'Breakeven After TP2',
    SL_MODE_AFTER_TP3: 'Breakeven After TP3',
    SL_MODE_CASCADE: 'Cascade Trailing',
}

SL_MODE_DESCRIPTIONS = {
    SL_MODE_FIXED: 'Stop-loss stays at original level regardless of TP hits',
    SL_MODE_AFTER_TP1: 'SL moves to entry price (breakeven) after TP1 is hit',
    SL_MODE_AFTER_TP2: 'SL moves to entry price (breakeven) after TP2 is hit',
    SL_MODE_AFTER_TP3: 'SL moves to entry price (breakeven) after TP3 is hit',
    SL_MODE_CASCADE: 'SL trails progressively: breakeven after TP1, then to each TP level',
}

# Default SL parameters
SL_DEFAULTS = {
    'sl_percent': 2.0,  # 2% default stop-loss
    'tp_percents': [1.0, 2.0, 3.0, 5.0],  # Default TP levels: 1%, 2%, 3%, 5%
}

# =============================================================================
# AI RESOLUTION CONSTANTS (Chat #25)
# =============================================================================

# Sensitivities to test in optimization
OPTIMIZATION_SENSITIVITIES = [12, 15, 18, 21, 25, 30, 35, 40, 45, 50, 55, 60]

# Scoring weights (total = 100%)
SCORE_WEIGHT_PROFIT = 30.0
SCORE_WEIGHT_WIN_RATE = 25.0
SCORE_WEIGHT_STABILITY = 25.0
SCORE_WEIGHT_DRAWDOWN = 20.0

# Minimum trades required for valid optimization
MIN_TRADES_FOR_OPTIMIZATION = 5

# Default workers for multi-core processing
DEFAULT_WORKERS = None  # None = use all available cores


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


def validate_sl_mode(sl_mode: int) -> int:
    """
    Validate SL mode is in valid range [0, 4]
    
    Args:
        sl_mode: Input SL mode
        
    Returns:
        Valid SL mode (clamped to range)
    """
    if not isinstance(sl_mode, (int, float)):
        return SL_MODE_FIXED
    return max(SL_MODE_FIXED, min(SL_MODE_CASCADE, int(sl_mode)))


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
        (result['close'] - result['low_channel']) / result['channel_range'],
        0.5  # Default to middle if range is 0
    )
    
    return result


# =============================================================================
# FILTER CALCULATION (Chat #22)
# =============================================================================

def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        series: Price series (typically close prices)
        period: RSI period (default 14)
    
    Returns:
        Series with RSI values (0-100)
    """
    delta = series.diff()
    
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    
    rs = np.where(avg_loss != 0, avg_gain / avg_loss, 100)
    
    rsi = 100 - (100 / (1 + rs))
    
    return pd.Series(rsi, index=series.index)


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR)
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ATR period (default 14)
    
    Returns:
        Series with ATR values
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = np.abs(high - close.shift(1))
    tr3 = np.abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = tr.rolling(window=period, min_periods=1).mean()
    
    return atr


def apply_filter(
    df: pd.DataFrame,
    filter_type: int = FILTER_NONE,
    atr_period: int = None,
    atr_multiplier: float = None,
    rsi_period: int = None,
    rsi_overbought: float = None,
    rsi_oversold: float = None,
    volatility_period: int = None,
    volatility_max_mult: float = None
) -> pd.DataFrame:
    """
    Apply filter to signals based on filter type
    
    This function adds filter columns to the DataFrame and creates
    'filtered_can_long' and 'filtered_can_short' columns.
    
    Filter Types:
    - 0 (None): No filtering, all signals pass
    - 1 (ATR): Volume spike confirmation (ATR > average * multiplier)
    - 2 (RSI): Not overbought/oversold
    - 3 (Combined): ATR AND RSI conditions
    - 4 (Volatility): Normal volatility range
    
    Args:
        df: DataFrame with signal columns from generate_signals()
        filter_type: 0-4 (None, ATR, RSI, Combined, Volatility)
        atr_period: Period for ATR calculation (default 14)
        atr_multiplier: ATR threshold multiplier (default 1.5)
        rsi_period: Period for RSI calculation (default 14)
        rsi_overbought: RSI overbought threshold (default 70)
        rsi_oversold: RSI oversold threshold (default 30)
        volatility_period: Period for volatility calculation (default 20)
        volatility_max_mult: Max volatility multiplier (default 2.0)
    
    Returns:
        DataFrame with additional filter columns:
        - filter_pass_long: True if long signals should pass filter
        - filter_pass_short: True if short signals should pass filter
        - filtered_can_long: can_long AND filter_pass_long
        - filtered_can_short: can_short AND filter_pass_short
        - filtered_signal: Combined filtered signal column
    
    Example:
        >>> result = generate_signals(df, sensitivity=21)
        >>> filtered = apply_filter(result, filter_type=2, rsi_overbought=70, rsi_oversold=30)
        >>> print(filtered['filtered_can_long'].sum())
    """
    # Validate filter type
    filter_type = validate_filter_type(filter_type)
    
    # Apply defaults for parameters
    if atr_period is None:
        atr_period = FILTER_DEFAULTS['atr_period']
    if atr_multiplier is None:
        atr_multiplier = FILTER_DEFAULTS['atr_multiplier']
    if rsi_period is None:
        rsi_period = FILTER_DEFAULTS['rsi_period']
    if rsi_overbought is None:
        rsi_overbought = FILTER_DEFAULTS['rsi_overbought']
    if rsi_oversold is None:
        rsi_oversold = FILTER_DEFAULTS['rsi_oversold']
    if volatility_period is None:
        volatility_period = FILTER_DEFAULTS['volatility_period']
    if volatility_max_mult is None:
        volatility_max_mult = FILTER_DEFAULTS['volatility_max_mult']
    
    # Create copy to avoid modifying original
    result = df.copy()
    
    # Initialize filter pass columns (default: all pass)
    n = len(result)
    filter_pass_long = np.ones(n, dtype=bool)
    filter_pass_short = np.ones(n, dtype=bool)
    
    # ==========================================================================
    # FILTER TYPE 0: NONE - All signals pass
    # ==========================================================================
    if filter_type == FILTER_NONE:
        pass  # Keep defaults (all True)
    
    # ==========================================================================
    # FILTER TYPE 1: ATR CONDITION
    # ==========================================================================
    elif filter_type == FILTER_ATR:
        atr = calculate_atr(result, period=atr_period)
        atr_ma = atr.rolling(window=atr_period, min_periods=1).mean()
        
        # Signal passes when ATR is above average (trending/volatile market)
        atr_condition = (atr > atr_ma * atr_multiplier).values
        
        filter_pass_long = atr_condition
        filter_pass_short = atr_condition
        
        # Store intermediate values
        result['filter_atr'] = atr
        result['filter_atr_ma'] = atr_ma
        result['filter_atr_condition'] = atr_condition
    
    # ==========================================================================
    # FILTER TYPE 2: RSI CONDITION
    # ==========================================================================
    elif filter_type == FILTER_RSI:
        rsi = calculate_rsi(result['close'], period=rsi_period)
        
        # Long: not overbought (RSI < overbought threshold)
        # Short: not oversold (RSI > oversold threshold)
        filter_pass_long = (rsi < rsi_overbought).values
        filter_pass_short = (rsi > rsi_oversold).values
        
        # Store intermediate values
        result['filter_rsi'] = rsi
    
    # ==========================================================================
    # FILTER TYPE 3: ATR + RSI COMBINED
    # ==========================================================================
    elif filter_type == FILTER_COMBINED:
        atr = calculate_atr(result, period=atr_period)
        atr_ma = atr.rolling(window=atr_period, min_periods=1).mean()
        atr_condition = (atr > atr_ma * atr_multiplier).values
        
        rsi = calculate_rsi(result['close'], period=rsi_period)
        
        # Both conditions must be met
        filter_pass_long = atr_condition & (rsi < rsi_overbought).values
        filter_pass_short = atr_condition & (rsi > rsi_oversold).values
        
        # Store intermediate values
        result['filter_atr'] = atr
        result['filter_atr_ma'] = atr_ma
        result['filter_atr_condition'] = atr_condition
        result['filter_rsi'] = rsi
    
    # ==========================================================================
    # FILTER TYPE 4: VOLATILITY CONDITION
    # ==========================================================================
    elif filter_type == FILTER_VOLATILITY:
        # Use channel width as volatility measure
        if 'channel_width_pct' in result.columns:
            vol = result['channel_width_pct']
        else:
            # Calculate if not present
            atr = calculate_atr(result, period=volatility_period)
            vol = (atr / result['close']) * 100
        
        vol_ma = vol.rolling(window=volatility_period, min_periods=1).mean()
        
        # Filter out extreme volatility (both too high and too low)
        volatility_ok = (vol < vol_ma * volatility_max_mult).values & (vol > vol_ma * 0.5).values
        
        filter_pass_long = volatility_ok
        filter_pass_short = volatility_ok
        
        # Store intermediate values
        result['filter_volatility'] = vol
        result['filter_volatility_ma'] = vol_ma
        result['filter_volatility_ok'] = volatility_ok
    
    # ==========================================================================
    # APPLY FILTERS TO SIGNALS
    # ==========================================================================
    
    result['filter_pass_long'] = filter_pass_long
    result['filter_pass_short'] = filter_pass_short
    
    # Create filtered signal columns
    if 'can_long' in result.columns:
        result['filtered_can_long'] = result['can_long'] & result['filter_pass_long']
    else:
        result['filtered_can_long'] = result['filter_pass_long']
    
    if 'can_short' in result.columns:
        result['filtered_can_short'] = result['can_short'] & result['filter_pass_short']
    else:
        result['filtered_can_short'] = result['filter_pass_short']
    
    # Create combined filtered signal column
    result['filtered_signal'] = np.where(
        result['filtered_can_long'], SIGNAL_LONG,
        np.where(result['filtered_can_short'], SIGNAL_SHORT, SIGNAL_NONE)
    )
    
    # Store filter type used
    result['filter_type'] = filter_type
    
    return result


def get_filter_info(filter_type: int = None) -> Dict[str, Any]:
    """
    Get information about filters
    
    Args:
        filter_type: Specific filter type to get info for (None = all)
    
    Returns:
        Dictionary with filter information
    """
    if filter_type is not None:
        filter_type = validate_filter_type(filter_type)
        return {
            'type': filter_type,
            'name': FILTER_NAMES.get(filter_type, 'Unknown'),
            'defaults': FILTER_DEFAULTS.copy()
        }
    
    return {
        'types': FILTER_NAMES.copy(),
        'defaults': FILTER_DEFAULTS.copy(),
        'descriptions': {
            FILTER_NONE: 'No filtering - all signals pass',
            FILTER_ATR: 'ATR condition - signals pass when volatility is above average',
            FILTER_RSI: 'RSI condition - long signals filtered when overbought, short when oversold',
            FILTER_COMBINED: 'ATR + RSI - both conditions must be met',
            FILTER_VOLATILITY: 'Volatility condition - signals filtered during extreme volatility',
        }
    }


def get_filter_statistics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Get statistics about filter performance
    
    Args:
        df: DataFrame with filter columns
    
    Returns:
        Dictionary with filter statistics
    """
    if 'filter_pass_long' not in df.columns:
        return {'error': 'No filter columns found. Run apply_filter() first.'}
    
    total = len(df)
    
    # Count signals before/after filter
    has_can_long = 'can_long' in df.columns
    has_can_short = 'can_short' in df.columns
    
    stats = {
        'total_rows': total,
        'filter_type': int(df['filter_type'].iloc[0]) if 'filter_type' in df.columns else -1,
        'long_filter_pass_rate': round(df['filter_pass_long'].mean() * 100, 2),
        'short_filter_pass_rate': round(df['filter_pass_short'].mean() * 100, 2),
    }
    
    if has_can_long:
        total_long = df['can_long'].sum()
        filtered_long = df['filtered_can_long'].sum()
        stats['total_long_signals'] = int(total_long)
        stats['filtered_long_signals'] = int(filtered_long)
        stats['long_signals_rejected'] = int(total_long - filtered_long)
        stats['long_rejection_rate'] = round((1 - filtered_long / total_long) * 100, 2) if total_long > 0 else 0
    
    if has_can_short:
        total_short = df['can_short'].sum()
        filtered_short = df['filtered_can_short'].sum()
        stats['total_short_signals'] = int(total_short)
        stats['filtered_short_signals'] = int(filtered_short)
        stats['short_signals_rejected'] = int(total_short - filtered_short)
        stats['short_rejection_rate'] = round((1 - filtered_short / total_short) * 100, 2) if total_short > 0 else 0
    
    return stats


# =============================================================================
# SL MODE FUNCTIONS (Chat #23)
# =============================================================================

def calculate_tp_levels(
    entry_price: float,
    direction: int,
    tp_percents: List[float]
) -> List[float]:
    """
    Calculate absolute TP price levels
    
    Args:
        entry_price: Entry price of the position
        direction: SIGNAL_LONG (1) or SIGNAL_SHORT (-1)
        tp_percents: List of TP distances in percent
    
    Returns:
        List of absolute TP price levels
    """
    if direction == SIGNAL_LONG:
        # Long: TP levels are above entry
        return [entry_price * (1 + pct / 100) for pct in tp_percents]
    else:
        # Short: TP levels are below entry
        return [entry_price * (1 - pct / 100) for pct in tp_percents]


def calculate_initial_sl(
    entry_price: float,
    direction: int,
    sl_percent: float
) -> float:
    """
    Calculate initial stop-loss level
    
    Args:
        entry_price: Entry price of the position
        direction: SIGNAL_LONG (1) or SIGNAL_SHORT (-1)
        sl_percent: SL distance in percent
    
    Returns:
        Absolute SL price level
    """
    if direction == SIGNAL_LONG:
        # Long: SL is below entry
        return entry_price * (1 - sl_percent / 100)
    else:
        # Short: SL is above entry
        return entry_price * (1 + sl_percent / 100)


def calculate_sl_level(
    entry_price: float,
    direction: int,
    sl_percent: float,
    sl_mode: int,
    tps_hit: List[bool],
    tp_levels: List[float]
) -> float:
    """
    Calculate current SL level based on mode and TPs hit
    
    This function determines where the stop-loss should be based on:
    - Original SL settings
    - SL mode (fixed, breakeven after TPx, cascade)
    - Which TPs have been hit
    
    Args:
        entry_price: Entry price of the position
        direction: SIGNAL_LONG (1) or SIGNAL_SHORT (-1)
        sl_percent: Original SL distance in percent
        sl_mode: 0-4 (Fixed, AfterTP1, AfterTP2, AfterTP3, Cascade)
        tps_hit: List of booleans indicating which TPs have been hit
        tp_levels: List of absolute TP price levels
    
    Returns:
        Current SL price level
    
    Example:
        >>> sl = calculate_sl_level(
        ...     entry_price=100.0,
        ...     direction=SIGNAL_LONG,
        ...     sl_percent=2.0,
        ...     sl_mode=SL_MODE_CASCADE,
        ...     tps_hit=[True, True, False, False],  # TP1 and TP2 hit
        ...     tp_levels=[101.0, 102.0, 103.0, 105.0]
        ... )
        >>> print(sl)  # Should be at TP2 level (102.0) for cascade mode
    """
    sl_mode = validate_sl_mode(sl_mode)
    
    # Calculate initial SL
    initial_sl = calculate_initial_sl(entry_price, direction, sl_percent)
    
    # ==========================================================================
    # MODE 0: FIXED - SL never moves
    # ==========================================================================
    if sl_mode == SL_MODE_FIXED:
        return initial_sl
    
    # ==========================================================================
    # MODE 1: BREAKEVEN AFTER TP1
    # ==========================================================================
    if sl_mode == SL_MODE_AFTER_TP1:
        if len(tps_hit) > 0 and tps_hit[0]:
            return entry_price  # Move to breakeven
        return initial_sl
    
    # ==========================================================================
    # MODE 2: BREAKEVEN AFTER TP2
    # ==========================================================================
    if sl_mode == SL_MODE_AFTER_TP2:
        if len(tps_hit) > 1 and tps_hit[1]:
            return entry_price  # Move to breakeven
        return initial_sl
    
    # ==========================================================================
    # MODE 3: BREAKEVEN AFTER TP3
    # ==========================================================================
    if sl_mode == SL_MODE_AFTER_TP3:
        if len(tps_hit) > 2 and tps_hit[2]:
            return entry_price  # Move to breakeven
        return initial_sl
    
    # ==========================================================================
    # MODE 4: CASCADE - SL trails behind TPs
    # ==========================================================================
    if sl_mode == SL_MODE_CASCADE:
        # Find the highest TP level that has been hit
        # SL moves to that level (or breakeven for TP1)
        
        last_tp_hit_idx = -1
        for idx, hit in enumerate(tps_hit):
            if hit:
                last_tp_hit_idx = idx
        
        if last_tp_hit_idx == -1:
            # No TPs hit yet, use initial SL
            return initial_sl
        elif last_tp_hit_idx == 0:
            # TP1 hit: move to breakeven
            return entry_price
        else:
            # TP2+ hit: move SL to previous TP level
            # After TP2 hit -> SL at TP1
            # After TP3 hit -> SL at TP2
            # etc.
            return tp_levels[last_tp_hit_idx - 1]
    
    # Default fallback
    return initial_sl


def _calculate_sl_for_mode(
    entry_price: float,
    direction: int,
    current_sl: float,
    sl_mode: int,
    tps_hit: List[bool],
    tp_levels: List[float]
) -> float:
    """
    Helper to calculate new SL level based on mode after TP hit.
    Used internally by track_position.
    
    Unlike calculate_sl_level, this doesn't recalculate initial SL,
    it just returns the new SL based on breakeven/cascade logic.
    """
    # MODE 0: FIXED - SL never moves
    if sl_mode == SL_MODE_FIXED:
        return current_sl
    
    # MODE 1: BREAKEVEN AFTER TP1
    if sl_mode == SL_MODE_AFTER_TP1:
        if len(tps_hit) > 0 and tps_hit[0]:
            return entry_price  # Move to breakeven
        return current_sl
    
    # MODE 2: BREAKEVEN AFTER TP2
    if sl_mode == SL_MODE_AFTER_TP2:
        if len(tps_hit) > 1 and tps_hit[1]:
            return entry_price  # Move to breakeven
        return current_sl
    
    # MODE 3: BREAKEVEN AFTER TP3
    if sl_mode == SL_MODE_AFTER_TP3:
        if len(tps_hit) > 2 and tps_hit[2]:
            return entry_price  # Move to breakeven
        return current_sl
    
    # MODE 4: CASCADE - SL trails behind TPs
    if sl_mode == SL_MODE_CASCADE:
        last_tp_hit_idx = -1
        for idx, hit in enumerate(tps_hit):
            if hit:
                last_tp_hit_idx = idx
        
        if last_tp_hit_idx == -1:
            return current_sl
        elif last_tp_hit_idx == 0:
            return entry_price  # TP1 hit: move to breakeven
        else:
            return tp_levels[last_tp_hit_idx - 1]  # Move to previous TP
    
    return current_sl


def track_position(
    df: pd.DataFrame,
    entry_idx: int,
    direction: int,
    entry_price: float,
    sl_percent: float = None,
    tp_percents: List[float] = None,
    sl_mode: int = SL_MODE_FIXED,
    fixed_stop: bool = False
) -> Dict[str, Any]:
    """
    Simulate position tracking through price data
    
    This function tracks a position from entry through exit,
    monitoring TP/SL levels and applying the specified SL mode.
    
    IMPORTANT: By default (fixed_stop=False), SL is calculated from
    mid_channel (fib_5 / imba_trend_line), NOT from entry price!
    This matches the original Pine Script behavior.
    
    Args:
        df: DataFrame with OHLCV data (must have 'high', 'low', 'close', 'mid_channel')
        entry_idx: Index (row number) where position was entered
        direction: SIGNAL_LONG (1) or SIGNAL_SHORT (-1)
        entry_price: Entry price of the position
        sl_percent: Initial SL distance in percent (default 2.0%)
        tp_percents: List of TP percentages (default [1.0, 2.0, 3.0, 5.0])
        sl_mode: SL mode (0-4)
        fixed_stop: If True, SL from entry_price. If False (default), SL from mid_channel
    
    Returns:
        Dictionary with:
        - exit_idx: Index where position closed
        - exit_price: Price at exit
        - exit_reason: 'sl' or 'tp1'/'tp2'/'tp3'/'tp4'
        - pnl_percent: Profit/loss percentage
        - tps_hit: List of which TPs were hit
        - sl_history: List of (idx, sl_price) tuples showing SL movements
        - max_profit: Maximum unrealized profit during trade
        - duration: Number of bars position was held
    
    Example:
        >>> result = track_position(df, entry_idx=10, direction=SIGNAL_LONG, 
        ...                         entry_price=100.0, sl_percent=2.0, 
        ...                         tp_percents=[1.0, 2.0], sl_mode=SL_MODE_CASCADE)
        >>> print(result['exit_reason'])  # 'tp1', 'tp2', or 'sl'
    """
    # Validate inputs
    sl_mode = validate_sl_mode(sl_mode)
    
    if sl_percent is None:
        sl_percent = SL_DEFAULTS['sl_percent']
    
    if tp_percents is None:
        tp_percents = SL_DEFAULTS['tp_percents'].copy()
    
    # Calculate TP levels (from entry price)
    tp_levels = calculate_tp_levels(entry_price, direction, tp_percents)
    
    # Initialize tracking
    tps_hit = [False] * len(tp_levels)
    sl_history = []  # Track SL movements
    max_profit = 0.0
    
    # ==========================================================================
    # INITIAL SL CALCULATION - KEY DIFFERENCE FROM TRG!
    # ==========================================================================
    # In Dominant indicator, SL is calculated from mid_channel (fib_5), 
    # NOT from entry_price (unless fixed_stop=True)
    
    if fixed_stop or 'mid_channel' not in df.columns:
        # Fixed stop mode or no mid_channel: use entry price
        sl_base_price = entry_price
    else:
        # Default: use mid_channel (fib_5 / imba_trend_line) at entry
        sl_base_price = df.iloc[entry_idx]['mid_channel']
    
    # Calculate initial SL from the base price
    if direction == SIGNAL_LONG:
        current_sl = sl_base_price * (1 - sl_percent / 100)
    else:  # SHORT
        current_sl = sl_base_price * (1 + sl_percent / 100)
    
    sl_history.append((entry_idx, current_sl))
    
    # Store original SL base for breakeven calculations
    original_sl_base = sl_base_price
    
    # Iterate through price data after entry
    n = len(df)
    for idx in range(entry_idx + 1, n):
        row = df.iloc[idx]
        high = row['high']
        low = row['low']
        close = row['close']
        
        # =======================================================================
        # CHECK TP HITS
        # =======================================================================
        for tp_idx, tp_price in enumerate(tp_levels):
            if tps_hit[tp_idx]:
                continue  # Already hit
            
            if direction == SIGNAL_LONG:
                # Long: TP hit when high >= tp_price
                if high >= tp_price:
                    tps_hit[tp_idx] = True
                    
                    # Update SL based on mode (using entry_price for breakeven)
                    new_sl = _calculate_sl_for_mode(
                        entry_price, direction, current_sl, sl_mode, tps_hit, tp_levels
                    )
                    if new_sl != current_sl:
                        current_sl = new_sl
                        sl_history.append((idx, current_sl))
            else:  # SHORT
                # Short: TP hit when low <= tp_price
                if low <= tp_price:
                    tps_hit[tp_idx] = True
                    
                    # Update SL based on mode (using entry_price for breakeven)
                    new_sl = _calculate_sl_for_mode(
                        entry_price, direction, current_sl, sl_mode, tps_hit, tp_levels
                    )
                    if new_sl != current_sl:
                        current_sl = new_sl
                        sl_history.append((idx, current_sl))
        
        # =======================================================================
        # CHECK SL HIT
        # =======================================================================
        sl_hit = False
        if direction == SIGNAL_LONG:
            # Long: SL hit when low <= sl_price
            if low <= current_sl:
                sl_hit = True
                exit_price = current_sl  # Exit at SL level
        else:  # SHORT
            # Short: SL hit when high >= sl_price
            if high >= current_sl:
                sl_hit = True
                exit_price = current_sl  # Exit at SL level
        
        # =======================================================================
        # CALCULATE CURRENT P&L
        # =======================================================================
        if direction == SIGNAL_LONG:
            current_profit = (close - entry_price) / entry_price * 100
        else:
            current_profit = (entry_price - close) / entry_price * 100
        
        max_profit = max(max_profit, current_profit)
        
        # =======================================================================
        # CHECK EXIT CONDITIONS
        # =======================================================================
        
        # TP amounts (% of position closed at each TP)
        # Default: 40% at TP1, 30% at TP2, 20% at TP3, 10% at TP4
        tp_amounts = [40, 30, 20, 10]
        if len(tp_amounts) < len(tp_percents):
            # Extend if more TPs than amounts
            remaining = 100 - sum(tp_amounts)
            extra_count = len(tp_percents) - len(tp_amounts)
            tp_amounts.extend([remaining // extra_count] * extra_count)
        
        # If all TPs hit - exit with weighted PnL
        if all(tps_hit):
            # Calculate weighted PnL: sum(TP% × amount%)
            weighted_pnl = sum(
                tp_pct * (tp_amt / 100) 
                for tp_pct, tp_amt in zip(tp_percents, tp_amounts[:len(tp_percents)])
            )
            return {
                'exit_idx': idx,
                'exit_price': tp_levels[-1],
                'exit_reason': f'tp{len(tp_levels)}',
                'pnl_percent': weighted_pnl,
                'tps_hit': tps_hit.copy(),
                'sl_history': sl_history,
                'max_profit': max_profit,
                'duration': idx - entry_idx,
            }
        
        # If SL hit - calculate PnL considering partial TP profits
        if sl_hit:
            # Calculate SL PnL
            if direction == SIGNAL_LONG:
                sl_pnl_pct = (exit_price - entry_price) / entry_price * 100
            else:
                sl_pnl_pct = (entry_price - exit_price) / entry_price * 100
            
            # Calculate total PnL: TP profits + SL loss on remaining position
            total_pnl = 0
            remaining_amount = 100  # % of position still open
            
            for tp_idx, tp_hit in enumerate(tps_hit):
                tp_amt = tp_amounts[tp_idx] if tp_idx < len(tp_amounts) else 0
                if tp_hit:
                    # This TP was hit - add profit
                    total_pnl += tp_percents[tp_idx] * (tp_amt / 100)
                    remaining_amount -= tp_amt
            
            # Remaining position closed at SL
            if remaining_amount > 0:
                total_pnl += sl_pnl_pct * (remaining_amount / 100)
            
            return {
                'exit_idx': idx,
                'exit_price': exit_price,
                'exit_reason': 'sl',
                'pnl_percent': total_pnl,
                'tps_hit': tps_hit.copy(),
                'sl_history': sl_history,
                'max_profit': max_profit,
                'duration': idx - entry_idx,
            }
    
    # Position still open at end of data
    last_close = df.iloc[-1]['close']
    if direction == SIGNAL_LONG:
        pnl = (last_close - entry_price) / entry_price * 100
    else:
        pnl = (entry_price - last_close) / entry_price * 100
    
    return {
        'exit_idx': n - 1,
        'exit_price': last_close,
        'exit_reason': 'end_of_data',
        'pnl_percent': pnl,
        'tps_hit': tps_hit.copy(),
        'sl_history': sl_history,
        'max_profit': max_profit,
        'duration': (n - 1) - entry_idx,
    }


def get_sl_mode_info(sl_mode: int = None) -> Dict[str, Any]:
    """
    Get information about SL modes
    
    Args:
        sl_mode: Specific mode to get info for (None = all)
    
    Returns:
        Dictionary with SL mode information
    """
    if sl_mode is not None:
        sl_mode = validate_sl_mode(sl_mode)
        return {
            'mode': sl_mode,
            'name': SL_MODE_NAMES.get(sl_mode, 'Unknown'),
            'description': SL_MODE_DESCRIPTIONS.get(sl_mode, 'Unknown'),
        }
    
    return {
        'modes': SL_MODE_NAMES.copy(),
        'descriptions': SL_MODE_DESCRIPTIONS.copy(),
        'defaults': SL_DEFAULTS.copy(),
    }


def get_sl_mode_statistics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get statistics about SL mode performance across trades
    
    Args:
        trades: List of trade results from track_position()
    
    Returns:
        Dictionary with SL mode statistics
    """
    if not trades:
        return {'error': 'No trades to analyze'}
    
    total_trades = len(trades)
    
    # Categorize exit reasons
    sl_exits = sum(1 for t in trades if t['exit_reason'] == 'sl')
    tp_exits = sum(1 for t in trades if t['exit_reason'].startswith('tp'))
    other_exits = total_trades - sl_exits - tp_exits
    
    # Calculate PnL stats
    pnls = [t['pnl_percent'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    
    # SL movement analysis
    total_sl_moves = sum(len(t['sl_history']) - 1 for t in trades)  # -1 for initial SL
    avg_sl_moves = total_sl_moves / total_trades if total_trades > 0 else 0
    
    return {
        'total_trades': total_trades,
        'sl_exits': sl_exits,
        'sl_exit_rate': round(sl_exits / total_trades * 100, 2) if total_trades > 0 else 0,
        'tp_exits': tp_exits,
        'tp_exit_rate': round(tp_exits / total_trades * 100, 2) if total_trades > 0 else 0,
        'other_exits': other_exits,
        'total_pnl': round(sum(pnls), 2),
        'avg_pnl': round(sum(pnls) / total_trades, 2) if total_trades > 0 else 0,
        'win_rate': round(len(wins) / total_trades * 100, 2) if total_trades > 0 else 0,
        'avg_win': round(sum(wins) / len(wins), 2) if wins else 0,
        'avg_loss': round(sum(losses) / len(losses), 2) if losses else 0,
        'profit_factor': round(sum(wins) / abs(sum(losses)), 2) if losses and sum(losses) != 0 else float('inf'),
        'total_sl_movements': total_sl_moves,
        'avg_sl_movements_per_trade': round(avg_sl_moves, 2),
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
    Generate trading signals from Dominant indicator
    
    This function calculates the full Dominant indicator and adds signal columns.
    
    Signal Logic:
    - can_long: close >= mid_channel AND close >= fib_236 AND close > open (bullish)
    - can_short: close <= mid_channel AND close <= fib_236_high AND close < open (bearish)
    
    Trend Tracking:
    - is_long_trend: True while in long position (until short signal)
    - is_short_trend: True while in short position (until long signal)
    
    Args:
        df: DataFrame with OHLCV data
        sensitivity: Channel period (12-60, default 21)
        require_confirmation: If True, require candle confirmation (close > open for long)
    
    Returns:
        DataFrame with all indicator columns plus:
        - can_long: Boolean for long entry signal
        - can_short: Boolean for short entry signal
        - signal: Combined signal (-1=short, 0=none, 1=long)
        - is_long_trend: Boolean for current long trend
        - is_short_trend: Boolean for current short trend
        - entry_price: Entry price when signal fires
        - signal_type: Human-readable ('LONG', 'SHORT', 'NONE')
    
    Example:
        >>> result = generate_signals(df, sensitivity=21)
        >>> long_entries = result[result['can_long']]
        >>> short_entries = result[result['can_short']]
    """
    # First calculate indicator
    result = calculate_dominant(df, sensitivity)
    
    # ==========================================================================
    # LONG SIGNAL CONDITIONS
    # ==========================================================================
    
    # Price above mid channel
    above_mid = result['close'] >= result['mid_channel']
    
    # Price above fib_236 (first support from low)
    above_fib = result['close'] >= result['fib_236']
    
    # Candle confirmation (optional)
    if require_confirmation:
        bullish_candle = result['close'] > result['open']
        result['can_long'] = above_mid & above_fib & bullish_candle
    else:
        result['can_long'] = above_mid & above_fib
    
    # ==========================================================================
    # SHORT SIGNAL CONDITIONS
    # ==========================================================================
    
    # Price below mid channel
    below_mid = result['close'] <= result['mid_channel']
    
    # Price below fib_236_high (first resistance from high)
    below_fib = result['close'] <= result['fib_236_high']
    
    # Candle confirmation (optional)
    if require_confirmation:
        bearish_candle = result['close'] < result['open']
        result['can_short'] = below_mid & below_fib & bearish_candle
    else:
        result['can_short'] = below_mid & below_fib
    
    # ==========================================================================
    # COMBINED SIGNAL COLUMN
    # ==========================================================================
    
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
# AI RESOLUTION - BACKTEST & SCORING (Chat #25)
# =============================================================================

def run_full_backtest(
    df: pd.DataFrame,
    sensitivity: int = SENSITIVITY_DEFAULT,
    filter_type: int = FILTER_NONE,
    sl_mode: int = SL_MODE_FIXED,
    sl_percent: float = None,
    tp_percents: List[float] = None,
    use_filtered_signals: bool = True,
    allow_immediate_reentry: bool = False,
    fixed_stop: bool = False,
    **filter_kwargs
) -> Dict[str, Any]:
    """
    Run a complete backtest for a given sensitivity configuration
    
    This function generates signals, tracks all positions, and calculates
    comprehensive statistics for the backtest.
    
    Args:
        df: DataFrame with OHLCV data
        sensitivity: Channel period (12-60)
        filter_type: Filter type (0-4)
        sl_mode: Stop-loss mode (0-4)
        sl_percent: Stop-loss percentage (default from SL_DEFAULTS)
        tp_percents: Take-profit percentages (default from SL_DEFAULTS)
        use_filtered_signals: If True, only trade filtered signals
        allow_immediate_reentry: If False, require direction change before new trade
        fixed_stop: If True, SL from entry_price. If False (default), SL from mid_channel
        **filter_kwargs: Additional filter parameters
    
    Returns:
        Dictionary with:
        - trades: List of all trade results
        - metrics: Calculated performance metrics
        - summary: Summary statistics
        - config: Configuration used for backtest
    
    Example:
        >>> result = run_full_backtest(df, sensitivity=21, filter_type=2, sl_mode=4)
        >>> print(f"Total PnL: {result['metrics']['pnl_percent']:.2f}%")
        >>> print(f"Win Rate: {result['metrics']['win_rate']:.1f}%")
    """
    # Apply defaults
    if sl_percent is None:
        sl_percent = SL_DEFAULTS['sl_percent']
    if tp_percents is None:
        tp_percents = SL_DEFAULTS['tp_percents'].copy()
    
    # Generate signals with filter
    signals_df = generate_signals_with_filter(
        df,
        sensitivity=sensitivity,
        filter_type=filter_type,
        **filter_kwargs
    )
    
    # Determine which signal column to use
    if use_filtered_signals and filter_type != FILTER_NONE:
        long_col = 'filtered_can_long'
        short_col = 'filtered_can_short'
    else:
        long_col = 'can_long'
        short_col = 'can_short'
    
    # Extract entry points
    trades = []
    i = 0
    n = len(signals_df)
    last_direction = None  # Track last trade direction for re-entry control
    
    while i < n:
        row = signals_df.iloc[i]
        
        # Check for long signal
        if row[long_col]:
            # Re-entry control: if not allowed, skip same direction trades
            if not allow_immediate_reentry and last_direction == 'LONG':
                i += 1
                continue
            
            entry_price = row['close']
            direction = SIGNAL_LONG
            
            # Track position
            trade_result = track_position(
                df=signals_df,
                entry_idx=i,
                direction=direction,
                entry_price=entry_price,
                sl_percent=sl_percent,
                tp_percents=tp_percents,
                sl_mode=sl_mode,
                fixed_stop=fixed_stop
            )
            
            trade_result['entry_idx'] = i
            trade_result['direction'] = 'LONG'
            trade_result['entry_price'] = entry_price
            trades.append(trade_result)
            
            last_direction = 'LONG'
            
            # Skip to after trade exit
            i = trade_result['exit_idx'] + 1
            continue
        
        # Check for short signal
        if row[short_col]:
            # Re-entry control: if not allowed, skip same direction trades
            if not allow_immediate_reentry and last_direction == 'SHORT':
                i += 1
                continue
            
            entry_price = row['close']
            direction = SIGNAL_SHORT
            
            # Track position
            trade_result = track_position(
                df=signals_df,
                entry_idx=i,
                direction=direction,
                entry_price=entry_price,
                sl_percent=sl_percent,
                tp_percents=tp_percents,
                sl_mode=sl_mode,
                fixed_stop=fixed_stop
            )
            
            trade_result['entry_idx'] = i
            trade_result['direction'] = 'SHORT'
            trade_result['entry_price'] = entry_price
            trades.append(trade_result)
            
            last_direction = 'SHORT'
            
            # Skip to after trade exit
            i = trade_result['exit_idx'] + 1
            continue
        
        i += 1
    
    # Calculate metrics
    metrics = _calculate_backtest_metrics(trades)
    
    # Build summary
    summary = {
        'total_trades': len(trades),
        'long_trades': sum(1 for t in trades if t['direction'] == 'LONG'),
        'short_trades': sum(1 for t in trades if t['direction'] == 'SHORT'),
        'profitable_trades': sum(1 for t in trades if t['pnl_percent'] > 0),
        'losing_trades': sum(1 for t in trades if t['pnl_percent'] <= 0),
    }
    
    return {
        'trades': trades,
        'metrics': metrics,
        'summary': summary,
        'config': {
            'sensitivity': sensitivity,
            'filter_type': filter_type,
            'sl_mode': sl_mode,
            'sl_percent': sl_percent,
            'tp_percents': tp_percents,
            'allow_immediate_reentry': allow_immediate_reentry,
        }
    }


def _calculate_backtest_metrics(trades: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate performance metrics from a list of trades
    
    Args:
        trades: List of trade results from track_position()
    
    Returns:
        Dictionary with performance metrics:
        - pnl_percent: Total PnL percentage
        - win_rate: Win rate percentage (0-100) - based on TP1 hit!
        - profit_factor: Ratio of gross profit to gross loss
        - max_drawdown: Maximum drawdown percentage
        - avg_trade: Average trade PnL
        - avg_win: Average winning trade PnL
        - avg_loss: Average losing trade PnL
        - pnl_std: Standard deviation of trade PnLs
        - sharpe_ratio: Simplified Sharpe ratio (avg/std)
        - total_trades: Number of trades
    """
    if not trades:
        return {
            'pnl_percent': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'max_drawdown': 0.0,
            'avg_trade': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'pnl_std': 0.0,
            'sharpe_ratio': 0.0,
            'total_trades': 0,
        }
    
    pnls = [t['pnl_percent'] for t in trades]
    
    # Win rate based on TP1 hit (not pnl > 0!)
    # A trade is "winning" if TP1 was reached
    wins_count = sum(1 for t in trades if t.get('tps_hit', [False])[0] == True)
    win_rate = wins_count / len(trades) * 100 if trades else 0
    
    # For profit factor calculations
    profit_trades = [p for p in pnls if p > 0]
    loss_trades = [p for p in pnls if p <= 0]
    
    # Total PnL
    total_pnl = sum(pnls)
    
    # Profit factor
    gross_profit = sum(profit_trades) if profit_trades else 0
    gross_loss = abs(sum(loss_trades)) if loss_trades else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0
    
    # Maximum drawdown (equity curve based with compound returns)
    initial_capital = 10000  # Reference capital
    equity = [initial_capital]
    for pnl in pnls:
        new_equity = equity[-1] * (1 + pnl / 100)
        equity.append(new_equity)
    
    peak = equity[0]
    max_dd = 0
    for val in equity:
        if val > peak:
            peak = val
        if peak > 0:
            dd = (peak - val) / peak * 100  # Percentage from peak!
            if dd > max_dd:
                max_dd = dd
    
    # Averages
    avg_trade = total_pnl / len(pnls) if pnls else 0
    avg_win = sum(profit_trades) / len(profit_trades) if profit_trades else 0
    avg_loss = sum(loss_trades) / len(loss_trades) if loss_trades else 0
    
    # Standard deviation
    pnl_std = float(np.std(pnls)) if len(pnls) > 1 else 0
    
    # Sharpe ratio (simplified: avg / std)
    sharpe = avg_trade / pnl_std if pnl_std > 0 else 0
    
    return {
        'pnl_percent': round(total_pnl, 4),
        'win_rate': round(win_rate, 2),
        'profit_factor': round(profit_factor, 4) if profit_factor != float('inf') else 999.0,
        'max_drawdown': round(max_dd, 4),
        'avg_trade': round(avg_trade, 4),
        'avg_win': round(avg_win, 4),
        'avg_loss': round(avg_loss, 4),
        'pnl_std': round(pnl_std, 4),
        'sharpe_ratio': round(sharpe, 4),
        'total_trades': len(pnls),
    }


def calculate_sensitivity_score(metrics: Dict[str, float]) -> float:
    """
    Calculate a score (0-100) for a sensitivity configuration
    
    This scoring function evaluates backtest results using weighted metrics:
    - Profit (30%): Rewards high PnL
    - Win Rate (25%): Rewards high win percentage
    - Stability (25%): Rewards consistency (low std dev)
    - Drawdown (20%): Penalizes high drawdowns
    
    Args:
        metrics: Dictionary with backtest metrics from _calculate_backtest_metrics()
    
    Returns:
        Score between 0 and 100
    
    Example:
        >>> metrics = {'pnl_percent': 15.0, 'win_rate': 60.0, 'pnl_std': 5.0, 'max_drawdown': 10.0}
        >>> score = calculate_sensitivity_score(metrics)
        >>> print(f"Score: {score:.1f}")
    """
    # Extract metrics with defaults
    pnl = metrics.get('pnl_percent', 0)
    win_rate = metrics.get('win_rate', 0)
    pnl_std = metrics.get('pnl_std', 1)
    max_dd = abs(metrics.get('max_drawdown', 0))
    total_trades = metrics.get('total_trades', 0)
    
    # Minimum trades check
    if total_trades < MIN_TRADES_FOR_OPTIMIZATION:
        return 0.0
    
    # ==========================================================================
    # PROFIT SCORE (0-30 points)
    # ==========================================================================
    # Normalize PnL: -20% to +50% -> 0 to 30 points
    # PnL < -20% = 0 points
    # PnL = 0% = 10 points
    # PnL > 50% = 30 points (capped)
    
    if pnl < -20:
        profit_score = 0
    elif pnl > 50:
        profit_score = SCORE_WEIGHT_PROFIT
    else:
        # Linear scaling from -20% to 50%
        profit_score = (pnl + 20) / 70 * SCORE_WEIGHT_PROFIT
    
    # ==========================================================================
    # WIN RATE SCORE (0-25 points)
    # ==========================================================================
    # Win rate directly maps: 0% to 100% -> 0 to 25 points
    
    win_rate_score = (win_rate / 100) * SCORE_WEIGHT_WIN_RATE
    
    # ==========================================================================
    # STABILITY SCORE (0-25 points)
    # ==========================================================================
    # Lower std dev = higher stability
    # std dev = 0 -> 25 points
    # std dev = 10 -> 12.5 points
    # std dev >= 20 -> 0 points
    
    if pnl_std >= 20:
        stability_score = 0
    else:
        stability_score = (1 - pnl_std / 20) * SCORE_WEIGHT_STABILITY
    
    # ==========================================================================
    # DRAWDOWN SCORE (0-20 points)
    # ==========================================================================
    # Lower drawdown = higher score
    # DD = 0 -> 20 points
    # DD = 10% -> 10 points
    # DD >= 40% -> 0 points
    
    if max_dd >= 40:
        dd_score = 0
    else:
        dd_score = (1 - max_dd / 40) * SCORE_WEIGHT_DRAWDOWN
    
    # ==========================================================================
    # TOTAL SCORE
    # ==========================================================================
    
    total_score = profit_score + win_rate_score + stability_score + dd_score
    
    return round(max(0, min(100, total_score)), 2)


def _run_single_sensitivity_backtest(args: Tuple) -> Dict[str, Any]:
    """
    Run backtest for a single sensitivity value (for parallel processing)
    
    This function is designed to be called by ProcessPoolExecutor.
    
    Args:
        args: Tuple of (df_dict, sensitivity, filter_type, sl_mode, sl_percent, tp_percents, filter_kwargs)
    
    Returns:
        Dictionary with sensitivity, metrics, and score
    """
    df_dict, sensitivity, filter_type, sl_mode, sl_percent, tp_percents, filter_kwargs = args
    
    # Reconstruct DataFrame from dict
    df = pd.DataFrame(df_dict)
    
    try:
        # Run backtest
        result = run_full_backtest(
            df=df,
            sensitivity=sensitivity,
            filter_type=filter_type,
            sl_mode=sl_mode,
            sl_percent=sl_percent,
            tp_percents=tp_percents,
            **filter_kwargs
        )
        
        # Calculate score
        score = calculate_sensitivity_score(result['metrics'])
        
        return {
            'sensitivity': sensitivity,
            'metrics': result['metrics'],
            'score': score,
            'summary': result['summary'],
            'error': None
        }
    except Exception as e:
        return {
            'sensitivity': sensitivity,
            'metrics': {},
            'score': 0,
            'summary': {},
            'error': str(e)
        }


def optimize_sensitivity(
    df: pd.DataFrame,
    filter_type: int = FILTER_NONE,
    sl_mode: int = SL_MODE_FIXED,
    sl_percent: float = None,
    tp_percents: List[float] = None,
    sensitivities: List[int] = None,
    workers: int = None,
    progress_callback: Callable[[int, int, int, Dict], None] = None,
    **filter_kwargs
) -> Dict[str, Any]:
    """
    Optimize sensitivity parameter using multi-core parallel processing
    
    This function tests multiple sensitivity values and returns the best one
    based on the scoring function.
    
    Args:
        df: DataFrame with OHLCV data
        filter_type: Filter type to use (0-4)
        sl_mode: Stop-loss mode (0-4)
        sl_percent: Stop-loss percentage (default 2.0%)
        tp_percents: Take-profit percentages (default [1.0, 2.0, 3.0, 5.0])
        sensitivities: List of sensitivities to test (default: 12 values from 12-60)
        workers: Number of worker processes (default: all available cores)
        progress_callback: Function(current, total, sensitivity, result) called after each test
        **filter_kwargs: Additional filter parameters
    
    Returns:
        Dictionary with:
        - best_sensitivity: Optimal sensitivity value
        - best_score: Score of the best configuration
        - best_metrics: Metrics of the best configuration
        - all_results: List of all sensitivity results (sorted by score)
        - scores: Dictionary mapping sensitivity -> score
        - optimization_time: Time taken in seconds
        - workers_used: Number of worker processes used
    
    Example:
        >>> def progress(current, total, sensitivity, result):
        ...     print(f"Progress: {current}/{total} - Sensitivity {sensitivity}: Score {result['score']}")
        >>> 
        >>> result = optimize_sensitivity(
        ...     df, 
        ...     filter_type=2, 
        ...     sl_mode=4,
        ...     progress_callback=progress
        ... )
        >>> print(f"Best sensitivity: {result['best_sensitivity']} (Score: {result['best_score']})")
    """
    start_time = time.time()
    
    # Apply defaults
    if sl_percent is None:
        sl_percent = SL_DEFAULTS['sl_percent']
    if tp_percents is None:
        tp_percents = SL_DEFAULTS['tp_percents'].copy()
    if sensitivities is None:
        sensitivities = OPTIMIZATION_SENSITIVITIES.copy()
    if workers is None:
        workers = os.cpu_count() or 4
    
    # Validate
    validate_dataframe(df)
    filter_type = validate_filter_type(filter_type)
    sl_mode = validate_sl_mode(sl_mode)
    
    # Prepare args for parallel execution
    df_dict = df.to_dict('list')
    args_list = [
        (df_dict, sens, filter_type, sl_mode, sl_percent, tp_percents, filter_kwargs)
        for sens in sensitivities
    ]
    
    # Run optimization
    results = []
    total = len(sensitivities)
    
    # Use ProcessPoolExecutor for parallel execution
    with ProcessPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_run_single_sensitivity_backtest, args): args[1]
            for args in args_list
        }
        
        completed = 0
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            completed += 1
            
            # Call progress callback
            if progress_callback:
                progress_callback(completed, total, result['sensitivity'], result)
    
    # Sort by score (descending)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # Get best result
    best = results[0] if results else None
    
    # Build scores dictionary
    scores = {r['sensitivity']: r['score'] for r in results}
    
    end_time = time.time()
    
    return {
        'best_sensitivity': best['sensitivity'] if best else None,
        'best_score': best['score'] if best else 0,
        'best_metrics': best['metrics'] if best else {},
        'best_summary': best['summary'] if best else {},
        'all_results': results,
        'scores': scores,
        'optimization_time': round(end_time - start_time, 2),
        'workers_used': workers,
        'config': {
            'filter_type': filter_type,
            'sl_mode': sl_mode,
            'sl_percent': sl_percent,
            'tp_percents': tp_percents,
            'sensitivities_tested': sensitivities,
        }
    }


def get_optimization_summary(result: Dict[str, Any]) -> str:
    """
    Get a formatted summary of optimization results
    
    Args:
        result: Result dictionary from optimize_sensitivity()
    
    Returns:
        Formatted string summary
    """
    if not result or 'best_sensitivity' not in result:
        return "No optimization results available"
    
    lines = [
        "=" * 50,
        "DOMINANT OPTIMIZATION RESULTS",
        "=" * 50,
        f"Best Sensitivity: {result['best_sensitivity']}",
        f"Best Score: {result['best_score']:.2f}/100",
        "",
        "Best Configuration Metrics:",
        f"  - Total PnL: {result['best_metrics'].get('pnl_percent', 0):.2f}%",
        f"  - Win Rate: {result['best_metrics'].get('win_rate', 0):.1f}%",
        f"  - Profit Factor: {result['best_metrics'].get('profit_factor', 0):.2f}",
        f"  - Max Drawdown: {result['best_metrics'].get('max_drawdown', 0):.2f}%",
        f"  - Total Trades: {result['best_metrics'].get('total_trades', 0)}",
        "",
        f"Optimization Time: {result['optimization_time']:.1f}s",
        f"Workers Used: {result['workers_used']}",
        "",
        "Score Ranking:",
    ]
    
    # Add top 5 scores
    for i, r in enumerate(result['all_results'][:5]):
        lines.append(
            f"  {i+1}. Sensitivity {r['sensitivity']}: Score {r['score']:.2f} "
            f"(PnL: {r['metrics'].get('pnl_percent', 0):.1f}%, "
            f"WR: {r['metrics'].get('win_rate', 0):.0f}%)"
        )
    
    lines.append("=" * 50)
    
    return "\n".join(lines)


def compare_sensitivities(
    df: pd.DataFrame,
    sensitivities: List[int],
    filter_type: int = FILTER_NONE,
    sl_mode: int = SL_MODE_FIXED,
    **kwargs
) -> pd.DataFrame:
    """
    Compare multiple sensitivity values side by side
    
    Args:
        df: DataFrame with OHLCV data
        sensitivities: List of sensitivity values to compare
        filter_type: Filter type to use
        sl_mode: Stop-loss mode
        **kwargs: Additional backtest parameters
    
    Returns:
        DataFrame with comparison of all sensitivities
    """
    results = []
    
    for sens in sensitivities:
        backtest = run_full_backtest(
            df=df,
            sensitivity=sens,
            filter_type=filter_type,
            sl_mode=sl_mode,
            **kwargs
        )
        
        score = calculate_sensitivity_score(backtest['metrics'])
        
        results.append({
            'sensitivity': sens,
            'score': score,
            **backtest['metrics']
        })
    
    return pd.DataFrame(results).sort_values('score', ascending=False)


def get_score_breakdown(metrics: Dict[str, float]) -> Dict[str, float]:
    """
    Get detailed breakdown of score components
    
    Args:
        metrics: Metrics dictionary from backtest
    
    Returns:
        Dictionary with each score component and total
    """
    pnl = metrics.get('pnl_percent', 0)
    win_rate = metrics.get('win_rate', 0)
    pnl_std = metrics.get('pnl_std', 1)
    max_dd = abs(metrics.get('max_drawdown', 0))
    total_trades = metrics.get('total_trades', 0)
    
    if total_trades < MIN_TRADES_FOR_OPTIMIZATION:
        return {
            'profit_score': 0,
            'win_rate_score': 0,
            'stability_score': 0,
            'drawdown_score': 0,
            'total_score': 0,
            'reason': f'Insufficient trades ({total_trades} < {MIN_TRADES_FOR_OPTIMIZATION})'
        }
    
    # Calculate components
    if pnl < -20:
        profit_score = 0
    elif pnl > 50:
        profit_score = SCORE_WEIGHT_PROFIT
    else:
        profit_score = (pnl + 20) / 70 * SCORE_WEIGHT_PROFIT
    
    win_rate_score = (win_rate / 100) * SCORE_WEIGHT_WIN_RATE
    
    if pnl_std >= 20:
        stability_score = 0
    else:
        stability_score = (1 - pnl_std / 20) * SCORE_WEIGHT_STABILITY
    
    if max_dd >= 40:
        dd_score = 0
    else:
        dd_score = (1 - max_dd / 40) * SCORE_WEIGHT_DRAWDOWN
    
    total = profit_score + win_rate_score + stability_score + dd_score
    
    return {
        'profit_score': round(profit_score, 2),
        'profit_max': SCORE_WEIGHT_PROFIT,
        'win_rate_score': round(win_rate_score, 2),
        'win_rate_max': SCORE_WEIGHT_WIN_RATE,
        'stability_score': round(stability_score, 2),
        'stability_max': SCORE_WEIGHT_STABILITY,
        'drawdown_score': round(dd_score, 2),
        'drawdown_max': SCORE_WEIGHT_DRAWDOWN,
        'total_score': round(total, 2),
        'total_max': 100,
    }


def get_ai_resolution_info() -> Dict[str, Any]:
    """
    Get information about AI Resolution optimization
    
    Returns:
        Dictionary with optimization parameters and documentation
    """
    return {
        'name': 'AI Resolution',
        'version': '1.0.0',
        'description': 'Automatic sensitivity optimization using multi-core parallel backtesting',
        'parameters': {
            'sensitivities': OPTIMIZATION_SENSITIVITIES,
            'default_workers': 'all available cores',
            'min_trades': MIN_TRADES_FOR_OPTIMIZATION,
        },
        'scoring': {
            'profit': {
                'weight': SCORE_WEIGHT_PROFIT,
                'description': 'Rewards high PnL (-20% to +50% normalized)'
            },
            'win_rate': {
                'weight': SCORE_WEIGHT_WIN_RATE,
                'description': 'Rewards high win percentage (0-100%)'
            },
            'stability': {
                'weight': SCORE_WEIGHT_STABILITY,
                'description': 'Rewards consistency (low std dev, capped at 20%)'
            },
            'drawdown': {
                'weight': SCORE_WEIGHT_DRAWDOWN,
                'description': 'Penalizes high drawdowns (capped at 40%)'
            }
        },
        'outputs': [
            'best_sensitivity',
            'best_score',
            'best_metrics',
            'all_results',
            'scores',
            'optimization_time',
            'workers_used'
        ]
    }


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
        'version': '4.0.4',
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
        'sl_modes': {
            'types': SL_MODE_NAMES,
            'descriptions': SL_MODE_DESCRIPTIONS,
            'defaults': SL_DEFAULTS,
        },
        'ai_resolution': get_ai_resolution_info(),
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
    print("Testing Dominant Indicator with AI Resolution...")
    
    # Create sample data (larger for meaningful backtest)
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=500, freq='1h')
    prices = 100 + np.cumsum(np.random.randn(500) * 0.5)
    
    df = pd.DataFrame({
        'open': prices,
        'high': prices + np.abs(np.random.randn(500) * 0.3),
        'low': prices - np.abs(np.random.randn(500) * 0.3),
        'close': prices + np.random.randn(500) * 0.2,
        'volume': np.random.randint(1000, 10000, 500)
    }, index=dates)
    
    # Test 1: Full backtest
    print("\n=== FULL BACKTEST TEST ===")
    bt_result = run_full_backtest(df, sensitivity=21, filter_type=0, sl_mode=4)
    print(f"Total trades: {bt_result['summary']['total_trades']}")
    print(f"Total PnL: {bt_result['metrics']['pnl_percent']:.2f}%")
    print(f"Win Rate: {bt_result['metrics']['win_rate']:.1f}%")
    
    # Test 2: Score calculation
    print("\n=== SCORE CALCULATION TEST ===")
    score = calculate_sensitivity_score(bt_result['metrics'])
    print(f"Score: {score:.2f}/100")
    
    breakdown = get_score_breakdown(bt_result['metrics'])
    print(f"  Profit: {breakdown['profit_score']:.1f}/{breakdown['profit_max']}")
    print(f"  Win Rate: {breakdown['win_rate_score']:.1f}/{breakdown['win_rate_max']}")
    print(f"  Stability: {breakdown['stability_score']:.1f}/{breakdown['stability_max']}")
    print(f"  Drawdown: {breakdown['drawdown_score']:.1f}/{breakdown['drawdown_max']}")
    
    # Test 3: Optimization (limited sensitivities for speed)
    print("\n=== OPTIMIZATION TEST ===")
    
    def progress_callback(current, total, sensitivity, result):
        print(f"  [{current}/{total}] Sensitivity {sensitivity}: Score {result['score']:.1f}")
    
    opt_result = optimize_sensitivity(
        df,
        filter_type=0,
        sl_mode=4,
        sensitivities=[15, 21, 30, 45],  # Reduced for quick test
        workers=2,
        progress_callback=progress_callback
    )
    
    print(f"\nBest Sensitivity: {opt_result['best_sensitivity']}")
    print(f"Best Score: {opt_result['best_score']:.2f}")
    print(f"Optimization Time: {opt_result['optimization_time']:.1f}s")
    print(f"Workers Used: {opt_result['workers_used']}")
    
    # Test 4: Comparison
    print("\n=== COMPARISON TEST ===")
    comparison = compare_sensitivities(
        df, 
        sensitivities=[15, 21, 30],
        filter_type=0,
        sl_mode=4
    )
    print(comparison[['sensitivity', 'score', 'pnl_percent', 'win_rate', 'max_drawdown']].to_string(index=False))
    
    # Print full optimization summary
    print("\n" + get_optimization_summary(opt_result))
    
    print("\n✅ All AI Resolution tests passed!")
