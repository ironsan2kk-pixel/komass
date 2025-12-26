"""
TRG Signal Generator
====================
Signal generation for TRG indicator with filter support.

Author: Komas Trading System
Version: 1.0.0
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS
# ============================================================================

class SignalType(int, Enum):
    """Trading signal types"""
    LONG = 1
    NONE = 0
    SHORT = -1


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class SignalResult:
    """Result of signal generation"""
    
    signal: SignalType
    timestamp: Any = None
    price: float = 0.0
    trend: int = 0
    
    # Filter states
    supertrend_ok: bool = True
    rsi_ok: bool = True
    adx_ok: bool = True
    volume_ok: bool = True
    
    @property
    def all_filters_passed(self) -> bool:
        """Check if all filters passed"""
        return self.supertrend_ok and self.rsi_ok and self.adx_ok and self.volume_ok
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "signal": self.signal.value,
            "timestamp": str(self.timestamp) if self.timestamp else None,
            "price": self.price,
            "trend": self.trend,
            "filters": {
                "supertrend": self.supertrend_ok,
                "rsi": self.rsi_ok,
                "adx": self.adx_ok,
                "volume": self.volume_ok
            }
        }


# ============================================================================
# TRG SIGNAL GENERATOR
# ============================================================================

class TRGSignalGenerator:
    """
    Signal generator for TRG indicator.
    
    Generates entry signals based on TRG trend changes with optional filters:
    - SuperTrend filter
    - RSI filter
    - ADX filter
    - Volume filter
    """
    
    def __init__(self):
        """Initialize signal generator"""
        self.last_signal: Optional[SignalResult] = None
    
    def generate_signals(
        self,
        df: pd.DataFrame,
        settings: Optional[Any] = None
    ) -> pd.DataFrame:
        """
        Generate entry signals on DataFrame with TRG data.
        
        Args:
            df: DataFrame with TRG indicator columns
            settings: Optional settings (dict or object with filter settings)
            
        Returns:
            DataFrame with 'signal' column added
        """
        # Make copy
        df = df.copy()
        
        # Validate TRG data exists
        if 'trg_trend' not in df.columns:
            raise ValueError("DataFrame must have 'trg_trend' column. Run TRGIndicator.calculate() first.")
        
        # Initialize signal column
        df['signal'] = 0
        
        # Detect trend changes
        trend_change_long = (df['trg_trend'] == 1) & (df['trg_trend'].shift(1) == -1)
        trend_change_short = (df['trg_trend'] == -1) & (df['trg_trend'].shift(1) == 1)
        
        # Debug counts
        long_count = trend_change_long.sum()
        short_count = trend_change_short.sum()
        logger.debug(f"Trend changes detected: long={long_count}, short={short_count}")
        
        # Apply filters if settings provided
        long_filter = pd.Series(True, index=df.index)
        short_filter = pd.Series(True, index=df.index)
        
        if settings is not None:
            # Convert to dict if needed
            if hasattr(settings, 'model_dump'):
                cfg = settings.model_dump()
            elif hasattr(settings, '__dict__'):
                cfg = vars(settings)
            else:
                cfg = dict(settings) if settings else {}
            
            # SuperTrend filter
            if cfg.get('use_supertrend', False) and 'supertrend_dir' in df.columns:
                long_filter &= df['supertrend_dir'] == 1
                short_filter &= df['supertrend_dir'] == -1
            
            # RSI filter
            if cfg.get('use_rsi_filter', False) and 'rsi' in df.columns:
                rsi_ob = cfg.get('rsi_overbought', 70)
                rsi_os = cfg.get('rsi_oversold', 30)
                long_filter &= df['rsi'] < rsi_ob
                short_filter &= df['rsi'] > rsi_os
            
            # ADX filter
            if cfg.get('use_adx_filter', False) and 'adx' in df.columns:
                adx_thresh = cfg.get('adx_threshold', 25)
                long_filter &= df['adx'] > adx_thresh
                short_filter &= df['adx'] > adx_thresh
            
            # Volume filter
            if cfg.get('use_volume_filter', False) and 'volume' in df.columns:
                vol_period = cfg.get('volume_ma_period', 20)
                vol_thresh = cfg.get('volume_threshold', 1.5)
                vol_ma = df['volume'].rolling(vol_period).mean()
                long_filter &= df['volume'] > vol_ma * vol_thresh
                short_filter &= df['volume'] > vol_ma * vol_thresh
        
        # Apply signals with filters
        df.loc[trend_change_long & long_filter, 'signal'] = 1
        df.loc[trend_change_short & short_filter, 'signal'] = -1
        
        # Debug final counts
        final_long = (df['signal'] == 1).sum()
        final_short = (df['signal'] == -1).sum()
        logger.debug(f"Final signals: long={final_long}, short={final_short}")
        
        return df
    
    def count_signals(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Count signals in DataFrame.
        
        Args:
            df: DataFrame with 'signal' column
            
        Returns:
            Dictionary with signal counts
        """
        if 'signal' not in df.columns:
            return {"long": 0, "short": 0, "total": 0}
        
        long_count = (df['signal'] == 1).sum()
        short_count = (df['signal'] == -1).sum()
        
        return {
            "long": int(long_count),
            "short": int(short_count),
            "total": int(long_count + short_count)
        }
    
    def get_current_signal(self, df: pd.DataFrame) -> SignalResult:
        """
        Get the current (last) signal from DataFrame.
        
        Args:
            df: DataFrame with TRG and signal data
            
        Returns:
            SignalResult for the last bar
        """
        if df is None or len(df) == 0:
            return SignalResult(signal=SignalType.NONE)
        
        last_row = df.iloc[-1]
        
        # Get signal value
        signal_value = int(last_row.get('signal', 0))
        signal_type = SignalType(signal_value) if signal_value in [-1, 0, 1] else SignalType.NONE
        
        result = SignalResult(
            signal=signal_type,
            timestamp=df.index[-1],
            price=float(last_row.get('close', 0)),
            trend=int(last_row.get('trg_trend', 0))
        )
        
        self.last_signal = result
        return result
    
    def get_signals_list(
        self,
        df: pd.DataFrame,
        limit: int = 100
    ) -> List[SignalResult]:
        """
        Get list of all signals from DataFrame.
        
        Args:
            df: DataFrame with signals
            limit: Maximum number of signals to return
            
        Returns:
            List of SignalResult objects
        """
        signals = []
        
        if 'signal' not in df.columns:
            return signals
        
        # Find rows with signals
        signal_mask = df['signal'] != 0
        signal_rows = df[signal_mask].tail(limit)
        
        for idx, row in signal_rows.iterrows():
            signal_type = SignalType(int(row['signal']))
            signals.append(SignalResult(
                signal=signal_type,
                timestamp=idx,
                price=float(row.get('close', 0)),
                trend=int(row.get('trg_trend', 0))
            ))
        
        return signals


# ============================================================================
# FILTER CALCULATORS
# ============================================================================

def calculate_supertrend(
    df: pd.DataFrame,
    period: int = 10,
    multiplier: float = 3.0
) -> pd.DataFrame:
    """
    Calculate SuperTrend indicator.
    
    Args:
        df: DataFrame with OHLCV data
        period: ATR period
        multiplier: ATR multiplier
        
    Returns:
        DataFrame with SuperTrend columns added
    """
    df = df.copy()
    
    # Calculate ATR
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    
    # Calculate basic bands
    hl2 = (high + low) / 2
    upper_basic = hl2 + multiplier * atr
    lower_basic = hl2 - multiplier * atr
    
    # Calculate final bands
    n = len(df)
    upper = np.zeros(n)
    lower = np.zeros(n)
    direction = np.zeros(n)
    
    upper[0] = upper_basic.iloc[0]
    lower[0] = lower_basic.iloc[0]
    direction[0] = 1
    
    for i in range(1, n):
        # Upper band
        if upper_basic.iloc[i] < upper[i-1] or close.iloc[i-1] > upper[i-1]:
            upper[i] = upper_basic.iloc[i]
        else:
            upper[i] = upper[i-1]
        
        # Lower band
        if lower_basic.iloc[i] > lower[i-1] or close.iloc[i-1] < lower[i-1]:
            lower[i] = lower_basic.iloc[i]
        else:
            lower[i] = lower[i-1]
        
        # Direction
        if direction[i-1] == 1:
            if close.iloc[i] < lower[i]:
                direction[i] = -1
            else:
                direction[i] = 1
        else:
            if close.iloc[i] > upper[i]:
                direction[i] = 1
            else:
                direction[i] = -1
    
    df['supertrend_upper'] = upper
    df['supertrend_lower'] = lower
    df['supertrend_dir'] = direction
    df['supertrend'] = np.where(direction == 1, lower, upper)
    
    return df


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate RSI indicator.
    
    Args:
        df: DataFrame with close prices
        period: RSI period
        
    Returns:
        DataFrame with RSI column added
    """
    df = df.copy()
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    return df


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Calculate ADX indicator.
    
    Args:
        df: DataFrame with OHLCV data
        period: ADX period
        
    Returns:
        DataFrame with ADX column added
    """
    df = df.copy()
    
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


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'SignalType',
    'SignalResult',
    'TRGSignalGenerator',
    'calculate_supertrend',
    'calculate_rsi',
    'calculate_adx',
]
