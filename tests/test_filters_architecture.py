"""
Unit Tests for KOMAS Filter Architecture
========================================

Comprehensive test suite for the filter system:
- BaseFilter tests
- FilterRegistry tests
- FilterChain tests
- SignalContext tests

Chat #37: Filters Architecture
Chat #38: Time Filters (updated)
"""

import pytest
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

# Add parent to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "app"))

from filters.base import (
    FilterCategory,
    FilterPriority,
    FilterResult,
    FilterConfig,
    Signal,
    SignalContext,
    FilterDecision,
    BaseFilter,
    AlwaysAllowFilter,
    AlwaysBlockFilter,
    ConditionalFilter,
    create_pass_decision,
    create_block_decision,
    create_skip_decision,
)
from filters.registry import (
    FilterRegistry,
    register_filter,
)
from filters.chain import (
    ChainResult,
    FilterChain,
    create_chain_from_config,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_signal():
    """Sample trading signal"""
    return Signal(
        symbol="BTCUSDT",
        direction="long",
        entry_price=50000.0,
        timestamp=datetime.now(timezone.utc),
        timeframe="1h",
    )


@pytest.fixture
def sample_context():
    """Sample signal context"""
    return SignalContext(
        current_time=datetime.now(timezone.utc),
        current_price=50000.0,
        atr=1000.0,
        volume=1000000.0,
        current_equity=10000.0,
        starting_equity=10000.0,
    )


@pytest.fixture
def fresh_registry():
    """Fresh registry for testing"""
    FilterRegistry.clear()
    return FilterRegistry


# =============================================================================
# FILTER RESULT TESTS
# =============================================================================

class TestFilterResult:
    """Tests for FilterResult enum"""
    
    def test_filter_result_values(self):
        """Test FilterResult enum values"""
        assert FilterResult.PASS.value == "pass"
        assert FilterResult.BLOCK.value == "block"
        assert FilterResult.SKIP.value == "skip"


# =============================================================================
# FILTER DECISION TESTS
# =============================================================================

class TestFilterDecision:
    """Tests for FilterDecision dataclass"""
    
    def test_create_pass_decision(self):
        """Test creating a pass decision"""
        decision = create_pass_decision("test_filter", "Allowed")
        assert decision.result == FilterResult.PASS
        assert decision.is_passed
        assert not decision.is_blocked
        assert decision.filter_name == "test_filter"
        assert decision.reason == "Allowed"
    
    def test_create_block_decision(self):
        """Test creating a block decision"""
        decision = create_block_decision("test_filter", "Blocked for testing")
        assert decision.result == FilterResult.BLOCK
        assert decision.is_blocked
        assert not decision.is_passed
        assert decision.reason == "Blocked for testing"
    
    def test_create_skip_decision(self):
        """Test creating a skip decision"""
        decision = create_skip_decision("test_filter", "Filter disabled")
        assert decision.result == FilterResult.SKIP
        assert not decision.is_passed
        assert not decision.is_blocked
    
    def test_decision_str_representation(self):
        """Test string representation"""
        pass_decision = create_pass_decision("test", "OK")
        block_decision = create_block_decision("test", "Blocked")
        
        assert "PASS" in str(pass_decision)
        assert "BLOCK" in str(block_decision)


# =============================================================================
# FILTER CONFIG TESTS
# =============================================================================

class TestFilterConfig:
    """Tests for FilterConfig dataclass"""
    
    def test_create_config(self):
        """Test creating a filter config"""
        config = FilterConfig(
            filter_name="session_filter",
            enabled=True,
            params={"sessions": ["europe", "us"]},
        )
        assert config.filter_name == "session_filter"
        assert config.enabled is True
        assert config.params["sessions"] == ["europe", "us"]
    
    def test_to_dict(self):
        """Test serialization"""
        config = FilterConfig(
            filter_name="test",
            enabled=True,
            params={"key": "value"},
        )
        d = config.to_dict()
        
        assert d["enabled"] is True
        assert d["key"] == "value"
    
    def test_from_dict(self):
        """Test deserialization"""
        data = {
            "enabled": False,
            "threshold": 0.5,
        }
        config = FilterConfig.from_dict("my_filter", data)
        
        assert config.filter_name == "my_filter"
        assert config.enabled is False
        assert config.params["threshold"] == 0.5


# =============================================================================
# SIGNAL TESTS
# =============================================================================

class TestSignal:
    """Tests for Signal dataclass"""
    
    def test_create_signal(self):
        """Test creating a signal"""
        signal = Signal(
            symbol="BTCUSDT",
            direction="long",
            entry_price=50000.0,
            timestamp=datetime.now(timezone.utc),
        )
        assert signal.symbol == "BTCUSDT"
        assert signal.direction == "long"
        assert signal.entry_price == 50000.0
    
    def test_signal_invalid_direction(self):
        """Test signal rejects invalid direction"""
        with pytest.raises(ValueError):
            Signal(
                symbol="BTCUSDT",
                direction="invalid",
                entry_price=50000.0,
                timestamp=datetime.now(timezone.utc),
            )
    
    def test_signal_optional_fields(self):
        """Test signal optional fields"""
        signal = Signal(
            symbol="ETHUSDT",
            direction="short",
            entry_price=3000.0,
            timestamp=datetime.now(timezone.utc),
            timeframe="4h",
            indicator="dominant",
            score=85,
            grade="A",
        )
        assert signal.timeframe == "4h"
        assert signal.indicator == "dominant"
        assert signal.score == 85
        assert signal.grade == "A"


# =============================================================================
# SIGNAL CONTEXT TESTS
# =============================================================================

class TestSignalContext:
    """Tests for SignalContext dataclass"""
    
    def test_create_context(self):
        """Test creating a signal context"""
        context = SignalContext(
            current_time=datetime.now(timezone.utc),
            current_price=50000.0,
        )
        assert context.current_price == 50000.0
    
    def test_context_drawdown_calculation(self):
        """Test drawdown calculation"""
        context = SignalContext(
            current_time=datetime.now(timezone.utc),
            current_price=50000.0,
            current_equity=9000.0,
            starting_equity=10000.0,
            equity_curve=[10000, 10500, 10000, 9500, 9000],
        )
        # Peak is 10500, current is 9000
        # DD = (10500 - 9000) / 10500 * 100 = 14.28%
        assert context.current_dd_percent == pytest.approx(14.28, rel=0.01)
    
    def test_context_with_positions(self):
        """Test context with open positions"""
        context = SignalContext(
            current_time=datetime.now(timezone.utc),
            current_price=50000.0,
            open_positions=[
                {"symbol": "BTCUSDT", "direction": "long"},
                {"symbol": "ETHUSDT", "direction": "short"},
            ],
        )
        assert len(context.open_positions) == 2


# =============================================================================
# BASE FILTER TESTS
# =============================================================================

class TestBaseFilter:
    """Tests for BaseFilter and example filters"""
    
    def test_always_allow_filter(self, sample_signal, sample_context):
        """Test AlwaysAllowFilter"""
        filter_obj = AlwaysAllowFilter()
        result = filter_obj.should_allow(sample_signal, sample_context)
        
        assert result.is_passed
        assert result.filter_name == "always_allow"
    
    def test_always_block_filter(self, sample_signal, sample_context):
        """Test AlwaysBlockFilter"""
        filter_obj = AlwaysBlockFilter()
        result = filter_obj.should_allow(sample_signal, sample_context)
        
        assert result.is_blocked
        assert result.filter_name == "always_block"
    
    def test_always_block_custom_reason(self, sample_signal, sample_context):
        """Test AlwaysBlockFilter with custom reason"""
        filter_obj = AlwaysBlockFilter({"reason": "Custom block reason"})
        result = filter_obj.should_allow(sample_signal, sample_context)
        
        assert result.reason == "Custom block reason"
    
    def test_conditional_filter_pass(self, sample_signal, sample_context):
        """Test ConditionalFilter passes"""
        filter_obj = ConditionalFilter({"should_pass": True})
        result = filter_obj.should_allow(sample_signal, sample_context)
        
        assert result.is_passed
    
    def test_conditional_filter_block(self, sample_signal, sample_context):
        """Test ConditionalFilter blocks"""
        filter_obj = ConditionalFilter({"should_pass": False})
        result = filter_obj.should_allow(sample_signal, sample_context)
        
        assert result.is_blocked
    
    def test_filter_enable_disable(self):
        """Test enable/disable"""
        filter_obj = AlwaysAllowFilter()
        
        assert filter_obj.enabled is True
        filter_obj.enabled = False
        assert filter_obj.enabled is False
    
    def test_filter_get_ui_display(self):
        """Test get_ui_display method"""
        filter_obj = AlwaysAllowFilter()
        info = filter_obj.get_ui_display()
        
        assert info["name"] == "always_allow"
        assert info["category"] == "time"
        assert "schema" in info
    
    def test_filter_repr(self):
        """Test string representation"""
        filter_obj = AlwaysAllowFilter()
        repr_str = repr(filter_obj)
        
        assert "AlwaysAllowFilter" in repr_str
        assert "always_allow" in repr_str


# =============================================================================
# FILTER REGISTRY TESTS
# =============================================================================

class TestFilterRegistry:
    """Tests for FilterRegistry"""
    
    def test_register_filter(self, fresh_registry):
        """Test registering a filter"""
        @register_filter
        class TestFilter(BaseFilter):
            name = "test_filter"
            description = "Test"
            
            def should_allow(self, signal, context):
                return create_pass_decision(self.name)
            
            def get_config_schema(self):
                return {}
        
        assert "test_filter" in fresh_registry.get_names()
    
    def test_get_filter(self, fresh_registry):
        """Test getting a filter class"""
        # AlwaysAllowFilter should be available
        cls = fresh_registry.get("always_allow")
        # May or may not be registered depending on import order
        # Just test the method works
        assert cls is None or issubclass(cls, BaseFilter)
    
    def test_create_instance(self, fresh_registry):
        """Test creating a filter instance"""
        # Register a test filter
        @register_filter
        class TestFilter2(BaseFilter):
            name = "test_filter_2"
            description = "Test 2"
            
            def should_allow(self, signal, context):
                return create_pass_decision(self.name)
            
            def get_config_schema(self):
                return {"param": {"type": "int", "default": 5}}
        
        instance = fresh_registry.create_instance("test_filter_2", {"param": 10})
        
        assert instance is not None
        assert instance.config.get("param") == 10
    
    def test_get_by_category(self, fresh_registry):
        """Test getting filters by category"""
        @register_filter
        class TimeFilter(BaseFilter):
            name = "time_test"
            description = "Time test"
            category = FilterCategory.TIME
            
            def should_allow(self, signal, context):
                return create_pass_decision(self.name)
            
            def get_config_schema(self):
                return {}
        
        time_filters = fresh_registry.get_by_category(FilterCategory.TIME)
        assert "time_test" in time_filters
    
    def test_count(self, fresh_registry):
        """Test count method"""
        initial_count = fresh_registry.count()
        
        @register_filter
        class CountTestFilter(BaseFilter):
            name = "count_test"
            description = "Count test"
            
            def should_allow(self, signal, context):
                return create_pass_decision(self.name)
            
            def get_config_schema(self):
                return {}
        
        assert fresh_registry.count() == initial_count + 1


# =============================================================================
# FILTER CHAIN TESTS
# =============================================================================

class TestFilterChain:
    """Tests for FilterChain"""
    
    def test_empty_chain(self, sample_signal, sample_context):
        """Test empty chain allows all"""
        chain = FilterChain([])
        result = chain.apply(sample_signal, sample_context)
        
        assert result.is_passed
        assert len(result.passed_filters) == 0
    
    def test_chain_with_allow_filter(self, sample_signal, sample_context):
        """Test chain with allowing filter"""
        chain = FilterChain([AlwaysAllowFilter()])
        result = chain.apply(sample_signal, sample_context)
        
        assert result.is_passed
        assert "always_allow" in result.passed_filters
    
    def test_chain_with_block_filter(self, sample_signal, sample_context):
        """Test chain with blocking filter"""
        chain = FilterChain([AlwaysBlockFilter()])
        result = chain.apply(sample_signal, sample_context)
        
        assert result.is_blocked
        assert result.blocked_by == "always_block"
    
    def test_chain_short_circuit(self, sample_signal, sample_context):
        """Test short-circuit behavior"""
        chain = FilterChain([
            AlwaysBlockFilter({"reason": "Block 1"}),
            AlwaysAllowFilter(),
        ], short_circuit=True)
        
        result = chain.apply(sample_signal, sample_context)
        
        # Should stop at first block
        assert result.is_blocked
        assert len(result.passed_filters) == 0
    
    def test_chain_no_short_circuit(self, sample_signal, sample_context):
        """Test without short-circuit"""
        chain = FilterChain([
            AlwaysBlockFilter({"reason": "Block 1"}),
            AlwaysAllowFilter(),
        ], short_circuit=False)
        
        result = chain.apply(sample_signal, sample_context)
        
        # Should process all filters
        assert result.is_blocked
        # AlwaysAllowFilter should have been processed too
        assert len(result.decisions) == 2
    
    def test_chain_priority_ordering(self):
        """Test filters are sorted by priority"""
        class LowPriorityFilter(AlwaysAllowFilter):
            name = "low_priority"
            priority = FilterPriority.LOW
        
        class CriticalFilter(AlwaysAllowFilter):
            name = "critical"
            priority = FilterPriority.CRITICAL
        
        chain = FilterChain([
            LowPriorityFilter(),
            CriticalFilter(),
        ])
        
        # Critical should come first after sorting
        assert chain.filters[0].name == "critical"
        assert chain.filters[1].name == "low_priority"
    
    def test_chain_enable_disable(self, sample_signal, sample_context):
        """Test enable/disable filters in chain"""
        chain = FilterChain([AlwaysBlockFilter()])
        
        # Initially should block
        assert chain.apply(sample_signal, sample_context).is_blocked
        
        # Disable and should skip
        chain.disable_filter("always_block")
        result = chain.apply(sample_signal, sample_context)
        assert result.is_passed
        assert "always_block" in result.skipped_filters
        
        # Re-enable and should block again
        chain.enable_filter("always_block")
        assert chain.apply(sample_signal, sample_context).is_blocked
    
    def test_chain_add_remove(self, sample_signal, sample_context):
        """Test adding and removing filters"""
        chain = FilterChain([])
        
        # Add filter
        chain.add_filter(AlwaysBlockFilter())
        assert len(chain) == 1
        assert chain.apply(sample_signal, sample_context).is_blocked
        
        # Remove filter
        chain.remove_filter("always_block")
        assert len(chain) == 0
        assert chain.apply(sample_signal, sample_context).is_passed
    
    def test_chain_statistics(self, sample_signal, sample_context):
        """Test chain statistics tracking"""
        chain = FilterChain([AlwaysAllowFilter()])
        
        chain.apply(sample_signal, sample_context)
        chain.apply(sample_signal, sample_context)
        
        stats = chain.get_stats()
        assert stats["total_calls"] == 2
        assert stats["total_passed"] == 2
    
    def test_chain_on_trade_complete(self):
        """Test on_trade_complete propagation"""
        class StatefulFilter(AlwaysAllowFilter):
            name = "stateful"
            
            def __init__(self, config=None):
                super().__init__(config)
                self.trade_count = 0
            
            def on_trade_complete(self, trade_result):
                self.trade_count += 1
        
        stateful = StatefulFilter()
        chain = FilterChain([stateful])
        
        chain.on_trade_complete({"pnl": 100})
        chain.on_trade_complete({"pnl": -50})
        
        assert stateful.trade_count == 2


# =============================================================================
# CHAIN RESULT TESTS
# =============================================================================

class TestChainResult:
    """Tests for ChainResult"""
    
    def test_passed_result(self):
        """Test passed chain result"""
        result = ChainResult(
            is_blocked=False,
            passed_filters=["filter1", "filter2"],
        )
        
        assert result.is_passed
        assert not result.is_blocked
        assert len(result.passed_filters) == 2
    
    def test_blocked_result(self):
        """Test blocked chain result"""
        result = ChainResult(
            is_blocked=True,
            blocked_by="blocking_filter",
            decisions=[create_block_decision("blocking_filter", "Blocked")],
        )
        
        assert result.is_blocked
        assert result.blocked_by == "blocking_filter"
        assert result.blocking_reason == "Blocked"
    
    def test_summary(self):
        """Test summary property"""
        result = ChainResult(
            is_blocked=False,
            passed_filters=["f1", "f2"],
            skipped_filters=["f3"],
        )
        
        summary = result.summary
        assert summary["passed"] is True
        assert summary["passed_count"] == 2
        assert summary["skipped_count"] == 1
    
    def test_str_representation(self):
        """Test string representation"""
        passed = ChainResult(is_blocked=False, passed_filters=["f1"])
        blocked = ChainResult(is_blocked=True, blocked_by="blocker")
        
        assert "PASSED" in str(passed)
        assert "BLOCKED" in str(blocked)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the filter system"""
    
    def test_full_workflow(self, sample_signal, sample_context):
        """Test complete workflow"""
        # 1. Create filters
        allow_filter = AlwaysAllowFilter()
        conditional = ConditionalFilter({"should_pass": True})
        
        # 2. Create chain
        chain = FilterChain([allow_filter, conditional])
        
        # 3. Apply and verify
        result = chain.apply(sample_signal, sample_context)
        assert result.is_passed
        assert len(result.passed_filters) == 2
        
        # 4. Change conditional to block
        chain.remove_filter("conditional")
        chain.add_filter(ConditionalFilter({"should_pass": False}))
        
        result = chain.apply(sample_signal, sample_context)
        assert result.is_blocked
    
    def test_create_chain_from_config(self, fresh_registry):
        """Test creating chain from configuration"""
        # Register filters
        @register_filter
        class ConfigTestFilter(BaseFilter):
            name = "config_test"
            description = "Config test"
            
            def should_allow(self, signal, context):
                threshold = self.config.get("threshold", 50)
                if threshold > 25:
                    return create_pass_decision(self.name)
                return create_block_decision(self.name, "Below threshold")
            
            def get_config_schema(self):
                return {"threshold": {"type": "int", "default": 50}}
        
        # Create chain from config
        config = {
            "config_test": {"enabled": True, "threshold": 30}
        }
        chain = create_chain_from_config(config)
        
        assert len(chain) == 1


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
