"""
Komas Trading System - Base Filter
==================================
Abstract base class for signal filters.
Filters can allow/block entry signals based on market conditions.

Version: 1.0
Author: Komas Team
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import numpy as np

from .indicator import IndicatorParameter


class FilterResult(Enum):
    """Filter decision result"""
    ALLOW = "allow"      # Allow the signal
    BLOCK = "block"      # Block the signal
    NEUTRAL = "neutral"  # No opinion (pass to next filter)


@dataclass
class FilterOutput:
    """
    Output of filter calculation.
    Contains decision and additional data for UI.
    """
    result: FilterResult
    reason: str = ""
    values: Dict[str, float] = field(default_factory=dict)
    
    # Series data for chart display
    chart_data: Dict[str, pd.Series] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "result": self.result.value,
            "reason": self.reason,
            "values": self.values
        }


class BaseFilter(ABC):
    """
    Abstract base class for signal filters.
    
    Filters are applied to entry signals to allow/block trades
    based on market conditions (trend, momentum, volume, etc.)
    
    Subclasses must implement:
    - get_id(): Return unique filter identifier
    - get_name(): Return display name
    - get_parameters(): Return configurable parameters
    - calculate(): Calculate filter indicator
    - check(): Check if signal should be allowed
    
    Optional overrides:
    - get_description(): Return filter description
    - get_chart_config(): Return chart visualization config
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None, enabled: bool = True):
        """
        Initialize filter with parameters.
        
        Args:
            params: Dictionary of parameter values
            enabled: Whether filter is active
        """
        self._params = self._init_params(params or {})
        self._enabled = enabled
        self._calculated = False
        self._df: Optional[pd.DataFrame] = None
    
    def _init_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize parameters with defaults"""
        result = {}
        for param in self.get_parameters():
            if param.name in params:
                value = params[param.name]
                if param.validate(value):
                    result[param.name] = value
                else:
                    result[param.name] = param.default
            else:
                result[param.name] = param.default
        return result
    
    # ==================== ABSTRACT METHODS ====================
    
    @abstractmethod
    def get_id(self) -> str:
        """
        Return unique filter identifier.
        
        Example: "supertrend", "rsi", "adx", "volume"
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        Return human-readable filter name.
        
        Example: "SuperTrend Filter", "RSI Filter"
        """
        pass
    
    @abstractmethod
    def get_parameters(self) -> List[IndicatorParameter]:
        """
        Return list of configurable parameters.
        
        Example:
        [
            IndicatorParameter("period", "Period", "int", 10, 1, 100, 1),
            IndicatorParameter("multiplier", "Multiplier", "float", 3.0, 0.1, 10.0, 0.1),
        ]
        """
        pass
    
    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate filter indicator values.
        
        Args:
            df: OHLCV DataFrame
        
        Returns:
            DataFrame with added filter columns
        """
        pass
    
    @abstractmethod
    def check(self, df: pd.DataFrame, index: int, signal: int) -> FilterOutput:
        """
        Check if signal should be allowed at specific index.
        
        Args:
            df: DataFrame with calculated filter values
            index: Bar index to check
            signal: Signal to filter (1=long, -1=short)
        
        Returns:
            FilterOutput with decision
        """
        pass
    
    # ==================== OPTIONAL OVERRIDES ====================
    
    def get_description(self) -> str:
        """Return filter description"""
        return ""
    
    def get_chart_config(self) -> Dict[str, Any]:
        """Return chart visualization config"""
        return {
            "overlay": False,  # Usually in separate pane
            "lines": [],
            "bands": []
        }
    
    def get_output_columns(self) -> List[str]:
        """Return list of columns this filter adds"""
        return []
    
    def warmup_period(self) -> int:
        """Candles needed before filter is valid"""
        return 20
    
    # ==================== PUBLIC API ====================
    
    @property
    def enabled(self) -> bool:
        """Check if filter is enabled"""
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        """Enable/disable filter"""
        self._enabled = value
    
    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Run filter calculation.
        
        Args:
            df: OHLCV DataFrame
        
        Returns:
            DataFrame with filter columns added
        """
        if not self._enabled:
            return df
        
        self._df = df.copy()
        self._df = self.calculate(self._df)
        self._calculated = True
        
        return self._df
    
    def filter_signal(self, index: int, signal: int) -> FilterOutput:
        """
        Filter a signal at specific index.
        
        Args:
            index: Bar index
            signal: Signal to filter
        
        Returns:
            FilterOutput with decision
        """
        if not self._enabled:
            return FilterOutput(FilterResult.ALLOW, "Filter disabled")
        
        if not self._calculated or self._df is None:
            return FilterOutput(FilterResult.NEUTRAL, "Filter not calculated")
        
        if index < self.warmup_period():
            return FilterOutput(FilterResult.NEUTRAL, "Warmup period")
        
        return self.check(self._df, index, signal)
    
    def filter_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Filter all signals in DataFrame.
        
        Args:
            df: DataFrame with 'signal' column
        
        Returns:
            Series with filtered signals
        """
        if not self._enabled:
            return df.get('signal', pd.Series(0, index=df.index))
        
        # Calculate if needed
        if not self._calculated:
            self.run(df)
        
        # Apply filter to each signal
        result = pd.Series(0, index=df.index)
        
        for i in range(len(df)):
            signal = df.iloc[i].get('signal', 0)
            if signal == 0:
                continue
            
            output = self.filter_signal(i, signal)
            if output.result == FilterResult.ALLOW:
                result.iloc[i] = signal
        
        return result
    
    def get_param(self, name: str, default: Any = None) -> Any:
        """Get parameter value"""
        return self._params.get(name, default)
    
    def set_param(self, name: str, value: Any) -> bool:
        """Set parameter value"""
        for param in self.get_parameters():
            if param.name == name and param.validate(value):
                self._params[name] = value
                self._calculated = False
                return True
        return False
    
    def get_all_params(self) -> Dict[str, Any]:
        """Get all parameters"""
        return self._params.copy()
    
    def to_dict(self) -> Dict:
        """Convert filter info to dictionary"""
        return {
            "id": self.get_id(),
            "name": self.get_name(),
            "description": self.get_description(),
            "enabled": self._enabled,
            "parameters": [p.to_dict() for p in self.get_parameters()],
            "output_columns": self.get_output_columns()
        }
    
    def __repr__(self) -> str:
        status = "enabled" if self._enabled else "disabled"
        return f"{self.__class__.__name__}(id='{self.get_id()}', {status})"


# ==================== CONCRETE FILTER IMPLEMENTATIONS ====================
# These are commonly used filters that can be imported and used directly


class SuperTrendFilter(BaseFilter):
    """
    SuperTrend trend filter.
    Allows longs only in uptrend, shorts only in downtrend.
    """
    
    def get_id(self) -> str:
        return "supertrend"
    
    def get_name(self) -> str:
        return "SuperTrend Filter"
    
    def get_description(self) -> str:
        return "Filters signals based on SuperTrend direction"
    
    def get_parameters(self) -> List[IndicatorParameter]:
        return [
            IndicatorParameter(
                "period", "Period", "int", 10,
                min_value=1, max_value=100, step=1,
                description="ATR period"
            ),
            IndicatorParameter(
                "multiplier", "Multiplier", "float", 3.0,
                min_value=0.1, max_value=10.0, step=0.1,
                description="ATR multiplier"
            ),
        ]
    
    def get_output_columns(self) -> List[str]:
        return ["supertrend", "supertrend_dir"]
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        period = self.get_param("period")
        mult = self.get_param("multiplier")
        
        high = df['high']
        low = df['low']
        close = df['close']
        
        # ATR
        tr = pd.concat([
            high - low,
            abs(high - close.shift(1)),
            abs(low - close.shift(1))
        ], axis=1).max(axis=1)
        atr = tr.rolling(period).mean()
        
        hl2 = (high + low) / 2
        upper = hl2 + (mult * atr)
        lower = hl2 - (mult * atr)
        
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(index=df.index, dtype=int)
        
        for i in range(period, len(df)):
            if close.iloc[i] > upper.iloc[i-1]:
                direction.iloc[i] = 1
            elif close.iloc[i] < lower.iloc[i-1]:
                direction.iloc[i] = -1
            else:
                direction.iloc[i] = direction.iloc[i-1] if i > period else 1
            
            supertrend.iloc[i] = lower.iloc[i] if direction.iloc[i] == 1 else upper.iloc[i]
        
        df['supertrend'] = supertrend
        df['supertrend_dir'] = direction
        
        return df
    
    def check(self, df: pd.DataFrame, index: int, signal: int) -> FilterOutput:
        if 'supertrend_dir' not in df.columns:
            return FilterOutput(FilterResult.NEUTRAL, "SuperTrend not calculated")
        
        direction = df['supertrend_dir'].iloc[index]
        
        # Long signals allowed only in uptrend
        if signal == 1:
            if direction == 1:
                return FilterOutput(FilterResult.ALLOW, "Uptrend confirmed")
            else:
                return FilterOutput(FilterResult.BLOCK, "Blocked: Downtrend")
        
        # Short signals allowed only in downtrend
        if signal == -1:
            if direction == -1:
                return FilterOutput(FilterResult.ALLOW, "Downtrend confirmed")
            else:
                return FilterOutput(FilterResult.BLOCK, "Blocked: Uptrend")
        
        return FilterOutput(FilterResult.NEUTRAL)


class RSIFilter(BaseFilter):
    """
    RSI overbought/oversold filter.
    Blocks longs in overbought, shorts in oversold.
    """
    
    def get_id(self) -> str:
        return "rsi"
    
    def get_name(self) -> str:
        return "RSI Filter"
    
    def get_description(self) -> str:
        return "Filters signals based on RSI levels"
    
    def get_parameters(self) -> List[IndicatorParameter]:
        return [
            IndicatorParameter(
                "period", "Period", "int", 14,
                min_value=2, max_value=100, step=1
            ),
            IndicatorParameter(
                "overbought", "Overbought", "int", 70,
                min_value=50, max_value=100, step=1
            ),
            IndicatorParameter(
                "oversold", "Oversold", "int", 30,
                min_value=0, max_value=50, step=1
            ),
        ]
    
    def get_output_columns(self) -> List[str]:
        return ["rsi"]
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        period = self.get_param("period")
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        return df
    
    def check(self, df: pd.DataFrame, index: int, signal: int) -> FilterOutput:
        if 'rsi' not in df.columns:
            return FilterOutput(FilterResult.NEUTRAL, "RSI not calculated")
        
        rsi = df['rsi'].iloc[index]
        overbought = self.get_param("overbought")
        oversold = self.get_param("oversold")
        
        if pd.isna(rsi):
            return FilterOutput(FilterResult.NEUTRAL, "RSI is NaN")
        
        # Block longs in overbought
        if signal == 1:
            if rsi < overbought:
                return FilterOutput(FilterResult.ALLOW, f"RSI {rsi:.1f} < {overbought}")
            else:
                return FilterOutput(FilterResult.BLOCK, f"Blocked: RSI overbought ({rsi:.1f})")
        
        # Block shorts in oversold
        if signal == -1:
            if rsi > oversold:
                return FilterOutput(FilterResult.ALLOW, f"RSI {rsi:.1f} > {oversold}")
            else:
                return FilterOutput(FilterResult.BLOCK, f"Blocked: RSI oversold ({rsi:.1f})")
        
        return FilterOutput(FilterResult.NEUTRAL)


class ADXFilter(BaseFilter):
    """
    ADX trend strength filter.
    Only allows signals when trend is strong enough.
    """
    
    def get_id(self) -> str:
        return "adx"
    
    def get_name(self) -> str:
        return "ADX Filter"
    
    def get_description(self) -> str:
        return "Filters signals based on ADX trend strength"
    
    def get_parameters(self) -> List[IndicatorParameter]:
        return [
            IndicatorParameter(
                "period", "Period", "int", 14,
                min_value=2, max_value=100, step=1
            ),
            IndicatorParameter(
                "threshold", "Threshold", "int", 25,
                min_value=0, max_value=100, step=1,
                description="Minimum ADX for strong trend"
            ),
        ]
    
    def get_output_columns(self) -> List[str]:
        return ["adx", "plus_di", "minus_di"]
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        period = self.get_param("period")
        
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
        df['plus_di'] = plus_di
        df['minus_di'] = minus_di
        
        return df
    
    def check(self, df: pd.DataFrame, index: int, signal: int) -> FilterOutput:
        if 'adx' not in df.columns:
            return FilterOutput(FilterResult.NEUTRAL, "ADX not calculated")
        
        adx = df['adx'].iloc[index]
        threshold = self.get_param("threshold")
        
        if pd.isna(adx):
            return FilterOutput(FilterResult.NEUTRAL, "ADX is NaN")
        
        if adx >= threshold:
            return FilterOutput(
                FilterResult.ALLOW, 
                f"Strong trend: ADX {adx:.1f} >= {threshold}",
                values={"adx": adx}
            )
        else:
            return FilterOutput(
                FilterResult.BLOCK, 
                f"Weak trend: ADX {adx:.1f} < {threshold}",
                values={"adx": adx}
            )


class VolumeFilter(BaseFilter):
    """
    Volume filter.
    Only allows signals when volume is above average.
    """
    
    def get_id(self) -> str:
        return "volume"
    
    def get_name(self) -> str:
        return "Volume Filter"
    
    def get_description(self) -> str:
        return "Filters signals based on volume"
    
    def get_parameters(self) -> List[IndicatorParameter]:
        return [
            IndicatorParameter(
                "period", "MA Period", "int", 20,
                min_value=2, max_value=200, step=1
            ),
            IndicatorParameter(
                "threshold", "Threshold", "float", 1.5,
                min_value=0.1, max_value=10.0, step=0.1,
                description="Volume must be X times average"
            ),
        ]
    
    def get_output_columns(self) -> List[str]:
        return ["volume_ma", "volume_ratio"]
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        if 'volume' not in df.columns:
            return df
        
        period = self.get_param("period")
        
        df['volume_ma'] = df['volume'].rolling(period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        return df
    
    def check(self, df: pd.DataFrame, index: int, signal: int) -> FilterOutput:
        if 'volume_ratio' not in df.columns:
            return FilterOutput(FilterResult.NEUTRAL, "Volume not calculated")
        
        ratio = df['volume_ratio'].iloc[index]
        threshold = self.get_param("threshold")
        
        if pd.isna(ratio):
            return FilterOutput(FilterResult.NEUTRAL, "Volume ratio is NaN")
        
        if ratio >= threshold:
            return FilterOutput(
                FilterResult.ALLOW,
                f"High volume: {ratio:.1f}x average",
                values={"volume_ratio": ratio}
            )
        else:
            return FilterOutput(
                FilterResult.BLOCK,
                f"Low volume: {ratio:.1f}x < {threshold}x required",
                values={"volume_ratio": ratio}
            )


# ==================== FILTER CHAIN ====================

class FilterChain:
    """
    Chain of filters applied in sequence.
    Signal is allowed only if all enabled filters allow it.
    """
    
    def __init__(self, filters: Optional[List[BaseFilter]] = None):
        self.filters = filters or []
    
    def add_filter(self, filter_obj: BaseFilter) -> None:
        """Add filter to chain"""
        self.filters.append(filter_obj)
    
    def remove_filter(self, filter_id: str) -> bool:
        """Remove filter by ID"""
        for i, f in enumerate(self.filters):
            if f.get_id() == filter_id:
                self.filters.pop(i)
                return True
        return False
    
    def get_filter(self, filter_id: str) -> Optional[BaseFilter]:
        """Get filter by ID"""
        for f in self.filters:
            if f.get_id() == filter_id:
                return f
        return None
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """Run calculation for all filters"""
        for f in self.filters:
            if f.enabled:
                df = f.run(df)
        return df
    
    def check_signal(self, index: int, signal: int) -> Tuple[bool, List[FilterOutput]]:
        """
        Check signal against all filters.
        
        Returns:
            Tuple of (allowed, list of filter outputs)
        """
        outputs = []
        
        for f in self.filters:
            if not f.enabled:
                continue
            
            output = f.filter_signal(index, signal)
            outputs.append(output)
            
            # Block if any filter blocks
            if output.result == FilterResult.BLOCK:
                return False, outputs
        
        return True, outputs
    
    def filter_all_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        Filter all signals in DataFrame.
        
        Returns:
            Series with filtered signals
        """
        # Calculate all filters
        df = self.calculate_all(df)
        
        # Apply filters
        result = df.get('signal', pd.Series(0, index=df.index)).copy()
        
        for i in range(len(df)):
            signal = result.iloc[i]
            if signal == 0:
                continue
            
            allowed, _ = self.check_signal(i, signal)
            if not allowed:
                result.iloc[i] = 0
        
        return result
    
    def to_dict(self) -> List[Dict]:
        """Convert filter chain to list of dictionaries"""
        return [f.to_dict() for f in self.filters]
