"""
KOMAS v4.0 — Volatility Filters Unit Tests
===========================================

Comprehensive tests for ATRFilter, VolumeFilter, ExtremeFilter.

Chat #39: Filters Volatility
Author: KOMAS Team
Version: 4.0
"""

import unittest
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))

from filters.base import (
    Signal,
    SignalContext,
    FilterResult,
    FilterCategory,
    FilterPriority,
)
from filters.volatility_filters import (
    ATRFilter,
    VolumeFilter,
    ExtremeFilter,
    calculate_atr_percent,
    calculate_volume_ratio,
    is_extreme_atr,
    is_extreme_volume,
    format_atr_value,
    get_volatility_state,
    create_volatility_filter_chain,
    create_volatility_profile,
    validate_volatility_config,
    DEFAULT_ATR_PERIOD,
    DEFAULT_VOLUME_MA_PERIOD,
    DEFAULT_EXTREME_ATR_MULTIPLIER,
    DEFAULT_EXTREME_VOLUME_MULTIPLIER,
    DEFAULT_EXTREME_PAUSE_MINUTES,
)


def create_test_signal(
    symbol: str = "BTCUSDT",
    direction: str = "long",
    entry_price: float = 50000.0
) -> Signal:
    """Create a test signal."""
    return Signal(
        symbol=symbol,
        direction=direction,
        entry_price=entry_price,
        timestamp=datetime.now(timezone.utc)
    )


def create_test_context(
    current_price: float = 50000.0,
    atr: Optional[float] = None,
    volume: Optional[float] = None,
    avg_volume: Optional[float] = None,
    avg_atr: Optional[float] = None
) -> SignalContext:
    """Create a test context with optional market data."""
    htf_data = {}
    if avg_atr is not None:
        htf_data["avg_atr"] = avg_atr
    
    return SignalContext(
        current_time=datetime.now(timezone.utc),
        current_price=current_price,
        atr=atr,
        volume=volume,
        avg_volume=avg_volume,
        htf_data=htf_data
    )


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestHelperFunctions(unittest.TestCase):
    """Tests for helper functions."""
    
    def test_calculate_atr_percent(self):
        """Test ATR percentage calculation."""
        # Normal case
        self.assertAlmostEqual(calculate_atr_percent(1000, 50000), 2.0)
        self.assertAlmostEqual(calculate_atr_percent(500, 50000), 1.0)
        
        # Edge cases
        self.assertEqual(calculate_atr_percent(0, 50000), 0.0)
        self.assertEqual(calculate_atr_percent(1000, 0), 0.0)
        self.assertEqual(calculate_atr_percent(1000, -100), 0.0)
    
    def test_calculate_volume_ratio(self):
        """Test volume ratio calculation."""
        # Normal case
        self.assertEqual(calculate_volume_ratio(1500, 1000), 1.5)
        self.assertEqual(calculate_volume_ratio(500, 1000), 0.5)
        
        # Edge cases
        self.assertEqual(calculate_volume_ratio(1000, 0), 0.0)
        self.assertEqual(calculate_volume_ratio(0, 1000), 0.0)
    
    def test_is_extreme_atr(self):
        """Test extreme ATR detection."""
        # Not extreme
        self.assertFalse(is_extreme_atr(100, 100, 3.0))
        self.assertFalse(is_extreme_atr(200, 100, 3.0))
        self.assertFalse(is_extreme_atr(300, 100, 3.0))  # Equal
        
        # Extreme
        self.assertTrue(is_extreme_atr(400, 100, 3.0))
        self.assertTrue(is_extreme_atr(500, 100, 3.0))
        
        # Edge cases
        self.assertFalse(is_extreme_atr(100, 0, 3.0))
        self.assertFalse(is_extreme_atr(100, -50, 3.0))
    
    def test_is_extreme_volume(self):
        """Test extreme volume detection."""
        # Not extreme
        self.assertFalse(is_extreme_volume(4000, 1000, 5.0))
        self.assertFalse(is_extreme_volume(5000, 1000, 5.0))  # Equal
        
        # Extreme
        self.assertTrue(is_extreme_volume(6000, 1000, 5.0))
        self.assertTrue(is_extreme_volume(10000, 1000, 5.0))
        
        # Edge cases
        self.assertFalse(is_extreme_volume(5000, 0, 5.0))
    
    def test_format_atr_value(self):
        """Test ATR formatting."""
        # Percentage format
        result = format_atr_value(1000, 50000, use_percent=True)
        self.assertEqual(result, "2.00%")
        
        # Absolute format
        result = format_atr_value(1000, 50000, use_percent=False)
        self.assertEqual(result, "1000.00")
    
    def test_get_volatility_state(self):
        """Test volatility state calculation."""
        # Normal state
        state = get_volatility_state(100, 100, 1000, 1000)
        self.assertEqual(state["state"], "normal")
        self.assertEqual(state["atr_ratio"], 1.0)
        self.assertEqual(state["volume_ratio"], 1.0)
        
        # High state
        state = get_volatility_state(200, 100, 2500, 1000)
        self.assertEqual(state["state"], "high")
        
        # Extreme state
        state = get_volatility_state(400, 100, 6000, 1000)
        self.assertEqual(state["state"], "extreme")
        
        # Low state
        state = get_volatility_state(30, 100, 400, 1000)
        self.assertEqual(state["state"], "low")


# =============================================================================
# ATR FILTER TESTS
# =============================================================================

class TestATRFilter(unittest.TestCase):
    """Tests for ATRFilter."""
    
    def test_filter_metadata(self):
        """Test filter metadata."""
        f = ATRFilter({})
        self.assertEqual(f.name, "atr_filter")
        self.assertEqual(f.category, FilterCategory.VOLATILITY)
        self.assertEqual(f.priority, FilterPriority.MEDIUM)
    
    def test_disabled_filter(self):
        """Test disabled filter skips."""
        f = ATRFilter({"enabled": False})
        signal = create_test_signal()
        context = create_test_context(atr=1000)
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.SKIP)
    
    def test_no_atr_data_skips(self):
        """Test filter skips when no ATR data."""
        f = ATRFilter({"min_atr": 1.0})
        signal = create_test_signal()
        context = create_test_context(atr=None)
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.SKIP)
        self.assertTrue(decision.details.get("data_missing"))
    
    def test_atr_percent_below_minimum(self):
        """Test ATR percent below minimum blocks."""
        # ATR = 250, Price = 50000 -> 0.5%
        f = ATRFilter({"min_atr": 1.0, "use_atr_percent": True})
        signal = create_test_signal()
        context = create_test_context(current_price=50000, atr=250)
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.BLOCK)
        self.assertIn("too low", decision.reason.lower())
    
    def test_atr_percent_above_maximum(self):
        """Test ATR percent above maximum blocks."""
        # ATR = 3000, Price = 50000 -> 6%
        f = ATRFilter({"max_atr": 5.0, "use_atr_percent": True})
        signal = create_test_signal()
        context = create_test_context(current_price=50000, atr=3000)
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.BLOCK)
        self.assertIn("too high", decision.reason.lower())
    
    def test_atr_percent_within_range_passes(self):
        """Test ATR percent within range passes."""
        # ATR = 1000, Price = 50000 -> 2%
        f = ATRFilter({"min_atr": 1.0, "max_atr": 5.0, "use_atr_percent": True})
        signal = create_test_signal()
        context = create_test_context(current_price=50000, atr=1000)
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_atr_absolute_value(self):
        """Test ATR filter with absolute values."""
        f = ATRFilter({
            "min_atr": 500,
            "max_atr": 2000,
            "use_atr_percent": False
        })
        signal = create_test_signal()
        
        # ATR within range
        context = create_test_context(atr=1000)
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.PASS)
        
        # ATR below minimum
        context = create_test_context(atr=300)
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.BLOCK)
        
        # ATR above maximum
        context = create_test_context(atr=2500)
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.BLOCK)
    
    def test_atr_only_minimum(self):
        """Test ATR filter with only minimum set."""
        f = ATRFilter({"min_atr": 1.0, "max_atr": None, "use_atr_percent": True})
        signal = create_test_signal()
        
        # Very high ATR should pass (no max)
        context = create_test_context(current_price=50000, atr=10000)
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_atr_only_maximum(self):
        """Test ATR filter with only maximum set."""
        f = ATRFilter({"min_atr": None, "max_atr": 5.0, "use_atr_percent": True})
        signal = create_test_signal()
        
        # Very low ATR should pass (no min)
        context = create_test_context(current_price=50000, atr=100)
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_config_schema(self):
        """Test config schema is valid."""
        f = ATRFilter({})
        schema = f.get_config_schema()
        
        self.assertIn("enabled", schema)
        self.assertIn("min_atr", schema)
        self.assertIn("max_atr", schema)
        self.assertIn("atr_period", schema)
        self.assertIn("use_atr_percent", schema)


# =============================================================================
# VOLUME FILTER TESTS
# =============================================================================

class TestVolumeFilter(unittest.TestCase):
    """Tests for VolumeFilter."""
    
    def test_filter_metadata(self):
        """Test filter metadata."""
        f = VolumeFilter({})
        self.assertEqual(f.name, "volume_filter")
        self.assertEqual(f.category, FilterCategory.VOLATILITY)
        self.assertEqual(f.priority, FilterPriority.MEDIUM)
    
    def test_disabled_filter(self):
        """Test disabled filter skips."""
        f = VolumeFilter({"enabled": False})
        signal = create_test_signal()
        context = create_test_context(volume=1000)
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.SKIP)
    
    def test_no_volume_data_skips(self):
        """Test filter skips when no volume data."""
        f = VolumeFilter({"min_volume_ratio": 1.5})
        signal = create_test_signal()
        context = create_test_context(volume=None)
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.SKIP)
    
    def test_volume_ratio_below_minimum_blocks(self):
        """Test volume ratio below minimum blocks."""
        f = VolumeFilter({
            "min_volume_ratio": 1.5,
            "require_above_average": True
        })
        signal = create_test_signal()
        # Volume = 1000, Avg = 1000 -> ratio = 1.0
        context = create_test_context(volume=1000, avg_volume=1000)
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.BLOCK)
    
    def test_volume_ratio_above_minimum_passes(self):
        """Test volume ratio above minimum passes."""
        f = VolumeFilter({
            "min_volume_ratio": 1.5,
            "require_above_average": True
        })
        signal = create_test_signal()
        # Volume = 2000, Avg = 1000 -> ratio = 2.0
        context = create_test_context(volume=2000, avg_volume=1000)
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_absolute_volume_minimum(self):
        """Test absolute volume minimum."""
        f = VolumeFilter({
            "min_absolute_volume": 500000,
            "require_above_average": False
        })
        signal = create_test_signal()
        
        # Volume below absolute minimum
        context = create_test_context(volume=400000)
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.BLOCK)
        
        # Volume above absolute minimum
        context = create_test_context(volume=600000)
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_no_avg_volume_without_require_above_average(self):
        """Test filter passes when no avg_volume and require_above_average is False."""
        f = VolumeFilter({
            "require_above_average": False
        })
        signal = create_test_signal()
        context = create_test_context(volume=1000, avg_volume=None)
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_config_schema(self):
        """Test config schema is valid."""
        f = VolumeFilter({})
        schema = f.get_config_schema()
        
        self.assertIn("enabled", schema)
        self.assertIn("min_volume_ratio", schema)
        self.assertIn("volume_ma_period", schema)
        self.assertIn("require_above_average", schema)
        self.assertIn("min_absolute_volume", schema)


# =============================================================================
# EXTREME FILTER TESTS
# =============================================================================

class TestExtremeFilter(unittest.TestCase):
    """Tests for ExtremeFilter."""
    
    def test_filter_metadata(self):
        """Test filter metadata."""
        f = ExtremeFilter({})
        self.assertEqual(f.name, "extreme_filter")
        self.assertEqual(f.category, FilterCategory.VOLATILITY)
        self.assertEqual(f.priority, FilterPriority.CRITICAL)  # High priority
    
    def test_disabled_filter(self):
        """Test disabled filter skips."""
        f = ExtremeFilter({"enabled": False})
        signal = create_test_signal()
        context = create_test_context(atr=1000)
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.SKIP)
    
    def test_no_extreme_conditions_passes(self):
        """Test filter passes when no extreme conditions."""
        f = ExtremeFilter({
            "atr_multiplier": 3.0,
            "volume_multiplier": 5.0
        })
        signal = create_test_signal()
        # Normal conditions
        context = create_test_context(
            atr=100,
            volume=1500,
            avg_volume=1000
        )
        context.htf_data["avg_atr"] = 100
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_extreme_atr_blocks(self):
        """Test extreme ATR blocks."""
        f = ExtremeFilter({
            "atr_multiplier": 3.0,
            "volume_multiplier": 5.0,
            "pause_minutes": 60
        })
        signal = create_test_signal()
        # ATR is 4x average (extreme)
        context = create_test_context(
            atr=400,
            volume=1000,
            avg_volume=1000
        )
        context.htf_data["avg_atr"] = 100
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.BLOCK)
        self.assertIn("ATR spike", decision.reason)
    
    def test_extreme_volume_blocks(self):
        """Test extreme volume blocks."""
        f = ExtremeFilter({
            "atr_multiplier": 3.0,
            "volume_multiplier": 5.0,
            "pause_minutes": 60
        })
        signal = create_test_signal()
        # Volume is 6x average (extreme)
        context = create_test_context(
            atr=100,
            volume=6000,
            avg_volume=1000
        )
        context.htf_data["avg_atr"] = 100
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.BLOCK)
        self.assertIn("Volume spike", decision.reason)
    
    def test_pause_period_maintained(self):
        """Test pause period is maintained after extreme detection."""
        f = ExtremeFilter({
            "atr_multiplier": 3.0,
            "volume_multiplier": 5.0,
            "pause_minutes": 60
        })
        signal = create_test_signal()
        
        # First call - detect extreme
        now = datetime.now(timezone.utc)
        context = SignalContext(
            current_time=now,
            current_price=50000,
            atr=400,
            volume=1000,
            avg_volume=1000,
            htf_data={"avg_atr": 100}
        )
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.BLOCK)
        
        # Second call - 30 minutes later (still in pause)
        later = now + timedelta(minutes=30)
        context2 = SignalContext(
            current_time=later,
            current_price=50000,
            atr=100,  # Normal now
            volume=1000,
            avg_volume=1000,
            htf_data={"avg_atr": 100}
        )
        decision2 = f.should_allow(signal, context2)
        self.assertEqual(decision2.result, FilterResult.BLOCK)
        self.assertIn("remaining", decision2.reason.lower())
    
    def test_pause_period_expires(self):
        """Test pause period expires and trading resumes."""
        f = ExtremeFilter({
            "atr_multiplier": 3.0,
            "volume_multiplier": 5.0,
            "pause_minutes": 60
        })
        signal = create_test_signal()
        
        # First call - detect extreme
        now = datetime.now(timezone.utc)
        context = SignalContext(
            current_time=now,
            current_price=50000,
            atr=400,
            volume=1000,
            avg_volume=1000,
            htf_data={"avg_atr": 100}
        )
        f.should_allow(signal, context)
        
        # Third call - 90 minutes later (pause expired)
        much_later = now + timedelta(minutes=90)
        context3 = SignalContext(
            current_time=much_later,
            current_price=50000,
            atr=100,  # Normal
            volume=1000,
            avg_volume=1000,
            htf_data={"avg_atr": 100}
        )
        decision3 = f.should_allow(signal, context3)
        self.assertEqual(decision3.result, FilterResult.PASS)
    
    def test_reset_clears_pause(self):
        """Test reset() clears pause state."""
        f = ExtremeFilter({
            "atr_multiplier": 3.0,
            "pause_minutes": 60
        })
        signal = create_test_signal()
        
        # Trigger extreme
        now = datetime.now(timezone.utc)
        context = SignalContext(
            current_time=now,
            current_price=50000,
            atr=400,
            volume=1000,
            avg_volume=1000,
            htf_data={"avg_atr": 100}
        )
        f.should_allow(signal, context)
        
        # Reset
        f.reset()
        
        # Should pass now (no pause)
        context2 = SignalContext(
            current_time=now + timedelta(minutes=5),
            current_price=50000,
            atr=100,
            volume=1000,
            avg_volume=1000,
            htf_data={"avg_atr": 100}
        )
        decision = f.should_allow(signal, context2)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_check_atr_disabled(self):
        """Test filter works with ATR check disabled."""
        f = ExtremeFilter({
            "check_atr": False,
            "check_volume": True,
            "volume_multiplier": 5.0
        })
        signal = create_test_signal()
        
        # High ATR should be ignored
        context = SignalContext(
            current_time=datetime.now(timezone.utc),
            current_price=50000,
            atr=1000,  # Would be extreme
            volume=1000,  # Normal
            avg_volume=1000,
            htf_data={"avg_atr": 100}
        )
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_check_volume_disabled(self):
        """Test filter works with volume check disabled."""
        f = ExtremeFilter({
            "check_atr": True,
            "check_volume": False,
            "atr_multiplier": 3.0
        })
        signal = create_test_signal()
        
        # High volume should be ignored
        context = SignalContext(
            current_time=datetime.now(timezone.utc),
            current_price=50000,
            atr=100,  # Normal
            volume=10000,  # Would be extreme
            avg_volume=1000,
            htf_data={"avg_atr": 100}
        )
        
        decision = f.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_is_in_pause_method(self):
        """Test is_in_pause() method."""
        f = ExtremeFilter({"pause_minutes": 60})
        
        # Not in pause initially
        now = datetime.now(timezone.utc)
        self.assertFalse(f.is_in_pause(now))
        
        # Trigger extreme
        signal = create_test_signal()
        context = SignalContext(
            current_time=now,
            current_price=50000,
            atr=400,
            volume=1000,
            avg_volume=1000,
            htf_data={"avg_atr": 100}
        )
        f.should_allow(signal, context)
        
        # Now in pause
        self.assertTrue(f.is_in_pause(now + timedelta(minutes=5)))
        
        # Not in pause after expiry
        self.assertFalse(f.is_in_pause(now + timedelta(minutes=90)))
    
    def test_get_pause_remaining_method(self):
        """Test get_pause_remaining() method."""
        f = ExtremeFilter({"pause_minutes": 60})
        
        # No pause initially
        now = datetime.now(timezone.utc)
        self.assertIsNone(f.get_pause_remaining(now))
        
        # Trigger extreme
        signal = create_test_signal()
        context = SignalContext(
            current_time=now,
            current_price=50000,
            atr=400,
            volume=1000,
            avg_volume=1000,
            htf_data={"avg_atr": 100}
        )
        f.should_allow(signal, context)
        
        # Check remaining
        remaining = f.get_pause_remaining(now + timedelta(minutes=20))
        self.assertIsNotNone(remaining)
        self.assertGreater(remaining, 35)  # Should be ~40 min remaining
        self.assertLess(remaining, 45)
    
    def test_config_schema(self):
        """Test config schema is valid."""
        f = ExtremeFilter({})
        schema = f.get_config_schema()
        
        self.assertIn("enabled", schema)
        self.assertIn("atr_multiplier", schema)
        self.assertIn("volume_multiplier", schema)
        self.assertIn("pause_minutes", schema)
        self.assertIn("check_atr", schema)
        self.assertIn("check_volume", schema)


# =============================================================================
# PROFILE AND VALIDATION TESTS
# =============================================================================

class TestVolatilityProfiles(unittest.TestCase):
    """Tests for volatility profiles and validation."""
    
    def test_conservative_profile(self):
        """Test conservative profile configuration."""
        config = create_volatility_profile("conservative")
        
        self.assertIn("atr_filter", config)
        self.assertIn("volume_filter", config)
        self.assertIn("extreme_filter", config)
        
        # Conservative should have tighter limits
        self.assertEqual(config["atr_filter"]["max_atr"], 3.0)
        self.assertEqual(config["volume_filter"]["min_volume_ratio"], 1.5)
        self.assertEqual(config["extreme_filter"]["pause_minutes"], 120)
    
    def test_balanced_profile(self):
        """Test balanced profile configuration."""
        config = create_volatility_profile("balanced")
        
        self.assertEqual(config["atr_filter"]["max_atr"], 5.0)
        self.assertEqual(config["volume_filter"]["min_volume_ratio"], 1.0)
        self.assertEqual(config["extreme_filter"]["pause_minutes"], 60)
    
    def test_aggressive_profile(self):
        """Test aggressive profile configuration."""
        config = create_volatility_profile("aggressive")
        
        # Aggressive should have loose limits
        self.assertEqual(config["atr_filter"]["max_atr"], 10.0)
        self.assertFalse(config["volume_filter"]["enabled"])
        self.assertEqual(config["extreme_filter"]["pause_minutes"], 30)
    
    def test_disabled_profile(self):
        """Test disabled profile configuration."""
        config = create_volatility_profile("disabled")
        
        self.assertFalse(config["atr_filter"]["enabled"])
        self.assertFalse(config["volume_filter"]["enabled"])
        self.assertFalse(config["extreme_filter"]["enabled"])
    
    def test_unknown_profile_defaults_to_balanced(self):
        """Test unknown profile defaults to balanced."""
        config = create_volatility_profile("unknown_profile")
        balanced = create_volatility_profile("balanced")
        
        self.assertEqual(config, balanced)
    
    def test_validate_valid_config(self):
        """Test validation of valid config."""
        config = {
            "atr_filter": {
                "enabled": True,
                "min_atr": 1.0,
                "max_atr": 5.0
            },
            "volume_filter": {
                "enabled": True,
                "min_volume_ratio": 1.5
            },
            "extreme_filter": {
                "enabled": True,
                "atr_multiplier": 3.0,
                "volume_multiplier": 5.0,
                "pause_minutes": 60
            }
        }
        
        is_valid, errors = validate_volatility_config(config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_min_greater_than_max(self):
        """Test validation catches min >= max."""
        config = {
            "atr_filter": {
                "enabled": True,
                "min_atr": 5.0,
                "max_atr": 3.0  # Invalid!
            }
        }
        
        is_valid, errors = validate_volatility_config(config)
        self.assertFalse(is_valid)
        self.assertIn("min_atr must be less than max_atr", errors[0])
    
    def test_validate_negative_min_atr(self):
        """Test validation catches negative min_atr."""
        config = {
            "atr_filter": {
                "enabled": True,
                "min_atr": -1.0
            }
        }
        
        is_valid, errors = validate_volatility_config(config)
        self.assertFalse(is_valid)
        self.assertIn("non-negative", errors[0])
    
    def test_validate_invalid_extreme_config(self):
        """Test validation of invalid extreme config."""
        config = {
            "extreme_filter": {
                "enabled": True,
                "atr_multiplier": 0.5,  # Too low
                "pause_minutes": 0  # Too low
            }
        }
        
        is_valid, errors = validate_volatility_config(config)
        self.assertFalse(is_valid)
        self.assertGreaterEqual(len(errors), 2)


# =============================================================================
# CHAIN CREATION TESTS
# =============================================================================

class TestVolatilityFilterChain(unittest.TestCase):
    """Tests for volatility filter chain creation."""
    
    def test_create_chain_with_all_filters(self):
        """Test creating chain with all filters."""
        filters = create_volatility_filter_chain(
            atr_config={"min_atr": 1.0, "max_atr": 5.0},
            volume_config={"min_volume_ratio": 1.5},
            extreme_config={"pause_minutes": 60}
        )
        
        self.assertEqual(len(filters), 3)
        self.assertIsInstance(filters[0], ATRFilter)
        self.assertIsInstance(filters[1], VolumeFilter)
        self.assertIsInstance(filters[2], ExtremeFilter)
    
    def test_create_chain_with_some_filters(self):
        """Test creating chain with only some filters."""
        filters = create_volatility_filter_chain(
            atr_config={"min_atr": 1.0},
            volume_config=None,
            extreme_config={"pause_minutes": 30}
        )
        
        self.assertEqual(len(filters), 2)
        self.assertIsInstance(filters[0], ATRFilter)
        self.assertIsInstance(filters[1], ExtremeFilter)
    
    def test_create_empty_chain(self):
        """Test creating empty chain."""
        filters = create_volatility_filter_chain()
        self.assertEqual(len(filters), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
