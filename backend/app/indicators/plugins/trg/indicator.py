"""
TRG Indicator
=============
TRG (Trend-following Range) indicator implementation.
ATR-based trend detection with long/short levels.

Author: Komas Trading System
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TRGIndicatorResult:
    """Result of TRG indicator calculation"""
    
    df: pd.DataFrame  # DataFrame with indicator columns
    atr_length: int
    multiplier: float
    
    # Statistics
    long_signals: int = 0
    short_signals: int = 0
    total_bars: int = 0
    
    def __post_init__(self):
        if self.df is not None and len(self.df) > 0:
            self.total_bars = len(self.df)
            if 'trg_trend' in self.df.columns:
                trend_changes = self.df['trg_trend'].diff()
                self.long_signals = (trend_changes == 2).sum()  # -1 to 1
                self.short_signals = (trend_changes == -2).sum()  # 1 to -1


# ============================================================================
# TRG INDICATOR
# ============================================================================

class TRGIndicator:
    """
    TRG (Trend-following Range) Indicator.
    
    Uses ATR-based bands to determine trend direction:
    - Long when price closes above upper band
    - Short when price closes below lower band
    
    Parameters:
        atr_length: ATR period (default: 45)
        multiplier: ATR multiplier for band width (default: 4.0)
    
    Output columns added to DataFrame:
        - trg_atr: ATR value
        - trg_trend: Trend direction (1=long, -1=short)
        - long_level: Long entry level
        - short_level: Short entry level
    """
    
    # Default parameters
    DEFAULT_ATR_LENGTH = 45
    DEFAULT_MULTIPLIER = 4.0
    
    # Parameter ranges
    ATR_LENGTH_RANGE = (10, 200)
    MULTIPLIER_RANGE = (1.0, 10.0)
    
    def __init__(
        self,
        atr_length: int = DEFAULT_ATR_LENGTH,
        multiplier: float = DEFAULT_MULTIPLIER
    ):
        """
        Initialize TRG indicator.
        
        Args:
            atr_length: ATR period
            multiplier: ATR multiplier
        """
        self.atr_length = atr_length
        self.multiplier = multiplier
        
        # Validate parameters
        if not self.ATR_LENGTH_RANGE[0] <= atr_length <= self.ATR_LENGTH_RANGE[1]:
            logger.warning(f"ATR length {atr_length} outside range {self.ATR_LENGTH_RANGE}")
        if not self.MULTIPLIER_RANGE[0] <= multiplier <= self.MULTIPLIER_RANGE[1]:
            logger.warning(f"Multiplier {multiplier} outside range {self.MULTIPLIER_RANGE}")
    
    def calculate(
        self,
        df: pd.DataFrame,
        atr_length: Optional[int] = None,
        multiplier: Optional[float] = None
    ) -> pd.DataFrame:
        """
        Calculate TRG indicator on DataFrame.
        
        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
            atr_length: Override ATR period
            multiplier: Override multiplier
            
        Returns:
            DataFrame with indicator columns added
        """
        # Use instance values if not overridden
        atr_len = atr_length if atr_length is not None else self.atr_length
        mult = multiplier if multiplier is not None else self.multiplier
        
        # Make a copy to avoid modifying original
        df = df.copy()
        
        # Validate input
        required_columns = ['high', 'low', 'close']
        missing = [col for col in required_columns if col not in df.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        
        if len(df) < atr_len:
            logger.warning(f"DataFrame has {len(df)} rows, less than ATR length {atr_len}")
        
        # Calculate ATR
        df['trg_atr'] = self._calculate_atr(df, atr_len)
        
        # Calculate TRG levels and trend
        df = self._calculate_trend(df, mult)
        
        logger.debug(f"TRG calculated: atr_length={atr_len}, multiplier={mult}, bars={len(df)}")
        
        return df
    
    def _calculate_atr(self, df: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range components
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        
        # True Range = max of the three
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # ATR = SMA of True Range (using EMA for smoother results)
        atr = tr.ewm(span=period, adjust=False).mean()
        
        return atr
    
    def _calculate_trend(self, df: pd.DataFrame, multiplier: float) -> pd.DataFrame:
        """Calculate TRG trend direction and levels"""
        
        close = df['close'].values
        atr = df['trg_atr'].values
        
        n = len(df)
        
        # Initialize arrays
        trend = np.zeros(n, dtype=int)
        long_level = np.zeros(n)
        short_level = np.zeros(n)
        
        # Initial values
        trend[0] = 1  # Start with long trend
        long_level[0] = close[0] - atr[0] * multiplier
        short_level[0] = close[0] + atr[0] * multiplier
        
        # Calculate trend for each bar
        for i in range(1, n):
            # Calculate potential levels
            up = close[i] - atr[i] * multiplier
            dn = close[i] + atr[i] * multiplier
            
            # Long level: maximum of previous long level and new up
            if trend[i-1] == 1:
                long_level[i] = max(long_level[i-1], up)
            else:
                long_level[i] = up
            
            # Short level: minimum of previous short level and new down
            if trend[i-1] == -1:
                short_level[i] = min(short_level[i-1], dn)
            else:
                short_level[i] = dn
            
            # Determine trend
            if trend[i-1] == 1:
                # In uptrend - switch to downtrend if close below long level
                if close[i] < long_level[i-1]:
                    trend[i] = -1
                else:
                    trend[i] = 1
            else:
                # In downtrend - switch to uptrend if close above short level
                if close[i] > short_level[i-1]:
                    trend[i] = 1
                else:
                    trend[i] = -1
        
        # Add to DataFrame
        df['trg_trend'] = trend
        df['long_level'] = long_level
        df['short_level'] = short_level
        
        return df
    
    def get_parameters(self) -> Dict[str, Any]:
        """Get current parameter values"""
        return {
            "atr_length": self.atr_length,
            "multiplier": self.multiplier
        }
    
    def set_parameters(self, **kwargs):
        """Set parameters"""
        if 'atr_length' in kwargs:
            self.atr_length = int(kwargs['atr_length'])
        if 'multiplier' in kwargs:
            self.multiplier = float(kwargs['multiplier'])
    
    @classmethod
    def get_parameter_info(cls) -> List[Dict[str, Any]]:
        """Get parameter definitions for UI schema"""
        return [
            {
                "name": "atr_length",
                "type": "int",
                "default": cls.DEFAULT_ATR_LENGTH,
                "min": cls.ATR_LENGTH_RANGE[0],
                "max": cls.ATR_LENGTH_RANGE[1],
                "step": 1,
                "description": "ATR period for TRG calculation",
                "ui_name": "ATR Length (i1)"
            },
            {
                "name": "multiplier",
                "type": "float",
                "default": cls.DEFAULT_MULTIPLIER,
                "min": cls.MULTIPLIER_RANGE[0],
                "max": cls.MULTIPLIER_RANGE[1],
                "step": 0.5,
                "description": "ATR multiplier for band width",
                "ui_name": "Multiplier (i2)"
            }
        ]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_trg(
    df: pd.DataFrame,
    atr_length: int = TRGIndicator.DEFAULT_ATR_LENGTH,
    multiplier: float = TRGIndicator.DEFAULT_MULTIPLIER
) -> pd.DataFrame:
    """
    Convenience function to calculate TRG indicator.
    
    Args:
        df: DataFrame with OHLCV data
        atr_length: ATR period
        multiplier: ATR multiplier
        
    Returns:
        DataFrame with TRG columns added
    """
    indicator = TRGIndicator(atr_length, multiplier)
    return indicator.calculate(df)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'TRGIndicator',
    'TRGIndicatorResult',
    'calculate_trg',
]
