"""
KOMAS v4.0 — Filter Chain
==========================

Executes filters in priority order and aggregates results.

Features:
- Priority-based execution (CRITICAL → HIGH → MEDIUM → LOW)
- Short-circuit on first BLOCK (configurable)
- Detailed logging and statistics
- Batch processing support

Usage:
    chain = FilterChain([session_filter, weekday_filter, cooldown_filter])
    result = chain.apply(signal, context)
    
    if result.is_blocked:
        print(f"Signal blocked: {result.blocking_reason}")
    else:
        print(f"Signal passed all {len(result.passed_filters)} filters")

Chat #37: Filters Architecture
Author: KOMAS Team
Version: 4.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime

from .base import (
    BaseFilter, 
    Signal, 
    SignalContext, 
    FilterDecision,
    FilterResult,
    FilterPriority,
    FilterCategory
)

logger = logging.getLogger(__name__)


# =============================================================================
# CHAIN RESULT
# =============================================================================

@dataclass
class ChainResult:
    """
    Result of applying a filter chain to a signal.
    """
    # Overall result
    is_blocked: bool
    
    # Lists of filter names
    passed_filters: List[str] = field(default_factory=list)
    blocked_by: Optional[str] = None
    skipped_filters: List[str] = field(default_factory=list)
    
    # Detailed decisions
    decisions: List[FilterDecision] = field(default_factory=list)
    
    # Timing
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def is_passed(self) -> bool:
        return not self.is_blocked
    
    @property
    def blocking_reason(self) -> Optional[str]:
        """Get the reason for blocking"""
        if not self.is_blocked:
            return None
        for d in self.decisions:
            if d.is_blocked:
                return d.reason
        return None
    
    @property
    def execution_time_ms(self) -> float:
        """Get execution time in milliseconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() * 1000
        return 0.0
    
    @property
    def summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        return {
            "passed": self.is_passed,
            "passed_count": len(self.passed_filters),
            "skipped_count": len(self.skipped_filters),
            "blocked_by": self.blocked_by,
            "blocking_reason": self.blocking_reason,
            "execution_time_ms": self.execution_time_ms
        }
    
    def __str__(self) -> str:
        if self.is_passed:
            return f"✅ PASSED ({len(self.passed_filters)} filters)"
        else:
            return f"❌ BLOCKED by {self.blocked_by}: {self.blocking_reason}"


# =============================================================================
# FILTER CHAIN
# =============================================================================

class FilterChain:
    """
    Executes a chain of filters in priority order.
    """
    
    def __init__(
        self,
        filters: Optional[List[BaseFilter]] = None,
        short_circuit: bool = True,
        log_decisions: bool = True
    ):
        """
        Initialize filter chain.
        
        Args:
            filters: List of filter instances
            short_circuit: Stop on first BLOCK (default True)
            log_decisions: Log each filter decision (default True)
        """
        self.filters = filters or []
        self.short_circuit = short_circuit
        self.log_decisions = log_decisions
        
        # Sort by priority
        self._sort_filters()
        
        # Statistics
        self._stats = {
            "total_calls": 0,
            "total_passed": 0,
            "total_blocked": 0,
            "blocks_by_filter": {},
            "avg_execution_time_ms": 0.0
        }
    
    def _sort_filters(self) -> None:
        """Sort filters by priority (CRITICAL first)"""
        self.filters = sorted(
            self.filters, 
            key=lambda f: f.priority.value
        )
    
    def add_filter(self, filter_instance: BaseFilter) -> None:
        """
        Add a filter to the chain.
        
        Args:
            filter_instance: Filter to add
        """
        self.filters.append(filter_instance)
        self._sort_filters()
        logger.debug(f"Added filter: {filter_instance.name}")
    
    def remove_filter(self, name: str) -> bool:
        """
        Remove a filter by name.
        
        Args:
            name: Filter name to remove
            
        Returns:
            True if removed, False if not found
        """
        for i, f in enumerate(self.filters):
            if f.name == name:
                del self.filters[i]
                logger.debug(f"Removed filter: {name}")
                return True
        return False
    
    def get_filter(self, name: str) -> Optional[BaseFilter]:
        """Get a filter by name"""
        for f in self.filters:
            if f.name == name:
                return f
        return None
    
    def apply(self, signal: Signal, context: SignalContext) -> ChainResult:
        """
        Apply all filters to a signal.
        
        Args:
            signal: The trading signal
            context: Market and portfolio context
            
        Returns:
            ChainResult with all decisions
        """
        start_time = datetime.now()
        result = ChainResult(
            is_blocked=False,
            start_time=start_time
        )
        
        self._stats["total_calls"] += 1
        
        for filter_instance in self.filters:
            # Skip disabled filters
            if not filter_instance.enabled:
                result.skipped_filters.append(filter_instance.name)
                continue
            
            try:
                decision = filter_instance.should_allow(signal, context)
                result.decisions.append(decision)
                
                if self.log_decisions:
                    logger.debug(str(decision))
                
                if decision.result == FilterResult.PASS:
                    result.passed_filters.append(filter_instance.name)
                    
                elif decision.result == FilterResult.BLOCK:
                    result.is_blocked = True
                    result.blocked_by = filter_instance.name
                    
                    # Update stats
                    self._stats["total_blocked"] += 1
                    self._stats["blocks_by_filter"][filter_instance.name] = \
                        self._stats["blocks_by_filter"].get(filter_instance.name, 0) + 1
                    
                    if self.short_circuit:
                        # Stop processing on first block
                        break
                        
                elif decision.result == FilterResult.SKIP:
                    result.skipped_filters.append(filter_instance.name)
                    
            except Exception as e:
                logger.error(f"Filter error in {filter_instance.name}: {e}")
                # Continue to next filter on error
                result.skipped_filters.append(filter_instance.name)
        
        result.end_time = datetime.now()
        
        if not result.is_blocked:
            self._stats["total_passed"] += 1
        
        # Update average execution time
        current_avg = self._stats["avg_execution_time_ms"]
        new_time = result.execution_time_ms
        total_calls = self._stats["total_calls"]
        self._stats["avg_execution_time_ms"] = (
            (current_avg * (total_calls - 1) + new_time) / total_calls
        )
        
        return result
    
    def apply_batch(
        self, 
        signals: List[Tuple[Signal, SignalContext]]
    ) -> List[ChainResult]:
        """
        Apply filters to multiple signals.
        
        Args:
            signals: List of (signal, context) tuples
            
        Returns:
            List of ChainResults
        """
        return [self.apply(signal, context) for signal, context in signals]
    
    def on_trade_complete(self, trade_result: Dict[str, Any]) -> None:
        """
        Notify all filters of trade completion.
        
        Args:
            trade_result: Trade result data
        """
        for f in self.filters:
            try:
                f.on_trade_complete(trade_result)
            except Exception as e:
                logger.error(f"Error in {f.name}.on_trade_complete: {e}")
    
    def reset(self) -> None:
        """Reset all filters"""
        for f in self.filters:
            try:
                f.reset()
            except Exception as e:
                logger.error(f"Error resetting {f.name}: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get chain statistics"""
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """Reset statistics"""
        self._stats = {
            "total_calls": 0,
            "total_passed": 0,
            "total_blocked": 0,
            "blocks_by_filter": {},
            "avg_execution_time_ms": 0.0
        }
    
    def get_filter_list(self) -> List[Dict[str, Any]]:
        """Get list of filters with their status"""
        return [
            {
                "name": f.name,
                "category": f.category.value,
                "priority": f.priority.name,
                "enabled": f.enabled,
                "description": f.description
            }
            for f in self.filters
        ]
    
    def enable_filter(self, name: str) -> bool:
        """Enable a filter by name"""
        f = self.get_filter(name)
        if f:
            f.enabled = True
            return True
        return False
    
    def disable_filter(self, name: str) -> bool:
        """Disable a filter by name"""
        f = self.get_filter(name)
        if f:
            f.enabled = False
            return True
        return False
    
    def __len__(self) -> int:
        return len(self.filters)
    
    def __repr__(self) -> str:
        enabled = sum(1 for f in self.filters if f.enabled)
        return f"<FilterChain({enabled}/{len(self.filters)} enabled)>"


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_chain_from_config(
    config: Dict[str, Dict],
    short_circuit: bool = True
) -> FilterChain:
    """
    Create a filter chain from configuration.
    
    Args:
        config: Dict of filter_name -> filter_config
        short_circuit: Stop on first block
        
    Returns:
        Configured FilterChain
    """
    from .registry import FilterRegistry
    
    filters = []
    for name, filter_config in config.items():
        filter_class = FilterRegistry.get(name)
        if filter_class is None:
            logger.warning(f"Unknown filter: {name}, skipping")
            continue
        
        try:
            instance = filter_class(filter_config)
            filters.append(instance)
        except Exception as e:
            logger.error(f"Failed to create filter {name}: {e}")
    
    return FilterChain(filters, short_circuit=short_circuit)
