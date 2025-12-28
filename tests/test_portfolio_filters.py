"""
KOMAS v4.0 — Portfolio Filters Unit Tests
==========================================

Comprehensive tests for CorrelationFilter, DirectionFilter, and SectorFilter.

Chat #41: Filters Portfolio
Author: KOMAS Team
"""

import unittest
from datetime import datetime
from typing import Dict, List, Any

# Import test targets
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
from filters.portfolio_filters import (
    # Filters
    CorrelationFilter,
    DirectionFilter,
    SectorFilter,
    
    # Constants
    DEFAULT_MAX_CORRELATED_POSITIONS,
    DEFAULT_MAX_LONG_POSITIONS,
    DEFAULT_MAX_SHORT_POSITIONS,
    DEFAULT_MAX_PER_SECTOR,
    
    # Sector data
    SECTOR_MAPPING,
    AVAILABLE_SECTORS,
    CORRELATION_GROUPS,
    
    # Helpers
    get_sector,
    get_correlation_groups_for_symbol,
    are_correlated,
    count_correlated_positions,
    count_positions_by_direction,
    count_positions_by_sector,
    get_positions_in_sector,
    calculate_net_exposure,
    get_portfolio_summary,
    create_portfolio_filter_chain,
    validate_portfolio_config,
    create_portfolio_profile,
)


def create_test_signal(symbol="BTCUSDT", direction="long", entry_price=50000.0):
    """Create a test signal."""
    return Signal(
        symbol=symbol,
        direction=direction,
        entry_price=entry_price,
        timestamp=datetime.now(),
        timeframe="1h",
        indicator="trg"
    )


def create_test_context(open_positions=None, current_equity=10000.0):
    """Create a test context."""
    return SignalContext(
        current_time=datetime.now(),
        current_price=50000.0,
        open_positions=open_positions or [],
        current_equity=current_equity,
        starting_equity=10000.0
    )


def create_position(symbol, direction="long", entry_price=50000.0):
    """Create a position dict."""
    return {
        "symbol": symbol,
        "direction": direction,
        "entry_price": entry_price,
        "entry_time": datetime.now()
    }


class TestSectorHelpers(unittest.TestCase):
    """Tests for sector classification helper functions."""
    
    def test_get_sector_btc(self):
        self.assertEqual(get_sector("BTCUSDT"), "layer1")
    
    def test_get_sector_eth(self):
        self.assertEqual(get_sector("ETHUSDT"), "layer1")
    
    def test_get_sector_defi(self):
        self.assertEqual(get_sector("UNIUSDT"), "defi")
    
    def test_get_sector_meme(self):
        self.assertEqual(get_sector("DOGEUSDT"), "meme")
    
    def test_get_sector_ai(self):
        self.assertEqual(get_sector("FETUSDT"), "ai")
    
    def test_get_sector_gaming(self):
        self.assertEqual(get_sector("AXSUSDT"), "gaming")
    
    def test_get_sector_unknown(self):
        self.assertEqual(get_sector("UNKNOWNUSDT"), "unknown")
    
    def test_get_sector_custom_mapping(self):
        custom = {"CUSTOMUSDT": "custom_sector"}
        self.assertEqual(get_sector("CUSTOMUSDT", custom), "custom_sector")
    
    def test_available_sectors(self):
        self.assertIn("layer1", AVAILABLE_SECTORS)
        self.assertIn("defi", AVAILABLE_SECTORS)
        self.assertIn("meme", AVAILABLE_SECTORS)


class TestCorrelationHelpers(unittest.TestCase):
    """Tests for correlation helper functions."""
    
    def test_get_correlation_groups_btc(self):
        groups = get_correlation_groups_for_symbol("BTCUSDT")
        self.assertIn("btc_correlated", groups)
    
    def test_get_correlation_groups_eth(self):
        groups = get_correlation_groups_for_symbol("ETHUSDT")
        self.assertIn("btc_correlated", groups)
        self.assertIn("eth_ecosystem", groups)
    
    def test_get_correlation_groups_sol(self):
        groups = get_correlation_groups_for_symbol("SOLUSDT")
        self.assertIn("sol_ecosystem", groups)
    
    def test_get_correlation_groups_unknown(self):
        groups = get_correlation_groups_for_symbol("UNKNOWNUSDT")
        self.assertEqual(groups, [])
    
    def test_are_correlated_btc_eth(self):
        self.assertTrue(are_correlated("BTCUSDT", "ETHUSDT"))
    
    def test_are_correlated_same_group(self):
        self.assertTrue(are_correlated("DOGEUSDT", "SHIBUSDT"))
    
    def test_are_correlated_different_groups(self):
        self.assertFalse(are_correlated("BTCUSDT", "AXSUSDT"))
    
    def test_count_correlated_positions_none(self):
        count, symbols = count_correlated_positions("BTCUSDT", [])
        self.assertEqual(count, 0)
        self.assertEqual(symbols, [])
    
    def test_count_correlated_positions_one(self):
        positions = [create_position("ETHUSDT")]
        count, symbols = count_correlated_positions("BTCUSDT", positions)
        self.assertEqual(count, 1)
        self.assertIn("ETHUSDT", symbols)
    
    def test_count_correlated_positions_excludes_self(self):
        positions = [create_position("BTCUSDT")]
        count, symbols = count_correlated_positions("BTCUSDT", positions)
        self.assertEqual(count, 0)


class TestDirectionHelpers(unittest.TestCase):
    """Tests for direction helper functions."""
    
    def test_count_positions_empty(self):
        long_count, short_count = count_positions_by_direction([])
        self.assertEqual(long_count, 0)
        self.assertEqual(short_count, 0)
    
    def test_count_positions_longs(self):
        positions = [
            create_position("BTCUSDT", "long"),
            create_position("ETHUSDT", "long"),
        ]
        long_count, short_count = count_positions_by_direction(positions)
        self.assertEqual(long_count, 2)
        self.assertEqual(short_count, 0)
    
    def test_count_positions_shorts(self):
        positions = [
            create_position("BTCUSDT", "short"),
            create_position("ETHUSDT", "short"),
        ]
        long_count, short_count = count_positions_by_direction(positions)
        self.assertEqual(long_count, 0)
        self.assertEqual(short_count, 2)
    
    def test_count_positions_mixed(self):
        positions = [
            create_position("BTCUSDT", "long"),
            create_position("ETHUSDT", "short"),
            create_position("SOLUSDT", "long"),
        ]
        long_count, short_count = count_positions_by_direction(positions)
        self.assertEqual(long_count, 2)
        self.assertEqual(short_count, 1)
    
    def test_calculate_net_exposure_balanced(self):
        self.assertEqual(calculate_net_exposure(2, 2), 0)
    
    def test_calculate_net_exposure_long_bias(self):
        self.assertEqual(calculate_net_exposure(5, 2), 3)
    
    def test_calculate_net_exposure_short_bias(self):
        self.assertEqual(calculate_net_exposure(2, 5), -3)


class TestSectorCounts(unittest.TestCase):
    """Tests for sector counting functions."""
    
    def test_count_empty(self):
        counts = count_positions_by_sector([])
        self.assertEqual(counts, {})
    
    def test_count_single(self):
        positions = [create_position("BTCUSDT")]
        counts = count_positions_by_sector(positions)
        self.assertEqual(counts.get("layer1", 0), 1)
    
    def test_count_multiple_same(self):
        positions = [
            create_position("BTCUSDT"),
            create_position("ETHUSDT"),
            create_position("SOLUSDT"),
        ]
        counts = count_positions_by_sector(positions)
        self.assertEqual(counts.get("layer1", 0), 3)
    
    def test_count_multiple_different(self):
        positions = [
            create_position("BTCUSDT"),
            create_position("UNIUSDT"),
            create_position("DOGEUSDT"),
        ]
        counts = count_positions_by_sector(positions)
        self.assertEqual(counts.get("layer1", 0), 1)
        self.assertEqual(counts.get("defi", 0), 1)
        self.assertEqual(counts.get("meme", 0), 1)
    
    def test_get_positions_in_sector(self):
        positions = [
            create_position("BTCUSDT"),
            create_position("UNIUSDT"),
            create_position("ETHUSDT"),
        ]
        layer1_positions = get_positions_in_sector(positions, "layer1")
        self.assertEqual(len(layer1_positions), 2)


class TestCorrelationFilter(unittest.TestCase):
    """Tests for CorrelationFilter."""
    
    def test_filter_disabled(self):
        f = CorrelationFilter({"enabled": False})
        decision = f.should_allow(create_test_signal(), create_test_context())
        self.assertEqual(decision.result, FilterResult.SKIP)
    
    def test_filter_no_positions(self):
        f = CorrelationFilter()
        decision = f.should_allow(create_test_signal(), create_test_context([]))
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_filter_uncorrelated_positions(self):
        f = CorrelationFilter({"max_correlated_positions": 2})
        ctx = create_test_context([create_position("AXSUSDT")])
        decision = f.should_allow(create_test_signal("BTCUSDT"), ctx)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_filter_one_correlated_under_limit(self):
        f = CorrelationFilter({"max_correlated_positions": 2})
        ctx = create_test_context([create_position("ETHUSDT")])
        decision = f.should_allow(create_test_signal("BTCUSDT"), ctx)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_filter_at_limit_blocks(self):
        f = CorrelationFilter({"max_correlated_positions": 1})
        ctx = create_test_context([create_position("ETHUSDT")])
        decision = f.should_allow(create_test_signal("BTCUSDT"), ctx)
        self.assertEqual(decision.result, FilterResult.BLOCK)
    
    def test_filter_over_limit_blocks(self):
        f = CorrelationFilter({"max_correlated_positions": 1})
        ctx = create_test_context([
            create_position("SHIBUSDT"),
            create_position("PEPEUSDT"),
        ])
        decision = f.should_allow(create_test_signal("DOGEUSDT"), ctx)
        self.assertEqual(decision.result, FilterResult.BLOCK)
    
    def test_filter_category_and_priority(self):
        f = CorrelationFilter()
        self.assertEqual(f.category, FilterCategory.PORTFOLIO)
        self.assertEqual(f.priority, FilterPriority.LOW)
    
    def test_filter_config_schema(self):
        f = CorrelationFilter()
        schema = f.get_config_schema()
        self.assertIn("enabled", schema)
        self.assertIn("max_correlated_positions", schema)
        self.assertIn("correlation_threshold", schema)


class TestDirectionFilter(unittest.TestCase):
    """Tests for DirectionFilter."""
    
    def test_filter_disabled(self):
        f = DirectionFilter({"enabled": False})
        decision = f.should_allow(create_test_signal(), create_test_context())
        self.assertEqual(decision.result, FilterResult.SKIP)
    
    def test_filter_no_positions(self):
        f = DirectionFilter()
        decision = f.should_allow(create_test_signal(), create_test_context([]))
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_filter_long_under_limit(self):
        f = DirectionFilter({"max_long_positions": 3})
        ctx = create_test_context([
            create_position("ETHUSDT", "long"),
            create_position("SOLUSDT", "long"),
        ])
        decision = f.should_allow(create_test_signal("BTCUSDT", "long"), ctx)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_filter_long_at_limit_blocks(self):
        f = DirectionFilter({"max_long_positions": 2})
        ctx = create_test_context([
            create_position("ETHUSDT", "long"),
            create_position("SOLUSDT", "long"),
        ])
        decision = f.should_allow(create_test_signal("BTCUSDT", "long"), ctx)
        self.assertEqual(decision.result, FilterResult.BLOCK)
    
    def test_filter_short_at_limit_blocks(self):
        f = DirectionFilter({"max_short_positions": 2})
        ctx = create_test_context([
            create_position("ETHUSDT", "short"),
            create_position("SOLUSDT", "short"),
        ])
        decision = f.should_allow(create_test_signal("BTCUSDT", "short"), ctx)
        self.assertEqual(decision.result, FilterResult.BLOCK)
    
    def test_filter_both_directions_allowed(self):
        f = DirectionFilter({"allow_both_directions": True})
        ctx = create_test_context([create_position("ETHUSDT", "short")])
        decision = f.should_allow(create_test_signal("BTCUSDT", "long"), ctx)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_filter_both_directions_blocked(self):
        f = DirectionFilter({"allow_both_directions": False})
        ctx = create_test_context([create_position("ETHUSDT", "short")])
        decision = f.should_allow(create_test_signal("BTCUSDT", "long"), ctx)
        self.assertEqual(decision.result, FilterResult.BLOCK)
    
    def test_filter_net_exposure_at_limit_blocks(self):
        f = DirectionFilter({"net_exposure_limit": 2})
        ctx = create_test_context([
            create_position("ETHUSDT", "long"),
            create_position("SOLUSDT", "long"),
        ])
        decision = f.should_allow(create_test_signal("BTCUSDT", "long"), ctx)
        self.assertEqual(decision.result, FilterResult.BLOCK)
    
    def test_filter_category_and_priority(self):
        f = DirectionFilter()
        self.assertEqual(f.category, FilterCategory.PORTFOLIO)
        self.assertEqual(f.priority, FilterPriority.LOW)


class TestSectorFilter(unittest.TestCase):
    """Tests for SectorFilter."""
    
    def test_filter_disabled(self):
        f = SectorFilter({"enabled": False})
        decision = f.should_allow(create_test_signal(), create_test_context())
        self.assertEqual(decision.result, FilterResult.SKIP)
    
    def test_filter_no_positions(self):
        f = SectorFilter()
        decision = f.should_allow(create_test_signal(), create_test_context([]))
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_filter_sector_under_limit(self):
        f = SectorFilter({"max_per_sector": 2})
        ctx = create_test_context([create_position("ETHUSDT")])
        decision = f.should_allow(create_test_signal("BTCUSDT"), ctx)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_filter_sector_at_limit_blocks(self):
        f = SectorFilter({"max_per_sector": 2})
        ctx = create_test_context([
            create_position("BTCUSDT"),
            create_position("ETHUSDT"),
        ])
        decision = f.should_allow(create_test_signal("SOLUSDT"), ctx)
        self.assertEqual(decision.result, FilterResult.BLOCK)
    
    def test_filter_different_sectors_pass(self):
        f = SectorFilter({"max_per_sector": 1})
        ctx = create_test_context([
            create_position("UNIUSDT"),
            create_position("DOGEUSDT"),
        ])
        decision = f.should_allow(create_test_signal("BTCUSDT"), ctx)
        self.assertEqual(decision.result, FilterResult.PASS)
    
    def test_filter_excluded_sector_blocks(self):
        f = SectorFilter({"max_per_sector": 10, "excluded_sectors": ["meme"]})
        decision = f.should_allow(create_test_signal("DOGEUSDT"), create_test_context([]))
        self.assertEqual(decision.result, FilterResult.BLOCK)
    
    def test_filter_category_and_priority(self):
        f = SectorFilter()
        self.assertEqual(f.category, FilterCategory.PORTFOLIO)
        self.assertEqual(f.priority, FilterPriority.LOW)


class TestPortfolioSummary(unittest.TestCase):
    """Tests for portfolio summary functions."""
    
    def test_empty_portfolio(self):
        summary = get_portfolio_summary([])
        self.assertEqual(summary["total_positions"], 0)
        self.assertEqual(summary["long_count"], 0)
        self.assertEqual(summary["short_count"], 0)
        self.assertEqual(summary["net_exposure"], 0)
    
    def test_mixed_portfolio(self):
        positions = [
            create_position("BTCUSDT", "long"),
            create_position("ETHUSDT", "long"),
            create_position("SOLUSDT", "short"),
            create_position("UNIUSDT", "long"),
        ]
        summary = get_portfolio_summary(positions)
        self.assertEqual(summary["total_positions"], 4)
        self.assertEqual(summary["long_count"], 3)
        self.assertEqual(summary["short_count"], 1)
        self.assertEqual(summary["net_exposure"], 2)


class TestConfigValidation(unittest.TestCase):
    """Tests for config validation functions."""
    
    def test_valid_config(self):
        config = {
            "correlation": {"max_correlated_positions": 2},
            "direction": {"max_long_positions": 5, "max_short_positions": 5},
            "sector": {"max_per_sector": 2}
        }
        is_valid, errors = validate_portfolio_config(config)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_invalid_correlation(self):
        config = {"correlation": {"max_correlated_positions": -1}}
        is_valid, errors = validate_portfolio_config(config)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_invalid_threshold(self):
        config = {"correlation": {"correlation_threshold": 1.5}}
        is_valid, errors = validate_portfolio_config(config)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestPortfolioProfiles(unittest.TestCase):
    """Tests for portfolio profile presets."""
    
    def test_conservative_profile(self):
        profile = create_portfolio_profile("conservative")
        self.assertEqual(profile["correlation"]["max_correlated_positions"], 1)
        self.assertEqual(profile["direction"]["max_long_positions"], 3)
        self.assertEqual(profile["sector"]["max_per_sector"], 1)
    
    def test_balanced_profile(self):
        profile = create_portfolio_profile("balanced")
        self.assertEqual(profile["correlation"]["max_correlated_positions"], 2)
        self.assertEqual(profile["direction"]["max_long_positions"], 5)
        self.assertEqual(profile["sector"]["max_per_sector"], 2)
    
    def test_aggressive_profile(self):
        profile = create_portfolio_profile("aggressive")
        self.assertEqual(profile["correlation"]["max_correlated_positions"], 3)
        self.assertEqual(profile["direction"]["max_long_positions"], 8)
        self.assertEqual(profile["sector"]["max_per_sector"], 3)
    
    def test_unknown_profile(self):
        profile = create_portfolio_profile("unknown_profile")
        balanced = create_portfolio_profile("balanced")
        self.assertEqual(profile, balanced)


class TestPortfolioFilterChain(unittest.TestCase):
    """Tests for portfolio filter chain creation."""
    
    def test_empty_chain(self):
        chain = create_portfolio_filter_chain()
        self.assertEqual(len(chain), 0)
    
    def test_chain_with_correlation(self):
        chain = create_portfolio_filter_chain(
            correlation_config={"max_correlated_positions": 2}
        )
        self.assertEqual(len(chain), 1)
        self.assertIsInstance(chain[0], CorrelationFilter)
    
    def test_chain_with_all(self):
        chain = create_portfolio_filter_chain(
            correlation_config={"max_correlated_positions": 2},
            direction_config={"max_long_positions": 5},
            sector_config={"max_per_sector": 2}
        )
        self.assertEqual(len(chain), 3)


class TestPortfolioFiltersIntegration(unittest.TestCase):
    """Integration tests for portfolio filters."""
    
    def test_all_filters_pass(self):
        correlation_filter = CorrelationFilter({"max_correlated_positions": 3})
        direction_filter = DirectionFilter({"max_long_positions": 5})
        sector_filter = SectorFilter({"max_per_sector": 3})
        
        signal = create_test_signal("BTCUSDT", "long")
        context = create_test_context([create_position("ETHUSDT", "long")])
        
        self.assertEqual(correlation_filter.should_allow(signal, context).result, FilterResult.PASS)
        self.assertEqual(direction_filter.should_allow(signal, context).result, FilterResult.PASS)
        self.assertEqual(sector_filter.should_allow(signal, context).result, FilterResult.PASS)
    
    def test_correlation_blocks_first(self):
        correlation_filter = CorrelationFilter({"max_correlated_positions": 0})
        signal = create_test_signal("BTCUSDT", "long")
        context = create_test_context([create_position("ETHUSDT", "long")])
        
        decision = correlation_filter.should_allow(signal, context)
        self.assertEqual(decision.result, FilterResult.BLOCK)


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestSectorHelpers))
    suite.addTests(loader.loadTestsFromTestCase(TestCorrelationHelpers))
    suite.addTests(loader.loadTestsFromTestCase(TestDirectionHelpers))
    suite.addTests(loader.loadTestsFromTestCase(TestSectorCounts))
    suite.addTests(loader.loadTestsFromTestCase(TestCorrelationFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestDirectionFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestSectorFilter))
    suite.addTests(loader.loadTestsFromTestCase(TestPortfolioSummary))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestPortfolioProfiles))
    suite.addTests(loader.loadTestsFromTestCase(TestPortfolioFilterChain))
    suite.addTests(loader.loadTestsFromTestCase(TestPortfolioFiltersIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success: {result.wasSuccessful()}")
    print("="*70)
    
    exit(0 if result.wasSuccessful() else 1)
