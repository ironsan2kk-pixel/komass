"""
KOMAS v4.0 — Filter Manager
=============================

Unified filter management for bots.

FilterManager provides:
- Load filter configurations from database
- Create and manage filter instances
- Apply complete filter chain to signals
- Log filter decisions for debugging
- Provide filter statistics and summaries
- Save/restore filter state for persistence

Usage:
    # Create manager for a bot
    manager = FilterManager(bot_id="bot_123")
    
    # Load configuration from database
    await manager.load_config(db_session)
    
    # Apply filters to signal
    result = manager.apply_filters(signal, context)
    
    if result.is_passed:
        # Execute trade
        pass
    
    # After trade completes
    manager.on_trade_complete(trade_result)
    
    # Get statistics
    stats = manager.get_stats()

Chat #43: Filters Integration
Author: KOMAS Team
Version: 4.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Type
import logging
import json
import sqlite3
from pathlib import Path

from .base import (
    BaseFilter,
    Signal,
    SignalContext,
    FilterDecision,
    FilterConfig,
    FilterCategory,
    FilterPriority,
    FilterResult,
    create_pass_decision,
    create_block_decision,
)
from .chain import FilterChain, ChainResult
from .registry import FilterRegistry, discover_filters

logger = logging.getLogger(__name__)


# =============================================================================
# FILTER STATS
# =============================================================================

@dataclass
class FilterStats:
    """
    Track filter performance statistics.
    """
    total_signals: int = 0
    passed_signals: int = 0
    blocked_signals: int = 0
    
    # Breakdown by filter and category
    blocks_by_filter: Dict[str, int] = field(default_factory=dict)
    blocks_by_category: Dict[str, int] = field(default_factory=dict)
    
    # Pass rate by filter
    checks_by_filter: Dict[str, int] = field(default_factory=dict)
    passes_by_filter: Dict[str, int] = field(default_factory=dict)
    
    # Timing
    total_time_ms: float = 0.0
    avg_time_ms: float = 0.0
    max_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    
    # Timestamps
    first_check: Optional[datetime] = None
    last_check: Optional[datetime] = None
    
    def record_check(
        self, 
        result: ChainResult, 
        decisions: List[FilterDecision]
    ) -> None:
        """Record statistics from a filter check."""
        self.total_signals += 1
        
        if result.is_passed:
            self.passed_signals += 1
        else:
            self.blocked_signals += 1
            if result.blocked_by:
                self.blocks_by_filter[result.blocked_by] = \
                    self.blocks_by_filter.get(result.blocked_by, 0) + 1
        
        # Record per-filter stats
        for decision in decisions:
            filter_name = decision.filter_name
            self.checks_by_filter[filter_name] = \
                self.checks_by_filter.get(filter_name, 0) + 1
            
            if decision.result == FilterResult.PASS:
                self.passes_by_filter[filter_name] = \
                    self.passes_by_filter.get(filter_name, 0) + 1
        
        # Timing
        exec_time = result.execution_time_ms
        self.total_time_ms += exec_time
        self.avg_time_ms = self.total_time_ms / self.total_signals
        self.max_time_ms = max(self.max_time_ms, exec_time)
        self.min_time_ms = min(self.min_time_ms, exec_time) if self.min_time_ms != float('inf') else exec_time
        
        # Timestamps
        now = datetime.now()
        if self.first_check is None:
            self.first_check = now
        self.last_check = now
    
    def record_category_block(self, category: FilterCategory) -> None:
        """Record a block by category."""
        cat_name = category.value
        self.blocks_by_category[cat_name] = \
            self.blocks_by_category.get(cat_name, 0) + 1
    
    @property
    def pass_rate(self) -> float:
        """Calculate overall pass rate."""
        if self.total_signals == 0:
            return 0.0
        return self.passed_signals / self.total_signals * 100
    
    @property
    def block_rate(self) -> float:
        """Calculate overall block rate."""
        if self.total_signals == 0:
            return 0.0
        return self.blocked_signals / self.total_signals * 100
    
    def get_filter_pass_rate(self, filter_name: str) -> float:
        """Calculate pass rate for specific filter."""
        checks = self.checks_by_filter.get(filter_name, 0)
        if checks == 0:
            return 0.0
        passes = self.passes_by_filter.get(filter_name, 0)
        return passes / checks * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_signals": self.total_signals,
            "passed_signals": self.passed_signals,
            "blocked_signals": self.blocked_signals,
            "pass_rate": round(self.pass_rate, 2),
            "block_rate": round(self.block_rate, 2),
            "blocks_by_filter": self.blocks_by_filter.copy(),
            "blocks_by_category": self.blocks_by_category.copy(),
            "checks_by_filter": self.checks_by_filter.copy(),
            "passes_by_filter": self.passes_by_filter.copy(),
            "timing": {
                "total_ms": round(self.total_time_ms, 2),
                "avg_ms": round(self.avg_time_ms, 4),
                "max_ms": round(self.max_time_ms, 4),
                "min_ms": round(self.min_time_ms, 4) if self.min_time_ms != float('inf') else 0.0,
            },
            "first_check": self.first_check.isoformat() if self.first_check else None,
            "last_check": self.last_check.isoformat() if self.last_check else None,
        }
    
    def reset(self) -> None:
        """Reset all statistics."""
        self.total_signals = 0
        self.passed_signals = 0
        self.blocked_signals = 0
        self.blocks_by_filter = {}
        self.blocks_by_category = {}
        self.checks_by_filter = {}
        self.passes_by_filter = {}
        self.total_time_ms = 0.0
        self.avg_time_ms = 0.0
        self.max_time_ms = 0.0
        self.min_time_ms = float('inf')
        self.first_check = None
        self.last_check = None


# =============================================================================
# DECISION LOG
# =============================================================================

@dataclass
class DecisionLogEntry:
    """Single entry in the decision log."""
    timestamp: datetime
    signal_id: str
    symbol: str
    direction: str
    result: str  # 'pass' or 'block'
    blocked_by: Optional[str]
    reason: Optional[str]
    decisions: List[Dict[str, Any]]
    execution_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "direction": self.direction,
            "result": self.result,
            "blocked_by": self.blocked_by,
            "reason": self.reason,
            "decisions": self.decisions,
            "execution_time_ms": round(self.execution_time_ms, 4),
        }


class DecisionLog:
    """
    Log of filter decisions for debugging and analysis.
    Maintains a rolling buffer of recent decisions.
    """
    
    def __init__(self, max_entries: int = 1000):
        """
        Initialize decision log.
        
        Args:
            max_entries: Maximum entries to keep (FIFO)
        """
        self.max_entries = max_entries
        self.entries: List[DecisionLogEntry] = []
    
    def add(
        self, 
        signal: Signal, 
        result: ChainResult,
        signal_id: Optional[str] = None
    ) -> DecisionLogEntry:
        """
        Add a decision to the log.
        
        Args:
            signal: The signal that was evaluated
            result: The filter chain result
            signal_id: Optional custom signal ID
        """
        entry = DecisionLogEntry(
            timestamp=datetime.now(),
            signal_id=signal_id or f"{signal.symbol}_{signal.timestamp.timestamp():.0f}",
            symbol=signal.symbol,
            direction=signal.direction,
            result="pass" if result.is_passed else "block",
            blocked_by=result.blocked_by,
            reason=result.blocking_reason,
            decisions=[
                {
                    "filter": d.filter_name,
                    "result": d.result.value,
                    "reason": d.reason,
                }
                for d in result.decisions
            ],
            execution_time_ms=result.execution_time_ms,
        )
        
        self.entries.append(entry)
        
        # Trim if over max
        if len(self.entries) > self.max_entries:
            self.entries = self.entries[-self.max_entries:]
        
        return entry
    
    def get_recent(self, n: int = 100) -> List[DecisionLogEntry]:
        """Get N most recent entries."""
        return self.entries[-n:]
    
    def get_by_symbol(self, symbol: str, n: int = 100) -> List[DecisionLogEntry]:
        """Get entries for a specific symbol."""
        return [e for e in self.entries if e.symbol == symbol][-n:]
    
    def get_blocked(self, n: int = 100) -> List[DecisionLogEntry]:
        """Get blocked entries."""
        return [e for e in self.entries if e.result == "block"][-n:]
    
    def get_by_filter(self, filter_name: str, n: int = 100) -> List[DecisionLogEntry]:
        """Get entries blocked by a specific filter."""
        return [e for e in self.entries if e.blocked_by == filter_name][-n:]
    
    def clear(self) -> None:
        """Clear all entries."""
        self.entries.clear()
    
    def to_list(self) -> List[Dict[str, Any]]:
        """Convert to list of dicts."""
        return [e.to_dict() for e in self.entries]
    
    def __len__(self) -> int:
        return len(self.entries)


# =============================================================================
# FILTER MANAGER
# =============================================================================

class FilterManager:
    """
    Unified filter management for bots.
    
    Responsibilities:
    - Load filter configs from database
    - Create filter instances
    - Apply filter chain to signals
    - Log decisions
    - Provide statistics
    - Persist and restore state
    """
    
    def __init__(
        self, 
        bot_id: str,
        log_decisions: bool = True,
        max_log_entries: int = 1000
    ):
        """
        Initialize FilterManager for a specific bot.
        
        Args:
            bot_id: The bot ID this manager is for
            log_decisions: Whether to log all filter decisions
            max_log_entries: Maximum decision log entries to keep
        """
        self.bot_id = bot_id
        self.log_decisions = log_decisions
        
        # Ensure filters are discovered
        discover_filters()
        
        # Filter chain (populated by load_config)
        self.chain: Optional[FilterChain] = None
        
        # Filter instances by name
        self.filters: Dict[str, BaseFilter] = {}
        
        # Configuration
        self.config: Dict[str, FilterConfig] = {}
        
        # Statistics
        self.stats: FilterStats = FilterStats()
        
        # Decision log
        self.decision_log: DecisionLog = DecisionLog(max_entries=max_log_entries)
        
        # State
        self._loaded = False
        self._last_load_time: Optional[datetime] = None
        
        logger.info(f"FilterManager created for bot: {bot_id}")
    
    # -------------------------------------------------------------------------
    # Configuration Loading
    # -------------------------------------------------------------------------
    
    def load_config(self, db_path: str) -> None:
        """
        Load filter configuration from SQLite database.
        
        Args:
            db_path: Path to SQLite database file
        """
        logger.info(f"Loading filter config for bot {self.bot_id} from {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Ensure table exists
            self._ensure_table(cursor)
            
            # Load configs for this bot
            cursor.execute("""
                SELECT filter_name, enabled, config 
                FROM bot_filter_configs 
                WHERE bot_id = ?
            """, (self.bot_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Parse configs
            self.config = {}
            for row in rows:
                config_data = json.loads(row["config"]) if row["config"] else {}
                config_data["enabled"] = bool(row["enabled"])
                
                self.config[row["filter_name"]] = FilterConfig(
                    filter_name=row["filter_name"],
                    enabled=config_data.get("enabled", True),
                    params=config_data
                )
            
            # Create filter instances
            self._create_filter_instances()
            
            # Build chain
            self._build_chain()
            
            self._loaded = True
            self._last_load_time = datetime.now()
            
            logger.info(f"Loaded {len(self.config)} filter configs, created {len(self.filters)} instances")
            
        except Exception as e:
            logger.error(f"Failed to load filter config: {e}")
            raise
    
    def load_config_from_dict(self, config: Dict[str, Dict[str, Any]]) -> None:
        """
        Load filter configuration from a dictionary.
        
        Args:
            config: Dict of filter_name -> config_dict
        """
        self.config = {}
        for name, cfg in config.items():
            self.config[name] = FilterConfig(
                filter_name=name,
                enabled=cfg.get("enabled", True),
                params=cfg
            )
        
        self._create_filter_instances()
        self._build_chain()
        
        self._loaded = True
        self._last_load_time = datetime.now()
        
        logger.info(f"Loaded {len(self.config)} filter configs from dict")
    
    def save_config(self, db_path: str) -> None:
        """
        Save current filter configuration to database.
        
        Args:
            db_path: Path to SQLite database file
        """
        logger.info(f"Saving filter config for bot {self.bot_id} to {db_path}")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Ensure table exists
            self._ensure_table(cursor)
            
            # Save each config
            for name, cfg in self.config.items():
                config_json = json.dumps(cfg.params)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO bot_filter_configs 
                    (bot_id, filter_name, enabled, config, updated_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (self.bot_id, name, cfg.enabled, config_json))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(self.config)} filter configs")
            
        except Exception as e:
            logger.error(f"Failed to save filter config: {e}")
            raise
    
    def _ensure_table(self, cursor: sqlite3.Cursor) -> None:
        """Ensure the bot_filter_configs table exists."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bot_filter_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bot_id TEXT NOT NULL,
                filter_name TEXT NOT NULL,
                enabled BOOLEAN DEFAULT TRUE,
                config JSON NOT NULL DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(bot_id, filter_name)
            )
        """)
        
        # Create index for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bot_filter_configs_bot_id 
            ON bot_filter_configs(bot_id)
        """)
    
    def _create_filter_instances(self) -> None:
        """Create filter instances from loaded config."""
        self.filters = {}
        
        for name, cfg in self.config.items():
            filter_class = FilterRegistry.get(name)
            if filter_class is None:
                logger.warning(f"Unknown filter: {name}, skipping")
                continue
            
            try:
                instance = filter_class(cfg.to_dict())
                self.filters[name] = instance
                logger.debug(f"Created filter instance: {name}")
            except Exception as e:
                logger.error(f"Failed to create filter {name}: {e}")
    
    def _build_chain(self) -> None:
        """Build filter chain from instances."""
        filter_list = list(self.filters.values())
        self.chain = FilterChain(
            filters=filter_list,
            short_circuit=True,
            log_decisions=self.log_decisions
        )
        logger.debug(f"Built filter chain with {len(filter_list)} filters")
    
    # -------------------------------------------------------------------------
    # Filter Application
    # -------------------------------------------------------------------------
    
    def apply_filters(
        self, 
        signal: Signal, 
        context: SignalContext,
        signal_id: Optional[str] = None
    ) -> ChainResult:
        """
        Apply all configured filters to a signal.
        
        Args:
            signal: The trading signal to evaluate
            context: Market and portfolio context
            signal_id: Optional custom ID for logging
            
        Returns:
            ChainResult with all filter decisions
        """
        if not self._loaded or self.chain is None:
            logger.warning("FilterManager not loaded, creating pass result")
            return ChainResult(
                is_blocked=False,
                passed_filters=["(not configured)"],
                start_time=datetime.now(),
                end_time=datetime.now()
            )
        
        # Apply chain
        result = self.chain.apply(signal, context)
        
        # Update stats
        self.stats.record_check(result, result.decisions)
        
        # Record category if blocked
        if result.is_blocked and result.blocked_by:
            filter_instance = self.filters.get(result.blocked_by)
            if filter_instance:
                self.stats.record_category_block(filter_instance.category)
        
        # Log decision
        if self.log_decisions:
            entry = self.decision_log.add(signal, result, signal_id)
            logger.debug(
                f"Filter decision: {entry.symbol} {entry.direction} -> "
                f"{entry.result}" + (f" (blocked by {entry.blocked_by})" if entry.blocked_by else "")
            )
        
        return result
    
    def check_single_filter(
        self,
        filter_name: str,
        signal: Signal,
        context: SignalContext
    ) -> Optional[FilterDecision]:
        """
        Check a single filter (for testing/debugging).
        
        Args:
            filter_name: Name of the filter to check
            signal: The trading signal
            context: Market context
            
        Returns:
            FilterDecision or None if filter not found
        """
        filter_instance = self.filters.get(filter_name)
        if filter_instance is None:
            logger.warning(f"Filter not found: {filter_name}")
            return None
        
        try:
            return filter_instance.should_allow(signal, context)
        except Exception as e:
            logger.error(f"Error in filter {filter_name}: {e}")
            return None
    
    # -------------------------------------------------------------------------
    # Trade Lifecycle
    # -------------------------------------------------------------------------
    
    def on_trade_complete(self, trade_result: Dict[str, Any]) -> None:
        """
        Notify filters of trade completion.
        Called after a trade closes to update filter state.
        
        Args:
            trade_result: Trade result data including:
                - symbol: str
                - direction: str
                - pnl: float
                - pnl_percent: float
                - exit_reason: str
                - exit_time: datetime
        """
        if self.chain is None:
            return
        
        logger.debug(f"Trade complete notification: {trade_result.get('symbol')} -> {trade_result.get('exit_reason')}")
        
        self.chain.on_trade_complete(trade_result)
    
    def reset_filters(self) -> None:
        """
        Reset all filter states.
        Call this at start of new backtest or when resetting bot.
        """
        if self.chain is None:
            return
        
        self.chain.reset()
        logger.info(f"Reset filters for bot {self.bot_id}")
    
    # -------------------------------------------------------------------------
    # Filter Management
    # -------------------------------------------------------------------------
    
    def enable_filter(self, filter_name: str) -> bool:
        """Enable a filter by name."""
        if filter_name in self.config:
            self.config[filter_name].enabled = True
        
        if filter_name in self.filters:
            self.filters[filter_name].enabled = True
            return True
        
        return False
    
    def disable_filter(self, filter_name: str) -> bool:
        """Disable a filter by name."""
        if filter_name in self.config:
            self.config[filter_name].enabled = False
        
        if filter_name in self.filters:
            self.filters[filter_name].enabled = False
            return True
        
        return False
    
    def update_filter_config(
        self, 
        filter_name: str, 
        config: Dict[str, Any]
    ) -> bool:
        """
        Update configuration for a specific filter.
        
        Args:
            filter_name: Filter to update
            config: New configuration
            
        Returns:
            True if successful
        """
        filter_class = FilterRegistry.get(filter_name)
        if filter_class is None:
            logger.error(f"Unknown filter: {filter_name}")
            return False
        
        try:
            # Create new instance with updated config
            new_instance = filter_class(config)
            
            # Update stores
            self.filters[filter_name] = new_instance
            self.config[filter_name] = FilterConfig(
                filter_name=filter_name,
                enabled=config.get("enabled", True),
                params=config
            )
            
            # Rebuild chain
            self._build_chain()
            
            logger.info(f"Updated filter config: {filter_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update filter {filter_name}: {e}")
            return False
    
    def add_filter(self, filter_name: str, config: Dict[str, Any]) -> bool:
        """
        Add a new filter to the manager.
        
        Args:
            filter_name: Name of filter to add
            config: Filter configuration
            
        Returns:
            True if successful
        """
        if filter_name in self.filters:
            logger.warning(f"Filter already exists: {filter_name}, use update_filter_config instead")
            return False
        
        return self.update_filter_config(filter_name, config)
    
    def remove_filter(self, filter_name: str) -> bool:
        """
        Remove a filter from the manager.
        
        Args:
            filter_name: Name of filter to remove
            
        Returns:
            True if removed
        """
        if filter_name not in self.filters:
            return False
        
        del self.filters[filter_name]
        if filter_name in self.config:
            del self.config[filter_name]
        
        self._build_chain()
        logger.info(f"Removed filter: {filter_name}")
        return True
    
    # -------------------------------------------------------------------------
    # Statistics and Info
    # -------------------------------------------------------------------------
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive filter statistics.
        
        Returns:
            Dict with statistics including:
            - Overall pass/block rates
            - Per-filter performance
            - Timing statistics
            - Category breakdown
        """
        return {
            "bot_id": self.bot_id,
            "loaded": self._loaded,
            "last_load_time": self._last_load_time.isoformat() if self._last_load_time else None,
            "filter_count": len(self.filters),
            "enabled_count": sum(1 for f in self.filters.values() if f.enabled),
            "statistics": self.stats.to_dict(),
            "log_entries": len(self.decision_log),
        }
    
    def get_filter_list(self) -> List[Dict[str, Any]]:
        """Get list of all configured filters with their status."""
        result = []
        for name, instance in self.filters.items():
            cfg = self.config.get(name)
            result.append({
                "name": name,
                "category": instance.category.value,
                "priority": instance.priority.name,
                "enabled": instance.enabled,
                "description": instance.description,
                "config": cfg.params if cfg else {},
                "pass_rate": round(self.stats.get_filter_pass_rate(name), 2),
                "block_count": self.stats.blocks_by_filter.get(name, 0),
            })
        
        # Sort by priority
        result.sort(key=lambda x: FilterPriority[x["priority"]].value)
        return result
    
    def get_filter_summary(self) -> Dict[str, Any]:
        """Get summary of filters by category."""
        summary = {
            "by_category": {},
            "enabled": [],
            "disabled": [],
        }
        
        for name, instance in self.filters.items():
            cat = instance.category.value
            if cat not in summary["by_category"]:
                summary["by_category"][cat] = []
            summary["by_category"][cat].append(name)
            
            if instance.enabled:
                summary["enabled"].append(name)
            else:
                summary["disabled"].append(name)
        
        return summary
    
    def get_decision_log(
        self, 
        n: int = 100, 
        symbol: Optional[str] = None,
        blocked_only: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get recent filter decisions.
        
        Args:
            n: Number of entries to return
            symbol: Filter by symbol (optional)
            blocked_only: Only return blocked decisions
        """
        if symbol:
            entries = self.decision_log.get_by_symbol(symbol, n)
        elif blocked_only:
            entries = self.decision_log.get_blocked(n)
        else:
            entries = self.decision_log.get_recent(n)
        
        return [e.to_dict() for e in entries]
    
    def reset_stats(self) -> None:
        """Reset statistics."""
        self.stats.reset()
        self.decision_log.clear()
        logger.info(f"Reset stats for bot {self.bot_id}")
    
    # -------------------------------------------------------------------------
    # Available Filters
    # -------------------------------------------------------------------------
    
    @staticmethod
    def get_available_filters() -> Dict[str, Dict[str, Any]]:
        """
        Get all available filters from registry.
        
        Returns:
            Dict of filter_name -> filter info
        """
        discover_filters()
        return FilterRegistry.get_schema()
    
    @staticmethod
    def get_available_filter_names() -> List[str]:
        """Get list of all available filter names."""
        discover_filters()
        return FilterRegistry.get_names()
    
    @staticmethod
    def get_filters_by_category(category: str) -> Dict[str, Type[BaseFilter]]:
        """Get filters by category name."""
        discover_filters()
        try:
            cat = FilterCategory(category)
            return FilterRegistry.get_by_category(cat)
        except ValueError:
            return {}
    
    # -------------------------------------------------------------------------
    # Presets / Profiles
    # -------------------------------------------------------------------------
    
    def apply_profile(self, profile: str) -> bool:
        """
        Apply a filter profile (preset configuration).
        
        Args:
            profile: Profile name ('conservative', 'balanced', 'aggressive', 'minimal')
            
        Returns:
            True if successful
        """
        profiles = get_filter_profiles()
        if profile not in profiles:
            logger.error(f"Unknown profile: {profile}")
            return False
        
        self.load_config_from_dict(profiles[profile])
        logger.info(f"Applied filter profile: {profile}")
        return True
    
    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------
    
    def export_config(self) -> Dict[str, Any]:
        """Export current configuration as dict."""
        return {
            name: cfg.to_dict()
            for name, cfg in self.config.items()
        }
    
    def import_config(self, config: Dict[str, Any]) -> None:
        """Import configuration from dict."""
        self.load_config_from_dict(config)
    
    def __repr__(self) -> str:
        status = "loaded" if self._loaded else "not loaded"
        count = len(self.filters)
        return f"<FilterManager(bot={self.bot_id}, {count} filters, {status})>"


# =============================================================================
# FILTER PROFILES
# =============================================================================

def get_filter_profiles() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Get predefined filter profiles.
    
    Returns:
        Dict of profile_name -> filter configurations
    """
    return {
        "minimal": {
            # Only basic time filters
            "session_filter": {
                "enabled": True,
                "sessions": ["all"],
            },
        },
        
        "conservative": {
            # Time filters
            "session_filter": {
                "enabled": True,
                "sessions": ["europe", "us"],
                "allow_overlaps": True,
            },
            "weekday_filter": {
                "enabled": True,
                "allowed_days": [0, 1, 2, 3, 4],  # Mon-Fri
            },
            "cooldown_filter": {
                "enabled": True,
                "cooldown_minutes": 30,
                "loss_cooldown_minutes": 60,
            },
            
            # Volatility filters
            "atr_filter": {
                "enabled": True,
                "min_atr": 1.0,
                "max_atr": 4.0,
                "use_atr_percent": True,
            },
            "volume_filter": {
                "enabled": True,
                "min_volume_ratio": 1.0,
            },
            "extreme_filter": {
                "enabled": True,
                "atr_multiplier": 2.5,
                "pause_minutes": 120,
            },
            
            # Portfolio filters
            "correlation_filter": {
                "enabled": True,
                "max_correlated_positions": 1,
            },
            "direction_filter": {
                "enabled": True,
                "max_long_positions": 3,
                "max_short_positions": 3,
            },
            "sector_filter": {
                "enabled": True,
                "max_per_sector": 1,
            },
        },
        
        "balanced": {
            # Time filters
            "session_filter": {
                "enabled": True,
                "sessions": ["asia", "europe", "us"],
            },
            "weekday_filter": {
                "enabled": True,
                "allowed_days": [0, 1, 2, 3, 4, 5, 6],  # All week
            },
            "cooldown_filter": {
                "enabled": True,
                "cooldown_minutes": 15,
                "loss_cooldown_minutes": 30,
            },
            
            # Volatility filters
            "atr_filter": {
                "enabled": True,
                "min_atr": 0.5,
                "max_atr": 6.0,
                "use_atr_percent": True,
            },
            "volume_filter": {
                "enabled": True,
                "min_volume_ratio": 0.8,
            },
            "extreme_filter": {
                "enabled": True,
                "atr_multiplier": 3.0,
                "pause_minutes": 60,
            },
            
            # Portfolio filters
            "correlation_filter": {
                "enabled": True,
                "max_correlated_positions": 2,
            },
            "direction_filter": {
                "enabled": True,
                "max_long_positions": 5,
                "max_short_positions": 5,
            },
            "sector_filter": {
                "enabled": True,
                "max_per_sector": 2,
            },
        },
        
        "aggressive": {
            # Time filters
            "session_filter": {
                "enabled": False,
            },
            "weekday_filter": {
                "enabled": False,
            },
            "cooldown_filter": {
                "enabled": True,
                "cooldown_minutes": 5,
                "loss_cooldown_minutes": 15,
            },
            
            # Volatility filters
            "atr_filter": {
                "enabled": True,
                "min_atr": 0.3,
                "max_atr": 10.0,
                "use_atr_percent": True,
            },
            "volume_filter": {
                "enabled": False,
            },
            "extreme_filter": {
                "enabled": True,
                "atr_multiplier": 4.0,
                "pause_minutes": 30,
            },
            
            # Portfolio filters
            "correlation_filter": {
                "enabled": True,
                "max_correlated_positions": 3,
            },
            "direction_filter": {
                "enabled": True,
                "max_long_positions": 10,
                "max_short_positions": 10,
            },
            "sector_filter": {
                "enabled": False,
            },
        },
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def create_filter_manager(
    bot_id: str,
    config: Optional[Dict[str, Dict[str, Any]]] = None,
    profile: Optional[str] = None,
    db_path: Optional[str] = None
) -> FilterManager:
    """
    Create and configure a FilterManager.
    
    Args:
        bot_id: Bot identifier
        config: Direct configuration dict (optional)
        profile: Profile name to apply (optional)
        db_path: Database path to load from (optional)
        
    Returns:
        Configured FilterManager
        
    Note:
        Priority: config > db_path > profile > empty
    """
    manager = FilterManager(bot_id)
    
    if config:
        manager.load_config_from_dict(config)
    elif db_path:
        manager.load_config(db_path)
    elif profile:
        manager.apply_profile(profile)
    else:
        # Create empty but valid manager
        manager.load_config_from_dict({})
    
    return manager


def validate_filter_config(filter_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate filter configuration.
    
    Args:
        filter_name: Name of the filter
        config: Configuration to validate
        
    Returns:
        Dict with validation results:
        - valid: bool
        - errors: List[str]
        - warnings: List[str]
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
    }
    
    filter_class = FilterRegistry.get(filter_name)
    if filter_class is None:
        result["valid"] = False
        result["errors"].append(f"Unknown filter: {filter_name}")
        return result
    
    # Get schema
    try:
        temp_instance = filter_class({})
        schema = temp_instance.get_config_schema()
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Failed to get schema: {e}")
        return result
    
    # Check required fields
    for key, props in schema.items():
        if props.get("required", False) and key not in config:
            result["valid"] = False
            result["errors"].append(f"Missing required field: {key}")
    
    # Check types and ranges
    for key, value in config.items():
        if key not in schema:
            result["warnings"].append(f"Unknown config key: {key}")
            continue
        
        props = schema[key]
        expected_type = props.get("type", "str")
        
        # Type check
        type_map = {
            "int": int,
            "float": (int, float),
            "bool": bool,
            "str": str,
            "list": list,
        }
        
        if expected_type in type_map:
            if not isinstance(value, type_map[expected_type]):
                result["valid"] = False
                result["errors"].append(f"Invalid type for {key}: expected {expected_type}")
                continue
        
        # Range check for numbers
        if isinstance(value, (int, float)):
            if "min" in props and value < props["min"]:
                result["errors"].append(f"{key} below minimum: {value} < {props['min']}")
                result["valid"] = False
            if "max" in props and value > props["max"]:
                result["errors"].append(f"{key} above maximum: {value} > {props['max']}")
                result["valid"] = False
        
        # Options check
        if "options" in props and value not in props["options"]:
            result["warnings"].append(f"{key} value '{value}' not in options: {props['options']}")
    
    return result


def get_filter_categories() -> List[Dict[str, Any]]:
    """
    Get all filter categories with their filters.
    
    Returns:
        List of category info dicts
    """
    discover_filters()
    
    categories = []
    for category in FilterCategory:
        filters = FilterRegistry.get_by_category(category)
        categories.append({
            "name": category.value,
            "display_name": category.value.title(),
            "filter_count": len(filters),
            "filters": list(filters.keys()),
        })
    
    return categories
