"""
KOMAS v4.0 — Protection Filters Tests
=======================================

Comprehensive tests for protection-based filters.

Tests:
- EquityCurveFilter: 10 tests
- MaxDDFilter: 10 tests
- StreakFilter: 10 tests
- RecoveryFilter: 10 tests
- Helper functions: 5 tests

Total: 45+ tests

Chat #42: Filters Protection
"""

import unittest
from datetime import datetime, timedelta
from typing import Dict, List, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.filters.base import (
    Signal,
    SignalContext,
    FilterResult,
    FilterCategory,
    FilterPriority,
)
from app.filters.protection_filters import (
    # Filters
    EquityCurveFilter,
    MaxDDFilter,
    StreakFilter,
    RecoveryFilter,
    
    # Constants
    DEFAULT_EQUITY_MA_PERIOD,
    DEFAULT_MAX_DAILY_DD,
    DEFAULT_MAX_TOTAL_DD,
    DEFAULT_MAX_CONSECUTIVE_LOSSES,
    DEFAULT_DD_THRESHOLD,
    DEFAULT_SCALE_FACTOR,
    
    # Helpers
    calculate_simple_ma,
    calculate_ema,
    calculate_equity_ma,
    calculate_drawdown,
    calculate_daily_drawdown,
    get_equity_curve_peak,
    count_consecutive_losses,
    count_consecutive_wins,
    get_trades_today,
    calculate_recovery_progress,
    get_protection_state,
    validate_protection_config,
    create_protection_profile,
    create_protection_filter_chain,
)


def create_test_signal(
    symbol: str = "BTCUSDT",
    direction: str = "long",
    entry_price: float = 50000.0
) -> Signal:
    """Create a test signal"""
    return Signal(
        symbol=symbol,
        direction=direction,
        entry_price=entry_price,
        timestamp=datetime.now()
    )


def create_test_context(
    current_equity: float = 10000.0,
    starting_equity: float = 10000.0,
    equity_curve: List[float] = None,
    recent_trades: List[Dict] = None,
    current_time: datetime = None,
) -> SignalContext:
    """Create a test context"""
    return SignalContext(
        current_time=current_time or datetime.now(),
        current_price=50000.0,
        current_equity=current_equity,
        starting_equity=starting_equity,
        equity_curve=equity_curve or [starting_equity],
        recent_trades=recent_trades or [],
    )


def create_trade(
    pnl: float,
    entry_time: datetime = None,
    exit_time: datetime = None,
) -> Dict[str, Any]:
    """Create a test trade"""
    now = datetime.now()
    return {
        "pnl": pnl,
        "entry_time": entry_time or now - timedelta(hours=1),
        "exit_time": exit_time or now,
        "equity_after": 10000 + pnl,
    }


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestHelperFunctions(unittest.TestCase):
    """Tests for helper functions"""
    
    def test_calculate_simple_ma(self):
        """Test simple MA calculation"""
        data = [10, 20, 30, 40, 50]
        
        # MA5
        ma = calculate_simple_ma(data, 5)
        self.assertEqual(ma, 30.0)
        
        # MA3
        ma = calculate_simple_ma(data, 3)
        self.assertEqual(ma, 40.0)  # (30+40+50)/3
        
        # Insufficient data
        ma = calculate_simple_ma(data, 10)
        self.assertIsNone(ma)
        
        # Empty data
        ma = calculate_simple_ma([], 5)
        self.assertIsNone(ma)
    
    def test_calculate_ema(self):
        """Test EMA calculation"""
        data = [10, 20, 30, 40, 50]
        
        # EMA should be calculated
        ema = calculate_ema(data, 3)
        self.assertIsNotNone(ema)
        self.assertIsInstance(ema, float)
        
        # EMA with insufficient data
        ema = calculate_ema(data, 10)
        self.assertIsNone(ema)
    
    def test_calculate_drawdown(self):
        """Test drawdown calculation"""
        # No drawdown
        dd = calculate_drawdown(10000, 10000)
        self.assertEqual(dd, 0.0)
        
        # 10% drawdown
        dd = calculate_drawdown(9000, 10000)
        self.assertEqual(dd, 10.0)
        
        # Above peak (no DD)
        dd = calculate_drawdown(11000, 10000)
        self.assertEqual(dd, 0.0)
        
        # Edge case: zero peak
        dd = calculate_drawdown(100, 0)
        self.assertEqual(dd, 0.0)
    
    def test_count_consecutive_losses(self):
        """Test consecutive loss counting"""
        now = datetime.now()
        
        # 3 consecutive losses
        trades = [
            create_trade(-100, exit_time=now - timedelta(minutes=3)),
            create_trade(-50, exit_time=now - timedelta(minutes=2)),
            create_trade(-75, exit_time=now - timedelta(minutes=1)),
        ]
        count = count_consecutive_losses(trades)
        self.assertEqual(count, 3)
        
        # Empty trades
        count = count_consecutive_losses([])
        self.assertEqual(count, 0)
        
        # Win at the end breaks streak
        trades_with_win = [
            create_trade(-100, exit_time=now - timedelta(minutes=3)),
            create_trade(-50, exit_time=now - timedelta(minutes=2)),
            create_trade(100, exit_time=now - timedelta(minutes=1)),  # Win
        ]
        count = count_consecutive_losses(trades_with_win)
        self.assertEqual(count, 0)  # Most recent is win
    
    def test_calculate_recovery_progress(self):
        """Test recovery progress calculation"""
        # Just triggered (0% progress)
        progress = calculate_recovery_progress(10.0, 10.0, 5.0)
        self.assertEqual(progress, 0.0)
        
        # Fully recovered
        progress = calculate_recovery_progress(5.0, 10.0, 5.0)
        self.assertEqual(progress, 100.0)
        
        # Halfway
        progress = calculate_recovery_progress(7.5, 10.0, 5.0)
        self.assertEqual(progress, 50.0)
        
        # Over recovered
        progress = calculate_recovery_progress(2.0, 10.0, 5.0)
        self.assertEqual(progress, 100.0)


# =============================================================================
# EQUITY CURVE FILTER TESTS
# =============================================================================

class TestEquityCurveFilter(unittest.TestCase):
    """Tests for EquityCurveFilter"""
    
    def test_filter_properties(self):
        """Test filter class properties"""
        f = EquityCurveFilter()
        
        self.assertEqual(f.name, "equity_curve_filter")
        self.assertEqual(f.category, FilterCategory.PROTECTION)
        self.assertEqual(f.priority, FilterPriority.CRITICAL)
    
    def test_disabled_filter(self):
        """Test disabled filter passes everything"""
        f = EquityCurveFilter({"enabled": False})
        signal = create_test_signal()
        context = create_test_context()
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.SKIP)
    
    def test_insufficient_data(self):
        """Test with insufficient equity curve data"""
        f = EquityCurveFilter({"ma_period": 20})
        signal = create_test_signal()
        context = create_test_context(equity_curve=[10000] * 10)  # Only 10 points
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
        self.assertIn("Insufficient data", result.reason)
    
    def test_equity_above_ma(self):
        """Test trading when equity above MA"""
        # Create equity curve with upward trend
        curve = [10000 + i * 100 for i in range(25)]
        
        f = EquityCurveFilter({"ma_period": 20, "mode": "above"})
        signal = create_test_signal()
        context = create_test_context(
            current_equity=curve[-1],
            equity_curve=curve
        )
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_equity_below_ma_blocked(self):
        """Test blocking when equity below MA"""
        # Create equity curve with downward trend
        curve = [10000 - i * 100 for i in range(25)]
        
        f = EquityCurveFilter({
            "ma_period": 20,
            "mode": "above",
            "pause_on_below": True
        })
        signal = create_test_signal()
        context = create_test_context(
            current_equity=curve[-1],
            equity_curve=curve
        )
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.BLOCK)
    
    def test_contrarian_mode(self):
        """Test contrarian mode (trade below MA)"""
        # Create flat then drop curve
        curve = [10000] * 15 + [9000] * 10
        
        f = EquityCurveFilter({
            "ma_period": 20,
            "mode": "below",
        })
        signal = create_test_signal()
        context = create_test_context(
            current_equity=curve[-1],
            equity_curve=curve
        )
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_both_mode(self):
        """Test both mode allows trading"""
        curve = [10000] * 25
        
        f = EquityCurveFilter({"mode": "both"})
        signal = create_test_signal()
        context = create_test_context(
            current_equity=10000,
            equity_curve=curve
        )
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_buffer_zone(self):
        """Test buffer zone around MA"""
        curve = [10000] * 25
        
        f = EquityCurveFilter({
            "ma_period": 20,
            "mode": "above",
            "buffer_percent": 1.0  # 1% buffer
        })
        signal = create_test_signal()
        context = create_test_context(
            current_equity=9950,  # Slightly below MA but in buffer
            equity_curve=curve
        )
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_use_ema(self):
        """Test EMA mode"""
        curve = [10000 + i * 50 for i in range(25)]
        
        f = EquityCurveFilter({
            "ma_period": 20,
            "use_ema": True
        })
        signal = create_test_signal()
        context = create_test_context(
            current_equity=curve[-1],
            equity_curve=curve
        )
        
        result = f.should_allow(signal, context)
        self.assertIn("ma_value", result.details)
    
    def test_config_schema(self):
        """Test config schema"""
        f = EquityCurveFilter()
        schema = f.get_config_schema()
        
        self.assertIn("ma_period", schema)
        self.assertIn("mode", schema)
        self.assertIn("pause_on_below", schema)
        self.assertIn("use_ema", schema)


# =============================================================================
# MAX DD FILTER TESTS
# =============================================================================

class TestMaxDDFilter(unittest.TestCase):
    """Tests for MaxDDFilter"""
    
    def test_filter_properties(self):
        """Test filter class properties"""
        f = MaxDDFilter()
        
        self.assertEqual(f.name, "max_dd_filter")
        self.assertEqual(f.category, FilterCategory.PROTECTION)
        self.assertEqual(f.priority, FilterPriority.CRITICAL)
    
    def test_disabled_filter(self):
        """Test disabled filter passes everything"""
        f = MaxDDFilter({"enabled": False})
        signal = create_test_signal()
        context = create_test_context()
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.SKIP)
    
    def test_no_drawdown(self):
        """Test with no drawdown"""
        f = MaxDDFilter()
        signal = create_test_signal()
        context = create_test_context(
            current_equity=10000,
            starting_equity=10000,
            equity_curve=[10000]
        )
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_total_dd_exceeded(self):
        """Test blocking when total DD exceeded"""
        f = MaxDDFilter({"max_total_dd": 10.0})
        signal = create_test_signal()
        
        # 15% DD
        context = create_test_context(
            current_equity=8500,
            starting_equity=10000,
            equity_curve=[10000, 9500, 9000, 8500]
        )
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.BLOCK)
    
    def test_cooldown_period(self):
        """Test cooldown after DD hit"""
        now = datetime.now()
        f = MaxDDFilter({
            "max_total_dd": 10.0,
            "cooldown_hours": 24
        })
        
        # First, trigger the DD limit
        signal = create_test_signal()
        context = create_test_context(
            current_equity=8900,
            starting_equity=10000,
            equity_curve=[10000, 9000, 8900],
            current_time=now
        )
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.BLOCK)
        
        # Check we're in cooldown
        context2 = create_test_context(
            current_equity=9500,  # Recovered
            starting_equity=10000,
            equity_curve=[10000, 9000, 8900, 9500],
            current_time=now + timedelta(hours=1)  # 1 hour later
        )
        
        result2 = f.should_allow(signal, context2)
        self.assertEqual(result2.result, FilterResult.BLOCK)
        self.assertIn("cooldown", result2.reason.lower())
    
    def test_cooldown_expired(self):
        """Test trading resumes after cooldown"""
        now = datetime.now()
        f = MaxDDFilter({
            "max_total_dd": 10.0,
            "cooldown_hours": 24
        })
        
        # Trigger DD
        signal = create_test_signal()
        context = create_test_context(
            current_equity=8900,
            starting_equity=10000,
            equity_curve=[10000, 9000, 8900],
            current_time=now
        )
        f.should_allow(signal, context)
        
        # After cooldown
        context2 = create_test_context(
            current_equity=9500,
            starting_equity=10000,
            equity_curve=[10000, 9000, 8900, 9500],
            current_time=now + timedelta(hours=25)  # After 24h cooldown
        )
        
        result = f.should_allow(signal, context2)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_check_daily_only(self):
        """Test checking only daily DD"""
        f = MaxDDFilter({
            "check_daily": True,
            "check_total": False,
            "max_total_dd": 5.0
        })
        signal = create_test_signal()
        
        # Total DD exceeds, but we're not checking it
        context = create_test_context(
            current_equity=9000,
            starting_equity=10000,
            equity_curve=[10000, 9000]
        )
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_reset(self):
        """Test reset clears state"""
        f = MaxDDFilter()
        f._dd_hit_time = datetime.now()
        f._dd_hit_type = "total"
        
        f.reset()
        
        self.assertIsNone(f._dd_hit_time)
        self.assertIsNone(f._dd_hit_type)
    
    def test_config_schema(self):
        """Test config schema"""
        f = MaxDDFilter()
        schema = f.get_config_schema()
        
        self.assertIn("max_daily_dd", schema)
        self.assertIn("max_total_dd", schema)
        self.assertIn("cooldown_hours", schema)
    
    def test_dd_details_in_result(self):
        """Test DD details are included in result"""
        f = MaxDDFilter()
        signal = create_test_signal()
        context = create_test_context(
            current_equity=9500,
            starting_equity=10000,
            equity_curve=[10000, 9800, 9500]
        )
        
        result = f.should_allow(signal, context)
        self.assertIn("total_dd_percent", result.details)
        self.assertIn("current_equity", result.details)


# =============================================================================
# STREAK FILTER TESTS
# =============================================================================

class TestStreakFilter(unittest.TestCase):
    """Tests for StreakFilter"""
    
    def test_filter_properties(self):
        """Test filter class properties"""
        f = StreakFilter()
        
        self.assertEqual(f.name, "streak_filter")
        self.assertEqual(f.category, FilterCategory.PROTECTION)
        self.assertEqual(f.priority, FilterPriority.CRITICAL)
    
    def test_disabled_filter(self):
        """Test disabled filter passes everything"""
        f = StreakFilter({"enabled": False})
        signal = create_test_signal()
        context = create_test_context()
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.SKIP)
    
    def test_no_trades(self):
        """Test with no previous trades"""
        f = StreakFilter()
        signal = create_test_signal()
        context = create_test_context(recent_trades=[])
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_below_loss_threshold(self):
        """Test with losses below threshold"""
        now = datetime.now()
        f = StreakFilter({"max_consecutive_losses": 3})
        signal = create_test_signal()
        
        trades = [
            create_trade(-100, exit_time=now - timedelta(minutes=2)),
            create_trade(-50, exit_time=now - timedelta(minutes=1)),
        ]
        context = create_test_context(recent_trades=trades, current_time=now)
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_loss_threshold_exceeded(self):
        """Test blocking after loss threshold"""
        now = datetime.now()
        f = StreakFilter({
            "max_consecutive_losses": 3,
            "pause_trades": 5
        })
        signal = create_test_signal()
        
        # Create 3 consecutive losses with distinct times
        trades = [
            create_trade(-100, exit_time=now - timedelta(minutes=3)),
            create_trade(-50, exit_time=now - timedelta(minutes=2)),
            create_trade(-75, exit_time=now - timedelta(minutes=1)),
        ]
        context = create_test_context(recent_trades=trades, current_time=now)
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.BLOCK)
    
    def test_pause_count_decrements(self):
        """Test pause count decrements on each signal"""
        now = datetime.now()
        f = StreakFilter({
            "max_consecutive_losses": 2,
            "pause_trades": 3
        })
        signal = create_test_signal()
        
        trades = [
            create_trade(-100, exit_time=now - timedelta(minutes=2)),
            create_trade(-50, exit_time=now - timedelta(minutes=1)),
        ]
        context = create_test_context(recent_trades=trades, current_time=now)
        
        # First signal - blocked
        result1 = f.should_allow(signal, context)
        self.assertEqual(result1.result, FilterResult.BLOCK)
        
        # Second signal - blocked
        result2 = f.should_allow(signal, context)
        self.assertEqual(result2.result, FilterResult.BLOCK)
        
        # Third signal - blocked
        result3 = f.should_allow(signal, context)
        self.assertEqual(result3.result, FilterResult.BLOCK)
        
        # Fourth signal - should pass
        result4 = f.should_allow(signal, context)
        self.assertEqual(result4.result, FilterResult.PASS)
    
    def test_win_breaks_streak(self):
        """Test that win breaks loss streak"""
        now = datetime.now()
        f = StreakFilter({"max_consecutive_losses": 2})
        signal = create_test_signal()
        
        # Losses followed by win
        trades = [
            create_trade(-100, exit_time=now - timedelta(minutes=3)),
            create_trade(-50, exit_time=now - timedelta(minutes=2)),
            create_trade(200, exit_time=now - timedelta(minutes=1)),  # Win
        ]
        context = create_test_context(recent_trades=trades, current_time=now)
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_on_trade_complete_resets(self):
        """Test on_trade_complete resets pause"""
        f = StreakFilter({"reset_on_win": True})
        f._signals_to_skip = 5
        f._last_consecutive_losses = 3
        
        f.on_trade_complete({"pnl": 100})  # Win
        
        self.assertEqual(f._signals_to_skip, 0)
        self.assertEqual(f._last_consecutive_losses, 0)
    
    def test_reset(self):
        """Test reset clears state"""
        f = StreakFilter()
        f._signals_to_skip = 5
        f._last_consecutive_losses = 3
        
        f.reset()
        
        self.assertEqual(f._signals_to_skip, 0)
        self.assertEqual(f._last_consecutive_losses, 0)
    
    def test_config_schema(self):
        """Test config schema"""
        f = StreakFilter()
        schema = f.get_config_schema()
        
        self.assertIn("max_consecutive_losses", schema)
        self.assertIn("pause_trades", schema)
        self.assertIn("reset_on_win", schema)


# =============================================================================
# RECOVERY FILTER TESTS
# =============================================================================

class TestRecoveryFilter(unittest.TestCase):
    """Tests for RecoveryFilter"""
    
    def test_filter_properties(self):
        """Test filter class properties"""
        f = RecoveryFilter()
        
        self.assertEqual(f.name, "recovery_filter")
        self.assertEqual(f.category, FilterCategory.PROTECTION)
        self.assertEqual(f.priority, FilterPriority.CRITICAL)
    
    def test_disabled_filter(self):
        """Test disabled filter passes everything"""
        f = RecoveryFilter({"enabled": False})
        signal = create_test_signal()
        context = create_test_context()
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.SKIP)
    
    def test_no_drawdown(self):
        """Test normal mode with no DD"""
        f = RecoveryFilter({"dd_threshold": 10.0})
        signal = create_test_signal()
        context = create_test_context(
            current_equity=10000,
            starting_equity=10000,
            equity_curve=[10000]
        )
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
        self.assertIn("Normal mode", result.reason)
    
    def test_enters_recovery_mode(self):
        """Test entering recovery mode"""
        f = RecoveryFilter({
            "dd_threshold": 10.0,
            "scale_factor": 0.5
        })
        signal = create_test_signal()
        
        # 12% DD
        context = create_test_context(
            current_equity=8800,
            starting_equity=10000,
            equity_curve=[10000, 9500, 9000, 8800]
        )
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
        self.assertIn("Recovery mode", result.reason)
        self.assertTrue(f._in_recovery)
    
    def test_scale_factor_applied(self):
        """Test scale factor is applied to signal"""
        f = RecoveryFilter({
            "dd_threshold": 10.0,
            "scale_factor": 0.5,
            "gradual_recovery": False
        })
        signal = create_test_signal()
        
        # 12% DD
        context = create_test_context(
            current_equity=8800,
            starting_equity=10000,
            equity_curve=[10000, 9500, 9000, 8800]
        )
        
        result = f.should_allow(signal, context)
        
        # Check scale factor in signal metadata
        self.assertIn("recovery_scale_factor", signal.metadata)
        self.assertEqual(signal.metadata["recovery_scale_factor"], 0.5)
    
    def test_gradual_recovery(self):
        """Test gradual recovery increases scale"""
        f = RecoveryFilter({
            "dd_threshold": 10.0,
            "scale_factor": 0.5,
            "recovery_target": 5.0,
            "gradual_recovery": True
        })
        signal = create_test_signal()
        
        # 10% DD - just triggered
        context1 = create_test_context(
            current_equity=9000,
            starting_equity=10000,
            equity_curve=[10000, 9500, 9000]
        )
        f.should_allow(signal, context1)
        self.assertTrue(f._in_recovery)
        
        # Now at 7.5% DD - halfway recovered
        signal2 = create_test_signal()
        context2 = create_test_context(
            current_equity=9250,
            starting_equity=10000,
            equity_curve=[10000, 9500, 9000, 9250]
        )
        result2 = f.should_allow(signal2, context2)
        
        # Scale should be between 0.5 and 1.0
        scale = signal2.metadata.get("recovery_scale_factor", 1.0)
        self.assertGreater(scale, 0.5)
        self.assertLess(scale, 1.0)
    
    def test_exits_recovery_mode(self):
        """Test exiting recovery mode"""
        f = RecoveryFilter({
            "dd_threshold": 10.0,
            "recovery_target": 5.0
        })
        signal = create_test_signal()
        
        # Trigger recovery
        context1 = create_test_context(
            current_equity=8900,
            starting_equity=10000,
            equity_curve=[10000, 9000, 8900]
        )
        f.should_allow(signal, context1)
        self.assertTrue(f._in_recovery)
        
        # Recover to 5% DD
        context2 = create_test_context(
            current_equity=9500,
            starting_equity=10000,
            equity_curve=[10000, 9000, 8900, 9500]
        )
        result = f.should_allow(signal, context2)
        
        self.assertFalse(f._in_recovery)
        self.assertIn("Normal mode", result.reason)
    
    def test_block_on_extreme_dd(self):
        """Test blocking on extreme DD"""
        f = RecoveryFilter({
            "dd_threshold": 10.0,
            "block_on_extreme_dd": True,
            "extreme_dd_threshold": 25.0
        })
        signal = create_test_signal()
        
        # 30% DD
        context = create_test_context(
            current_equity=7000,
            starting_equity=10000,
            equity_curve=[10000, 8000, 7000]
        )
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.BLOCK)
    
    def test_reset(self):
        """Test reset clears state"""
        f = RecoveryFilter()
        f._in_recovery = True
        f._recovery_started_dd = 15.0
        
        f.reset()
        
        self.assertFalse(f._in_recovery)
        self.assertEqual(f._recovery_started_dd, 0.0)
    
    def test_config_schema(self):
        """Test config schema"""
        f = RecoveryFilter()
        schema = f.get_config_schema()
        
        self.assertIn("dd_threshold", schema)
        self.assertIn("scale_factor", schema)
        self.assertIn("recovery_target", schema)
        self.assertIn("gradual_recovery", schema)


# =============================================================================
# PROFILE AND FACTORY TESTS
# =============================================================================

class TestProfilesAndFactories(unittest.TestCase):
    """Tests for profiles and factory functions"""
    
    def test_create_protection_profile_conservative(self):
        """Test conservative profile"""
        profile = create_protection_profile("conservative")
        
        self.assertIn("equity_curve_filter", profile)
        self.assertIn("max_dd_filter", profile)
        self.assertIn("streak_filter", profile)
        self.assertIn("recovery_filter", profile)
        
        # Conservative has stricter limits
        self.assertEqual(profile["max_dd_filter"]["max_daily_dd"], 3.0)
        self.assertEqual(profile["streak_filter"]["max_consecutive_losses"], 2)
    
    def test_create_protection_profile_balanced(self):
        """Test balanced profile"""
        profile = create_protection_profile("balanced")
        
        self.assertEqual(profile["max_dd_filter"]["max_daily_dd"], 5.0)
        self.assertEqual(profile["streak_filter"]["max_consecutive_losses"], 3)
    
    def test_create_protection_profile_aggressive(self):
        """Test aggressive profile"""
        profile = create_protection_profile("aggressive")
        
        self.assertEqual(profile["max_dd_filter"]["max_daily_dd"], 8.0)
        self.assertEqual(profile["streak_filter"]["max_consecutive_losses"], 5)
    
    def test_create_protection_profile_disabled(self):
        """Test disabled profile"""
        profile = create_protection_profile("disabled")
        
        for filter_config in profile.values():
            self.assertFalse(filter_config.get("enabled", True))
    
    def test_create_protection_profile_unknown(self):
        """Test unknown profile falls back to balanced"""
        profile = create_protection_profile("unknown_profile")
        
        # Should be same as balanced
        balanced = create_protection_profile("balanced")
        self.assertEqual(
            profile["max_dd_filter"]["max_daily_dd"],
            balanced["max_dd_filter"]["max_daily_dd"]
        )
    
    def test_create_protection_filter_chain(self):
        """Test creating filter chain"""
        filters = create_protection_filter_chain()
        
        self.assertEqual(len(filters), 4)
        
        filter_names = [f.name for f in filters]
        self.assertIn("equity_curve_filter", filter_names)
        self.assertIn("max_dd_filter", filter_names)
        self.assertIn("streak_filter", filter_names)
        self.assertIn("recovery_filter", filter_names)
    
    def test_create_protection_filter_chain_partial(self):
        """Test creating partial chain"""
        filters = create_protection_filter_chain(
            equity_curve=True,
            max_dd=True,
            streak=False,
            recovery=False
        )
        
        self.assertEqual(len(filters), 2)
        
        filter_names = [f.name for f in filters]
        self.assertIn("equity_curve_filter", filter_names)
        self.assertIn("max_dd_filter", filter_names)
        self.assertNotIn("streak_filter", filter_names)


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestValidation(unittest.TestCase):
    """Tests for config validation"""
    
    def test_validate_valid_config(self):
        """Test validation of valid config"""
        config = {
            "ma_period": 20,
            "mode": "above",
            "max_daily_dd": 5.0,
            "max_total_dd": 15.0,
            "max_consecutive_losses": 3,
            "scale_factor": 0.5,
        }
        
        is_valid, errors = validate_protection_config(config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_invalid_ma_period(self):
        """Test validation catches invalid MA period"""
        config = {"ma_period": 0}
        
        is_valid, errors = validate_protection_config(config)
        self.assertFalse(is_valid)
        self.assertTrue(any("ma_period" in e for e in errors))
    
    def test_validate_invalid_mode(self):
        """Test validation catches invalid mode"""
        config = {"mode": "invalid"}
        
        is_valid, errors = validate_protection_config(config)
        self.assertFalse(is_valid)
        self.assertTrue(any("mode" in e for e in errors))
    
    def test_validate_invalid_dd(self):
        """Test validation catches invalid DD values"""
        config = {"max_daily_dd": -5.0}
        
        is_valid, errors = validate_protection_config(config)
        self.assertFalse(is_valid)
        self.assertTrue(any("max_daily_dd" in e for e in errors))
    
    def test_validate_invalid_scale_factor(self):
        """Test validation catches invalid scale factor"""
        config = {"scale_factor": 1.5}  # Must be <= 1.0
        
        is_valid, errors = validate_protection_config(config)
        self.assertFalse(is_valid)
        self.assertTrue(any("scale_factor" in e for e in errors))


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration(unittest.TestCase):
    """Integration tests for protection filters"""
    
    def test_all_filters_together(self):
        """Test all filters working together"""
        filters = create_protection_filter_chain()
        
        signal = create_test_signal()
        context = create_test_context(
            current_equity=10000,
            starting_equity=10000,
            equity_curve=[10000] * 25
        )
        
        # All should pass with healthy equity
        for f in filters:
            result = f.should_allow(signal, context)
            self.assertIn(result.result, [FilterResult.PASS, FilterResult.SKIP])
    
    def test_protection_state_helper(self):
        """Test get_protection_state helper"""
        now = datetime.now()
        trades = [
            create_trade(-100, exit_time=now - timedelta(minutes=2)),
            create_trade(-50, exit_time=now - timedelta(minutes=1)),
        ]
        
        context = create_test_context(
            current_equity=9850,
            starting_equity=10000,
            equity_curve=[10000, 9900, 9850],
            recent_trades=trades,
            current_time=now
        )
        
        state = get_protection_state(context)
        
        self.assertEqual(state["current_equity"], 9850)
        self.assertEqual(state["consecutive_losses"], 2)
        self.assertGreater(state["current_dd_percent"], 0)


# =============================================================================
# RUN TESTS
# =============================================================================

def run_tests():
    """Run all tests and print summary"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestHelperFunctions))
    suite.addTests(loader.loadTestsFromTestCase(TestEquityCurveFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestMaxDDFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestStreakFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestRecoveryFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestProfilesAndFactories))
    suite.addTests(loader.loadTestsFromTestCase(TestValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("PROTECTION FILTERS TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n✅ ALL TESTS PASSED!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        if result.failures:
            print("\nFailures:")
            for test, trace in result.failures:
                print(f"  - {test}")
        if result.errors:
            print("\nErrors:")
            for test, trace in result.errors:
                print(f"  - {test}")
    
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
