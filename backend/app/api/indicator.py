# -*- coding: utf-8 -*-
"""
Komas Trading Server - Indicator API
====================================
Modular API for indicator calculation, backtesting, and optimization.
Uses plugin architecture for extensibility.

Endpoints:
    POST /api/indicator/calculate         - Calculate indicator with backtest
    GET  /api/indicator/candles/{s}/{tf}  - Get candles for chart
    POST /api/indicator/replay            - Replay mode (step by step)
    POST /api/indicator/heatmap           - Generate i1/i2 heatmap
    POST /api/indicator/auto-optimize-stream - SSE optimization
    GET  /api/indicator/{plugin}/ui-schema   - Get UI schema
    GET  /api/indicator/{plugin}/defaults    - Get default settings
    POST /api/indicator/{plugin}/validate    - Validate settings

Version: 1.0.0
"""
import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Generator
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing

import numpy as np
import pandas as pd
import aiohttp
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

# Configure logging
logger = logging.getLogger(__name__)

# Router
router = APIRouter(prefix="/api/indicator", tags=["Indicator"])

# Number of workers for parallel processing
NUM_WORKERS = os.cpu_count() or 4

# ============================================================================
# DATA DIRECTORY
# ============================================================================

def find_data_dir() -> Path:
    """Find data directory with parquet files"""
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
            logger.info(f"[Indicator API] Found DATA_DIR: {p.absolute()}")
            return p
    
    default = Path(__file__).parent.parent.parent / "data"
    default.mkdir(exist_ok=True)
    logger.info(f"[Indicator API] Created DATA_DIR: {default.absolute()}")
    return default

DATA_DIR = find_data_dir()


# ============================================================================
# PLUGIN IMPORTS (Lazy loading)
# ============================================================================

_TRG_LOADED = False
_TRG_CLASSES = {}

def _load_trg_plugin():
    """Lazy load TRG plugin components"""
    global _TRG_LOADED, _TRG_CLASSES
    
    if _TRG_LOADED:
        return _TRG_CLASSES
    
    try:
        # Try to import from plugins
        from app.plugins.trg import (
            TRGIndicator,
            TRGSignalGenerator,
            TRGBacktest,
            BacktestConfig,
            TRGOptimizer,
            TRGOptimizerConfig,
            get_ui_schema,
            get_defaults,
            validate_settings,
        )
        _TRG_CLASSES = {
            'indicator': TRGIndicator,
            'signals': TRGSignalGenerator,
            'backtest': TRGBacktest,
            'backtest_config': BacktestConfig,
            'optimizer': TRGOptimizer,
            'optimizer_config': TRGOptimizerConfig,
            'ui_schema': get_ui_schema,
            'defaults': get_defaults,
            'validate': validate_settings,
        }
        _TRG_LOADED = True
        logger.info("[Indicator API] TRG plugin loaded successfully")
        
    except ImportError as e:
        logger.warning(f"[Indicator API] Could not load TRG plugin: {e}")
        logger.info("[Indicator API] Using fallback implementation")
        _TRG_LOADED = True
    
    return _TRG_CLASSES


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class IndicatorSettings(BaseModel):
    """Complete indicator settings model"""
    
    # Data
    symbol: str = Field(default="BTCUSDT", description="Trading pair")
    timeframe: str = Field(default="1h", description="Timeframe")
    start_date: Optional[str] = Field(default=None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(default=None, description="End date (YYYY-MM-DD)")
    
    # TRG Indicator
    trg_atr_length: int = Field(default=45, ge=5, le=500, description="ATR length (i1)")
    trg_multiplier: float = Field(default=4.0, ge=0.5, le=20.0, description="Multiplier (i2)")
    
    # Take Profits (10 levels)
    tp_count: int = Field(default=4, ge=1, le=10, description="Number of TP levels")
    tp1_percent: float = Field(default=1.05, ge=0.1, le=100.0)
    tp2_percent: float = Field(default=1.95, ge=0.1, le=100.0)
    tp3_percent: float = Field(default=3.75, ge=0.1, le=100.0)
    tp4_percent: float = Field(default=6.0, ge=0.1, le=100.0)
    tp5_percent: float = Field(default=8.0, ge=0.1, le=100.0)
    tp6_percent: float = Field(default=10.0, ge=0.1, le=100.0)
    tp7_percent: float = Field(default=12.0, ge=0.1, le=100.0)
    tp8_percent: float = Field(default=15.0, ge=0.1, le=100.0)
    tp9_percent: float = Field(default=18.0, ge=0.1, le=100.0)
    tp10_percent: float = Field(default=20.0, ge=0.1, le=100.0)
    
    tp1_amount: float = Field(default=50.0, ge=0, le=100.0)
    tp2_amount: float = Field(default=30.0, ge=0, le=100.0)
    tp3_amount: float = Field(default=15.0, ge=0, le=100.0)
    tp4_amount: float = Field(default=5.0, ge=0, le=100.0)
    tp5_amount: float = Field(default=0.0, ge=0, le=100.0)
    tp6_amount: float = Field(default=0.0, ge=0, le=100.0)
    tp7_amount: float = Field(default=0.0, ge=0, le=100.0)
    tp8_amount: float = Field(default=0.0, ge=0, le=100.0)
    tp9_amount: float = Field(default=0.0, ge=0, le=100.0)
    tp10_amount: float = Field(default=0.0, ge=0, le=100.0)
    
    # Stop Loss
    sl_percent: float = Field(default=6.0, ge=0.1, le=100.0, description="Stop loss %")
    sl_trailing_mode: str = Field(default="breakeven", description="Trailing: fixed/breakeven/cascade")
    
    # Position
    leverage: float = Field(default=1.0, ge=1, le=125, description="Leverage multiplier")
    use_commission: bool = Field(default=False, description="Enable commission")
    commission_percent: float = Field(default=0.1, ge=0, le=1.0, description="Commission %")
    initial_capital: float = Field(default=10000.0, ge=100, description="Initial capital")
    
    # Filters
    use_supertrend: bool = Field(default=False)
    supertrend_period: int = Field(default=10, ge=1, le=100)
    supertrend_multiplier: float = Field(default=3.0, ge=0.5, le=10.0)
    
    use_rsi_filter: bool = Field(default=False)
    rsi_period: int = Field(default=14, ge=2, le=100)
    rsi_overbought: int = Field(default=70, ge=50, le=100)
    rsi_oversold: int = Field(default=30, ge=0, le=50)
    
    use_adx_filter: bool = Field(default=False)
    adx_period: int = Field(default=14, ge=2, le=100)
    adx_threshold: int = Field(default=25, ge=10, le=100)
    
    use_volume_filter: bool = Field(default=False)
    volume_ma_period: int = Field(default=20, ge=5, le=100)
    volume_threshold: float = Field(default=1.5, ge=1.0, le=5.0)
    
    # Re-entry
    allow_reentry: bool = Field(default=True)
    reentry_after_sl: bool = Field(default=True)
    reentry_after_tp: bool = Field(default=False)
    
    # Adaptive
    adaptive_mode: Optional[str] = Field(default=None, description="None/indicator/tp/all")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTCUSDT",
                "timeframe": "1h",
                "trg_atr_length": 45,
                "trg_multiplier": 4.0,
                "tp_count": 4,
                "sl_percent": 6.0,
                "sl_trailing_mode": "breakeven",
            }
        }


class ReplayRequest(BaseModel):
    """Request for replay mode"""
    settings: IndicatorSettings
    step: int = Field(default=0, ge=0, description="Step number (0 = all)")


class HeatmapRequest(BaseModel):
    """Request for heatmap generation"""
    settings: IndicatorSettings
    i1_min: int = Field(default=20, ge=5, le=200)
    i1_max: int = Field(default=80, ge=5, le=200)
    i1_step: int = Field(default=5, ge=1, le=50)
    i2_min: float = Field(default=2.0, ge=0.5, le=15.0)
    i2_max: float = Field(default=8.0, ge=0.5, le=15.0)
    i2_step: float = Field(default=0.5, ge=0.1, le=5.0)
    metric: str = Field(default="profit", description="Metric: profit/winrate/sharpe/combined")


class AutoOptimizeRequest(BaseModel):
    """Request for auto-optimization"""
    settings: IndicatorSettings
    mode: str = Field(default="indicator", description="Mode: indicator/tp/sl/filters/full")
    metric: str = Field(default="combined", description="Score metric")
    tp_range_percent: float = Field(default=50.0, ge=10, le=200, description="TP range %")
    tp_step_percent: float = Field(default=10.0, ge=5, le=50, description="TP step %")
    full_mode_depth: str = Field(default="medium", description="Full mode depth: light/medium/deep")


# ============================================================================
# INDICATOR CALCULATION FUNCTIONS (Fallback)
# ============================================================================

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.ewm(span=period, adjust=False).mean()
    
    return atr


def calculate_trg(df: pd.DataFrame, atr_length: int = 45, multiplier: float = 4.0) -> pd.DataFrame:
    """Calculate TRG indicator"""
    df = df.copy()
    
    # ATR
    df['trg_atr'] = calculate_atr(df, atr_length)
    
    # TRG bands
    hl2 = (df['high'] + df['low']) / 2
    df['trg_upper'] = hl2 + (multiplier * df['trg_atr'])
    df['trg_lower'] = hl2 - (multiplier * df['trg_atr'])
    
    # Initialize trend
    df['trg_trend'] = 0
    df['trg_line'] = np.nan
    
    # Calculate trend
    close = df['close'].values
    upper = df['trg_upper'].values
    lower = df['trg_lower'].values
    trend = np.zeros(len(df))
    line = np.zeros(len(df))
    
    for i in range(1, len(df)):
        if close[i] > upper[i-1]:
            trend[i] = 1
        elif close[i] < lower[i-1]:
            trend[i] = -1
        else:
            trend[i] = trend[i-1]
        
        if trend[i] == 1:
            line[i] = lower[i]
        else:
            line[i] = upper[i]
    
    df['trg_trend'] = trend
    df['trg_line'] = line
    
    return df


def calculate_supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """Calculate SuperTrend indicator"""
    df = df.copy()
    
    atr = calculate_atr(df, period)
    hl2 = (df['high'] + df['low']) / 2
    
    df['st_upper'] = hl2 + (multiplier * atr)
    df['st_lower'] = hl2 - (multiplier * atr)
    df['st_trend'] = 0
    
    close = df['close'].values
    st_upper = df['st_upper'].values.copy()
    st_lower = df['st_lower'].values.copy()
    st_trend = np.zeros(len(df))
    
    for i in range(1, len(df)):
        # Update bands
        if close[i-1] > st_upper[i-1]:
            st_lower[i] = max(st_lower[i], st_lower[i-1])
        if close[i-1] < st_lower[i-1]:
            st_upper[i] = min(st_upper[i], st_upper[i-1])
        
        # Determine trend
        if close[i] > st_upper[i-1]:
            st_trend[i] = 1
        elif close[i] < st_lower[i-1]:
            st_trend[i] = -1
        else:
            st_trend[i] = st_trend[i-1]
    
    df['st_upper'] = st_upper
    df['st_lower'] = st_lower
    df['st_trend'] = st_trend
    df['supertrend'] = np.where(st_trend == 1, st_lower, st_upper)
    
    return df


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculate RSI indicator"""
    df = df.copy()
    
    delta = df['close'].diff()
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    df['rsi'] = 100 - (100 / (1 + rs))
    
    return df


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Calculate ADX indicator"""
    df = df.copy()
    
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
    
    # Smoothed
    atr = tr.ewm(span=period, adjust=False).mean()
    plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr)
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr)
    
    # ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    df['adx'] = dx.ewm(span=period, adjust=False).mean()
    df['plus_di'] = plus_di
    df['minus_di'] = minus_di
    
    return df


def generate_signals(df: pd.DataFrame, settings: IndicatorSettings) -> pd.DataFrame:
    """Generate trading signals based on TRG and filters"""
    df = df.copy()
    df['signal'] = 0
    
    trend = df['trg_trend'].values
    
    for i in range(1, len(df)):
        signal = 0
        
        # TRG signal on trend change
        if trend[i] == 1 and trend[i-1] != 1:
            signal = 1  # Long
        elif trend[i] == -1 and trend[i-1] != -1:
            signal = -1  # Short
        
        # Apply filters
        if signal != 0:
            # SuperTrend filter
            if settings.use_supertrend and 'st_trend' in df.columns:
                if signal == 1 and df['st_trend'].iloc[i] != 1:
                    signal = 0
                elif signal == -1 and df['st_trend'].iloc[i] != -1:
                    signal = 0
            
            # RSI filter
            if settings.use_rsi_filter and 'rsi' in df.columns:
                rsi = df['rsi'].iloc[i]
                if signal == 1 and rsi > settings.rsi_overbought:
                    signal = 0
                elif signal == -1 and rsi < settings.rsi_oversold:
                    signal = 0
            
            # ADX filter
            if settings.use_adx_filter and 'adx' in df.columns:
                if df['adx'].iloc[i] < settings.adx_threshold:
                    signal = 0
            
            # Volume filter
            if settings.use_volume_filter:
                vol_ma = df['volume'].rolling(settings.volume_ma_period).mean()
                if df['volume'].iloc[i] < vol_ma.iloc[i] * settings.volume_threshold:
                    signal = 0
        
        df.iloc[i, df.columns.get_loc('signal')] = signal
    
    return df


# ============================================================================
# BACKTEST ENGINE (Fallback)
# ============================================================================

def run_backtest(
    df: pd.DataFrame,
    settings: IndicatorSettings,
    adaptive_mode: Optional[str] = None
) -> tuple:
    """Run full backtest with TP/SL tracking"""
    
    trades = []
    equity_curve = []
    tp_stats = {f'tp{i}': {'hit': 0, 'total': 0} for i in range(1, 11)}
    monthly_stats = {}
    param_changes = []
    
    # Initial state
    capital = settings.initial_capital
    position = None
    position_size = 0
    remaining_amount = 100.0
    
    # Get TP levels
    tp_levels = []
    for i in range(1, settings.tp_count + 1):
        pct = getattr(settings, f'tp{i}_percent')
        amt = getattr(settings, f'tp{i}_amount')
        if amt > 0:
            tp_levels.append({'level': i, 'percent': pct, 'amount': amt})
    
    # Iterate through candles
    for i in range(len(df)):
        row = df.iloc[i]
        timestamp = df.index[i]
        close = row['close']
        high = row['high']
        low = row['low']
        signal = row.get('signal', 0)
        
        # Track equity
        equity_value = capital
        if position:
            if position['direction'] == 'long':
                pnl = (close - position['entry_price']) / position['entry_price'] * remaining_amount
            else:
                pnl = (position['entry_price'] - close) / position['entry_price'] * remaining_amount
            equity_value = capital + (position['size'] * pnl / 100)
        
        equity_curve.append({
            'time': int(timestamp.timestamp()),
            'value': round(equity_value, 2)
        })
        
        # Check TP/SL if in position
        if position:
            direction = position['direction']
            entry_price = position['entry_price']
            
            # Check TPs
            for tp in tp_levels:
                if tp['level'] <= position.get('hit_tps', 0):
                    continue
                
                tp_price = entry_price * (1 + tp['percent'] / 100) if direction == 'long' else entry_price * (1 - tp['percent'] / 100)
                
                hit = (high >= tp_price) if direction == 'long' else (low <= tp_price)
                
                if hit:
                    # Partial close
                    close_amount = min(tp['amount'], remaining_amount)
                    if direction == 'long':
                        pnl_pct = tp['percent']
                    else:
                        pnl_pct = tp['percent']
                    
                    realized_pnl = position['size'] * (close_amount / 100) * (pnl_pct / 100) * settings.leverage
                    
                    if settings.use_commission:
                        realized_pnl -= position['size'] * (close_amount / 100) * settings.commission_percent / 100
                    
                    capital += realized_pnl
                    remaining_amount -= close_amount
                    
                    position['hit_tps'] = tp['level']
                    tp_stats[f"tp{tp['level']}"]['hit'] += 1
                    
                    # Move SL to breakeven after TP1
                    if tp['level'] == 1 and settings.sl_trailing_mode == 'breakeven':
                        position['sl_price'] = entry_price
            
            # Check SL
            sl_price = position.get('sl_price', entry_price * (1 - settings.sl_percent / 100) if direction == 'long' else entry_price * (1 + settings.sl_percent / 100))
            
            hit_sl = (low <= sl_price) if direction == 'long' else (high >= sl_price)
            
            if hit_sl and remaining_amount > 0:
                # Close remaining position
                if direction == 'long':
                    pnl_pct = (sl_price - entry_price) / entry_price * 100
                else:
                    pnl_pct = (entry_price - sl_price) / entry_price * 100
                
                realized_pnl = position['size'] * (remaining_amount / 100) * (pnl_pct / 100) * settings.leverage
                
                if settings.use_commission:
                    realized_pnl -= position['size'] * (remaining_amount / 100) * settings.commission_percent / 100
                
                capital += realized_pnl
                
                # Record trade
                trade = {
                    'id': len(trades) + 1,
                    'entry_time': position['entry_time'],
                    'exit_time': int(timestamp.timestamp()),
                    'direction': direction,
                    'entry_price': entry_price,
                    'exit_price': sl_price,
                    'size': position['size'],
                    'pnl': realized_pnl,
                    'pnl_pct': pnl_pct * settings.leverage,
                    'exit_reason': 'sl',
                    'tps_hit': position.get('hit_tps', 0),
                    'result': 'loss' if realized_pnl < 0 else 'win'
                }
                trades.append(trade)
                
                # Update monthly stats
                month_key = timestamp.strftime('%Y-%m')
                if month_key not in monthly_stats:
                    monthly_stats[month_key] = {'pnl': 0, 'trades': 0, 'wins': 0}
                monthly_stats[month_key]['pnl'] += realized_pnl
                monthly_stats[month_key]['trades'] += 1
                if realized_pnl > 0:
                    monthly_stats[month_key]['wins'] += 1
                
                position = None
                remaining_amount = 100.0
            
            # Close on opposite signal or full TP hit
            if remaining_amount <= 0 or (signal != 0 and signal != (1 if direction == 'long' else -1)):
                if remaining_amount > 0:
                    # Close remaining
                    if direction == 'long':
                        pnl_pct = (close - entry_price) / entry_price * 100
                    else:
                        pnl_pct = (entry_price - close) / entry_price * 100
                    
                    realized_pnl = position['size'] * (remaining_amount / 100) * (pnl_pct / 100) * settings.leverage
                    capital += realized_pnl
                    
                    trade = {
                        'id': len(trades) + 1,
                        'entry_time': position['entry_time'],
                        'exit_time': int(timestamp.timestamp()),
                        'direction': direction,
                        'entry_price': entry_price,
                        'exit_price': close,
                        'size': position['size'],
                        'pnl': realized_pnl,
                        'pnl_pct': pnl_pct * settings.leverage,
                        'exit_reason': 'signal' if signal != 0 else 'tp_full',
                        'tps_hit': position.get('hit_tps', 0),
                        'result': 'win' if realized_pnl > 0 else 'loss'
                    }
                    trades.append(trade)
                    
                    month_key = timestamp.strftime('%Y-%m')
                    if month_key not in monthly_stats:
                        monthly_stats[month_key] = {'pnl': 0, 'trades': 0, 'wins': 0}
                    monthly_stats[month_key]['pnl'] += realized_pnl
                    monthly_stats[month_key]['trades'] += 1
                    if realized_pnl > 0:
                        monthly_stats[month_key]['wins'] += 1
                
                position = None
                remaining_amount = 100.0
        
        # Open new position
        if signal != 0 and position is None:
            direction = 'long' if signal == 1 else 'short'
            position_size = capital  # Full position
            
            # Entry commission
            if settings.use_commission:
                capital -= position_size * settings.commission_percent / 100
            
            sl_price = close * (1 - settings.sl_percent / 100) if direction == 'long' else close * (1 + settings.sl_percent / 100)
            
            position = {
                'direction': direction,
                'entry_price': close,
                'entry_time': int(timestamp.timestamp()),
                'size': position_size,
                'sl_price': sl_price,
                'hit_tps': 0
            }
            remaining_amount = 100.0
            
            for tp in tp_levels:
                tp_stats[f"tp{tp['level']}"]['total'] += 1
    
    # Convert monthly stats to list
    monthly_list = []
    for month, stats in sorted(monthly_stats.items()):
        monthly_list.append({
            'month': month,
            'pnl': round(stats['pnl'], 2),
            'pnl_pct': round(stats['pnl'] / settings.initial_capital * 100, 2),
            'trades': stats['trades'],
            'wins': stats['wins'],
            'winrate': round(stats['wins'] / stats['trades'] * 100, 1) if stats['trades'] > 0 else 0
        })
    
    return trades, equity_curve, tp_stats, monthly_list, param_changes


def calculate_statistics(
    trades: List[dict],
    equity_curve: List[dict],
    settings: IndicatorSettings,
    monthly_stats: List[dict]
) -> dict:
    """Calculate comprehensive backtest statistics"""
    
    if not trades:
        return {
            'total_trades': 0,
            'win_rate': 0,
            'profit_factor': 0,
            'total_pnl': 0,
            'total_pnl_pct': 0,
            'max_drawdown': 0,
            'max_drawdown_pct': 0,
            'sharpe_ratio': 0,
            'avg_trade_pnl': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'best_trade': 0,
            'worst_trade': 0,
            'long_trades': 0,
            'short_trades': 0,
            'long_winrate': 0,
            'short_winrate': 0,
        }
    
    # Basic stats
    total_trades = len(trades)
    wins = [t for t in trades if t['pnl'] > 0]
    losses = [t for t in trades if t['pnl'] <= 0]
    
    win_rate = len(wins) / total_trades * 100 if total_trades > 0 else 0
    
    total_profit = sum(t['pnl'] for t in wins)
    total_loss = abs(sum(t['pnl'] for t in losses))
    profit_factor = total_profit / total_loss if total_loss > 0 else 999
    
    total_pnl = sum(t['pnl'] for t in trades)
    total_pnl_pct = total_pnl / settings.initial_capital * 100
    
    # Drawdown
    peak = settings.initial_capital
    max_dd = 0
    max_dd_pct = 0
    
    for eq in equity_curve:
        value = eq['value']
        if value > peak:
            peak = value
        dd = peak - value
        dd_pct = dd / peak * 100 if peak > 0 else 0
        if dd > max_dd:
            max_dd = dd
            max_dd_pct = dd_pct
    
    # Sharpe ratio (simplified)
    pnl_list = [t['pnl'] for t in trades]
    avg_pnl = np.mean(pnl_list) if pnl_list else 0
    std_pnl = np.std(pnl_list) if len(pnl_list) > 1 else 1
    sharpe = (avg_pnl / std_pnl * np.sqrt(252)) if std_pnl > 0 else 0
    
    # Per-direction stats
    long_trades = [t for t in trades if t['direction'] == 'long']
    short_trades = [t for t in trades if t['direction'] == 'short']
    long_wins = len([t for t in long_trades if t['pnl'] > 0])
    short_wins = len([t for t in short_trades if t['pnl'] > 0])
    
    return {
        'total_trades': total_trades,
        'win_rate': round(win_rate, 1),
        'profit_factor': round(profit_factor, 2),
        'total_pnl': round(total_pnl, 2),
        'total_pnl_pct': round(total_pnl_pct, 2),
        'max_drawdown': round(max_dd, 2),
        'max_drawdown_pct': round(max_dd_pct, 2),
        'sharpe_ratio': round(sharpe, 2),
        'avg_trade_pnl': round(avg_pnl, 2),
        'avg_win': round(np.mean([t['pnl'] for t in wins]), 2) if wins else 0,
        'avg_loss': round(np.mean([t['pnl'] for t in losses]), 2) if losses else 0,
        'best_trade': round(max(t['pnl'] for t in trades), 2) if trades else 0,
        'worst_trade': round(min(t['pnl'] for t in trades), 2) if trades else 0,
        'long_trades': len(long_trades),
        'short_trades': len(short_trades),
        'long_winrate': round(long_wins / len(long_trades) * 100, 1) if long_trades else 0,
        'short_winrate': round(short_wins / len(short_trades) * 100, 1) if short_trades else 0,
    }


# ============================================================================
# DATA HELPERS
# ============================================================================

def prepare_candles(df: pd.DataFrame) -> List[dict]:
    """Convert DataFrame to chart-ready candles"""
    candles = []
    for idx, row in df.iterrows():
        candles.append({
            'time': int(idx.timestamp()),
            'open': round(row['open'], 8),
            'high': round(row['high'], 8),
            'low': round(row['low'], 8),
            'close': round(row['close'], 8),
            'volume': round(row['volume'], 2) if 'volume' in row else 0
        })
    return candles


def prepare_indicators(df: pd.DataFrame, settings: IndicatorSettings) -> dict:
    """Prepare indicator data for chart"""
    indicators = {}
    
    if 'trg_line' in df.columns:
        trg_data = []
        for idx, row in df.iterrows():
            if not pd.isna(row['trg_line']):
                trg_data.append({
                    'time': int(idx.timestamp()),
                    'value': round(row['trg_line'], 8),
                    'trend': int(row['trg_trend'])
                })
        indicators['trg'] = trg_data
    
    if settings.use_supertrend and 'supertrend' in df.columns:
        st_data = []
        for idx, row in df.iterrows():
            if not pd.isna(row['supertrend']):
                st_data.append({
                    'time': int(idx.timestamp()),
                    'value': round(row['supertrend'], 8),
                    'trend': int(row['st_trend'])
                })
        indicators['supertrend'] = st_data
    
    if 'signal' in df.columns:
        signals = []
        for idx, row in df.iterrows():
            if row['signal'] != 0:
                signals.append({
                    'time': int(idx.timestamp()),
                    'signal': int(row['signal']),
                    'price': round(row['close'], 8)
                })
        indicators['signals'] = signals
    
    return indicators


def prepare_trade_markers(trades: List[dict]) -> List[dict]:
    """Prepare trade markers for chart"""
    markers = []
    
    for trade in trades:
        # Entry marker
        markers.append({
            'time': trade['entry_time'],
            'position': 'belowBar' if trade['direction'] == 'long' else 'aboveBar',
            'color': '#22c55e' if trade['direction'] == 'long' else '#ef4444',
            'shape': 'arrowUp' if trade['direction'] == 'long' else 'arrowDown',
            'text': f"{'L' if trade['direction'] == 'long' else 'S'} @ {trade['entry_price']:.2f}"
        })
        
        # Exit marker
        markers.append({
            'time': trade['exit_time'],
            'position': 'aboveBar' if trade['direction'] == 'long' else 'belowBar',
            'color': '#f59e0b',
            'shape': 'circle',
            'text': f"Exit @ {trade['exit_price']:.2f} ({trade['pnl_pct']:+.2f}%)"
        })
    
    return markers


def get_current_signal(df: pd.DataFrame) -> dict:
    """Get current signal state"""
    if len(df) < 2:
        return {'signal': 0, 'trend': 0}
    
    last = df.iloc[-1]
    return {
        'signal': int(last.get('signal', 0)),
        'trend': int(last.get('trg_trend', 0)),
        'price': float(last['close']),
        'trg_line': float(last.get('trg_line', 0)) if not pd.isna(last.get('trg_line')) else 0
    }


# ============================================================================
# DATA DOWNLOAD
# ============================================================================

async def download_symbol(symbol: str, timeframe: str, days: int = 365) -> bool:
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
                logger.error(f"Error downloading {symbol}: {e}")
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
    
    filepath = DATA_DIR / f"{symbol}_{timeframe}.parquet"
    df.to_parquet(filepath)
    logger.info(f"[Indicator API] Downloaded {symbol} {timeframe}: {len(df)} candles")
    
    return True


# ============================================================================
# OPTIMIZATION HELPERS
# ============================================================================

def calculate_optimization_score(
    trades: List[dict],
    equity_curve: List[dict],
    settings: IndicatorSettings,
    metric: str = "combined"
) -> tuple:
    """Calculate optimization score and metrics"""
    
    if not trades:
        return -999, {'profit_pct': 0, 'win_rate': 0, 'total_trades': 0}
    
    # Calculate metrics
    total_pnl = sum(t['pnl'] for t in trades)
    profit_pct = total_pnl / settings.initial_capital * 100
    wins = len([t for t in trades if t['pnl'] > 0])
    win_rate = wins / len(trades) * 100
    
    # Drawdown
    peak = settings.initial_capital
    max_dd_pct = 0
    for eq in equity_curve:
        if eq['value'] > peak:
            peak = eq['value']
        dd_pct = (peak - eq['value']) / peak * 100
        if dd_pct > max_dd_pct:
            max_dd_pct = dd_pct
    
    metrics = {
        'profit_pct': round(profit_pct, 2),
        'win_rate': round(win_rate, 1),
        'total_trades': len(trades),
        'max_drawdown_pct': round(max_dd_pct, 2),
    }
    
    # Score based on metric
    if metric == "profit":
        score = profit_pct
    elif metric == "winrate":
        score = win_rate
    elif metric == "sharpe":
        pnl_list = [t['pnl'] for t in trades]
        std = np.std(pnl_list) if len(pnl_list) > 1 else 1
        score = (np.mean(pnl_list) / std * np.sqrt(252)) if std > 0 else 0
    else:  # combined
        # Weighted score
        profit_score = min(profit_pct / 100, 3)  # Cap at 300%
        wr_score = win_rate / 100
        dd_penalty = max_dd_pct / 100
        trade_bonus = min(len(trades) / 100, 1)  # Bonus for more trades
        
        score = (profit_score * 0.4 + wr_score * 0.3 + trade_bonus * 0.2 - dd_penalty * 0.1) * 100
    
    return score, metrics


# Worker function for parallel processing
def _backtest_worker(params: dict) -> dict:
    """Worker function for parallel backtest"""
    try:
        df = params['df'].copy()
        settings_dict = params['settings']
        i1 = params.get('i1', settings_dict.get('trg_atr_length', 45))
        i2 = params.get('i2', settings_dict.get('trg_multiplier', 4.0))
        metric = params.get('metric', 'combined')
        
        # Recreate settings
        settings = IndicatorSettings(**settings_dict)
        settings.trg_atr_length = i1
        settings.trg_multiplier = i2
        
        # Calculate
        df = calculate_trg(df, i1, i2)
        if settings.use_supertrend:
            df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
        if settings.use_rsi_filter:
            df = calculate_rsi(df, settings.rsi_period)
        if settings.use_adx_filter:
            df = calculate_adx(df, settings.adx_period)
        
        df = generate_signals(df, settings)
        trades, equity, _, _, _ = run_backtest(df, settings)
        score, metrics = calculate_optimization_score(trades, equity, settings, metric)
        
        return {
            'i1': i1,
            'i2': i2,
            'score': round(score, 2),
            'profit': metrics['profit_pct'],
            'win_rate': metrics['win_rate'],
            'trades': metrics['total_trades'],
        }
    except Exception as e:
        return {
            'i1': params.get('i1'),
            'i2': params.get('i2'),
            'score': -999,
            'error': str(e)
        }


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/calculate")
async def calculate_indicator(settings: IndicatorSettings):
    """
    Calculate indicator with full backtest.
    
    Returns candles, indicators, trades, equity curve, and statistics.
    """
    # Load data
    filepath = DATA_DIR / f"{settings.symbol}_{settings.timeframe}.parquet"
    
    if not filepath.exists():
        # Try to download
        try:
            success = await download_symbol(settings.symbol, settings.timeframe)
            if not success or not filepath.exists():
                raise HTTPException(
                    404,
                    f"Данные не найдены для {settings.symbol} {settings.timeframe}. "
                    "Перейдите в раздел 'Данные' и скачайте историю."
                )
        except Exception as e:
            raise HTTPException(404, f"Ошибка загрузки данных: {str(e)}")
    
    df = pd.read_parquet(filepath)
    df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()
    
    # Filter by date
    if settings.start_date:
        df = df[df.index >= settings.start_date]
    if settings.end_date:
        df = df[df.index <= settings.end_date]
    
    if len(df) < 100:
        raise HTTPException(400, "Недостаточно данных (нужно минимум 100 свечей)")
    
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
    
    # Debug info
    long_signals = (df['signal'] == 1).sum()
    short_signals = (df['signal'] == -1).sum()
    logger.info(f"[Calculate] {settings.symbol} {settings.timeframe}: {len(df)} candles, {long_signals} long, {short_signals} short signals")
    
    # Run backtest
    trades, equity_curve, tp_stats, monthly_stats, param_changes = run_backtest(
        df, settings, adaptive_mode=settings.adaptive_mode
    )
    
    # Calculate statistics
    stats = calculate_statistics(trades, equity_curve, settings, monthly_stats)
    
    # Prepare response
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
        "settings": settings.model_dump()
    }


@router.get("/candles/{symbol}/{timeframe}")
async def get_candles(symbol: str, timeframe: str, limit: int = Query(default=500, ge=100, le=5000)):
    """
    Get candles for initial chart display.
    """
    filepath = DATA_DIR / f"{symbol}_{timeframe}.parquet"
    
    if not filepath.exists():
        raise HTTPException(404, f"Данные не найдены для {symbol} {timeframe}")
    
    df = pd.read_parquet(filepath)
    df = df[~df.index.duplicated(keep='first')]
    df = df.sort_index()
    df = df.tail(limit)
    
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
    """
    Get indicator state at specific step for replay mode.
    """
    settings = request.settings
    step = request.step
    
    filepath = DATA_DIR / f"{settings.symbol}_{settings.timeframe}.parquet"
    if not filepath.exists():
        raise HTTPException(404, "Данные не найдены")
    
    df = pd.read_parquet(filepath)
    
    if settings.start_date:
        df = df[df.index >= settings.start_date]
    if settings.end_date:
        df = df[df.index <= settings.end_date]
    
    total_steps = len(df)
    
    if step > 0 and step < len(df):
        df = df.iloc[:step]
    
    # Calculate
    df = calculate_trg(df, settings.trg_atr_length, settings.trg_multiplier)
    if settings.use_supertrend:
        df = calculate_supertrend(df, settings.supertrend_period, settings.supertrend_multiplier)
    
    df = generate_signals(df, settings)
    trades, equity_curve, tp_stats, _, _ = run_backtest(df, settings)
    
    return {
        "step": step if step > 0 else len(df),
        "total_steps": total_steps,
        "candles": prepare_candles(df),
        "indicators": prepare_indicators(df, settings),
        "trades": trades[-10:] if trades else [],
        "equity": equity_curve[-1]['value'] if equity_curve else settings.initial_capital,
        "current_signal": get_current_signal(df)
    }


@router.post("/heatmap")
async def generate_heatmap(request: HeatmapRequest):
    """
    Generate optimization heatmap for i1/i2 parameters.
    Uses parallel processing for speed.
    """
    settings = request.settings
    
    filepath = DATA_DIR / f"{settings.symbol}_{settings.timeframe}.parquet"
    if not filepath.exists():
        raise HTTPException(404, "Данные не найдены")
    
    df_original = pd.read_parquet(filepath)
    df_original = df_original[~df_original.index.duplicated(keep='first')]
    df_original = df_original.sort_index()
    
    if settings.start_date:
        df_original = df_original[df_original.index >= settings.start_date]
    if settings.end_date:
        df_original = df_original[df_original.index <= settings.end_date]
    
    # Generate parameter grid
    i1_values = list(range(request.i1_min, request.i1_max + 1, request.i1_step))
    i2_values = []
    current = request.i2_min
    while current <= request.i2_max:
        i2_values.append(round(current, 1))
        current += request.i2_step
    
    # Prepare tasks
    tasks = []
    settings_dict = settings.model_dump()
    
    for i1 in i1_values:
        for i2 in i2_values:
            tasks.append({
                'df': df_original,
                'settings': settings_dict,
                'i1': i1,
                'i2': i2,
                'metric': request.metric
            })
    
    logger.info(f"[Heatmap] Starting {len(tasks)} combinations with {NUM_WORKERS} workers")
    
    # Run parallel processing
    results = []
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(_backtest_worker, task): task for task in tasks}
        
        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                logger.error(f"[Heatmap] Worker error: {e}")
    
    # Find best result
    best_result = max(results, key=lambda x: x.get('score', -999))
    
    # Build heatmap matrix
    heatmap_data = []
    for i1 in i1_values:
        row = []
        for i2 in i2_values:
            r = next((x for x in results if x.get('i1') == i1 and x.get('i2') == i2), None)
            row.append(r.get('score', 0) if r else 0)
        heatmap_data.append(row)
    
    return {
        "success": True,
        "heatmap": heatmap_data,
        "i1_values": i1_values,
        "i2_values": i2_values,
        "best": best_result,
        "results": results,
        "workers": NUM_WORKERS,
        "total_combinations": len(tasks)
    }


@router.post("/auto-optimize-stream")
async def auto_optimize_stream(request: AutoOptimizeRequest):
    """
    Auto-optimize with SSE streaming progress.
    
    Modes:
    - indicator: Optimize i1/i2
    - tp: Optimize take profit levels
    - sl: Optimize stop loss
    - filters: Optimize filter settings
    - full: Full optimization (all parameters)
    """
    settings = request.settings
    mode = request.mode
    metric = request.metric
    
    async def generate():
        """SSE generator"""
        filepath = DATA_DIR / f"{settings.symbol}_{settings.timeframe}.parquet"
        
        if not filepath.exists():
            yield f"data: {json.dumps({'type': 'error', 'message': 'Данные не найдены'})}\n\n"
            return
        
        df_original = pd.read_parquet(filepath)
        df_original = df_original[~df_original.index.duplicated(keep='first')]
        df_original = df_original.sort_index()
        
        yield f"data: {json.dumps({'type': 'progress', 'message': f'Загружено {len(df_original)} свечей'})}\n\n"
        await asyncio.sleep(0.01)
        
        # Calculate current performance
        df_current = df_original.copy()
        df_current = calculate_trg(df_current, settings.trg_atr_length, settings.trg_multiplier)
        if settings.use_supertrend:
            df_current = calculate_supertrend(df_current, settings.supertrend_period, settings.supertrend_multiplier)
        df_current = generate_signals(df_current, settings)
        current_trades, current_equity, _, _, _ = run_backtest(df_current, settings)
        current_score, current_metrics = calculate_optimization_score(current_trades, current_equity, settings, metric)
        
        yield f"data: {json.dumps({'type': 'current', 'profit': current_metrics.get('profit_pct', 0), 'win_rate': current_metrics.get('win_rate', 0), 'trades': current_metrics.get('total_trades', 0)})}\n\n"
        
        # Prepare parameter combinations based on mode
        param_list = []
        settings_dict = settings.model_dump()
        
        if mode == "indicator":
            i1_range = [20, 30, 35, 40, 45, 50, 55, 60, 70, 80, 100, 120]
            i2_range = [1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 7, 8]
            for i1 in i1_range:
                for i2 in i2_range:
                    param_list.append({
                        'df': df_original,
                        'settings': settings_dict,
                        'i1': i1,
                        'i2': i2,
                        'metric': metric
                    })
        
        elif mode == "sl":
            for sl_pct in [2, 3, 4, 5, 6, 7, 8, 10, 12, 15]:
                for trail_mode in ["fixed", "breakeven", "cascade"]:
                    param_list.append({
                        'df': df_original,
                        'settings': {**settings_dict, 'sl_percent': sl_pct, 'sl_trailing_mode': trail_mode},
                        'i1': settings.trg_atr_length,
                        'i2': settings.trg_multiplier,
                        'metric': metric
                    })
        
        elif mode == "tp":
            tp_configs = [
                {"tp1_percent": 0.5, "tp2_percent": 1.0, "tp3_percent": 1.5, "tp4_percent": 2.0},
                {"tp1_percent": 0.75, "tp2_percent": 1.25, "tp3_percent": 2.0, "tp4_percent": 3.0},
                {"tp1_percent": 1.0, "tp2_percent": 1.5, "tp3_percent": 2.5, "tp4_percent": 4.0},
                {"tp1_percent": 1.0, "tp2_percent": 2.0, "tp3_percent": 3.5, "tp4_percent": 5.0},
                {"tp1_percent": 1.05, "tp2_percent": 1.95, "tp3_percent": 3.75, "tp4_percent": 6.0},
                {"tp1_percent": 1.25, "tp2_percent": 2.5, "tp3_percent": 4.0, "tp4_percent": 6.5},
                {"tp1_percent": 1.5, "tp2_percent": 3.0, "tp3_percent": 5.0, "tp4_percent": 8.0},
                {"tp1_percent": 2.0, "tp2_percent": 4.0, "tp3_percent": 6.0, "tp4_percent": 10.0},
            ]
            for cfg in tp_configs:
                param_list.append({
                    'df': df_original,
                    'settings': {**settings_dict, **cfg},
                    'i1': settings.trg_atr_length,
                    'i2': settings.trg_multiplier,
                    'metric': metric
                })
        
        elif mode == "filters":
            filter_configs = [
                {'use_supertrend': False, 'use_rsi_filter': False, 'use_adx_filter': False},
                {'use_supertrend': True, 'supertrend_period': 10, 'supertrend_multiplier': 3.0},
                {'use_supertrend': True, 'supertrend_period': 7, 'supertrend_multiplier': 2.0},
                {'use_rsi_filter': True, 'rsi_period': 14, 'rsi_overbought': 70, 'rsi_oversold': 30},
                {'use_rsi_filter': True, 'rsi_period': 7, 'rsi_overbought': 80, 'rsi_oversold': 20},
                {'use_adx_filter': True, 'adx_period': 14, 'adx_threshold': 25},
                {'use_adx_filter': True, 'adx_period': 14, 'adx_threshold': 20},
                {'use_supertrend': True, 'use_rsi_filter': True},
                {'use_supertrend': True, 'use_adx_filter': True},
            ]
            for cfg in filter_configs:
                param_list.append({
                    'df': df_original,
                    'settings': {**settings_dict, **cfg},
                    'i1': settings.trg_atr_length,
                    'i2': settings.trg_multiplier,
                    'metric': metric
                })
        
        elif mode == "full":
            i1_range = [30, 40, 45, 50, 60, 80]
            i2_range = [2, 3, 4, 5, 6]
            sl_configs = [
                {'sl_percent': 4, 'sl_trailing_mode': 'breakeven'},
                {'sl_percent': 6, 'sl_trailing_mode': 'breakeven'},
                {'sl_percent': 8, 'sl_trailing_mode': 'cascade'},
            ]
            for i1 in i1_range:
                for i2 in i2_range:
                    for sl_cfg in sl_configs:
                        param_list.append({
                            'df': df_original,
                            'settings': {**settings_dict, **sl_cfg},
                            'i1': i1,
                            'i2': i2,
                            'metric': metric
                        })
        
        total_combinations = len(param_list)
        yield f"data: {json.dumps({'type': 'start', 'total': total_combinations, 'mode': mode, 'workers': NUM_WORKERS})}\n\n"
        await asyncio.sleep(0.01)
        
        # Run parallel optimization
        best_result = None
        best_score = float('-inf')
        all_results = []
        completed = 0
        
        with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = {executor.submit(_backtest_worker, params): params for params in param_list}
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    all_results.append(result)
                    completed += 1
                    
                    if result.get('score', -999) > best_score:
                        best_score = result['score']
                        best_result = result
                    
                    # Send progress every 5 completions
                    if completed % 5 == 0 or completed == total_combinations:
                        yield f"data: {json.dumps({'type': 'test', 'completed': completed, 'total': total_combinations, 'current_best': best_result})}\n\n"
                        await asyncio.sleep(0.001)
                
                except Exception as e:
                    logger.error(f"[Optimize] Worker error: {e}")
                    completed += 1
        
        # Final result
        yield f"data: {json.dumps({'type': 'complete', 'best': best_result, 'all_results': all_results, 'total_tested': len(all_results)})}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============================================================================
# PLUGIN UI SCHEMA ENDPOINTS
# ============================================================================

@router.get("/{plugin_id}/ui-schema")
async def get_plugin_ui_schema(plugin_id: str):
    """
    Get UI schema for a plugin.
    Used by frontend to dynamically build settings panel.
    """
    if plugin_id == "trg":
        # Return TRG UI schema
        trg = _load_trg_plugin()
        
        if 'ui_schema' in trg:
            schema = trg['ui_schema']()
            return {"success": True, "plugin_id": plugin_id, "schema": schema}
        
        # Fallback: return basic schema
        return {
            "success": True,
            "plugin_id": plugin_id,
            "schema": {
                "sections": [
                    {
                        "id": "indicator",
                        "label": "TRG Indicator",
                        "fields": [
                            {"id": "trg_atr_length", "label": "ATR Length (i1)", "type": "number", "min": 5, "max": 500, "default": 45},
                            {"id": "trg_multiplier", "label": "Multiplier (i2)", "type": "number", "min": 0.5, "max": 20, "step": 0.1, "default": 4.0},
                        ]
                    },
                    {
                        "id": "tp",
                        "label": "Take Profits",
                        "fields": [
                            {"id": "tp_count", "label": "TP Levels", "type": "number", "min": 1, "max": 10, "default": 4},
                            {"id": "tp1_percent", "label": "TP1 %", "type": "number", "min": 0.1, "max": 100, "step": 0.05, "default": 1.05},
                            {"id": "tp1_amount", "label": "TP1 Amount %", "type": "number", "min": 0, "max": 100, "default": 50},
                        ]
                    },
                    {
                        "id": "sl",
                        "label": "Stop Loss",
                        "fields": [
                            {"id": "sl_percent", "label": "SL %", "type": "number", "min": 0.1, "max": 100, "default": 6.0},
                            {"id": "sl_trailing_mode", "label": "Trailing Mode", "type": "select", "options": ["fixed", "breakeven", "cascade"], "default": "breakeven"},
                        ]
                    }
                ],
                "tabs": ["chart", "stats", "trades", "monthly", "optimizer", "heatmap"]
            }
        }
    
    raise HTTPException(404, f"Plugin '{plugin_id}' not found")


@router.get("/{plugin_id}/defaults")
async def get_plugin_defaults(plugin_id: str):
    """
    Get default settings for a plugin.
    """
    if plugin_id == "trg":
        trg = _load_trg_plugin()
        
        if 'defaults' in trg:
            defaults = trg['defaults']()
            return {"success": True, "plugin_id": plugin_id, "defaults": defaults}
        
        # Fallback
        return {
            "success": True,
            "plugin_id": plugin_id,
            "defaults": IndicatorSettings().model_dump()
        }
    
    raise HTTPException(404, f"Plugin '{plugin_id}' not found")


@router.post("/{plugin_id}/validate")
async def validate_plugin_settings(plugin_id: str, settings: dict):
    """
    Validate settings for a plugin.
    """
    if plugin_id == "trg":
        trg = _load_trg_plugin()
        
        if 'validate' in trg:
            result = trg['validate'](settings)
            return {"success": True, "plugin_id": plugin_id, "valid": result.get('valid', True), "errors": result.get('errors', [])}
        
        # Fallback: basic validation via Pydantic
        try:
            IndicatorSettings(**settings)
            return {"success": True, "plugin_id": plugin_id, "valid": True, "errors": []}
        except Exception as e:
            return {"success": True, "plugin_id": plugin_id, "valid": False, "errors": [str(e)]}
    
    raise HTTPException(404, f"Plugin '{plugin_id}' not found")


# ============================================================================
# AVAILABLE PLUGINS
# ============================================================================

@router.get("/plugins")
async def list_available_plugins():
    """
    List all available indicator plugins.
    """
    plugins = []
    
    # TRG is always available
    plugins.append({
        "id": "trg",
        "name": "TRG Indicator",
        "version": "1.5.0",
        "description": "Trend Range Grid indicator with TP/SL management, filters, and optimization",
        "author": "Komas Team",
        "features": ["indicator", "signals", "trading", "filters", "optimizer", "backtest", "ui_schema"]
    })
    
    return {
        "success": True,
        "plugins": plugins,
        "count": len(plugins)
    }


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def indicator_health():
    """Health check for indicator API"""
    trg = _load_trg_plugin()
    
    return {
        "status": "healthy",
        "api": "indicator",
        "version": "1.0.0",
        "data_dir": str(DATA_DIR),
        "data_dir_exists": DATA_DIR.exists(),
        "workers": NUM_WORKERS,
        "trg_plugin_loaded": len(trg) > 0
    }
