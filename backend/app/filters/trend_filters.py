"""
KOMAS v4.0 — Trend Filters
===========================

Trend-based filters for controlling when trades can be executed.

Filters:
- BTCTrendFilter: Control trading based on BTC market trend direction
- MultiTFFilter: Require alignment across multiple timeframes
- RegimeFilter: Detect and filter by market regime (trending/ranging)

Chat #40: Filters Trend
Author: KOMAS Team
Version: 4.0
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import math

from .base import (
    BaseFilter,
    Signal,
    SignalContext,
    FilterDecision,
    FilterResult,
    FilterCategory,
    FilterPriority,
    create_pass_decision,
    create_block_decision,
    create_skip_decision
)
from .registry import register_filter

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# BTC Trend settings
DEFAULT_BTC_TREND_PERIOD = 20
DEFAULT_BTC_TREND_METHOD = "ma"
BTC_TREND_METHODS = ["ma", "ema", "supertrend"]

# Multi-TF settings
DEFAULT_REQUIRED_TIMEFRAMES = ["4h", "1d"]
VALID_TIMEFRAMES = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w"]
TIMEFRAME_HIERARCHY = {
    "1m": 0, "5m": 1, "15m": 2, "30m": 3,
    "1h": 4, "2h": 5, "4h": 6, "6h": 7,
    "8h": 8, "12h": 9, "1d": 10, "3d": 11, "1w": 12
}

# Regime detection settings
DEFAULT_REGIME_METHOD = "adx"
DEFAULT_ADX_THRESHOLD = 25
DEFAULT_ATR_RATIO_THRESHOLD = 1.5
DEFAULT_BB_WIDTH_THRESHOLD = 0.1
REGIME_METHODS = ["adx", "atr_ratio", "bb_width"]
MARKET_REGIMES = ["trending", "ranging"]


# =============================================================================
# HELPER FUNCTIONS — TREND DETECTION
# =============================================================================

def calculate_ma(prices: List[float], period: int) -> Optional[float]:
    """
    Calculate Simple Moving Average.
    
    Args:
        prices: List of prices (newest last)
        period: MA period
        
    Returns:
        MA value or None if insufficient data
    """
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period


def calculate_ema(prices: List[float], period: int) -> Optional[float]:
    """
    Calculate Exponential Moving Average.
    
    Args:
        prices: List of prices (newest last)
        period: EMA period
        
    Returns:
        EMA value or None if insufficient data
    """
    if len(prices) < period:
        return None
    
    multiplier = 2.0 / (period + 1)
    ema = prices[0]
    
    for price in prices[1:]:
        ema = (price - ema) * multiplier + ema
    
    return ema


def calculate_supertrend(
    high: List[float],
    low: List[float],
    close: List[float],
    period: int = 10,
    multiplier: float = 3.0
) -> Optional[Tuple[str, float]]:
    """
    Calculate SuperTrend indicator direction.
    
    Args:
        high: List of high prices
        low: List of low prices
        close: List of close prices
        period: ATR period
        multiplier: ATR multiplier
        
    Returns:
        Tuple of (trend_direction, supertrend_value) or None
    """
    if len(close) < period + 1:
        return None
    
    # Calculate ATR (simplified)
    tr_list = []
    for i in range(1, len(close)):
        tr = max(
            high[i] - low[i],
            abs(high[i] - close[i-1]),
            abs(low[i] - close[i-1])
        )
        tr_list.append(tr)
    
    if len(tr_list) < period:
        return None
    
    atr = sum(tr_list[-period:]) / period
    
    # Calculate bands
    hl2 = (high[-1] + low[-1]) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    # Determine trend based on close vs bands
    current_close = close[-1]
    prev_close = close[-2]
    
    if current_close > upper_band or (prev_close <= lower_band and current_close > lower_band):
        return ("up", lower_band)
    elif current_close < lower_band or (prev_close >= upper_band and current_close < upper_band):
        return ("down", upper_band)
    else:
        # Maintain previous trend (simplified: check price position)
        mid = (upper_band + lower_band) / 2
        if current_close > mid:
            return ("up", lower_band)
        else:
            return ("down", upper_band)


def get_trend_from_price_and_ma(price: float, ma: float) -> str:
    """
    Determine trend direction from price vs MA.
    
    Args:
        price: Current price
        ma: Moving average value
        
    Returns:
        'up', 'down', or 'neutral'
    """
    if ma <= 0:
        return "neutral"
    
    # Calculate percentage difference
    diff_pct = ((price - ma) / ma) * 100
    
    # Use 0.5% threshold for neutral zone
    if diff_pct > 0.5:
        return "up"
    elif diff_pct < -0.5:
        return "down"
    else:
        return "neutral"


def determine_btc_trend(
    btc_data: Dict[str, Any],
    method: str = "ma",
    period: int = 20
) -> str:
    """
    Determine BTC trend using specified method.
    
    Args:
        btc_data: Dict containing BTC price data
            - 'price': current price
            - 'prices': list of recent prices
            - 'high': list of highs (for supertrend)
            - 'low': list of lows (for supertrend)
        method: 'ma', 'ema', or 'supertrend'
        period: Period for calculation
        
    Returns:
        'up', 'down', or 'neutral'
    """
    price = btc_data.get("price", 0)
    prices = btc_data.get("prices", [])
    
    if price <= 0 or not prices:
        return "neutral"
    
    if method == "ma":
        ma = calculate_ma(prices, period)
        if ma is None:
            return "neutral"
        return get_trend_from_price_and_ma(price, ma)
    
    elif method == "ema":
        ema = calculate_ema(prices, period)
        if ema is None:
            return "neutral"
        return get_trend_from_price_and_ma(price, ema)
    
    elif method == "supertrend":
        high = btc_data.get("high", [])
        low = btc_data.get("low", [])
        close = prices
        
        result = calculate_supertrend(high, low, close, period, 3.0)
        if result is None:
            return "neutral"
        return result[0]
    
    return "neutral"


# =============================================================================
# HELPER FUNCTIONS — REGIME DETECTION
# =============================================================================

def calculate_adx(
    high: List[float],
    low: List[float],
    close: List[float],
    period: int = 14
) -> Optional[float]:
    """
    Calculate Average Directional Index (ADX).
    
    ADX measures trend strength:
    - ADX < 20: Weak trend (ranging)
    - ADX 20-40: Moderate trend
    - ADX > 40: Strong trend
    
    Args:
        high: List of high prices
        low: List of low prices
        close: List of close prices
        period: ADX period
        
    Returns:
        ADX value or None
    """
    if len(close) < period * 2:
        return None
    
    # Calculate +DM and -DM
    plus_dm = []
    minus_dm = []
    tr_list = []
    
    for i in range(1, len(close)):
        high_diff = high[i] - high[i-1]
        low_diff = low[i-1] - low[i]
        
        if high_diff > low_diff and high_diff > 0:
            plus_dm.append(high_diff)
        else:
            plus_dm.append(0)
        
        if low_diff > high_diff and low_diff > 0:
            minus_dm.append(low_diff)
        else:
            minus_dm.append(0)
        
        # True Range
        tr = max(
            high[i] - low[i],
            abs(high[i] - close[i-1]),
            abs(low[i] - close[i-1])
        )
        tr_list.append(tr)
    
    if len(tr_list) < period:
        return None
    
    # Smooth with EMA
    def smooth_ema(data: List[float], period: int) -> List[float]:
        result = []
        if not data:
            return result
        ema = data[0]
        result.append(ema)
        multiplier = 2.0 / (period + 1)
        for val in data[1:]:
            ema = (val - ema) * multiplier + ema
            result.append(ema)
        return result
    
    smooth_tr = smooth_ema(tr_list, period)
    smooth_plus_dm = smooth_ema(plus_dm, period)
    smooth_minus_dm = smooth_ema(minus_dm, period)
    
    # Calculate +DI and -DI
    dx_list = []
    for i in range(len(smooth_tr)):
        if smooth_tr[i] == 0:
            continue
        plus_di = (smooth_plus_dm[i] / smooth_tr[i]) * 100
        minus_di = (smooth_minus_dm[i] / smooth_tr[i]) * 100
        
        di_sum = plus_di + minus_di
        if di_sum == 0:
            continue
        
        dx = abs(plus_di - minus_di) / di_sum * 100
        dx_list.append(dx)
    
    if len(dx_list) < period:
        return None
    
    # ADX is smoothed DX
    adx_values = smooth_ema(dx_list, period)
    if not adx_values:
        return None
    
    return adx_values[-1]


def calculate_atr_ratio(
    atr: float,
    avg_atr: float
) -> float:
    """
    Calculate ATR ratio for regime detection.
    
    Higher ratio = more volatility = trending market
    Lower ratio = less volatility = ranging market
    
    Args:
        atr: Current ATR
        avg_atr: Long-term average ATR
        
    Returns:
        ATR ratio
    """
    if avg_atr <= 0:
        return 1.0
    return atr / avg_atr


def calculate_bb_width(
    close: List[float],
    period: int = 20,
    std_dev: float = 2.0
) -> Optional[float]:
    """
    Calculate Bollinger Bands width.
    
    Narrow bands = ranging market
    Wide bands = trending market
    
    Args:
        close: List of close prices
        period: BB period
        std_dev: Standard deviation multiplier
        
    Returns:
        BB width as percentage of price
    """
    if len(close) < period:
        return None
    
    prices = close[-period:]
    ma = sum(prices) / period
    
    if ma <= 0:
        return None
    
    # Calculate standard deviation
    variance = sum((p - ma) ** 2 for p in prices) / period
    std = math.sqrt(variance)
    
    # Width = (Upper - Lower) / MA
    upper = ma + std_dev * std
    lower = ma - std_dev * std
    width = (upper - lower) / ma
    
    return width


def detect_market_regime(
    market_data: Dict[str, Any],
    method: str = "adx",
    **params
) -> str:
    """
    Detect market regime using specified method.
    
    Args:
        market_data: Dict containing:
            - 'high': list of highs
            - 'low': list of lows
            - 'close': list of closes
            - 'atr': current ATR
            - 'avg_atr': average ATR
        method: Detection method
        **params: Method-specific parameters
        
    Returns:
        'trending' or 'ranging'
    """
    if method == "adx":
        high = market_data.get("high", [])
        low = market_data.get("low", [])
        close = market_data.get("close", [])
        threshold = params.get("adx_threshold", DEFAULT_ADX_THRESHOLD)
        
        adx = calculate_adx(high, low, close)
        if adx is None:
            return "trending"  # Default to trending if can't calculate
        
        return "trending" if adx >= threshold else "ranging"
    
    elif method == "atr_ratio":
        atr = market_data.get("atr", 0)
        avg_atr = market_data.get("avg_atr", 0)
        threshold = params.get("atr_ratio_threshold", DEFAULT_ATR_RATIO_THRESHOLD)
        
        if avg_atr <= 0:
            return "trending"
        
        ratio = calculate_atr_ratio(atr, avg_atr)
        return "trending" if ratio >= threshold else "ranging"
    
    elif method == "bb_width":
        close = market_data.get("close", [])
        threshold = params.get("bb_width_threshold", DEFAULT_BB_WIDTH_THRESHOLD)
        
        width = calculate_bb_width(close)
        if width is None:
            return "trending"
        
        return "trending" if width >= threshold else "ranging"
    
    return "trending"


# =============================================================================
# HELPER FUNCTIONS — MULTI-TF
# =============================================================================

def is_higher_timeframe(tf1: str, tf2: str) -> bool:
    """
    Check if tf1 is a higher timeframe than tf2.
    
    Args:
        tf1: First timeframe
        tf2: Second timeframe
        
    Returns:
        True if tf1 > tf2
    """
    return TIMEFRAME_HIERARCHY.get(tf1, 0) > TIMEFRAME_HIERARCHY.get(tf2, 0)


def get_tf_trend(tf_data: Dict[str, Any], direction: str) -> bool:
    """
    Check if timeframe trend aligns with signal direction.
    
    Args:
        tf_data: Timeframe data with 'trend' key
        direction: Signal direction ('long' or 'short')
        
    Returns:
        True if aligned
    """
    trend = tf_data.get("trend", "neutral")
    
    if direction == "long":
        return trend == "up"
    elif direction == "short":
        return trend == "down"
    
    return False


def count_aligned_timeframes(
    htf_data: Dict[str, Dict[str, Any]],
    direction: str,
    required_tfs: List[str]
) -> Tuple[int, int]:
    """
    Count how many timeframes are aligned with the signal.
    
    Args:
        htf_data: Dict of timeframe -> data
        direction: Signal direction
        required_tfs: List of required timeframes
        
    Returns:
        Tuple of (aligned_count, total_count)
    """
    aligned = 0
    total = 0
    
    for tf in required_tfs:
        if tf in htf_data:
            total += 1
            if get_tf_trend(htf_data[tf], direction):
                aligned += 1
    
    return aligned, total


# =============================================================================
# SUMMARY HELPERS
# =============================================================================

def get_trend_state(
    btc_trend: str,
    tf_alignments: Dict[str, bool],
    market_regime: str
) -> Dict[str, Any]:
    """
    Get comprehensive trend state.
    
    Args:
        btc_trend: BTC trend direction
        tf_alignments: Dict of timeframe -> aligned
        market_regime: Current market regime
        
    Returns:
        Dict with trend metrics
    """
    aligned_count = sum(1 for v in tf_alignments.values() if v)
    total_count = len(tf_alignments)
    alignment_pct = (aligned_count / total_count * 100) if total_count > 0 else 0
    
    return {
        "btc_trend": btc_trend,
        "tf_alignments": tf_alignments,
        "aligned_count": aligned_count,
        "total_count": total_count,
        "alignment_percent": alignment_pct,
        "market_regime": market_regime
    }


def get_trend_filter_summary(filters: List['BaseFilter']) -> Dict[str, Any]:
    """
    Get summary of all trend filters.
    
    Args:
        filters: List of trend filter instances
        
    Returns:
        Summary dict
    """
    enabled = []
    disabled = []
    
    for f in filters:
        if f.enabled:
            enabled.append(f.name)
        else:
            disabled.append(f.name)
    
    return {
        "enabled_filters": enabled,
        "disabled_filters": disabled,
        "total_filters": len(filters),
        "active_count": len(enabled)
    }


def create_trend_filter_chain(
    btc_filter_config: Optional[Dict] = None,
    multi_tf_config: Optional[Dict] = None,
    regime_config: Optional[Dict] = None
) -> List['BaseFilter']:
    """
    Create a list of trend filters from configs.
    
    Args:
        btc_filter_config: BTCTrendFilter config
        multi_tf_config: MultiTFFilter config
        regime_config: RegimeFilter config
        
    Returns:
        List of filter instances
    """
    filters = []
    
    if btc_filter_config is not None:
        filters.append(BTCTrendFilter(btc_filter_config))
    
    if multi_tf_config is not None:
        filters.append(MultiTFFilter(multi_tf_config))
    
    if regime_config is not None:
        filters.append(RegimeFilter(regime_config))
    
    return filters


def validate_trend_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate trend filter configuration.
    
    Args:
        config: Combined trend filter config
        
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    # Validate BTC trend method
    btc_method = config.get("btc_trend_method")
    if btc_method and btc_method not in BTC_TREND_METHODS:
        errors.append(f"Invalid BTC trend method: {btc_method}. Valid: {BTC_TREND_METHODS}")
    
    # Validate BTC trend period
    btc_period = config.get("btc_trend_period", DEFAULT_BTC_TREND_PERIOD)
    if not isinstance(btc_period, int) or btc_period < 5 or btc_period > 200:
        errors.append(f"BTC trend period must be int between 5-200, got: {btc_period}")
    
    # Validate timeframes
    required_tfs = config.get("required_timeframes", [])
    if required_tfs:
        for tf in required_tfs:
            if tf not in VALID_TIMEFRAMES:
                errors.append(f"Invalid timeframe: {tf}. Valid: {VALID_TIMEFRAMES}")
    
    # Validate regime method
    regime_method = config.get("regime_detection_method")
    if regime_method and regime_method not in REGIME_METHODS:
        errors.append(f"Invalid regime method: {regime_method}. Valid: {REGIME_METHODS}")
    
    # Validate ADX threshold
    adx_threshold = config.get("adx_threshold", DEFAULT_ADX_THRESHOLD)
    if not isinstance(adx_threshold, (int, float)) or adx_threshold < 10 or adx_threshold > 50:
        errors.append(f"ADX threshold must be 10-50, got: {adx_threshold}")
    
    # Validate allowed regimes
    allowed_regimes = config.get("allowed_regimes", [])
    if allowed_regimes:
        for regime in allowed_regimes:
            if regime not in MARKET_REGIMES:
                errors.append(f"Invalid regime: {regime}. Valid: {MARKET_REGIMES}")
    
    return len(errors) == 0, errors


# =============================================================================
# BTC TREND FILTER
# =============================================================================

@register_filter
class BTCTrendFilter(BaseFilter):
    """
    Filter trades based on BTC market trend direction.
    
    When BTC is in an uptrend:
    - Allow long signals
    - Block short signals (optional)
    
    When BTC is in a downtrend:
    - Allow short signals
    - Block long signals (optional)
    
    Neutral BTC trend:
    - Configurable: allow all or block all
    """
    
    name = "btc_trend_filter"
    description = "Control trading based on BTC market trend direction"
    category = FilterCategory.TREND
    priority = FilterPriority.MEDIUM
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Configuration
        self.follow_btc_trend = self.config.get("follow_btc_trend", True)
        self.btc_trend_method = self.config.get("btc_trend_method", DEFAULT_BTC_TREND_METHOD)
        self.btc_trend_period = self.config.get("btc_trend_period", DEFAULT_BTC_TREND_PERIOD)
        self.allow_neutral = self.config.get("allow_neutral", True)
        self.strict_mode = self.config.get("strict_mode", False)
        
        # Validate method
        if self.btc_trend_method not in BTC_TREND_METHODS:
            logger.warning(f"Invalid BTC trend method: {self.btc_trend_method}, using 'ma'")
            self.btc_trend_method = "ma"
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """
        Check if signal aligns with BTC trend.
        """
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        if not self.follow_btc_trend:
            return create_pass_decision(
                self.name,
                "BTC trend following disabled",
                follow_btc_trend=False
            )
        
        # Skip for BTC itself
        if signal.symbol.upper().startswith("BTC"):
            return create_pass_decision(
                self.name,
                "BTC signal - skip trend filter",
                is_btc=True
            )
        
        # Get BTC trend from context
        btc_trend = context.btc_trend
        
        # If no pre-calculated trend, try to calculate
        if btc_trend is None:
            btc_data = context.htf_data.get("btc", {})
            if btc_data:
                btc_trend = determine_btc_trend(
                    btc_data,
                    self.btc_trend_method,
                    self.btc_trend_period
                )
            else:
                btc_trend = "neutral"
        
        # Handle neutral trend
        if btc_trend == "neutral":
            if self.allow_neutral:
                return create_pass_decision(
                    self.name,
                    "BTC neutral - trades allowed",
                    btc_trend=btc_trend,
                    direction=signal.direction
                )
            else:
                return create_block_decision(
                    self.name,
                    "BTC neutral - no clear trend direction",
                    btc_trend=btc_trend,
                    direction=signal.direction
                )
        
        # Check alignment
        is_aligned = False
        if signal.direction == "long" and btc_trend == "up":
            is_aligned = True
        elif signal.direction == "short" and btc_trend == "down":
            is_aligned = True
        
        # In strict mode, require exact alignment
        # In normal mode, allow trades that don't contradict
        if self.strict_mode:
            if is_aligned:
                return create_pass_decision(
                    self.name,
                    f"Signal aligned with BTC trend ({btc_trend})",
                    btc_trend=btc_trend,
                    direction=signal.direction,
                    aligned=True
                )
            else:
                return create_block_decision(
                    self.name,
                    f"Signal contradicts BTC trend ({btc_trend})",
                    btc_trend=btc_trend,
                    direction=signal.direction,
                    aligned=False
                )
        else:
            # Non-strict: only block direct contradictions
            is_contradiction = False
            if signal.direction == "long" and btc_trend == "down":
                is_contradiction = True
            elif signal.direction == "short" and btc_trend == "up":
                is_contradiction = True
            
            if is_contradiction:
                return create_block_decision(
                    self.name,
                    f"{signal.direction.upper()} blocked - BTC trend is {btc_trend}",
                    btc_trend=btc_trend,
                    direction=signal.direction,
                    contradiction=True
                )
            else:
                return create_pass_decision(
                    self.name,
                    f"Signal compatible with BTC trend ({btc_trend})",
                    btc_trend=btc_trend,
                    direction=signal.direction
                )
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable BTC trend filter"
            },
            "follow_btc_trend": {
                "type": "bool",
                "default": True,
                "description": "Trade only in BTC trend direction"
            },
            "btc_trend_method": {
                "type": "str",
                "default": DEFAULT_BTC_TREND_METHOD,
                "options": BTC_TREND_METHODS,
                "description": "Method for trend detection: ma, ema, supertrend"
            },
            "btc_trend_period": {
                "type": "int",
                "default": DEFAULT_BTC_TREND_PERIOD,
                "min": 5,
                "max": 200,
                "description": "Period for trend calculation"
            },
            "allow_neutral": {
                "type": "bool",
                "default": True,
                "description": "Allow trades when BTC trend is neutral"
            },
            "strict_mode": {
                "type": "bool",
                "default": False,
                "description": "Strict mode: require exact alignment, not just non-contradiction"
            }
        }


# =============================================================================
# MULTI-TIMEFRAME FILTER
# =============================================================================

@register_filter
class MultiTFFilter(BaseFilter):
    """
    Filter trades based on multi-timeframe alignment.
    
    Checks if the signal direction aligns with trends on higher timeframes.
    For example, a 1h long signal should have 4h and 1d also in uptrends.
    """
    
    name = "multi_tf_filter"
    description = "Require alignment across multiple timeframes"
    category = FilterCategory.TREND
    priority = FilterPriority.MEDIUM
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Configuration
        self.required_timeframes = self.config.get("required_timeframes", DEFAULT_REQUIRED_TIMEFRAMES)
        self.require_all_aligned = self.config.get("require_all_aligned", True)
        self.min_aligned_count = self.config.get("min_aligned_count", 1)
        self.skip_if_no_data = self.config.get("skip_if_no_data", True)
        
        # Validate timeframes
        valid_tfs = []
        for tf in self.required_timeframes:
            if tf in VALID_TIMEFRAMES:
                valid_tfs.append(tf)
            else:
                logger.warning(f"Invalid timeframe in MultiTFFilter: {tf}")
        self.required_timeframes = valid_tfs if valid_tfs else DEFAULT_REQUIRED_TIMEFRAMES
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """
        Check if signal aligns with required timeframes.
        """
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        if not self.required_timeframes:
            return create_pass_decision(
                self.name,
                "No required timeframes configured",
                required_timeframes=[]
            )
        
        # Get HTF data
        htf_data = context.htf_data
        if not htf_data:
            if self.skip_if_no_data:
                return create_skip_decision(
                    self.name,
                    "No HTF data available",
                    skip_reason="no_data"
                )
            else:
                return create_block_decision(
                    self.name,
                    "No HTF data available - blocking",
                    skip_reason="no_data"
                )
        
        # Count alignments
        aligned_count, total_count = count_aligned_timeframes(
            htf_data,
            signal.direction,
            self.required_timeframes
        )
        
        # Build alignment details
        alignment_details = {}
        for tf in self.required_timeframes:
            if tf in htf_data:
                trend = htf_data[tf].get("trend", "unknown")
                aligned = get_tf_trend(htf_data[tf], signal.direction)
                alignment_details[tf] = {
                    "trend": trend,
                    "aligned": aligned
                }
        
        # Check if enough timeframes aligned
        if self.require_all_aligned:
            required_count = total_count
        else:
            required_count = min(self.min_aligned_count, total_count)
        
        if total_count == 0:
            if self.skip_if_no_data:
                return create_skip_decision(
                    self.name,
                    f"No data for required timeframes: {self.required_timeframes}",
                    required_timeframes=self.required_timeframes
                )
            else:
                return create_block_decision(
                    self.name,
                    f"No data for required timeframes: {self.required_timeframes}",
                    required_timeframes=self.required_timeframes
                )
        
        if aligned_count >= required_count:
            return create_pass_decision(
                self.name,
                f"{aligned_count}/{total_count} timeframes aligned",
                aligned_count=aligned_count,
                total_count=total_count,
                required_count=required_count,
                alignments=alignment_details
            )
        else:
            return create_block_decision(
                self.name,
                f"Only {aligned_count}/{total_count} timeframes aligned (need {required_count})",
                aligned_count=aligned_count,
                total_count=total_count,
                required_count=required_count,
                alignments=alignment_details
            )
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable multi-TF filter"
            },
            "required_timeframes": {
                "type": "list",
                "default": DEFAULT_REQUIRED_TIMEFRAMES,
                "options": VALID_TIMEFRAMES,
                "description": "Timeframes that must align with signal"
            },
            "require_all_aligned": {
                "type": "bool",
                "default": True,
                "description": "Require ALL timeframes aligned (vs minimum count)"
            },
            "min_aligned_count": {
                "type": "int",
                "default": 1,
                "min": 1,
                "max": 10,
                "description": "Minimum aligned timeframes if require_all is False"
            },
            "skip_if_no_data": {
                "type": "bool",
                "default": True,
                "description": "Skip filter (allow trade) if no HTF data available"
            }
        }


# =============================================================================
# REGIME FILTER
# =============================================================================

@register_filter
class RegimeFilter(BaseFilter):
    """
    Filter trades based on market regime (trending vs ranging).
    
    Uses different detection methods:
    - ADX: ADX > threshold = trending
    - ATR ratio: current ATR / avg ATR > threshold = trending
    - BB width: Bollinger Band width > threshold = trending
    
    Can allow trades only in specific regimes:
    - trending: Strong directional movement
    - ranging: Sideways/consolidating market
    """
    
    name = "regime_filter"
    description = "Detect and filter by market regime (trending/ranging)"
    category = FilterCategory.TREND
    priority = FilterPriority.MEDIUM
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Configuration
        self.allowed_regimes = self.config.get("allowed_regimes", ["trending"])
        self.regime_detection_method = self.config.get("regime_detection_method", DEFAULT_REGIME_METHOD)
        self.adx_threshold = self.config.get("adx_threshold", DEFAULT_ADX_THRESHOLD)
        self.atr_ratio_threshold = self.config.get("atr_ratio_threshold", DEFAULT_ATR_RATIO_THRESHOLD)
        self.bb_width_threshold = self.config.get("bb_width_threshold", DEFAULT_BB_WIDTH_THRESHOLD)
        self.skip_if_no_data = self.config.get("skip_if_no_data", True)
        
        # Validate method
        if self.regime_detection_method not in REGIME_METHODS:
            logger.warning(f"Invalid regime method: {self.regime_detection_method}, using 'adx'")
            self.regime_detection_method = "adx"
        
        # Validate allowed regimes
        valid_regimes = []
        for regime in self.allowed_regimes:
            if regime in MARKET_REGIMES:
                valid_regimes.append(regime)
            else:
                logger.warning(f"Invalid regime: {regime}")
        self.allowed_regimes = valid_regimes if valid_regimes else ["trending"]
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """
        Check if current market regime is allowed.
        """
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        # Build market data from context
        market_data = {
            "high": context.htf_data.get("high", []),
            "low": context.htf_data.get("low", []),
            "close": context.htf_data.get("close", []),
            "atr": context.atr,
            "avg_atr": context.htf_data.get("avg_atr", 0)
        }
        
        # Check if we have enough data
        has_data = False
        if self.regime_detection_method == "adx":
            has_data = len(market_data["close"]) >= 28  # Need 2x period
        elif self.regime_detection_method == "atr_ratio":
            has_data = market_data["atr"] is not None and market_data["avg_atr"] > 0
        elif self.regime_detection_method == "bb_width":
            has_data = len(market_data["close"]) >= 20
        
        if not has_data:
            if self.skip_if_no_data:
                return create_skip_decision(
                    self.name,
                    "Insufficient data for regime detection",
                    method=self.regime_detection_method
                )
            else:
                return create_block_decision(
                    self.name,
                    "Insufficient data for regime detection",
                    method=self.regime_detection_method
                )
        
        # Detect regime
        params = {
            "adx_threshold": self.adx_threshold,
            "atr_ratio_threshold": self.atr_ratio_threshold,
            "bb_width_threshold": self.bb_width_threshold
        }
        
        current_regime = detect_market_regime(
            market_data,
            self.regime_detection_method,
            **params
        )
        
        # Check if regime is allowed
        if current_regime in self.allowed_regimes:
            return create_pass_decision(
                self.name,
                f"Market regime '{current_regime}' is allowed",
                current_regime=current_regime,
                allowed_regimes=self.allowed_regimes,
                method=self.regime_detection_method
            )
        else:
            return create_block_decision(
                self.name,
                f"Market regime '{current_regime}' not in allowed: {self.allowed_regimes}",
                current_regime=current_regime,
                allowed_regimes=self.allowed_regimes,
                method=self.regime_detection_method
            )
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable regime filter"
            },
            "allowed_regimes": {
                "type": "list",
                "default": ["trending"],
                "options": MARKET_REGIMES,
                "description": "Allowed market regimes for trading"
            },
            "regime_detection_method": {
                "type": "str",
                "default": DEFAULT_REGIME_METHOD,
                "options": REGIME_METHODS,
                "description": "Method for regime detection: adx, atr_ratio, bb_width"
            },
            "adx_threshold": {
                "type": "int",
                "default": DEFAULT_ADX_THRESHOLD,
                "min": 10,
                "max": 50,
                "description": "ADX threshold for trending detection"
            },
            "atr_ratio_threshold": {
                "type": "float",
                "default": DEFAULT_ATR_RATIO_THRESHOLD,
                "min": 0.5,
                "max": 3.0,
                "description": "ATR ratio threshold for trending detection"
            },
            "bb_width_threshold": {
                "type": "float",
                "default": DEFAULT_BB_WIDTH_THRESHOLD,
                "min": 0.02,
                "max": 0.5,
                "description": "BB width threshold for trending detection"
            },
            "skip_if_no_data": {
                "type": "bool",
                "default": True,
                "description": "Skip filter if no data for regime detection"
            }
        }
