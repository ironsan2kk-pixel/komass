"""
Komas Trading Server - Indicator API
====================================
Full indicator calculation with trades, stats, equity
"""
import asyncio
import numpy as np
import pandas as pd
import aiohttp
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from pathlib import Path
import os
import json as json_lib
from concurrent.futures import ProcessPoolExecutor, as_completed

router = APIRouter(prefix="/api/indicator", tags=["Indicator"])

# Try multiple possible data locations
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

# Parallel processing workers
NUM_WORKERS = os.cpu_count() or 4


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
    
    # Load data
    filepath = DATA_DIR / f"{settings.symbol}_{settings.timeframe}.parquet"
    if not filepath.exists():
        # Try to download automatically
        try:
            await download_single_symbol(settings.symbol, settings.timeframe)
            # Check again after download
            if not filepath.exists():
                raise HTTPException(404, f"Data not found for {settings.symbol} {settings.timeframe}. Go to Data section and download history.")
        except Exception as e:
            raise HTTPException(404, f"Data not found for {settings.symbol} {settings.timeframe}. Go to Data section and download history. Error: {str(e)}")
    
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
    
    return {
        "success": True,
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


@router.get("/candles/{symbol}/{timeframe}")
async def get_candles(symbol: str, timeframe: str):
    """Get candles only for initial chart display"""
    
    filepath = DATA_DIR / f"{symbol}_{timeframe}.parquet"
    if not filepath.exists():
        raise HTTPException(404, f"Data not found for {symbol} {timeframe}")
    
    df = pd.read_parquet(filepath)
    
    # Remove duplicates and sort
    df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()
    
    # Return last 500 candles for initial view
    df = df.tail(500)
    
    candles = prepare_candles(df)
    
    return {
        "success": True,
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": candles,
        "total": len(candles)
    }


@router.post("/replay")
async def replay_indicator(request: ReplayRequest):
    """Get indicator state at specific step for replay mode"""
    
    settings = request.settings
    step = request.step
    
    filepath = DATA_DIR / f"{settings.symbol}_{settings.timeframe}.parquet"
    if not filepath.exists():
        raise HTTPException(404, f"Data not found")
    
    df = pd.read_parquet(filepath)
    
    if settings.start_date:
        df = df[df.index >= settings.start_date]
    if settings.end_date:
        df = df[df.index <= settings.end_date]
    
    # Limit to step
    if step > 0 and step < len(df):
        df = df.iloc[:step]
    
    # Calculate
    df = calculate_trg(df, settings.trg_atr_length, settings.trg_multiplier)
    if settings.use_supertrend:
        df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
    
    df = generate_signals(df, settings)
    trades, equity_curve, tp_stats, _, _ = run_backtest(df, settings)
    
    return {
        "step": step,
        "total_steps": len(df),
        "candles": prepare_candles(df),
        "indicators": prepare_indicators(df, settings),
        "trades": trades[-10:] if trades else [],  # Last 10 trades
        "equity": equity_curve[-1]['value'] if equity_curve else settings.initial_capital,
        "current_signal": get_current_signal(df)
    }


@router.post("/heatmap")
async def generate_heatmap(settings: IndicatorSettings):
    """Generate optimization heatmap for i1/i2 (parallel)"""
    
    filepath = DATA_DIR / f"{settings.symbol}_{settings.timeframe}.parquet"
    if not filepath.exists():
        raise HTTPException(404, f"Data not found")
    
    df_original = pd.read_parquet(filepath)
    df_original = df_original[~df_original.index.duplicated(keep='first')]
    df_original = df_original.sort_index()
    
    if settings.start_date:
        df_original = df_original[df_original.index >= settings.start_date]
    if settings.end_date:
        df_original = df_original[df_original.index <= settings.end_date]
    
    # Parameter ranges
    i1_range = [20, 30, 40, 45, 50, 60, 70, 80, 100]
    i2_range = [2, 3, 4, 5, 6, 7, 8, 10]
    
    # Prepare params for parallel execution
    param_list = []
    for i1 in i1_range:
        for i2 in i2_range:
            param_list.append({'df': df_original, 'settings': settings, 'i1': i1, 'i2': i2, 'metric': 'profit'})
    
    results = []
    
    # Run in parallel
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = [executor.submit(run_single_backtest_indicator, params) for params in param_list]
        for future in as_completed(futures):
            r = future.result()
            results.append({
                "i1": r['i1'],
                "i2": r['i2'],
                "pnl": r.get('profit', 0),
                "win_rate": r.get('win_rate', 0),
                "trades": r.get('trades', 0)
            })
    
    return {
        "success": True,
        "i1_range": i1_range,
        "i2_range": i2_range,
        "results": results,
        "workers_used": NUM_WORKERS
    }


class AutoOptimizeMode(BaseModel):
    mode: str = "indicator"  # "indicator", "tp", "sl", "filters", "tp_custom", "all", "full", "adaptive"
    settings: IndicatorSettings
    metric: str = "advanced"  # "profit", "winrate", "sharpe", "profit_factor", "advanced"
    lookback_months: int = 3  # For adaptive mode - optimize on last N months
    reoptimize_period: str = "month"  # "week", "month", "quarter"
    # For tp_custom mode: percentage range from current settings
    tp_range_percent: float = 50.0  # ±50% from current TP values
    tp_step_percent: float = 10.0  # Step 10%
    # For full mode: control search depth
    full_mode_depth: str = "medium"  # "fast", "medium", "deep"


def calculate_advanced_score(trades: list, equity_curve: list, settings, detailed: bool = False) -> tuple:
    """
    Advanced scoring system for optimization that considers:
    - Profit/Loss
    - Win rate
    - Max drawdown
    - TP1 hit rate (important for BE strategy)
    - Profit factor
    - Risk-adjusted return (Sharpe-like)
    - Re-entry performance
    - Consistency (std of returns)
    - Recovery factor
    """
    
    if not trades or len(trades) < 5:
        return float('-inf'), {}
    
    import numpy as np
    
    # Basic metrics
    pnls = [float(t['pnl']) for t in trades]
    pnl_amounts = [float(t.get('pnl_amount', 0)) for t in trades]
    
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    
    total_trades = len(trades)
    win_count = len(wins)
    loss_count = len(losses)
    
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    
    # Profit metrics
    total_profit = sum(wins) if wins else 0
    total_loss = abs(sum(losses)) if losses else 0
    net_profit = total_profit - total_loss
    
    profit_factor = (total_profit / total_loss) if total_loss > 0 else 999
    profit_factor = min(profit_factor, 100)  # Cap at 100
    
    avg_win = (sum(wins) / len(wins)) if wins else 0
    avg_loss = (abs(sum(losses)) / len(losses)) if losses else 0
    
    # Risk/Reward ratio
    rr_ratio = (avg_win / avg_loss) if avg_loss > 0 else 999
    
    # TP1 Hit Rate (critical for BE strategy)
    tp1_hits = sum(1 for t in trades if 1 in t.get('tp_hit', []))
    tp1_hit_rate = (tp1_hits / total_trades * 100) if total_trades > 0 else 0
    
    # TP2+ Hit Rate
    tp2_hits = sum(1 for t in trades if 2 in t.get('tp_hit', []))
    tp2_hit_rate = (tp2_hits / total_trades * 100) if total_trades > 0 else 0
    
    # Drawdown calculation
    if equity_curve:
        equity_values = [float(eq['value']) for eq in equity_curve]
        peak = equity_values[0]
        max_dd = 0
        max_dd_duration = 0
        current_dd_start = 0
        
        for i, val in enumerate(equity_values):
            if val > peak:
                peak = val
                current_dd_start = i
            dd = (peak - val) / peak * 100 if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
                max_dd_duration = i - current_dd_start
        
        final_capital = equity_values[-1]
        initial_capital = float(settings.initial_capital)
        profit_pct = ((final_capital / initial_capital) - 1) * 100
        
        # Recovery factor = Net Profit / Max Drawdown
        recovery_factor = (profit_pct / max_dd) if max_dd > 0 else profit_pct
    else:
        max_dd = 0
        max_dd_duration = 0
        profit_pct = sum(pnls)
        recovery_factor = profit_pct
        final_capital = float(settings.initial_capital)
    
    # Sharpe-like ratio (return / volatility)
    if len(pnls) > 1:
        avg_return = float(np.mean(pnls))
        std_return = float(np.std(pnls))
        sharpe = (avg_return / std_return) if std_return > 0 else 0
    else:
        sharpe = 0
        std_return = 0
    
    # Re-entry analysis
    reentry_trades = [t for t in trades if t.get('is_reentry', False)]
    reentry_count = len(reentry_trades)
    reentry_wins = sum(1 for t in reentry_trades if t['pnl'] > 0)
    reentry_win_rate = (reentry_wins / reentry_count * 100) if reentry_count > 0 else 0
    reentry_profit = sum(t['pnl'] for t in reentry_trades) if reentry_trades else 0
    
    # Long/Short balance
    long_trades = [t for t in trades if t.get('type') == 'long']
    short_trades = [t for t in trades if t.get('type') == 'short']
    long_win_rate = (sum(1 for t in long_trades if t['pnl'] > 0) / len(long_trades) * 100) if long_trades else 0
    short_win_rate = (sum(1 for t in short_trades if t['pnl'] > 0) / len(short_trades) * 100) if short_trades else 0
    
    # Exit reason analysis
    sl_exits = sum(1 for t in trades if t.get('exit_reason') == 'SL')
    tp_exits = sum(1 for t in trades if t.get('exit_reason', '').startswith('TP'))
    reverse_exits = sum(1 for t in trades if t.get('exit_reason') == 'Reverse')
    
    sl_rate = (sl_exits / total_trades * 100) if total_trades > 0 else 0
    
    # Consistency score (lower std = more consistent)
    consistency = (1 / (1 + std_return)) * 100 if std_return >= 0 else 0
    
    # ========== ADVANCED SCORING ==========
    # Weight factors (total = 100%)
    WEIGHTS = {
        'profit': 0.20,          # Net profit
        'win_rate': 0.15,        # Overall win rate
        'tp1_hit_rate': 0.15,    # TP1 hit rate (critical for BE)
        'drawdown': 0.15,        # Max drawdown penalty
        'profit_factor': 0.10,   # Profit factor
        'sharpe': 0.10,          # Risk-adjusted return
        'recovery': 0.05,        # Recovery factor
        'consistency': 0.05,     # Return consistency
        'reentry': 0.05,         # Re-entry performance
    }
    
    # Normalize scores to 0-100 scale
    def normalize(value, min_val, max_val, invert=False):
        if max_val == min_val:
            return 50
        normalized = (value - min_val) / (max_val - min_val) * 100
        normalized = max(0, min(100, normalized))
        return (100 - normalized) if invert else normalized
    
    # Calculate component scores
    profit_score = normalize(profit_pct, -50, 200)
    win_rate_score = normalize(win_rate, 30, 70)
    tp1_score = normalize(tp1_hit_rate, 30, 80)
    dd_score = normalize(max_dd, 5, 50, invert=True)  # Lower DD = better
    pf_score = normalize(profit_factor, 0.5, 3.0)
    sharpe_score = normalize(sharpe, -1, 2)
    recovery_score = normalize(recovery_factor, -2, 5)
    consistency_score = consistency
    reentry_score = normalize(reentry_win_rate, 30, 70) if reentry_count > 3 else 50
    
    # Calculate final score
    final_score = (
        profit_score * WEIGHTS['profit'] +
        win_rate_score * WEIGHTS['win_rate'] +
        tp1_score * WEIGHTS['tp1_hit_rate'] +
        dd_score * WEIGHTS['drawdown'] +
        pf_score * WEIGHTS['profit_factor'] +
        sharpe_score * WEIGHTS['sharpe'] +
        recovery_score * WEIGHTS['recovery'] +
        consistency_score * WEIGHTS['consistency'] +
        reentry_score * WEIGHTS['reentry']
    )
    
    # Penalties
    # Too few trades penalty
    if total_trades < 20:
        final_score *= 0.7
    elif total_trades < 50:
        final_score *= 0.85
    
    # High SL rate penalty (>60% stopped out)
    if sl_rate > 60:
        final_score *= 0.8
    
    # Very low TP1 hit rate penalty
    if tp1_hit_rate < 40:
        final_score *= 0.9
    
    # Extreme drawdown penalty
    if max_dd > 40:
        final_score *= 0.7
    elif max_dd > 30:
        final_score *= 0.85
    
    # Build metrics dict
    metrics = {
        # Basic
        "profit_pct": float(round(profit_pct, 2)),
        "win_rate": float(round(win_rate, 2)),
        "total_trades": int(total_trades),
        "profit_factor": float(round(min(profit_factor, 99.99), 2)),
        
        # Risk
        "max_drawdown": float(round(max_dd, 2)),
        "sharpe": float(round(sharpe, 2)),
        "recovery_factor": float(round(recovery_factor, 2)),
        
        # TP analysis
        "tp1_hit_rate": float(round(tp1_hit_rate, 2)),
        "tp2_hit_rate": float(round(tp2_hit_rate, 2)),
        
        # Trade breakdown
        "avg_win": float(round(avg_win, 2)),
        "avg_loss": float(round(avg_loss, 2)),
        "rr_ratio": float(round(min(rr_ratio, 99.99), 2)),
        
        # Exit analysis
        "sl_exits": int(sl_exits),
        "tp_exits": int(tp_exits),
        "reverse_exits": int(reverse_exits),
        "sl_rate": float(round(sl_rate, 2)),
        
        # Re-entry
        "reentry_count": int(reentry_count),
        "reentry_win_rate": float(round(reentry_win_rate, 2)),
        "reentry_profit": float(round(reentry_profit, 2)),
        
        # Long/Short
        "long_trades": int(len(long_trades)),
        "short_trades": int(len(short_trades)),
        "long_win_rate": float(round(long_win_rate, 2)),
        "short_win_rate": float(round(short_win_rate, 2)),
        
        # Score components (for debugging)
        "final_capital": float(round(final_capital, 2)),
    }
    
    if detailed:
        metrics["score_breakdown"] = {
            "profit_score": float(round(profit_score, 2)),
            "win_rate_score": float(round(win_rate_score, 2)),
            "tp1_score": float(round(tp1_score, 2)),
            "dd_score": float(round(dd_score, 2)),
            "pf_score": float(round(pf_score, 2)),
            "sharpe_score": float(round(sharpe_score, 2)),
            "recovery_score": float(round(recovery_score, 2)),
            "consistency_score": float(round(consistency_score, 2)),
            "reentry_score": float(round(reentry_score, 2)),
        }
    
    return float(round(final_score, 2)), metrics


def run_single_backtest_full(params: dict) -> dict:
    """Run a single backtest for FULL optimization (all parameters at once)"""
    try:
        df = params['df'].copy()
        base_settings = params['settings']
        cfg = params['cfg']
        use_advanced_score = params.get('use_advanced_score', True)
        
        # Apply ALL config parameters
        temp_settings = base_settings.model_copy()
        
        # Indicator params
        temp_settings.trg_atr_length = cfg.get('i1', base_settings.trg_atr_length)
        temp_settings.trg_multiplier = cfg.get('i2', base_settings.trg_multiplier)
        
        # TP params
        temp_settings.tp1_percent = cfg.get('tp1', base_settings.tp1_percent)
        temp_settings.tp2_percent = cfg.get('tp2', base_settings.tp2_percent)
        temp_settings.tp3_percent = cfg.get('tp3', base_settings.tp3_percent)
        temp_settings.tp4_percent = cfg.get('tp4', base_settings.tp4_percent)
        
        # SL params
        temp_settings.sl_percent = cfg.get('sl', base_settings.sl_percent)
        temp_settings.sl_trailing_mode = cfg.get('sl_mode', base_settings.sl_trailing_mode)
        
        # Filter params
        temp_settings.use_supertrend = cfg.get('use_st', base_settings.use_supertrend)
        temp_settings.supertrend_period = cfg.get('st_period', base_settings.supertrend_period)
        temp_settings.supertrend_multiplier = cfg.get('st_mult', base_settings.supertrend_multiplier)
        
        temp_settings.use_rsi_filter = cfg.get('use_rsi', base_settings.use_rsi_filter)
        temp_settings.rsi_period = cfg.get('rsi_period', base_settings.rsi_period)
        
        temp_settings.use_adx_filter = cfg.get('use_adx', base_settings.use_adx_filter)
        temp_settings.adx_threshold = cfg.get('adx_threshold', base_settings.adx_threshold)
        
        # Re-entry params
        temp_settings.allow_reentry = cfg.get('allow_reentry', base_settings.allow_reentry)
        temp_settings.reentry_after_sl = cfg.get('reentry_sl', base_settings.reentry_after_sl)
        temp_settings.reentry_after_tp = cfg.get('reentry_tp', base_settings.reentry_after_tp)
        
        # Calculate indicators
        df = calculate_trg(df, temp_settings.trg_atr_length, temp_settings.trg_multiplier)
        
        if temp_settings.use_supertrend:
            df = calculate_supertrend(df, temp_settings.supertrend_period, temp_settings.supertrend_multiplier)
        if temp_settings.use_rsi_filter:
            df = calculate_rsi(df, temp_settings.rsi_period)
        if temp_settings.use_adx_filter:
            df = calculate_adx(df, temp_settings.adx_period)
        
        df = generate_signals(df, temp_settings)
        trades, equity_curve, _, _, _ = run_backtest(df, temp_settings)
        
        # Use advanced or simple scoring
        if use_advanced_score:
            score, metrics = calculate_advanced_score(trades, equity_curve, temp_settings)
        else:
            score, metrics = calculate_optimization_score(trades, equity_curve, temp_settings, "profit")
        
        return {
            "cfg": cfg,
            "score": float(round(score, 2)),
            "profit": float(metrics.get("profit_pct", 0)),
            "win_rate": float(metrics.get("win_rate", 0)),
            "trades": int(metrics.get("total_trades", 0)),
            "tp1_hit": float(metrics.get("tp1_hit_rate", 0)),
            "max_dd": float(metrics.get("max_drawdown", 0)),
            "metrics": metrics
        }
    except Exception as e:
        return {"cfg": params.get('cfg', {}), "score": -999, "profit": 0, "win_rate": 0, "trades": 0, "error": str(e)}


def generate_full_optimization_configs(settings: IndicatorSettings, depth: str = "medium") -> list:
    """
    Generate comprehensive parameter combinations for full optimization
    
    Depth levels:
    - fast: ~100 combinations (quick scan)
    - medium: ~500 combinations (balanced)
    - deep: ~2000+ combinations (thorough)
    """
    configs = []
    
    # Base ranges based on depth
    if depth == "fast":
        i1_range = [35, 45, 60]
        i2_range = [3, 4, 5]
        tp1_range = [0.8, 1.0, 1.5]
        sl_range = [4, 6, 8]
        sl_modes = ["breakeven", "moving"]
        filter_presets = [
            {"use_st": False, "use_rsi": False, "use_adx": False},
            {"use_st": True, "st_period": 10, "st_mult": 3.0, "use_rsi": False, "use_adx": False},
        ]
        reentry_presets = [
            {"allow_reentry": True, "reentry_sl": True, "reentry_tp": False},
        ]
    
    elif depth == "medium":
        i1_range = [30, 40, 45, 50, 60, 80]
        i2_range = [2, 3, 4, 5, 6]
        tp1_range = [0.6, 0.8, 1.0, 1.2, 1.5]
        sl_range = [3, 4, 5, 6, 8, 10]
        sl_modes = ["no", "breakeven", "moving"]
        filter_presets = [
            {"use_st": False, "use_rsi": False, "use_adx": False},
            {"use_st": True, "st_period": 10, "st_mult": 3.0, "use_rsi": False, "use_adx": False},
            {"use_st": True, "st_period": 14, "st_mult": 2.0, "use_rsi": False, "use_adx": False},
            {"use_st": False, "use_rsi": True, "rsi_period": 14, "use_adx": False},
            {"use_st": False, "use_rsi": False, "use_adx": True, "adx_threshold": 25},
            {"use_st": True, "st_period": 10, "st_mult": 3.0, "use_rsi": True, "rsi_period": 14, "use_adx": False},
        ]
        reentry_presets = [
            {"allow_reentry": False, "reentry_sl": False, "reentry_tp": False},
            {"allow_reentry": True, "reentry_sl": True, "reentry_tp": False},
            {"allow_reentry": True, "reentry_sl": True, "reentry_tp": True},
        ]
    
    else:  # deep
        i1_range = [25, 30, 35, 40, 45, 50, 55, 60, 70, 80, 100]
        i2_range = [1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 7]
        tp1_range = [0.5, 0.6, 0.8, 1.0, 1.2, 1.5, 2.0]
        sl_range = [2, 3, 4, 5, 6, 7, 8, 10, 12]
        sl_modes = ["no", "breakeven", "moving"]
        filter_presets = [
            {"use_st": False, "use_rsi": False, "use_adx": False},
            {"use_st": True, "st_period": 7, "st_mult": 2.0, "use_rsi": False, "use_adx": False},
            {"use_st": True, "st_period": 10, "st_mult": 3.0, "use_rsi": False, "use_adx": False},
            {"use_st": True, "st_period": 14, "st_mult": 2.0, "use_rsi": False, "use_adx": False},
            {"use_st": True, "st_period": 20, "st_mult": 3.0, "use_rsi": False, "use_adx": False},
            {"use_st": False, "use_rsi": True, "rsi_period": 7, "use_adx": False},
            {"use_st": False, "use_rsi": True, "rsi_period": 14, "use_adx": False},
            {"use_st": False, "use_rsi": True, "rsi_period": 21, "use_adx": False},
            {"use_st": False, "use_rsi": False, "use_adx": True, "adx_threshold": 20},
            {"use_st": False, "use_rsi": False, "use_adx": True, "adx_threshold": 25},
            {"use_st": False, "use_rsi": False, "use_adx": True, "adx_threshold": 30},
            {"use_st": True, "st_period": 10, "st_mult": 3.0, "use_rsi": True, "rsi_period": 14, "use_adx": False},
            {"use_st": True, "st_period": 10, "st_mult": 3.0, "use_rsi": False, "use_adx": True, "adx_threshold": 25},
        ]
        reentry_presets = [
            {"allow_reentry": False, "reentry_sl": False, "reentry_tp": False},
            {"allow_reentry": True, "reentry_sl": True, "reentry_tp": False},
            {"allow_reentry": True, "reentry_sl": False, "reentry_tp": True},
            {"allow_reentry": True, "reentry_sl": True, "reentry_tp": True},
        ]
    
    # TP ratios (relative to TP1)
    tp_ratios = [
        {"r2": 1.8, "r3": 3.0, "r4": 4.5},  # Conservative
        {"r2": 2.0, "r3": 3.5, "r4": 5.5},  # Balanced
        {"r2": 2.5, "r3": 4.0, "r4": 6.0},  # Aggressive
    ]
    
    # Generate combinations
    count = 0
    max_configs = {"fast": 150, "medium": 600, "deep": 2500}
    
    for i1 in i1_range:
        for i2 in i2_range:
            for tp1 in tp1_range:
                for tp_ratio in tp_ratios:
                    tp2 = round(tp1 * tp_ratio["r2"], 2)
                    tp3 = round(tp1 * tp_ratio["r3"], 2)
                    tp4 = round(tp1 * tp_ratio["r4"], 2)
                    
                    for sl in sl_range:
                        for sl_mode in sl_modes:
                            for filter_cfg in filter_presets:
                                for reentry_cfg in reentry_presets:
                                    cfg = {
                                        "i1": i1,
                                        "i2": i2,
                                        "tp1": tp1,
                                        "tp2": tp2,
                                        "tp3": tp3,
                                        "tp4": tp4,
                                        "sl": sl,
                                        "sl_mode": sl_mode,
                                        **filter_cfg,
                                        **reentry_cfg,
                                    }
                                    configs.append(cfg)
                                    count += 1
                                    
                                    if count >= max_configs[depth]:
                                        return configs
    
    return configs


@router.post("/auto-optimize")
async def auto_optimize(request: AutoOptimizeMode):
    """Auto-optimize parameters based on selected mode"""
    
    settings = request.settings
    mode = request.mode
    metric = request.metric
    
    filepath = DATA_DIR / f"{settings.symbol}_{settings.timeframe}.parquet"
    if not filepath.exists():
        raise HTTPException(404, f"Data not found for {settings.symbol}")
    
    df_original = pd.read_parquet(filepath)
    df_original = df_original[~df_original.index.duplicated(keep='first')]
    df_original = df_original.sort_index()
    
    if settings.start_date:
        df_original = df_original[df_original.index >= settings.start_date]
    if settings.end_date:
        df_original = df_original[df_original.index <= settings.end_date]
    
    # Adaptive Walk-Forward Optimization
    if mode == "adaptive":
        return await run_adaptive_optimization(df_original, settings, metric, request.lookback_months, request.reoptimize_period)
    
    # First, calculate CURRENT performance with existing settings
    df_current = df_original.copy()
    df_current = calculate_trg(df_current, settings.trg_atr_length, settings.trg_multiplier)
    if settings.use_supertrend:
        df_current = calculate_supertrend(df_current, settings.supertrend_period, settings.supertrend_multiplier)
    df_current = generate_signals(df_current, settings)
    current_trades, current_equity, _, _, _ = run_backtest(df_current, settings)
    current_score, current_metrics = calculate_optimization_score(current_trades, current_equity, settings, metric)
    
    best_result = None
    best_score = float('-inf')
    best_params = {}
    all_results = []
    tested_count = 0
    
    if mode == "indicator":
        # Optimize i1 (ATR Length) and i2 (Multiplier)
        i1_range = [20, 30, 35, 40, 45, 50, 55, 60, 70, 80, 100, 120]
        i2_range = [1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 7, 8]
        
        for i1 in i1_range:
            for i2 in i2_range:
                tested_count += 1
                df = df_original.copy()
                df = calculate_trg(df, i1, i2)
                if settings.use_supertrend:
                    df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
                
                temp_settings = settings.model_copy()
                temp_settings.trg_atr_length = i1
                temp_settings.trg_multiplier = i2
                
                df = generate_signals(df, temp_settings)
                trades, equity_curve, _, _, _ = run_backtest(df, temp_settings)
                
                score, metrics = calculate_optimization_score(trades, equity_curve, settings, metric)
                
                all_results.append({
                    "i1": i1, "i2": i2, 
                    "score": round(score, 2),
                    "profit": metrics.get("profit_pct", 0),
                    "win_rate": metrics.get("win_rate", 0),
                    "trades": metrics.get("total_trades", 0),
                    "pf": metrics.get("profit_factor", 0)
                })
                
                if score > best_score:
                    best_score = score
                    best_params = {"trg_atr_length": i1, "trg_multiplier": i2}
                    best_result = metrics
    
    elif mode == "tp":
        # Optimize TP levels and amounts
        tp_configs = [
            # Conservative
            {"tp1": 0.5, "tp2": 1.0, "tp3": 1.5, "tp4": 2.0, "a1": 40, "a2": 30, "a3": 20, "a4": 10},
            {"tp1": 0.75, "tp2": 1.25, "tp3": 2.0, "tp4": 3.0, "a1": 50, "a2": 25, "a3": 15, "a4": 10},
            {"tp1": 1.0, "tp2": 1.5, "tp3": 2.5, "tp4": 4.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
            # Balanced
            {"tp1": 1.0, "tp2": 2.0, "tp3": 3.5, "tp4": 5.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
            {"tp1": 1.05, "tp2": 1.95, "tp3": 3.75, "tp4": 6.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
            {"tp1": 1.25, "tp2": 2.5, "tp3": 4.0, "tp4": 6.5, "a1": 45, "a2": 30, "a3": 15, "a4": 10},
            # Aggressive
            {"tp1": 1.5, "tp2": 3.0, "tp3": 5.0, "tp4": 8.0, "a1": 40, "a2": 30, "a3": 20, "a4": 10},
            {"tp1": 2.0, "tp2": 4.0, "tp3": 6.0, "tp4": 10.0, "a1": 35, "a2": 30, "a3": 20, "a4": 15},
            {"tp1": 2.5, "tp2": 5.0, "tp3": 8.0, "tp4": 12.0, "a1": 30, "a2": 30, "a3": 25, "a4": 15},
            # Heavy first TP
            {"tp1": 0.8, "tp2": 1.5, "tp3": 3.0, "tp4": 5.0, "a1": 60, "a2": 25, "a3": 10, "a4": 5},
            {"tp1": 1.0, "tp2": 2.0, "tp3": 4.0, "tp4": 7.0, "a1": 70, "a2": 20, "a3": 7, "a4": 3},
            # Equal distribution
            {"tp1": 1.0, "tp2": 2.0, "tp3": 3.0, "tp4": 4.0, "a1": 25, "a2": 25, "a3": 25, "a4": 25},
            {"tp1": 1.5, "tp2": 3.0, "tp3": 4.5, "tp4": 6.0, "a1": 25, "a2": 25, "a3": 25, "a4": 25},
            # More configs
            {"tp1": 0.6, "tp2": 1.2, "tp3": 2.0, "tp4": 3.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
            {"tp1": 0.8, "tp2": 1.6, "tp3": 2.8, "tp4": 4.5, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
            {"tp1": 1.2, "tp2": 2.4, "tp3": 4.0, "tp4": 6.0, "a1": 45, "a2": 30, "a3": 15, "a4": 10},
        ]
        
        for cfg in tp_configs:
            tested_count += 1
            df = df_original.copy()
            df = calculate_trg(df, settings.trg_atr_length, settings.trg_multiplier)
            if settings.use_supertrend:
                df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
            
            temp_settings = settings.model_copy()
            temp_settings.tp1_percent = cfg["tp1"]
            temp_settings.tp2_percent = cfg["tp2"]
            temp_settings.tp3_percent = cfg["tp3"]
            temp_settings.tp4_percent = cfg["tp4"]
            temp_settings.tp1_amount = cfg["a1"]
            temp_settings.tp2_amount = cfg["a2"]
            temp_settings.tp3_amount = cfg["a3"]
            temp_settings.tp4_amount = cfg["a4"]
            
            df = generate_signals(df, temp_settings)
            trades, equity_curve, _, _, _ = run_backtest(df, temp_settings)
            
            score, metrics = calculate_optimization_score(trades, equity_curve, settings, metric)
            
            all_results.append({
                "config": f"TP:{cfg['tp1']}/{cfg['tp2']}/{cfg['tp3']}/{cfg['tp4']} Amt:{cfg['a1']}/{cfg['a2']}/{cfg['a3']}/{cfg['a4']}",
                "score": round(score, 2),
                "profit": metrics.get("profit_pct", 0),
                "win_rate": metrics.get("win_rate", 0),
                "trades": metrics.get("total_trades", 0)
            })
            
            if score > best_score:
                best_score = score
                best_params = {
                    "tp1_percent": cfg["tp1"], "tp2_percent": cfg["tp2"],
                    "tp3_percent": cfg["tp3"], "tp4_percent": cfg["tp4"],
                    "tp1_amount": cfg["a1"], "tp2_amount": cfg["a2"],
                    "tp3_amount": cfg["a3"], "tp4_amount": cfg["a4"]
                }
                best_result = metrics
    
    elif mode == "sl":
        # Optimize SL percent and trailing mode
        for sl_pct in [2, 3, 4, 5, 6, 7, 8, 10, 12, 15]:
            for trail_mode in ["no", "breakeven", "moving"]:
                tested_count += 1
                df = df_original.copy()
                df = calculate_trg(df, settings.trg_atr_length, settings.trg_multiplier)
                if settings.use_supertrend:
                    df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
                
                temp_settings = settings.model_copy()
                temp_settings.sl_percent = sl_pct
                temp_settings.sl_trailing_mode = trail_mode
                
                df = generate_signals(df, temp_settings)
                trades, equity_curve, _, _, _ = run_backtest(df, temp_settings)
                
                score, metrics = calculate_optimization_score(trades, equity_curve, settings, metric)
                
                all_results.append({
                    "sl": sl_pct,
                    "mode": trail_mode,
                    "score": round(score, 2),
                    "profit": metrics.get("profit_pct", 0),
                    "win_rate": metrics.get("win_rate", 0),
                    "trades": metrics.get("total_trades", 0)
                })
                
                if score > best_score:
                    best_score = score
                    best_params = {"sl_percent": sl_pct, "sl_trailing_mode": trail_mode}
                    best_result = metrics
    
    elif mode == "all":
        # Quick optimization of all parameters (reduced search space)
        i1_range = [30, 40, 45, 50, 60, 80]
        i2_range = [2, 3, 4, 5, 6]
        tp_presets = [
            {"tp1": 0.8, "tp2": 1.5, "tp3": 2.5, "tp4": 4.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
            {"tp1": 1.0, "tp2": 2.0, "tp3": 3.5, "tp4": 5.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
            {"tp1": 1.5, "tp2": 3.0, "tp3": 5.0, "tp4": 8.0, "a1": 40, "a2": 30, "a3": 20, "a4": 10},
        ]
        sl_configs = [
            {"sl_percent": 4, "sl_trailing_mode": "breakeven"},
            {"sl_percent": 6, "sl_trailing_mode": "breakeven"},
            {"sl_percent": 8, "sl_trailing_mode": "moving"},
        ]
        
        for i1 in i1_range:
            for i2 in i2_range:
                for tp_cfg in tp_presets:
                    for sl_cfg in sl_configs:
                        tested_count += 1
                        df = df_original.copy()
                        df = calculate_trg(df, i1, i2)
                        if settings.use_supertrend:
                            df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
                        
                        temp_settings = settings.model_copy()
                        temp_settings.trg_atr_length = i1
                        temp_settings.trg_multiplier = i2
                        temp_settings.tp1_percent = tp_cfg["tp1"]
                        temp_settings.tp2_percent = tp_cfg["tp2"]
                        temp_settings.tp3_percent = tp_cfg["tp3"]
                        temp_settings.tp4_percent = tp_cfg["tp4"]
                        temp_settings.tp1_amount = tp_cfg["a1"]
                        temp_settings.tp2_amount = tp_cfg["a2"]
                        temp_settings.tp3_amount = tp_cfg["a3"]
                        temp_settings.tp4_amount = tp_cfg["a4"]
                        temp_settings.sl_percent = sl_cfg["sl_percent"]
                        temp_settings.sl_trailing_mode = sl_cfg["sl_trailing_mode"]
                        
                        df = generate_signals(df, temp_settings)
                        trades, equity_curve, _, _, _ = run_backtest(df, temp_settings)
                        
                        score, metrics = calculate_optimization_score(trades, equity_curve, settings, metric)
                        
                        all_results.append({
                            "i1": i1, "i2": i2,
                            "tp1": tp_cfg["tp1"],
                            "sl": sl_cfg["sl_percent"],
                            "score": round(score, 2),
                            "profit": metrics.get("profit_pct", 0),
                            "win_rate": metrics.get("win_rate", 0)
                        })
                        
                        if score > best_score:
                            best_score = score
                            best_params = {
                                "trg_atr_length": i1, "trg_multiplier": i2,
                                "tp1_percent": tp_cfg["tp1"], "tp2_percent": tp_cfg["tp2"],
                                "tp3_percent": tp_cfg["tp3"], "tp4_percent": tp_cfg["tp4"],
                                "tp1_amount": tp_cfg["a1"], "tp2_amount": tp_cfg["a2"],
                                "tp3_amount": tp_cfg["a3"], "tp4_amount": tp_cfg["a4"],
                                "sl_percent": sl_cfg["sl_percent"],
                                "sl_trailing_mode": sl_cfg["sl_trailing_mode"]
                            }
                            best_result = metrics
    
    elif mode == "filters":
        # Optimize filter settings
        filter_configs = generate_filter_configs()
        
        for filter_cfg in filter_configs:
            tested_count += 1
            df = df_original.copy()
            df = calculate_trg(df, settings.trg_atr_length, settings.trg_multiplier)
            
            temp_settings = settings.model_copy()
            temp_settings.use_supertrend = filter_cfg.get('use_supertrend', False)
            temp_settings.supertrend_period = filter_cfg.get('supertrend_period', 10)
            temp_settings.supertrend_multiplier = filter_cfg.get('supertrend_multiplier', 3.0)
            temp_settings.use_rsi_filter = filter_cfg.get('use_rsi_filter', False)
            temp_settings.rsi_period = filter_cfg.get('rsi_period', 14)
            temp_settings.rsi_overbought = filter_cfg.get('rsi_overbought', 70)
            temp_settings.rsi_oversold = filter_cfg.get('rsi_oversold', 30)
            temp_settings.use_adx_filter = filter_cfg.get('use_adx_filter', False)
            temp_settings.adx_period = filter_cfg.get('adx_period', 14)
            temp_settings.adx_threshold = filter_cfg.get('adx_threshold', 25)
            temp_settings.use_volume_filter = filter_cfg.get('use_volume_filter', False)
            temp_settings.volume_ma_period = filter_cfg.get('volume_ma_period', 20)
            temp_settings.volume_threshold = filter_cfg.get('volume_threshold', 1.5)
            
            if temp_settings.use_supertrend:
                df = calculate_supertrend(df, temp_settings.supertrend_period, temp_settings.supertrend_multiplier)
            if temp_settings.use_rsi_filter:
                df = calculate_rsi(df, temp_settings.rsi_period)
            if temp_settings.use_adx_filter:
                df = calculate_adx(df, temp_settings.adx_period)
            
            df = generate_signals(df, temp_settings)
            trades, equity_curve, _, _, _ = run_backtest(df, temp_settings)
            
            score, metrics = calculate_optimization_score(trades, equity_curve, settings, metric)
            
            all_results.append({
                "config": filter_cfg.get('name', 'Filter'),
                "score": round(score, 2),
                "profit": metrics.get("profit_pct", 0),
                "win_rate": metrics.get("win_rate", 0),
                "trades": metrics.get("total_trades", 0)
            })
            
            if score > best_score:
                best_score = score
                best_params = {
                    "use_supertrend": filter_cfg.get('use_supertrend', False),
                    "supertrend_period": filter_cfg.get('supertrend_period', 10),
                    "supertrend_multiplier": filter_cfg.get('supertrend_multiplier', 3.0),
                    "use_rsi_filter": filter_cfg.get('use_rsi_filter', False),
                    "rsi_period": filter_cfg.get('rsi_period', 14),
                    "rsi_overbought": filter_cfg.get('rsi_overbought', 70),
                    "rsi_oversold": filter_cfg.get('rsi_oversold', 30),
                    "use_adx_filter": filter_cfg.get('use_adx_filter', False),
                    "adx_period": filter_cfg.get('adx_period', 14),
                    "adx_threshold": filter_cfg.get('adx_threshold', 25),
                    "use_volume_filter": filter_cfg.get('use_volume_filter', False),
                    "volume_ma_period": filter_cfg.get('volume_ma_period', 20),
                    "volume_threshold": filter_cfg.get('volume_threshold', 1.5),
                    "filter_name": filter_cfg.get('name', 'Custom')
                }
                best_result = metrics
    
    elif mode == "tp_custom":
        # Optimize TP/SL based on current settings ±range%
        tp_custom_configs = generate_tp_custom_configs(settings, 50.0, 10.0)  # Default: ±50%, step 10%
        
        for tp_cfg in tp_custom_configs:
            tested_count += 1
            df = df_original.copy()
            df = calculate_trg(df, settings.trg_atr_length, settings.trg_multiplier)
            if settings.use_supertrend:
                df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
            
            temp_settings = settings.model_copy()
            
            # Validate and apply TP values (ensure positive and max 200%)
            temp_settings.tp1_percent = max(0.1, min(200.0, tp_cfg["tp1"]))
            temp_settings.tp2_percent = max(0.1, min(200.0, tp_cfg["tp2"]))
            temp_settings.tp3_percent = max(0.1, min(200.0, tp_cfg["tp3"]))
            temp_settings.tp4_percent = max(0.1, min(200.0, tp_cfg["tp4"]))
            
            # Ensure TPs are in ascending order
            tps = [temp_settings.tp1_percent, temp_settings.tp2_percent, temp_settings.tp3_percent, temp_settings.tp4_percent]
            tps_sorted = sorted(tps)
            temp_settings.tp1_percent = tps_sorted[0]
            temp_settings.tp2_percent = tps_sorted[1]
            temp_settings.tp3_percent = tps_sorted[2]
            temp_settings.tp4_percent = tps_sorted[3]
            
            # Validate SL
            if "sl" in tp_cfg:
                temp_settings.sl_percent = max(0.5, min(200.0, tp_cfg["sl"]))
            
            df = generate_signals(df, temp_settings)
            trades, equity_curve, _, _, _ = run_backtest(df, temp_settings)
            
            score, metrics = calculate_optimization_score(trades, equity_curve, settings, metric)
            
            all_results.append({
                "config": f"TP:{tp_cfg['tp1']:.1f}/{tp_cfg['tp2']:.1f}/{tp_cfg['tp3']:.1f}/{tp_cfg['tp4']:.1f} SL:{tp_cfg.get('sl', settings.sl_percent):.1f}",
                "score": round(score, 2),
                "profit": metrics.get("profit_pct", 0),
                "win_rate": metrics.get("win_rate", 0),
                "trades": metrics.get("total_trades", 0)
            })
            
            if score > best_score:
                best_score = score
                best_params = {
                    "tp1_percent": tp_cfg["tp1"],
                    "tp2_percent": tp_cfg["tp2"],
                    "tp3_percent": tp_cfg["tp3"],
                    "tp4_percent": tp_cfg["tp4"],
                    "sl_percent": tp_cfg.get("sl", settings.sl_percent)
                }
                best_result = metrics
    
    # Sort all results by score and get top 10
    all_results_sorted = sorted(all_results, key=lambda x: x.get('score', 0), reverse=True)[:10]
    
    # Calculate improvement
    improvement = {
        "profit_change": round((best_result.get("profit_pct", 0) - current_metrics.get("profit_pct", 0)), 2),
        "win_rate_change": round((best_result.get("win_rate", 0) - current_metrics.get("win_rate", 0)), 2),
    }
    
    return {
        "success": True,
        "mode": mode,
        "metric": metric,
        "tested_combinations": tested_count,
        "current_params": {
            "trg_atr_length": settings.trg_atr_length,
            "trg_multiplier": settings.trg_multiplier,
            "tp1_percent": settings.tp1_percent,
            "sl_percent": settings.sl_percent,
        },
        "current_result": {
            "profit_pct": current_metrics.get("profit_pct", 0),
            "win_rate": current_metrics.get("win_rate", 0),
            "total_trades": current_metrics.get("total_trades", 0),
            "profit_factor": current_metrics.get("profit_factor", 0),
        },
        "best_params": best_params,
        "best_score": round(best_score, 2),
        "best_result": best_result,
        "improvement": improvement,
        "top_10_results": all_results_sorted
    }


from fastapi.responses import StreamingResponse
import asyncio

# Number of workers for parallel processing


def run_single_backtest_indicator(params: dict) -> dict:
    """Run a single backtest for indicator optimization (for parallel execution)"""
    try:
        df = params['df'].copy()
        settings = params['settings']
        i1 = params['i1']
        i2 = params['i2']
        metric = params['metric']
        
        df = calculate_trg(df, i1, i2)
        if settings.use_supertrend:
            df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
        
        temp_settings = settings.model_copy()
        temp_settings.trg_atr_length = i1
        temp_settings.trg_multiplier = i2
        
        df = generate_signals(df, temp_settings)
        trades, equity_curve, _, _, _ = run_backtest(df, temp_settings)
        score, metrics = calculate_optimization_score(trades, equity_curve, settings, metric)
        
        return {
            "i1": i1, "i2": i2,
            "score": round(score, 2),
            "profit": metrics.get("profit_pct", 0),
            "win_rate": metrics.get("win_rate", 0),
            "trades": metrics.get("total_trades", 0),
            "metrics": metrics
        }
    except Exception as e:
        return {"i1": params.get('i1'), "i2": params.get('i2'), "score": -999, "profit": 0, "win_rate": 0, "trades": 0, "error": str(e)}


def run_single_backtest_sl(params: dict) -> dict:
    """Run a single backtest for SL optimization"""
    try:
        df = params['df'].copy()
        settings = params['settings']
        sl_pct = params['sl_pct']
        trail_mode = params['trail_mode']
        metric = params['metric']
        
        df = calculate_trg(df, settings.trg_atr_length, settings.trg_multiplier)
        if settings.use_supertrend:
            df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
        
        temp_settings = settings.model_copy()
        temp_settings.sl_percent = sl_pct
        temp_settings.sl_trailing_mode = trail_mode
        
        df = generate_signals(df, temp_settings)
        trades, equity_curve, _, _, _ = run_backtest(df, temp_settings)
        score, metrics = calculate_optimization_score(trades, equity_curve, settings, metric)
        
        return {
            "sl": sl_pct, "mode": trail_mode,
            "score": round(score, 2),
            "profit": metrics.get("profit_pct", 0),
            "win_rate": metrics.get("win_rate", 0),
            "trades": metrics.get("total_trades", 0),
            "metrics": metrics
        }
    except Exception as e:
        return {"sl": params.get('sl_pct'), "mode": params.get('trail_mode'), "score": -999, "profit": 0, "win_rate": 0, "trades": 0, "error": str(e)}


def run_single_backtest_tp(params: dict) -> dict:
    """Run a single backtest for TP optimization"""
    try:
        df = params['df'].copy()
        settings = params['settings']
        cfg = params['cfg']
        metric = params['metric']
        
        df = calculate_trg(df, settings.trg_atr_length, settings.trg_multiplier)
        if settings.use_supertrend:
            df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
        
        temp_settings = settings.model_copy()
        temp_settings.tp1_percent = cfg["tp1"]
        temp_settings.tp2_percent = cfg["tp2"]
        temp_settings.tp3_percent = cfg["tp3"]
        temp_settings.tp4_percent = cfg["tp4"]
        temp_settings.tp1_amount = cfg["a1"]
        temp_settings.tp2_amount = cfg["a2"]
        temp_settings.tp3_amount = cfg["a3"]
        temp_settings.tp4_amount = cfg["a4"]
        
        df = generate_signals(df, temp_settings)
        trades, equity_curve, _, _, _ = run_backtest(df, temp_settings)
        score, metrics = calculate_optimization_score(trades, equity_curve, settings, metric)
        
        return {
            "cfg": cfg,
            "config": f"TP:{cfg['tp1']}/{cfg['tp2']}/{cfg['tp3']}/{cfg['tp4']}",
            "score": round(score, 2),
            "profit": metrics.get("profit_pct", 0),
            "win_rate": metrics.get("win_rate", 0),
            "trades": metrics.get("total_trades", 0),
            "metrics": metrics
        }
    except Exception as e:
        return {"cfg": params.get('cfg'), "score": -999, "profit": 0, "win_rate": 0, "trades": 0, "error": str(e)}


def run_single_backtest_all(params: dict) -> dict:
    """Run a single backtest for ALL optimization"""
    try:
        df = params['df'].copy()
        settings = params['settings']
        i1 = params['i1']
        i2 = params['i2']
        tp_cfg = params['tp_cfg']
        sl_cfg = params['sl_cfg']
        metric = params['metric']
        
        df = calculate_trg(df, i1, i2)
        if settings.use_supertrend:
            df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
        
        temp_settings = settings.model_copy()
        temp_settings.trg_atr_length = i1
        temp_settings.trg_multiplier = i2
        temp_settings.tp1_percent = tp_cfg["tp1"]
        temp_settings.tp2_percent = tp_cfg["tp2"]
        temp_settings.tp3_percent = tp_cfg["tp3"]
        temp_settings.tp4_percent = tp_cfg["tp4"]
        temp_settings.tp1_amount = tp_cfg["a1"]
        temp_settings.tp2_amount = tp_cfg["a2"]
        temp_settings.tp3_amount = tp_cfg["a3"]
        temp_settings.tp4_amount = tp_cfg["a4"]
        temp_settings.sl_percent = sl_cfg["sl_percent"]
        temp_settings.sl_trailing_mode = sl_cfg["sl_trailing_mode"]
        
        df = generate_signals(df, temp_settings)
        trades, equity_curve, _, _, _ = run_backtest(df, temp_settings)
        score, metrics = calculate_optimization_score(trades, equity_curve, settings, metric)
        
        return {
            "i1": i1, "i2": i2,
            "tp_cfg": tp_cfg, "sl_cfg": sl_cfg,
            "score": round(score, 2),
            "profit": metrics.get("profit_pct", 0),
            "win_rate": metrics.get("win_rate", 0),
            "trades": metrics.get("total_trades", 0),
            "metrics": metrics
        }
    except Exception as e:
        return {"i1": params.get('i1'), "i2": params.get('i2'), "score": -999, "profit": 0, "win_rate": 0, "trades": 0, "error": str(e)}


def run_single_backtest_filters(params: dict) -> dict:
    """Run a single backtest for FILTERS optimization"""
    try:
        df = params['df'].copy()
        settings = params['settings']
        filter_cfg = params['filter_cfg']
        metric = params['metric']
        
        df = calculate_trg(df, settings.trg_atr_length, settings.trg_multiplier)
        
        temp_settings = settings.model_copy()
        
        # Apply filter config
        temp_settings.use_supertrend = filter_cfg.get('use_supertrend', False)
        temp_settings.supertrend_period = filter_cfg.get('supertrend_period', 10)
        temp_settings.supertrend_multiplier = filter_cfg.get('supertrend_multiplier', 3.0)
        
        temp_settings.use_rsi_filter = filter_cfg.get('use_rsi_filter', False)
        temp_settings.rsi_period = filter_cfg.get('rsi_period', 14)
        temp_settings.rsi_overbought = filter_cfg.get('rsi_overbought', 70)
        temp_settings.rsi_oversold = filter_cfg.get('rsi_oversold', 30)
        
        temp_settings.use_adx_filter = filter_cfg.get('use_adx_filter', False)
        temp_settings.adx_period = filter_cfg.get('adx_period', 14)
        temp_settings.adx_threshold = filter_cfg.get('adx_threshold', 25)
        
        temp_settings.use_volume_filter = filter_cfg.get('use_volume_filter', False)
        temp_settings.volume_ma_period = filter_cfg.get('volume_ma_period', 20)
        temp_settings.volume_threshold = filter_cfg.get('volume_threshold', 1.5)
        
        # Calculate required indicators
        if temp_settings.use_supertrend:
            df = calculate_supertrend(df, temp_settings.supertrend_period, temp_settings.supertrend_multiplier)
        if temp_settings.use_rsi_filter:
            df = calculate_rsi(df, temp_settings.rsi_period)
        if temp_settings.use_adx_filter:
            df = calculate_adx(df, temp_settings.adx_period)
        
        df = generate_signals(df, temp_settings)
        trades, equity_curve, _, _, _ = run_backtest(df, temp_settings)
        score, metrics = calculate_optimization_score(trades, equity_curve, settings, metric)
        
        return {
            "filter_cfg": filter_cfg,
            "config": filter_cfg.get('name', 'Filter config'),
            "score": round(score, 2),
            "profit": metrics.get("profit_pct", 0),
            "win_rate": metrics.get("win_rate", 0),
            "trades": metrics.get("total_trades", 0),
            "metrics": metrics
        }
    except Exception as e:
        return {"filter_cfg": params.get('filter_cfg'), "score": -999, "profit": 0, "win_rate": 0, "trades": 0, "error": str(e)}


def run_single_backtest_tp_custom(params: dict) -> dict:
    """Run a single backtest for TP_CUSTOM optimization (based on current settings ±range%)"""
    try:
        df = params['df'].copy()
        settings = params['settings']
        tp_cfg = params['tp_cfg']
        metric = params['metric']
        
        # Minimum values for each level (to prevent HFT-like strategies)
        TP_MINIMUMS = [0.5, 0.8, 1.2, 1.5]  # TP1, TP2, TP3, TP4
        SL_MINIMUM = 1.0
        MAX_VALUE = 200.0
        
        df = calculate_trg(df, settings.trg_atr_length, settings.trg_multiplier)
        if settings.use_supertrend:
            df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
        
        temp_settings = settings.model_copy()
        
        # Validate and apply TP values with proper minimums
        temp_settings.tp1_percent = max(TP_MINIMUMS[0], min(MAX_VALUE, tp_cfg["tp1"]))
        temp_settings.tp2_percent = max(TP_MINIMUMS[1], min(MAX_VALUE, tp_cfg["tp2"]))
        temp_settings.tp3_percent = max(TP_MINIMUMS[2], min(MAX_VALUE, tp_cfg["tp3"]))
        temp_settings.tp4_percent = max(TP_MINIMUMS[3], min(MAX_VALUE, tp_cfg["tp4"]))
        
        # Ensure TPs are in ascending order with minimum distance
        MIN_DISTANCE = 0.2
        tps = [temp_settings.tp1_percent, temp_settings.tp2_percent, temp_settings.tp3_percent, temp_settings.tp4_percent]
        for i in range(1, len(tps)):
            if tps[i] <= tps[i-1] + MIN_DISTANCE:
                tps[i] = tps[i-1] + MIN_DISTANCE
        
        temp_settings.tp1_percent = tps[0]
        temp_settings.tp2_percent = tps[1]
        temp_settings.tp3_percent = tps[2]
        temp_settings.tp4_percent = tps[3]
        
        # Validate SL (minimum 1%)
        if "sl" in tp_cfg:
            temp_settings.sl_percent = max(SL_MINIMUM, min(MAX_VALUE, tp_cfg["sl"]))
        
        df = generate_signals(df, temp_settings)
        trades, equity_curve, _, _, _ = run_backtest(df, temp_settings)
        score, metrics = calculate_optimization_score(trades, equity_curve, settings, metric)
        
        return {
            "tp_cfg": tp_cfg,
            "config": f"TP:{tp_cfg['tp1']:.1f}/{tp_cfg['tp2']:.1f}/{tp_cfg['tp3']:.1f}/{tp_cfg['tp4']:.1f}",
            "score": round(score, 2),
            "profit": metrics.get("profit_pct", 0),
            "win_rate": metrics.get("win_rate", 0),
            "trades": metrics.get("total_trades", 0),
            "metrics": metrics
        }
    except Exception as e:
        return {"tp_cfg": params.get('tp_cfg'), "score": -999, "profit": 0, "win_rate": 0, "trades": 0, "error": str(e)}


def generate_tp_custom_configs(settings: IndicatorSettings, range_pct: float = 50.0, step_pct: float = 10.0) -> list:
    """
    Generate TP configurations based on current settings ±range%
    
    Example: if TP1=1.0 and range=50%, step=10%
    Will test: 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5
    
    Constraints (to avoid HFT-like behavior):
    - TP1 minimum: 0.5%
    - TP2 minimum: 0.8% 
    - TP3 minimum: 1.2%
    - TP4 minimum: 1.5%
    - SL minimum: 1.0%
    - All values max: 200%
    - TPs must be in ascending order (TP1 < TP2 < TP3 < TP4)
    """
    configs = []
    
    # Minimum values for each level (to prevent HFT-like strategies)
    TP_MINIMUMS = {
        0: 0.5,   # TP1 min 0.5%
        1: 0.8,   # TP2 min 0.8%
        2: 1.2,   # TP3 min 1.2%
        3: 1.5,   # TP4 min 1.5%
    }
    SL_MINIMUM = 1.0  # SL min 1%
    MAX_VALUE = 200.0  # Maximum 200%
    
    # Get current TP values
    current_tps = [
        settings.tp1_percent,
        settings.tp2_percent,
        settings.tp3_percent,
        settings.tp4_percent
    ]
    
    current_sl = settings.sl_percent
    
    # Calculate ranges for each TP with minimums
    def get_range_values(base_val, range_pct, step_pct, min_val, max_val=MAX_VALUE):
        # Calculate range boundaries
        min_range = max(min_val, base_val * (1 - range_pct / 100))
        max_range = min(max_val, base_val * (1 + range_pct / 100))
        
        # Calculate step
        step = base_val * (step_pct / 100)
        step = max(0.1, step)  # Minimum step 0.1%
        
        values = []
        val = min_range
        while val <= max_range + 0.001:
            values.append(round(val, 2))
            val += step
        
        # Ensure at least base value is included
        if base_val not in values and min_val <= base_val <= max_val:
            values.append(round(base_val, 2))
            values = sorted(set(values))
        
        return values
    
    # Generate value ranges for each TP with their minimum limits
    tp1_values = get_range_values(current_tps[0], range_pct, step_pct, TP_MINIMUMS[0])
    tp2_values = get_range_values(current_tps[1], range_pct, step_pct, TP_MINIMUMS[1])
    tp3_values = get_range_values(current_tps[2], range_pct, step_pct, TP_MINIMUMS[2])
    tp4_values = get_range_values(current_tps[3], range_pct, step_pct, TP_MINIMUMS[3])
    sl_values = get_range_values(current_sl, range_pct, step_pct, SL_MINIMUM)
    
    # Limit combinations to avoid explosion
    # Take middle values + extremes
    def limit_values(values, max_count=5):
        if len(values) <= max_count:
            return values
        # Take min, max, and evenly spaced middle values
        indices = [0]
        step = (len(values) - 1) / (max_count - 1)
        for i in range(1, max_count - 1):
            indices.append(int(i * step))
        indices.append(len(values) - 1)
        return [values[i] for i in sorted(set(indices))]
    
    tp1_limited = limit_values(tp1_values, 5)
    tp2_limited = limit_values(tp2_values, 5)
    tp3_limited = limit_values(tp3_values, 4)
    tp4_limited = limit_values(tp4_values, 4)
    sl_limited = limit_values(sl_values, 4)
    
    # Generate combinations (with ascending order check and minimum distance)
    MIN_TP_DISTANCE = 0.2  # Minimum 0.2% between consecutive TPs
    
    for tp1 in tp1_limited:
        for tp2 in tp2_limited:
            if tp2 <= tp1 + MIN_TP_DISTANCE:
                continue
            for tp3 in tp3_limited:
                if tp3 <= tp2 + MIN_TP_DISTANCE:
                    continue
                for tp4 in tp4_limited:
                    if tp4 <= tp3 + MIN_TP_DISTANCE:
                        continue
                    for sl in sl_limited:
                        configs.append({
                            "tp1": tp1,
                            "tp2": tp2,
                            "tp3": tp3,
                            "tp4": tp4,
                            "sl": sl
                        })
    
    # If too few configs, add current settings as baseline
    if len(configs) == 0:
        configs.append({
            "tp1": max(TP_MINIMUMS[0], current_tps[0]),
            "tp2": max(TP_MINIMUMS[1], current_tps[1]),
            "tp3": max(TP_MINIMUMS[2], current_tps[2]),
            "tp4": max(TP_MINIMUMS[3], current_tps[3]),
            "sl": max(SL_MINIMUM, current_sl)
        })
    
    return configs


def generate_filter_configs() -> list:
    """Generate filter configurations to test"""
    configs = []
    
    # No filters (baseline)
    configs.append({
        "name": "No filters",
        "use_supertrend": False,
        "use_rsi_filter": False,
        "use_adx_filter": False,
        "use_volume_filter": False
    })
    
    # SuperTrend only - various settings
    for period in [7, 10, 14, 20]:
        for mult in [2.0, 3.0, 4.0]:
            configs.append({
                "name": f"ST({period},{mult})",
                "use_supertrend": True,
                "supertrend_period": period,
                "supertrend_multiplier": mult,
                "use_rsi_filter": False,
                "use_adx_filter": False,
                "use_volume_filter": False
            })
    
    # RSI only - various settings
    for period in [7, 14, 21]:
        for ob in [65, 70, 75]:
            os = 100 - ob
            configs.append({
                "name": f"RSI({period},{ob}/{os})",
                "use_supertrend": False,
                "use_rsi_filter": True,
                "rsi_period": period,
                "rsi_overbought": ob,
                "rsi_oversold": os,
                "use_adx_filter": False,
                "use_volume_filter": False
            })
    
    # ADX only - various settings
    for period in [10, 14, 20]:
        for threshold in [20, 25, 30]:
            configs.append({
                "name": f"ADX({period},{threshold})",
                "use_supertrend": False,
                "use_rsi_filter": False,
                "use_adx_filter": True,
                "adx_period": period,
                "adx_threshold": threshold,
                "use_volume_filter": False
            })
    
    # Volume only
    for period in [10, 20, 30]:
        for threshold in [1.2, 1.5, 2.0]:
            configs.append({
                "name": f"Vol({period},{threshold}x)",
                "use_supertrend": False,
                "use_rsi_filter": False,
                "use_adx_filter": False,
                "use_volume_filter": True,
                "volume_ma_period": period,
                "volume_threshold": threshold
            })
    
    # Combinations
    # SuperTrend + RSI
    configs.append({
        "name": "ST(10,3)+RSI(14)",
        "use_supertrend": True,
        "supertrend_period": 10,
        "supertrend_multiplier": 3.0,
        "use_rsi_filter": True,
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "use_adx_filter": False,
        "use_volume_filter": False
    })
    
    # SuperTrend + ADX
    configs.append({
        "name": "ST(10,3)+ADX(14,25)",
        "use_supertrend": True,
        "supertrend_period": 10,
        "supertrend_multiplier": 3.0,
        "use_rsi_filter": False,
        "use_adx_filter": True,
        "adx_period": 14,
        "adx_threshold": 25,
        "use_volume_filter": False
    })
    
    # RSI + ADX
    configs.append({
        "name": "RSI(14)+ADX(14,25)",
        "use_supertrend": False,
        "use_rsi_filter": True,
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "use_adx_filter": True,
        "adx_period": 14,
        "adx_threshold": 25,
        "use_volume_filter": False
    })
    
    # All filters
    configs.append({
        "name": "ALL filters",
        "use_supertrend": True,
        "supertrend_period": 10,
        "supertrend_multiplier": 3.0,
        "use_rsi_filter": True,
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "use_adx_filter": True,
        "adx_period": 14,
        "adx_threshold": 25,
        "use_volume_filter": True,
        "volume_ma_period": 20,
        "volume_threshold": 1.5
    })
    
    return configs


@router.post("/auto-optimize-stream")
async def auto_optimize_stream(request: AutoOptimizeMode):
    """Auto-optimize with SSE streaming progress and parallel processing"""
    
    settings = request.settings
    mode = request.mode
    metric = request.metric
    
    async def generate():
        filepath = DATA_DIR / f"{settings.symbol}_{settings.timeframe}.parquet"
        if not filepath.exists():
            yield f"data: {json_lib.dumps({'type': 'error', 'message': f'Data not found'})}\n\n"
            return
        
        df_original = pd.read_parquet(filepath)
        df_original = df_original[~df_original.index.duplicated(keep='first')]
        df_original = df_original.sort_index()
        
        yield f"data: {json_lib.dumps({'type': 'progress', 'message': f'Loaded {len(df_original)} candles. Calculating current params...'})}\n\n"
        await asyncio.sleep(0.01)
        
        # Calculate current performance
        df_current = df_original.copy()
        df_current = calculate_trg(df_current, settings.trg_atr_length, settings.trg_multiplier)
        if settings.use_supertrend:
            df_current = calculate_supertrend(df_current, settings.supertrend_period, settings.supertrend_multiplier)
        df_current = generate_signals(df_current, settings)
        current_trades, current_equity, _, _, _ = run_backtest(df_current, settings)
        current_score, current_metrics = calculate_optimization_score(current_trades, current_equity, settings, metric)
        
        yield f"data: {json_lib.dumps({'type': 'current', 'profit': current_metrics.get('profit_pct', 0), 'win_rate': current_metrics.get('win_rate', 0), 'trades': current_metrics.get('total_trades', 0)})}\n\n"
        
        best_result = None
        best_score = float('-inf')
        best_params = {}
        all_results = []
        
        # Total combinations
        filter_configs = generate_filter_configs()
        tp_custom_configs = generate_tp_custom_configs(settings, request.tp_range_percent, request.tp_step_percent)
        full_configs_preview = generate_full_optimization_configs(settings, request.full_mode_depth) if mode == "full" else []
        
        total_map = {
            "indicator": 144, 
            "tp": 16, 
            "sl": 30, 
            "all": 270,
            "filters": len(filter_configs),
            "tp_custom": len(tp_custom_configs),
            "full": len(full_configs_preview)
        }
        total_combinations = total_map.get(mode, 100)
        
        yield f"data: {json_lib.dumps({'type': 'start', 'total': total_combinations, 'mode': mode, 'workers': NUM_WORKERS})}\n\n"
        await asyncio.sleep(0.01)
        
        # Prepare parameter combinations
        param_list = []
        
        if mode == "indicator":
            i1_range = [20, 30, 35, 40, 45, 50, 55, 60, 70, 80, 100, 120]
            i2_range = [1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 7, 8]
            for i1 in i1_range:
                for i2 in i2_range:
                    param_list.append({'df': df_original, 'settings': settings, 'i1': i1, 'i2': i2, 'metric': metric})
        
        elif mode == "sl":
            for sl_pct in [2, 3, 4, 5, 6, 7, 8, 10, 12, 15]:
                for trail_mode in ["no", "breakeven", "moving"]:
                    param_list.append({'df': df_original, 'settings': settings, 'sl_pct': sl_pct, 'trail_mode': trail_mode, 'metric': metric})
        
        elif mode == "tp":
            tp_configs = [
                {"tp1": 0.5, "tp2": 1.0, "tp3": 1.5, "tp4": 2.0, "a1": 40, "a2": 30, "a3": 20, "a4": 10},
                {"tp1": 0.75, "tp2": 1.25, "tp3": 2.0, "tp4": 3.0, "a1": 50, "a2": 25, "a3": 15, "a4": 10},
                {"tp1": 1.0, "tp2": 1.5, "tp3": 2.5, "tp4": 4.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
                {"tp1": 1.0, "tp2": 2.0, "tp3": 3.5, "tp4": 5.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
                {"tp1": 1.05, "tp2": 1.95, "tp3": 3.75, "tp4": 6.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
                {"tp1": 1.25, "tp2": 2.5, "tp3": 4.0, "tp4": 6.5, "a1": 45, "a2": 30, "a3": 15, "a4": 10},
                {"tp1": 1.5, "tp2": 3.0, "tp3": 5.0, "tp4": 8.0, "a1": 40, "a2": 30, "a3": 20, "a4": 10},
                {"tp1": 2.0, "tp2": 4.0, "tp3": 6.0, "tp4": 10.0, "a1": 35, "a2": 30, "a3": 20, "a4": 15},
                {"tp1": 2.5, "tp2": 5.0, "tp3": 8.0, "tp4": 12.0, "a1": 30, "a2": 30, "a3": 25, "a4": 15},
                {"tp1": 0.8, "tp2": 1.5, "tp3": 3.0, "tp4": 5.0, "a1": 60, "a2": 25, "a3": 10, "a4": 5},
                {"tp1": 1.0, "tp2": 2.0, "tp3": 4.0, "tp4": 7.0, "a1": 70, "a2": 20, "a3": 7, "a4": 3},
                {"tp1": 1.0, "tp2": 2.0, "tp3": 3.0, "tp4": 4.0, "a1": 25, "a2": 25, "a3": 25, "a4": 25},
                {"tp1": 1.5, "tp2": 3.0, "tp3": 4.5, "tp4": 6.0, "a1": 25, "a2": 25, "a3": 25, "a4": 25},
                {"tp1": 0.6, "tp2": 1.2, "tp3": 2.0, "tp4": 3.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
                {"tp1": 0.8, "tp2": 1.6, "tp3": 2.8, "tp4": 4.5, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
                {"tp1": 1.2, "tp2": 2.4, "tp3": 4.0, "tp4": 6.0, "a1": 45, "a2": 30, "a3": 15, "a4": 10},
            ]
            for cfg in tp_configs:
                param_list.append({'df': df_original, 'settings': settings, 'cfg': cfg, 'metric': metric})
        
        elif mode == "filters":
            # Optimize filter settings
            for cfg in filter_configs:
                param_list.append({'df': df_original, 'settings': settings, 'filter_cfg': cfg, 'metric': metric})
        
        elif mode == "tp_custom":
            # Optimize TP/SL based on current settings ±range%
            for cfg in tp_custom_configs:
                param_list.append({'df': df_original, 'settings': settings, 'tp_cfg': cfg, 'metric': metric})
        
        elif mode == "all":
            i1_range = [30, 40, 45, 50, 60, 80]
            i2_range = [2, 3, 4, 5, 6]
            tp_presets = [
                {"tp1": 0.8, "tp2": 1.5, "tp3": 2.5, "tp4": 4.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
                {"tp1": 1.0, "tp2": 2.0, "tp3": 3.5, "tp4": 5.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
                {"tp1": 1.5, "tp2": 3.0, "tp3": 5.0, "tp4": 8.0, "a1": 40, "a2": 30, "a3": 20, "a4": 10},
            ]
            sl_configs = [
                {"sl_percent": 4, "sl_trailing_mode": "breakeven"},
                {"sl_percent": 6, "sl_trailing_mode": "breakeven"},
                {"sl_percent": 8, "sl_trailing_mode": "moving"},
            ]
            for i1 in i1_range:
                for i2 in i2_range:
                    for tp_cfg in tp_presets:
                        for sl_cfg in sl_configs:
                            param_list.append({'df': df_original, 'settings': settings, 'i1': i1, 'i2': i2, 'tp_cfg': tp_cfg, 'sl_cfg': sl_cfg, 'metric': metric})
        
        elif mode == "full":
            # FULL optimization: all parameters at once with advanced scoring
            full_configs = generate_full_optimization_configs(settings, request.full_mode_depth)
            total_combinations = len(full_configs)
            
            yield f"data: {json_lib.dumps({'type': 'info', 'message': f'Full optimization: {total_combinations} combinations (mode: {request.full_mode_depth})'})}\n\n"
            
            use_advanced = (metric == "advanced")
            for cfg in full_configs:
                param_list.append({'df': df_original, 'settings': settings, 'cfg': cfg, 'use_advanced_score': use_advanced})
        
        # Select the right function
        func_map = {
            "indicator": run_single_backtest_indicator,
            "sl": run_single_backtest_sl,
            "tp": run_single_backtest_tp,
            "all": run_single_backtest_all,
            "filters": run_single_backtest_filters,
            "tp_custom": run_single_backtest_tp_custom,
            "full": run_single_backtest_full
        }
        backtest_func = func_map.get(mode)
        
        if backtest_func is None:
            yield f"data: {json_lib.dumps({'type': 'error', 'message': f'Unknown mode: {mode}'})}\n\n"
            return
        
        # Run parallel optimization
        tested_count = 0
        loop = asyncio.get_event_loop()
        
        with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
            # Submit all tasks
            futures = {executor.submit(backtest_func, params): params for params in param_list}
            
            # Process results as they complete
            for future in as_completed(futures):
                tested_count += 1
                result = future.result()
                all_results.append(result)
                
                is_best = result.get('score', -999) > best_score
                if is_best:
                    best_score = result['score']
                    best_result = result.get('metrics', result)
                    
                    if mode == "indicator":
                        best_params = {"trg_atr_length": result['i1'], "trg_multiplier": result['i2']}
                    elif mode == "sl":
                        best_params = {"sl_percent": result['sl'], "sl_trailing_mode": result['mode']}
                    elif mode == "tp":
                        cfg = result['cfg']
                        best_params = {
                            "tp1_percent": cfg["tp1"], "tp2_percent": cfg["tp2"],
                            "tp3_percent": cfg["tp3"], "tp4_percent": cfg["tp4"],
                            "tp1_amount": cfg["a1"], "tp2_amount": cfg["a2"],
                            "tp3_amount": cfg["a3"], "tp4_amount": cfg["a4"]
                        }
                    elif mode == "all":
                        tp_cfg = result['tp_cfg']
                        sl_cfg = result['sl_cfg']
                        best_params = {
                            "trg_atr_length": result['i1'], "trg_multiplier": result['i2'],
                            "tp1_percent": tp_cfg["tp1"], "tp2_percent": tp_cfg["tp2"],
                            "tp3_percent": tp_cfg["tp3"], "tp4_percent": tp_cfg["tp4"],
                            "tp1_amount": tp_cfg["a1"], "tp2_amount": tp_cfg["a2"],
                            "tp3_amount": tp_cfg["a3"], "tp4_amount": tp_cfg["a4"],
                            "sl_percent": sl_cfg["sl_percent"],
                            "sl_trailing_mode": sl_cfg["sl_trailing_mode"]
                        }
                    elif mode == "full":
                        cfg = result['cfg']
                        best_params = {
                            # Indicator
                            "trg_atr_length": cfg.get('i1'),
                            "trg_multiplier": cfg.get('i2'),
                            # TP levels
                            "tp1_percent": cfg.get('tp1'),
                            "tp2_percent": cfg.get('tp2'),
                            "tp3_percent": cfg.get('tp3'),
                            "tp4_percent": cfg.get('tp4'),
                            # SL
                            "sl_percent": cfg.get('sl'),
                            "sl_trailing_mode": cfg.get('sl_mode'),
                            # Filters
                            "use_supertrend": cfg.get('use_st', False),
                            "supertrend_period": cfg.get('st_period', 10),
                            "supertrend_multiplier": cfg.get('st_mult', 3.0),
                            "use_rsi_filter": cfg.get('use_rsi', False),
                            "rsi_period": cfg.get('rsi_period', 14),
                            "use_adx_filter": cfg.get('use_adx', False),
                            "adx_threshold": cfg.get('adx_threshold', 25),
                            # Re-entry
                            "allow_reentry": cfg.get('allow_reentry', True),
                            "reentry_after_sl": cfg.get('reentry_sl', True),
                            "reentry_after_tp": cfg.get('reentry_tp', False),
                        }
                    elif mode == "filters":
                        filter_cfg = result['filter_cfg']
                        best_params = {
                            "use_supertrend": filter_cfg.get('use_supertrend', False),
                            "supertrend_period": filter_cfg.get('supertrend_period', 10),
                            "supertrend_multiplier": filter_cfg.get('supertrend_multiplier', 3.0),
                            "use_rsi_filter": filter_cfg.get('use_rsi_filter', False),
                            "rsi_period": filter_cfg.get('rsi_period', 14),
                            "rsi_overbought": filter_cfg.get('rsi_overbought', 70),
                            "rsi_oversold": filter_cfg.get('rsi_oversold', 30),
                            "use_adx_filter": filter_cfg.get('use_adx_filter', False),
                            "adx_period": filter_cfg.get('adx_period', 14),
                            "adx_threshold": filter_cfg.get('adx_threshold', 25),
                            "use_volume_filter": filter_cfg.get('use_volume_filter', False),
                            "volume_ma_period": filter_cfg.get('volume_ma_period', 20),
                            "volume_threshold": filter_cfg.get('volume_threshold', 1.5),
                            "filter_name": filter_cfg.get('name', 'Custom')
                        }
                    elif mode == "tp_custom":
                        tp_cfg = result['tp_cfg']
                        best_params = {
                            "tp1_percent": tp_cfg["tp1"],
                            "tp2_percent": tp_cfg["tp2"],
                            "tp3_percent": tp_cfg["tp3"],
                            "tp4_percent": tp_cfg["tp4"],
                            "sl_percent": tp_cfg.get("sl", settings.sl_percent)
                        }
                
                # Format params string for display
                if mode == "indicator":
                    params_str = f"i1={result.get('i1')} i2={result.get('i2')}"
                elif mode == "sl":
                    params_str = f"SL={result.get('sl')}% {result.get('mode')}"
                elif mode == "tp":
                    params_str = result.get('config', 'TP config')
                elif mode == "all":
                    params_str = f"i1={result.get('i1')} i2={result.get('i2')} SL={result.get('sl_cfg', {}).get('sl_percent', '?')}%"
                elif mode == "full":
                    cfg = result.get('cfg', {})
                    params_str = f"i1={cfg.get('i1')} i2={cfg.get('i2')} TP1={cfg.get('tp1')} SL={cfg.get('sl')}% {cfg.get('sl_mode', 'be')}"
                elif mode == "filters":
                    params_str = result.get('config', result.get('filter_cfg', {}).get('name', 'Filter'))
                elif mode == "tp_custom":
                    params_str = result.get('config', 'TP custom')
                else:
                    params_str = "Unknown"
                
                # Send progress (every result or every 5th/10th for heavy modes)
                send_progress = True
                if mode == "all" and tested_count % 5 != 0 and not is_best:
                    send_progress = False
                elif mode == "full" and tested_count % 10 != 0 and not is_best:
                    send_progress = False
                
                if send_progress:
                    # Convert numpy types to Python native types for JSON
                    progress_data = {
                        'type': 'test', 
                        'n': tested_count, 
                        'total': len(param_list),
                        'params': params_str, 
                        'profit': float(result.get('profit', 0)), 
                        'win_rate': float(result.get('win_rate', 0)),
                        'tp1_hit': float(result.get('tp1_hit', 0)) if mode == "full" else None,
                        'max_dd': float(result.get('max_dd', 0)) if mode == "full" else None,
                        'is_best': bool(is_best)
                    }
                    
                    # For best result, include full config details
                    if is_best:
                        if mode == "full":
                            cfg = result.get('cfg', {})
                            progress_data['best_config'] = {
                                'trg': f"i1={cfg.get('i1')} i2={cfg.get('i2')}",
                                'tp': f"TP1={cfg.get('tp1')}% TP2={cfg.get('tp2')}% TP3={cfg.get('tp3')}% TP4={cfg.get('tp4')}%",
                                'sl': f"SL={cfg.get('sl')}% ({cfg.get('sl_mode')})",
                                'filters': [],
                                'reentry': cfg.get('allow_reentry', False)
                            }
                            if cfg.get('use_st'):
                                progress_data['best_config']['filters'].append(f"ST({cfg.get('st_period')},{cfg.get('st_mult')})")
                            if cfg.get('use_rsi'):
                                progress_data['best_config']['filters'].append(f"RSI({cfg.get('rsi_period')})")
                            if cfg.get('use_adx'):
                                progress_data['best_config']['filters'].append(f"ADX({cfg.get('adx_threshold')})")
                            if not progress_data['best_config']['filters']:
                                progress_data['best_config']['filters'] = ['None']
                        elif mode == "indicator":
                            progress_data['best_config'] = {
                                'trg': f"i1={result.get('i1')} i2={result.get('i2')}"
                            }
                        elif mode == "sl":
                            progress_data['best_config'] = {
                                'sl': f"SL={result.get('sl')}% ({result.get('mode')})"
                            }
                        elif mode == "tp" or mode == "tp_custom":
                            cfg = result.get('cfg', result.get('tp_cfg', {}))
                            progress_data['best_config'] = {
                                'tp': f"TP1={cfg.get('tp1')}% TP2={cfg.get('tp2')}% TP3={cfg.get('tp3')}% TP4={cfg.get('tp4')}%",
                                'sl': f"SL={cfg.get('sl', '?')}%"
                            }
                        elif mode == "filters":
                            filter_cfg = result.get('filter_cfg', {})
                            progress_data['best_config'] = {
                                'name': filter_cfg.get('name', 'Custom'),
                                'details': filter_cfg
                            }
                    
                    # Remove None values
                    progress_data = {k: v for k, v in progress_data.items() if v is not None}
                    yield f"data: {json_lib.dumps(progress_data)}\n\n"
                    await asyncio.sleep(0.001)
        
        # Sort and get top 10
        all_results_sorted = sorted(all_results, key=lambda x: x.get('score', 0), reverse=True)[:10]
        
        # Clean up results for JSON
        for r in all_results_sorted:
            if 'metrics' in r:
                del r['metrics']
            if 'cfg' in r:
                del r['cfg']
            if 'tp_cfg' in r:
                del r['tp_cfg']
            if 'sl_cfg' in r:
                del r['sl_cfg']
            if 'filter_cfg' in r:
                del r['filter_cfg']
        
        improvement = {
            "profit_change": float(round((best_result.get("profit_pct", 0) - current_metrics.get("profit_pct", 0)), 2)) if best_result else 0,
            "win_rate_change": float(round((best_result.get("win_rate", 0) - current_metrics.get("win_rate", 0)), 2)) if best_result else 0,
        }
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy(v) for v in obj]
            elif isinstance(obj, (np.integer, np.floating)):
                return float(obj)
            elif isinstance(obj, np.bool_):
                return bool(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        final_result = {
            "type": "done",
            "success": True,
            "mode": mode,
            "tested_combinations": tested_count,
            "workers_used": NUM_WORKERS,
            "current_params": {"trg_atr_length": settings.trg_atr_length, "trg_multiplier": float(settings.trg_multiplier), "tp1_percent": float(settings.tp1_percent), "sl_percent": float(settings.sl_percent)},
            "current_result": {"profit_pct": float(current_metrics.get("profit_pct", 0)), "win_rate": float(current_metrics.get("win_rate", 0)), "total_trades": int(current_metrics.get("total_trades", 0))},
            "best_params": convert_numpy(best_params),
            "best_score": float(round(best_score, 2)) if best_score != float('-inf') else 0,
            "best_result": convert_numpy(best_result) if best_result else {},
            "improvement": improvement,
            "top_10_results": convert_numpy(all_results_sorted)
        }
        
        yield f"data: {json_lib.dumps(final_result)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


async def run_adaptive_optimization(df_original: pd.DataFrame, settings: IndicatorSettings, metric: str, lookback_months: int, reoptimize_period: str):
    """
    Walk-Forward Adaptive Optimization
    - Split data into periods
    - For each period: optimize on previous N months, trade on current period
    - Parameters change dynamically over time
    - Properly handles partial TP closes
    """
    
    # Get unique months
    df_original['month'] = df_original.index.to_period('M')
    months = df_original['month'].unique()
    
    if len(months) < lookback_months + 1:
        raise HTTPException(400, f"Not enough data. Need at least {lookback_months + 1} months")
    
    # Parameter search space
    i1_range = [30, 40, 45, 50, 60, 80]
    i2_range = [2, 3, 4, 5, 6]
    
    # TP presets for optimization
    tp_presets = [
        {"tp1": 1.0, "tp2": 2.0, "tp3": 3.5, "tp4": 5.0},
        {"tp1": 0.8, "tp2": 1.5, "tp3": 2.5, "tp4": 4.0},
        {"tp1": 1.5, "tp2": 3.0, "tp3": 5.0, "tp4": 8.0},
    ]
    
    # SL presets
    sl_presets = [4, 6, 8]
    
    all_trades = []
    equity_history = []
    capital = settings.initial_capital
    period_results = []
    params_history = []
    
    # Track TP statistics
    total_tp_stats = {"tp1": 0, "tp2": 0, "tp3": 0, "tp4": 0, "sl": 0, "reverse": 0}
    
    # Start from lookback_months onwards
    for period_idx in range(lookback_months, len(months)):
        current_month = months[period_idx]
        
        # Training period: previous N months
        train_months = months[period_idx - lookback_months:period_idx]
        train_df = df_original[df_original['month'].isin(train_months)].copy()
        
        # Test period: current month
        test_df = df_original[df_original['month'] == current_month].copy()
        
        if len(train_df) < 100 or len(test_df) < 10:
            continue
        
        # Find best params on training data
        best_score = float('-inf')
        best_params = {
            "i1": settings.trg_atr_length,
            "i2": settings.trg_multiplier,
            "tp": {"tp1": settings.tp1_percent, "tp2": settings.tp2_percent, "tp3": settings.tp3_percent, "tp4": settings.tp4_percent},
            "sl": settings.sl_percent
        }
        
        # Optimize i1/i2
        for i1 in i1_range:
            for i2 in i2_range:
                df_train = train_df.copy()
                df_train = calculate_trg(df_train, i1, i2)
                if settings.use_supertrend:
                    df_train = calculate_supertrend(df_train, settings.supertrend_period, settings.supertrend_multiplier)
                
                temp_settings = settings.model_copy()
                temp_settings.trg_atr_length = i1
                temp_settings.trg_multiplier = i2
                
                df_train = generate_signals(df_train, temp_settings)
                trades, eq, _, _, _ = run_backtest(df_train, temp_settings)
                
                if trades and eq:
                    score, _ = calculate_optimization_score(trades, eq, temp_settings, metric)
                    
                    if score > best_score:
                        best_score = score
                        best_params["i1"] = i1
                        best_params["i2"] = i2
        
        # Optionally optimize TP presets (quick)
        for tp_cfg in tp_presets:
            df_train = train_df.copy()
            df_train = calculate_trg(df_train, best_params["i1"], best_params["i2"])
            if settings.use_supertrend:
                df_train = calculate_supertrend(df_train, settings.supertrend_period, settings.supertrend_multiplier)
            
            temp_settings = settings.model_copy()
            temp_settings.trg_atr_length = best_params["i1"]
            temp_settings.trg_multiplier = best_params["i2"]
            temp_settings.tp1_percent = tp_cfg["tp1"]
            temp_settings.tp2_percent = tp_cfg["tp2"]
            temp_settings.tp3_percent = tp_cfg["tp3"]
            temp_settings.tp4_percent = tp_cfg["tp4"]
            
            df_train = generate_signals(df_train, temp_settings)
            trades, eq, _, _, _ = run_backtest(df_train, temp_settings)
            
            if trades and eq:
                score, _ = calculate_optimization_score(trades, eq, temp_settings, metric)
                
                if score > best_score:
                    best_score = score
                    best_params["tp"] = tp_cfg
        
        # Apply best params to test period
        df_test = test_df.copy()
        df_test = calculate_trg(df_test, best_params["i1"], best_params["i2"])
        if settings.use_supertrend:
            df_test = calculate_supertrend(df_test, settings.supertrend_period, settings.supertrend_multiplier)
        
        temp_settings = settings.model_copy()
        temp_settings.trg_atr_length = best_params["i1"]
        temp_settings.trg_multiplier = best_params["i2"]
        temp_settings.tp1_percent = best_params["tp"]["tp1"]
        temp_settings.tp2_percent = best_params["tp"]["tp2"]
        temp_settings.tp3_percent = best_params["tp"]["tp3"]
        temp_settings.tp4_percent = best_params["tp"]["tp4"]
        temp_settings.initial_capital = capital  # Continue with current capital
        
        df_test = generate_signals(df_test, temp_settings)
        trades, eq, monthly, tp_stats, _ = run_backtest(df_test, temp_settings)
        
        # Update capital from trades (not equity curve which resets)
        period_pnl_amount = 0
        for t in trades:
            period_pnl_amount += t.get('pnl_amount', 0)
            
            # Track TP stats
            exit_reason = t.get('exit_reason', '')
            if exit_reason.startswith('TP'):
                tp_num = exit_reason.lower()
                if tp_num in total_tp_stats:
                    total_tp_stats[tp_num] += 1
            elif exit_reason == 'SL':
                total_tp_stats['sl'] += 1
            elif exit_reason == 'Reverse':
                total_tp_stats['reverse'] += 1
        
        capital += period_pnl_amount
        
        # Record equity point
        equity_history.append({
            "month": str(current_month),
            "capital": round(capital, 2),
            "pnl": round(period_pnl_amount, 2)
        })
        
        all_trades.extend(trades)
        
        # Record period result with ALL info
        period_pnl_pct = (period_pnl_amount / (capital - period_pnl_amount)) * 100 if (capital - period_pnl_amount) > 0 else 0
        period_wins = len([t for t in trades if t.get('pnl', 0) > 0])
        period_wr = (period_wins / len(trades) * 100) if trades else 0
        
        # Count TP hits in this period
        period_tp_hits = {"tp1": 0, "tp2": 0, "tp3": 0, "tp4": 0}
        for t in trades:
            tp_hit_list = t.get('tp_hit', [])
            for tp_num in tp_hit_list:
                if 1 <= tp_num <= 4:
                    period_tp_hits[f"tp{tp_num}"] += 1
        
        period_results.append({
            "month": str(current_month),
            "i1": best_params["i1"],
            "i2": best_params["i2"],
            "tp1": best_params["tp"]["tp1"],
            "sl": best_params["sl"],
            "trades": len(trades),
            "wins": period_wins,
            "win_rate": round(period_wr, 1),
            "pnl_pct": round(period_pnl_pct, 2),
            "pnl_amount": round(period_pnl_amount, 2),
            "capital": round(capital, 2),
            "tp_hits": period_tp_hits
        })
        
        params_history.append({
            "month": str(current_month),
            "i1": best_params["i1"],
            "i2": best_params["i2"],
            "tp1": best_params["tp"]["tp1"],
            "tp2": best_params["tp"]["tp2"],
            "tp3": best_params["tp"]["tp3"],
            "tp4": best_params["tp"]["tp4"]
        })
    
    # Calculate final statistics
    if all_trades:
        wins = len([t for t in all_trades if t.get('pnl', 0) > 0])
        final_profit = ((capital / settings.initial_capital) - 1) * 100
        
        # Calculate average win/loss
        winning_pnls = [t.get('pnl', 0) for t in all_trades if t.get('pnl', 0) > 0]
        losing_pnls = [t.get('pnl', 0) for t in all_trades if t.get('pnl', 0) < 0]
        avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0
        avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0
        profit_factor = sum(winning_pnls) / abs(sum(losing_pnls)) if losing_pnls and sum(losing_pnls) != 0 else 999
        
        # TP hit rates
        tp_hit_rates = {}
        for tp_name, count in total_tp_stats.items():
            tp_hit_rates[tp_name] = round(count / len(all_trades) * 100, 1) if all_trades else 0
        
        return {
            "success": True,
            "mode": "adaptive",
            "metric": metric,
            "lookback_months": lookback_months,
            "total_trades": len(all_trades),
            "wins": wins,
            "losses": len(all_trades) - wins,
            "win_rate": round(wins / len(all_trades) * 100, 2) if all_trades else 0,
            "avg_win": round(avg_win, 2),
            "avg_loss": round(avg_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "final_profit_pct": round(final_profit, 2),
            "initial_capital": settings.initial_capital,
            "final_capital": round(capital, 2),
            "tp_hit_rates": tp_hit_rates,
            "period_results": period_results,
            "equity_history": equity_history,
            "params_history": params_history,
            "best_params": {
                "adaptive": True,
                "lookback_months": lookback_months,
                "periods_tested": len(period_results),
                "note": "Parameters optimized monthly based on previous performance"
            }
        }
    
    return {"success": False, "error": "No trades generated"}


def calculate_optimization_score(trades, equity_curve, settings, metric: str):
    """Calculate optimization score based on selected metric"""
    
    if not trades or not equity_curve:
        return float('-inf'), {}
    
    # Use advanced scoring if metric is "advanced"
    if metric == "advanced":
        return calculate_advanced_score(trades, equity_curve, settings)
    
    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    
    final_capital = equity_curve[-1]['value']
    profit_pct = ((final_capital / settings.initial_capital) - 1) * 100
    win_rate = len(wins) / len(trades) * 100 if trades else 0
    profit_factor = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else 999
    
    # Calculate Sharpe-like ratio
    if len(pnls) > 1:
        avg_return = float(np.mean(pnls))
        std_return = float(np.std(pnls))
        sharpe = avg_return / std_return if std_return > 0 else 0
    else:
        sharpe = 0.0
    
    # Max drawdown
    peak = settings.initial_capital
    max_dd = 0
    for eq in equity_curve:
        if eq['value'] > peak:
            peak = eq['value']
        dd = (peak - eq['value']) / peak * 100
        if dd > max_dd:
            max_dd = dd
    
    # TP1 hit rate (important for BE strategy)
    tp1_hits = sum(1 for t in trades if 1 in t.get('tp_hit', []))
    tp1_hit_rate = (tp1_hits / len(trades) * 100) if trades else 0
    
    # Convert all to native Python types
    metrics = {
        "profit_pct": float(round(profit_pct, 2)),
        "win_rate": float(round(win_rate, 2)),
        "profit_factor": float(round(min(profit_factor, 99.99), 2)),
        "sharpe": float(round(sharpe, 2)),
        "max_drawdown": float(round(max_dd, 2)),
        "total_trades": int(len(trades)),
        "final_capital": float(round(final_capital, 2)),
        "tp1_hit_rate": float(round(tp1_hit_rate, 2))
    }
    
    # Calculate score based on metric
    if metric == "profit":
        score = profit_pct
    elif metric == "winrate":
        score = win_rate
    elif metric == "sharpe":
        score = sharpe
    elif metric == "profit_factor":
        score = profit_factor if profit_factor < 100 else profit_pct
    else:
        # Combined score
        score = (profit_pct * 0.4) + (win_rate * 0.3) + (sharpe * 10 * 0.2) - (max_dd * 0.1)
    
    # Penalize if too few trades
    if len(trades) < 20:
        score *= 0.5
    
    return float(score), metrics


# ============ CALCULATION FUNCTIONS ============

def calculate_trg(df: pd.DataFrame, atr_length: int, multiplier: float) -> pd.DataFrame:
    """Calculate TRG indicator"""
    
    # ATR
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # RMA (Wilder's smoothing)
    atr = tr.ewm(alpha=1/atr_length, adjust=False).mean()
    
    # Bands
    hl2 = (high + low) / 2
    df['trg_upper'] = hl2 + (multiplier * atr)
    df['trg_lower'] = hl2 - (multiplier * atr)
    df['trg_atr'] = atr
    
    # Trend direction
    df['trg_trend'] = 0
    trend = 0
    
    for i in range(1, len(df)):
        prev_upper = df['trg_upper'].iloc[i-1]
        prev_lower = df['trg_lower'].iloc[i-1]
        curr_close = close.iloc[i]
        
        if curr_close > prev_upper:
            trend = 1
        elif curr_close < prev_lower:
            trend = -1
        # else: keep previous trend
        
        df.iloc[i, df.columns.get_loc('trg_trend')] = trend
    
    # Debug
    trend_values = df['trg_trend'].value_counts().to_dict()
    trend_changes = (df['trg_trend'] != df['trg_trend'].shift(1)).sum()
    print(f"[DEBUG calculate_trg] i1={atr_length}, i2={multiplier}, trends: {trend_values}, changes: {trend_changes}")
    
    # TRG line (follows trend)
    df['trg_line'] = np.where(df['trg_trend'] == 1, df['trg_lower'], df['trg_upper'])
    
    return df


def calculate_supertrend(df: pd.DataFrame, period: int, multiplier: float) -> pd.DataFrame:
    """Calculate SuperTrend indicator"""
    
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr = pd.concat([
        high - low,
        abs(high - close.shift(1)),
        abs(low - close.shift(1))
    ], axis=1).max(axis=1)
    
    atr = tr.rolling(period).mean()
    
    hl2 = (high + low) / 2
    upper = hl2 + (multiplier * atr)
    lower = hl2 - (multiplier * atr)
    
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)
    
    for i in range(period, len(df)):
        if close.iloc[i] > upper.iloc[i-1]:
            direction.iloc[i] = 1
        elif close.iloc[i] < lower.iloc[i-1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1] if i > period else 1
        
        if direction.iloc[i] == 1:
            supertrend.iloc[i] = lower.iloc[i]
        else:
            supertrend.iloc[i] = upper.iloc[i]
    
    df['supertrend'] = supertrend
    df['supertrend_dir'] = direction
    
    return df


def calculate_rsi(df: pd.DataFrame, period: int) -> pd.DataFrame:
    """Calculate RSI"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df


def calculate_adx(df: pd.DataFrame, period: int) -> pd.DataFrame:
    """Calculate ADX"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    plus_dm = high.diff()
    minus_dm = low.diff().abs()
    
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    tr = pd.concat([
        high - low,
        abs(high - close.shift(1)),
        abs(low - close.shift(1))
    ], axis=1).max(axis=1)
    
    atr = tr.rolling(period).mean()
    plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
    
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    df['adx'] = dx.rolling(period).mean()
    
    return df


def generate_signals(df: pd.DataFrame, settings: IndicatorSettings) -> pd.DataFrame:
    """Generate entry signals"""
    
    df['signal'] = 0
    
    # TRG signals
    trend_change_long = (df['trg_trend'] == 1) & (df['trg_trend'].shift(1) == -1)
    trend_change_short = (df['trg_trend'] == -1) & (df['trg_trend'].shift(1) == 1)
    
    long_count = trend_change_long.sum()
    short_count = trend_change_short.sum()
    
    # Apply filters
    long_filter = pd.Series(True, index=df.index)
    short_filter = pd.Series(True, index=df.index)
    
    if settings.use_supertrend and 'supertrend_dir' in df.columns:
        long_filter &= df['supertrend_dir'] == 1
        short_filter &= df['supertrend_dir'] == -1
    
    if settings.use_rsi_filter and 'rsi' in df.columns:
        long_filter &= df['rsi'] < settings.rsi_overbought
        short_filter &= df['rsi'] > settings.rsi_oversold
    
    if settings.use_adx_filter and 'adx' in df.columns:
        long_filter &= df['adx'] > settings.adx_threshold
        short_filter &= df['adx'] > settings.adx_threshold
    
    df.loc[trend_change_long & long_filter, 'signal'] = 1
    df.loc[trend_change_short & short_filter, 'signal'] = -1
    
    final_long = (df['signal'] == 1).sum()
    final_short = (df['signal'] == -1).sum()
    print(f"[DEBUG generate_signals] Trend changes: long={long_count}, short={short_count}, After filters: long={final_long}, short={final_short}")
    
    return df


def run_backtest(df: pd.DataFrame, settings: IndicatorSettings, adaptive_mode: str = None):
    """
    Run backtest with proper Partial TP Close and trailing SL
    
    Now supports:
    - Leverage: multiplies PnL (e.g., 10x leverage = 10x profits AND losses)
    - Commission: deducted on entry and exit (e.g., 0.1% per side = 0.2% round trip)
    
    adaptive_mode options:
    - None: Use fixed parameters
    - "indicator": Re-optimize i1/i2 every N trades
    - "tp": Re-optimize TP levels every N trades  
    - "all": Re-optimize everything every N trades
    """
    
    trades = []
    equity_curve = []
    monthly_stats = {}
    capital = settings.initial_capital
    
    # Leverage and commission settings
    leverage = max(1.0, settings.leverage)  # Minimum 1x
    use_commission = settings.use_commission
    commission_pct = settings.commission_percent if use_commission else 0.0
    
    # Adaptive optimization settings
    REOPTIMIZE_EVERY = 20  # Re-optimize after every N trades
    LOOKBACK_CANDLES = 500  # Use last N candles for optimization
    
    # Current active parameters (can change during backtest)
    active_i1 = settings.trg_atr_length
    active_i2 = settings.trg_multiplier
    active_tp_levels = [
        settings.tp1_percent, settings.tp2_percent, settings.tp3_percent,
        settings.tp4_percent, settings.tp5_percent, settings.tp6_percent,
        settings.tp7_percent, settings.tp8_percent, settings.tp9_percent,
        settings.tp10_percent
    ][:settings.tp_count]
    active_sl = settings.sl_percent
    
    # Track parameter changes
    param_changes = []
    last_optimization_trade = 0
    
    # TP amounts (fixed)
    tp_amounts = [
        settings.tp1_amount, settings.tp2_amount, settings.tp3_amount,
        settings.tp4_amount, settings.tp5_amount, settings.tp6_amount,
        settings.tp7_amount, settings.tp8_amount, settings.tp9_amount,
        settings.tp10_amount
    ][:settings.tp_count]
    
    total_amount = sum(tp_amounts)
    if total_amount > 0:
        tp_amounts = [a / total_amount * 100 for a in tp_amounts]
    
    # TP hit tracking
    tp_stats = {f"tp{i+1}_hits": 0 for i in range(settings.tp_count)}
    tp_stats["total_trades"] = 0
    
    # Commission tracking
    total_commission_paid = 0.0
    
    position = None
    last_exit_reason = None
    last_exit_trend = None
    
    # Check if indicators already calculated (from calculate_indicator)
    if 'trg_trend' not in df.columns:
        df = calculate_trg(df, active_i1, active_i2)
        if settings.use_supertrend:
            df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
        df = generate_signals(df, settings)
    
    # Debug signal count
    signal_count = (df['signal'] != 0).sum()
    if signal_count == 0:
        print(f"[DEBUG run_backtest] WARNING: No signals found in {len(df)} candles!")
        print(f"[DEBUG] trg_trend unique values: {df['trg_trend'].unique()}")
        print(f"[DEBUG] trg_trend value counts: {df['trg_trend'].value_counts().to_dict()}")
    
    for i in range(len(df)):
        row = df.iloc[i]
        timestamp = df.index[i]
        current_trend = int(row.get('trg_trend', 0))
        month_key = timestamp.strftime("%Y-%m")
        
        # Initialize month stats
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {
                "trades": 0, "wins": 0, "losses": 0,
                "pnl": 0, "pnl_amount": 0,
                "long_trades": 0, "short_trades": 0,
                "tp1_hits": 0, "tp2_hits": 0, "tp3_hits": 0, "tp4_hits": 0
            }
        
        # === ADAPTIVE OPTIMIZATION: Re-optimize parameters periodically ===
        if adaptive_mode and len(trades) > 0 and len(trades) - last_optimization_trade >= REOPTIMIZE_EVERY:
            if i > LOOKBACK_CANDLES:
                # Get lookback data
                lookback_df = df.iloc[i - LOOKBACK_CANDLES:i].copy()
                
                new_params = optimize_on_lookback(
                    lookback_df, settings, adaptive_mode,
                    active_i1, active_i2, active_tp_levels, active_sl
                )
                
                if new_params:
                    params_changed = False
                    
                    if adaptive_mode in ["indicator", "all"]:
                        if new_params.get('i1') != active_i1 or new_params.get('i2') != active_i2:
                            active_i1 = new_params.get('i1', active_i1)
                            active_i2 = new_params.get('i2', active_i2)
                            params_changed = True
                            
                            # Recalculate TRG with new parameters for remaining data
                            remaining_df = df.iloc[i:].copy()
                            remaining_df = calculate_trg(remaining_df, active_i1, active_i2)
                            if settings.use_supertrend:
                                remaining_df = calculate_supertrend(remaining_df, settings.supertrend_period, settings.supertrend_multiplier)
                            remaining_df = generate_signals(remaining_df, settings)
                            
                            # Update df with new calculations
                            for col in remaining_df.columns:
                                df.loc[remaining_df.index, col] = remaining_df[col]
                    
                    if adaptive_mode in ["tp", "all"]:
                        if new_params.get('tp_levels'):
                            active_tp_levels = new_params['tp_levels']
                            params_changed = True
                    
                    if adaptive_mode == "all":
                        if new_params.get('sl') and new_params['sl'] != active_sl:
                            active_sl = new_params['sl']
                            params_changed = True
                    
                    if params_changed:
                        param_changes.append({
                            "trade_num": len(trades),
                            "timestamp": timestamp.isoformat(),
                            "i1": active_i1,
                            "i2": active_i2,
                            "tp1": active_tp_levels[0] if active_tp_levels else None,
                            "sl": active_sl
                        })
                
                last_optimization_trade = len(trades)
        
        # Reload row after potential recalculation
        row = df.iloc[i]
        
        # Check position updates (TP hits, SL)
        if position:
            high = row['high']
            low = row['low']
            close = row['close']
            
            # Update trailing prices
            if position['type'] == 'long':
                position['highest_price'] = max(position['highest_price'], high)
            else:
                position['lowest_price'] = min(position['lowest_price'], low)
            
            # Check each TP level (partial close)
            for tp_idx in range(len(position['tp_levels_active'])):
                if tp_idx in position['tp_closed']:
                    continue
                
                tp_price = position['tp_prices'][tp_idx]
                tp_amount_pct = tp_amounts[tp_idx]
                
                tp_hit = False
                if position['type'] == 'long' and high >= tp_price:
                    tp_hit = True
                elif position['type'] == 'short' and low <= tp_price:
                    tp_hit = True
                
                if tp_hit:
                    portion_size = position['entry_capital'] * (tp_amount_pct / 100)
                    
                    if position['type'] == 'long':
                        portion_pnl_pct = position['tp_levels_active'][tp_idx]
                    else:
                        portion_pnl_pct = position['tp_levels_active'][tp_idx]
                    
                    # Apply leverage to PnL
                    portion_pnl_pct_leveraged = portion_pnl_pct * leverage
                    
                    # Deduct exit commission for this portion
                    exit_commission = portion_size * (commission_pct / 100) if use_commission else 0
                    
                    portion_pnl = portion_size * (portion_pnl_pct_leveraged / 100) - exit_commission
                    position['commission_paid'] = position.get('commission_paid', 0) + exit_commission
                    
                    position['realized_pnl'] += portion_pnl
                    position['remaining_pct'] -= tp_amount_pct
                    position['tp_closed'].append(tp_idx)
                    position['tp_hit'].append(tp_idx + 1)
                    
                    tp_stats[f"tp{tp_idx + 1}_hits"] += 1
                    monthly_stats[month_key][f"tp{tp_idx + 1}_hits"] = monthly_stats[month_key].get(f"tp{tp_idx + 1}_hits", 0) + 1
                    
                    # Update trailing SL
                    if settings.sl_trailing_mode == 'breakeven' and len(position['tp_closed']) == 1:
                        position['sl_price'] = position['entry_price']
                    elif settings.sl_trailing_mode == 'moving':
                        if len(position['tp_closed']) > 1:
                            prev_tp_idx = position['tp_closed'][-2]
                            position['sl_price'] = position['tp_prices'][prev_tp_idx]
                        else:
                            position['sl_price'] = position['entry_price']
            
            all_tp_closed = position['remaining_pct'] <= 0.01
            
            # Check SL
            sl_hit = False
            if position['type'] == 'long' and low <= position['sl_price']:
                sl_hit = True
            elif position['type'] == 'short' and high >= position['sl_price']:
                sl_hit = True
            
            # Check reverse signal
            reverse_signal = False
            if row['signal'] != 0:
                if (position['type'] == 'long' and row['signal'] == -1) or \
                   (position['type'] == 'short' and row['signal'] == 1):
                    reverse_signal = True
            
            # Close position
            if all_tp_closed or sl_hit or reverse_signal:
                if position['remaining_pct'] > 0.01:
                    remaining_size = position['entry_capital'] * (position['remaining_pct'] / 100)
                    
                    if sl_hit:
                        exit_price = position['sl_price']
                    else:
                        exit_price = close
                    
                    if position['type'] == 'long':
                        remaining_pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100
                    else:
                        remaining_pnl_pct = (position['entry_price'] - exit_price) / position['entry_price'] * 100
                    
                    # Apply leverage to remaining PnL
                    remaining_pnl_pct_leveraged = remaining_pnl_pct * leverage
                    
                    # Deduct exit commission for remaining portion
                    exit_commission = remaining_size * (commission_pct / 100) if use_commission else 0
                    
                    remaining_pnl = remaining_size * (remaining_pnl_pct_leveraged / 100) - exit_commission
                    position['commission_paid'] = position.get('commission_paid', 0) + exit_commission
                    position['realized_pnl'] += remaining_pnl
                
                total_pnl = position['realized_pnl']
                total_pnl_pct = (total_pnl / position['entry_capital']) * 100
                total_commission = position.get('commission_paid', 0)
                total_commission_paid += total_commission
                
                capital += total_pnl
                
                if all_tp_closed:
                    exit_reason = f"TP{len(position['tp_closed'])}"
                elif sl_hit:
                    exit_reason = "SL"
                else:
                    exit_reason = "Reverse"
                
                tp_stats["total_trades"] += 1
                monthly_stats[month_key]["trades"] += 1
                monthly_stats[month_key]["pnl"] += total_pnl_pct
                monthly_stats[month_key]["pnl_amount"] += total_pnl
                
                if total_pnl > 0:
                    monthly_stats[month_key]["wins"] += 1
                else:
                    monthly_stats[month_key]["losses"] += 1
                
                if position['type'] == 'long':
                    monthly_stats[month_key]["long_trades"] += 1
                else:
                    monthly_stats[month_key]["short_trades"] += 1
                
                trade = {
                    "id": len(trades) + 1,
                    "type": position['type'],
                    "entry_time": position['entry_time'].isoformat(),
                    "entry_price": position['entry_price'],
                    "exit_time": timestamp.isoformat(),
                    "exit_price": exit_price if not all_tp_closed else position['tp_prices'][position['tp_closed'][-1]],
                    "pnl": round(total_pnl_pct, 2),
                    "pnl_amount": round(total_pnl, 2),
                    "exit_reason": exit_reason,
                    "tp_hit": position['tp_hit'],
                    "tp_levels": position['tp_prices'],
                    "sl_level": position['sl_price'],
                    "is_reentry": position.get('is_reentry', False),
                    "partial_closes": len(position['tp_closed']),
                    "params_used": {"i1": position.get('i1_used'), "i2": position.get('i2_used')},
                    "leverage": leverage,
                    "commission": round(total_commission, 4) if use_commission else 0
                }
                trades.append(trade)
                
                last_exit_reason = exit_reason
                last_exit_trend = current_trend
                position = None
        
        # Check entry
        if position is None:
            should_enter = False
            entry_type = None
            is_reentry = False
            
            if row['signal'] != 0:
                should_enter = True
                entry_type = "long" if row['signal'] == 1 else "short"
            
            elif settings.allow_reentry and last_exit_reason and last_exit_trend:
                can_reentry = False
                
                if last_exit_reason == "SL" and settings.reentry_after_sl:
                    if last_exit_trend == current_trend and current_trend != 0:
                        can_reentry = True
                
                if last_exit_reason and last_exit_reason.startswith("TP") and settings.reentry_after_tp:
                    if last_exit_trend == current_trend and current_trend != 0:
                        can_reentry = True
                
                if can_reentry:
                    should_enter = True
                    entry_type = "long" if current_trend == 1 else "short"
                    is_reentry = True
                    last_exit_reason = None
            
            if should_enter and entry_type:
                entry_price = row['close']
                entry_capital = capital
                
                # Deduct entry commission from capital
                entry_commission = entry_capital * (commission_pct / 100) if use_commission else 0
                
                position = {
                    "type": entry_type,
                    "entry_time": timestamp,
                    "entry_price": entry_price,
                    "entry_capital": entry_capital,
                    "remaining_pct": 100.0,
                    "realized_pnl": -entry_commission,  # Start with negative (commission)
                    "commission_paid": entry_commission,
                    "tp_closed": [],
                    "tp_hit": [],
                    "highest_price": entry_price,
                    "lowest_price": entry_price,
                    "is_reentry": is_reentry,
                    "tp_levels_active": active_tp_levels.copy(),
                    "i1_used": active_i1,
                    "i2_used": active_i2
                }
                
                # Calculate TP/SL prices using ACTIVE parameters
                if position['type'] == 'long':
                    position['tp_prices'] = [entry_price * (1 + tp/100) for tp in active_tp_levels]
                    position['sl_price'] = entry_price * (1 - active_sl/100)
                else:
                    position['tp_prices'] = [entry_price * (1 - tp/100) for tp in active_tp_levels]
                    position['sl_price'] = entry_price * (1 + active_sl/100)
        
        equity_curve.append({
            "time": timestamp.isoformat(),
            "value": round(capital, 2)
        })
    
    return trades, equity_curve, tp_stats, monthly_stats, param_changes


def optimize_on_lookback(df: pd.DataFrame, settings: IndicatorSettings, mode: str,
                         current_i1: int, current_i2: float, 
                         current_tp: list, current_sl: float) -> dict:
    """Quick optimization on lookback period to find better parameters"""
    
    best_score = float('-inf')
    best_params = {}
    
    if mode in ["indicator", "all"]:
        # Test different i1/i2 combinations
        i1_range = [30, 40, 45, 50, 60, 80]
        i2_range = [2, 3, 4, 5, 6]
        
        for i1 in i1_range:
            for i2 in i2_range:
                try:
                    test_df = df.copy()
                    test_df = calculate_trg(test_df, i1, i2)
                    if settings.use_supertrend:
                        test_df = calculate_supertrend(test_df, settings.supertrend_period, settings.supertrend_multiplier)
                    test_df = generate_signals(test_df, settings)
                    
                    # Quick backtest
                    trades = quick_backtest(test_df, settings)
                    
                    if len(trades) >= 3:
                        pnl = sum([t['pnl'] for t in trades])
                        wins = len([t for t in trades if t['pnl'] > 0])
                        wr = wins / len(trades)
                        score = pnl * (0.5 + wr * 0.5)  # Balance profit and win rate
                        
                        if score > best_score:
                            best_score = score
                            best_params['i1'] = i1
                            best_params['i2'] = i2
                except:
                    continue
    
    if mode in ["tp", "all"]:
        # Test different TP configurations
        tp_configs = [
            [0.8, 1.5, 2.5, 4.0],
            [1.0, 2.0, 3.5, 5.0],
            [1.5, 3.0, 5.0, 8.0],
            [1.0, 1.5, 2.5, 4.0],
        ]
        
        best_tp_score = float('-inf')
        for tp_cfg in tp_configs:
            try:
                test_df = df.copy()
                if 'trg_trend' not in test_df.columns:
                    test_df = calculate_trg(test_df, current_i1, current_i2)
                    test_df = generate_signals(test_df, settings)
                
                trades = quick_backtest(test_df, settings, tp_levels=tp_cfg)
                
                if len(trades) >= 3:
                    pnl = sum([t['pnl'] for t in trades])
                    if pnl > best_tp_score:
                        best_tp_score = pnl
                        best_params['tp_levels'] = tp_cfg
            except:
                continue
    
    if mode == "all":
        # Test different SL
        sl_range = [3, 4, 5, 6, 8]
        best_sl_score = float('-inf')
        for sl in sl_range:
            try:
                test_df = df.copy()
                if 'trg_trend' not in test_df.columns:
                    test_df = calculate_trg(test_df, current_i1, current_i2)
                    test_df = generate_signals(test_df, settings)
                
                trades = quick_backtest(test_df, settings, sl_pct=sl)
                
                if len(trades) >= 3:
                    pnl = sum([t['pnl'] for t in trades])
                    if pnl > best_sl_score:
                        best_sl_score = pnl
                        best_params['sl'] = sl
            except:
                continue
    
    return best_params if best_params else None


def quick_backtest(df: pd.DataFrame, settings: IndicatorSettings, 
                   tp_levels: list = None, sl_pct: float = None) -> list:
    """Simplified fast backtest for optimization"""
    
    if tp_levels is None:
        tp_levels = [settings.tp1_percent, settings.tp2_percent, 
                     settings.tp3_percent, settings.tp4_percent][:settings.tp_count]
    if sl_pct is None:
        sl_pct = settings.sl_percent
    
    trades = []
    position = None
    
    for i in range(len(df)):
        row = df.iloc[i]
        
        if position:
            high, low, close = row['high'], row['low'], row['close']
            
            # Check TP1 hit (simplified - just check first TP)
            tp1_price = position['tp_price']
            sl_price = position['sl_price']
            
            exit_price = None
            if position['type'] == 'long':
                if high >= tp1_price:
                    exit_price = tp1_price
                    pnl = tp_levels[0]
                elif low <= sl_price:
                    exit_price = sl_price
                    pnl = -sl_pct
            else:
                if low <= tp1_price:
                    exit_price = tp1_price
                    pnl = tp_levels[0]
                elif high >= sl_price:
                    exit_price = sl_price
                    pnl = -sl_pct
            
            if exit_price:
                trades.append({"pnl": pnl})
                position = None
        
        if position is None and row.get('signal', 0) != 0:
            entry_price = row['close']
            position = {
                "type": "long" if row['signal'] == 1 else "short",
                "entry_price": entry_price,
            }
            
            if position['type'] == 'long':
                position['tp_price'] = entry_price * (1 + tp_levels[0]/100)
                position['sl_price'] = entry_price * (1 - sl_pct/100)
            else:
                position['tp_price'] = entry_price * (1 - tp_levels[0]/100)
                position['sl_price'] = entry_price * (1 + sl_pct/100)
    
    return trades


def check_exit(position, row, settings, tp_levels, tp_amounts):
    """Check for exit conditions"""
    
    high = row['high']
    low = row['low']
    close = row['close']
    
    exit_price = None
    exit_reason = None
    tp_hit = list(position.get('tp_hit', []))
    
    # Update highest/lowest
    if position['type'] == 'long':
        position['highest_price'] = max(position['highest_price'], high)
    else:
        position['lowest_price'] = min(position['lowest_price'], low)
    
    # Check TPs
    for i, (tp_price, tp_amount) in enumerate(zip(position['tp_prices'], tp_amounts)):
        if i + 1 in tp_hit:
            continue
        
        hit = False
        if position['type'] == 'long' and high >= tp_price:
            hit = True
        elif position['type'] == 'short' and low <= tp_price:
            hit = True
        
        if hit:
            tp_hit.append(i + 1)
            position['tp_hit'] = tp_hit
            position['remaining_amount'] -= tp_amount
            
            # Update trailing SL
            if settings.sl_trailing_mode == 'breakeven' and len(tp_hit) >= 1:
                position['sl_price'] = position['entry_price']
            elif settings.sl_trailing_mode == 'moving' and len(tp_hit) >= 1:
                if position['type'] == 'long':
                    position['sl_price'] = position['tp_prices'][len(tp_hit) - 1] if len(tp_hit) > 0 else position['entry_price']
                else:
                    position['sl_price'] = position['tp_prices'][len(tp_hit) - 1] if len(tp_hit) > 0 else position['entry_price']
            
            # Full exit if all TPs hit
            if position['remaining_amount'] <= 0 or len(tp_hit) >= len(tp_levels):
                exit_price = tp_price
                exit_reason = f"TP{len(tp_hit)}"
                return exit_price, exit_reason, tp_hit
    
    # Check SL
    sl_price = position['sl_price']
    if position['type'] == 'long' and low <= sl_price:
        exit_price = sl_price
        exit_reason = "SL"
    elif position['type'] == 'short' and high >= sl_price:
        exit_price = sl_price
        exit_reason = "SL"
    
    # Check reverse signal
    if row['signal'] != 0:
        if (position['type'] == 'long' and row['signal'] == -1) or \
           (position['type'] == 'short' and row['signal'] == 1):
            exit_price = close
            exit_reason = "Reverse"
    
    return exit_price, exit_reason, tp_hit


def calculate_statistics(trades: List[Dict], equity_curve: List[Dict], settings: IndicatorSettings, monthly_stats: Dict) -> Dict:
    """Calculate comprehensive statistics including monthly breakdown"""
    
    if not trades:
        return {}
    
    pnls = [t['pnl'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    
    long_trades = [t for t in trades if t['type'] == 'long']
    short_trades = [t for t in trades if t['type'] == 'short']
    reentry_trades = [t for t in trades if t.get('is_reentry', False)]
    
    long_wins = len([t for t in long_trades if t['pnl'] > 0])
    short_wins = len([t for t in short_trades if t['pnl'] > 0])
    reentry_wins = len([t for t in reentry_trades if t['pnl'] > 0])
    
    # TP accuracy breakdown
    accuracy = {}
    for n in [5, 10, 20, 50, 100]:
        recent = trades[-n:] if len(trades) >= n else trades
        accuracy[f"last_{n}"] = {}
        for tp_num in range(1, settings.tp_count + 1):
            hits = len([t for t in recent if tp_num in t.get('tp_hit', [])])
            accuracy[f"last_{n}"][f"tp{tp_num}"] = round(hits / len(recent) * 100, 1) if recent else 0
    
    # Overall accuracy
    accuracy["total"] = {}
    for tp_num in range(1, settings.tp_count + 1):
        hits = len([t for t in trades if tp_num in t.get('tp_hit', [])])
        accuracy["total"][f"tp{tp_num}"] = round(hits / len(trades) * 100, 2) if trades else 0
    
    # Profit panel per TP
    # For each TP level:
    # - Winning = trades that reached this TP
    # - Profit = sum of profits from trades that hit this TP (proportional to TP amount)
    # - Loss = sum of losses from trades that did NOT reach this TP
    profit_panel = {}
    
    # Get TP amounts for proper profit calculation
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
        # Trades that reached this TP
        tp_hit_trades = [t for t in trades if tp_num in t.get('tp_hit', [])]
        # Trades that did NOT reach this TP (stopped out before)
        tp_missed_trades = [t for t in trades if tp_num not in t.get('tp_hit', [])]
        
        # Calculate profit: TP% * amount% for each winning trade
        tp_profit = 0
        for t in tp_hit_trades:
            # Profit from this specific TP level
            tp_profit += tp_percents[tp_num - 1] * (tp_amounts_normalized[tp_num - 1] / 100)
        
        # Calculate loss: for trades that missed this TP, calculate the loss portion
        tp_loss = 0
        for t in tp_missed_trades:
            if t['pnl'] < 0:
                # Loss proportional to the amount that would have been at this TP
                tp_loss += t['pnl'] * (tp_amounts_normalized[tp_num - 1] / 100)
        
        # Also add partial losses from trades that hit some TPs but not this one
        for t in tp_missed_trades:
            if t['pnl'] > 0:
                # Trade was profitable but didn't reach this TP
                # This means lower TPs were hit but not this one
                pass  # Don't count as loss if overall profitable
        
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
    
    # Calculate Sharpe ratio (simplified - using daily returns)
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
                sharpe = round((avg_return / std_return) * (252 ** 0.5), 2)  # Annualized
    
    # Recovery factor = total profit / max drawdown
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
        
        # Skip duplicates
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
    
    # Sort by time
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
        
        # Skip duplicates
        if time_val in seen_times:
            continue
        seen_times.add(time_val)
        
        if pd.notna(row.get('trg_upper')):
            indicators["trg_upper"].append({"time": time_val, "value": float(row['trg_upper'])})
        if pd.notna(row.get('trg_lower')):
            indicators["trg_lower"].append({"time": time_val, "value": float(row['trg_lower'])})
        if pd.notna(row.get('trg_line')):
            indicators["trg_line"].append({"time": time_val, "value": float(row['trg_line'])})
    
    # Sort all
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
        
        # Entry marker
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
        
        # Exit marker
        markers.append({
            "time": exit_time,
            "position": "aboveBar" if trade['type'] == 'long' else "belowBar",
            "color": "#22c55e" if trade['pnl'] > 0 else "#ef4444",
            "shape": "circle",
            "text": f"{trade['pnl']:+.1f}%"
        })
    
    # Sort markers by time
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
