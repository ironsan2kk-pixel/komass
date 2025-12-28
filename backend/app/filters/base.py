"""
KOMAS v4.0 — Bot Filters Base Architecture
==========================================

Base classes and interfaces for the modular filter system.

Filter Categories:
- TIME: Session, Weekday, Cooldown
- VOLATILITY: ATR, Volume, Extreme
- TREND: BTC trend, Multi-TF, Regime
- PORTFOLIO: Correlation, Direction, Sector
- PROTECTION: Equity Curve, DD, Streak, Recovery

Chat #37: Filters Architecture
Chat #38: Time Filters
Author: KOMAS Team
Version: 4.0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Any, Tuple, Callable
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class FilterCategory(Enum):
    """Filter categories for grouping and UI organization"""
    TIME = "time"
    VOLATILITY = "volatility"
    TREND = "trend"
    PORTFOLIO = "portfolio"
    PROTECTION = "protection"


class FilterPriority(Enum):
    """
    Filter execution priority.
    Lower values execute first.
    """
    CRITICAL = 1   # Protection filters (DD, Equity)
    HIGH = 2       # Time filters (Session, Weekday)
    MEDIUM = 3     # Trend filters (BTC, Regime)
    LOW = 4        # Portfolio filters (Correlation)
    
    def __lt__(self, other):
        if isinstance(other, FilterPriority):
            return self.value < other.value
        return NotImplemented
    
    def __le__(self, other):
        if isinstance(other, FilterPriority):
            return self.value <= other.value
        return NotImplemented


class FilterResult(Enum):
    """Result of filter check"""
    PASS = "pass"           # Signal allowed
    BLOCK = "block"         # Signal blocked
    SKIP = "skip"           # Filter not applicable


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Signal:
    """
    Represents a trading signal to be filtered.
    """
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    timestamp: datetime
    
    # Optional fields
    timeframe: str = "1h"
    indicator: str = "trg"
    preset_id: Optional[str] = None
    score: Optional[int] = None  # Signal score 0-100
    grade: Optional[str] = None  # A/B/C/D/F
    
    # Take profit / Stop loss
    tp_levels: List[Dict] = field(default_factory=list)
    sl_percent: float = 2.5
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.direction not in ('long', 'short'):
            raise ValueError(f"Direction must be 'long' or 'short', got: {self.direction}")


@dataclass
class SignalContext:
    """
    Context information for filter decisions.
    Contains market data, portfolio state, and recent history.
    """
    # Current time
    current_time: datetime
    
    # Market data for the symbol
    current_price: float
    atr: Optional[float] = None
    volume: Optional[float] = None
    avg_volume: Optional[float] = None
    
    # Higher timeframe data
    htf_trend: Optional[str] = None  # 'up', 'down', 'neutral'
    htf_data: Dict[str, Any] = field(default_factory=dict)
    
    # BTC context (for BTC trend filter)
    btc_trend: Optional[str] = None
    btc_price: Optional[float] = None
    
    # Portfolio state
    open_positions: List[Dict] = field(default_factory=list)
    total_exposure: float = 0.0
    current_equity: float = 0.0
    starting_equity: float = 0.0
    
    # Recent trades (for cooldown, streak filters)
    recent_trades: List[Dict] = field(default_factory=list)
    
    # Equity curve (for equity curve filter)
    equity_curve: List[float] = field(default_factory=list)
    
    # Bot config reference
    bot_config: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def current_dd_percent(self) -> float:
        """Calculate current drawdown percentage"""
        if self.starting_equity <= 0:
            return 0.0
        if not self.equity_curve:
            return 0.0
        peak = max(self.equity_curve) if self.equity_curve else self.starting_equity
        if peak <= 0:
            return 0.0
        return (peak - self.current_equity) / peak * 100


@dataclass
class FilterDecision:
    """
    Result of a filter evaluation.
    """
    result: FilterResult
    filter_name: str
    reason: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_blocked(self) -> bool:
        return self.result == FilterResult.BLOCK
    
    @property
    def is_passed(self) -> bool:
        return self.result == FilterResult.PASS
    
    def __str__(self) -> str:
        status = "✅ PASS" if self.is_passed else "❌ BLOCK" if self.is_blocked else "⏭️ SKIP"
        msg = f"[{self.filter_name}] {status}"
        if self.reason:
            msg += f": {self.reason}"
        return msg


@dataclass
class FilterConfig:
    """
    Configuration for a single filter.
    Used when loading/saving filter configurations.
    """
    filter_name: str
    enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for filter instantiation"""
        return {
            "enabled": self.enabled,
            **self.params
        }
    
    @classmethod
    def from_dict(cls, name: str, data: Dict[str, Any]) -> "FilterConfig":
        """Create from dict"""
        enabled = data.pop("enabled", True)
        return cls(
            filter_name=name,
            enabled=enabled,
            params=data
        )


# =============================================================================
# BASE FILTER CLASS
# =============================================================================

class BaseFilter(ABC):
    """
    Abstract base class for all filters.
    
    Each filter must implement:
    - should_allow(): Check if signal should pass
    - get_config_schema(): Define configurable parameters
    
    Filters can optionally implement:
    - on_trade_complete(): Called after trade closes
    - reset(): Reset internal state
    """
    
    # Class-level attributes (override in subclasses)
    name: str = "base_filter"
    description: str = "Base filter class"
    category: FilterCategory = FilterCategory.TIME
    priority: FilterPriority = FilterPriority.MEDIUM
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize filter with configuration.
        
        Args:
            config: Filter-specific configuration dict
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self._validate_config()
        
    def _validate_config(self) -> None:
        """
        Validate configuration against schema.
        Override for custom validation.
        """
        schema = self.get_config_schema()
        for key, props in schema.items():
            if props.get("required", False) and key not in self.config:
                raise ValueError(f"Required config key missing: {key}")
    
    @abstractmethod
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """
        Evaluate whether the signal should be allowed.
        
        Args:
            signal: The trading signal to evaluate
            context: Market and portfolio context
            
        Returns:
            FilterDecision with result and reasoning
        """
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Return the configuration schema for this filter.
        
        Schema format:
        {
            "param_name": {
                "type": "int" | "float" | "bool" | "str" | "list",
                "default": value,
                "min": optional_min,
                "max": optional_max,
                "options": [list_of_options],  # for str/list types
                "description": "Human readable description",
                "required": bool
            }
        }
        """
        pass
    
    def on_trade_complete(self, trade_result: Dict[str, Any]) -> None:
        """
        Called when a trade completes.
        Override to update internal state.
        
        Args:
            trade_result: Dict with trade details (pnl, exit_time, etc)
        """
        pass
    
    def reset(self) -> None:
        """
        Reset internal state.
        Override if filter maintains state.
        """
        pass
    
    def get_ui_display(self) -> Dict[str, Any]:
        """
        Return UI display information.
        """
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "priority": self.priority.name,
            "enabled": self.enabled,
            "config": self.config,
            "schema": self.get_config_schema()
        }
    
    def __repr__(self) -> str:
        status = "ON" if self.enabled else "OFF"
        return f"<{self.__class__.__name__}({self.name}) [{status}]>"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_pass_decision(filter_name: str, reason: str = None, **details) -> FilterDecision:
    """Create a PASS decision"""
    return FilterDecision(
        result=FilterResult.PASS,
        filter_name=filter_name,
        reason=reason,
        details=details
    )


def create_block_decision(filter_name: str, reason: str, **details) -> FilterDecision:
    """Create a BLOCK decision"""
    return FilterDecision(
        result=FilterResult.BLOCK,
        filter_name=filter_name,
        reason=reason,
        details=details
    )


def create_skip_decision(filter_name: str, reason: str = None, **details) -> FilterDecision:
    """Create a SKIP decision"""
    return FilterDecision(
        result=FilterResult.SKIP,
        filter_name=filter_name,
        reason=reason,
        details=details
    )


# =============================================================================
# TEST FILTER CLASSES (for testing purposes)
# =============================================================================

class AlwaysAllowFilter(BaseFilter):
    """
    Test filter that always allows signals.
    Used for testing filter chain behavior.
    """
    name = "always_allow"
    description = "Always allows signals (for testing)"
    category = FilterCategory.TIME
    priority = FilterPriority.LOW
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        return create_pass_decision(self.name, "Always allowed")
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable filter"
            }
        }


class AlwaysBlockFilter(BaseFilter):
    """
    Test filter that always blocks signals.
    Used for testing filter chain behavior.
    """
    name = "always_block"
    description = "Always blocks signals (for testing)"
    category = FilterCategory.TIME
    priority = FilterPriority.LOW
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        reason = self.config.get("reason", "Always blocked")
        return create_block_decision(self.name, reason)
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable filter"
            },
            "reason": {
                "type": "str",
                "default": "Always blocked",
                "description": "Block reason message"
            }
        }


class ConditionalFilter(BaseFilter):
    """
    Test filter with configurable pass/block behavior.
    Used for testing filter chain behavior.
    """
    name = "conditional"
    description = "Conditionally allows/blocks based on config"
    category = FilterCategory.TIME
    priority = FilterPriority.MEDIUM
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        should_pass = self.config.get("should_pass", True)
        if should_pass:
            return create_pass_decision(self.name, "Condition met")
        else:
            return create_block_decision(self.name, "Condition not met")
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable filter"
            },
            "should_pass": {
                "type": "bool",
                "default": True,
                "description": "Whether to pass or block"
            }
        }
