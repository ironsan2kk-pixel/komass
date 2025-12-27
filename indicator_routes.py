"""
Komas Trading Server - Indicator API
====================================
Full indicator calculation with trades, stats, equity
With LRU Cache (TTL 5 min, max 100 entries)
"""
import asyncio
import numpy as np
import pandas as pd
import aiohttp
import hashlib
import json
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
from collections import OrderedDict

router = APIRouter(prefix="/api/indicator", tags=["Indicator"])


# ============================================================================
# LRU CACHE WITH TTL
# ============================================================================
class LRUCache:
    """
    Thread-safe LRU Cache with TTL
    - Max 100 entries
    - TTL 5 minutes (300 seconds)
    """
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0
    
    def _make_key(self, settings: dict) -> str:
        """Create hash key from settings (excluding force_recalculate)"""
        # Remove force_recalculate from settings for hashing
        settings_copy = {k: v for k, v in settings.items() if k != 'force_recalculate'}
        # Sort keys for consistent hashing
        sorted_json = json.dumps(settings_copy, sort_keys=True)
        return hashlib.md5(sorted_json.encode()).hexdigest()
    
    def get(self, settings: dict) -> Optional[dict]:
        """Get value from cache if exists and not expired"""
        key = self._make_key(settings)
        
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None
            
            # Check TTL
            if time.time() - self.timestamps[key] > self.ttl_seconds:
                # Expired - remove
                del self.cache[key]
                del self.timestamps[key]
                self.misses += 1
                return None
            
            # Move to end (LRU)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]
    
    def set(self, settings: dict, value: dict):
        """Set value in cache"""
        key = self._make_key(settings)
        
        with self.lock:
            # Remove oldest if at capacity
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
            
            self.cache[key] = value
            self.timestamps[key] = time.time()
            self.cache.move_to_end(key)
    
    def clear(self):
        """Clear all cache entries"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def stats(self) -> dict:
        """Get cache statistics"""
        with self.lock:
            # Count non-expired entries
            now = time.time()
            valid_entries = sum(1 for k, ts in self.timestamps.items() 
                               if now - ts <= self.ttl_seconds)
            
            total_requests = self.hits + self.misses
            hit_rate = round(self.hits / total_requests * 100, 1) if total_requests > 0 else 0
            
            return {
                "entries": valid_entries,
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate
            }


# Global cache instance
calculation_cache = LRUCache(max_size=100, ttl_seconds=300)


# ============================================================================
# CACHE ENDPOINTS
# ============================================================================
@router.get("/cache-stats")
async def get_cache_stats():
    """Get cache statistics"""
    return {
        "success": True,
        **calculation_cache.stats()
    }


@router.post("/cache-clear")
async def clear_cache():
    """Clear all cache entries"""
    calculation_cache.clear()
    return {
        "success": True,
        "message": "Cache cleared"
    }


# ============================================================================
# DATA DIRECTORY
# ============================================================================
def find_data_dir():
    possible_paths = [
        Path(__file__).parent.parent.parent / "data",  # backend/data
        Path("data"),  # relative
        Path("backend/data"),  # from root
        Path("../data"),  # from backend
        Path.cwd() / "data",  # current dir / data
        Path.cwd() / "backend" / "data",  # current dir / backend / data
    ]
    
    for p in possible_paths:
        if p.exists():
            print(f"[Indicator] Found DATA_DIR: {p.absolute()}")
            return p
    
    # Default
    default = Path(__file__).parent.parent.parent / "data"
    default.mkdir(exist_ok=True)
    print(f"[Indicator] Created DATA_DIR: {default.absolute()}")
    return default

DATA_DIR = find_data_dir()


async def download_single_symbol(symbol: str, timeframe: str, days: int = 365):
    """Download historical data for a single symbol"""
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
    
    # Save
    filepath = DATA_DIR / f"{symbol}_{timeframe}.parquet"
    df.to_parquet(filepath)
    print(f"[Indicator] Downloaded {symbol} {timeframe}: {len(df)} candles")
    
    return True


class IndicatorSettings(BaseModel):
    # Data
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    # Cache control
    force_recalculate: bool = False  # Force bypass cache
    
    # TRG
    trg_atr_length: int = 45
    trg_multiplier: float = 4.0
    
    # Take Profits
    tp_count: int = 4
    tp1_percent: float = 1.05
    tp2_percent: float = 1.95
    tp3_percent: float = 3.75
    tp4_percent: float = 6.0
    tp5_percent: float = 8.0
    tp6_percent: float = 10.0
    tp7_percent: float = 12.0
    tp8_percent: float = 15.0
    tp9_percent: float = 18.0
    tp10_percent: float = 20.0
    
    tp1_amount: float = 50.0
    tp2_amount: float = 30.0
    tp3_amount: float = 15.0
    tp4_amount: float = 5.0
    tp5_amount: float = 0.0
    tp6_amount: float = 0.0
    tp7_amount: float = 0.0
    tp8_amount: float = 0.0
    tp9_amount: float = 0.0
    tp10_amount: float = 0.0
    
    # Stop Loss
    sl_percent: float = 6.0
    sl_trailing_mode: str = "breakeven"  # no, breakeven, moving
    
    # Leverage & Commission
    leverage: float = 1.0  # 1x = spot, 10x = 10x leverage
    use_commission: bool = False  # Enable/disable commission
    commission_percent: float = 0.1  # Commission per trade (0.1% = spot, 0.04% = futures maker)
    
    # Filters
    use_supertrend: bool = False
    supertrend_period: int = 10
    supertrend_multiplier: float = 3.0
    
    use_rsi_filter: bool = False
    rsi_period: int = 14
    rsi_overbought: int = 70
    rsi_oversold: int = 30
    
    use_adx_filter: bool = False
    adx_period: int = 14
    adx_threshold: int = 25
    
    use_volume_filter: bool = False
    volume_ma_period: int = 20
    volume_threshold: float = 1.5
    
    # Re-entry
    allow_reentry: bool = True
    reentry_after_sl: bool = True
    reentry_after_tp: bool = False
    
    # Adaptive optimization (during backtest)
    adaptive_mode: Optional[str] = None  # None, "indicator", "tp", "all"
    
    # Capital
    initial_capital: float = 10000.0


class ReplayRequest(BaseModel):
    settings: IndicatorSettings
    step: int = 0  # 0 = all, >0 = up to candle N


@router.post("/calculate")
async def calculate_indicator(settings: IndicatorSettings):
    """Calculate full indicator with all trades and statistics"""
    
    # Check cache first (unless force_recalculate)
    settings_dict = settings.dict()
    
    if not settings.force_recalculate:
        cached_result = calculation_cache.get(settings_dict)
        if cached_result is not None:
            print(f"[Cache] HIT for {settings.symbol} {settings.timeframe}")
            # Add cache status to result
            cached_result["cached"] = True
            return cached_result
    
    print(f"[Cache] {'FORCE RECALC' if settings.force_recalculate else 'MISS'} for {settings.symbol} {settings.timeframe}")
    
    # Load data
    filepath = DATA_DIR / f"{settings.symbol}_{settings.timeframe}.parquet"
    if not filepath.exists():
        # Try to download automatically
        try:
            await download_single_symbol(settings.symbol, settings.timeframe)
            # Check again after download
            if not filepath.exists():
                raise HTTPException(404, f"Данные не найдены для {settings.symbol} {settings.timeframe}. Перейдите в раздел 'Данные' и скачайте историю.")
        except Exception as e:
            raise HTTPException(404, f"Данные не найдены для {settings.symbol} {settings.timeframe}. Перейдите в раздел 'Данные' и скачайте историю. Ошибка: {str(e)}")
    
    df = pd.read_parquet(filepath)
    
    # Remove duplicates and sort
    df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()
    
    # Filter by date
    if settings.start_date:
        df = df[df.index >= settings.start_date]
    if settings.end_date:
        df = df[df.index <= settings.end_date]
    
    if len(df) < 100:
        raise HTTPException(400, "Not enough data (need at least 100 candles)")
    
    # Calculate indicators
    df = calculate_trg(df, settings.trg_atr_length, settings.trg_multiplier)
    
    if settings.use_supertrend:
        df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
    
    if settings.use_rsi_filter:
        df = calculate_rsi(df, settings.rsi_period)
    
    if settings.use_adx_filter:
        df = calculate_adx(df, settings.adx_period)
    
    # Generate signals
    df = generate_signals(df, settings)
    
    # Debug: count signals
    long_signals = (df['signal'] == 1).sum()
    short_signals = (df['signal'] == -1).sum()
    trend_changes = (df['trg_trend'] != df['trg_trend'].shift(1)).sum()
    
    print(f"[DEBUG] Candles: {len(df)}, TRG trend changes: {trend_changes}, Long signals: {long_signals}, Short signals: {short_signals}")
    
    # Run backtest with optional adaptive optimization
    trades, equity_curve, tp_stats, monthly_stats, param_changes = run_backtest(
        df, settings, adaptive_mode=settings.adaptive_mode
    )
    
    # Calculate statistics
    stats = calculate_statistics(trades, equity_curve, settings, monthly_stats)
    
    # Prepare chart data
    candles = prepare_candles(df)
    indicators = prepare_indicators(df, settings)
    trade_markers = prepare_trade_markers(trades)
    
    result = {
        "success": True,
        "cached": False,  # Fresh calculation
        "candles": candles,
        "indicators": indicators,
        "trades": trades,
        "trade_markers": trade_markers,
        "equity_curve": equity_curve,
        "stats": stats,
        "tp_stats": tp_stats,
        "monthly": monthly_stats,
        "param_changes": param_changes,
        "settings": settings.dict()
    }
    
    # Store in cache
    calculation_cache.set(settings_dict, result)
    
    return result


@router.get("/candles/{symbol}/{timeframe}")
async def get_candles(symbol: str, timeframe: str):
    """Get candles only for initial chart display"""
    
    filepath = DATA_DIR / f"{symbol}_{timeframe}.parquet"
    if not filepath.exists():
        raise HTTPException(404, f"Data not found for {symbol} {timeframe}")
    
    df = pd.read_parquet(filepath)
    df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()
    
    candles = prepare_candles(df)
    return {"success": True, "candles": candles}


# ============================================================================
# INDICATOR CALCULATIONS
# ============================================================================

def calculate_trg(df: pd.DataFrame, atr_length: int, multiplier: float) -> pd.DataFrame:
    """Calculate TRG indicator (ATR-based trend detection)"""
    df = df.copy()
    
    # ATR calculation
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=atr_length).mean()
    
    df['atr'] = atr
    df['trg_upper'] = close + atr * multiplier
    df['trg_lower'] = close - atr * multiplier
    
    # TRG Line calculation with trend
    trg_line = np.zeros(len(df))
    trg_trend = np.zeros(len(df))
    
    for i in range(1, len(df)):
        prev_trg = trg_line[i-1] if i > 0 else close.iloc[i]
        prev_trend = trg_trend[i-1] if i > 0 else 0
        
        upper = df['trg_upper'].iloc[i]
        lower = df['trg_lower'].iloc[i]
        current_close = close.iloc[i]
        
        if pd.isna(upper) or pd.isna(lower):
            trg_line[i] = prev_trg
            trg_trend[i] = prev_trend
            continue
        
        if current_close > prev_trg:
            trg_line[i] = max(lower, prev_trg)
            trg_trend[i] = 1
        elif current_close < prev_trg:
            trg_line[i] = min(upper, prev_trg)
            trg_trend[i] = -1
        else:
            trg_line[i] = prev_trg
            trg_trend[i] = prev_trend
    
    df['trg_line'] = trg_line
    df['trg_trend'] = trg_trend
    
    return df


def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """Calculate SuperTrend indicator"""
    df = df.copy()
    
    high = df['high']
    low = df['low']
    close = df['close']
    
    # ATR for SuperTrend
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    hl2 = (high + low) / 2
    upper_band = hl2 + multiplier * atr
    lower_band = hl2 - multiplier * atr
    
    supertrend = np.zeros(len(df))
    direction = np.zeros(len(df))
    
    for i in range(1, len(df)):
        if pd.isna(upper_band.iloc[i]) or pd.isna(lower_band.iloc[i]):
            supertrend[i] = supertrend[i-1]
            direction[i] = direction[i-1]
            continue
            
        if close.iloc[i] > supertrend[i-1]:
            supertrend[i] = lower_band.iloc[i]
            direction[i] = 1
        elif close.iloc[i] < supertrend[i-1]:
            supertrend[i] = upper_band.iloc[i]
            direction[i] = -1
        else:
            supertrend[i] = supertrend[i-1]
            direction[i] = direction[i-1]
            
            if direction[i] == 1 and lower_band.iloc[i] > supertrend[i]:
                supertrend[i] = lower_band.iloc[i]
            if direction[i] == -1 and upper_band.iloc[i] < supertrend[i]:
                supertrend[i] = upper_band.iloc[i]
    
    df['supertrend'] = supertrend
    df['supertrend_dir'] = direction
    
    return df


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculate RSI indicator"""
    df = df.copy()
    
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    return df


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculate ADX indicator"""
    df = df.copy()
    
    high = df['high']
    low = df['low']
    close = df['close']
    
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    df['adx'] = dx.rolling(window=period).mean()
    df['plus_di'] = plus_di
    df['minus_di'] = minus_di
    
    return df


def generate_signals(df: pd.DataFrame, settings: IndicatorSettings) -> pd.DataFrame:
    """Generate trading signals based on TRG and filters"""
    df = df.copy()
    df['signal'] = 0
    
    # TRG trend changes
    trend_change = df['trg_trend'] != df['trg_trend'].shift(1)
    
    for i in range(1, len(df)):
        if not trend_change.iloc[i]:
            continue
            
        signal = 0
        current_trend = df['trg_trend'].iloc[i]
        
        if current_trend == 1:  # Bullish
            signal = 1
        elif current_trend == -1:  # Bearish
            signal = -1
        
        # Apply filters
        if signal != 0:
            # SuperTrend filter
            if settings.use_supertrend and 'supertrend_dir' in df.columns:
                st_dir = df['supertrend_dir'].iloc[i]
                if signal == 1 and st_dir != 1:
                    signal = 0
                if signal == -1 and st_dir != -1:
                    signal = 0
            
            # RSI filter
            if settings.use_rsi_filter and 'rsi' in df.columns:
                rsi = df['rsi'].iloc[i]
                if not pd.isna(rsi):
                    if signal == 1 and rsi > settings.rsi_overbought:
                        signal = 0
                    if signal == -1 and rsi < settings.rsi_oversold:
                        signal = 0
            
            # ADX filter
            if settings.use_adx_filter and 'adx' in df.columns:
                adx = df['adx'].iloc[i]
                if not pd.isna(adx) and adx < settings.adx_threshold:
                    signal = 0
            
            # Volume filter
            if settings.use_volume_filter:
                vol = df['volume'].iloc[i]
                vol_ma = df['volume'].rolling(window=settings.volume_ma_period).mean().iloc[i]
                if not pd.isna(vol_ma) and vol < vol_ma * settings.volume_threshold:
                    signal = 0
        
        df.iloc[i, df.columns.get_loc('signal')] = signal
    
    return df


def run_backtest(df: pd.DataFrame, settings: IndicatorSettings, adaptive_mode: Optional[str] = None):
    """Run backtest simulation"""
    trades = []
    equity_curve = []
    tp_stats = {}
    monthly_stats = {}
    param_changes = []
    
    capital = settings.initial_capital
    position = None
    
    # TP percentages and amounts
    tp_percents = [
        settings.tp1_percent, settings.tp2_percent, settings.tp3_percent,
        settings.tp4_percent, settings.tp5_percent, settings.tp6_percent,
        settings.tp7_percent, settings.tp8_percent, settings.tp9_percent,
        settings.tp10_percent
    ][:settings.tp_count]
    
    tp_amounts = [
        settings.tp1_amount, settings.tp2_amount, settings.tp3_amount,
        settings.tp4_amount, settings.tp5_amount, settings.tp6_amount,
        settings.tp7_amount, settings.tp8_amount, settings.tp9_amount,
        settings.tp10_amount
    ][:settings.tp_count]
    
    # Normalize TP amounts
    total_amount = sum(tp_amounts) if sum(tp_amounts) > 0 else 100
    tp_amounts_norm = [a / total_amount * 100 for a in tp_amounts]
    
    last_exit_reason = None
    trade_count_for_adaptive = 0
    
    for i in range(len(df)):
        timestamp = df.index[i]
        row = df.iloc[i]
        close = row['close']
        signal = row.get('signal', 0)
        
        # Track monthly stats
        month_key = timestamp.strftime('%Y-%m')
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {'trades': 0, 'wins': 0, 'pnl': 0}
        
        # Check for position exit
        if position is not None:
            exit_reason = None
            exit_price = None
            pnl = 0
            tp_hit_list = []
            
            # Calculate unrealized PnL
            if position['type'] == 'long':
                unrealized = (close - position['entry_price']) / position['entry_price'] * 100 * settings.leverage
            else:
                unrealized = (position['entry_price'] - close) / position['entry_price'] * 100 * settings.leverage
            
            # Check Stop Loss
            sl_price = position.get('sl_price')
            if sl_price:
                if position['type'] == 'long' and close <= sl_price:
                    exit_reason = 'sl'
                    exit_price = sl_price
                elif position['type'] == 'short' and close >= sl_price:
                    exit_reason = 'sl'
                    exit_price = sl_price
            
            # Check Take Profits
            if exit_reason is None:
                for tp_idx, (tp_pct, tp_amt) in enumerate(zip(tp_percents, tp_amounts_norm)):
                    if tp_idx + 1 in position.get('tp_hit', []):
                        continue
                    
                    if position['type'] == 'long':
                        tp_price = position['entry_price'] * (1 + tp_pct / 100)
                        if close >= tp_price:
                            tp_hit_list.append(tp_idx + 1)
                            pnl += tp_pct * (tp_amt / 100) * settings.leverage
                            
                            # Update SL on breakeven mode
                            if settings.sl_trailing_mode == 'breakeven' and tp_idx == 0:
                                position['sl_price'] = position['entry_price']
                            elif settings.sl_trailing_mode == 'moving':
                                position['sl_price'] = tp_price * 0.99
                    else:
                        tp_price = position['entry_price'] * (1 - tp_pct / 100)
                        if close <= tp_price:
                            tp_hit_list.append(tp_idx + 1)
                            pnl += tp_pct * (tp_amt / 100) * settings.leverage
                            
                            if settings.sl_trailing_mode == 'breakeven' and tp_idx == 0:
                                position['sl_price'] = position['entry_price']
                            elif settings.sl_trailing_mode == 'moving':
                                position['sl_price'] = tp_price * 1.01
                
                if tp_hit_list:
                    position['tp_hit'] = position.get('tp_hit', []) + tp_hit_list
                    
                    # Check if all TPs hit
                    if len(position['tp_hit']) >= settings.tp_count:
                        exit_reason = 'tp'
                        exit_price = close
            
            # Check for signal reversal
            if exit_reason is None and signal != 0 and signal != (1 if position['type'] == 'long' else -1):
                exit_reason = 'signal'
                exit_price = close
                # Calculate PnL for remaining position
                remaining = 100 - sum(tp_amounts_norm[tp-1] for tp in position.get('tp_hit', []))
                if remaining > 0:
                    pnl += unrealized * (remaining / 100)
            
            # Exit position
            if exit_reason:
                if exit_reason == 'sl':
                    sl_pct = settings.sl_percent * settings.leverage
                    pnl = -sl_pct
                
                # Apply commission
                if settings.use_commission:
                    pnl -= settings.commission_percent * 2  # Entry + exit
                
                # Update capital
                capital_change = capital * pnl / 100
                capital += capital_change
                
                trade = {
                    'entry_time': position['entry_time'].isoformat(),
                    'exit_time': timestamp.isoformat(),
                    'type': position['type'],
                    'entry_price': position['entry_price'],
                    'exit_price': exit_price or close,
                    'pnl': round(pnl, 2),
                    'exit_reason': exit_reason,
                    'tp_hit': position.get('tp_hit', []),
                    'is_reentry': position.get('is_reentry', False)
                }
                trades.append(trade)
                
                # Update monthly stats
                monthly_stats[month_key]['trades'] += 1
                monthly_stats[month_key]['pnl'] += pnl
                if pnl > 0:
                    monthly_stats[month_key]['wins'] += 1
                
                last_exit_reason = exit_reason
                position = None
                trade_count_for_adaptive += 1
        
        # Check for new position entry
        if position is None and signal != 0:
            # Re-entry logic
            can_enter = True
            is_reentry = False
            
            if last_exit_reason == 'sl' and not settings.reentry_after_sl:
                if settings.allow_reentry:
                    is_reentry = True
                else:
                    can_enter = False
            elif last_exit_reason == 'tp' and not settings.reentry_after_tp:
                if settings.allow_reentry:
                    is_reentry = True
                else:
                    can_enter = False
            
            if can_enter:
                entry_price = close
                
                # Calculate SL price
                if signal == 1:  # Long
                    sl_price = entry_price * (1 - settings.sl_percent / 100)
                else:  # Short
                    sl_price = entry_price * (1 + settings.sl_percent / 100)
                
                position = {
                    'type': 'long' if signal == 1 else 'short',
                    'entry_time': timestamp,
                    'entry_price': entry_price,
                    'sl_price': sl_price,
                    'tp_hit': [],
                    'is_reentry': is_reentry
                }
        
        # Update equity curve
        equity_value = capital
        if position is not None:
            if position['type'] == 'long':
                unrealized = (close - position['entry_price']) / position['entry_price'] * 100 * settings.leverage
            else:
                unrealized = (position['entry_price'] - close) / position['entry_price'] * 100 * settings.leverage
            equity_value = capital + capital * unrealized / 100
        
        equity_curve.append({
            'time': timestamp.isoformat(),
            'value': round(equity_value, 2)
        })
    
    return trades, equity_curve, tp_stats, monthly_stats, param_changes


def calculate_statistics(trades: List[Dict], equity_curve: List[Dict], settings: IndicatorSettings, monthly_stats: Dict) -> Dict:
    """Calculate trading statistics"""
    if not trades:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "avg_win": 0,
            "avg_loss": 0,
            "profit_factor": 0,
            "max_drawdown": 0,
            "initial_capital": settings.initial_capital,
            "final_capital": settings.initial_capital,
            "profit_pct": 0
        }
    
    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    
    long_trades = [t for t in trades if t['type'] == 'long']
    short_trades = [t for t in trades if t['type'] == 'short']
    reentry_trades = [t for t in trades if t.get('is_reentry', False)]
    
    long_wins = sum(1 for t in long_trades if t['pnl'] > 0)
    short_wins = sum(1 for t in short_trades if t['pnl'] > 0)
    reentry_wins = sum(1 for t in reentry_trades if t['pnl'] > 0)
    
    # Accuracy calculation
    accuracy = {}
    for period_name, period_size in [('last_5', 5), ('last_10', 10), ('last_20', 20), ('last_50', 50), ('last_100', 100)]:
        recent = trades[-period_size:] if len(trades) >= period_size else trades
        accuracy[period_name] = {}
        for tp_num in range(1, settings.tp_count + 1):
            tp_hits = sum(1 for t in recent if tp_num in t.get('tp_hit', []))
            accuracy[period_name][f'tp{tp_num}'] = round(tp_hits / len(recent) * 100) if recent else 0
    
    accuracy['total'] = {}
    for tp_num in range(1, settings.tp_count + 1):
        tp_hits = sum(1 for t in trades if tp_num in t.get('tp_hit', []))
        accuracy['total'][f'tp{tp_num}'] = round(tp_hits / len(trades) * 100) if trades else 0
    
    # Profit panel
    profit_panel = {}
    tp_amounts_list = [
        settings.tp1_amount, settings.tp2_amount, settings.tp3_amount,
        settings.tp4_amount, settings.tp5_amount, settings.tp6_amount,
        settings.tp7_amount, settings.tp8_amount, settings.tp9_amount,
        settings.tp10_amount
    ][:settings.tp_count]
    
    tp_percents = [
        settings.tp1_percent, settings.tp2_percent, settings.tp3_percent,
        settings.tp4_percent, settings.tp5_percent, settings.tp6_percent,
        settings.tp7_percent, settings.tp8_percent, settings.tp9_percent,
        settings.tp10_percent
    ][:settings.tp_count]
    
    total_amount = sum(tp_amounts_list) if sum(tp_amounts_list) > 0 else 100
    tp_amounts_normalized = [a / total_amount * 100 for a in tp_amounts_list]
    
    for tp_num in range(1, settings.tp_count + 1):
        tp_hit_trades = [t for t in trades if tp_num in t.get('tp_hit', [])]
        tp_missed_trades = [t for t in trades if tp_num not in t.get('tp_hit', [])]
        
        tp_profit = 0
        for t in tp_hit_trades:
            tp_profit += tp_percents[tp_num - 1] * (tp_amounts_normalized[tp_num - 1] / 100)
        
        tp_loss = 0
        for t in tp_missed_trades:
            if t['pnl'] < 0:
                tp_loss += t['pnl'] * (tp_amounts_normalized[tp_num - 1] / 100)
        
        profit_panel[f"tp{tp_num}"] = {
            "winning": len(tp_hit_trades),
            "total": len(trades),
            "profit": round(tp_profit, 2),
            "loss": round(tp_loss, 2),
            "final": round(tp_profit + tp_loss, 2)
        }
    
    # Max drawdown
    peak = settings.initial_capital
    max_dd = 0
    for eq in equity_curve:
        if eq['value'] > peak:
            peak = eq['value']
        dd = (peak - eq['value']) / peak * 100
        if dd > max_dd:
            max_dd = dd
    
    # Sharpe ratio
    sharpe = None
    if len(equity_curve) > 1:
        returns = []
        for i in range(1, len(equity_curve)):
            prev_val = equity_curve[i-1]['value']
            curr_val = equity_curve[i]['value']
            if prev_val > 0:
                returns.append((curr_val - prev_val) / prev_val)
        if returns:
            avg_return = sum(returns) / len(returns)
            std_return = (sum((r - avg_return)**2 for r in returns) / len(returns)) ** 0.5
            if std_return > 0:
                sharpe = round((avg_return / std_return) * (252 ** 0.5), 2)
    
    # Recovery factor
    total_profit = equity_curve[-1]['value'] - settings.initial_capital if equity_curve else 0
    recovery_factor = round(total_profit / (settings.initial_capital * max_dd / 100), 2) if max_dd > 0 else None
    
    return {
        "total_trades": len(trades),
        "winning_trades": len(wins),
        "losing_trades": len(losses),
        "win_rate": round(len(wins) / len(trades) * 100, 2) if trades else 0,
        "total_pnl": round(sum(pnls), 2),
        "avg_win": round(sum(wins) / len(wins), 2) if wins else 0,
        "avg_loss": round(sum(losses) / len(losses), 2) if losses else 0,
        "profit_factor": round(sum(wins) / abs(sum(losses)), 2) if losses and sum(losses) != 0 else 999,
        "max_drawdown": round(max_dd, 2),
        "initial_capital": settings.initial_capital,
        "final_capital": round(equity_curve[-1]['value'], 2) if equity_curve else settings.initial_capital,
        "profit_pct": round((equity_curve[-1]['value'] / settings.initial_capital - 1) * 100, 2) if equity_curve else 0,
        "sharpe": sharpe,
        "recovery_factor": recovery_factor,
        "long_trades": len(long_trades),
        "long_wins": long_wins,
        "long_win_rate": round(long_wins / len(long_trades) * 100, 2) if long_trades else 0,
        "short_trades": len(short_trades),
        "short_wins": short_wins,
        "short_win_rate": round(short_wins / len(short_trades) * 100, 2) if short_trades else 0,
        "reentry_trades": len(reentry_trades),
        "reentry_wins": reentry_wins,
        "reentry_win_rate": round(reentry_wins / len(reentry_trades) * 100, 2) if reentry_trades else 0,
        "accuracy": accuracy,
        "profit_panel": profit_panel
    }


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


def prepare_indicators(df: pd.DataFrame, settings: IndicatorSettings) -> Dict:
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
                indicators["supertrend"].append({
                    "time": time_val,
                    "value": float(row['supertrend']),
                    "color": "#00ff00" if row.get('supertrend_dir', 0) == 1 else "#ff0000"
                })
        indicators["supertrend"].sort(key=lambda x: x['time'])
    
    return indicators


def prepare_trade_markers(trades: List[Dict]) -> List[Dict]:
    """Prepare trade markers for chart"""
    markers = []
    
    for trade in trades:
        entry_time = int(datetime.fromisoformat(trade['entry_time']).timestamp())
        exit_time = int(datetime.fromisoformat(trade['exit_time']).timestamp())
        is_reentry = trade.get('is_reentry', False)
        
        entry_text = trade['type'].upper()
        if is_reentry:
            entry_text = f"RE-{entry_text}"
        
        markers.append({
            "time": entry_time,
            "position": "belowBar" if trade['type'] == 'long' else "aboveBar",
            "color": "#fbbf24" if is_reentry else ("#22c55e" if trade['type'] == 'long' else "#ef4444"),
            "shape": "arrowUp" if trade['type'] == 'long' else "arrowDown",
            "text": entry_text
        })
        
        markers.append({
            "time": exit_time,
            "position": "aboveBar" if trade['type'] == 'long' else "belowBar",
            "color": "#22c55e" if trade['pnl'] > 0 else "#ef4444",
            "shape": "circle",
            "text": f"{trade['pnl']:+.1f}%"
        })
    
    markers.sort(key=lambda x: x['time'])
    
    return markers


def get_current_signal(df: pd.DataFrame) -> Dict:
    """Get current signal state"""
    last = df.iloc[-1]
    return {
        "signal": int(last.get('signal', 0)),
        "trg_trend": int(last.get('trg_trend', 0)),
        "close": last['close'],
        "trg_line": last.get('trg_line', 0)
    }


# ============================================================================
# HEATMAP
# ============================================================================

class HeatmapRequest(BaseModel):
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    i1_min: int = 20
    i1_max: int = 80
    i1_step: int = 5
    i2_min: float = 2.0
    i2_max: float = 8.0
    i2_step: float = 1.0
    
    # Copy other settings
    tp_count: int = 4
    tp1_percent: float = 1.05
    tp2_percent: float = 1.95
    tp3_percent: float = 3.75
    tp4_percent: float = 6.0
    tp5_percent: float = 8.0
    tp6_percent: float = 10.0
    tp7_percent: float = 12.0
    tp8_percent: float = 15.0
    tp9_percent: float = 18.0
    tp10_percent: float = 20.0
    
    tp1_amount: float = 50.0
    tp2_amount: float = 30.0
    tp3_amount: float = 15.0
    tp4_amount: float = 5.0
    tp5_amount: float = 0.0
    tp6_amount: float = 0.0
    tp7_amount: float = 0.0
    tp8_amount: float = 0.0
    tp9_amount: float = 0.0
    tp10_amount: float = 0.0
    
    sl_percent: float = 6.0
    sl_trailing_mode: str = "breakeven"
    leverage: float = 1.0
    use_commission: bool = False
    commission_percent: float = 0.1
    initial_capital: float = 10000.0


@router.post("/heatmap")
async def generate_heatmap(request: HeatmapRequest):
    """Generate heatmap for i1/i2 parameter combinations"""
    
    filepath = DATA_DIR / f"{request.symbol}_{request.timeframe}.parquet"
    if not filepath.exists():
        raise HTTPException(404, f"Data not found for {request.symbol} {request.timeframe}")
    
    df = pd.read_parquet(filepath)
    df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()
    
    results = []
    best_result = None
    best_profit = float('-inf')
    
    i1_values = list(range(request.i1_min, request.i1_max + 1, request.i1_step))
    i2_values = []
    current_i2 = request.i2_min
    while current_i2 <= request.i2_max:
        i2_values.append(round(current_i2, 1))
        current_i2 += request.i2_step
    
    for i1 in i1_values:
        for i2 in i2_values:
            settings = IndicatorSettings(
                symbol=request.symbol,
                timeframe=request.timeframe,
                trg_atr_length=i1,
                trg_multiplier=i2,
                tp_count=request.tp_count,
                tp1_percent=request.tp1_percent,
                tp2_percent=request.tp2_percent,
                tp3_percent=request.tp3_percent,
                tp4_percent=request.tp4_percent,
                tp5_percent=request.tp5_percent,
                tp6_percent=request.tp6_percent,
                tp7_percent=request.tp7_percent,
                tp8_percent=request.tp8_percent,
                tp9_percent=request.tp9_percent,
                tp10_percent=request.tp10_percent,
                tp1_amount=request.tp1_amount,
                tp2_amount=request.tp2_amount,
                tp3_amount=request.tp3_amount,
                tp4_amount=request.tp4_amount,
                tp5_amount=request.tp5_amount,
                tp6_amount=request.tp6_amount,
                tp7_amount=request.tp7_amount,
                tp8_amount=request.tp8_amount,
                tp9_amount=request.tp9_amount,
                tp10_amount=request.tp10_amount,
                sl_percent=request.sl_percent,
                sl_trailing_mode=request.sl_trailing_mode,
                leverage=request.leverage,
                use_commission=request.use_commission,
                commission_percent=request.commission_percent,
                initial_capital=request.initial_capital
            )
            
            try:
                df_calc = calculate_trg(df.copy(), i1, i2)
                df_calc = generate_signals(df_calc, settings)
                trades, equity_curve, _, _, _ = run_backtest(df_calc, settings)
                
                if equity_curve:
                    profit_pct = round((equity_curve[-1]['value'] / request.initial_capital - 1) * 100, 2)
                else:
                    profit_pct = 0
                
                win_rate = round(len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100, 1) if trades else 0
                
                results.append({
                    'i1': i1,
                    'i2': i2,
                    'profit': profit_pct,
                    'win_rate': win_rate,
                    'trades': len(trades)
                })
                
                if profit_pct > best_profit:
                    best_profit = profit_pct
                    best_result = {'i1': i1, 'i2': i2, 'profit': profit_pct, 'win_rate': win_rate}
                    
            except Exception as e:
                print(f"Heatmap error for i1={i1}, i2={i2}: {e}")
                continue
    
    return {
        "success": True,
        "results": results,
        "best": best_result,
        "i1_values": i1_values,
        "i2_values": i2_values
    }


# ============================================================================
# AUTO-OPTIMIZE (SSE)
# ============================================================================

from fastapi.responses import StreamingResponse
import json as json_module


class OptimizeRequest(BaseModel):
    mode: str = "indicator"  # indicator, tp, sl, filters, full
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    
    # Current settings to use as base
    trg_atr_length: int = 45
    trg_multiplier: float = 4.0
    tp_count: int = 4
    tp1_percent: float = 1.05
    tp2_percent: float = 1.95
    tp3_percent: float = 3.75
    tp4_percent: float = 6.0
    tp5_percent: float = 8.0
    tp6_percent: float = 10.0
    tp7_percent: float = 12.0
    tp8_percent: float = 15.0
    tp9_percent: float = 18.0
    tp10_percent: float = 20.0
    tp1_amount: float = 50.0
    tp2_amount: float = 30.0
    tp3_amount: float = 15.0
    tp4_amount: float = 5.0
    tp5_amount: float = 0.0
    tp6_amount: float = 0.0
    tp7_amount: float = 0.0
    tp8_amount: float = 0.0
    tp9_amount: float = 0.0
    tp10_amount: float = 0.0
    sl_percent: float = 6.0
    sl_trailing_mode: str = "breakeven"
    leverage: float = 1.0
    use_commission: bool = False
    commission_percent: float = 0.1
    initial_capital: float = 10000.0
    use_supertrend: bool = False
    supertrend_period: int = 10
    supertrend_multiplier: float = 3.0
    use_rsi_filter: bool = False
    rsi_period: int = 14
    rsi_overbought: int = 70
    rsi_oversold: int = 30
    use_adx_filter: bool = False
    adx_period: int = 14
    adx_threshold: int = 25
    allow_reentry: bool = True
    reentry_after_sl: bool = True
    reentry_after_tp: bool = False


@router.get("/auto-optimize-stream")
async def auto_optimize_stream(
    mode: str = "indicator",
    symbol: str = "BTCUSDT",
    timeframe: str = "1h"
):
    """SSE endpoint for optimization progress"""
    import os
    
    async def generate():
        workers = os.cpu_count() or 4
        
        yield f"data: {json_module.dumps({'type': 'start', 'workers': workers, 'mode': mode})}\n\n"
        
        # Load data
        filepath = DATA_DIR / f"{symbol}_{timeframe}.parquet"
        if not filepath.exists():
            yield f"data: {json_module.dumps({'type': 'error', 'message': 'Data not found'})}\n\n"
            return
        
        df = pd.read_parquet(filepath)
        df = df[~df.index.duplicated(keep='first')]
        df = df.sort_index()
        
        # Generate parameter combinations based on mode
        combinations = []
        
        if mode == "indicator":
            for i1 in range(20, 81, 5):
                for i2 in [2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]:
                    combinations.append({'i1': i1, 'i2': i2})
        elif mode == "tp":
            for tp1 in [0.5, 0.75, 1.0, 1.25, 1.5]:
                for tp2 in [1.5, 2.0, 2.5, 3.0]:
                    combinations.append({'tp1': tp1, 'tp2': tp2})
        elif mode == "sl":
            for sl in [3, 4, 5, 6, 7, 8, 10]:
                for mode_sl in ['no', 'breakeven', 'moving']:
                    combinations.append({'sl': sl, 'sl_mode': mode_sl})
        else:
            # Full mode - simplified
            for i1 in [30, 45, 60]:
                for i2 in [3.0, 4.0, 5.0]:
                    combinations.append({'i1': i1, 'i2': i2})
        
        total = len(combinations)
        best_result = None
        best_profit = float('-inf')
        
        for idx, params in enumerate(combinations):
            i1 = params.get('i1', 45)
            i2 = params.get('i2', 4.0)
            tp1 = params.get('tp1', 1.05)
            tp2 = params.get('tp2', 1.95)
            sl = params.get('sl', 6.0)
            sl_mode = params.get('sl_mode', 'breakeven')
            
            settings = IndicatorSettings(
                symbol=symbol,
                timeframe=timeframe,
                trg_atr_length=i1,
                trg_multiplier=i2,
                tp1_percent=tp1,
                tp2_percent=tp2,
                sl_percent=sl,
                sl_trailing_mode=sl_mode
            )
            
            try:
                df_calc = calculate_trg(df.copy(), i1, i2)
                df_calc = generate_signals(df_calc, settings)
                trades, equity_curve, _, _, _ = run_backtest(df_calc, settings)
                
                if equity_curve:
                    profit_pct = round((equity_curve[-1]['value'] / settings.initial_capital - 1) * 100, 2)
                else:
                    profit_pct = 0
                
                win_rate = round(len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100, 1) if trades else 0
                
                if profit_pct > best_profit:
                    best_profit = profit_pct
                    best_result = {
                        **params,
                        'profit': profit_pct,
                        'win_rate': win_rate,
                        'trades': len(trades)
                    }
                
                yield f"data: {json_module.dumps({'type': 'test', 'progress': idx + 1, 'total': total, 'params': params, 'profit': profit_pct, 'win_rate': win_rate})}\n\n"
                
            except Exception as e:
                print(f"Optimize error: {e}")
                continue
            
            await asyncio.sleep(0.01)
        
        yield f"data: {json_module.dumps({'type': 'complete', 'best': best_result})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
