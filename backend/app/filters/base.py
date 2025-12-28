"""
KOMAS Trading System - Filter Base Classes
==========================================

Base classes for the modular filter system.

Components:
- FilterResult: Result of a single filter check
- FilterCategory: Enum of filter categories
- FilterConfig: Configuration for a filter
- BaseFilter: Abstract base class for all filters

Chat #37: Filters Architecture
Author: KOMAS Team
Version: 4.0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Type
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class FilterCategory(Enum):
    """Categories of filters"""
    TIME = "time"               # Session, weekday, cooldown
    VOLATILITY = "volatility"   # ATR, volume, extreme conditions
    TREND = "trend"             # BTC trend, multi-TF, regime
    PORTFOLIO = "portfolio"     # Correlation, direction, sector limits
    PROTECTION = "protection"   # Equity curve, DD, streak, recovery


class FilterPriority(Enum):
    """Filter execution priority (lower = earlier)"""
    CRITICAL = 1    # Protection filters run first (equity, DD)
    HIGH = 2        # Time filters
    NORMAL = 3      # Trend, volatility
    LOW = 4         # Portfolio filters


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class FilterResult:
    """
    Result of a filter check.
    
    Attributes:
        allowed: True if signal passes the filter
        reason: Human-readable reason if blocked
        filter_name: Name of the filter that made the decision
        filter_category: Category of the filter
        details: Additional information about the decision
        timestamp: When the decision was made
    """
    allowed: bool
    reason: Optional[str] = None
    filter_name: str = ""
    filter_category: Optional[FilterCategory] = None
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __repr__(self) -> str:
        status = "ALLOWED" if self.allowed else "BLOCKED"
        if self.reason:
            return f"FilterResult({status}: {self.reason})"
        return f"FilterResult({status})"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "filter_name": self.filter_name,
            "filter_category": self.filter_category.value if self.filter_category else None,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }
    
    @classmethod
    def allow(cls, filter_name: str = "", category: Optional[FilterCategory] = None,
              details: Optional[Dict[str, Any]] = None) -> "FilterResult":
        """Factory method for allowed result"""
        return cls(
            allowed=True,
            filter_name=filter_name,
            filter_category=category,
            details=details or {},
        )
    
    @classmethod
    def block(cls, reason: str, filter_name: str = "", 
              category: Optional[FilterCategory] = None,
              details: Optional[Dict[str, Any]] = None) -> "FilterResult":
        """Factory method for blocked result"""
        return cls(
            allowed=False,
            reason=reason,
            filter_name=filter_name,
            filter_category=category,
            details=details or {},
        )


@dataclass
class FilterConfig:
    """
    Configuration for a filter instance.
    
    Attributes:
        name: Filter name (e.g., 'session_filter')
        enabled: Whether the filter is active
        params: Filter-specific parameters
        priority: Execution priority
    """
    name: str
    enabled: bool = True
    params: Dict[str, Any] = field(default_factory=dict)
    priority: FilterPriority = FilterPriority.NORMAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "params": self.params,
            "priority": self.priority.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FilterConfig":
        """Create from dictionary"""
        priority = data.get("priority", FilterPriority.NORMAL.value)
        if isinstance(priority, int):
            priority = FilterPriority(priority)
        elif isinstance(priority, str):
            priority = FilterPriority[priority.upper()]
        else:
            priority = FilterPriority.NORMAL
            
        return cls(
            name=data["name"],
            enabled=data.get("enabled", True),
            params=data.get("params", {}),
            priority=priority,
        )


@dataclass
class SignalContext:
    """
    Context information passed to filters.
    
    Contains all relevant information about the current trading state.
    
    Attributes:
        signal: The trade signal being evaluated
        symbol: Trading symbol (e.g., 'BTCUSDT')
        timeframe: Timeframe (e.g., '1h')
        current_price: Current market price
        current_time: Current datetime
        open_positions: List of currently open positions
        recent_trades: List of recent closed trades
        equity: Current account equity
        starting_equity: Starting account equity
        daily_pnl: Today's P&L
        market_data: Additional market data (OHLCV, indicators)
        bot_config: Bot configuration parameters
        extra: Any additional data
    """
    signal: Dict[str, Any]
    symbol: str
    timeframe: str
    current_price: float
    current_time: datetime
    open_positions: List[Dict[str, Any]] = field(default_factory=list)
    recent_trades: List[Dict[str, Any]] = field(default_factory=list)
    equity: float = 10000.0
    starting_equity: float = 10000.0
    daily_pnl: float = 0.0
    market_data: Optional[Dict[str, Any]] = None
    bot_config: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def direction(self) -> str:
        """Get signal direction"""
        return self.signal.get("direction", "long")
    
    @property
    def entry_price(self) -> float:
        """Get signal entry price"""
        return self.signal.get("entry_price", self.current_price)
    
    @property
    def current_drawdown(self) -> float:
        """Calculate current drawdown percentage"""
        if self.starting_equity <= 0:
            return 0.0
        return ((self.starting_equity - self.equity) / self.starting_equity) * 100
    
    @property
    def position_count(self) -> int:
        """Number of open positions"""
        return len(self.open_positions)
    
    def get_positions_by_direction(self, direction: str) -> List[Dict[str, Any]]:
        """Get positions filtered by direction"""
        return [p for p in self.open_positions if p.get("direction") == direction]
    
    @property
    def long_positions(self) -> List[Dict[str, Any]]:
        """Get long positions"""
        return self.get_positions_by_direction("long")
    
    @property
    def short_positions(self) -> List[Dict[str, Any]]:
        """Get short positions"""
        return self.get_positions_by_direction("short")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "signal": self.signal,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "current_price": self.current_price,
            "current_time": self.current_time.isoformat(),
            "open_positions": self.open_positions,
            "recent_trades": self.recent_trades,
            "equity": self.equity,
            "starting_equity": self.starting_equity,
            "daily_pnl": self.daily_pnl,
            "position_count": self.position_count,
            "current_drawdown": self.current_drawdown,
        }


# =============================================================================
# BASE FILTER CLASS
# =============================================================================

class BaseFilter(ABC):
    """
    Abstract base class for all trading filters.
    
    Each filter must implement:
    - can_trade(): Main filter logic
    - get_config_schema(): JSON schema for configuration
    
    Attributes:
        name: Unique filter name
        display_name: Human-readable name
        description: Filter description
        category: Filter category
        priority: Execution priority
        enabled: Whether filter is active
        config: Filter configuration
    """
    
    # Class-level attributes (override in subclasses)
    name: str = "base_filter"
    display_name: str = "Base Filter"
    description: str = "Abstract base filter"
    category: FilterCategory = FilterCategory.TREND
    priority: FilterPriority = FilterPriority.NORMAL
    version: str = "1.0"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize filter with configuration.
        
        Args:
            config: Filter configuration parameters
        """
        self.enabled = True
        self.config = config or {}
        self._validate_and_apply_config()
        logger.debug(f"Initialized filter: {self.name}")
    
    def _validate_and_apply_config(self) -> None:
        """Validate and apply configuration"""
        schema = self.get_config_schema()
        
        # Apply defaults from schema
        for param_name, param_schema in schema.get("properties", {}).items():
            if param_name not in self.config and "default" in param_schema:
                self.config[param_name] = param_schema["default"]
        
        # Check enabled status
        if "enabled" in self.config:
            self.enabled = bool(self.config["enabled"])
    
    @abstractmethod
    def can_trade(self, context: SignalContext) -> FilterResult:
        """
        Check if the signal should be allowed.
        
        This is the main filter logic. Each subclass must implement this.
        
        Args:
            context: SignalContext with all relevant trading state
            
        Returns:
            FilterResult indicating whether signal is allowed
        """
        pass
    
    @abstractmethod
    def get_config_schema(self) -> Dict[str, Any]:
        """
        Return JSON schema for filter configuration.
        
        The schema should follow JSON Schema format and include:
        - properties: Dict of parameter definitions
        - required: List of required parameters
        - Each property should have: type, description, default
        
        Returns:
            Dict with JSON schema
        """
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration against schema.
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid, False otherwise
        """
        schema = self.get_config_schema()
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Check required fields
        for field in required:
            if field not in config:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate types
        for key, value in config.items():
            if key in properties:
                prop_schema = properties[key]
                expected_type = prop_schema.get("type")
                
                if expected_type == "number" or expected_type == "integer":
                    if not isinstance(value, (int, float)):
                        logger.warning(f"Invalid type for {key}: expected number")
                        return False
                elif expected_type == "string":
                    if not isinstance(value, str):
                        logger.warning(f"Invalid type for {key}: expected string")
                        return False
                elif expected_type == "boolean":
                    if not isinstance(value, bool):
                        logger.warning(f"Invalid type for {key}: expected boolean")
                        return False
                elif expected_type == "array":
                    if not isinstance(value, list):
                        logger.warning(f"Invalid type for {key}: expected array")
                        return False
        
        return True
    
    def update_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Update filter configuration.
        
        Args:
            new_config: New configuration values
            
        Returns:
            True if update successful
        """
        if self.validate_config({**self.config, **new_config}):
            self.config.update(new_config)
            self._validate_and_apply_config()
            return True
        return False
    
    def enable(self) -> None:
        """Enable the filter"""
        self.enabled = True
        logger.info(f"Filter enabled: {self.name}")
    
    def disable(self) -> None:
        """Disable the filter"""
        self.enabled = False
        logger.info(f"Filter disabled: {self.name}")
    
    def get_info(self) -> Dict[str, Any]:
        """Get filter information"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category.value,
            "priority": self.priority.value,
            "enabled": self.enabled,
            "version": self.version,
            "config": self.config,
            "config_schema": self.get_config_schema(),
        }
    
    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"{self.__class__.__name__}(name='{self.name}', {status})"
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseFilter):
            return False
        return self.name == other.name
    
    def __hash__(self) -> int:
        return hash(self.name)


# =============================================================================
# EXAMPLE FILTER (for testing and reference)
# =============================================================================

class AlwaysAllowFilter(BaseFilter):
    """
    Example filter that always allows signals.
    Useful for testing the filter chain.
    """
    
    name = "always_allow"
    display_name = "Always Allow"
    description = "Test filter that always allows signals"
    category = FilterCategory.TREND
    priority = FilterPriority.LOW
    
    def can_trade(self, context: SignalContext) -> FilterResult:
        """Always returns allowed"""
        return FilterResult.allow(
            filter_name=self.name,
            category=self.category,
            details={"message": "Always allowed for testing"},
        )
    
    def get_config_schema(self) -> Dict[str, Any]:
        """No configuration needed"""
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }


class AlwaysBlockFilter(BaseFilter):
    """
    Example filter that always blocks signals.
    Useful for testing the filter chain.
    """
    
    name = "always_block"
    display_name = "Always Block"
    description = "Test filter that always blocks signals"
    category = FilterCategory.PROTECTION
    priority = FilterPriority.CRITICAL
    
    def can_trade(self, context: SignalContext) -> FilterResult:
        """Always returns blocked"""
        block_reason = self.config.get("reason", "Blocked by always_block filter")
        return FilterResult.block(
            reason=block_reason,
            filter_name=self.name,
            category=self.category,
            details={"message": "Always blocked for testing"},
        )
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Configuration for block reason"""
        return {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "description": "Custom block reason",
                    "default": "Blocked by always_block filter",
                },
            },
            "required": [],
        }


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "FilterCategory",
    "FilterPriority",
    "FilterResult",
    "FilterConfig",
    "SignalContext",
    "BaseFilter",
    "AlwaysAllowFilter",
    "AlwaysBlockFilter",
]
