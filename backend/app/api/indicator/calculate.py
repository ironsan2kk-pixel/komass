"""
Indicator Calculations
======================
Technical indicator calculation functions.
"""
import numpy as np
import pandas as pd
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import IndicatorSettings


def calculate_trg(df: pd.DataFrame, atr_length: int, multiplier: float) -> pd.DataFrame:
    """Calculate TRG indicator (ATR-based trend detection)"""

    high = df['high']
    low = df['low']
    close = df['close']

    # True Range
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # RMA (Wilder's smoothing) for ATR
    atr = tr.ewm(alpha=1/atr_length, adjust=False).mean()

    # Bands
    hl2 = (high + low) / 2
    df['trg_upper'] = hl2 + (multiplier * atr)
    df['trg_lower'] = hl2 - (multiplier * atr)
    df['trg_atr'] = atr

    # Trend direction
    df['trg_trend'] = 0
    trend = 0

    for i in range(1, len(df)):
        prev_upper = df['trg_upper'].iloc[i-1]
        prev_lower = df['trg_lower'].iloc[i-1]
        curr_close = close.iloc[i]

        if curr_close > prev_upper:
            trend = 1
        elif curr_close < prev_lower:
            trend = -1
        # else: keep previous trend

        df.iloc[i, df.columns.get_loc('trg_trend')] = trend

    # TRG line (follows trend)
    df['trg_line'] = np.where(df['trg_trend'] == 1, df['trg_lower'], df['trg_upper'])

    return df


def calculate_supertrend(df: pd.DataFrame, period: int, multiplier: float) -> pd.DataFrame:
    """Calculate SuperTrend indicator"""

    high = df['high']
    low = df['low']
    close = df['close']

    tr = pd.concat([
        high - low,
        abs(high - close.shift(1)),
        abs(low - close.shift(1))
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()

    hl2 = (high + low) / 2
    upper = hl2 + (multiplier * atr)
    lower = hl2 - (multiplier * atr)

    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)

    for i in range(period, len(df)):
        if close.iloc[i] > upper.iloc[i-1]:
            direction.iloc[i] = 1
        elif close.iloc[i] < lower.iloc[i-1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1] if i > period else 1

        if direction.iloc[i] == 1:
            supertrend.iloc[i] = lower.iloc[i]
        else:
            supertrend.iloc[i] = upper.iloc[i]

    df['supertrend'] = supertrend
    df['supertrend_dir'] = direction

    return df


def calculate_rsi(df: pd.DataFrame, period: int) -> pd.DataFrame:
    """Calculate RSI (Relative Strength Index)"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df


def calculate_adx(df: pd.DataFrame, period: int) -> pd.DataFrame:
    """Calculate ADX (Average Directional Index)"""
    high = df['high']
    low = df['low']
    close = df['close']

    plus_dm = high.diff()
    minus_dm = low.diff().abs()

    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)

    tr = pd.concat([
        high - low,
        abs(high - close.shift(1)),
        abs(low - close.shift(1))
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)

    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    df['adx'] = dx.rolling(period).mean()

    return df


def generate_signals(df: pd.DataFrame, settings: "IndicatorSettings") -> pd.DataFrame:
    """Generate entry signals based on indicator and filters"""

    df['signal'] = 0

    # TRG signals (trend change)
    trend_change_long = (df['trg_trend'] == 1) & (df['trg_trend'].shift(1) == -1)
    trend_change_short = (df['trg_trend'] == -1) & (df['trg_trend'].shift(1) == 1)

    # Apply filters
    long_filter = pd.Series(True, index=df.index)
    short_filter = pd.Series(True, index=df.index)

    if settings.use_supertrend and 'supertrend_dir' in df.columns:
        long_filter &= df['supertrend_dir'] == 1
        short_filter &= df['supertrend_dir'] == -1

    if settings.use_rsi_filter and 'rsi' in df.columns:
        long_filter &= df['rsi'] < settings.rsi_overbought
        short_filter &= df['rsi'] > settings.rsi_oversold

    if settings.use_adx_filter and 'adx' in df.columns:
        long_filter &= df['adx'] > settings.adx_threshold
        short_filter &= df['adx'] > settings.adx_threshold

    df.loc[trend_change_long & long_filter, 'signal'] = 1
    df.loc[trend_change_short & short_filter, 'signal'] = -1

    return df


def prepare_indicators(df: pd.DataFrame, settings: "IndicatorSettings") -> pd.DataFrame:
    """Calculate all required indicators based on settings"""

    # Main indicator (TRG)
    df = calculate_trg(df, settings.trg_atr_length, settings.trg_multiplier)

    # Optional filters
    if settings.use_supertrend:
        df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)

    if settings.use_rsi_filter:
        df = calculate_rsi(df, settings.rsi_period)

    if settings.use_adx_filter:
        df = calculate_adx(df, settings.adx_period)

    # Generate signals
    df = generate_signals(df, settings)

    return df
