"""
KOMAS v4.0 — Trend Filters Unit Tests
======================================

Comprehensive tests for BTCTrendFilter, MultiTFFilter, RegimeFilter.

Chat #40: Filters Trend
Author: KOMAS Team
Version: 4.0
"""

import unittest
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

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
from filters.trend_filters import (
    BTCTrendFilter,
    MultiTFFilter,
    RegimeFilter,
    # Helper functions
    calculate_ma,
    calculate_ema,
    calculate_supertrend,
    get_trend_from_price_and_ma,
    determine_btc_trend,
    calculate_adx,
    calculate_atr_ratio,
    calculate_bb_width,
    detect_market_regime,
    is_higher_timeframe,
    get_tf_trend,
    count_aligned_timeframes,
    get_trend_state,
    get_trend_filter_summary,
    create_trend_filter_chain,
    validate_trend_config,
    # Constants
    BTC_TREND_METHODS,
    VALID_TIMEFRAMES,
    TIMEFRAME_HIERARCHY,
    REGIME_METHODS,
    MARKET_REGIMES,
    DEFAULT_BTC_TREND_PERIOD,
    DEFAULT_ADX_THRESHOLD,
)


def create_test_signal(
    symbol: str = "ETHUSDT",
    direction: str = "long",
    entry_price: float = 2500.0
) -> Signal:
    """Create a test signal."""
    return Signal(
        symbol=symbol,
        direction=direction,
        entry_price=entry_price,
        timestamp=datetime.now(timezone.utc)
    )


def create_test_context(
    current_price: float = 2500.0,
    btc_trend: Optional[str] = None,
    btc_price: Optional[float] = None,
    atr: Optional[float] = None,
    htf_data: Optional[Dict[str, Any]] = None
) -> SignalContext:
    """Create a test context with optional market data."""
    return SignalContext(
        current_time=datetime.now(timezone.utc),
        current_price=current_price,
        btc_trend=btc_trend,
        btc_price=btc_price,
        atr=atr,
        htf_data=htf_data or {}
    )


def create_price_series(
    start_price: float,
    count: int,
    trend: str = "up",
    volatility: float = 0.02
) -> List[float]:
    """Create a synthetic price series."""
    import random
    prices = [start_price]
    
    for i in range(count - 1):
        if trend == "up":
            change = random.uniform(0, volatility * 2) - volatility * 0.3
        elif trend == "down":
            change = random.uniform(-volatility * 2, 0) + volatility * 0.3
        else:
            change = random.uniform(-volatility, volatility)
        
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    return prices


# =============================================================================
# HELPER FUNCTION TESTS
# =============================================================================

class TestMACalculations(unittest.TestCase):
    """Tests for moving average calculations."""
    
    def test_calculate_ma_basic(self):
        """Test basic MA calculation."""
        prices = [100, 102, 104, 106, 108]
        ma = calculate_ma(prices, 5)
        self.assertEqual(ma, 104.0)
    
    def test_calculate_ma_partial(self):
        """Test MA with partial data."""
        prices = [100, 102, 104]
        ma = calculate_ma(prices, 5)
        self.assertIsNone(ma)  # Not enough data
    
    def test_calculate_ma_longer_series(self):
        """Test MA with longer series uses last N values."""
        prices = [80, 90, 100, 102, 104, 106, 108]
        ma = calculate_ma(prices, 5)
        self.assertEqual(ma, 104.0)  # Uses last 5
    
    def test_calculate_ema_basic(self):
        """Test basic EMA calculation."""
        prices = [100, 102, 104, 106, 108, 110]
        ema = calculate_ema(prices, 5)
        self.assertIsNotNone(ema)
        self.assertTrue(ema > 100)
    
    def test_calculate_ema_insufficient_data(self):
        """Test EMA with insufficient data."""
        prices = [100, 102]
        ema = calculate_ema(prices, 5)
        self.assertIsNone(ema)


class TestTrendDetection(unittest.TestCase):
    """Tests for trend detection functions."""
    
    def test_get_trend_from_price_and_ma_up(self):
        """Test uptrend detection."""
        trend = get_trend_from_price_and_ma(105, 100)
        self.assertEqual(trend, "up")
    
    def test_get_trend_from_price_and_ma_down(self):
        """Test downtrend detection."""
        trend = get_trend_from_price_and_ma(95, 100)
        self.assertEqual(trend, "down")
    
    def test_get_trend_from_price_and_ma_neutral(self):
        """Test neutral trend detection."""
        trend = get_trend_from_price_and_ma(100.3, 100)
        self.assertEqual(trend, "neutral")
    
    def test_get_trend_from_price_and_ma_zero_ma(self):
        """Test with zero MA."""
        trend = get_trend_from_price_and_ma(100, 0)
        self.assertEqual(trend, "neutral")
    
    def test_determine_btc_trend_ma_up(self):
        """Test BTC trend determination using MA - uptrend."""
        btc_data = {
            "price": 50000,
            "prices": [45000, 46000, 47000, 48000, 49000] * 4  # 20 prices
        }
        trend = determine_btc_trend(btc_data, "ma", 20)
        self.assertEqual(trend, "up")
    
    def test_determine_btc_trend_ma_down(self):
        """Test BTC trend determination using MA - downtrend."""
        btc_data = {
            "price": 45000,
            "prices": [50000, 49000, 48000, 47000, 46000] * 4  # 20 prices
        }
        trend = determine_btc_trend(btc_data, "ma", 20)
        self.assertEqual(trend, "down")
    
    def test_determine_btc_trend_ema(self):
        """Test BTC trend determination using EMA."""
        btc_data = {
            "price": 50000,
            "prices": [45000 + i * 200 for i in range(20)]
        }
        trend = determine_btc_trend(btc_data, "ema", 20)
        self.assertEqual(trend, "up")
    
    def test_determine_btc_trend_no_data(self):
        """Test BTC trend with no data."""
        btc_data = {}
        trend = determine_btc_trend(btc_data, "ma", 20)
        self.assertEqual(trend, "neutral")


class TestRegimeDetection(unittest.TestCase):
    """Tests for market regime detection."""
    
    def test_calculate_atr_ratio(self):
        """Test ATR ratio calculation."""
        ratio = calculate_atr_ratio(150, 100)
        self.assertEqual(ratio, 1.5)
    
    def test_calculate_atr_ratio_zero_avg(self):
        """Test ATR ratio with zero average."""
        ratio = calculate_atr_ratio(150, 0)
        self.assertEqual(ratio, 1.0)
    
    def test_calculate_bb_width_basic(self):
        """Test BB width calculation."""
        # Create stable prices for predictable std dev
        prices = [100, 101, 99, 100, 101, 99, 100, 101, 99, 100] * 2
        width = calculate_bb_width(prices, 20)
        self.assertIsNotNone(width)
        self.assertTrue(width > 0)
    
    def test_calculate_bb_width_insufficient_data(self):
        """Test BB width with insufficient data."""
        prices = [100, 101, 102]
        width = calculate_bb_width(prices, 20)
        self.assertIsNone(width)
    
    def test_detect_market_regime_atr_trending(self):
        """Test regime detection - trending via ATR."""
        market_data = {"atr": 200, "avg_atr": 100}
        regime = detect_market_regime(market_data, "atr_ratio", atr_ratio_threshold=1.5)
        self.assertEqual(regime, "trending")
    
    def test_detect_market_regime_atr_ranging(self):
        """Test regime detection - ranging via ATR."""
        market_data = {"atr": 100, "avg_atr": 100}
        regime = detect_market_regime(market_data, "atr_ratio", atr_ratio_threshold=1.5)
        self.assertEqual(regime, "ranging")


class TestMultiTFHelpers(unittest.TestCase):
    """Tests for multi-timeframe helpers."""
    
    def test_is_higher_timeframe(self):
        """Test timeframe comparison."""
        self.assertTrue(is_higher_timeframe("4h", "1h"))
        self.assertTrue(is_higher_timeframe("1d", "4h"))
        self.assertFalse(is_higher_timeframe("1h", "4h"))
        self.assertFalse(is_higher_timeframe("1h", "1h"))
    
    def test_get_tf_trend_aligned_long(self):
        """Test TF trend alignment for long."""
        tf_data = {"trend": "up"}
        self.assertTrue(get_tf_trend(tf_data, "long"))
    
    def test_get_tf_trend_aligned_short(self):
        """Test TF trend alignment for short."""
        tf_data = {"trend": "down"}
        self.assertTrue(get_tf_trend(tf_data, "short"))
    
    def test_get_tf_trend_not_aligned(self):
        """Test TF trend not aligned."""
        tf_data = {"trend": "up"}
        self.assertFalse(get_tf_trend(tf_data, "short"))
    
    def test_count_aligned_timeframes(self):
        """Test counting aligned timeframes."""
        htf_data = {
            "4h": {"trend": "up"},
            "1d": {"trend": "up"},
            "1w": {"trend": "down"}
        }
        aligned, total = count_aligned_timeframes(htf_data, "long", ["4h", "1d", "1w"])
        self.assertEqual(aligned, 2)
        self.assertEqual(total, 3)


class TestValidation(unittest.TestCase):
    """Tests for configuration validation."""
    
    def test_validate_trend_config_valid(self):
        """Test valid config validation."""
        config = {
            "btc_trend_method": "ma",
            "btc_trend_period": 20,
            "required_timeframes": ["4h", "1d"],
            "regime_detection_method": "adx",
            "adx_threshold": 25,
            "allowed_regimes": ["trending"]
        }
        is_valid, errors = validate_trend_config(config)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])
    
    def test_validate_trend_config_invalid_method(self):
        """Test invalid method validation."""
        config = {"btc_trend_method": "invalid"}
        is_valid, errors = validate_trend_config(config)
        self.assertFalse(is_valid)
        self.assertTrue(len(errors) > 0)
    
    def test_validate_trend_config_invalid_timeframe(self):
        """Test invalid timeframe validation."""
        config = {"required_timeframes": ["invalid_tf"]}
        is_valid, errors = validate_trend_config(config)
        self.assertFalse(is_valid)


# =============================================================================
# BTC TREND FILTER TESTS
# =============================================================================

class TestBTCTrendFilterBasics(unittest.TestCase):
    """Basic tests for BTCTrendFilter."""
    
    def test_filter_attributes(self):
        """Test filter class attributes."""
        filter = BTCTrendFilter()
        self.assertEqual(filter.name, "btc_trend_filter")
        self.assertEqual(filter.category, FilterCategory.TREND)
        self.assertEqual(filter.priority, FilterPriority.MEDIUM)
    
    def test_filter_disabled(self):
        """Test disabled filter."""
        filter = BTCTrendFilter({"enabled": False})
        signal = create_test_signal()
        context = create_test_context()
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.SKIP)
    
    def test_filter_follow_disabled(self):
        """Test filter with follow_btc_trend disabled."""
        filter = BTCTrendFilter({"follow_btc_trend": False})
        signal = create_test_signal()
        context = create_test_context()
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_btc_signal_skip(self):
        """Test that BTC signals skip the filter."""
        filter = BTCTrendFilter()
        signal = create_test_signal(symbol="BTCUSDT")
        context = create_test_context()
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
        self.assertTrue(result.details.get("is_btc", False))


class TestBTCTrendFilterAlignment(unittest.TestCase):
    """Tests for BTC trend alignment logic."""
    
    def test_long_with_btc_uptrend(self):
        """Test long signal with BTC uptrend."""
        filter = BTCTrendFilter()
        signal = create_test_signal(direction="long")
        context = create_test_context(btc_trend="up")
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_short_with_btc_downtrend(self):
        """Test short signal with BTC downtrend."""
        filter = BTCTrendFilter()
        signal = create_test_signal(direction="short")
        context = create_test_context(btc_trend="down")
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_long_with_btc_downtrend_blocked(self):
        """Test long signal blocked when BTC down."""
        filter = BTCTrendFilter()
        signal = create_test_signal(direction="long")
        context = create_test_context(btc_trend="down")
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.BLOCK)
    
    def test_short_with_btc_uptrend_blocked(self):
        """Test short signal blocked when BTC up."""
        filter = BTCTrendFilter()
        signal = create_test_signal(direction="short")
        context = create_test_context(btc_trend="up")
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.BLOCK)


class TestBTCTrendFilterNeutral(unittest.TestCase):
    """Tests for BTC neutral trend handling."""
    
    def test_neutral_allowed(self):
        """Test neutral trend allows trades by default."""
        filter = BTCTrendFilter({"allow_neutral": True})
        signal = create_test_signal()
        context = create_test_context(btc_trend="neutral")
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_neutral_blocked(self):
        """Test neutral trend blocks trades when configured."""
        filter = BTCTrendFilter({"allow_neutral": False})
        signal = create_test_signal()
        context = create_test_context(btc_trend="neutral")
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.BLOCK)


class TestBTCTrendFilterStrictMode(unittest.TestCase):
    """Tests for strict mode."""
    
    def test_strict_mode_aligned(self):
        """Test strict mode with aligned direction."""
        filter = BTCTrendFilter({"strict_mode": True})
        signal = create_test_signal(direction="long")
        context = create_test_context(btc_trend="up")
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_strict_mode_not_aligned(self):
        """Test strict mode with non-aligned direction."""
        filter = BTCTrendFilter({"strict_mode": True})
        signal = create_test_signal(direction="long")
        context = create_test_context(btc_trend="down")
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.BLOCK)


class TestBTCTrendFilterSchema(unittest.TestCase):
    """Tests for config schema."""
    
    def test_config_schema(self):
        """Test config schema completeness."""
        filter = BTCTrendFilter()
        schema = filter.get_config_schema()
        
        self.assertIn("enabled", schema)
        self.assertIn("follow_btc_trend", schema)
        self.assertIn("btc_trend_method", schema)
        self.assertIn("btc_trend_period", schema)
        self.assertIn("allow_neutral", schema)
        self.assertIn("strict_mode", schema)
        
        # Check method options
        self.assertEqual(
            schema["btc_trend_method"]["options"],
            BTC_TREND_METHODS
        )


# =============================================================================
# MULTI-TF FILTER TESTS
# =============================================================================

class TestMultiTFFilterBasics(unittest.TestCase):
    """Basic tests for MultiTFFilter."""
    
    def test_filter_attributes(self):
        """Test filter class attributes."""
        filter = MultiTFFilter()
        self.assertEqual(filter.name, "multi_tf_filter")
        self.assertEqual(filter.category, FilterCategory.TREND)
    
    def test_filter_disabled(self):
        """Test disabled filter."""
        filter = MultiTFFilter({"enabled": False})
        signal = create_test_signal()
        context = create_test_context()
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.SKIP)
    
    def test_no_required_timeframes(self):
        """Test with no required timeframes - defaults to standard TFs."""
        filter = MultiTFFilter({"required_timeframes": []})
        signal = create_test_signal()
        context = create_test_context()
        
        result = filter.should_allow(signal, context)
        # Empty list gets replaced with DEFAULT_REQUIRED_TIMEFRAMES in __init__
        # So filter will SKIP if no HTF data available
        self.assertEqual(result.result, FilterResult.SKIP)


class TestMultiTFFilterAlignment(unittest.TestCase):
    """Tests for multi-TF alignment logic."""
    
    def test_all_aligned(self):
        """Test all timeframes aligned."""
        filter = MultiTFFilter({
            "required_timeframes": ["4h", "1d"],
            "require_all_aligned": True
        })
        signal = create_test_signal(direction="long")
        context = create_test_context(
            htf_data={
                "4h": {"trend": "up"},
                "1d": {"trend": "up"}
            }
        )
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
        self.assertEqual(result.details["aligned_count"], 2)
    
    def test_partial_alignment_blocked(self):
        """Test partial alignment when all required."""
        filter = MultiTFFilter({
            "required_timeframes": ["4h", "1d"],
            "require_all_aligned": True
        })
        signal = create_test_signal(direction="long")
        context = create_test_context(
            htf_data={
                "4h": {"trend": "up"},
                "1d": {"trend": "down"}
            }
        )
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.BLOCK)
    
    def test_partial_alignment_allowed(self):
        """Test partial alignment with min count."""
        filter = MultiTFFilter({
            "required_timeframes": ["4h", "1d"],
            "require_all_aligned": False,
            "min_aligned_count": 1
        })
        signal = create_test_signal(direction="long")
        context = create_test_context(
            htf_data={
                "4h": {"trend": "up"},
                "1d": {"trend": "down"}
            }
        )
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)


class TestMultiTFFilterNoData(unittest.TestCase):
    """Tests for missing data handling."""
    
    def test_no_htf_data_skip(self):
        """Test skip when no HTF data and skip_if_no_data=True."""
        filter = MultiTFFilter({"skip_if_no_data": True})
        signal = create_test_signal()
        context = create_test_context(htf_data={})
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.SKIP)
    
    def test_no_htf_data_block(self):
        """Test block when no HTF data and skip_if_no_data=False."""
        filter = MultiTFFilter({"skip_if_no_data": False})
        signal = create_test_signal()
        context = create_test_context(htf_data={})
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.BLOCK)


class TestMultiTFFilterSchema(unittest.TestCase):
    """Tests for config schema."""
    
    def test_config_schema(self):
        """Test config schema completeness."""
        filter = MultiTFFilter()
        schema = filter.get_config_schema()
        
        self.assertIn("enabled", schema)
        self.assertIn("required_timeframes", schema)
        self.assertIn("require_all_aligned", schema)
        self.assertIn("min_aligned_count", schema)
        self.assertIn("skip_if_no_data", schema)


# =============================================================================
# REGIME FILTER TESTS
# =============================================================================

class TestRegimeFilterBasics(unittest.TestCase):
    """Basic tests for RegimeFilter."""
    
    def test_filter_attributes(self):
        """Test filter class attributes."""
        filter = RegimeFilter()
        self.assertEqual(filter.name, "regime_filter")
        self.assertEqual(filter.category, FilterCategory.TREND)
    
    def test_filter_disabled(self):
        """Test disabled filter."""
        filter = RegimeFilter({"enabled": False})
        signal = create_test_signal()
        context = create_test_context()
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.SKIP)
    
    def test_default_config(self):
        """Test default configuration."""
        filter = RegimeFilter()
        self.assertEqual(filter.allowed_regimes, ["trending"])
        self.assertEqual(filter.regime_detection_method, "adx")


class TestRegimeFilterATRMethod(unittest.TestCase):
    """Tests for ATR ratio regime detection."""
    
    def test_trending_via_atr(self):
        """Test trending detection via ATR ratio."""
        filter = RegimeFilter({
            "regime_detection_method": "atr_ratio",
            "atr_ratio_threshold": 1.5,
            "allowed_regimes": ["trending"]
        })
        signal = create_test_signal()
        context = create_test_context(
            atr=200,
            htf_data={"avg_atr": 100}
        )
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)
    
    def test_ranging_via_atr_blocked(self):
        """Test ranging blocked via ATR ratio."""
        filter = RegimeFilter({
            "regime_detection_method": "atr_ratio",
            "atr_ratio_threshold": 1.5,
            "allowed_regimes": ["trending"]
        })
        signal = create_test_signal()
        context = create_test_context(
            atr=100,
            htf_data={"avg_atr": 100}
        )
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.BLOCK)
    
    def test_ranging_allowed(self):
        """Test ranging allowed when in allowed_regimes."""
        filter = RegimeFilter({
            "regime_detection_method": "atr_ratio",
            "atr_ratio_threshold": 1.5,
            "allowed_regimes": ["ranging"]
        })
        signal = create_test_signal()
        context = create_test_context(
            atr=100,
            htf_data={"avg_atr": 100}
        )
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.PASS)


class TestRegimeFilterNoData(unittest.TestCase):
    """Tests for missing data handling."""
    
    def test_no_data_skip(self):
        """Test skip when no data and skip_if_no_data=True."""
        filter = RegimeFilter({"skip_if_no_data": True})
        signal = create_test_signal()
        context = create_test_context(htf_data={})
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.SKIP)
    
    def test_no_data_block(self):
        """Test block when no data and skip_if_no_data=False."""
        filter = RegimeFilter({"skip_if_no_data": False})
        signal = create_test_signal()
        context = create_test_context(htf_data={})
        
        result = filter.should_allow(signal, context)
        self.assertEqual(result.result, FilterResult.BLOCK)


class TestRegimeFilterSchema(unittest.TestCase):
    """Tests for config schema."""
    
    def test_config_schema(self):
        """Test config schema completeness."""
        filter = RegimeFilter()
        schema = filter.get_config_schema()
        
        self.assertIn("enabled", schema)
        self.assertIn("allowed_regimes", schema)
        self.assertIn("regime_detection_method", schema)
        self.assertIn("adx_threshold", schema)
        self.assertIn("atr_ratio_threshold", schema)
        self.assertIn("bb_width_threshold", schema)
        self.assertIn("skip_if_no_data", schema)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestTrendFilterChain(unittest.TestCase):
    """Tests for creating filter chains."""
    
    def test_create_chain(self):
        """Test creating a chain of trend filters."""
        chain = create_trend_filter_chain(
            btc_filter_config={"enabled": True},
            multi_tf_config={"enabled": True},
            regime_config={"enabled": True}
        )
        
        self.assertEqual(len(chain), 3)
        self.assertIsInstance(chain[0], BTCTrendFilter)
        self.assertIsInstance(chain[1], MultiTFFilter)
        self.assertIsInstance(chain[2], RegimeFilter)
    
    def test_create_partial_chain(self):
        """Test creating a partial chain."""
        chain = create_trend_filter_chain(
            btc_filter_config={"enabled": True},
            multi_tf_config=None,  # Skip this one
            regime_config={"enabled": True}
        )
        
        self.assertEqual(len(chain), 2)


class TestTrendFilterSummary(unittest.TestCase):
    """Tests for filter summary."""
    
    def test_get_summary(self):
        """Test getting filter summary."""
        filters = [
            BTCTrendFilter({"enabled": True}),
            MultiTFFilter({"enabled": False}),
            RegimeFilter({"enabled": True})
        ]
        
        summary = get_trend_filter_summary(filters)
        
        self.assertEqual(summary["total_filters"], 3)
        self.assertEqual(summary["active_count"], 2)
        self.assertIn("btc_trend_filter", summary["enabled_filters"])
        self.assertIn("multi_tf_filter", summary["disabled_filters"])


class TestTrendState(unittest.TestCase):
    """Tests for trend state."""
    
    def test_get_trend_state(self):
        """Test getting trend state."""
        state = get_trend_state(
            btc_trend="up",
            tf_alignments={"4h": True, "1d": True, "1w": False},
            market_regime="trending"
        )
        
        self.assertEqual(state["btc_trend"], "up")
        self.assertEqual(state["aligned_count"], 2)
        self.assertEqual(state["total_count"], 3)
        self.assertAlmostEqual(state["alignment_percent"], 66.67, places=1)
        self.assertEqual(state["market_regime"], "trending")


# =============================================================================
# CONSTANTS TESTS
# =============================================================================

class TestConstants(unittest.TestCase):
    """Tests for module constants."""
    
    def test_btc_trend_methods(self):
        """Test BTC trend methods list."""
        self.assertIn("ma", BTC_TREND_METHODS)
        self.assertIn("ema", BTC_TREND_METHODS)
        self.assertIn("supertrend", BTC_TREND_METHODS)
    
    def test_valid_timeframes(self):
        """Test valid timeframes list."""
        expected = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", 
                   "6h", "8h", "12h", "1d", "3d", "1w"]
        self.assertEqual(VALID_TIMEFRAMES, expected)
    
    def test_timeframe_hierarchy(self):
        """Test timeframe hierarchy ordering."""
        self.assertTrue(TIMEFRAME_HIERARCHY["1d"] > TIMEFRAME_HIERARCHY["4h"])
        self.assertTrue(TIMEFRAME_HIERARCHY["4h"] > TIMEFRAME_HIERARCHY["1h"])
        self.assertTrue(TIMEFRAME_HIERARCHY["1w"] > TIMEFRAME_HIERARCHY["1d"])
    
    def test_regime_methods(self):
        """Test regime detection methods."""
        self.assertIn("adx", REGIME_METHODS)
        self.assertIn("atr_ratio", REGIME_METHODS)
        self.assertIn("bb_width", REGIME_METHODS)
    
    def test_market_regimes(self):
        """Test market regime types."""
        self.assertIn("trending", MARKET_REGIMES)
        self.assertIn("ranging", MARKET_REGIMES)


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        # Helper function tests
        TestMACalculations,
        TestTrendDetection,
        TestRegimeDetection,
        TestMultiTFHelpers,
        TestValidation,
        # BTC Trend Filter tests
        TestBTCTrendFilterBasics,
        TestBTCTrendFilterAlignment,
        TestBTCTrendFilterNeutral,
        TestBTCTrendFilterStrictMode,
        TestBTCTrendFilterSchema,
        # Multi-TF Filter tests
        TestMultiTFFilterBasics,
        TestMultiTFFilterAlignment,
        TestMultiTFFilterNoData,
        TestMultiTFFilterSchema,
        # Regime Filter tests
        TestRegimeFilterBasics,
        TestRegimeFilterATRMethod,
        TestRegimeFilterNoData,
        TestRegimeFilterSchema,
        # Integration tests
        TestTrendFilterChain,
        TestTrendFilterSummary,
        TestTrendState,
        # Constants tests
        TestConstants,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 70)
    print(f"Total tests: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    # Exit code
    sys.exit(0 if result.wasSuccessful() else 1)
