"""
Komas Trading System - Base Indicator
=====================================
Abstract base class for all trading indicators.
Provides common interface for indicator calculation and signal generation.

Version: 1.0
Author: Komas Team
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np


class SignalType(Enum):
    """Trading signal types"""
    NONE = 0
    LONG = 1
    SHORT = -1
    CLOSE_LONG = 2
    CLOSE_SHORT = -2


class TrendDirection(Enum):
    """Trend direction for indicators"""
    NONE = 0
    UP = 1
    DOWN = -1


@dataclass
class IndicatorParameter:
    """
    Indicator parameter definition.
    Used for UI generation and optimization ranges.
    """
    name: str
    display_name: str
    param_type: str  # "int", "float", "bool", "select"
    default: Any
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    options: Optional[List[Any]] = None  # For "select" type
    description: str = ""
    group: str = "main"  # For UI grouping: "main", "advanced", "filters"
    
    def validate(self, value: Any) -> bool:
        """Validate parameter value"""
        if self.param_type == "int":
            if not isinstance(value, (int, float)):
                return False
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        elif self.param_type == "float":
            if not isinstance(value, (int, float)):
                return False
            if self.min_value is not None and value < self.min_value:
                return False
            if self.max_value is not None and value > self.max_value:
                return False
        elif self.param_type == "bool":
            if not isinstance(value, bool):
                return False
        elif self.param_type == "select":
            if self.options and value not in self.options:
                return False
        return True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API response"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "type": self.param_type,
            "default": self.default,
            "min": self.min_value,
            "max": self.max_value,
            "step": self.step,
            "options": self.options,
            "description": self.description,
            "group": self.group
        }


@dataclass
class IndicatorResult:
    """
    Result of indicator calculation.
    Contains all computed values and signals.
    """
    # Main indicator values (as DataFrame columns)
    values: Dict[str, pd.Series] = field(default_factory=dict)
    
    # Generated signals
    signals: pd.Series = field(default_factory=lambda: pd.Series(dtype=int))
    
    # Trend direction
    trend: pd.Series = field(default_factory=lambda: pd.Series(dtype=int))
    
    # Additional chart data (lines, bands, etc.)
    chart_data: Dict[str, List[Dict]] = field(default_factory=dict)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_signal_at(self, index: int) -> SignalType:
        """Get signal at specific index"""
        if index < 0 or index >= len(self.signals):
            return SignalType.NONE
        value = self.signals.iloc[index]
        try:
            return SignalType(value)
        except ValueError:
            return SignalType.NONE
    
    def get_trend_at(self, index: int) -> TrendDirection:
        """Get trend direction at specific index"""
        if index < 0 or index >= len(self.trend):
            return TrendDirection.NONE
        value = self.trend.iloc[index]
        try:
            return TrendDirection(value)
        except ValueError:
            return TrendDirection.NONE


class BaseIndicator(ABC):
    """
    Abstract base class for all trading indicators.
    
    Subclasses must implement:
    - get_id(): Return unique indicator identifier
    - get_name(): Return display name
    - get_parameters(): Return list of configurable parameters
    - calculate(): Perform indicator calculation
    - generate_signals(): Generate trading signals
    
    Optional overrides:
    - get_description(): Return indicator description
    - get_version(): Return indicator version
    - get_chart_config(): Return chart visualization config
    - validate_data(): Custom data validation
    - warmup_period(): Required warmup candles
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Initialize indicator with parameters.
        
        Args:
            params: Dictionary of parameter values. If None, uses defaults.
        """
        self._params = self._init_params(params or {})
        self._result: Optional[IndicatorResult] = None
        self._calculated = False
    
    def _init_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize parameters with defaults and validation"""
        result = {}
        for param in self.get_parameters():
            if param.name in params:
                value = params[param.name]
                if param.validate(value):
                    result[param.name] = value
                else:
                    # Use default if validation fails
                    result[param.name] = param.default
            else:
                result[param.name] = param.default
        return result
    
    # ==================== ABSTRACT METHODS ====================
    
    @abstractmethod
    def get_id(self) -> str:
        """
        Return unique indicator identifier.
        Used for plugin registry and API routing.
        
        Example: "trg", "supertrend", "rsi_divergence"
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Return human-readable indicator name.
        Used in UI display.
        
        Example: "TRG Indicator", "SuperTrend", "RSI Divergence"
        """
        pass
    
    @abstractmethod
    def get_parameters(self) -> List[IndicatorParameter]:
        """
        Return list of configurable parameters.
        Used for UI generation and optimization.
        
        Example:
        [
            IndicatorParameter("atr_length", "ATR Length", "int", 45, 10, 200, 1),
            IndicatorParameter("multiplier", "Multiplier", "float", 4.0, 1.0, 10.0, 0.5),
        ]
        """
        pass
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicator values.
        
        Args:
            df: OHLCV DataFrame with columns: open, high, low, close, volume
                Index should be DatetimeIndex
        
        Returns:
            DataFrame with added indicator columns
            
        Notes:
            - Should not modify input DataFrame
            - Should handle missing data gracefully
            - Should respect warmup_period()
        """
        pass
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate trading signals based on calculated indicator.
        
        Args:
            df: DataFrame with calculated indicator columns
        
        Returns:
            DataFrame with 'signal' column added
            Signal values: 0 = no signal, 1 = long, -1 = short
        """
        pass
    
    # ==================== OPTIONAL OVERRIDES ====================
    
    def get_description(self) -> str:
        """Return indicator description for UI"""
        return ""
    
    def get_version(self) -> str:
        """Return indicator version"""
        return "1.0.0"
    
    def get_author(self) -> str:
        """Return indicator author"""
        return "Komas Team"
    
    def warmup_period(self) -> int:
        """
        Return number of candles needed before indicator is valid.
        Used to skip initial invalid values in backtest.
        """
        return 50
    
    def validate_data(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Validate input data before calculation.
        
        Args:
            df: Input DataFrame
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        required_columns = ['open', 'high', 'low', 'close']
        missing = [col for col in required_columns if col not in df.columns]
        
        if missing:
            return False, f"Missing required columns: {missing}"
        
        if len(df) < self.warmup_period():
            return False, f"Need at least {self.warmup_period()} candles, got {len(df)}"
        
        return True, ""
    
    def get_chart_config(self) -> Dict[str, Any]:
        """
        Return chart visualization configuration.
        Used by frontend to render indicator on chart.
        
        Returns:
            Dictionary with visualization settings:
            - lines: List of line configurations
            - bands: List of band configurations
            - overlays: Whether to overlay on price chart
        """
        return {
            "overlay": True,  # Overlay on price chart vs separate pane
            "lines": [],      # Line series to draw
            "bands": [],      # Band areas to fill
            "markers": []     # Signal markers
        }
    
    def get_output_columns(self) -> List[str]:
        """
        Return list of column names this indicator adds to DataFrame.
        Used for cleanup and UI display.
        """
        return []
    
    # ==================== PUBLIC API ====================
    
    def run(self, df: pd.DataFrame) -> IndicatorResult:
        """
        Full indicator calculation pipeline.
        
        Args:
            df: OHLCV DataFrame
        
        Returns:
            IndicatorResult with all computed values and signals
        """
        # Validate input
        is_valid, error = self.validate_data(df)
        if not is_valid:
            raise ValueError(f"Invalid data: {error}")
        
        # Calculate indicator
        df_calc = df.copy()
        df_calc = self.calculate(df_calc)
        
        # Generate signals
        df_calc = self.generate_signals(df_calc)
        
        # Build result
        result = IndicatorResult(
            values={col: df_calc[col] for col in self.get_output_columns() if col in df_calc.columns},
            signals=df_calc.get('signal', pd.Series(0, index=df_calc.index)),
            trend=df_calc.get('trend', pd.Series(0, index=df_calc.index)),
            metadata={
                "indicator_id": self.get_id(),
                "indicator_name": self.get_name(),
                "params": self._params.copy(),
                "candles_count": len(df),
                "warmup_period": self.warmup_period()
            }
        )
        
        self._result = result
        self._calculated = True
        
        return result
    
    def get_param(self, name: str, default: Any = None) -> Any:
        """Get parameter value by name"""
        return self._params.get(name, default)
    
    def set_param(self, name: str, value: Any) -> bool:
        """
        Set parameter value.
        Returns True if parameter was set successfully.
        """
        for param in self.get_parameters():
            if param.name == name:
                if param.validate(value):
                    self._params[name] = value
                    self._calculated = False  # Reset calculation flag
                    return True
                return False
        return False
    
    def get_all_params(self) -> Dict[str, Any]:
        """Get all current parameter values"""
        return self._params.copy()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert indicator info to dictionary"""
        return {
            "id": self.get_id(),
            "name": self.get_name(),
            "description": self.get_description(),
            "version": self.get_version(),
            "author": self.get_author(),
            "parameters": [p.to_dict() for p in self.get_parameters()],
            "warmup_period": self.warmup_period(),
            "chart_config": self.get_chart_config(),
            "output_columns": self.get_output_columns()
        }
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id='{self.get_id()}', params={self._params})"


# ==================== HELPER FUNCTIONS ====================

def calculate_atr(df: pd.DataFrame, period: int) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    Uses Wilder's smoothing (RMA).
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Wilder's smoothing (RMA)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Simple Moving Average"""
    return series.rolling(window=period).mean()


def calculate_rma(series: pd.Series, period: int) -> pd.Series:
    """Calculate Wilder's Moving Average (RMA)"""
    return series.ewm(alpha=1/period, adjust=False).mean()


def crossover(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """
    Check if series1 crosses over series2.
    Returns True on bars where crossover occurs.
    """
    prev_below = series1.shift(1) <= series2.shift(1)
    curr_above = series1 > series2
    return prev_below & curr_above


def crossunder(series1: pd.Series, series2: pd.Series) -> pd.Series:
    """
    Check if series1 crosses under series2.
    Returns True on bars where crossunder occurs.
    """
    prev_above = series1.shift(1) >= series2.shift(1)
    curr_below = series1 < series2
    return prev_above & curr_below
