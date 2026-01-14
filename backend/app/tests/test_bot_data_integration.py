"""
Unit Tests for Bot Data Integration
====================================
Tests for data_integration.py - data fetcher for bot runner
"""

import pytest
from pathlib import Path
from datetime import datetime
import pandas as pd
import tempfile
import shutil

from app.core.bots.data_integration import (
    BotDataFetcher,
    get_data_fetcher,
    create_runner_data_fetcher,
    validate_data_availability,
    get_missing_data_symbols
)


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory with test data"""
    temp_dir = Path(tempfile.mkdtemp())

    # Create test OHLCV data
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1h')
    df = pd.DataFrame({
        'open': [100.0 + i * 0.1 for i in range(200)],
        'high': [100.5 + i * 0.1 for i in range(200)],
        'low': [99.5 + i * 0.1 for i in range(200)],
        'close': [100.0 + i * 0.1 for i in range(200)],
        'volume': [1000000.0] * 200
    }, index=dates)

    # Save test files
    df.to_parquet(temp_dir / "BTCUSDT_1h.parquet")
    df.to_parquet(temp_dir / "ETHUSDT_1h.parquet")

    # Smaller dataset (insufficient data)
    df_small = df.head(50)
    df_small.to_parquet(temp_dir / "XRPUSDT_1h.parquet")

    yield temp_dir

    # Cleanup
    shutil.rmtree(temp_dir)


def test_bot_data_fetcher_init(temp_data_dir):
    """Test BotDataFetcher initialization"""
    fetcher = BotDataFetcher(data_dir=temp_data_dir)

    assert fetcher.storage is not None
    assert fetcher.storage.data_dir == temp_data_dir


def test_fetch_ohlcv_success(temp_data_dir):
    """Test fetching OHLCV data successfully"""
    fetcher = BotDataFetcher(data_dir=temp_data_dir)

    candles = fetcher.fetch_ohlcv("BTCUSDT", "1h", limit=100)

    assert len(candles) == 100
    assert all(k in candles[0] for k in ['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    assert candles[0]['open'] > 0
    assert candles[-1]['timestamp'] > candles[0]['timestamp']


def test_fetch_ohlcv_insufficient_data(temp_data_dir):
    """Test fetching with insufficient data"""
    fetcher = BotDataFetcher(data_dir=temp_data_dir)

    # XRP has only 50 candles (below MIN_CANDLES_REQUIRED=100)
    candles = fetcher.fetch_ohlcv("XRPUSDT", "1h", limit=500)

    assert len(candles) == 0  # Should return empty due to insufficient data


def test_fetch_ohlcv_no_data(temp_data_dir):
    """Test fetching non-existent symbol"""
    fetcher = BotDataFetcher(data_dir=temp_data_dir)

    candles = fetcher.fetch_ohlcv("FAKESYMBOL", "1h")

    assert len(candles) == 0


def test_get_latest_price(temp_data_dir):
    """Test getting latest price"""
    fetcher = BotDataFetcher(data_dir=temp_data_dir)

    price = fetcher.get_latest_price("BTCUSDT", "1h")

    assert price is not None
    assert price > 0
    assert isinstance(price, float)


def test_get_data_info(temp_data_dir):
    """Test getting data info"""
    fetcher = BotDataFetcher(data_dir=temp_data_dir)

    info = fetcher.get_data_info("BTCUSDT", "1h")

    assert info is not None
    assert info['rows'] == 200
    assert 'start' in info
    assert 'end' in info
    assert 'last_update' in info


def test_check_data_freshness(temp_data_dir):
    """Test checking data freshness"""
    fetcher = BotDataFetcher(data_dir=temp_data_dir)

    # Data ends at 2024-01-01 + 200 hours, so it's not fresh (old)
    is_fresh = fetcher.check_data_freshness("BTCUSDT", "1h", max_age_hours=24)

    # Should be False since test data is from 2024-01-01
    assert is_fresh == False


def test_get_data_fetcher_singleton():
    """Test singleton pattern for get_data_fetcher"""
    fetcher1 = get_data_fetcher()
    fetcher2 = get_data_fetcher()

    assert fetcher1 is fetcher2


def test_create_runner_data_fetcher(temp_data_dir):
    """Test creating runner data fetcher function"""
    fetch_func = create_runner_data_fetcher(data_dir=temp_data_dir)

    assert callable(fetch_func)

    candles = fetch_func("BTCUSDT", "1h")

    assert len(candles) > 0
    assert isinstance(candles, list)


def test_validate_data_availability(temp_data_dir):
    """Test validating data availability for multiple symbols"""
    # Need to use global fetcher with temp_data_dir
    from app.core.bots.data_integration import _global_fetcher
    import app.core.bots.data_integration as di

    # Temporarily set global fetcher
    old_fetcher = di._global_fetcher
    di._global_fetcher = BotDataFetcher(data_dir=temp_data_dir)

    try:
        symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "FAKESYMBOL"]
        results = validate_data_availability(symbols, "1h")

        assert results["BTCUSDT"] == True  # 200 candles
        assert results["ETHUSDT"] == True  # 200 candles
        assert results["XRPUSDT"] == False  # Only 50 candles
        assert results["FAKESYMBOL"] == False  # No data
    finally:
        # Restore global fetcher
        di._global_fetcher = old_fetcher


def test_get_missing_data_symbols(temp_data_dir):
    """Test getting missing data symbols"""
    from app.core.bots.data_integration import _global_fetcher
    import app.core.bots.data_integration as di

    old_fetcher = di._global_fetcher
    di._global_fetcher = BotDataFetcher(data_dir=temp_data_dir)

    try:
        symbols = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "FAKESYMBOL"]
        missing = get_missing_data_symbols(symbols, "1h")

        assert "BTCUSDT" not in missing
        assert "ETHUSDT" not in missing
        assert "XRPUSDT" in missing
        assert "FAKESYMBOL" in missing
    finally:
        di._global_fetcher = old_fetcher


def test_get_live_price_fallback(temp_data_dir):
    """Test get_live_price with Parquet fallback (no WebSocket)"""
    fetcher = BotDataFetcher(data_dir=temp_data_dir)

    # Without WebSocket cache, should fallback to Parquet
    price = fetcher.get_live_price("BTCUSDT")

    assert price is not None
    assert price > 0


def test_fetch_ohlcv_limit(temp_data_dir):
    """Test fetch_ohlcv with different limits"""
    fetcher = BotDataFetcher(data_dir=temp_data_dir)

    # Test limit=50
    candles_50 = fetcher.fetch_ohlcv("BTCUSDT", "1h", limit=50)
    assert len(candles_50) == 50

    # Test limit=150
    candles_150 = fetcher.fetch_ohlcv("BTCUSDT", "1h", limit=150)
    assert len(candles_150) == 150

    # Test limit=1000 (more than available)
    candles_all = fetcher.fetch_ohlcv("BTCUSDT", "1h", limit=1000)
    assert len(candles_all) == 200  # Only 200 available


def test_candle_data_structure(temp_data_dir):
    """Test that candles have correct data structure"""
    fetcher = BotDataFetcher(data_dir=temp_data_dir)

    candles = fetcher.fetch_ohlcv("BTCUSDT", "1h", limit=10)

    for candle in candles:
        assert isinstance(candle['timestamp'], datetime)
        assert isinstance(candle['open'], float)
        assert isinstance(candle['high'], float)
        assert isinstance(candle['low'], float)
        assert isinstance(candle['close'], float)
        assert isinstance(candle['volume'], float)

        # OHLC logic
        assert candle['high'] >= candle['low']
        assert candle['high'] >= candle['open']
        assert candle['high'] >= candle['close']
        assert candle['low'] <= candle['open']
        assert candle['low'] <= candle['close']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
