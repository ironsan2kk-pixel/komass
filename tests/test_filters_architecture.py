"""
Unit Tests for KOMAS Filter Architecture
========================================

Comprehensive test suite for the filter system:
- BaseFilter tests
- FilterResult tests
- FilterRegistry tests
- FilterChain tests
- SignalContext tests

Chat #37: Filters Architecture
"""

import pytest
from datetime import datetime, timedelta
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
    SignalContext,
    BaseFilter,
    AlwaysAllowFilter,
    AlwaysBlockFilter,
)
from filters.registry import (
    FilterRegistry,
    get_registry,
    register_filter,
)
from filters.chain import (
    ChainResult,
    FilterChain,
    FilterChainBuilder,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def sample_signal():
    """Sample trading signal"""
    return {
        "direction": "long",
        "entry_price": 50000.0,
        "stop_loss": 49000.0,
        "take_profits": [51000.0, 52000.0],
        "symbol": "BTCUSDT",
        "timeframe": "1h",
    }


@pytest.fixture
def sample_context(sample_signal):
    """Sample signal context"""
    return SignalContext(
        signal=sample_signal,
        symbol="BTCUSDT",
        timeframe="1h",
        current_price=50000.0,
        current_time=datetime.utcnow(),
        equity=10000.0,
        starting_equity=10000.0,
    )


@pytest.fixture
def fresh_registry():
    """Fresh registry for testing"""
    registry = FilterRegistry()
    registry.clear()
    return registry


@pytest.fixture
def empty_chain(fresh_registry):
    """Empty filter chain"""
    return FilterChain(registry=fresh_registry)


# =============================================================================
# FILTER RESULT TESTS
# =============================================================================

class TestFilterResult:
    """Tests for FilterResult dataclass"""
    
    def test_create_allowed_result(self):
        """Test creating an allowed result"""
        result = FilterResult(allowed=True, filter_name="test")
        assert result.allowed is True
        assert result.reason is None
        assert result.filter_name == "test"
    
    def test_create_blocked_result(self):
        """Test creating a blocked result"""
        result = FilterResult(
            allowed=False,
            reason="Signal blocked",
            filter_name="test",
        )
        assert result.allowed is False
        assert result.reason == "Signal blocked"
    
    def test_allow_factory(self):
        """Test FilterResult.allow() factory method"""
        result = FilterResult.allow(
            filter_name="my_filter",
            category=FilterCategory.TIME,
            details={"key": "value"},
        )
        assert result.allowed is True
        assert result.filter_name == "my_filter"
        assert result.filter_category == FilterCategory.TIME
        assert result.details == {"key": "value"}
    
    def test_block_factory(self):
        """Test FilterResult.block() factory method"""
        result = FilterResult.block(
            reason="Too volatile",
            filter_name="atr_filter",
            category=FilterCategory.VOLATILITY,
        )
        assert result.allowed is False
        assert result.reason == "Too volatile"
        assert result.filter_category == FilterCategory.VOLATILITY
    
    def test_to_dict(self):
        """Test serialization to dict"""
        result = FilterResult.block("Test reason", "test_filter")
        d = result.to_dict()
        
        assert d["allowed"] is False
        assert d["reason"] == "Test reason"
        assert d["filter_name"] == "test_filter"
        assert "timestamp" in d
    
    def test_repr(self):
        """Test string representation"""
        allowed = FilterResult.allow()
        blocked = FilterResult.block("Reason")
        
        assert "ALLOWED" in repr(allowed)
        assert "BLOCKED" in repr(blocked)


# =============================================================================
# FILTER CONFIG TESTS
# =============================================================================

class TestFilterConfig:
    """Tests for FilterConfig dataclass"""
    
    def test_create_config(self):
        """Test creating a filter config"""
        config = FilterConfig(
            name="session_filter",
            enabled=True,
            params={"sessions": ["london", "new_york"]},
        )
        assert config.name == "session_filter"
        assert config.enabled is True
        assert config.params["sessions"] == ["london", "new_york"]
    
    def test_to_dict(self):
        """Test serialization"""
        config = FilterConfig(
            name="test",
            params={"key": "value"},
        )
        d = config.to_dict()
        
        assert d["name"] == "test"
        assert d["enabled"] is True
        assert d["params"] == {"key": "value"}
    
    def test_from_dict(self):
        """Test deserialization"""
        data = {
            "name": "my_filter",
            "enabled": False,
            "params": {"threshold": 0.5},
            "priority": 2,
        }
        config = FilterConfig.from_dict(data)
        
        assert config.name == "my_filter"
        assert config.enabled is False
        assert config.params["threshold"] == 0.5
        assert config.priority == FilterPriority.HIGH


# =============================================================================
# SIGNAL CONTEXT TESTS
# =============================================================================

class TestSignalContext:
    """Tests for SignalContext dataclass"""
    
    def test_create_context(self, sample_signal):
        """Test creating a signal context"""
        context = SignalContext(
            signal=sample_signal,
            symbol="BTCUSDT",
            timeframe="1h",
            current_price=50000.0,
            current_time=datetime.utcnow(),
        )
        assert context.symbol == "BTCUSDT"
        assert context.direction == "long"
        assert context.current_price == 50000.0
    
    def test_direction_property(self, sample_context):
        """Test direction property"""
        assert sample_context.direction == "long"
    
    def test_entry_price_property(self, sample_context):
        """Test entry price property"""
        assert sample_context.entry_price == 50000.0
    
    def test_drawdown_calculation(self):
        """Test drawdown calculation"""
        context = SignalContext(
            signal={"direction": "long"},
            symbol="BTCUSDT",
            timeframe="1h",
            current_price=50000.0,
            current_time=datetime.utcnow(),
            equity=9000.0,
            starting_equity=10000.0,
        )
        assert context.current_drawdown == 10.0  # 10% drawdown
    
    def test_position_count(self, sample_signal):
        """Test position count"""
        context = SignalContext(
            signal=sample_signal,
            symbol="BTCUSDT",
            timeframe="1h",
            current_price=50000.0,
            current_time=datetime.utcnow(),
            open_positions=[
                {"symbol": "BTCUSDT", "direction": "long"},
                {"symbol": "ETHUSDT", "direction": "short"},
            ],
        )
        assert context.position_count == 2
        assert len(context.long_positions) == 1
        assert len(context.short_positions) == 1
    
    def test_to_dict(self, sample_context):
        """Test serialization"""
        d = sample_context.to_dict()
        
        assert d["symbol"] == "BTCUSDT"
        assert "current_time" in d
        assert d["position_count"] == 0


# =============================================================================
# BASE FILTER TESTS
# =============================================================================

class TestBaseFilter:
    """Tests for BaseFilter and example filters"""
    
    def test_always_allow_filter(self, sample_context):
        """Test AlwaysAllowFilter"""
        filter_obj = AlwaysAllowFilter()
        result = filter_obj.can_trade(sample_context)
        
        assert result.allowed is True
        assert result.filter_name == "always_allow"
    
    def test_always_block_filter(self, sample_context):
        """Test AlwaysBlockFilter"""
        filter_obj = AlwaysBlockFilter()
        result = filter_obj.can_trade(sample_context)
        
        assert result.allowed is False
        assert "always_block" in result.reason
    
    def test_always_block_custom_reason(self, sample_context):
        """Test AlwaysBlockFilter with custom reason"""
        filter_obj = AlwaysBlockFilter({"reason": "Custom block reason"})
        result = filter_obj.can_trade(sample_context)
        
        assert result.reason == "Custom block reason"
    
    def test_filter_enable_disable(self):
        """Test enable/disable methods"""
        filter_obj = AlwaysAllowFilter()
        
        assert filter_obj.enabled is True
        filter_obj.disable()
        assert filter_obj.enabled is False
        filter_obj.enable()
        assert filter_obj.enabled is True
    
    def test_filter_get_info(self):
        """Test get_info method"""
        filter_obj = AlwaysAllowFilter()
        info = filter_obj.get_info()
        
        assert info["name"] == "always_allow"
        assert info["display_name"] == "Always Allow"
        assert info["category"] == "trend"
        assert "config_schema" in info
    
    def test_filter_config_schema(self):
        """Test get_config_schema method"""
        filter_obj = AlwaysBlockFilter()
        schema = filter_obj.get_config_schema()
        
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "reason" in schema["properties"]
    
    def test_filter_equality(self):
        """Test filter equality based on name"""
        f1 = AlwaysAllowFilter()
        f2 = AlwaysAllowFilter()
        f3 = AlwaysBlockFilter()
        
        assert f1 == f2
        assert f1 != f3


# =============================================================================
# CUSTOM FILTER FOR TESTING
# =============================================================================

class MaxPositionsFilter(BaseFilter):
    """Test filter that limits max positions"""
    
    name = "max_positions"
    display_name = "Max Positions"
    description = "Limits the number of open positions"
    category = FilterCategory.PORTFOLIO
    priority = FilterPriority.NORMAL
    
    def can_trade(self, context: SignalContext) -> FilterResult:
        max_pos = self.config.get("max_positions", 3)
        
        if context.position_count >= max_pos:
            return FilterResult.block(
                reason=f"Max positions reached ({max_pos})",
                filter_name=self.name,
                category=self.category,
                details={"current": context.position_count, "max": max_pos},
            )
        
        return FilterResult.allow(
            filter_name=self.name,
            category=self.category,
        )
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "max_positions": {
                    "type": "integer",
                    "description": "Maximum number of open positions",
                    "default": 3,
                    "minimum": 1,
                    "maximum": 20,
                },
            },
            "required": [],
        }


class DrawdownFilter(BaseFilter):
    """Test filter that checks drawdown"""
    
    name = "drawdown_filter"
    display_name = "Drawdown Filter"
    description = "Blocks trading when drawdown exceeds limit"
    category = FilterCategory.PROTECTION
    priority = FilterPriority.CRITICAL
    
    def can_trade(self, context: SignalContext) -> FilterResult:
        max_dd = self.config.get("max_drawdown", 10.0)
        current_dd = context.current_drawdown
        
        if current_dd >= max_dd:
            return FilterResult.block(
                reason=f"Drawdown limit exceeded ({current_dd:.1f}% >= {max_dd}%)",
                filter_name=self.name,
                category=self.category,
                details={"current_dd": current_dd, "max_dd": max_dd},
            )
        
        return FilterResult.allow(
            filter_name=self.name,
            category=self.category,
        )
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "max_drawdown": {
                    "type": "number",
                    "description": "Maximum allowed drawdown percentage",
                    "default": 10.0,
                    "minimum": 1.0,
                    "maximum": 50.0,
                },
            },
            "required": [],
        }


# =============================================================================
# FILTER REGISTRY TESTS
# =============================================================================

class TestFilterRegistry:
    """Tests for FilterRegistry"""
    
    def test_register_filter(self, fresh_registry):
        """Test registering a filter"""
        result = fresh_registry.register(MaxPositionsFilter)
        
        assert result is True
        assert "max_positions" in fresh_registry
    
    def test_register_invalid(self, fresh_registry):
        """Test registering invalid filter"""
        with pytest.raises(ValueError):
            fresh_registry.register("not a class")
        
        with pytest.raises(ValueError):
            fresh_registry.register(BaseFilter)
    
    def test_get_filter(self, fresh_registry):
        """Test getting a filter class"""
        fresh_registry.register(MaxPositionsFilter)
        
        cls = fresh_registry.get("max_positions")
        assert cls is MaxPositionsFilter
        
        assert fresh_registry.get("nonexistent") is None
    
    def test_create_filter(self, fresh_registry):
        """Test creating a filter instance"""
        fresh_registry.register(MaxPositionsFilter)
        
        instance = fresh_registry.create("max_positions", {"max_positions": 5})
        
        assert instance is not None
        assert isinstance(instance, MaxPositionsFilter)
        assert instance.config["max_positions"] == 5
    
    def test_list_filters(self, fresh_registry):
        """Test listing filters"""
        fresh_registry.register(MaxPositionsFilter)
        fresh_registry.register(DrawdownFilter)
        
        all_filters = fresh_registry.list_all()
        assert "max_positions" in all_filters
        assert "drawdown_filter" in all_filters
    
    def test_list_by_category(self, fresh_registry):
        """Test listing by category"""
        fresh_registry.register(MaxPositionsFilter)
        fresh_registry.register(DrawdownFilter)
        
        portfolio_filters = fresh_registry.list_by_category(FilterCategory.PORTFOLIO)
        protection_filters = fresh_registry.list_by_category(FilterCategory.PROTECTION)
        
        assert "max_positions" in portfolio_filters
        assert "drawdown_filter" in protection_filters
    
    def test_unregister(self, fresh_registry):
        """Test unregistering a filter"""
        fresh_registry.register(MaxPositionsFilter)
        assert "max_positions" in fresh_registry
        
        result = fresh_registry.unregister("max_positions")
        assert result is True
        assert "max_positions" not in fresh_registry
    
    def test_get_info(self, fresh_registry):
        """Test getting filter info"""
        fresh_registry.register(MaxPositionsFilter)
        
        info = fresh_registry.get_info("max_positions")
        
        assert info["name"] == "max_positions"
        assert info["display_name"] == "Max Positions"
        assert info["category"] == "portfolio"
    
    def test_get_schema(self, fresh_registry):
        """Test getting filter schema"""
        fresh_registry.register(MaxPositionsFilter)
        
        schema = fresh_registry.get_schema("max_positions")
        
        assert schema["type"] == "object"
        assert "max_positions" in schema["properties"]


# =============================================================================
# FILTER CHAIN TESTS
# =============================================================================

class TestFilterChain:
    """Tests for FilterChain"""
    
    def test_empty_chain(self, empty_chain, sample_context):
        """Test empty chain allows all"""
        result = empty_chain.apply(sample_context)
        
        assert result.allowed is True
        assert result.rejection_count == 0
        assert result.total_filters == 0
    
    def test_add_filter(self, empty_chain):
        """Test adding filters"""
        filter_obj = AlwaysAllowFilter()
        empty_chain.add(filter_obj)
        
        assert len(empty_chain) == 1
        assert "always_allow" in empty_chain
    
    def test_remove_filter(self, empty_chain):
        """Test removing filters"""
        empty_chain.add(AlwaysAllowFilter())
        assert len(empty_chain) == 1
        
        result = empty_chain.remove("always_allow")
        assert result is True
        assert len(empty_chain) == 0
    
    def test_chain_allows(self, empty_chain, sample_context):
        """Test chain with allowing filters"""
        empty_chain.add(AlwaysAllowFilter())
        
        result = empty_chain.apply(sample_context)
        assert result.allowed is True
        assert result.approval_count == 1
    
    def test_chain_blocks(self, empty_chain, sample_context):
        """Test chain with blocking filter"""
        empty_chain.add(AlwaysBlockFilter())
        
        result = empty_chain.apply(sample_context)
        assert result.allowed is False
        assert result.rejection_count == 1
    
    def test_short_circuit(self, fresh_registry, sample_context):
        """Test short-circuit behavior"""
        fresh_registry.register(AlwaysAllowFilter)
        fresh_registry.register(AlwaysBlockFilter)
        
        chain = FilterChain(registry=fresh_registry, short_circuit=True)
        chain.add(AlwaysBlockFilter())
        chain.add(AlwaysAllowFilter())
        
        result = chain.apply(sample_context)
        
        # Should stop at first rejection
        assert result.rejection_count == 1
        assert result.approval_count == 0
    
    def test_no_short_circuit(self, fresh_registry, sample_context):
        """Test without short-circuit"""
        # Create two separate blocking filter classes with unique names
        class BlockFilter1(AlwaysBlockFilter):
            name = "block_filter_1"
        
        class BlockFilter2(AlwaysBlockFilter):
            name = "block_filter_2"
        
        chain = FilterChain(registry=fresh_registry, short_circuit=False)
        chain.add(BlockFilter1({"reason": "Block 1"}))
        chain.add(BlockFilter2({"reason": "Block 2"}))
        
        result = chain.apply(sample_context)
        
        # Should collect all rejections
        assert result.rejection_count == 2
    
    def test_priority_ordering(self, fresh_registry):
        """Test filters are applied in priority order"""
        fresh_registry.register(MaxPositionsFilter)  # NORMAL
        fresh_registry.register(DrawdownFilter)      # CRITICAL
        
        chain = FilterChain(registry=fresh_registry)
        chain.add(MaxPositionsFilter())
        chain.add(DrawdownFilter())
        
        # Critical should come first
        filters = chain.filters
        assert filters[0].priority == FilterPriority.CRITICAL
        assert filters[1].priority == FilterPriority.NORMAL
    
    def test_enable_disable(self, empty_chain, sample_context):
        """Test enable/disable filters in chain"""
        empty_chain.add(AlwaysBlockFilter())
        
        # Initially should block
        assert empty_chain.apply(sample_context).allowed is False
        
        # Disable and should allow
        empty_chain.disable("always_block")
        assert empty_chain.apply(sample_context).allowed is True
        
        # Re-enable and should block again
        empty_chain.enable("always_block")
        assert empty_chain.apply(sample_context).allowed is False
    
    def test_check_method(self, empty_chain, sample_context):
        """Test simple check method"""
        empty_chain.add(AlwaysBlockFilter({"reason": "Test reason"}))
        
        allowed, reason = empty_chain.check(sample_context)
        
        assert allowed is False
        assert reason == "Test reason"
    
    def test_get_rejections(self, fresh_registry, sample_context):
        """Test getting all rejection reasons"""
        # Create two separate blocking filter classes with unique names
        class BlockFilter1(AlwaysBlockFilter):
            name = "block_filter_1"
        
        class BlockFilter2(AlwaysBlockFilter):
            name = "block_filter_2"
        
        chain = FilterChain(registry=fresh_registry, short_circuit=True)
        chain.add(BlockFilter1({"reason": "Reason 1"}))
        chain.add(BlockFilter2({"reason": "Reason 2"}))
        
        reasons = chain.get_rejections(sample_context)
        
        # Should get all reasons even though short_circuit=True
        assert "Reason 1" in reasons
        assert "Reason 2" in reasons
    
    def test_custom_filter_in_chain(self, fresh_registry, sample_signal):
        """Test custom filter logic in chain"""
        fresh_registry.register(MaxPositionsFilter)
        
        chain = FilterChain(registry=fresh_registry)
        chain.add(MaxPositionsFilter({"max_positions": 2}))
        
        # Context with 1 position - should allow
        context1 = SignalContext(
            signal=sample_signal,
            symbol="BTCUSDT",
            timeframe="1h",
            current_price=50000.0,
            current_time=datetime.utcnow(),
            open_positions=[{"symbol": "ETHUSDT"}],
        )
        assert chain.apply(context1).allowed is True
        
        # Context with 2 positions - should block
        context2 = SignalContext(
            signal=sample_signal,
            symbol="BTCUSDT",
            timeframe="1h",
            current_price=50000.0,
            current_time=datetime.utcnow(),
            open_positions=[{"symbol": "ETHUSDT"}, {"symbol": "SOLUSDT"}],
        )
        assert chain.apply(context2).allowed is False
    
    def test_to_config_list(self, empty_chain):
        """Test exporting chain config"""
        empty_chain.add(AlwaysAllowFilter())
        empty_chain.add(MaxPositionsFilter({"max_positions": 5}))
        
        config_list = empty_chain.to_config_list()
        
        assert len(config_list) == 2
        assert config_list[0]["name"] == "always_allow"
    
    def test_from_config_list(self, fresh_registry):
        """Test creating chain from config"""
        fresh_registry.register(AlwaysAllowFilter)
        fresh_registry.register(MaxPositionsFilter)
        
        config_list = [
            {"name": "always_allow", "enabled": True, "params": {}},
            {"name": "max_positions", "enabled": True, "params": {"max_positions": 5}},
        ]
        
        chain = FilterChain.from_config_list(config_list, registry=fresh_registry)
        
        assert len(chain) == 2
        assert "always_allow" in chain
        assert "max_positions" in chain


# =============================================================================
# CHAIN RESULT TESTS
# =============================================================================

class TestChainResult:
    """Tests for ChainResult"""
    
    def test_allowed_result(self):
        """Test allowed chain result"""
        result = ChainResult(
            allowed=True,
            approvals=[FilterResult.allow()],
            total_filters=1,
            active_filters=1,
        )
        
        assert result.allowed is True
        assert result.is_blocked is False
        assert result.rejection_count == 0
        assert result.approval_count == 1
    
    def test_blocked_result(self):
        """Test blocked chain result"""
        rejection = FilterResult.block("Blocked")
        result = ChainResult(
            allowed=False,
            rejections=[rejection],
            total_filters=1,
            active_filters=1,
        )
        
        assert result.allowed is False
        assert result.is_blocked is True
        assert result.primary_rejection == rejection
        assert result.all_reasons == ["Blocked"]
    
    def test_to_dict(self):
        """Test serialization"""
        result = ChainResult(
            allowed=True,
            total_filters=2,
            active_filters=2,
            execution_time_ms=1.5,
        )
        d = result.to_dict()
        
        assert d["allowed"] is True
        assert d["total_filters"] == 2
        assert d["execution_time_ms"] == 1.5


# =============================================================================
# FILTER CHAIN BUILDER TESTS
# =============================================================================

class TestFilterChainBuilder:
    """Tests for FilterChainBuilder"""
    
    def test_build_empty(self, fresh_registry):
        """Test building empty chain"""
        builder = FilterChainBuilder(registry=fresh_registry)
        chain = builder.build()
        
        assert len(chain) == 0
    
    def test_build_with_filters(self, fresh_registry):
        """Test building chain with filters"""
        fresh_registry.register(AlwaysAllowFilter)
        fresh_registry.register(MaxPositionsFilter)
        
        chain = (
            FilterChainBuilder(registry=fresh_registry)
            .add("always_allow")
            .add("max_positions", max_positions=5)
            .build()
        )
        
        assert len(chain) == 2
    
    def test_with_short_circuit(self, fresh_registry):
        """Test setting short-circuit"""
        chain = (
            FilterChainBuilder(registry=fresh_registry)
            .with_short_circuit(False)
            .build()
        )
        
        assert chain.short_circuit is False


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests for the filter system"""
    
    def test_full_workflow(self, fresh_registry, sample_signal):
        """Test complete workflow"""
        # 1. Register filters
        fresh_registry.register(MaxPositionsFilter)
        fresh_registry.register(DrawdownFilter)
        
        # 2. Create chain
        chain = FilterChain(registry=fresh_registry)
        chain.add_by_name("max_positions", {"max_positions": 3})
        chain.add_by_name("drawdown_filter", {"max_drawdown": 10.0})
        
        # 3. Create context with acceptable conditions
        context_ok = SignalContext(
            signal=sample_signal,
            symbol="BTCUSDT",
            timeframe="1h",
            current_price=50000.0,
            current_time=datetime.utcnow(),
            open_positions=[{"symbol": "ETHUSDT"}],
            equity=9500.0,
            starting_equity=10000.0,  # 5% DD
        )
        
        result_ok = chain.apply(context_ok)
        assert result_ok.allowed is True
        
        # 4. Create context with drawdown exceeded
        context_dd = SignalContext(
            signal=sample_signal,
            symbol="BTCUSDT",
            timeframe="1h",
            current_price=50000.0,
            current_time=datetime.utcnow(),
            equity=8000.0,
            starting_equity=10000.0,  # 20% DD
        )
        
        result_dd = chain.apply(context_dd)
        assert result_dd.allowed is False
        assert "Drawdown" in result_dd.primary_rejection.reason
        
        # 5. Create context with max positions
        context_pos = SignalContext(
            signal=sample_signal,
            symbol="BTCUSDT",
            timeframe="1h",
            current_price=50000.0,
            current_time=datetime.utcnow(),
            open_positions=[
                {"symbol": "ETHUSDT"},
                {"symbol": "SOLUSDT"},
                {"symbol": "BNBUSDT"},
            ],
            equity=9500.0,
            starting_equity=10000.0,
        )
        
        result_pos = chain.apply(context_pos)
        assert result_pos.allowed is False
        # DD filter runs first (CRITICAL priority), but it passes
        # Max positions filter blocks
        assert "Max positions" in result_pos.primary_rejection.reason


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
