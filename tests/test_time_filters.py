"""
KOMAS v4.0 — Time Filters Unit Tests
=====================================

Comprehensive tests for SessionFilter, WeekdayFilter, and CooldownFilter.

Chat #38: Filters Time
Author: KOMAS Team
Version: 4.0
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from app.filters.base import (
    Signal,
    SignalContext,
    FilterResult,
    FilterCategory,
    FilterPriority,
    create_pass_decision,
    create_block_decision,
)
from app.filters.time_filters import (
    SessionFilter,
    WeekdayFilter,
    CooldownFilter,
    TRADING_SESSIONS,
    SESSION_OVERLAPS,
    WEEKDAY_NAMES,
    get_current_sessions,
    is_in_session,
    get_session_overlap,
    get_time_filter_summary,
    create_time_filter_chain,
)
from app.filters.chain import FilterChain, ChainResult
from app.filters.registry import FilterRegistry


# =============================================================================
# TEST HELPERS
# =============================================================================

def create_test_signal(
    symbol: str = "BTCUSDT",
    direction: str = "long",
    entry_price: float = 50000.0,
    timestamp: datetime = None
) -> Signal:
    """Create a test signal"""
    return Signal(
        symbol=symbol,
        direction=direction,
        entry_price=entry_price,
        timestamp=timestamp or datetime.now(timezone.utc)
    )


def create_test_context(
    current_time: datetime = None,
    recent_trades: list = None,
    **kwargs
) -> SignalContext:
    """Create a test context"""
    return SignalContext(
        current_time=current_time or datetime.now(timezone.utc),
        current_price=50000.0,
        recent_trades=recent_trades or [],
        **kwargs
    )


def make_utc_time(hour: int, weekday: int = 0) -> datetime:
    """Create a UTC datetime with specific hour and weekday"""
    # Start from a known Monday (2024-01-01 was a Monday)
    base = datetime(2024, 1, 1, hour, 0, 0, tzinfo=timezone.utc)
    # Adjust to desired weekday
    days_to_add = weekday  # 0=Monday
    return base + timedelta(days=days_to_add)


# =============================================================================
# SESSION FILTER TESTS
# =============================================================================

class TestSessionFilter(unittest.TestCase):
    """Tests for SessionFilter"""
    
    def test_init_default_config(self):
        """Test default configuration"""
        f = SessionFilter()
        self.assertTrue(f.enabled)
        self.assertEqual(f.name, "session_filter")
        self.assertEqual(f.category, FilterCategory.TIME)
        self.assertEqual(f.priority, FilterPriority.HIGH)
    
    def test_init_custom_config(self):
        """Test custom configuration"""
        f = SessionFilter({"sessions": ["europe"], "enabled": False})
        self.assertFalse(f.enabled)
        self.assertEqual(f.config.get("sessions"), ["europe"])
    
    def test_asia_session_allowed(self):
        """Test signal during Asia session (00:00-08:00 UTC)"""
        f = SessionFilter({"sessions": ["asia"]})
        
        # 03:00 UTC - middle of Asia session
        time = make_utc_time(hour=3)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
        self.assertIn("asia", result.reason.lower())
    
    def test_asia_session_blocked(self):
        """Test signal blocked outside Asia session"""
        f = SessionFilter({"sessions": ["asia"]})
        
        # 12:00 UTC - outside Asia session
        time = make_utc_time(hour=12)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_blocked)
    
    def test_europe_session_allowed(self):
        """Test signal during Europe session (08:00-16:00 UTC)"""
        f = SessionFilter({"sessions": ["europe"]})
        
        # 10:00 UTC - middle of Europe session
        time = make_utc_time(hour=10)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
    
    def test_us_session_allowed(self):
        """Test signal during US session (13:00-22:00 UTC)"""
        f = SessionFilter({"sessions": ["us"]})
        
        # 18:00 UTC - middle of US session
        time = make_utc_time(hour=18)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
    
    def test_multiple_sessions_allowed(self):
        """Test signal allowed when in any of multiple sessions"""
        f = SessionFilter({"sessions": ["asia", "europe"]})
        
        # 10:00 UTC - Europe session
        time = make_utc_time(hour=10)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
    
    def test_all_sessions_allowed(self):
        """Test 'all' sessions config allows any time"""
        f = SessionFilter({"sessions": ["all"]})
        
        # Any time should pass
        time = make_utc_time(hour=5)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
    
    def test_europe_us_overlap_allowed(self):
        """Test signal during Europe-US overlap (13:00-16:00 UTC)"""
        f = SessionFilter({"sessions": ["europe"], "include_overlaps": True})
        
        # 14:00 UTC - in overlap
        time = make_utc_time(hour=14)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
    
    def test_disabled_filter_skips(self):
        """Test disabled filter returns SKIP"""
        f = SessionFilter({"enabled": False, "sessions": ["asia"]})
        
        time = make_utc_time(hour=12)  # Outside Asia
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.SKIP)
    
    def test_empty_sessions_passes(self):
        """Test empty sessions list passes all"""
        f = SessionFilter({"sessions": []})
        
        time = make_utc_time(hour=12)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)


# =============================================================================
# WEEKDAY FILTER TESTS
# =============================================================================

class TestWeekdayFilter(unittest.TestCase):
    """Tests for WeekdayFilter"""
    
    def test_init_default_config(self):
        """Test default configuration (Monday-Friday)"""
        f = WeekdayFilter()
        self.assertTrue(f.enabled)
        self.assertEqual(f.name, "weekday_filter")
    
    def test_monday_allowed(self):
        """Test Monday (0) is allowed by default"""
        f = WeekdayFilter({"allowed_days": [0, 1, 2, 3, 4]})
        
        time = make_utc_time(hour=12, weekday=0)  # Monday
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
        self.assertIn("Monday", result.reason)
    
    def test_friday_allowed(self):
        """Test Friday (4) is allowed by default"""
        f = WeekdayFilter({"allowed_days": [0, 1, 2, 3, 4]})
        
        time = make_utc_time(hour=12, weekday=4)  # Friday
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
    
    def test_saturday_blocked(self):
        """Test Saturday (5) is blocked by default"""
        f = WeekdayFilter({"allowed_days": [0, 1, 2, 3, 4]})
        
        time = make_utc_time(hour=12, weekday=5)  # Saturday
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_blocked)
        self.assertIn("Saturday", result.reason)
    
    def test_sunday_blocked(self):
        """Test Sunday (6) is blocked by default"""
        f = WeekdayFilter({"allowed_days": [0, 1, 2, 3, 4]})
        
        time = make_utc_time(hour=12, weekday=6)  # Sunday
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_blocked)
    
    def test_weekend_only_config(self):
        """Test weekend-only configuration"""
        f = WeekdayFilter({"allowed_days": [5, 6]})  # Sat, Sun
        
        # Saturday should pass
        time = make_utc_time(hour=12, weekday=5)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
        
        # Monday should block
        time = make_utc_time(hour=12, weekday=0)
        context = create_test_context(current_time=time)
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_blocked)
    
    def test_empty_days_passes(self):
        """Test empty allowed_days passes all"""
        f = WeekdayFilter({"allowed_days": []})
        
        time = make_utc_time(hour=12, weekday=5)  # Saturday
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
    
    def test_disabled_filter_skips(self):
        """Test disabled filter returns SKIP"""
        f = WeekdayFilter({"enabled": False})
        
        time = make_utc_time(hour=12, weekday=6)  # Sunday
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.SKIP)


# =============================================================================
# COOLDOWN FILTER TESTS
# =============================================================================

class TestCooldownFilter(unittest.TestCase):
    """Tests for CooldownFilter"""
    
    def test_init_default_config(self):
        """Test default configuration"""
        f = CooldownFilter()
        self.assertTrue(f.enabled)
        self.assertEqual(f.name, "cooldown_filter")
        self.assertEqual(f.config.get("cooldown_minutes", 60), 60)
    
    def test_no_previous_trades_passes(self):
        """Test passes when no previous trades"""
        f = CooldownFilter({"cooldown_minutes": 60})
        
        signal = create_test_signal()
        context = create_test_context(recent_trades=[])
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
    
    def test_cooldown_active_blocks(self):
        """Test blocks when within cooldown period"""
        f = CooldownFilter({"cooldown_minutes": 60, "per_symbol": False})
        
        now = datetime.now(timezone.utc)
        # Last trade was 30 minutes ago
        last_trade_time = now - timedelta(minutes=30)
        
        recent_trades = [{
            "symbol": "BTCUSDT",
            "exit_time": last_trade_time,
            "pnl": 0  # Breakeven
        }]
        
        signal = create_test_signal()
        context = create_test_context(
            current_time=now,
            recent_trades=recent_trades
        )
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_blocked)
        self.assertIn("remaining", result.reason.lower())
    
    def test_cooldown_passed_allows(self):
        """Test allows when cooldown has passed"""
        f = CooldownFilter({"cooldown_minutes": 60, "per_symbol": False})
        
        now = datetime.now(timezone.utc)
        # Last trade was 90 minutes ago
        last_trade_time = now - timedelta(minutes=90)
        
        recent_trades = [{
            "symbol": "BTCUSDT",
            "exit_time": last_trade_time,
            "pnl": 0
        }]
        
        signal = create_test_signal()
        context = create_test_context(
            current_time=now,
            recent_trades=recent_trades
        )
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
    
    def test_after_win_shorter_cooldown(self):
        """Test shorter cooldown after winning trade"""
        f = CooldownFilter({
            "cooldown_minutes": 60,
            "after_win_cooldown": 15,
            "per_symbol": False
        })
        
        now = datetime.now(timezone.utc)
        # Last trade was 20 minutes ago (> 15 min win cooldown)
        last_trade_time = now - timedelta(minutes=20)
        
        recent_trades = [{
            "symbol": "BTCUSDT",
            "exit_time": last_trade_time,
            "pnl": 100  # Win
        }]
        
        signal = create_test_signal()
        context = create_test_context(
            current_time=now,
            recent_trades=recent_trades
        )
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
    
    def test_after_loss_longer_cooldown(self):
        """Test longer cooldown after losing trade"""
        f = CooldownFilter({
            "cooldown_minutes": 60,
            "after_loss_cooldown": 120,
            "per_symbol": False
        })
        
        now = datetime.now(timezone.utc)
        # Last trade was 90 minutes ago (< 120 min loss cooldown)
        last_trade_time = now - timedelta(minutes=90)
        
        recent_trades = [{
            "symbol": "BTCUSDT",
            "exit_time": last_trade_time,
            "pnl": -50  # Loss
        }]
        
        signal = create_test_signal()
        context = create_test_context(
            current_time=now,
            recent_trades=recent_trades
        )
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_blocked)
    
    def test_per_symbol_cooldown(self):
        """Test per-symbol cooldown"""
        f = CooldownFilter({
            "cooldown_minutes": 60,
            "per_symbol": True
        })
        
        now = datetime.now(timezone.utc)
        # Last trade on BTCUSDT was 30 minutes ago
        last_trade_time = now - timedelta(minutes=30)
        
        recent_trades = [{
            "symbol": "BTCUSDT",
            "exit_time": last_trade_time,
            "pnl": 0
        }]
        
        # Signal for BTCUSDT should be blocked
        btc_signal = create_test_signal(symbol="BTCUSDT")
        context = create_test_context(
            current_time=now,
            recent_trades=recent_trades
        )
        result = f.should_allow(btc_signal, context)
        self.assertTrue(result.is_blocked)
        
        # Signal for ETHUSDT should pass (different symbol)
        eth_signal = create_test_signal(symbol="ETHUSDT")
        result = f.should_allow(eth_signal, context)
        self.assertTrue(result.is_passed)
    
    def test_on_trade_complete_tracking(self):
        """Test trade completion tracking"""
        f = CooldownFilter({"cooldown_minutes": 60})
        
        # Simulate trade completion
        trade_result = {
            "symbol": "BTCUSDT",
            "exit_time": datetime.now(timezone.utc),
            "pnl": 100
        }
        f.on_trade_complete(trade_result)
        
        # Internal tracking should have the trade
        self.assertIn("BTCUSDT", f._last_trades)
        self.assertIn("__global__", f._last_trades)
    
    def test_reset_clears_tracking(self):
        """Test reset clears internal state"""
        f = CooldownFilter()
        
        # Add some trades
        f.on_trade_complete({"symbol": "BTCUSDT", "exit_time": datetime.now(timezone.utc), "pnl": 0})
        self.assertTrue(len(f._last_trades) > 0)
        
        # Reset
        f.reset()
        self.assertEqual(len(f._last_trades), 0)


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestHelperFunctions(unittest.TestCase):
    """Tests for helper functions"""
    
    def test_get_current_sessions_asia(self):
        """Test get_current_sessions during Asia hours"""
        time = make_utc_time(hour=3)  # 03:00 UTC
        sessions = get_current_sessions(time)
        
        self.assertIn("asia", sessions)
        self.assertNotIn("europe", sessions)
        self.assertNotIn("us", sessions)
    
    def test_get_current_sessions_europe(self):
        """Test get_current_sessions during Europe hours"""
        time = make_utc_time(hour=10)  # 10:00 UTC
        sessions = get_current_sessions(time)
        
        self.assertIn("europe", sessions)
        self.assertNotIn("asia", sessions)
    
    def test_get_current_sessions_overlap(self):
        """Test get_current_sessions during overlap"""
        time = make_utc_time(hour=14)  # 14:00 UTC
        sessions = get_current_sessions(time)
        
        self.assertIn("europe", sessions)
        self.assertIn("us", sessions)
    
    def test_is_in_session(self):
        """Test is_in_session function"""
        asia_time = make_utc_time(hour=3)
        europe_time = make_utc_time(hour=10)
        
        self.assertTrue(is_in_session(asia_time, "asia"))
        self.assertFalse(is_in_session(asia_time, "europe"))
        
        self.assertTrue(is_in_session(europe_time, "europe"))
        self.assertFalse(is_in_session(europe_time, "asia"))
    
    def test_get_session_overlap(self):
        """Test get_session_overlap function"""
        # During Europe-US overlap
        overlap_time = make_utc_time(hour=14)
        overlap = get_session_overlap(overlap_time)
        self.assertEqual(overlap, "europe_us")
        
        # During Asia-Europe overlap
        overlap_time = make_utc_time(hour=8)
        overlap = get_session_overlap(overlap_time)
        self.assertEqual(overlap, "asia_europe")
        
        # No overlap
        no_overlap_time = make_utc_time(hour=5)
        overlap = get_session_overlap(no_overlap_time)
        self.assertIsNone(overlap)
    
    def test_get_time_filter_summary(self):
        """Test get_time_filter_summary function"""
        time = make_utc_time(hour=14, weekday=2)  # Wednesday 14:00 UTC
        summary = get_time_filter_summary(time)
        
        self.assertEqual(summary["current_hour"], 14)
        self.assertEqual(summary["current_weekday"], 2)
        self.assertEqual(summary["weekday_name"], "Wednesday")
        self.assertIn("europe", summary["active_sessions"])
        self.assertIn("us", summary["active_sessions"])
    
    def test_create_time_filter_chain(self):
        """Test create_time_filter_chain factory function"""
        filters = create_time_filter_chain(
            session_enabled=True,
            sessions=["europe"],
            weekday_enabled=True,
            allowed_days=[0, 1, 2, 3, 4],
            cooldown_enabled=True,
            cooldown_minutes=30
        )
        
        self.assertEqual(len(filters), 3)
        self.assertIsInstance(filters[0], SessionFilter)
        self.assertIsInstance(filters[1], WeekdayFilter)
        self.assertIsInstance(filters[2], CooldownFilter)


# =============================================================================
# FILTER CHAIN TESTS
# =============================================================================

class TestFilterChain(unittest.TestCase):
    """Tests for FilterChain with time filters"""
    
    def test_chain_all_pass(self):
        """Test chain when all filters pass"""
        session_filter = SessionFilter({"sessions": ["europe"]})
        weekday_filter = WeekdayFilter({"allowed_days": [0, 1, 2, 3, 4]})
        
        chain = FilterChain([session_filter, weekday_filter])
        
        # Wednesday 10:00 UTC - Europe session, weekday
        time = make_utc_time(hour=10, weekday=2)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = chain.apply(signal, context)
        self.assertTrue(result.is_passed)
        self.assertEqual(len(result.passed_filters), 2)
    
    def test_chain_first_blocks(self):
        """Test chain stops on first block (short circuit)"""
        session_filter = SessionFilter({"sessions": ["asia"]})
        weekday_filter = WeekdayFilter({"allowed_days": [0, 1, 2, 3, 4]})
        
        chain = FilterChain([session_filter, weekday_filter], short_circuit=True)
        
        # Wednesday 10:00 UTC - Europe session (not Asia)
        time = make_utc_time(hour=10, weekday=2)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = chain.apply(signal, context)
        self.assertTrue(result.is_blocked)
        self.assertEqual(result.blocked_by, "session_filter")
    
    def test_chain_second_blocks(self):
        """Test chain stops on second filter block"""
        session_filter = SessionFilter({"sessions": ["europe"]})
        weekday_filter = WeekdayFilter({"allowed_days": [0, 1, 2, 3, 4]})  # Blocks weekends
        
        chain = FilterChain([session_filter, weekday_filter])
        
        # Saturday 10:00 UTC - Europe session, but weekend
        time = make_utc_time(hour=10, weekday=5)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = chain.apply(signal, context)
        self.assertTrue(result.is_blocked)
        self.assertEqual(result.blocked_by, "weekday_filter")
    
    def test_chain_skips_disabled(self):
        """Test chain skips disabled filters"""
        session_filter = SessionFilter({"sessions": ["asia"], "enabled": False})
        weekday_filter = WeekdayFilter({"allowed_days": [0, 1, 2, 3, 4]})
        
        chain = FilterChain([session_filter, weekday_filter])
        
        # Wednesday 10:00 UTC - would fail session if enabled
        time = make_utc_time(hour=10, weekday=2)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = chain.apply(signal, context)
        self.assertTrue(result.is_passed)
        self.assertIn("session_filter", result.skipped_filters)
    
    def test_chain_statistics(self):
        """Test chain statistics tracking"""
        chain = FilterChain([
            SessionFilter({"sessions": ["europe"]}),
            WeekdayFilter({"allowed_days": [0, 1, 2, 3, 4]})
        ])
        
        # Run some signals
        time = make_utc_time(hour=10, weekday=2)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        chain.apply(signal, context)
        chain.apply(signal, context)
        
        stats = chain.get_stats()
        self.assertEqual(stats["total_calls"], 2)
        self.assertEqual(stats["total_passed"], 2)


# =============================================================================
# REGISTRY TESTS
# =============================================================================

class TestFilterRegistry(unittest.TestCase):
    """Tests for filter registry"""
    
    def test_time_filters_registered(self):
        """Test time filters are registered"""
        names = FilterRegistry.get_names()
        
        self.assertIn("session_filter", names)
        self.assertIn("weekday_filter", names)
        self.assertIn("cooldown_filter", names)
    
    def test_get_by_category_time(self):
        """Test getting filters by TIME category"""
        time_filters = FilterRegistry.get_by_category(FilterCategory.TIME)
        
        self.assertIn("session_filter", time_filters)
        self.assertIn("weekday_filter", time_filters)
        self.assertIn("cooldown_filter", time_filters)
    
    def test_create_instance(self):
        """Test creating filter instance from registry"""
        instance = FilterRegistry.create_instance(
            "session_filter",
            {"sessions": ["europe"]}
        )
        
        self.assertIsInstance(instance, SessionFilter)
        self.assertEqual(instance.config.get("sessions"), ["europe"])


# =============================================================================
# EDGE CASE TESTS
# =============================================================================

class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and error handling"""
    
    def test_session_boundary_start(self):
        """Test session at exact start time"""
        f = SessionFilter({"sessions": ["europe"]})
        
        # Exactly 08:00 UTC - Europe start
        time = make_utc_time(hour=8)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        # 08:00 is in overlap, should pass
        self.assertTrue(result.is_passed)
    
    def test_session_boundary_end(self):
        """Test session at exact end time"""
        f = SessionFilter({"sessions": ["asia"]})
        
        # Exactly 08:00 UTC - Asia ends at 08:00
        time = make_utc_time(hour=8)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        # 08:00 is NOT in Asia (end is exclusive)
        # But overlap allows if include_overlaps is True
        # Default config includes overlaps, so should pass
        self.assertTrue(result.is_passed)
    
    def test_cooldown_iso_string_time(self):
        """Test cooldown with ISO string exit_time"""
        f = CooldownFilter({"cooldown_minutes": 60, "per_symbol": False})
        
        now = datetime.now(timezone.utc)
        # Last trade was 30 minutes ago, using ISO string
        last_trade_time = (now - timedelta(minutes=30)).isoformat()
        
        recent_trades = [{
            "symbol": "BTCUSDT",
            "exit_time": last_trade_time,
            "pnl": 0
        }]
        
        signal = create_test_signal()
        context = create_test_context(
            current_time=now,
            recent_trades=recent_trades
        )
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_blocked)
    
    def test_weekday_all_days_config(self):
        """Test weekday filter with all days allowed"""
        f = WeekdayFilter({"allowed_days": [0, 1, 2, 3, 4, 5, 6]})
        
        # Sunday should pass
        time = make_utc_time(hour=12, weekday=6)
        signal = create_test_signal()
        context = create_test_context(current_time=time)
        
        result = f.should_allow(signal, context)
        self.assertTrue(result.is_passed)
    
    def test_unknown_session_ignored(self):
        """Test unknown session name is handled"""
        # This should not raise, just log warning
        result = is_in_session(make_utc_time(hour=10), "unknown_session")
        self.assertFalse(result)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Run with verbosity
    unittest.main(verbosity=2)
