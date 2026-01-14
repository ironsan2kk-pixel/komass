"""
Indicator Routes
================
FastAPI route handlers for indicator calculations.
"""
import pandas as pd
from fastapi import HTTPException
from typing import Dict, Any

from . import router
from .models import IndicatorSettings, ReplayRequest
from .cache import calculation_cache
from .data import (
    DATA_DIR,
    download_single_symbol,
    load_data,
    prepare_candles,
    prepare_indicators,
    prepare_trade_markers,
    get_current_signal,
    get_data_range
)
from .backtest import run_backtest, calculate_statistics, build_monthly_stats

# Import Dominant indicator module
try:
    from app.indicators import dominant as dominant_indicator
    DOMINANT_AVAILABLE = True
except ImportError:
    DOMINANT_AVAILABLE = False


@router.post("/calculate")
async def calculate_indicator(settings: IndicatorSettings) -> Dict[str, Any]:
    """Calculate full indicator with all trades and statistics"""

    # Check cache first (unless force_recalculate)
    settings_dict = settings.model_dump()
    if not settings.force_recalculate:
        cached_result = calculation_cache.get(settings_dict)
        if cached_result:
            cached_result["cached"] = True
            return cached_result

    # Load data
    filepath = DATA_DIR / f"{settings.symbol}_{settings.timeframe}.parquet"
    if not filepath.exists():
        try:
            await download_single_symbol(settings.symbol, settings.timeframe)
            if not filepath.exists():
                raise HTTPException(404, f"Data not found for {settings.symbol} {settings.timeframe}")
        except Exception as e:
            raise HTTPException(404, f"Data not found: {str(e)}")

    df = pd.read_parquet(filepath)
    df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()

    # Get data range info
    data_range = get_data_range(df)

    # Filter by date
    if settings.start_date:
        df = df[df.index >= settings.start_date]
    if settings.end_date:
        df = df[df.index <= settings.end_date]

    data_range["used_start"] = df.index.min().strftime("%Y-%m-%d") if len(df) > 0 else None
    data_range["used_end"] = df.index.max().strftime("%Y-%m-%d") if len(df) > 0 else None
    data_range["used_candles"] = len(df)

    if len(df) < 100:
        raise HTTPException(400, "Not enough data (need at least 100 candles)")

    # Branch by indicator type
    if settings.indicator_type == "dominant" and DOMINANT_AVAILABLE:
        return await _calculate_dominant(df, settings, data_range)
    else:
        return await _calculate_trg(df, settings, data_range)


async def _calculate_trg(df: pd.DataFrame, settings: IndicatorSettings, data_range: dict) -> dict:
    """Calculate TRG indicator with backtest"""

    # Run backtest
    trades, equity_curve, tp_stats, monthly_stats, param_changes = run_backtest(df, settings)

    # Calculate statistics
    stats = calculate_statistics(
        trades,
        settings.initial_capital,
        settings.leverage,
        settings.use_commission,
        settings.commission_percent
    )

    # Prepare chart data
    candles = prepare_candles(df)
    indicators = prepare_indicators(df, settings)
    trade_markers = prepare_trade_markers(trades)
    current_signal = get_current_signal(df)

    result = {
        "candles": candles,
        "indicators": indicators,
        "trades": trades,
        "trade_markers": trade_markers,
        "statistics": stats,
        "tp_stats": tp_stats,
        "monthly_stats": monthly_stats,
        "equity_curve": equity_curve,
        "data_range": data_range,
        "current_signal": current_signal,
        "param_changes": param_changes,
        "cached": False
    }

    # Store in cache
    calculation_cache.set(settings.model_dump(), result)

    return result


async def _calculate_dominant(df: pd.DataFrame, settings: IndicatorSettings, data_range: dict) -> dict:
    """Calculate Dominant indicator with backtest"""

    tp_percents = [
        settings.dominant_tp1_percent,
        settings.dominant_tp2_percent,
        settings.dominant_tp3_percent,
        settings.dominant_tp4_percent,
    ]

    # Run Dominant full backtest
    dominant_result = dominant_indicator.run_full_backtest(
        df=df.copy(),
        sensitivity=settings.dominant_sensitivity,
        filter_type=settings.dominant_filter_type,
        sl_mode=settings.dominant_sl_mode,
        sl_percent=settings.dominant_sl_percent,
        tp_percents=tp_percents,
        use_filtered_signals=True,
        fixed_stop=settings.dominant_fixed_stop
    )

    trades = dominant_result.get('trades', [])
    metrics = dominant_result.get('metrics', {})

    # Build equity curve
    equity_curve = []
    current_equity = settings.initial_capital
    equity_curve.append({
        'time': int(df.index[0].timestamp()),
        'value': current_equity
    })

    for trade in trades:
        pnl_pct = trade.get('pnl_pct', 0)
        current_equity *= (1 + pnl_pct / 100)
        equity_curve.append({
            'time': trade.get('close_time', 0),
            'value': round(current_equity, 2)
        })

    # Prepare chart data
    candles = prepare_candles(df)

    # Calculate Dominant indicator for chart
    df_calc = dominant_indicator.calculate_dominant(df.copy(), settings.dominant_sensitivity)

    indicators = {
        "high_channel": df_calc['high_channel'].tolist() if 'high_channel' in df_calc.columns else [],
        "low_channel": df_calc['low_channel'].tolist() if 'low_channel' in df_calc.columns else [],
        "mid_channel": df_calc['mid_channel'].tolist() if 'mid_channel' in df_calc.columns else [],
    }

    # Prepare trade markers
    trade_markers = []
    for trade in trades:
        trade_markers.append({
            "time": trade.get('open_time', 0),
            "type": "entry",
            "direction": trade.get('direction', 'long'),
            "price": trade.get('entry_price', 0)
        })
        trade_markers.append({
            "time": trade.get('close_time', 0),
            "type": "exit",
            "direction": trade.get('direction', 'long'),
            "price": trade.get('exit_price', 0),
            "pnl": trade.get('pnl_pct', 0)
        })

    # Build statistics from metrics
    stats = {
        "total_trades": metrics.get('total_trades', 0),
        "winning_trades": metrics.get('winning_trades', 0),
        "losing_trades": metrics.get('losing_trades', 0),
        "win_rate": metrics.get('win_rate', 0),
        "total_pnl_pct": metrics.get('total_pnl', 0),
        "avg_pnl_pct": metrics.get('avg_pnl', 0),
        "max_drawdown_pct": metrics.get('max_drawdown', 0),
        "profit_factor": metrics.get('profit_factor', 0),
        "final_capital": current_equity,
    }

    result = {
        "candles": candles,
        "indicators": indicators,
        "trades": trades,
        "trade_markers": trade_markers,
        "statistics": stats,
        "monthly_stats": build_monthly_stats(trades),
        "equity_curve": equity_curve,
        "data_range": data_range,
        "indicator_type": "dominant",
        "cached": False
    }

    calculation_cache.set(settings.model_dump(), result)

    return result


@router.get("/candles/{symbol}/{timeframe}")
async def get_candles(symbol: str, timeframe: str, limit: int = 500) -> Dict[str, Any]:
    """Get raw candles data"""
    filepath = DATA_DIR / f"{symbol}_{timeframe}.parquet"
    if not filepath.exists():
        raise HTTPException(404, f"Data not found for {symbol} {timeframe}")

    df = pd.read_parquet(filepath)
    df = df.tail(limit)

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "candles": prepare_candles(df),
        "count": len(df)
    }


@router.post("/replay")
async def replay_trades(request: ReplayRequest) -> Dict[str, Any]:
    """Replay trades step by step for animation"""
    settings = IndicatorSettings(
        symbol=request.symbol,
        timeframe=request.timeframe,
        start_date=request.start_date,
        end_date=request.end_date,
        force_recalculate=True
    )

    # Get full result
    result = await calculate_indicator(settings)

    # Limit by step
    if request.step > 0:
        result["candles"] = result["candles"][:request.step]
        result["trades"] = [t for t in result["trades"] if t.get("entry_bar", 0) < request.step]

    return result


@router.get("/cache-stats")
async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return calculation_cache.stats()


@router.post("/cache-clear")
async def clear_cache() -> Dict[str, str]:
    """Clear calculation cache"""
    calculation_cache.clear()
    return {"status": "ok", "message": "Cache cleared"}
