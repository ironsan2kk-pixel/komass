"""
Multi-TF Data Loader - KOMAS v4.0
=================================

Provides automatic higher timeframe data loading and aggregation
for multi-timeframe signal analysis.

Features:
- Automatic TF hierarchy resolution
- Auto-aggregation from lower TF data
- Binance Futures API loading
- Multiple trend detection methods (EMA, SuperTrend, ADX)
- Configurable TF weights for scoring

Chat #35: Score Multi-TF
Author: KOMAS Team
Version: 4.0
"""

import pandas as pd
import numpy as np
import asyncio
import aiohttp
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Timeframe hierarchy: trading TF -> higher TFs to check
TF_HIERARCHY = {
    '1m': ['5m', '15m', '1h', '4h', '1d'],
    '3m': ['15m', '1h', '4h', '1d'],
    '5m': ['15m', '1h', '4h', '1d'],
    '15m': ['1h', '4h', '1d'],
    '30m': ['1h', '4h', '1d'],
    '1h': ['4h', '1d'],
    '2h': ['4h', '1d'],
    '4h': ['1d'],
    '6h': ['1d'],
    '8h': ['1d'],
    '12h': ['1d'],
    '1d': [],
}

# Default weight distribution for Multi-TF scoring (total 25 pts)
DEFAULT_TF_WEIGHTS = {
    '4h': 10,
    '1d': 15,
}

# Timeframe conversion to minutes
TF_MINUTES = {
    '1m': 1,
    '3m': 3,
    '5m': 5,
    '15m': 15,
    '30m': 30,
    '1h': 60,
    '2h': 120,
    '4h': 240,
    '6h': 360,
    '8h': 480,
    '12h': 720,
    '1d': 1440,
}

# Binance Futures API URL
BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1/klines"


class TrendDetectionMethod(Enum):
    """Available trend detection methods"""
    EMA = "ema"
    SUPERTREND = "supertrend"
    ADX = "adx"
    COMBINED = "combined"


class TrendDirection(Enum):
    """Trend direction"""
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class TFAnalysisResult:
    """Result of higher timeframe analysis"""
    timeframe: str
    direction: str
    method_used: str
    confidence: float
    data_source: str  # 'file', 'api', 'aggregated'
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timeframe': self.timeframe,
            'direction': self.direction,
            'method_used': self.method_used,
            'confidence': round(self.confidence, 2),
            'data_source': self.data_source,
            'details': self.details,
        }


@dataclass
class MultiTFResult:
    """Complete multi-TF analysis result"""
    score: float
    max_score: float
    aligned_tfs: List[str]
    misaligned_tfs: List[str]
    analyses: Dict[str, TFAnalysisResult]
    signal_direction: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'score': round(self.score, 1),
            'max_score': self.max_score,
            'aligned_tfs': self.aligned_tfs,
            'misaligned_tfs': self.misaligned_tfs,
            'analyses': {k: v.to_dict() for k, v in self.analyses.items()},
            'signal_direction': self.signal_direction,
        }


# =============================================================================
# TREND DETECTION METHODS
# =============================================================================

def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Calculate Exponential Moving Average"""
    return series.ewm(span=period, adjust=False).mean()


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period, min_periods=1).mean()
    
    return atr


def detect_trend_ema(
    df: pd.DataFrame,
    fast_period: int = 9,
    slow_period: int = 21
) -> Tuple[TrendDirection, float, Dict[str, Any]]:
    """
    Detect trend using EMA crossover
    
    Args:
        df: OHLCV DataFrame
        fast_period: Fast EMA period
        slow_period: Slow EMA period
        
    Returns:
        Tuple of (direction, confidence, details)
    """
    if len(df) < slow_period:
        return TrendDirection.SIDEWAYS, 0.0, {'error': 'Insufficient data'}
    
    close = df['close']
    ema_fast = calculate_ema(close, fast_period)
    ema_slow = calculate_ema(close, slow_period)
    
    current_fast = ema_fast.iloc[-1]
    current_slow = ema_slow.iloc[-1]
    
    # Calculate EMA difference as percentage
    ema_diff_pct = ((current_fast - current_slow) / current_slow) * 100
    
    # Check recent crossovers for stronger signals
    recent_len = min(5, len(df) - 1)
    prev_fast = ema_fast.iloc[-recent_len]
    prev_slow = ema_slow.iloc[-recent_len]
    
    # Determine direction and confidence
    if current_fast > current_slow:
        direction = TrendDirection.UP
        # Confidence based on distance between EMAs
        confidence = min(1.0, abs(ema_diff_pct) / 2.0)  # 2% diff = 100% confidence
        
        # Boost confidence if recent crossover
        if prev_fast <= prev_slow:
            confidence = min(1.0, confidence + 0.2)
    elif current_fast < current_slow:
        direction = TrendDirection.DOWN
        confidence = min(1.0, abs(ema_diff_pct) / 2.0)
        
        if prev_fast >= prev_slow:
            confidence = min(1.0, confidence + 0.2)
    else:
        direction = TrendDirection.SIDEWAYS
        confidence = 0.0
    
    details = {
        'ema_fast': round(current_fast, 2),
        'ema_slow': round(current_slow, 2),
        'ema_diff_pct': round(ema_diff_pct, 3),
        'fast_period': fast_period,
        'slow_period': slow_period,
    }
    
    return direction, confidence, details


def detect_trend_supertrend(
    df: pd.DataFrame,
    period: int = 10,
    multiplier: float = 3.0
) -> Tuple[TrendDirection, float, Dict[str, Any]]:
    """
    Detect trend using SuperTrend indicator
    
    Args:
        df: OHLCV DataFrame
        period: ATR period
        multiplier: ATR multiplier
        
    Returns:
        Tuple of (direction, confidence, details)
    """
    if len(df) < period:
        return TrendDirection.SIDEWAYS, 0.0, {'error': 'Insufficient data'}
    
    hl2 = (df['high'] + df['low']) / 2
    atr = calculate_atr(df, period)
    
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    close = df['close']
    
    # Calculate SuperTrend direction
    supertrend = pd.Series(index=df.index, dtype=float)
    direction_series = pd.Series(index=df.index, dtype=int)
    
    for i in range(len(df)):
        if i == 0:
            supertrend.iloc[i] = lower_band.iloc[i]
            direction_series.iloc[i] = 1
            continue
        
        if close.iloc[i] > supertrend.iloc[i-1]:
            supertrend.iloc[i] = max(lower_band.iloc[i], supertrend.iloc[i-1])
            direction_series.iloc[i] = 1
        else:
            supertrend.iloc[i] = min(upper_band.iloc[i], supertrend.iloc[i-1])
            direction_series.iloc[i] = -1
    
    current_dir = direction_series.iloc[-1]
    
    # Calculate confidence based on distance from supertrend line
    current_close = close.iloc[-1]
    current_st = supertrend.iloc[-1]
    distance_pct = abs((current_close - current_st) / current_close) * 100
    
    # More distance = higher confidence
    confidence = min(1.0, distance_pct / 2.0)  # 2% distance = 100% confidence
    
    # Count consecutive same-direction candles
    consecutive = 1
    for i in range(-2, -min(10, len(df)), -1):
        if direction_series.iloc[i] == current_dir:
            consecutive += 1
        else:
            break
    
    # Boost confidence for consecutive signals
    confidence = min(1.0, confidence + (consecutive * 0.05))
    
    if current_dir == 1:
        direction = TrendDirection.UP
    elif current_dir == -1:
        direction = TrendDirection.DOWN
    else:
        direction = TrendDirection.SIDEWAYS
    
    details = {
        'supertrend_direction': int(current_dir),
        'supertrend_line': round(current_st, 2),
        'close': round(current_close, 2),
        'distance_pct': round(distance_pct, 2),
        'consecutive_candles': consecutive,
        'period': period,
        'multiplier': multiplier,
    }
    
    return direction, confidence, details


def detect_trend_adx(
    df: pd.DataFrame,
    period: int = 14,
    threshold: int = 25
) -> Tuple[TrendDirection, float, Dict[str, Any]]:
    """
    Detect trend using ADX indicator
    
    Args:
        df: OHLCV DataFrame
        period: ADX period
        threshold: ADX threshold for trend strength
        
    Returns:
        Tuple of (direction, confidence, details)
    """
    if len(df) < period + 5:
        return TrendDirection.SIDEWAYS, 0.0, {'error': 'Insufficient data'}
    
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range
    tr = pd.concat([
        high - low,
        abs(high - close.shift(1)),
        abs(low - close.shift(1))
    ], axis=1).max(axis=1)
    
    # Directional Movement
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    # Smoothed TR and DM
    atr = tr.rolling(window=period, min_periods=1).mean()
    plus_di = 100 * (plus_dm.rolling(window=period, min_periods=1).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period, min_periods=1).mean() / atr)
    
    # DX and ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(window=period, min_periods=1).mean()
    
    current_adx = adx.iloc[-1]
    current_plus_di = plus_di.iloc[-1]
    current_minus_di = minus_di.iloc[-1]
    
    # Determine direction based on DI values
    if current_adx >= threshold:
        if current_plus_di > current_minus_di:
            direction = TrendDirection.UP
        else:
            direction = TrendDirection.DOWN
        
        # Confidence based on ADX value and DI difference
        adx_strength = min(1.0, (current_adx - threshold) / 25)  # 25 above threshold = 100%
        di_diff = abs(current_plus_di - current_minus_di)
        di_confidence = min(1.0, di_diff / 20)  # 20 DI diff = 100%
        
        confidence = (adx_strength + di_confidence) / 2
    else:
        direction = TrendDirection.SIDEWAYS
        confidence = 0.0
    
    details = {
        'adx': round(current_adx, 1),
        'plus_di': round(current_plus_di, 1),
        'minus_di': round(current_minus_di, 1),
        'is_trending': current_adx >= threshold,
        'threshold': threshold,
    }
    
    return direction, confidence, details


def detect_trend_combined(
    df: pd.DataFrame,
    ema_weight: float = 0.4,
    supertrend_weight: float = 0.35,
    adx_weight: float = 0.25
) -> Tuple[TrendDirection, float, Dict[str, Any]]:
    """
    Detect trend using combination of all methods
    
    Args:
        df: OHLCV DataFrame
        ema_weight: Weight for EMA method
        supertrend_weight: Weight for SuperTrend method
        adx_weight: Weight for ADX method
        
    Returns:
        Tuple of (direction, confidence, details)
    """
    # Get individual results
    ema_dir, ema_conf, ema_details = detect_trend_ema(df)
    st_dir, st_conf, st_details = detect_trend_supertrend(df)
    adx_dir, adx_conf, adx_details = detect_trend_adx(df)
    
    # Count votes
    up_votes = 0.0
    down_votes = 0.0
    
    methods = [
        (ema_dir, ema_conf, ema_weight, 'ema'),
        (st_dir, st_conf, supertrend_weight, 'supertrend'),
        (adx_dir, adx_conf, adx_weight, 'adx'),
    ]
    
    for direction, conf, weight, _ in methods:
        if direction == TrendDirection.UP:
            up_votes += conf * weight
        elif direction == TrendDirection.DOWN:
            down_votes += conf * weight
    
    total_weight = ema_weight + supertrend_weight + adx_weight
    up_score = up_votes / total_weight
    down_score = down_votes / total_weight
    
    # Determine final direction
    if up_score > down_score and up_score > 0.3:
        direction = TrendDirection.UP
        confidence = up_score
    elif down_score > up_score and down_score > 0.3:
        direction = TrendDirection.DOWN
        confidence = down_score
    else:
        direction = TrendDirection.SIDEWAYS
        confidence = 0.0
    
    details = {
        'ema': {
            'direction': ema_dir.value,
            'confidence': round(ema_conf, 2),
            **ema_details,
        },
        'supertrend': {
            'direction': st_dir.value,
            'confidence': round(st_conf, 2),
            **st_details,
        },
        'adx': {
            'direction': adx_dir.value,
            'confidence': round(adx_conf, 2),
            **adx_details,
        },
        'up_score': round(up_score, 2),
        'down_score': round(down_score, 2),
        'weights': {
            'ema': ema_weight,
            'supertrend': supertrend_weight,
            'adx': adx_weight,
        },
    }
    
    return direction, confidence, details


# =============================================================================
# DATA AGGREGATION
# =============================================================================

def aggregate_to_higher_tf(
    df: pd.DataFrame,
    source_tf: str,
    target_tf: str
) -> Optional[pd.DataFrame]:
    """
    Aggregate lower timeframe data to higher timeframe
    
    Args:
        df: Source OHLCV DataFrame
        source_tf: Source timeframe (e.g., '1h')
        target_tf: Target timeframe (e.g., '4h')
        
    Returns:
        Aggregated DataFrame or None if not possible
    """
    source_minutes = TF_MINUTES.get(source_tf)
    target_minutes = TF_MINUTES.get(target_tf)
    
    if not source_minutes or not target_minutes:
        logger.warning(f"Unknown timeframe: {source_tf} or {target_tf}")
        return None
    
    if target_minutes <= source_minutes:
        logger.warning(f"Cannot aggregate {source_tf} to {target_tf} (same or lower)")
        return None
    
    # Check if aggregation is possible
    if target_minutes % source_minutes != 0:
        logger.warning(f"Cannot evenly aggregate {source_tf} to {target_tf}")
        return None
    
    # Convert to pandas resample format
    resample_map = {
        5: '5T',
        15: '15T',
        30: '30T',
        60: '1H',
        120: '2H',
        240: '4H',
        360: '6H',
        480: '8H',
        720: '12H',
        1440: '1D',
    }
    
    resample_freq = resample_map.get(target_minutes)
    if not resample_freq:
        logger.warning(f"Unsupported target timeframe for aggregation: {target_tf}")
        return None
    
    try:
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'timestamp' in df.columns:
                df = df.set_index('timestamp')
            else:
                return None
        
        # Resample OHLCV data
        aggregated = df.resample(resample_freq).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
        }).dropna()
        
        if len(aggregated) < 10:
            logger.warning(f"Insufficient aggregated data: {len(aggregated)} candles")
            return None
        
        logger.debug(f"Aggregated {len(df)} {source_tf} candles to {len(aggregated)} {target_tf} candles")
        return aggregated
        
    except Exception as e:
        logger.error(f"Error aggregating data: {e}")
        return None


# =============================================================================
# DATA LOADING
# =============================================================================

def find_data_dir() -> Path:
    """Find data directory"""
    possible_paths = [
        Path(__file__).parent.parent.parent / "data",
        Path("data"),
        Path("backend/data"),
        Path("../data"),
        Path.cwd() / "data",
        Path.cwd() / "backend" / "data",
    ]
    
    for p in possible_paths:
        if p.exists():
            return p
    
    default = Path(__file__).parent.parent.parent / "data"
    default.mkdir(exist_ok=True)
    return default


DATA_DIR = find_data_dir()


def load_ohlcv_from_file(symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
    """
    Load OHLCV data from local file
    
    Args:
        symbol: Trading pair symbol
        timeframe: Timeframe
        
    Returns:
        DataFrame or None if not found
    """
    parquet_path = DATA_DIR / f"{symbol}_{timeframe}.parquet"
    csv_path = DATA_DIR / f"{symbol}_{timeframe}.csv"
    
    try:
        if parquet_path.exists():
            df = pd.read_parquet(parquet_path)
            return df
        elif csv_path.exists():
            df = pd.read_csv(csv_path, parse_dates=['timestamp'])
            if 'timestamp' in df.columns:
                df.set_index('timestamp', inplace=True)
            return df
    except Exception as e:
        logger.error(f"Error loading data from file: {e}")
    
    return None


async def load_ohlcv_from_api(
    symbol: str,
    timeframe: str,
    limit: int = 100
) -> Optional[pd.DataFrame]:
    """
    Load OHLCV data from Binance Futures API
    
    Args:
        symbol: Trading pair symbol
        timeframe: Timeframe
        limit: Number of candles to fetch
        
    Returns:
        DataFrame or None if API call fails
    """
    try:
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(
                BINANCE_FUTURES_URL,
                params={
                    "symbol": symbol.upper(),
                    "interval": timeframe,
                    "limit": limit,
                }
            ) as response:
                if response.status != 200:
                    logger.warning(f"Binance API returned status {response.status}")
                    return None
                
                data = await response.json()
                
                if not data or not isinstance(data, list):
                    return None
                
                candles = []
                for candle in data:
                    candles.append({
                        "timestamp": datetime.fromtimestamp(candle[0] / 1000),
                        "open": float(candle[1]),
                        "high": float(candle[2]),
                        "low": float(candle[3]),
                        "close": float(candle[4]),
                        "volume": float(candle[5]),
                    })
                
                df = pd.DataFrame(candles)
                df.set_index("timestamp", inplace=True)
                
                # Ensure numeric columns
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
                
    except asyncio.TimeoutError:
        logger.warning(f"Timeout loading {symbol}_{timeframe} from Binance API")
    except Exception as e:
        logger.error(f"Error loading from Binance API: {e}")
    
    return None


# =============================================================================
# MULTI-TF LOADER CLASS
# =============================================================================

class MultiTFLoader:
    """
    Multi-Timeframe Data Loader
    
    Provides automatic higher timeframe data loading and analysis
    for signal scoring.
    
    Usage:
        loader = MultiTFLoader()
        result = await loader.analyze(
            symbol='BTCUSDT',
            trading_tf='1h',
            signal_direction='long',
            trading_data=df_1h
        )
    """
    
    def __init__(
        self,
        tf_weights: Optional[Dict[str, int]] = None,
        detection_method: TrendDetectionMethod = TrendDetectionMethod.COMBINED,
        use_api_fallback: bool = True,
        use_aggregation_fallback: bool = True,
    ):
        """
        Initialize MultiTFLoader
        
        Args:
            tf_weights: Weight distribution for TFs (default: 4h=10, 1d=15)
            detection_method: Method to use for trend detection
            use_api_fallback: Whether to load from Binance API if file not found
            use_aggregation_fallback: Whether to aggregate from lower TF if API fails
        """
        self.tf_weights = tf_weights or DEFAULT_TF_WEIGHTS
        self.detection_method = detection_method
        self.use_api_fallback = use_api_fallback
        self.use_aggregation_fallback = use_aggregation_fallback
        
        # Cache for loaded data
        self._cache: Dict[str, pd.DataFrame] = {}
    
    async def load_higher_tf_data(
        self,
        symbol: str,
        trading_tf: str,
        trading_data: Optional[pd.DataFrame] = None,
    ) -> Dict[str, pd.DataFrame]:
        """
        Load all relevant higher timeframe data
        
        Args:
            symbol: Trading pair symbol
            trading_tf: Current trading timeframe
            trading_data: Optional trading TF data for aggregation
            
        Returns:
            Dict of higher TF DataFrames
        """
        higher_tfs = list(self.tf_weights.keys())
        result = {}
        
        for tf in higher_tfs:
            # Skip if TF is same or lower than trading TF
            if TF_MINUTES.get(tf, 0) <= TF_MINUTES.get(trading_tf, 0):
                continue
            
            df = None
            data_source = None
            
            # 1. Try loading from file
            df = load_ohlcv_from_file(symbol, tf)
            if df is not None and len(df) >= 10:
                data_source = 'file'
                logger.debug(f"Loaded {symbol}_{tf} from file ({len(df)} candles)")
            
            # 2. Try API fallback
            if df is None and self.use_api_fallback:
                df = await load_ohlcv_from_api(symbol, tf, limit=100)
                if df is not None:
                    data_source = 'api'
                    logger.debug(f"Loaded {symbol}_{tf} from API ({len(df)} candles)")
            
            # 3. Try aggregation fallback
            if df is None and self.use_aggregation_fallback and trading_data is not None:
                df = aggregate_to_higher_tf(trading_data, trading_tf, tf)
                if df is not None:
                    data_source = 'aggregated'
                    logger.debug(f"Aggregated {trading_tf} to {tf} ({len(df)} candles)")
            
            if df is not None and len(df) >= 10:
                result[tf] = df
                self._cache[f"{symbol}_{tf}"] = df
        
        return result
    
    def detect_trend(
        self,
        df: pd.DataFrame,
        method: Optional[TrendDetectionMethod] = None,
    ) -> Tuple[TrendDirection, float, Dict[str, Any]]:
        """
        Detect trend direction using specified method
        
        Args:
            df: OHLCV DataFrame
            method: Trend detection method (default: self.detection_method)
            
        Returns:
            Tuple of (direction, confidence, details)
        """
        method = method or self.detection_method
        
        if method == TrendDetectionMethod.EMA:
            return detect_trend_ema(df)
        elif method == TrendDetectionMethod.SUPERTREND:
            return detect_trend_supertrend(df)
        elif method == TrendDetectionMethod.ADX:
            return detect_trend_adx(df)
        else:
            return detect_trend_combined(df)
    
    async def analyze(
        self,
        symbol: str,
        trading_tf: str,
        signal_direction: str,
        trading_data: Optional[pd.DataFrame] = None,
        higher_tf_data: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> MultiTFResult:
        """
        Analyze multi-TF alignment for a signal
        
        Args:
            symbol: Trading pair symbol
            trading_tf: Current trading timeframe
            signal_direction: Signal direction ('long' or 'short')
            trading_data: Optional trading TF data for aggregation
            higher_tf_data: Optional pre-loaded higher TF data
            
        Returns:
            MultiTFResult with score and analysis details
        """
        # Normalize direction
        signal_direction = signal_direction.lower()
        if signal_direction not in ('long', 'short'):
            signal_direction = 'long' if signal_direction == '1' else 'short'
        
        # Load higher TF data if not provided
        if higher_tf_data is None:
            higher_tf_data = await self.load_higher_tf_data(
                symbol, trading_tf, trading_data
            )
        
        # Analyze each higher TF
        analyses: Dict[str, TFAnalysisResult] = {}
        aligned_tfs: List[str] = []
        misaligned_tfs: List[str] = []
        total_score = 0.0
        max_score = sum(self.tf_weights.values())
        
        for tf, weight in self.tf_weights.items():
            tf_df = higher_tf_data.get(tf)
            
            if tf_df is not None and len(tf_df) >= 10:
                # Detect trend
                direction, confidence, details = self.detect_trend(tf_df)
                
                # Check alignment
                is_aligned = False
                if signal_direction == 'long' and direction == TrendDirection.UP:
                    is_aligned = True
                elif signal_direction == 'short' and direction == TrendDirection.DOWN:
                    is_aligned = True
                
                # Calculate score
                if is_aligned:
                    tf_score = weight * confidence
                    total_score += tf_score
                    aligned_tfs.append(tf)
                else:
                    misaligned_tfs.append(tf)
                
                # Determine data source
                cache_key = f"{symbol}_{tf}"
                if cache_key in self._cache:
                    data_source = 'cached'
                else:
                    data_source = 'loaded'
                
                analyses[tf] = TFAnalysisResult(
                    timeframe=tf,
                    direction=direction.value,
                    method_used=self.detection_method.value,
                    confidence=confidence,
                    data_source=data_source,
                    details=details,
                )
            else:
                # Higher TF data not available - give partial points
                partial_score = weight * 0.5
                total_score += partial_score
                
                analyses[tf] = TFAnalysisResult(
                    timeframe=tf,
                    direction='unavailable',
                    method_used=self.detection_method.value,
                    confidence=0.5,
                    data_source='unavailable',
                    details={'message': 'Higher TF data not available'},
                )
        
        return MultiTFResult(
            score=total_score,
            max_score=max_score,
            aligned_tfs=aligned_tfs,
            misaligned_tfs=misaligned_tfs,
            analyses=analyses,
            signal_direction=signal_direction,
        )
    
    def calculate_score_sync(
        self,
        signal_direction: str,
        higher_tf_data: Dict[str, pd.DataFrame],
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Synchronous version of multi-TF score calculation
        
        Used by SignalScorer._calculate_multi_tf()
        
        Args:
            signal_direction: Signal direction ('long' or 'short')
            higher_tf_data: Dict of higher TF DataFrames
            
        Returns:
            Tuple of (score, details)
        """
        # Normalize direction
        signal_direction = signal_direction.lower()
        if signal_direction not in ('long', 'short'):
            signal_direction = 'long' if signal_direction == '1' else 'short'
        
        analyses = {}
        aligned_tfs = []
        misaligned_tfs = []
        total_score = 0.0
        max_score = sum(self.tf_weights.values())
        
        for tf, weight in self.tf_weights.items():
            tf_df = higher_tf_data.get(tf)
            
            if tf_df is not None and len(tf_df) >= 10:
                # Detect trend
                direction, confidence, details = self.detect_trend(tf_df)
                
                # Check alignment
                is_aligned = False
                if signal_direction == 'long' and direction == TrendDirection.UP:
                    is_aligned = True
                elif signal_direction == 'short' and direction == TrendDirection.DOWN:
                    is_aligned = True
                
                # Calculate score
                if is_aligned:
                    tf_score = weight * confidence
                    total_score += tf_score
                    aligned_tfs.append(tf)
                else:
                    misaligned_tfs.append(tf)
                
                analyses[tf] = {
                    'direction': direction.value,
                    'confidence': round(confidence, 2),
                    'aligned': is_aligned,
                    'details': details,
                }
            else:
                # Higher TF data not available - give partial points
                partial_score = weight * 0.5
                total_score += partial_score
                
                analyses[tf] = {
                    'direction': 'unavailable',
                    'confidence': 0.5,
                    'aligned': None,
                }
        
        details = {
            'higher_tfs': analyses,
            'alignments': aligned_tfs,
            'misalignments': misaligned_tfs,
            'method': self.detection_method.value,
        }
        
        return total_score, details
    
    def clear_cache(self):
        """Clear data cache"""
        self._cache.clear()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_higher_tfs(trading_tf: str) -> List[str]:
    """Get list of higher timeframes for a trading timeframe"""
    return TF_HIERARCHY.get(trading_tf, ['4h', '1d'])


def get_tf_weights(custom_weights: Optional[Dict[str, int]] = None) -> Dict[str, int]:
    """Get TF weights with optional custom overrides"""
    weights = DEFAULT_TF_WEIGHTS.copy()
    if custom_weights:
        weights.update(custom_weights)
    return weights


async def load_all_higher_tfs(
    symbol: str,
    trading_tf: str,
    trading_data: Optional[pd.DataFrame] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Convenience function to load all higher TF data
    
    Args:
        symbol: Trading pair symbol
        trading_tf: Current trading timeframe
        trading_data: Optional trading TF data for aggregation
        
    Returns:
        Dict of higher TF DataFrames
    """
    loader = MultiTFLoader()
    return await loader.load_higher_tf_data(symbol, trading_tf, trading_data)


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'MultiTFLoader',
    'MultiTFResult',
    'TFAnalysisResult',
    'TrendDetectionMethod',
    'TrendDirection',
    'detect_trend_ema',
    'detect_trend_supertrend',
    'detect_trend_adx',
    'detect_trend_combined',
    'aggregate_to_higher_tf',
    'load_ohlcv_from_file',
    'load_ohlcv_from_api',
    'get_higher_tfs',
    'get_tf_weights',
    'load_all_higher_tfs',
    'TF_HIERARCHY',
    'DEFAULT_TF_WEIGHTS',
    'TF_MINUTES',
]
