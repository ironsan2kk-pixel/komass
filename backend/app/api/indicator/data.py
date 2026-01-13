"""
Data Utilities Module
======================

Data loading, preparation, and transformation utilities.

Functions:
- find_data_dir: Find data directory
- download_single_symbol: Download historical data from Binance
- prepare_candles: Convert DataFrame to candle format for frontend
- prepare_indicators: Extract indicator data for frontend
- prepare_trade_markers: Format trade markers for chart display
- get_current_signal: Get current signal from DataFrame
"""

import aiohttp
import asyncio
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


def find_data_dir() -> Path:
    """
    Find data directory trying multiple possible locations

    Returns:
        Path object pointing to data directory
    """
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / "data",  # backend/../data
        Path("data"),  # relative
        Path("backend/data"),  # from root
        Path(__file__).parent.parent.parent / "data",  # backend/app/../data
    ]

    for path in possible_paths:
        if path.exists():
            return path

    # Default to first path and create if doesn't exist
    default = possible_paths[0]
    default.mkdir(parents=True, exist_ok=True)
    return default


async def download_single_symbol(symbol: str, timeframe: str, days: int = 365) -> bool:
    """
    Download historical data for a single symbol from Binance

    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        timeframe: Timeframe (1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d)
        days: Number of days of historical data

    Returns:
        True if successful, False otherwise
    """
    BINANCE_URL = "https://api.binance.com/api/v3/klines"

    tf_ms = {
        "1m": 60000, "5m": 300000, "15m": 900000, "30m": 1800000,
        "1h": 3600000, "2h": 7200000, "4h": 14400000, "1d": 86400000
    }
    interval_ms = tf_ms.get(timeframe, 3600000)

    end_time = int(datetime.now().timestamp() * 1000)
    start_time = end_time - (days * 24 * 60 * 60 * 1000)

    all_candles = []
    current_start = start_time

    async with aiohttp.ClientSession() as session:
        while current_start < end_time:
            params = {
                "symbol": symbol,
                "interval": timeframe,
                "startTime": current_start,
                "limit": 1000
            }

            try:
                async with session.get(BINANCE_URL, params=params, timeout=30) as response:
                    if response.status != 200:
                        break
                    data = await response.json()
                    if not data:
                        break

                    all_candles.extend(data)
                    current_start = data[-1][0] + interval_ms

                    # Rate limit
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Error downloading {symbol}: {e}")
                break

    if not all_candles:
        return False

    # Convert to DataFrame
    df = pd.DataFrame(all_candles, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_volume', 'trades', 'taker_buy_volume',
        'taker_buy_quote_volume', 'ignore'
    ])

    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)

    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)

    df = df[['open', 'high', 'low', 'close', 'volume']]
    df = df[~df.index.duplicated(keep='first')]
    df.sort_index(inplace=True)

    # Save to parquet
    data_dir = find_data_dir()
    filepath = data_dir / f"{symbol}_{timeframe}.parquet"
    df.to_parquet(filepath)
    print(f"[Data] Downloaded {symbol} {timeframe}: {len(df)} candles")

    return True


def prepare_candles(df: pd.DataFrame) -> List[Dict]:
    """
    Convert DataFrame to candle format for frontend (lightweight-charts)

    Args:
        df: DataFrame with OHLCV data and DatetimeIndex

    Returns:
        List of candle dicts with time and OHLC values
    """
    candles = []
    for idx, row in df.iterrows():
        candles.append({
            "time": idx.isoformat(),
            "open": round(float(row['open']), 8),
            "high": round(float(row['high']), 8),
            "low": round(float(row['low']), 8),
            "close": round(float(row['close']), 8),
            "volume": round(float(row.get('volume', 0)), 2)
        })
    return candles


def prepare_indicators(df: pd.DataFrame, settings: Any) -> Dict:
    """
    Extract indicator data for frontend visualization

    Args:
        df: DataFrame with calculated indicators
        settings: IndicatorSettings object

    Returns:
        Dict with indicator series data
    """
    indicators = {}

    # TRG indicator
    if 'trg_upper' in df.columns:
        indicators['trg_upper'] = [
            {"time": idx.isoformat(), "value": round(float(val), 8)}
            for idx, val in df['trg_upper'].items() if not pd.isna(val)
        ]

    if 'trg_lower' in df.columns:
        indicators['trg_lower'] = [
            {"time": idx.isoformat(), "value": round(float(val), 8)}
            for idx, val in df['trg_lower'].items() if not pd.isna(val)
        ]

    if 'trg_line' in df.columns:
        indicators['trg_line'] = [
            {"time": idx.isoformat(), "value": round(float(val), 8)}
            for idx, val in df['trg_line'].items() if not pd.isna(val)
        ]

    # SuperTrend
    if 'supertrend' in df.columns and settings.use_supertrend:
        indicators['supertrend'] = [
            {"time": idx.isoformat(), "value": round(float(val), 8)}
            for idx, val in df['supertrend'].items() if not pd.isna(val)
        ]

    # RSI
    if 'rsi' in df.columns and settings.use_rsi_filter:
        indicators['rsi'] = [
            {"time": idx.isoformat(), "value": round(float(val), 2)}
            for idx, val in df['rsi'].items() if not pd.isna(val)
        ]

    # ADX
    if 'adx' in df.columns and settings.use_adx_filter:
        indicators['adx'] = [
            {"time": idx.isoformat(), "value": round(float(val), 2)}
            for idx, val in df['adx'].items() if not pd.isna(val)
        ]

    return indicators


def prepare_trade_markers(trades: List[Dict]) -> List[Dict]:
    """
    Format trade markers for chart display

    Args:
        trades: List of trade dictionaries

    Returns:
        List of marker dicts for lightweight-charts
    """
    markers = []

    for trade in trades:
        # Entry marker
        markers.append({
            "time": trade['entry_time'],
            "position": "belowBar" if trade['type'] == 'long' else "aboveBar",
            "color": "green" if trade['type'] == 'long' else "red",
            "shape": "arrowUp" if trade['type'] == 'long' else "arrowDown",
            "text": f"Entry {trade['type'].upper()}"
        })

        # Exit marker
        color = "green" if trade.get('pnl', 0) > 0 else "red"
        markers.append({
            "time": trade['exit_time'],
            "position": "aboveBar" if trade['type'] == 'long' else "belowBar",
            "color": color,
            "shape": "circle",
            "text": f"Exit: {trade.get('exit_reason', 'Unknown')} ({trade.get('pnl', 0):.2f})"
        })

    return markers


def get_current_signal(df: pd.DataFrame) -> Dict:
    """
    Get current signal from DataFrame (last row)

    Args:
        df: DataFrame with signal column

    Returns:
        Dict with current signal information
    """
    if df.empty or 'signal' not in df.columns:
        return {"signal": 0, "trend": 0, "time": None}

    last_row = df.iloc[-1]
    return {
        "signal": int(last_row.get('signal', 0)),
        "trend": int(last_row.get('trg_trend', 0)),
        "time": df.index[-1].isoformat(),
        "close": round(float(last_row['close']), 8)
    }


# Data filtering utilities
def filter_by_date_range(df: pd.DataFrame,
                         start_date: Optional[str] = None,
                         end_date: Optional[str] = None) -> pd.DataFrame:
    """
    Filter DataFrame by date range

    Args:
        df: DataFrame with DatetimeIndex
        start_date: ISO format date string (YYYY-MM-DD)
        end_date: ISO format date string (YYYY-MM-DD)

    Returns:
        Filtered DataFrame
    """
    if start_date:
        df = df[df.index >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df.index <= pd.to_datetime(end_date)]
    return df


def resample_timeframe(df: pd.DataFrame, target_tf: str) -> pd.DataFrame:
    """
    Resample DataFrame to a different timeframe

    Args:
        df: DataFrame with OHLCV and DatetimeIndex
        target_tf: Target timeframe (5m, 15m, 1h, 4h, 1d)

    Returns:
        Resampled DataFrame
    """
    tf_map = {
        "5m": "5min", "15m": "15min", "30m": "30min",
        "1h": "1H", "2h": "2H", "4h": "4H", "1d": "1D"
    }

    freq = tf_map.get(target_tf, "1H")

    resampled = df.resample(freq).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()

    return resampled
