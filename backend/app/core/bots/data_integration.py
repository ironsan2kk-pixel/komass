"""
KOMAS Bot Runner - Data Integration
====================================
Connects bot runner to historical data storage and live WebSocket feeds.

Functions:
- get_historical_data: Fetch OHLCV from Parquet files
- get_live_price: Get current price from WebSocket cache
- create_data_fetcher: Factory for bot runner data fetcher
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
import pandas as pd

from ..data.storage import DataStorage
from ..logger import get_logger

logger = get_logger("bots.data_integration")


# WebSocket price cache (imported from ws.py when available)
_ws_price_cache: Optional[Dict[str, dict]] = None


# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

# Number of candles to fetch for indicator calculation
# ATR needs lookback period, so we fetch extra candles
DEFAULT_CANDLES_LIMIT = 500

# Minimum candles required for TRG calculation
MIN_CANDLES_REQUIRED = 100


# ═══════════════════════════════════════════════════════════════════
# DATA FETCHER
# ═══════════════════════════════════════════════════════════════════

class BotDataFetcher:
    """
    Data fetcher for bot runner.

    Provides OHLCV data from Parquet files for strategy execution.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Args:
            data_dir: Custom data directory (optional)
        """
        self.storage = DataStorage(data_dir=data_dir)
        logger.info("BotDataFetcher initialized")

    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = DEFAULT_CANDLES_LIMIT
    ) -> List[Dict]:
        """
        Fetch OHLCV data for a symbol.

        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            timeframe: Timeframe (e.g., "1h", "4h", "1d")
            limit: Number of recent candles to return

        Returns:
            List of candle dicts with keys: timestamp, open, high, low, close, volume
            Empty list if data not available
        """
        try:
            # Load from Parquet
            df = self.storage.load(symbol, timeframe)

            if df is None or len(df) == 0:
                logger.warning(f"No data found for {symbol} {timeframe}")
                return []

            # Get last N candles
            if limit > 0:
                df = df.tail(limit)

            # Check minimum requirement
            if len(df) < MIN_CANDLES_REQUIRED:
                logger.warning(
                    f"Insufficient data for {symbol} {timeframe}: "
                    f"{len(df)} candles (minimum {MIN_CANDLES_REQUIRED})"
                )
                return []

            # Convert to list of dicts
            candles = []
            for idx, row in df.iterrows():
                candles.append({
                    'timestamp': idx.to_pydatetime(),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume'])
                })

            logger.debug(f"Fetched {len(candles)} candles for {symbol} {timeframe}")
            return candles

        except Exception as e:
            logger.error(f"Error fetching data for {symbol} {timeframe}: {e}")
            return []

    def get_latest_price(self, symbol: str, timeframe: str) -> Optional[float]:
        """
        Get latest close price for a symbol.

        Args:
            symbol: Trading pair
            timeframe: Timeframe

        Returns:
            Latest close price or None
        """
        try:
            df = self.storage.load(symbol, timeframe)
            if df is None or len(df) == 0:
                return None

            return float(df.iloc[-1]['close'])

        except Exception as e:
            logger.error(f"Error getting latest price for {symbol}: {e}")
            return None

    def get_live_price(self, symbol: str) -> Optional[float]:
        """
        Get live price from WebSocket cache or fallback to Parquet.

        Args:
            symbol: Trading pair

        Returns:
            Current price or None
        """
        global _ws_price_cache

        # Try WebSocket cache first
        if _ws_price_cache is not None:
            price_data = _ws_price_cache.get(symbol.upper())
            if price_data:
                # Extract current price from ticker data
                price = price_data.get('c') or price_data.get('price') or price_data.get('close')
                if price:
                    return float(price)

        # Fallback to latest Parquet data
        # Try multiple timeframes (prefer lower timeframes for more recent data)
        for tf in ['1m', '5m', '15m', '1h']:
            price = self.get_latest_price(symbol, tf)
            if price is not None:
                return price

        logger.warning(f"No live price available for {symbol}")
        return None

    def get_data_info(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """
        Get information about available data for a symbol.

        Returns:
            Dict with keys: rows, start, end, last_update
            None if no data available
        """
        try:
            info = self.storage.get_info(symbol, timeframe)

            if info is None:
                return None

            return {
                'rows': info.rows,
                'start': info.start_date.isoformat() if info.start_date else None,
                'end': info.end_date.isoformat() if info.end_date else None,
                'last_update': info.modified.isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting data info for {symbol} {timeframe}: {e}")
            return None

    def check_data_freshness(
        self,
        symbol: str,
        timeframe: str,
        max_age_hours: int = 24
    ) -> bool:
        """
        Check if data is fresh (updated recently).

        Args:
            symbol: Trading pair
            timeframe: Timeframe
            max_age_hours: Maximum age in hours

        Returns:
            True if data is fresh, False otherwise
        """
        try:
            info = self.storage.get_info(symbol, timeframe)

            if info is None or info.end_date is None:
                return False

            age = datetime.now() - info.end_date
            is_fresh = age.total_seconds() / 3600 <= max_age_hours

            if not is_fresh:
                logger.warning(
                    f"Stale data for {symbol} {timeframe}: "
                    f"last candle {age.total_seconds() / 3600:.1f} hours old"
                )

            return is_fresh

        except Exception as e:
            logger.error(f"Error checking data freshness: {e}")
            return False


# ═══════════════════════════════════════════════════════════════════
# FACTORY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

_global_fetcher: Optional[BotDataFetcher] = None


def get_data_fetcher(data_dir: Optional[Path] = None) -> BotDataFetcher:
    """
    Get or create global data fetcher instance.

    Args:
        data_dir: Custom data directory (optional)

    Returns:
        BotDataFetcher instance
    """
    global _global_fetcher

    if _global_fetcher is None:
        _global_fetcher = BotDataFetcher(data_dir=data_dir)
        logger.info("Created global BotDataFetcher instance")

    return _global_fetcher


def create_runner_data_fetcher(data_dir: Optional[Path] = None):
    """
    Create a data fetcher function for bot runner.

    This function is compatible with BotsRunner.set_data_fetcher().

    Args:
        data_dir: Custom data directory (optional)

    Returns:
        Callable function(symbol: str, timeframe: str) -> List[Dict]
    """
    fetcher = get_data_fetcher(data_dir=data_dir)

    def fetch_data(symbol: str, timeframe: str) -> List[Dict]:
        """Fetch OHLCV data for bot runner"""
        return fetcher.fetch_ohlcv(symbol, timeframe)

    return fetch_data


# ═══════════════════════════════════════════════════════════════════
# VALIDATION
# ═══════════════════════════════════════════════════════════════════

def validate_data_availability(
    symbols: List[str],
    timeframe: str,
    min_candles: int = MIN_CANDLES_REQUIRED
) -> Dict[str, bool]:
    """
    Validate data availability for multiple symbols.

    Args:
        symbols: List of trading pairs
        timeframe: Timeframe
        min_candles: Minimum candles required

    Returns:
        Dict mapping symbol -> availability (True/False)
    """
    fetcher = get_data_fetcher()
    results = {}

    for symbol in symbols:
        try:
            info = fetcher.get_data_info(symbol, timeframe)

            if info is None:
                results[symbol] = False
            else:
                results[symbol] = info['rows'] >= min_candles

        except Exception as e:
            logger.error(f"Error validating {symbol}: {e}")
            results[symbol] = False

    return results


def get_missing_data_symbols(
    symbols: List[str],
    timeframe: str
) -> List[str]:
    """
    Get list of symbols with missing or insufficient data.

    Args:
        symbols: List of trading pairs
        timeframe: Timeframe

    Returns:
        List of symbols that need data download
    """
    availability = validate_data_availability(symbols, timeframe)
    return [symbol for symbol, available in availability.items() if not available]


# ═══════════════════════════════════════════════════════════════════
# WEBSOCKET INTEGRATION
# ═══════════════════════════════════════════════════════════════════

def connect_websocket_price_cache():
    """
    Connect to WebSocket price cache for live price updates.

    This allows the data fetcher to use live prices when available.
    """
    global _ws_price_cache

    try:
        # Import ws.py price cache
        from ...api import ws
        _ws_price_cache = ws._price_cache
        logger.info("Connected to WebSocket price cache")
        return True
    except Exception as e:
        logger.warning(f"Could not connect to WebSocket price cache: {e}")
        logger.info("Live prices will use Parquet data fallback")
        return False


def create_live_price_fetcher(data_dir: Optional[Path] = None):
    """
    Create a live price fetcher function for bot runner.

    Returns a function that can get current market price for a symbol.

    Args:
        data_dir: Custom data directory (optional)

    Returns:
        Callable function(symbol: str) -> Optional[float]
    """
    fetcher = get_data_fetcher(data_dir=data_dir)

    # Try to connect to WebSocket cache
    connect_websocket_price_cache()

    def get_price(symbol: str) -> Optional[float]:
        """Get live price for symbol"""
        return fetcher.get_live_price(symbol)

    return get_price
