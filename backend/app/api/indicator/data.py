"""
Data Management
===============
Functions for loading, downloading and preparing OHLCV data.
"""
import asyncio
import aiohttp
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, TYPE_CHECKING
import os

if TYPE_CHECKING:
    from .models import IndicatorSettings


def find_data_dir() -> Path:
    """Find or create data directory"""
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / "data",  # backend/data
        Path("data"),
        Path("backend/data"),
        Path("../data"),
        Path.cwd() / "data",
        Path.cwd() / "backend" / "data",
    ]

    for p in possible_paths:
        if p.exists():
            return p

    # Default
    default = Path(__file__).parent.parent.parent.parent / "data"
    default.mkdir(exist_ok=True)
    return default


DATA_DIR = find_data_dir()
NUM_WORKERS = os.cpu_count() or 4


async def download_single_symbol(symbol: str, timeframe: str, days: int = 365) -> bool:
    """Download historical data from Binance"""
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

    # Save
    filepath = DATA_DIR / f"{symbol}_{timeframe}.parquet"
    df.to_parquet(filepath)
    print(f"[Data] Downloaded {symbol} {timeframe}: {len(df)} candles")

    return True


def load_data(symbol: str, timeframe: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
    """Load data from parquet file with optional date filtering"""
    filepath = DATA_DIR / f"{symbol}_{timeframe}.parquet"

    if not filepath.exists():
        return None

    df = pd.read_parquet(filepath)

    # Apply date filters
    if start_date:
        df = df[df.index >= start_date]
    if end_date:
        df = df[df.index <= end_date]

    return df


def prepare_candles(df: pd.DataFrame) -> List[Dict]:
    """Prepare candle data for chart"""
    candles = []
    seen_times = set()

    for timestamp, row in df.iterrows():
        time_val = int(timestamp.timestamp())

        if time_val in seen_times:
            continue
        seen_times.add(time_val)

        candles.append({
            "time": time_val,
            "open": float(row['open']),
            "high": float(row['high']),
            "low": float(row['low']),
            "close": float(row['close']),
            "volume": float(row.get('volume', 0))
        })

    candles.sort(key=lambda x: x['time'])
    return candles


def prepare_indicators(df: pd.DataFrame, settings: "IndicatorSettings") -> Dict:
    """Prepare indicator data for chart"""

    indicators = {
        "trg_upper": [],
        "trg_lower": [],
        "trg_line": []
    }

    seen_times = set()

    for timestamp, row in df.iterrows():
        time_val = int(timestamp.timestamp())

        if time_val in seen_times:
            continue
        seen_times.add(time_val)

        if pd.notna(row.get('trg_upper')):
            indicators["trg_upper"].append({"time": time_val, "value": float(row['trg_upper'])})
        if pd.notna(row.get('trg_lower')):
            indicators["trg_lower"].append({"time": time_val, "value": float(row['trg_lower'])})
        if pd.notna(row.get('trg_line')):
            indicators["trg_line"].append({"time": time_val, "value": float(row['trg_line'])})

    for key in indicators:
        indicators[key].sort(key=lambda x: x['time'])

    if settings.use_supertrend and 'supertrend' in df.columns:
        indicators["supertrend"] = []
        seen_times_st = set()

        for timestamp, row in df.iterrows():
            time_val = int(timestamp.timestamp())
            if time_val in seen_times_st:
                continue
            seen_times_st.add(time_val)

            if pd.notna(row.get('supertrend')):
                indicators["supertrend"].append({"time": time_val, "value": float(row['supertrend'])})

        indicators["supertrend"].sort(key=lambda x: x['time'])

    return indicators


def prepare_trade_markers(trades: List[Dict]) -> List[Dict]:
    """Prepare trade markers for chart"""
    markers = []

    for trade in trades:
        entry_time = int(datetime.fromisoformat(trade['entry_time']).timestamp())
        exit_time = int(datetime.fromisoformat(trade['exit_time']).timestamp())
        is_reentry = trade.get('is_reentry', False)
        is_long = trade['type'] == 'long'

        # Entry marker
        entry_text = trade['type'].upper()
        if is_reentry:
            entry_text = f"RE-{entry_text}"

        markers.append({
            "time": entry_time,
            "position": "belowBar" if is_long else "aboveBar",
            "color": "#fbbf24" if is_reentry else ("#22c55e" if is_long else "#ef4444"),
            "shape": "arrowUp" if is_long else "arrowDown",
            "text": entry_text,
            "type": f"entry_{trade['type']}"
        })

        # TP hit markers
        tps_hit = trade.get('tps_hit', trade.get('tp_hit', []))
        if tps_hit and isinstance(tps_hit, list):
            duration = exit_time - entry_time
            for i, tp_num in enumerate(tps_hit):
                if isinstance(tp_num, int) and tp_num > 0:
                    tp_time = entry_time + int(duration * (i + 1) / (len(tps_hit) + 1))
                    markers.append({
                        "time": tp_time,
                        "position": "aboveBar" if is_long else "belowBar",
                        "color": "#22c55e",
                        "shape": "circle",
                        "text": f"TP{tp_num}",
                        "type": f"tp_hit_{tp_num}"
                    })

        # Exit marker
        exit_reason = trade.get('exit_reason', '')
        is_sl = exit_reason.upper() == 'SL'
        pnl = trade.get('pnl', 0)

        markers.append({
            "time": exit_time,
            "position": "aboveBar" if is_long else "belowBar",
            "color": "#ef4444" if is_sl else ("#22c55e" if pnl > 0 else "#ef4444"),
            "shape": "square" if is_sl else "circle",
            "text": f"SL {pnl:+.1f}%" if is_sl else f"{pnl:+.1f}%",
            "type": f"exit_{exit_reason}"
        })

    markers.sort(key=lambda x: x['time'])
    return markers


def get_current_signal(df: pd.DataFrame) -> Dict:
    """Get current signal state from last candle"""
    last = df.iloc[-1]
    return {
        "signal": int(last.get('signal', 0)),
        "trg_trend": int(last.get('trg_trend', 0)),
        "close": float(last['close']),
        "trg_line": float(last.get('trg_line', 0))
    }


def get_data_range(df: pd.DataFrame) -> Dict:
    """Get data range information"""
    return {
        "start": df.index[0].isoformat() if len(df) > 0 else None,
        "end": df.index[-1].isoformat() if len(df) > 0 else None,
        "candles": len(df),
        "used_start": df.index[0].strftime("%Y-%m-%d") if len(df) > 0 else None,
        "used_end": df.index[-1].strftime("%Y-%m-%d") if len(df) > 0 else None,
        "used_candles": len(df)
    }
