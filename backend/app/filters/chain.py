"""
KOMAS Trading System - Filter Chain
====================================

Filter chain for applying multiple filters to signals.

Features:
- Sequential filter application
- Short-circuit on first rejection (configurable)
- Priority-based ordering
- Detailed rejection logging
- Chain result aggregation

Chat #37: Filters Architecture
Author: KOMAS Team
Version: 4.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from .base import (
    BaseFilter,
    FilterResult,
    FilterConfig,
    FilterCategory,
    FilterPriority,
    SignalContext,
)
from .registry import get_registry, FilterRegistry

logger = logging.getLogger(__name__)


# =============================================================================
# CHAIN RESULT
# =============================================================================

@dataclass
class ChainResult:
    """
    Result of applying the entire filter chain.
    
    Attributes:
        allowed: True if signal passed all filters
        rejections: List of FilterResults that blocked the signal
        approvals: List of FilterResults that approved the signal
        total_filters: Total number of filters in chain
        active_filters: Number of enabled filters
        execution_time_ms: Time to execute the chain
        timestamp: When the chain was executed
    """
    allowed: bool
    rejections: List[FilterResult] = field(default_factory=list)
    approvals: List[FilterResult] = field(default_factory=list)
    total_filters: int = 0
    active_filters: int = 0
    execution_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def is_blocked(self) -> bool:
        """True if any filter blocked the signal"""
        return not self.allowed
    
    @property
    def rejection_count(self) -> int:
        """Number of filters that rejected"""
        return len(self.rejections)
    
    @property
    def approval_count(self) -> int:
        """Number of filters that approved"""
        return len(self.approvals)
    
    @property
    def primary_rejection(self) -> Optional[FilterResult]:
        """Get the first/primary rejection reason"""
        return self.rejections[0] if self.rejections else None
    
    @property
    def all_reasons(self) -> List[str]:
        """Get all rejection reasons"""
        return [r.reason for r in self.rejections if r.reason]
    
    def get_rejections_by_category(self, category: FilterCategory) -> List[FilterResult]:
        """Get rejections filtered by category"""
        return [r for r in self.rejections if r.filter_category == category]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "allowed": self.allowed,
            "rejections": [r.to_dict() for r in self.rejections],
            "approvals": [a.to_dict() for a in self.approvals],
            "rejection_count": self.rejection_count,
            "approval_count": self.approval_count,
            "total_filters": self.total_filters,
            "active_filters": self.active_filters,
            "execution_time_ms": self.execution_time_ms,
            "timestamp": self.timestamp.isoformat(),
            "primary_reason": self.primary_rejection.reason if self.primary_rejection else None,
        }
    
    def __repr__(self) -> str:
        status = "ALLOWED" if self.allowed else f"BLOCKED ({self.rejection_count} rejections)"
        return f"ChainResult({status})"


# =============================================================================
# FILTER CHAIN
# =============================================================================

class FilterChain:
    """
    Chain of filters applied sequentially to signals.
    
    The chain applies filters in priority order (CRITICAL -> HIGH -> NORMAL -> LOW).
    By default, it short-circuits on the first rejection, but this can be disabled
    to collect all rejections.
    
    Usage:
        chain = FilterChain()
        chain.add(SessionFilter({"sessions": ["london", "new_york"]}))
        chain.add(ATRFilter({"min_atr": 0.5}))
        
        result = chain.apply(signal_context)
        if result.allowed:
            # Execute trade
        else:
            print(f"Blocked: {result.primary_rejection.reason}")
    
    Attributes:
        filters: List of filters in the chain
        short_circuit: If True, stop on first rejection
        registry: Optional registry for filter lookup
    """
    
    def __init__(
        self,
        filters: Optional[List[BaseFilter]] = None,
        short_circuit: bool = True,
        registry: Optional[FilterRegistry] = None,
    ):
        """
        Initialize filter chain.
        
        Args:
            filters: Initial list of filters
            short_circuit: Stop on first rejection if True
            registry: Registry for filter lookup (uses global if None)
        """
        self._filters: List[BaseFilter] = []
        self.short_circuit = short_circuit
        self.registry = registry or get_registry()
        
        # Add initial filters
        if filters:
            for f in filters:
                self.add(f)
        
        logger.debug(f"FilterChain created with {len(self._filters)} filters")
    
    @property
    def filters(self) -> List[BaseFilter]:
        """Get sorted list of filters by priority"""
        return sorted(self._filters, key=lambda f: f.priority.value)
    
    @property
    def enabled_filters(self) -> List[BaseFilter]:
        """Get only enabled filters, sorted by priority"""
        return [f for f in self.filters if f.enabled]
    
    def add(self, filter_obj: BaseFilter) -> "FilterChain":
        """
        Add a filter to the chain.
        
        Args:
            filter_obj: Filter instance to add
            
        Returns:
            Self for method chaining
        """
        if not isinstance(filter_obj, BaseFilter):
            raise ValueError(f"Expected BaseFilter, got {type(filter_obj)}")
        
        # Check for duplicate
        existing = self.get(filter_obj.name)
        if existing:
            logger.warning(f"Replacing filter: {filter_obj.name}")
            self._filters.remove(existing)
        
        self._filters.append(filter_obj)
        logger.debug(f"Added filter: {filter_obj.name}")
        return self
    
    def add_by_name(
        self, 
        name: str, 
        config: Optional[Dict[str, Any]] = None
    ) -> "FilterChain":
        """
        Add a filter by name using the registry.
        
        Args:
            name: Filter name
            config: Filter configuration
            
        Returns:
            Self for method chaining
            
        Raises:
            ValueError: If filter not found in registry
        """
        filter_obj = self.registry.create(name, config)
        if filter_obj is None:
            raise ValueError(f"Filter not found: {name}")
        
        return self.add(filter_obj)
    
    def add_from_config(self, filter_config: FilterConfig) -> "FilterChain":
        """
        Add a filter from FilterConfig.
        
        Args:
            filter_config: Filter configuration
            
        Returns:
            Self for method chaining
        """
        filter_obj = self.registry.create_from_config(filter_config)
        if filter_obj is None:
            raise ValueError(f"Filter not found: {filter_config.name}")
        
        return self.add(filter_obj)
    
    def remove(self, name: str) -> bool:
        """
        Remove a filter by name.
        
        Args:
            name: Filter name
            
        Returns:
            True if removed, False if not found
        """
        filter_obj = self.get(name)
        if filter_obj:
            self._filters.remove(filter_obj)
            logger.debug(f"Removed filter: {name}")
            return True
        return False
    
    def get(self, name: str) -> Optional[BaseFilter]:
        """
        Get a filter by name.
        
        Args:
            name: Filter name
            
        Returns:
            Filter instance or None
        """
        for f in self._filters:
            if f.name == name:
                return f
        return None
    
    def has(self, name: str) -> bool:
        """Check if filter exists in chain"""
        return self.get(name) is not None
    
    def enable(self, name: str) -> bool:
        """Enable a filter by name"""
        filter_obj = self.get(name)
        if filter_obj:
            filter_obj.enable()
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """Disable a filter by name"""
        filter_obj = self.get(name)
        if filter_obj:
            filter_obj.disable()
            return True
        return False
    
    def enable_all(self) -> None:
        """Enable all filters"""
        for f in self._filters:
            f.enable()
    
    def disable_all(self) -> None:
        """Disable all filters"""
        for f in self._filters:
            f.disable()
    
    def clear(self) -> None:
        """Remove all filters from chain"""
        self._filters.clear()
        logger.debug("FilterChain cleared")
    
    def apply(self, context: SignalContext) -> ChainResult:
        """
        Apply all enabled filters to the signal.
        
        Filters are applied in priority order. If short_circuit is True,
        stops on the first rejection.
        
        Args:
            context: Signal context with all relevant data
            
        Returns:
            ChainResult with aggregate results
        """
        import time
        start_time = time.perf_counter()
        
        rejections: List[FilterResult] = []
        approvals: List[FilterResult] = []
        
        enabled = self.enabled_filters
        
        for filter_obj in enabled:
            try:
                result = filter_obj.can_trade(context)
                
                if result.allowed:
                    approvals.append(result)
                else:
                    rejections.append(result)
                    logger.debug(
                        f"Signal blocked by {filter_obj.name}: {result.reason}"
                    )
                    
                    if self.short_circuit:
                        break
                        
            except Exception as e:
                logger.error(f"Error in filter {filter_obj.name}: {e}")
                # On error, block the signal for safety
                rejections.append(FilterResult.block(
                    reason=f"Filter error: {e}",
                    filter_name=filter_obj.name,
                    category=filter_obj.category,
                ))
                if self.short_circuit:
                    break
        
        execution_time = (time.perf_counter() - start_time) * 1000
        
        return ChainResult(
            allowed=len(rejections) == 0,
            rejections=rejections,
            approvals=approvals,
            total_filters=len(self._filters),
            active_filters=len(enabled),
            execution_time_ms=execution_time,
        )
    
    def check(self, context: SignalContext) -> Tuple[bool, Optional[str]]:
        """
        Simple check returning (allowed, reason).
        
        Convenience method for quick checks.
        
        Args:
            context: Signal context
            
        Returns:
            Tuple of (allowed: bool, rejection_reason: Optional[str])
        """
        result = self.apply(context)
        reason = result.primary_rejection.reason if result.primary_rejection else None
        return result.allowed, reason
    
    def get_rejections(self, context: SignalContext) -> List[str]:
        """
        Get all rejection reasons for a signal.
        
        Runs with short_circuit=False to collect all rejections.
        
        Args:
            context: Signal context
            
        Returns:
            List of rejection reason strings
        """
        # Temporarily disable short-circuit
        old_setting = self.short_circuit
        self.short_circuit = False
        
        try:
            result = self.apply(context)
            return result.all_reasons
        finally:
            self.short_circuit = old_setting
    
    def list_filters(self) -> List[str]:
        """List all filter names in chain"""
        return [f.name for f in self.filters]
    
    def list_enabled(self) -> List[str]:
        """List enabled filter names"""
        return [f.name for f in self.enabled_filters]
    
    def list_disabled(self) -> List[str]:
        """List disabled filter names"""
        return [f.name for f in self._filters if not f.enabled]
    
    def get_info(self) -> Dict[str, Any]:
        """Get chain information"""
        return {
            "total_filters": len(self._filters),
            "enabled_filters": len(self.enabled_filters),
            "short_circuit": self.short_circuit,
            "filters": [f.get_info() for f in self.filters],
            "by_category": {
                cat.value: [f.name for f in self.filters if f.category == cat]
                for cat in FilterCategory
            },
        }
    
    def to_config_list(self) -> List[Dict[str, Any]]:
        """Export chain as list of filter configs"""
        return [
            FilterConfig(
                name=f.name,
                enabled=f.enabled,
                params=f.config,
                priority=f.priority,
            ).to_dict()
            for f in self._filters
        ]
    
    @classmethod
    def from_config_list(
        cls, 
        config_list: List[Dict[str, Any]],
        registry: Optional[FilterRegistry] = None,
    ) -> "FilterChain":
        """
        Create chain from list of filter configs.
        
        Args:
            config_list: List of filter configuration dicts
            registry: Filter registry to use
            
        Returns:
            New FilterChain instance
        """
        chain = cls(registry=registry)
        
        for config_dict in config_list:
            filter_config = FilterConfig.from_dict(config_dict)
            try:
                chain.add_from_config(filter_config)
            except ValueError as e:
                logger.warning(f"Could not add filter: {e}")
        
        return chain
    
    def __len__(self) -> int:
        """Number of filters in chain"""
        return len(self._filters)
    
    def __contains__(self, name: str) -> bool:
        """Check if filter name in chain"""
        return self.has(name)
    
    def __iter__(self):
        """Iterate over filters in priority order"""
        return iter(self.filters)
    
    def __repr__(self) -> str:
        enabled = len(self.enabled_filters)
        total = len(self._filters)
        return f"FilterChain(filters={enabled}/{total})"


# =============================================================================
# CHAIN BUILDER
# =============================================================================

class FilterChainBuilder:
    """
    Builder pattern for creating filter chains.
    
    Usage:
        chain = (
            FilterChainBuilder()
            .with_time_filters(sessions=["london"])
            .with_volatility_filters(min_atr=0.5)
            .with_protection(max_dd=10)
            .build()
        )
    """
    
    def __init__(self, registry: Optional[FilterRegistry] = None):
        """Initialize builder"""
        self.registry = registry or get_registry()
        self._configs: List[FilterConfig] = []
        self._short_circuit = True
    
    def add(
        self, 
        name: str, 
        enabled: bool = True, 
        **params
    ) -> "FilterChainBuilder":
        """
        Add a filter configuration.
        
        Args:
            name: Filter name
            enabled: Whether filter is enabled
            **params: Filter parameters
            
        Returns:
            Self for method chaining
        """
        self._configs.append(FilterConfig(
            name=name,
            enabled=enabled,
            params=params,
        ))
        return self
    
    def with_short_circuit(self, enabled: bool = True) -> "FilterChainBuilder":
        """Set short-circuit behavior"""
        self._short_circuit = enabled
        return self
    
    def build(self) -> FilterChain:
        """
        Build the filter chain.
        
        Returns:
            Configured FilterChain instance
        """
        chain = FilterChain(
            short_circuit=self._short_circuit,
            registry=self.registry,
        )
        
        for config in self._configs:
            try:
                chain.add_from_config(config)
            except ValueError as e:
                logger.warning(f"Could not add filter: {e}")
        
        return chain


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "ChainResult",
    "FilterChain",
    "FilterChainBuilder",
]
