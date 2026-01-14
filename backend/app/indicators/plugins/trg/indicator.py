"""
TRG Indicator
=============
TRG (Trend-following Range) indicator implementation.
ATR-based trend detection with long/short levels.

Refactored to inherit from BaseIndicator.

Author: Komas Trading System
Version: 2.0.0
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import pandas as pd
import numpy as np
import logging

from ...base.indicator import BaseIndicator, IndicatorParameter, SignalType

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
# TRG INDICATOR (BaseIndicator)
# ============================================================================

class TRGIndicator(BaseIndicator):
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
        - signal: Trading signal (1=long, -1=short, 0=none)
    """

    # Default parameters
    DEFAULT_ATR_LENGTH = 45
    DEFAULT_MULTIPLIER = 4.0

    # Parameter ranges
    ATR_LENGTH_RANGE = (10, 200)
    MULTIPLIER_RANGE = (1.0, 10.0)

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """Initialize TRG indicator with BaseIndicator interface."""
        super().__init__(params)

        # For backward compatibility
        self.atr_length = self._params.get('atr_length', self.DEFAULT_ATR_LENGTH)
        self.multiplier = self._params.get('multiplier', self.DEFAULT_MULTIPLIER)

    # ==================== ABSTRACT METHOD IMPLEMENTATIONS ====================

    def get_id(self) -> str:
        """Return unique indicator identifier."""
        return "trg"

    def get_name(self) -> str:
        """Return human-readable indicator name."""
        return "TRG Indicator"

    def get_parameters(self) -> List[IndicatorParameter]:
        """Return list of configurable parameters."""
        return [
            IndicatorParameter(
                name="atr_length",
                display_name="ATR Length (i1)",
                param_type="int",
                default=self.DEFAULT_ATR_LENGTH,
                min_value=self.ATR_LENGTH_RANGE[0],
                max_value=self.ATR_LENGTH_RANGE[1],
                step=1,
                description="ATR period for TRG calculation",
                group="main"
            ),
            IndicatorParameter(
                name="multiplier",
                display_name="Multiplier (i2)",
                param_type="float",
                default=self.DEFAULT_MULTIPLIER,
                min_value=self.MULTIPLIER_RANGE[0],
                max_value=self.MULTIPLIER_RANGE[1],
                step=0.5,
                description="ATR multiplier for band width",
                group="main"
            )
        ]

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate TRG indicator on DataFrame.

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)

        Returns:
            DataFrame with indicator columns added
        """
        atr_len = self._params.get('atr_length', self.atr_length)
        mult = self._params.get('multiplier', self.multiplier)

        # Make a copy to avoid modifying original
        df = df.copy()

        # Validate input
        is_valid, error = self.validate_data(df)
        if not is_valid:
            raise ValueError(error)

        # Calculate ATR
        df['trg_atr'] = self._calculate_atr(df, atr_len)

        # Calculate TRG levels and trend
        df = self._calculate_trend(df, mult)

        logger.debug(f"TRG calculated: atr_length={atr_len}, multiplier={mult}, bars={len(df)}")

        return df

    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on TRG trend changes.

        Args:
            df: DataFrame with calculated TRG columns

        Returns:
            DataFrame with 'signal' column added
        """
        df = df.copy()

        if 'trg_trend' not in df.columns:
            df = self.calculate(df)

        # Generate signals on trend change
        df['signal'] = 0
        trend_change = df['trg_trend'].diff()

        # Long signal when trend changes from -1 to 1 (change = 2)
        df.loc[trend_change == 2, 'signal'] = SignalType.LONG.value

        # Short signal when trend changes from 1 to -1 (change = -2)
        df.loc[trend_change == -2, 'signal'] = SignalType.SHORT.value

        return df

    # ==================== OPTIONAL OVERRIDES ====================

    def get_description(self) -> str:
        """Return indicator description."""
        return "ATR-based trend indicator with dynamic support/resistance levels"

    def get_version(self) -> str:
        """Return indicator version."""
        return "2.0.0"

    def warmup_period(self) -> int:
        """Return number of candles needed before indicator is valid."""
        return max(self._params.get('atr_length', self.DEFAULT_ATR_LENGTH) + 10, 50)

    def get_chart_config(self) -> Dict[str, Any]:
        """Return chart visualization configuration."""
        return {
            "overlays": True,  # Draw on price chart
            "lines": [
                {"name": "long_level", "color": "#22c55e", "width": 1, "style": "solid"},
                {"name": "short_level", "color": "#ef4444", "width": 1, "style": "solid"}
            ],
            "bands": [],
            "signals": {
                "long": {"marker": "triangle_up", "color": "#22c55e"},
                "short": {"marker": "triangle_down", "color": "#ef4444"}
            }
        }

    # ==================== INTERNAL METHODS ====================

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

        # ATR = EMA of True Range
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
                if close[i] < long_level[i-1]:
                    trend[i] = -1
                else:
                    trend[i] = 1
            else:
                if close[i] > short_level[i-1]:
                    trend[i] = 1
                else:
                    trend[i] = -1

        # Add to DataFrame
        df['trg_trend'] = trend
        df['long_level'] = long_level
        df['short_level'] = short_level

        return df

    # ==================== BACKWARD COMPATIBILITY ====================

    def set_parameters(self, **kwargs):
        """Set parameters (backward compatibility)"""
        if 'atr_length' in kwargs:
            self.atr_length = int(kwargs['atr_length'])
            self._params['atr_length'] = self.atr_length
        if 'multiplier' in kwargs:
            self.multiplier = float(kwargs['multiplier'])
            self._params['multiplier'] = self.multiplier

    @classmethod
    def get_parameter_info(cls) -> List[Dict[str, Any]]:
        """Get parameter definitions for UI schema (backward compatibility)"""
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
    indicator = TRGIndicator({'atr_length': atr_length, 'multiplier': multiplier})
    return indicator.calculate(df)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    'TRGIndicator',
    'TRGIndicatorResult',
    'calculate_trg',
]
