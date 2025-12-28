"""
KOMAS Trading Server - Preset Optimizer
========================================
Multi-pair preset optimization engine with parallel processing.

Features:
- Run backtest for all preset × pair combinations
- Calculate aggregate scores per preset
- Generate result matrix (preset × pair)
- SSE streaming for progress updates
- Stability and consistency metrics
- Multiple optimization modes (Quick/Standard/Smart/Full)

Chat #45: Preset Optimizer Core
Chat #46: Preset Optimizer Modes
"""

import asyncio
import json
import logging
import os
import uuid
import numpy as np
import pandas as pd
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, asdict, field
from datetime import datetime
from io import StringIO
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Tuple
from enum import Enum
import hashlib
import time
import threading

# Import optimization modes
from app.services.optimization_modes import (
    OptimizationMode,
    ModeConfig,
    get_mode_config,
    select_presets_for_mode,
    select_pairs_for_mode,
    estimate_optimization_time,
    get_liquidity_ranking,
)

logger = logging.getLogger(__name__)


# ============================================================================
# DATA CLASSES
# ============================================================================

class OptimizationStatus(str, Enum):
    """Optimization run status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ERROR = "error"


@dataclass
class PresetBacktestResult:
    """Result of a single preset × pair backtest"""
    preset_id: str
    preset_name: str
    symbol: str
    timeframe: str
    
    # Core metrics
    total_trades: int = 0
    win_rate: float = 0.0
    profit_pct: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    
    # Trade breakdown
    wins: int = 0
    losses: int = 0
    long_trades: int = 0
    short_trades: int = 0
    avg_trade_pct: float = 0.0
    avg_win_pct: float = 0.0
    avg_loss_pct: float = 0.0
    
    # TP hits
    tp1_hits: int = 0
    tp2_hits: int = 0
    tp3_hits: int = 0
    tp4_hits: int = 0
    sl_hits: int = 0
    
    # Time analysis
    avg_trade_duration_hours: float = 0.0
    longest_winning_streak: int = 0
    longest_losing_streak: int = 0
    
    # Error tracking
    error: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class PresetAggregateScore:
    """Aggregate score for a preset across all pairs"""
    preset_id: str
    preset_name: str
    indicator_type: str
    
    # Aggregate metrics (average across pairs)
    avg_pnl: float = 0.0
    avg_win_rate: float = 0.0
    avg_sharpe: float = 0.0
    avg_profit_factor: float = 0.0
    avg_max_dd: float = 0.0
    avg_trades: float = 0.0
    
    # Consistency metrics
    pnl_std: float = 0.0  # Standard deviation of PnL
    win_rate_std: float = 0.0
    consistency_score: float = 0.0  # Lower is better
    
    # Coverage
    total_pairs: int = 0
    positive_pairs: int = 0
    negative_pairs: int = 0
    positive_ratio: float = 0.0  # % of pairs with positive PnL
    
    # Best/worst
    best_pnl: float = 0.0
    worst_pnl: float = 0.0
    best_pair: str = ""
    worst_pair: str = ""
    
    # Combined scores (0-100)
    profitability_score: float = 0.0  # Based on avg_pnl
    stability_score: float = 0.0  # Based on consistency
    universality_score: float = 0.0  # Based on positive_ratio
    overall_score: float = 0.0  # Combined weighted score
    
    # Ranking
    rank: int = 0
    
    # Detailed results per pair
    pair_results: List[Dict] = field(default_factory=list)


@dataclass 
class OptimizationResult:
    """Complete optimization result"""
    run_id: str
    status: OptimizationStatus
    
    # Configuration
    preset_ids: List[str]
    pairs: List[str]
    timeframe: str
    start_date: Optional[str]
    end_date: Optional[str]
    
    # Mode information (NEW in Chat #46)
    mode: str = "standard"
    original_preset_count: int = 0
    original_pair_count: int = 0
    effective_preset_count: int = 0
    effective_pair_count: int = 0
    
    # Progress
    total_combinations: int = 0
    completed_combinations: int = 0
    progress_percent: float = 0.0
    
    # Timing
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration_seconds: float = 0.0
    estimated_seconds: float = 0.0
    
    # Results
    preset_scores: List[PresetAggregateScore] = field(default_factory=list)
    result_matrix: Dict = field(default_factory=dict)  # preset_id -> pair -> metrics
    
    # Top performers
    top_10_presets: List[Dict] = field(default_factory=list)
    
    # Errors
    errors: List[str] = field(default_factory=list)
    
    # Worker info
    num_workers: int = 0


# ============================================================================
# BACKTEST WORKER FUNCTION (for ProcessPoolExecutor)
# ============================================================================

def run_preset_backtest_worker(args: Dict) -> Dict:
    """
    Worker function for parallel backtest execution.
    This runs in a separate process.
    
    Args:
        args: Dict with keys:
            - df_json: DataFrame as JSON string
            - preset: Preset configuration dict
            - symbol: Trading pair symbol
            - timeframe: Timeframe
            - start_date: Optional start date
            - end_date: Optional end date
    
    Returns:
        Dict with backtest results
    """
    import pandas as pd
    import numpy as np
    import time
    import traceback
    
    start_time = time.time()
    
    try:
        # Parse arguments
        df = pd.read_json(StringIO(args['df_json']), orient='split')
        df.index = pd.to_datetime(df.index)
        preset = args['preset']
        symbol = args['symbol']
        timeframe = args['timeframe']
        
        # Filter by date if specified
        if args.get('start_date'):
            df = df[df.index >= args['start_date']]
        if args.get('end_date'):
            df = df[df.index <= args['end_date']]
        
        if len(df) < 100:
            return {
                'preset_id': preset['id'],
                'preset_name': preset.get('name', preset['id']),
                'symbol': symbol,
                'timeframe': timeframe,
                'error': 'Insufficient data (< 100 candles)',
                'execution_time_ms': (time.time() - start_time) * 1000
            }
        
        # Get indicator type and parameters from preset
        indicator_type = preset.get('indicator_type', 'trg')
        params = preset.get('params', {})
        
        # Run backtest based on indicator type
        if indicator_type == 'trg':
            result = run_trg_backtest(df, params)
        elif indicator_type == 'dominant':
            result = run_dominant_backtest(df, params)
        else:
            result = run_trg_backtest(df, params)  # Default to TRG
        
        # Add metadata
        result['preset_id'] = preset['id']
        result['preset_name'] = preset.get('name', preset['id'])
        result['symbol'] = symbol
        result['timeframe'] = timeframe
        result['execution_time_ms'] = (time.time() - start_time) * 1000
        
        return result
        
    except Exception as e:
        return {
            'preset_id': args.get('preset', {}).get('id', 'unknown'),
            'preset_name': args.get('preset', {}).get('name', 'unknown'),
            'symbol': args.get('symbol', 'unknown'),
            'timeframe': args.get('timeframe', 'unknown'),
            'error': str(e),
            'traceback': traceback.format_exc(),
            'execution_time_ms': (time.time() - start_time) * 1000
        }


def run_trg_backtest(df: pd.DataFrame, params: Dict) -> Dict:
    """
    Run TRG indicator backtest.
    Simplified version for parallel processing.
    """
    import numpy as np
    
    # Extract TRG parameters
    i1 = params.get('i1', params.get('trg_atr_length', 45))
    i2 = params.get('i2', params.get('trg_multiplier', 4.0))
    
    # TP/SL parameters
    tp_count = params.get('tp_count', 4)
    tp_levels = []
    tp_amounts = []
    for i in range(1, 11):
        tp_levels.append(params.get(f'tp{i}_percent', 1.0 + i * 0.5))
        tp_amounts.append(params.get(f'tp{i}_amount', max(0, 50 - i * 10)))
    tp_levels = tp_levels[:tp_count]
    tp_amounts = tp_amounts[:tp_count]
    
    sl_percent = params.get('sl_percent', 6.0)
    sl_mode = params.get('sl_trailing_mode', 'breakeven')
    
    # Filters
    use_supertrend = params.get('use_supertrend', False)
    supertrend_period = params.get('supertrend_period', 10)
    supertrend_multiplier = params.get('supertrend_multiplier', 3.0)
    
    use_rsi = params.get('use_rsi_filter', False)
    rsi_period = params.get('rsi_period', 14)
    rsi_overbought = params.get('rsi_overbought', 70)
    rsi_oversold = params.get('rsi_oversold', 30)
    
    use_adx = params.get('use_adx_filter', False)
    adx_period = params.get('adx_period', 14)
    adx_threshold = params.get('adx_threshold', 25)
    
    # Calculate TRG indicator
    df = calculate_trg_indicator(df, i1, i2)
    
    # Calculate filters if enabled
    if use_supertrend:
        df = calculate_supertrend_filter(df, supertrend_period, supertrend_multiplier)
    if use_rsi:
        df = calculate_rsi(df, rsi_period)
    if use_adx:
        df = calculate_adx(df, adx_period)
    
    # Generate signals
    df['signal'] = 0
    
    # Signal on trend change
    df['trend_change'] = df['trg_trend'].diff().fillna(0)
    
    for i in range(1, len(df)):
        if df.iloc[i]['trend_change'] == 1:  # Changed to bullish
            signal_valid = True
            
            if use_supertrend and 'supertrend_direction' in df.columns:
                if df.iloc[i]['supertrend_direction'] != 1:
                    signal_valid = False
            
            if use_rsi and 'rsi' in df.columns:
                if df.iloc[i]['rsi'] > rsi_overbought:
                    signal_valid = False
            
            if use_adx and 'adx' in df.columns:
                if df.iloc[i]['adx'] < adx_threshold:
                    signal_valid = False
            
            if signal_valid:
                df.iloc[i, df.columns.get_loc('signal')] = 1
                
        elif df.iloc[i]['trend_change'] == -1:  # Changed to bearish
            signal_valid = True
            
            if use_supertrend and 'supertrend_direction' in df.columns:
                if df.iloc[i]['supertrend_direction'] != -1:
                    signal_valid = False
            
            if use_rsi and 'rsi' in df.columns:
                if df.iloc[i]['rsi'] < rsi_oversold:
                    signal_valid = False
            
            if use_adx and 'adx' in df.columns:
                if df.iloc[i]['adx'] < adx_threshold:
                    signal_valid = False
            
            if signal_valid:
                df.iloc[i, df.columns.get_loc('signal')] = -1
    
    # Run backtest simulation
    return simulate_trades(df, tp_levels, tp_amounts, sl_percent, sl_mode)


def run_dominant_backtest(df: pd.DataFrame, params: Dict) -> Dict:
    """
    Run Dominant indicator backtest.
    Simplified version for parallel processing.
    """
    import numpy as np
    
    # Extract Dominant parameters
    sensitivity = params.get('sensitivity', params.get('dominant_sensitivity', 21))
    filter_type = params.get('filter_type', params.get('dominant_filter_type', 0))
    sl_mode = params.get('sl_mode', params.get('dominant_sl_mode', 0))
    
    # TP levels
    tp_levels = [
        params.get('dominant_tp1_percent', params.get('tp1_percent', 1.0)),
        params.get('dominant_tp2_percent', params.get('tp2_percent', 2.0)),
        params.get('dominant_tp3_percent', params.get('tp3_percent', 3.0)),
        params.get('dominant_tp4_percent', params.get('tp4_percent', 5.0))
    ]
    tp_amounts = [
        params.get('dominant_tp1_amount', params.get('tp1_amount', 40.0)),
        params.get('dominant_tp2_amount', params.get('tp2_amount', 30.0)),
        params.get('dominant_tp3_amount', params.get('tp3_amount', 20.0)),
        params.get('dominant_tp4_amount', params.get('tp4_amount', 10.0))
    ]
    
    sl_percent = params.get('dominant_sl_percent', params.get('sl_percent', 2.0))
    
    # Calculate Dominant indicator
    df = calculate_dominant_indicator(df, sensitivity)
    
    # Apply filter if needed
    if filter_type == 1:
        df = apply_atr_filter(df)
    elif filter_type == 2:
        df = calculate_rsi(df, 14)
    elif filter_type == 3:
        df = apply_atr_filter(df)
        df = calculate_rsi(df, 14)
    
    # Generate Dominant signals
    df['signal'] = 0
    
    for i in range(1, len(df)):
        row = df.iloc[i]
        prev_row = df.iloc[i-1]
        
        # Long signal
        can_long = (
            row['close'] >= row.get('imba_trend_line', row['mid_channel']) and
            row['close'] >= row.get('fib_236', row['mid_channel']) and
            row['close'] > row['open']
        )
        
        # Short signal
        can_short = (
            row['close'] <= row.get('imba_trend_line', row['mid_channel']) and
            row['close'] <= row.get('fib_786', row['mid_channel']) and
            row['close'] < row['open']
        )
        
        # Check for new signal (trend change)
        if can_long and not prev_row.get('is_long', False):
            signal_valid = True
            
            if filter_type in [1, 3] and 'atr_condition' in df.columns:
                if not row.get('atr_condition', True):
                    signal_valid = False
            
            if filter_type in [2, 3] and 'rsi' in df.columns:
                if row['rsi'] > 70:
                    signal_valid = False
            
            if signal_valid:
                df.iloc[i, df.columns.get_loc('signal')] = 1
                df.loc[df.index[i], 'is_long'] = True
                df.loc[df.index[i], 'is_short'] = False
                
        elif can_short and not prev_row.get('is_short', False):
            signal_valid = True
            
            if filter_type in [1, 3] and 'atr_condition' in df.columns:
                if not row.get('atr_condition', True):
                    signal_valid = False
            
            if filter_type in [2, 3] and 'rsi' in df.columns:
                if row['rsi'] < 30:
                    signal_valid = False
            
            if signal_valid:
                df.iloc[i, df.columns.get_loc('signal')] = -1
                df.loc[df.index[i], 'is_long'] = False
                df.loc[df.index[i], 'is_short'] = True
        else:
            # Maintain previous state
            df.loc[df.index[i], 'is_long'] = prev_row.get('is_long', False)
            df.loc[df.index[i], 'is_short'] = prev_row.get('is_short', False)
    
    # Map Dominant SL mode to string
    sl_mode_map = {0: 'fixed', 1: 'after_tp1', 2: 'after_tp2', 3: 'after_tp3', 4: 'cascade'}
    sl_mode_str = sl_mode_map.get(sl_mode, 'fixed')
    
    return simulate_trades(df, tp_levels, tp_amounts, sl_percent, sl_mode_str)


def calculate_trg_indicator(df: pd.DataFrame, i1: int, i2: float) -> pd.DataFrame:
    """Calculate TRG indicator values"""
    import numpy as np
    
    # Calculate ATR
    df['tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    df['atr'] = df['tr'].rolling(window=i1).mean()
    
    # Calculate bands
    df['upper_band'] = df['close'].rolling(window=i1).mean() + (i2 * df['atr'])
    df['lower_band'] = df['close'].rolling(window=i1).mean() - (i2 * df['atr'])
    
    # Determine trend
    df['trg_trend'] = 0
    
    for i in range(i1, len(df)):
        if df.iloc[i]['close'] > df.iloc[i-1].get('upper_band', df.iloc[i]['upper_band']):
            df.iloc[i, df.columns.get_loc('trg_trend')] = 1
        elif df.iloc[i]['close'] < df.iloc[i-1].get('lower_band', df.iloc[i]['lower_band']):
            df.iloc[i, df.columns.get_loc('trg_trend')] = -1
        else:
            df.iloc[i, df.columns.get_loc('trg_trend')] = df.iloc[i-1]['trg_trend']
    
    return df


def calculate_dominant_indicator(df: pd.DataFrame, sensitivity: int) -> pd.DataFrame:
    """Calculate Dominant indicator values"""
    import numpy as np
    
    # Calculate channel
    df['high_channel'] = df['high'].rolling(window=sensitivity).max()
    df['low_channel'] = df['low'].rolling(window=sensitivity).min()
    df['mid_channel'] = (df['high_channel'] + df['low_channel']) / 2
    df['channel_range'] = df['high_channel'] - df['low_channel']
    
    # Calculate Fibonacci levels
    df['fib_236'] = df['low_channel'] + (df['channel_range'] * 0.236)
    df['fib_382'] = df['low_channel'] + (df['channel_range'] * 0.382)
    df['fib_500'] = df['mid_channel']
    df['fib_618'] = df['low_channel'] + (df['channel_range'] * 0.618)
    df['fib_786'] = df['low_channel'] + (df['channel_range'] * 0.786)
    
    # imba_trend_line = fib_5 (0.5 level)
    df['imba_trend_line'] = df['fib_500']
    
    # Initialize trend tracking
    df['is_long'] = False
    df['is_short'] = False
    
    return df


def calculate_supertrend_filter(df: pd.DataFrame, period: int, multiplier: float) -> pd.DataFrame:
    """Calculate SuperTrend filter"""
    import numpy as np
    
    # Calculate ATR
    df['st_tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    df['st_atr'] = df['st_tr'].rolling(window=period).mean()
    
    # Calculate bands
    hl2 = (df['high'] + df['low']) / 2
    df['st_upper'] = hl2 + (multiplier * df['st_atr'])
    df['st_lower'] = hl2 - (multiplier * df['st_atr'])
    
    # Determine direction
    df['supertrend_direction'] = 0
    
    for i in range(period, len(df)):
        if df.iloc[i]['close'] > df.iloc[i-1]['st_upper']:
            df.iloc[i, df.columns.get_loc('supertrend_direction')] = 1
        elif df.iloc[i]['close'] < df.iloc[i-1]['st_lower']:
            df.iloc[i, df.columns.get_loc('supertrend_direction')] = -1
        else:
            df.iloc[i, df.columns.get_loc('supertrend_direction')] = df.iloc[i-1]['supertrend_direction']
    
    return df


def calculate_rsi(df: pd.DataFrame, period: int) -> pd.DataFrame:
    """Calculate RSI"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].fillna(50)
    
    return df


def calculate_adx(df: pd.DataFrame, period: int) -> pd.DataFrame:
    """Calculate ADX"""
    import numpy as np
    
    # Calculate +DM and -DM
    df['plus_dm'] = np.where(
        (df['high'] - df['high'].shift(1)) > (df['low'].shift(1) - df['low']),
        np.maximum(df['high'] - df['high'].shift(1), 0),
        0
    )
    df['minus_dm'] = np.where(
        (df['low'].shift(1) - df['low']) > (df['high'] - df['high'].shift(1)),
        np.maximum(df['low'].shift(1) - df['low'], 0),
        0
    )
    
    # Calculate TR
    df['adx_tr'] = np.maximum(
        df['high'] - df['low'],
        np.maximum(
            abs(df['high'] - df['close'].shift(1)),
            abs(df['low'] - df['close'].shift(1))
        )
    )
    
    # Calculate smoothed values
    df['atr_smooth'] = df['adx_tr'].rolling(window=period).mean()
    df['plus_di'] = 100 * (df['plus_dm'].rolling(window=period).mean() / df['atr_smooth'])
    df['minus_di'] = 100 * (df['minus_dm'].rolling(window=period).mean() / df['atr_smooth'])
    
    # Calculate DX and ADX
    df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
    df['adx'] = df['dx'].rolling(window=period).mean()
    df['adx'] = df['adx'].fillna(0)
    
    return df


def apply_atr_filter(df: pd.DataFrame) -> pd.DataFrame:
    """Apply ATR-based volatility filter"""
    import numpy as np
    
    # Calculate ATR if not present
    if 'atr' not in df.columns:
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(window=14).mean()
    
    # ATR condition: current ATR > average ATR (volatility spike)
    avg_atr = df['atr'].rolling(window=20).mean()
    df['atr_condition'] = df['atr'] > avg_atr
    
    return df


def simulate_trades(
    df: pd.DataFrame,
    tp_levels: List[float],
    tp_amounts: List[float],
    sl_percent: float,
    sl_mode: str
) -> Dict:
    """
    Simulate trades based on signals and TP/SL levels.
    Returns backtest statistics.
    """
    import numpy as np
    
    trades = []
    position = None
    capital = 10000.0
    equity_curve = [capital]
    
    # Normalize TP amounts
    total_amount = sum(tp_amounts)
    if total_amount > 0:
        tp_amounts = [a / total_amount * 100 for a in tp_amounts]
    
    # Track TP hits
    tp_hits = {f'tp{i+1}': 0 for i in range(len(tp_levels))}
    sl_hits = 0
    
    # Track streaks
    current_streak = 0
    longest_win_streak = 0
    longest_loss_streak = 0
    
    for i in range(len(df)):
        row = df.iloc[i]
        signal = row.get('signal', 0)
        
        # Check for position exit first
        if position is not None:
            current_price = row['close']
            
            # Check SL
            if position['direction'] == 1:  # Long
                sl_price = position['entry_price'] * (1 - sl_percent / 100)
                if sl_mode == 'breakeven' and position.get('tp1_hit', False):
                    sl_price = position['entry_price']
                elif sl_mode == 'cascade' and position.get('last_tp_hit'):
                    sl_price = position['entry_price'] * (1 + position['last_tp_hit'] / 200)
                
                if row['low'] <= sl_price:
                    # SL hit
                    remaining_amount = 100 - sum(position.get('closed_amounts', []))
                    pnl_pct = -sl_percent * (remaining_amount / 100)
                    
                    trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': df.index[i],
                        'direction': 'long',
                        'entry_price': position['entry_price'],
                        'exit_price': sl_price,
                        'pnl_pct': pnl_pct,
                        'exit_reason': 'sl'
                    })
                    
                    sl_hits += 1
                    capital *= (1 + pnl_pct / 100)
                    equity_curve.append(capital)
                    
                    if current_streak >= 0:
                        current_streak = -1
                    else:
                        current_streak -= 1
                    longest_loss_streak = max(longest_loss_streak, abs(current_streak))
                    
                    position = None
                    continue
                
                # Check TPs
                for tp_idx, (tp_pct, tp_amt) in enumerate(zip(tp_levels, tp_amounts)):
                    tp_key = f'tp{tp_idx + 1}'
                    if not position.get(f'{tp_key}_hit', False):
                        tp_price = position['entry_price'] * (1 + tp_pct / 100)
                        if row['high'] >= tp_price:
                            position[f'{tp_key}_hit'] = True
                            position['closed_amounts'] = position.get('closed_amounts', []) + [tp_amt]
                            position['last_tp_hit'] = tp_pct
                            tp_hits[tp_key] += 1
                            
                            # Check if position fully closed
                            if sum(position.get('closed_amounts', [])) >= 100:
                                total_pnl = sum([tp_levels[j] * tp_amounts[j] / 100 
                                               for j in range(tp_idx + 1) 
                                               if position.get(f'tp{j+1}_hit', False)])
                                
                                trades.append({
                                    'entry_time': position['entry_time'],
                                    'exit_time': df.index[i],
                                    'direction': 'long',
                                    'entry_price': position['entry_price'],
                                    'exit_price': tp_price,
                                    'pnl_pct': total_pnl,
                                    'exit_reason': tp_key
                                })
                                
                                capital *= (1 + total_pnl / 100)
                                equity_curve.append(capital)
                                
                                if current_streak <= 0:
                                    current_streak = 1
                                else:
                                    current_streak += 1
                                longest_win_streak = max(longest_win_streak, current_streak)
                                
                                position = None
                            break
            
            else:  # Short
                sl_price = position['entry_price'] * (1 + sl_percent / 100)
                if sl_mode == 'breakeven' and position.get('tp1_hit', False):
                    sl_price = position['entry_price']
                elif sl_mode == 'cascade' and position.get('last_tp_hit'):
                    sl_price = position['entry_price'] * (1 - position['last_tp_hit'] / 200)
                
                if row['high'] >= sl_price:
                    # SL hit
                    remaining_amount = 100 - sum(position.get('closed_amounts', []))
                    pnl_pct = -sl_percent * (remaining_amount / 100)
                    
                    trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': df.index[i],
                        'direction': 'short',
                        'entry_price': position['entry_price'],
                        'exit_price': sl_price,
                        'pnl_pct': pnl_pct,
                        'exit_reason': 'sl'
                    })
                    
                    sl_hits += 1
                    capital *= (1 + pnl_pct / 100)
                    equity_curve.append(capital)
                    
                    if current_streak >= 0:
                        current_streak = -1
                    else:
                        current_streak -= 1
                    longest_loss_streak = max(longest_loss_streak, abs(current_streak))
                    
                    position = None
                    continue
                
                # Check TPs
                for tp_idx, (tp_pct, tp_amt) in enumerate(zip(tp_levels, tp_amounts)):
                    tp_key = f'tp{tp_idx + 1}'
                    if not position.get(f'{tp_key}_hit', False):
                        tp_price = position['entry_price'] * (1 - tp_pct / 100)
                        if row['low'] <= tp_price:
                            position[f'{tp_key}_hit'] = True
                            position['closed_amounts'] = position.get('closed_amounts', []) + [tp_amt]
                            position['last_tp_hit'] = tp_pct
                            tp_hits[tp_key] += 1
                            
                            # Check if position fully closed
                            if sum(position.get('closed_amounts', [])) >= 100:
                                total_pnl = sum([tp_levels[j] * tp_amounts[j] / 100 
                                               for j in range(tp_idx + 1) 
                                               if position.get(f'tp{j+1}_hit', False)])
                                
                                trades.append({
                                    'entry_time': position['entry_time'],
                                    'exit_time': df.index[i],
                                    'direction': 'short',
                                    'entry_price': position['entry_price'],
                                    'exit_price': tp_price,
                                    'pnl_pct': total_pnl,
                                    'exit_reason': tp_key
                                })
                                
                                capital *= (1 + total_pnl / 100)
                                equity_curve.append(capital)
                                
                                if current_streak <= 0:
                                    current_streak = 1
                                else:
                                    current_streak += 1
                                longest_win_streak = max(longest_win_streak, current_streak)
                                
                                position = None
                            break
        
        # Open new position on signal
        if position is None and signal != 0:
            position = {
                'entry_time': df.index[i],
                'entry_price': row['close'],
                'direction': 1 if signal == 1 else -1,
                'closed_amounts': []
            }
    
    # Close any remaining position at last price
    if position is not None:
        last_row = df.iloc[-1]
        if position['direction'] == 1:
            pnl_pct = ((last_row['close'] - position['entry_price']) / position['entry_price']) * 100
        else:
            pnl_pct = ((position['entry_price'] - last_row['close']) / position['entry_price']) * 100
        
        remaining_amount = 100 - sum(position.get('closed_amounts', []))
        pnl_pct = pnl_pct * (remaining_amount / 100)
        
        trades.append({
            'entry_time': position['entry_time'],
            'exit_time': df.index[-1],
            'direction': 'long' if position['direction'] == 1 else 'short',
            'entry_price': position['entry_price'],
            'exit_price': last_row['close'],
            'pnl_pct': pnl_pct,
            'exit_reason': 'end_of_data'
        })
        
        capital *= (1 + pnl_pct / 100)
        equity_curve.append(capital)
    
    # Calculate statistics
    if not trades:
        return {
            'total_trades': 0,
            'win_rate': 0,
            'profit_pct': 0,
            'profit_factor': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'calmar_ratio': 0,
            'wins': 0,
            'losses': 0,
            'long_trades': 0,
            'short_trades': 0,
            'avg_trade_pct': 0,
            'avg_win_pct': 0,
            'avg_loss_pct': 0,
            'tp1_hits': 0,
            'tp2_hits': 0,
            'tp3_hits': 0,
            'tp4_hits': 0,
            'sl_hits': 0,
            'avg_trade_duration_hours': 0,
            'longest_winning_streak': 0,
            'longest_losing_streak': 0
        }
    
    pnls = [t['pnl_pct'] for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    
    total_trades = len(trades)
    win_count = len(wins)
    loss_count = len(losses)
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    
    profit_pct = (capital - 10000) / 10000 * 100
    
    gross_profit = sum(wins) if wins else 0
    gross_loss = abs(sum(losses)) if losses else 0
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else 99.99
    
    # Max drawdown
    equity_array = np.array(equity_curve)
    peak = np.maximum.accumulate(equity_array)
    drawdown = (peak - equity_array) / peak * 100
    max_drawdown = np.max(drawdown)
    
    # Sharpe ratio (simplified - using daily returns approximation)
    if len(pnls) > 1:
        returns = np.array(pnls)
        sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        # Sortino ratio (only negative returns in denominator)
        negative_returns = returns[returns < 0]
        downside_std = np.std(negative_returns) if len(negative_returns) > 0 else 1
        sortino_ratio = (np.mean(returns) / downside_std) * np.sqrt(252) if downside_std > 0 else 0
    else:
        sharpe_ratio = 0
        sortino_ratio = 0
    
    # Calmar ratio
    calmar_ratio = (profit_pct / max_drawdown) if max_drawdown > 0 else 99.99
    
    long_trades = len([t for t in trades if t['direction'] == 'long'])
    short_trades = len([t for t in trades if t['direction'] == 'short'])
    
    avg_trade_pct = np.mean(pnls)
    avg_win_pct = np.mean(wins) if wins else 0
    avg_loss_pct = np.mean(losses) if losses else 0
    
    # Calculate average trade duration
    durations = []
    for t in trades:
        if isinstance(t['entry_time'], str):
            entry = pd.to_datetime(t['entry_time'])
        else:
            entry = t['entry_time']
        if isinstance(t['exit_time'], str):
            exit = pd.to_datetime(t['exit_time'])
        else:
            exit = t['exit_time']
        duration_hours = (exit - entry).total_seconds() / 3600
        durations.append(duration_hours)
    
    avg_trade_duration_hours = np.mean(durations) if durations else 0
    
    return {
        'total_trades': total_trades,
        'win_rate': round(win_rate, 2),
        'profit_pct': round(profit_pct, 2),
        'profit_factor': round(profit_factor, 2),
        'max_drawdown': round(max_drawdown, 2),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'sortino_ratio': round(sortino_ratio, 2),
        'calmar_ratio': round(calmar_ratio, 2),
        'wins': win_count,
        'losses': loss_count,
        'long_trades': long_trades,
        'short_trades': short_trades,
        'avg_trade_pct': round(avg_trade_pct, 2),
        'avg_win_pct': round(avg_win_pct, 2),
        'avg_loss_pct': round(avg_loss_pct, 2),
        'tp1_hits': tp_hits.get('tp1', 0),
        'tp2_hits': tp_hits.get('tp2', 0),
        'tp3_hits': tp_hits.get('tp3', 0),
        'tp4_hits': tp_hits.get('tp4', 0),
        'sl_hits': sl_hits,
        'avg_trade_duration_hours': round(avg_trade_duration_hours, 2),
        'longest_winning_streak': longest_win_streak,
        'longest_losing_streak': longest_loss_streak
    }


# ============================================================================
# MAIN OPTIMIZER CLASS
# ============================================================================

class PresetOptimizer:
    """
    Multi-pair preset optimizer with parallel processing.
    
    Features:
    - Run backtests for all preset × pair combinations
    - Calculate aggregate scores per preset
    - Generate result matrix
    - SSE streaming for progress updates
    - Multiple optimization modes (Quick/Standard/Smart/Full)
    """
    
    def __init__(self, data_dir: str = "data", db_path: str = "data/komas.db"):
        self.data_dir = Path(data_dir)
        self.db_path = db_path
        
        # Worker configuration
        self.num_workers = os.cpu_count() or 4
        
        # Active optimization tracking
        self._active_runs: Dict[str, OptimizationResult] = {}
        self._cancelled_runs: set = set()
        self._lock = threading.Lock()
        
        # Previous results cache (for smart mode)
        self._previous_results: Dict[str, Dict] = {}
        
        logger.info(f"PresetOptimizer initialized with {self.num_workers} workers")
    
    def generate_run_id(self) -> str:
        """Generate unique run ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_part = uuid.uuid4().hex[:8]
        return f"opt_{timestamp}_{unique_part}"
    
    def load_candle_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Load candle data from parquet file"""
        filepath = self.data_dir / f"{symbol}_{timeframe}.parquet"
        
        if not filepath.exists():
            logger.warning(f"Data file not found: {filepath}")
            return None
        
        try:
            df = pd.read_parquet(filepath)
            df = df[~df.index.duplicated(keep='first')]
            df = df.sort_index()
            return df
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            return None
    
    def get_presets(self, preset_ids: List[str]) -> List[Dict]:
        """
        Load presets from database.
        Returns list of preset dictionaries.
        """
        from app.database.presets_db import get_preset
        
        presets = []
        for preset_id in preset_ids:
            preset = get_preset(preset_id)
            if preset:
                presets.append(preset)
            else:
                logger.warning(f"Preset not found: {preset_id}")
        
        return presets
    
    def get_all_presets(self, indicator_type: Optional[str] = None) -> List[Dict]:
        """
        Load all presets from database.
        Optionally filter by indicator type.
        """
        from app.database.presets_db import list_presets
        
        try:
            filters = {}
            if indicator_type:
                filters['indicator_type'] = indicator_type
            
            presets = list_presets(
                indicator_type=indicator_type,
                category=None,
                is_active=True,
                limit=1000
            )
            return presets
        except Exception as e:
            logger.error(f"Error loading presets: {e}")
            return []
    
    def calculate_aggregate_scores(
        self, 
        results: List[PresetBacktestResult],
        preset_id: str,
        preset_name: str,
        indicator_type: str
    ) -> PresetAggregateScore:
        """
        Calculate aggregate score for a preset across all pairs.
        """
        # Filter out error results
        valid_results = [r for r in results if r.error is None and r.total_trades > 0]
        
        if not valid_results:
            return PresetAggregateScore(
                preset_id=preset_id,
                preset_name=preset_name,
                indicator_type=indicator_type,
                total_pairs=len(results),
                positive_pairs=0,
                negative_pairs=len(results)
            )
        
        # Extract metrics
        pnls = [r.profit_pct for r in valid_results]
        win_rates = [r.win_rate for r in valid_results]
        sharpes = [r.sharpe_ratio for r in valid_results]
        profit_factors = [r.profit_factor for r in valid_results]
        max_dds = [r.max_drawdown for r in valid_results]
        trade_counts = [r.total_trades for r in valid_results]
        
        # Calculate averages
        avg_pnl = np.mean(pnls)
        avg_win_rate = np.mean(win_rates)
        avg_sharpe = np.mean(sharpes)
        avg_profit_factor = np.mean(profit_factors)
        avg_max_dd = np.mean(max_dds)
        avg_trades = np.mean(trade_counts)
        
        # Calculate consistency (standard deviation)
        pnl_std = np.std(pnls)
        win_rate_std = np.std(win_rates)
        
        # Consistency score (lower is better, 0-100 scale inverted)
        consistency_score = 100 - min(100, pnl_std * 5)  # Scale factor of 5
        
        # Coverage
        positive_pairs = len([p for p in pnls if p > 0])
        negative_pairs = len([p for p in pnls if p <= 0])
        positive_ratio = positive_pairs / len(pnls) * 100 if pnls else 0
        
        # Best/worst
        best_idx = np.argmax(pnls)
        worst_idx = np.argmin(pnls)
        best_pnl = pnls[best_idx]
        worst_pnl = pnls[worst_idx]
        best_pair = valid_results[best_idx].symbol
        worst_pair = valid_results[worst_idx].symbol
        
        # Calculate component scores (0-100)
        
        # Profitability score: based on avg_pnl
        # Scale: -50% to +100% -> 0 to 100
        profitability_score = max(0, min(100, (avg_pnl + 50) * 100 / 150))
        
        # Stability score: based on low drawdown and high consistency
        # Lower DD and lower variance = higher score
        dd_score = max(0, min(100, 100 - avg_max_dd * 2))  # 0% DD = 100, 50% DD = 0
        stability_score = (dd_score + consistency_score) / 2
        
        # Universality score: based on positive ratio
        universality_score = positive_ratio
        
        # Overall score: weighted combination
        # 40% profitability, 30% stability, 30% universality
        overall_score = (
            profitability_score * 0.40 +
            stability_score * 0.30 +
            universality_score * 0.30
        )
        
        # Prepare pair results for detailed view
        pair_results = []
        for r in valid_results:
            pair_results.append({
                'symbol': r.symbol,
                'profit_pct': r.profit_pct,
                'win_rate': r.win_rate,
                'total_trades': r.total_trades,
                'max_drawdown': r.max_drawdown,
                'sharpe_ratio': r.sharpe_ratio,
                'profit_factor': r.profit_factor
            })
        
        return PresetAggregateScore(
            preset_id=preset_id,
            preset_name=preset_name,
            indicator_type=indicator_type,
            avg_pnl=round(avg_pnl, 2),
            avg_win_rate=round(avg_win_rate, 2),
            avg_sharpe=round(avg_sharpe, 2),
            avg_profit_factor=round(avg_profit_factor, 2),
            avg_max_dd=round(avg_max_dd, 2),
            avg_trades=round(avg_trades, 2),
            pnl_std=round(pnl_std, 2),
            win_rate_std=round(win_rate_std, 2),
            consistency_score=round(consistency_score, 2),
            total_pairs=len(results),
            positive_pairs=positive_pairs,
            negative_pairs=negative_pairs,
            positive_ratio=round(positive_ratio, 2),
            best_pnl=round(best_pnl, 2),
            worst_pnl=round(worst_pnl, 2),
            best_pair=best_pair,
            worst_pair=worst_pair,
            profitability_score=round(profitability_score, 2),
            stability_score=round(stability_score, 2),
            universality_score=round(universality_score, 2),
            overall_score=round(overall_score, 2),
            pair_results=pair_results
        )
    
    def generate_result_matrix(
        self, 
        all_results: List[PresetBacktestResult]
    ) -> Dict[str, Dict[str, Dict]]:
        """
        Generate result matrix: preset_id -> symbol -> metrics
        """
        matrix = {}
        
        for result in all_results:
            if result.preset_id not in matrix:
                matrix[result.preset_id] = {}
            
            matrix[result.preset_id][result.symbol] = {
                'profit_pct': result.profit_pct,
                'win_rate': result.win_rate,
                'total_trades': result.total_trades,
                'max_drawdown': result.max_drawdown,
                'sharpe_ratio': result.sharpe_ratio,
                'profit_factor': result.profit_factor,
                'error': result.error
            }
        
        return matrix
    
    async def run_optimization(
        self,
        preset_ids: List[str],
        pairs: List[str],
        timeframe: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        mode: str = "standard",
        progress_callback: Optional[Callable] = None
    ) -> OptimizationResult:
        """
        Run optimization for all preset × pair combinations.
        
        Args:
            preset_ids: List of preset IDs to test
            pairs: List of trading pairs
            timeframe: Timeframe for backtest
            start_date: Optional start date (YYYY-MM-DD)
            end_date: Optional end date (YYYY-MM-DD)
            mode: Optimization mode (quick/standard/smart/full)
            progress_callback: Async callback for progress updates
        
        Returns:
            OptimizationResult with all scores and matrix
        """
        run_id = self.generate_run_id()
        started_at = datetime.now().isoformat()
        
        # Get mode configuration
        mode_config = get_mode_config(mode)
        
        # Store original counts
        original_preset_count = len(preset_ids)
        original_pair_count = len(pairs)
        
        # Initialize result
        result = OptimizationResult(
            run_id=run_id,
            status=OptimizationStatus.RUNNING,
            preset_ids=preset_ids,
            pairs=pairs,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            mode=mode,
            original_preset_count=original_preset_count,
            original_pair_count=original_pair_count,
            started_at=started_at,
            num_workers=self.num_workers
        )
        
        with self._lock:
            self._active_runs[run_id] = result
        
        try:
            # Load presets
            presets = self.get_presets(preset_ids)
            if not presets:
                result.status = OptimizationStatus.ERROR
                result.errors.append("No valid presets found")
                return result
            
            # Apply mode selection to presets
            previous_results = self._previous_results.get(timeframe, {})
            selected_presets = select_presets_for_mode(presets, mode, previous_results)
            
            # Apply mode selection to pairs
            selected_pairs = select_pairs_for_mode(pairs, mode)
            
            # Update effective counts
            result.effective_preset_count = len(selected_presets)
            result.effective_pair_count = len(selected_pairs)
            
            logger.info(f"Mode '{mode}': {len(selected_presets)}/{len(presets)} presets, "
                       f"{len(selected_pairs)}/{len(pairs)} pairs")
            
            # Prepare data for selected pairs
            pair_data = {}
            for symbol in selected_pairs:
                df = self.load_candle_data(symbol, timeframe)
                if df is not None:
                    pair_data[symbol] = df.to_json(orient='split', date_format='iso')
                else:
                    result.errors.append(f"No data for {symbol}")
            
            if not pair_data:
                result.status = OptimizationStatus.ERROR
                result.errors.append("No valid pair data found")
                return result
            
            # Calculate total combinations
            total_combinations = len(selected_presets) * len(pair_data)
            result.total_combinations = total_combinations
            
            # Estimate time
            time_estimate = estimate_optimization_time(
                mode, len(selected_presets), len(pair_data), self.num_workers
            )
            result.estimated_seconds = time_estimate['estimated_seconds']
            
            if progress_callback:
                await progress_callback({
                    'type': 'start',
                    'run_id': run_id,
                    'mode': mode,
                    'total': total_combinations,
                    'presets': len(selected_presets),
                    'pairs': len(pair_data),
                    'workers': self.num_workers,
                    'estimated_seconds': result.estimated_seconds,
                    'estimated_time': time_estimate['human_readable']
                })
            
            # Prepare work items
            work_items = []
            for preset in selected_presets:
                for symbol, df_json in pair_data.items():
                    work_items.append({
                        'df_json': df_json,
                        'preset': preset,
                        'symbol': symbol,
                        'timeframe': timeframe,
                        'start_date': start_date,
                        'end_date': end_date
                    })
            
            # Run parallel backtests
            all_results = []
            completed = 0
            
            with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
                # Submit all tasks
                futures = {
                    executor.submit(run_preset_backtest_worker, item): item 
                    for item in work_items
                }
                
                # Process results as they complete
                for future in as_completed(futures):
                    # Check for cancellation
                    if run_id in self._cancelled_runs:
                        executor.shutdown(wait=False, cancel_futures=True)
                        result.status = OptimizationStatus.CANCELLED
                        return result
                    
                    try:
                        backtest_result = future.result()
                        
                        # Convert to PresetBacktestResult
                        preset_result = PresetBacktestResult(
                            preset_id=backtest_result.get('preset_id', 'unknown'),
                            preset_name=backtest_result.get('preset_name', 'unknown'),
                            symbol=backtest_result.get('symbol', 'unknown'),
                            timeframe=timeframe,
                            total_trades=backtest_result.get('total_trades', 0),
                            win_rate=backtest_result.get('win_rate', 0),
                            profit_pct=backtest_result.get('profit_pct', 0),
                            profit_factor=backtest_result.get('profit_factor', 0),
                            max_drawdown=backtest_result.get('max_drawdown', 0),
                            sharpe_ratio=backtest_result.get('sharpe_ratio', 0),
                            sortino_ratio=backtest_result.get('sortino_ratio', 0),
                            calmar_ratio=backtest_result.get('calmar_ratio', 0),
                            wins=backtest_result.get('wins', 0),
                            losses=backtest_result.get('losses', 0),
                            long_trades=backtest_result.get('long_trades', 0),
                            short_trades=backtest_result.get('short_trades', 0),
                            avg_trade_pct=backtest_result.get('avg_trade_pct', 0),
                            avg_win_pct=backtest_result.get('avg_win_pct', 0),
                            avg_loss_pct=backtest_result.get('avg_loss_pct', 0),
                            tp1_hits=backtest_result.get('tp1_hits', 0),
                            tp2_hits=backtest_result.get('tp2_hits', 0),
                            tp3_hits=backtest_result.get('tp3_hits', 0),
                            tp4_hits=backtest_result.get('tp4_hits', 0),
                            sl_hits=backtest_result.get('sl_hits', 0),
                            avg_trade_duration_hours=backtest_result.get('avg_trade_duration_hours', 0),
                            longest_winning_streak=backtest_result.get('longest_winning_streak', 0),
                            longest_losing_streak=backtest_result.get('longest_losing_streak', 0),
                            error=backtest_result.get('error'),
                            execution_time_ms=backtest_result.get('execution_time_ms', 0)
                        )
                        
                        all_results.append(preset_result)
                        
                    except Exception as e:
                        logger.error(f"Backtest worker error: {e}")
                        result.errors.append(str(e))
                    
                    completed += 1
                    result.completed_combinations = completed
                    result.progress_percent = (completed / total_combinations) * 100
                    
                    if progress_callback and completed % 5 == 0:
                        await progress_callback({
                            'type': 'progress',
                            'run_id': run_id,
                            'completed': completed,
                            'total': total_combinations,
                            'percent': round(result.progress_percent, 1)
                        })
            
            # Calculate aggregate scores per preset
            preset_scores = []
            for preset in selected_presets:
                preset_results = [r for r in all_results if r.preset_id == preset['id']]
                score = self.calculate_aggregate_scores(
                    preset_results,
                    preset['id'],
                    preset.get('name', preset['id']),
                    preset.get('indicator_type', 'trg')
                )
                preset_scores.append(score)
            
            # Sort by overall score and assign ranks
            preset_scores.sort(key=lambda x: x.overall_score, reverse=True)
            for i, score in enumerate(preset_scores):
                score.rank = i + 1
            
            result.preset_scores = preset_scores
            
            # Generate result matrix
            result.result_matrix = self.generate_result_matrix(all_results)
            
            # Get top 10
            result.top_10_presets = [
                asdict(s) for s in preset_scores[:10]
            ]
            
            # Cache results for smart mode
            self._cache_results(timeframe, preset_scores)
            
            # Finalize
            result.status = OptimizationStatus.COMPLETED
            result.completed_at = datetime.now().isoformat()
            result.duration_seconds = (
                datetime.fromisoformat(result.completed_at) - 
                datetime.fromisoformat(result.started_at)
            ).total_seconds()
            
            if progress_callback:
                await progress_callback({
                    'type': 'complete',
                    'run_id': run_id,
                    'mode': mode,
                    'duration': round(result.duration_seconds, 2),
                    'top_preset': result.top_10_presets[0] if result.top_10_presets else None
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            result.status = OptimizationStatus.ERROR
            result.errors.append(str(e))
            return result
        
        finally:
            with self._lock:
                if run_id in self._active_runs:
                    del self._active_runs[run_id]
    
    def _cache_results(self, timeframe: str, preset_scores: List[PresetAggregateScore]):
        """Cache results for smart mode optimization"""
        self._previous_results[timeframe] = {
            score.preset_id: {
                'overall_score': score.overall_score,
                'avg_pnl': score.avg_pnl,
                'positive_ratio': score.positive_ratio
            }
            for score in preset_scores
        }
    
    def cancel_optimization(self, run_id: str) -> bool:
        """Cancel a running optimization"""
        with self._lock:
            if run_id in self._active_runs:
                self._cancelled_runs.add(run_id)
                return True
            return False
    
    def get_active_runs(self) -> List[str]:
        """Get list of active run IDs"""
        with self._lock:
            return list(self._active_runs.keys())
    
    def get_run_status(self, run_id: str) -> Optional[Dict]:
        """Get status of a specific run"""
        with self._lock:
            if run_id in self._active_runs:
                run = self._active_runs[run_id]
                return {
                    'run_id': run_id,
                    'status': run.status.value,
                    'mode': run.mode,
                    'progress': run.progress_percent,
                    'completed': run.completed_combinations,
                    'total': run.total_combinations,
                    'estimated_seconds': run.estimated_seconds
                }
            return None


# ============================================================================
# GLOBAL OPTIMIZER INSTANCE
# ============================================================================

_optimizer_instance: Optional[PresetOptimizer] = None


def get_preset_optimizer() -> PresetOptimizer:
    """Get or create global optimizer instance"""
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = PresetOptimizer()
    return _optimizer_instance
