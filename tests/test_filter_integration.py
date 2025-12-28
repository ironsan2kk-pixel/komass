"""
KOMAS v4.0 — Filter Integration Tests
======================================

Comprehensive tests for FilterManager and filter integration.

Chat #43: Filters Integration
Author: KOMAS Team
Version: 4.0
"""

import pytest
import tempfile
import os
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import test utilities
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

from filters.base import (
    Signal, 
    SignalContext, 
    FilterDecision,
    FilterResult,
    FilterCategory,
    FilterPriority,
    create_pass_decision,
    create_block_decision,
)
from filters.chain import FilterChain, ChainResult
from filters.registry import FilterRegistry, discover_filters
from filters.manager import (
    FilterManager,
    FilterStats,
    DecisionLog,
    DecisionLogEntry,
    get_filter_profiles,
    create_filter_manager,
    validate_filter_config,
    get_filter_categories,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_signal():
    """Create a sample signal for testing."""
    return Signal(
        symbol="BTCUSDT",
        direction="long",
        entry_price=50000.0,
        timestamp=datetime.now(),
        timeframe="1h",
        indicator="trg",
    )


@pytest.fixture
def sample_context():
    """Create a sample context for testing."""
    return SignalContext(
        current_time=datetime.now(),
        current_price=50000.0,
        atr=1500.0,
        volume=1000000.0,
        avg_volume=800000.0,
        open_positions=[],
        recent_trades=[],
        equity_curve=[10000, 10100, 10050, 10200],
        current_equity=10200.0,
        starting_equity=10000.0,
    )


@pytest.fixture
def temp_db_path():
    """Create temporary database path."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        path = f.name
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def sample_chain_result():
    """Create a sample chain result."""
    return ChainResult(
        is_blocked=False,
        passed_filters=["session_filter", "atr_filter"],
        blocked_by=None,
        skipped_filters=["volume_filter"],
        decisions=[
            create_pass_decision("session_filter", "Session allowed"),
            create_pass_decision("atr_filter", "ATR in range"),
        ],
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(milliseconds=5),
    )


@pytest.fixture
def blocked_chain_result():
    """Create a blocked chain result."""
    return ChainResult(
        is_blocked=True,
        passed_filters=["session_filter"],
        blocked_by="atr_filter",
        skipped_filters=[],
        decisions=[
            create_pass_decision("session_filter", "Session allowed"),
            create_block_decision("atr_filter", "ATR too high"),
        ],
        start_time=datetime.now(),
        end_time=datetime.now() + timedelta(milliseconds=3),
    )


# =============================================================================
# FILTER STATS TESTS
# =============================================================================

class TestFilterStats:
    """Tests for FilterStats class."""
    
    def test_stats_initialization(self):
        """Test stats are initialized to zero."""
        stats = FilterStats()
        assert stats.total_signals == 0
        assert stats.passed_signals == 0
        assert stats.blocked_signals == 0
        assert stats.pass_rate == 0.0
    
    def test_record_passed_check(self, sample_chain_result):
        """Test recording a passed check."""
        stats = FilterStats()
        stats.record_check(sample_chain_result, sample_chain_result.decisions)
        assert stats.total_signals == 1
        assert stats.passed_signals == 1
        assert stats.blocked_signals == 0
    
    def test_record_blocked_check(self, blocked_chain_result):
        """Test recording a blocked check."""
        stats = FilterStats()
        stats.record_check(blocked_chain_result, blocked_chain_result.decisions)
        assert stats.total_signals == 1
        assert stats.blocked_signals == 1
        assert "atr_filter" in stats.blocks_by_filter
    
    def test_multiple_checks(self, sample_chain_result, blocked_chain_result):
        """Test multiple checks accumulate correctly."""
        stats = FilterStats()
        stats.record_check(sample_chain_result, sample_chain_result.decisions)
        stats.record_check(sample_chain_result, sample_chain_result.decisions)
        stats.record_check(blocked_chain_result, blocked_chain_result.decisions)
        assert stats.total_signals == 3
        assert stats.passed_signals == 2
        assert stats.blocked_signals == 1
    
    def test_stats_to_dict(self, sample_chain_result):
        """Test stats serialization."""
        stats = FilterStats()
        stats.record_check(sample_chain_result, sample_chain_result.decisions)
        data = stats.to_dict()
        assert "total_signals" in data
        assert "pass_rate" in data
    
    def test_stats_reset(self, sample_chain_result):
        """Test stats reset."""
        stats = FilterStats()
        stats.record_check(sample_chain_result, sample_chain_result.decisions)
        stats.reset()
        assert stats.total_signals == 0


# =============================================================================
# DECISION LOG TESTS
# =============================================================================

class TestDecisionLog:
    """Tests for DecisionLog class."""
    
    def test_log_initialization(self):
        """Test log is initialized empty."""
        log = DecisionLog()
        assert len(log) == 0
    
    def test_add_entry(self, sample_signal, sample_chain_result):
        """Test adding an entry."""
        log = DecisionLog()
        entry = log.add(sample_signal, sample_chain_result)
        assert len(log) == 1
        assert entry.symbol == "BTCUSDT"
    
    def test_blocked_entry(self, sample_signal, blocked_chain_result):
        """Test blocked entry records reason."""
        log = DecisionLog()
        entry = log.add(sample_signal, blocked_chain_result)
        assert entry.result == "block"
        assert entry.blocked_by == "atr_filter"
    
    def test_max_entries_limit(self, sample_signal, sample_chain_result):
        """Test max entries limit."""
        log = DecisionLog(max_entries=5)
        for _ in range(10):
            log.add(sample_signal, sample_chain_result)
        assert len(log) == 5
    
    def test_get_recent(self, sample_signal, sample_chain_result):
        """Test getting recent entries."""
        log = DecisionLog()
        for _ in range(20):
            log.add(sample_signal, sample_chain_result)
        recent = log.get_recent(5)
        assert len(recent) == 5
    
    def test_log_clear(self, sample_signal, sample_chain_result):
        """Test clearing log."""
        log = DecisionLog()
        for _ in range(5):
            log.add(sample_signal, sample_chain_result)
        log.clear()
        assert len(log) == 0


# =============================================================================
# FILTER MANAGER TESTS
# =============================================================================

class TestFilterManager:
    """Tests for FilterManager class."""
    
    def test_manager_initialization(self):
        """Test manager initializes correctly."""
        manager = FilterManager("test_bot")
        assert manager.bot_id == "test_bot"
        assert not manager._loaded
    
    def test_load_config_from_dict(self):
        """Test loading config from dictionary."""
        discover_filters()
        manager = FilterManager("test_bot")
        config = {"session_filter": {"enabled": True, "sessions": ["europe", "us"]}}
        manager.load_config_from_dict(config)
        assert manager._loaded
        assert "session_filter" in manager.filters
    
    def test_load_config_from_db(self, temp_db_path):
        """Test loading config from database."""
        discover_filters()
        manager1 = FilterManager("test_bot")
        config = {"session_filter": {"enabled": True, "sessions": ["all"]}}
        manager1.load_config_from_dict(config)
        manager1.save_config(temp_db_path)
        
        manager2 = FilterManager("test_bot")
        manager2.load_config(temp_db_path)
        assert manager2._loaded
        assert "session_filter" in manager2.filters
    
    def test_save_config_to_db(self, temp_db_path):
        """Test saving config to database."""
        discover_filters()
        manager = FilterManager("test_bot")
        config = {
            "session_filter": {"enabled": True, "sessions": ["asia"]},
            "cooldown_filter": {"enabled": True, "cooldown_minutes": 30},
        }
        manager.load_config_from_dict(config)
        manager.save_config(temp_db_path)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bot_filter_configs WHERE bot_id = ?", ("test_bot",))
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 2
    
    def test_apply_filters_not_loaded(self, sample_signal, sample_context):
        """Test applying filters when not loaded."""
        manager = FilterManager("test_bot")
        result = manager.apply_filters(sample_signal, sample_context)
        assert result.is_passed
    
    def test_apply_filters_loaded(self, sample_signal, sample_context):
        """Test applying filters when loaded."""
        discover_filters()
        manager = FilterManager("test_bot")
        config = {"session_filter": {"enabled": True, "sessions": ["all"]}}
        manager.load_config_from_dict(config)
        result = manager.apply_filters(sample_signal, sample_context)
        assert result is not None
    
    def test_enable_disable_filter(self):
        """Test enabling and disabling filters."""
        discover_filters()
        manager = FilterManager("test_bot")
        manager.load_config_from_dict({"session_filter": {"enabled": True, "sessions": ["all"]}})
        
        manager.disable_filter("session_filter")
        assert not manager.filters["session_filter"].enabled
        
        manager.enable_filter("session_filter")
        assert manager.filters["session_filter"].enabled
    
    def test_update_filter_config(self):
        """Test updating filter configuration."""
        discover_filters()
        manager = FilterManager("test_bot")
        manager.load_config_from_dict({"session_filter": {"enabled": True, "sessions": ["asia"]}})
        success = manager.update_filter_config("session_filter", {"enabled": True, "sessions": ["europe", "us"]})
        assert success
    
    def test_add_filter(self):
        """Test adding a new filter."""
        discover_filters()
        manager = FilterManager("test_bot")
        manager.load_config_from_dict({})
        success = manager.add_filter("session_filter", {"enabled": True, "sessions": ["all"]})
        assert success
        assert "session_filter" in manager.filters
    
    def test_remove_filter(self):
        """Test removing a filter."""
        discover_filters()
        manager = FilterManager("test_bot")
        manager.load_config_from_dict({"session_filter": {"enabled": True, "sessions": ["all"]}})
        success = manager.remove_filter("session_filter")
        assert success
        assert "session_filter" not in manager.filters
    
    def test_get_stats(self, sample_signal, sample_context):
        """Test getting statistics."""
        discover_filters()
        manager = FilterManager("test_bot")
        manager.load_config_from_dict({"session_filter": {"enabled": True, "sessions": ["all"]}})
        manager.apply_filters(sample_signal, sample_context)
        stats = manager.get_stats()
        assert stats["bot_id"] == "test_bot"
        assert stats["loaded"]
    
    def test_get_filter_list(self):
        """Test getting filter list."""
        discover_filters()
        manager = FilterManager("test_bot")
        manager.load_config_from_dict({
            "session_filter": {"enabled": True, "sessions": ["all"]},
            "cooldown_filter": {"enabled": False},
        })
        filter_list = manager.get_filter_list()
        assert len(filter_list) == 2
    
    def test_get_filter_summary(self):
        """Test getting filter summary."""
        discover_filters()
        manager = FilterManager("test_bot")
        manager.load_config_from_dict({
            "session_filter": {"enabled": True, "sessions": ["all"]},
            "cooldown_filter": {"enabled": False},
        })
        summary = manager.get_filter_summary()
        assert "enabled" in summary
        assert "disabled" in summary
    
    def test_export_import_config(self):
        """Test config export/import."""
        discover_filters()
        manager1 = FilterManager("bot1")
        config = {"session_filter": {"enabled": True, "sessions": ["europe"]}}
        manager1.load_config_from_dict(config)
        exported = manager1.export_config()
        
        manager2 = FilterManager("bot2")
        manager2.import_config(exported)
        assert "session_filter" in manager2.filters


# =============================================================================
# PROFILE TESTS
# =============================================================================

class TestFilterProfiles:
    """Tests for filter profiles."""
    
    def test_get_profiles(self):
        """Test getting all profiles."""
        profiles = get_filter_profiles()
        assert "minimal" in profiles
        assert "conservative" in profiles
        assert "balanced" in profiles
        assert "aggressive" in profiles
    
    def test_apply_profile(self):
        """Test applying a profile to manager."""
        discover_filters()
        manager = FilterManager("test_bot")
        success = manager.apply_profile("balanced")
        assert success
        assert manager._loaded
    
    def test_apply_unknown_profile(self):
        """Test applying unknown profile fails."""
        manager = FilterManager("test_bot")
        success = manager.apply_profile("nonexistent")
        assert not success


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestFilterValidation:
    """Tests for filter configuration validation."""
    
    def test_validate_valid_config(self):
        """Test validating a valid configuration."""
        discover_filters()
        config = {"enabled": True, "sessions": ["europe", "us"]}
        result = validate_filter_config("session_filter", config)
        assert result["valid"]
    
    def test_validate_unknown_filter(self):
        """Test validating unknown filter."""
        result = validate_filter_config("nonexistent_filter", {})
        assert not result["valid"]


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_create_filter_manager_with_config(self):
        """Test creating manager with config."""
        discover_filters()
        config = {"session_filter": {"enabled": True, "sessions": ["all"]}}
        manager = create_filter_manager("test_bot", config=config)
        assert manager._loaded
    
    def test_create_filter_manager_with_profile(self):
        """Test creating manager with profile."""
        discover_filters()
        manager = create_filter_manager("test_bot", profile="balanced")
        assert manager._loaded
    
    def test_create_filter_manager_empty(self):
        """Test creating empty manager."""
        discover_filters()
        manager = create_filter_manager("test_bot")
        assert manager._loaded
    
    def test_get_filter_categories(self):
        """Test getting filter categories."""
        discover_filters()
        categories = get_filter_categories()
        assert len(categories) > 0
    
    def test_get_available_filters(self):
        """Test getting available filters."""
        discover_filters()
        available = FilterManager.get_available_filters()
        assert len(available) > 0
    
    def test_get_available_filter_names(self):
        """Test getting available filter names."""
        discover_filters()
        names = FilterManager.get_available_filter_names()
        assert isinstance(names, list)
        assert len(names) > 0


# =============================================================================
# DATABASE INTEGRATION TESTS
# =============================================================================

class TestDatabaseIntegration:
    """Tests for database operations."""
    
    def test_database_table_creation(self, temp_db_path):
        """Test that database table is created."""
        discover_filters()
        manager = FilterManager("test_bot")
        manager.load_config_from_dict({"session_filter": {"enabled": True}})
        manager.save_config(temp_db_path)
        
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bot_filter_configs'")
        table = cursor.fetchone()
        conn.close()
        assert table is not None
    
    def test_database_multiple_bots(self, temp_db_path):
        """Test multiple bots in same database."""
        discover_filters()
        
        manager1 = FilterManager("bot1")
        manager1.load_config_from_dict({"session_filter": {"enabled": True}})
        manager1.save_config(temp_db_path)
        
        manager2 = FilterManager("bot2")
        manager2.load_config_from_dict({"cooldown_filter": {"enabled": True}})
        manager2.save_config(temp_db_path)
        
        manager1_reload = FilterManager("bot1")
        manager1_reload.load_config(temp_db_path)
        assert "session_filter" in manager1_reload.filters
        assert "cooldown_filter" not in manager1_reload.filters


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_config(self):
        """Test loading empty config."""
        discover_filters()
        manager = FilterManager("test_bot")
        manager.load_config_from_dict({})
        assert manager._loaded
        assert len(manager.filters) == 0
    
    def test_unknown_filter_in_config(self):
        """Test unknown filter in config is skipped."""
        discover_filters()
        manager = FilterManager("test_bot")
        config = {
            "session_filter": {"enabled": True, "sessions": ["all"]},
            "unknown_filter": {"enabled": True},
        }
        manager.load_config_from_dict(config)
        assert "session_filter" in manager.filters
        assert "unknown_filter" not in manager.filters
    
    def test_repr(self):
        """Test string representation."""
        discover_filters()
        manager = FilterManager("test_bot")
        manager.load_config_from_dict({"session_filter": {"enabled": True}})
        repr_str = repr(manager)
        assert "test_bot" in repr_str


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
