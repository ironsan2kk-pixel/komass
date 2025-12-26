"""
Komas Trading System - TRG Backtest Engine
===========================================
Complete backtesting engine for TRG indicator plugin.

Features:
- Full backtesting with equity curve tracking
- Monthly statistics breakdown
- TP/SL hit tracking per trade
- Adaptive optimization during backtest
- Quick backtest for optimizer
- Parallel-safe execution
- Comprehensive statistics

Author: Komas Trading System
Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, List, Dict, Any, Tuple, Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd
import numpy as np
import logging
import json
import os

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class BacktestConfig:
    """Configuration for backtesting"""
    
    # Data
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    # TRG Indicator
    trg_atr_length: int = 45
    trg_multiplier: float = 4.0
    
    # Take Profits (10 levels)
    tp_count: int = 4
    tp_percents: List[float] = field(default_factory=lambda: [
        1.05, 1.95, 3.75, 6.0, 8.0, 10.0, 12.0, 15.0, 18.0, 20.0
    ])
    tp_amounts: List[float] = field(default_factory=lambda: [
        50.0, 30.0, 15.0, 5.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    ])
    
    # Stop Loss
    sl_percent: float = 6.0
    sl_trailing_mode: str = "breakeven"  # fixed, breakeven, cascade
    
    # Leverage & Commission
    leverage: float = 1.0
    use_commission: bool = False
    commission_percent: float = 0.1
    
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
    
    # Adaptive optimization
    adaptive_mode: Optional[str] = None  # None, "indicator", "tp", "all"
    
    # Capital
    initial_capital: float = 10000.0
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BacktestConfig':
        """Create config from dictionary"""
        config = cls()
        
        # Map flat TP fields to lists
        tp_percents = []
        tp_amounts = []
        for i in range(1, 11):
            tp_percents.append(data.get(f'tp{i}_percent', config.tp_percents[i-1]))
            tp_amounts.append(data.get(f'tp{i}_amount', config.tp_amounts[i-1]))
        
        # Set all fields
        for key, value in data.items():
            if hasattr(config, key) and not key.startswith('tp') and key not in ['tp_percents', 'tp_amounts']:
                setattr(config, key, value)
        
        config.tp_percents = tp_percents
        config.tp_amounts = tp_amounts
        config.tp_count = data.get('tp_count', 4)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'trg_atr_length': self.trg_atr_length,
            'trg_multiplier': self.trg_multiplier,
            'tp_count': self.tp_count,
            'sl_percent': self.sl_percent,
            'sl_trailing_mode': self.sl_trailing_mode,
            'leverage': self.leverage,
            'use_commission': self.use_commission,
            'commission_percent': self.commission_percent,
            'use_supertrend': self.use_supertrend,
            'supertrend_period': self.supertrend_period,
            'supertrend_multiplier': self.supertrend_multiplier,
            'use_rsi_filter': self.use_rsi_filter,
            'rsi_period': self.rsi_period,
            'rsi_overbought': self.rsi_overbought,
            'rsi_oversold': self.rsi_oversold,
            'use_adx_filter': self.use_adx_filter,
            'adx_period': self.adx_period,
            'adx_threshold': self.adx_threshold,
            'use_volume_filter': self.use_volume_filter,
            'volume_ma_period': self.volume_ma_period,
            'volume_threshold': self.volume_threshold,
            'allow_reentry': self.allow_reentry,
            'reentry_after_sl': self.reentry_after_sl,
            'reentry_after_tp': self.reentry_after_tp,
            'adaptive_mode': self.adaptive_mode,
            'initial_capital': self.initial_capital,
        }
        
        # Flatten TP arrays
        for i in range(10):
            result[f'tp{i+1}_percent'] = self.tp_percents[i]
            result[f'tp{i+1}_amount'] = self.tp_amounts[i]
        
        return result
    
    def get_active_tp_levels(self) -> Tuple[List[float], List[float]]:
        """Get active TP percents and amounts (normalized)"""
        percents = self.tp_percents[:self.tp_count]
        amounts = self.tp_amounts[:self.tp_count]
        
        # Normalize amounts to 100%
        total = sum(amounts)
        if total > 0:
            amounts = [a / total * 100 for a in amounts]
        
        return percents, amounts


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class MonthlyStats:
    """Monthly statistics"""
    month: str
    trades: int = 0
    wins: int = 0
    losses: int = 0
    pnl: float = 0.0
    pnl_amount: float = 0.0
    long_trades: int = 0
    short_trades: int = 0
    tp1_hits: int = 0
    tp2_hits: int = 0
    tp3_hits: int = 0
    tp4_hits: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'month': self.month,
            'trades': self.trades,
            'wins': self.wins,
            'losses': self.losses,
            'pnl': round(self.pnl, 2),
            'pnl_amount': round(self.pnl_amount, 2),
            'long_trades': self.long_trades,
            'short_trades': self.short_trades,
            'tp1_hits': self.tp1_hits,
            'tp2_hits': self.tp2_hits,
            'tp3_hits': self.tp3_hits,
            'tp4_hits': self.tp4_hits,
        }


@dataclass
class TPStats:
    """Take profit hit statistics"""
    total_trades: int = 0
    tp1_hits: int = 0
    tp2_hits: int = 0
    tp3_hits: int = 0
    tp4_hits: int = 0
    tp5_hits: int = 0
    tp6_hits: int = 0
    tp7_hits: int = 0
    tp8_hits: int = 0
    tp9_hits: int = 0
    tp10_hits: int = 0
    sl_hits: int = 0
    reverse_exits: int = 0
    
    def record_tp_hit(self, tp_index: int):
        """Record a TP hit (1-based index)"""
        attr_name = f'tp{tp_index}_hits'
        if hasattr(self, attr_name):
            setattr(self, attr_name, getattr(self, attr_name) + 1)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_trades': self.total_trades,
            'tp1_hits': self.tp1_hits,
            'tp2_hits': self.tp2_hits,
            'tp3_hits': self.tp3_hits,
            'tp4_hits': self.tp4_hits,
            'tp5_hits': self.tp5_hits,
            'tp6_hits': self.tp6_hits,
            'tp7_hits': self.tp7_hits,
            'tp8_hits': self.tp8_hits,
            'tp9_hits': self.tp9_hits,
            'tp10_hits': self.tp10_hits,
            'sl_hits': self.sl_hits,
            'reverse_exits': self.reverse_exits,
        }


@dataclass
class BacktestResult:
    """Complete backtest result"""
    
    # Trades
    trades: List[Dict[str, Any]] = field(default_factory=list)
    equity_curve: List[Dict[str, Any]] = field(default_factory=list)
    
    # Statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: Optional[float] = None
    recovery_factor: Optional[float] = None
    
    # Capital
    initial_capital: float = 10000.0
    final_capital: float = 10000.0
    profit_pct: float = 0.0
    
    # Breakdown
    long_trades: int = 0
    long_wins: int = 0
    long_win_rate: float = 0.0
    short_trades: int = 0
    short_wins: int = 0
    short_win_rate: float = 0.0
    reentry_trades: int = 0
    reentry_wins: int = 0
    reentry_win_rate: float = 0.0
    
    # TP/SL stats
    tp_stats: TPStats = field(default_factory=TPStats)
    monthly_stats: Dict[str, MonthlyStats] = field(default_factory=dict)
    accuracy: Dict[str, float] = field(default_factory=dict)
    profit_panel: Dict[str, Dict] = field(default_factory=dict)
    
    # Parameter changes (for adaptive mode)
    param_changes: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': round(self.win_rate, 2),
            'total_pnl': round(self.total_pnl, 2),
            'avg_win': round(self.avg_win, 2),
            'avg_loss': round(self.avg_loss, 2),
            'profit_factor': round(self.profit_factor, 2),
            'max_drawdown': round(self.max_drawdown, 2),
            'sharpe': self.sharpe_ratio,
            'recovery_factor': self.recovery_factor,
            'initial_capital': self.initial_capital,
            'final_capital': round(self.final_capital, 2),
            'profit_pct': round(self.profit_pct, 2),
            'long_trades': self.long_trades,
            'long_wins': self.long_wins,
            'long_win_rate': round(self.long_win_rate, 2),
            'short_trades': self.short_trades,
            'short_wins': self.short_wins,
            'short_win_rate': round(self.short_win_rate, 2),
            'reentry_trades': self.reentry_trades,
            'reentry_wins': self.reentry_wins,
            'reentry_win_rate': round(self.reentry_win_rate, 2),
            'accuracy': self.accuracy,
            'profit_panel': self.profit_panel,
        }


# ============================================================================
# INDICATOR CALCULATIONS
# ============================================================================

def calculate_atr(df: pd.DataFrame, period: int) -> pd.Series:
    """Calculate ATR (Average True Range)"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # RMA (Wilder's smoothing)
    atr = tr.ewm(alpha=1/period, adjust=False).mean()
    return atr


def calculate_trg(df: pd.DataFrame, atr_length: int, multiplier: float) -> pd.DataFrame:
    """Calculate TRG indicator"""
    df = df.copy()
    
    high = df['high']
    low = df['low']
    close = df['close']
    
    # ATR
    atr = calculate_atr(df, atr_length)
    
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
        
        df.iloc[i, df.columns.get_loc('trg_trend')] = trend
    
    # TRG line (follows trend)
    df['trg_line'] = np.where(df['trg_trend'] == 1, df['trg_lower'], df['trg_upper'])
    
    return df


def calculate_supertrend(df: pd.DataFrame, period: int, multiplier: float) -> pd.DataFrame:
    """Calculate SuperTrend indicator"""
    df = df.copy()
    
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
    df = df.copy()
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))
    return df


def calculate_adx(df: pd.DataFrame, period: int) -> pd.DataFrame:
    """Calculate ADX"""
    df = df.copy()
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


def generate_signals(df: pd.DataFrame, config: BacktestConfig) -> pd.DataFrame:
    """Generate entry signals with filter application"""
    df = df.copy()
    df['signal'] = 0
    
    # TRG signals (trend change)
    trend_change_long = (df['trg_trend'] == 1) & (df['trg_trend'].shift(1) == -1)
    trend_change_short = (df['trg_trend'] == -1) & (df['trg_trend'].shift(1) == 1)
    
    # Filter conditions
    long_filter = pd.Series(True, index=df.index)
    short_filter = pd.Series(True, index=df.index)
    
    # SuperTrend filter
    if config.use_supertrend and 'supertrend_dir' in df.columns:
        long_filter &= df['supertrend_dir'] == 1
        short_filter &= df['supertrend_dir'] == -1
    
    # RSI filter
    if config.use_rsi_filter and 'rsi' in df.columns:
        long_filter &= df['rsi'] < config.rsi_overbought
        short_filter &= df['rsi'] > config.rsi_oversold
    
    # ADX filter
    if config.use_adx_filter and 'adx' in df.columns:
        long_filter &= df['adx'] > config.adx_threshold
        short_filter &= df['adx'] > config.adx_threshold
    
    # Volume filter
    if config.use_volume_filter and 'volume' in df.columns:
        vol_ma = df['volume'].rolling(config.volume_ma_period).mean()
        vol_filter = df['volume'] > vol_ma * config.volume_threshold
        long_filter &= vol_filter
        short_filter &= vol_filter
    
    # Apply signals
    df.loc[trend_change_long & long_filter, 'signal'] = 1
    df.loc[trend_change_short & short_filter, 'signal'] = -1
    
    return df


# ============================================================================
# BACKTEST ENGINE
# ============================================================================

class TRGBacktest:
    """
    Complete backtesting engine for TRG indicator.
    
    Features:
    - Full backtest with equity curve
    - Partial TP closes
    - Trailing stop loss (fixed, breakeven, cascade)
    - Re-entry after SL/TP
    - Leverage and commission
    - Adaptive optimization
    - Monthly statistics
    """
    
    def __init__(self, config: Optional[BacktestConfig] = None):
        """Initialize backtest engine"""
        self.config = config or BacktestConfig()
        
        # Results
        self.result: Optional[BacktestResult] = None
        self._trades: List[Dict] = []
        self._equity_curve: List[Dict] = []
        self._monthly_stats: Dict[str, MonthlyStats] = {}
        self._tp_stats = TPStats()
        self._param_changes: List[Dict] = []
    
    def run(self, df: pd.DataFrame) -> BacktestResult:
        """
        Run full backtest on data.
        
        Args:
            df: DataFrame with OHLCV data
        
        Returns:
            BacktestResult with all statistics
        """
        # Prepare data
        df = self._prepare_data(df)
        
        # Calculate indicators
        df = calculate_trg(df, self.config.trg_atr_length, self.config.trg_multiplier)
        
        if self.config.use_supertrend:
            df = calculate_supertrend(df, self.config.supertrend_period, self.config.supertrend_multiplier)
        
        if self.config.use_rsi_filter:
            df = calculate_rsi(df, self.config.rsi_period)
        
        if self.config.use_adx_filter:
            df = calculate_adx(df, self.config.adx_period)
        
        # Generate signals
        df = generate_signals(df, self.config)
        
        # Run trading simulation
        trades, equity_curve, tp_stats, monthly_stats, param_changes = self._run_trading(
            df, 
            adaptive_mode=self.config.adaptive_mode
        )
        
        # Calculate statistics
        result = self._calculate_statistics(trades, equity_curve, monthly_stats)
        result.trades = trades
        result.equity_curve = equity_curve
        result.tp_stats = tp_stats
        result.monthly_stats = monthly_stats
        result.param_changes = param_changes
        
        self.result = result
        return result
    
    def run_quick(self, df: pd.DataFrame, 
                  tp_levels: Optional[List[float]] = None,
                  sl_pct: Optional[float] = None) -> List[Dict]:
        """
        Run quick backtest for optimization.
        Returns only trades list, not full statistics.
        
        Args:
            df: DataFrame with signals already generated
            tp_levels: Optional TP levels override
            sl_pct: Optional SL percent override
        
        Returns:
            List of trade dicts
        """
        # Use provided overrides
        config = BacktestConfig()
        config.__dict__.update(self.config.__dict__)
        
        if tp_levels:
            config.tp_percents = tp_levels + [0.0] * (10 - len(tp_levels))
            config.tp_count = len(tp_levels)
        
        if sl_pct:
            config.sl_percent = sl_pct
        
        # Simple trading simulation without statistics
        trades = self._run_quick_trading(df, config)
        return trades
    
    def _prepare_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare data for backtesting"""
        df = df.copy()
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Sort by time
        df = df.sort_index()
        
        # Filter by date range
        if self.config.start_date:
            df = df[df.index >= self.config.start_date]
        if self.config.end_date:
            df = df[df.index <= self.config.end_date]
        
        return df
    
    def _run_trading(self, df: pd.DataFrame, 
                     adaptive_mode: Optional[str] = None) -> Tuple:
        """
        Run trading simulation.
        
        Args:
            df: DataFrame with indicators and signals
            adaptive_mode: None, "indicator", "tp", "all"
        
        Returns:
            Tuple of (trades, equity_curve, tp_stats, monthly_stats, param_changes)
        """
        config = self.config
        trades = []
        equity_curve = []
        monthly_stats = {}
        param_changes = []
        tp_stats = TPStats()
        
        capital = config.initial_capital
        leverage = max(1.0, config.leverage)
        use_commission = config.use_commission
        commission_pct = config.commission_percent if use_commission else 0.0
        
        # Active parameters (can change in adaptive mode)
        active_i1 = config.trg_atr_length
        active_i2 = config.trg_multiplier
        active_tp_levels, active_tp_amounts = config.get_active_tp_levels()
        active_sl = config.sl_percent
        
        # Position state
        position = None
        last_exit_reason = None
        last_exit_trend = None
        
        # Adaptive optimization settings
        REOPTIMIZE_EVERY = 20
        LOOKBACK_CANDLES = 500
        last_optimization_trade = 0
        
        for i in range(len(df)):
            row = df.iloc[i]
            timestamp = df.index[i]
            current_trend = int(row.get('trg_trend', 0))
            month_key = timestamp.strftime("%Y-%m")
            
            # Initialize month stats
            if month_key not in monthly_stats:
                monthly_stats[month_key] = MonthlyStats(month=month_key)
            
            # === ADAPTIVE OPTIMIZATION ===
            if adaptive_mode and len(trades) > 0 and len(trades) - last_optimization_trade >= REOPTIMIZE_EVERY:
                if i > LOOKBACK_CANDLES:
                    lookback_df = df.iloc[i - LOOKBACK_CANDLES:i].copy()
                    new_params = self._optimize_on_lookback(
                        lookback_df, adaptive_mode,
                        active_i1, active_i2, active_tp_levels, active_sl
                    )
                    
                    if new_params:
                        if adaptive_mode in ["indicator", "all"]:
                            if new_params.get('i1') != active_i1 or new_params.get('i2') != active_i2:
                                active_i1 = new_params.get('i1', active_i1)
                                active_i2 = new_params.get('i2', active_i2)
                                
                                # Recalculate TRG
                                remaining_df = df.iloc[i:].copy()
                                remaining_df = calculate_trg(remaining_df, active_i1, active_i2)
                                if config.use_supertrend:
                                    remaining_df = calculate_supertrend(
                                        remaining_df, config.supertrend_period, 
                                        config.supertrend_multiplier
                                    )
                                remaining_df = generate_signals(remaining_df, config)
                                
                                for col in remaining_df.columns:
                                    df.loc[remaining_df.index, col] = remaining_df[col]
                        
                        if adaptive_mode in ["tp", "all"]:
                            if new_params.get('tp_levels'):
                                active_tp_levels = new_params['tp_levels']
                        
                        if adaptive_mode == "all":
                            if new_params.get('sl'):
                                active_sl = new_params['sl']
                        
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
            
            # === CHECK POSITION UPDATES (TP/SL) ===
            if position:
                high = row['high']
                low = row['low']
                close = row['close']
                
                # Update trailing prices
                if position['type'] == 'long':
                    position['highest_price'] = max(position['highest_price'], high)
                else:
                    position['lowest_price'] = min(position['lowest_price'], low)
                
                # Check each TP level
                for tp_idx in range(len(position['tp_levels_active'])):
                    if tp_idx in position['tp_closed']:
                        continue
                    
                    tp_price = position['tp_prices'][tp_idx]
                    tp_amount_pct = active_tp_amounts[tp_idx]
                    
                    tp_hit = False
                    if position['type'] == 'long' and high >= tp_price:
                        tp_hit = True
                    elif position['type'] == 'short' and low <= tp_price:
                        tp_hit = True
                    
                    if tp_hit:
                        portion_size = position['entry_capital'] * (tp_amount_pct / 100)
                        portion_pnl_pct = position['tp_levels_active'][tp_idx]
                        portion_pnl_pct_leveraged = portion_pnl_pct * leverage
                        
                        exit_commission = portion_size * (commission_pct / 100) if use_commission else 0
                        portion_pnl = portion_size * (portion_pnl_pct_leveraged / 100) - exit_commission
                        
                        position['commission_paid'] = position.get('commission_paid', 0) + exit_commission
                        position['realized_pnl'] += portion_pnl
                        position['remaining_pct'] -= tp_amount_pct
                        position['tp_closed'].append(tp_idx)
                        position['tp_hit'].append(tp_idx + 1)
                        
                        tp_stats.record_tp_hit(tp_idx + 1)
                        month_stats = monthly_stats[month_key]
                        if tp_idx == 0:
                            month_stats.tp1_hits += 1
                        elif tp_idx == 1:
                            month_stats.tp2_hits += 1
                        elif tp_idx == 2:
                            month_stats.tp3_hits += 1
                        elif tp_idx == 3:
                            month_stats.tp4_hits += 1
                        
                        # Update trailing SL after TP1
                        if tp_idx == 0 and config.sl_trailing_mode in ['breakeven', 'cascade']:
                            position['sl_price'] = position['entry_price']
                        elif tp_idx >= 1 and config.sl_trailing_mode == 'cascade':
                            prev_tp_price = position['tp_prices'][tp_idx - 1]
                            position['sl_price'] = prev_tp_price
                
                # Check SL hit
                sl_hit = False
                all_tp_closed = len(position['tp_closed']) >= len(position['tp_levels_active'])
                
                if position['remaining_pct'] > 0:
                    sl_price = position['sl_price']
                    if position['type'] == 'long' and low <= sl_price:
                        sl_hit = True
                    elif position['type'] == 'short' and high >= sl_price:
                        sl_hit = True
                
                # Check reverse signal
                reverse_signal = False
                signal = row.get('signal', 0)
                if signal != 0 and position['remaining_pct'] > 0:
                    if (position['type'] == 'long' and signal == -1) or \
                       (position['type'] == 'short' and signal == 1):
                        reverse_signal = True
                
                # Close position if needed
                if all_tp_closed or sl_hit or reverse_signal:
                    exit_price = close
                    
                    if sl_hit:
                        exit_price = position['sl_price']
                    
                    # Calculate remaining PnL
                    if position['remaining_pct'] > 0:
                        remaining_size = position['entry_capital'] * (position['remaining_pct'] / 100)
                        
                        if position['type'] == 'long':
                            remaining_pnl_pct = (exit_price / position['entry_price'] - 1) * 100
                        else:
                            remaining_pnl_pct = (1 - exit_price / position['entry_price']) * 100
                        
                        remaining_pnl_pct_leveraged = remaining_pnl_pct * leverage
                        exit_commission = remaining_size * (commission_pct / 100) if use_commission else 0
                        remaining_pnl = remaining_size * (remaining_pnl_pct_leveraged / 100) - exit_commission
                        
                        position['commission_paid'] = position.get('commission_paid', 0) + exit_commission
                        position['realized_pnl'] += remaining_pnl
                    
                    total_pnl = position['realized_pnl']
                    total_pnl_pct = (total_pnl / position['entry_capital']) * 100
                    
                    capital += total_pnl
                    
                    if all_tp_closed:
                        exit_reason = f"TP{len(position['tp_closed'])}"
                    elif sl_hit:
                        exit_reason = "SL"
                        tp_stats.sl_hits += 1
                    else:
                        exit_reason = "Reverse"
                        tp_stats.reverse_exits += 1
                    
                    tp_stats.total_trades += 1
                    month_stats = monthly_stats[month_key]
                    month_stats.trades += 1
                    month_stats.pnl += total_pnl_pct
                    month_stats.pnl_amount += total_pnl
                    
                    if total_pnl > 0:
                        month_stats.wins += 1
                    else:
                        month_stats.losses += 1
                    
                    if position['type'] == 'long':
                        month_stats.long_trades += 1
                    else:
                        month_stats.short_trades += 1
                    
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
                        "commission": round(position.get('commission_paid', 0), 4) if use_commission else 0
                    }
                    trades.append(trade)
                    
                    last_exit_reason = exit_reason
                    last_exit_trend = current_trend
                    position = None
            
            # === CHECK ENTRY ===
            if position is None:
                should_enter = False
                entry_type = None
                is_reentry = False
                
                signal = row.get('signal', 0)
                
                if signal != 0:
                    should_enter = True
                    entry_type = "long" if signal == 1 else "short"
                
                elif config.allow_reentry and last_exit_reason and last_exit_trend:
                    can_reentry = False
                    
                    if last_exit_reason == "SL" and config.reentry_after_sl:
                        if last_exit_trend == current_trend and current_trend != 0:
                            can_reentry = True
                    
                    if last_exit_reason and last_exit_reason.startswith("TP") and config.reentry_after_tp:
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
                    
                    entry_commission = entry_capital * (commission_pct / 100) if use_commission else 0
                    
                    position = {
                        "type": entry_type,
                        "entry_time": timestamp,
                        "entry_price": entry_price,
                        "entry_capital": entry_capital,
                        "remaining_pct": 100.0,
                        "realized_pnl": -entry_commission,
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
                    
                    # Calculate TP/SL prices
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
    
    def _run_quick_trading(self, df: pd.DataFrame, config: BacktestConfig) -> List[Dict]:
        """Run quick trading simulation for optimizer"""
        trades = []
        capital = config.initial_capital
        tp_percents, tp_amounts = config.get_active_tp_levels()
        sl_pct = config.sl_percent
        
        position = None
        
        for i in range(len(df)):
            row = df.iloc[i]
            timestamp = df.index[i]
            
            if position:
                high = row['high']
                low = row['low']
                close = row['close']
                
                # Check TP1 (simplified - just check first TP)
                tp_hit = False
                sl_hit = False
                
                if tp_percents:
                    tp_price = position['tp_prices'][0]
                    if position['type'] == 'long' and high >= tp_price:
                        tp_hit = True
                    elif position['type'] == 'short' and low <= tp_price:
                        tp_hit = True
                
                # Check SL
                sl_price = position['sl_price']
                if position['type'] == 'long' and low <= sl_price:
                    sl_hit = True
                elif position['type'] == 'short' and high >= sl_price:
                    sl_hit = True
                
                # Check reverse
                signal = row.get('signal', 0)
                reverse_signal = False
                if signal != 0:
                    if (position['type'] == 'long' and signal == -1) or \
                       (position['type'] == 'short' and signal == 1):
                        reverse_signal = True
                
                if tp_hit or sl_hit or reverse_signal:
                    if tp_hit:
                        exit_price = position['tp_prices'][0]
                        pnl_pct = tp_percents[0] if position['type'] == 'long' else tp_percents[0]
                    elif sl_hit:
                        exit_price = sl_price
                        if position['type'] == 'long':
                            pnl_pct = (exit_price / position['entry_price'] - 1) * 100
                        else:
                            pnl_pct = (1 - exit_price / position['entry_price']) * 100
                    else:
                        exit_price = close
                        if position['type'] == 'long':
                            pnl_pct = (exit_price / position['entry_price'] - 1) * 100
                        else:
                            pnl_pct = (1 - exit_price / position['entry_price']) * 100
                    
                    trades.append({
                        "id": len(trades) + 1,
                        "type": position['type'],
                        "entry_price": position['entry_price'],
                        "exit_price": exit_price,
                        "pnl": round(pnl_pct, 2),
                        "exit_reason": "TP1" if tp_hit else "SL" if sl_hit else "Reverse"
                    })
                    
                    position = None
            
            # Check entry
            if position is None:
                signal = row.get('signal', 0)
                if signal != 0:
                    entry_price = row['close']
                    entry_type = "long" if signal == 1 else "short"
                    
                    if entry_type == 'long':
                        tp_prices = [entry_price * (1 + tp/100) for tp in tp_percents]
                        sl_price = entry_price * (1 - sl_pct/100)
                    else:
                        tp_prices = [entry_price * (1 - tp/100) for tp in tp_percents]
                        sl_price = entry_price * (1 + sl_pct/100)
                    
                    position = {
                        "type": entry_type,
                        "entry_price": entry_price,
                        "tp_prices": tp_prices,
                        "sl_price": sl_price
                    }
        
        return trades
    
    def _optimize_on_lookback(self, df: pd.DataFrame, mode: str,
                              current_i1: int, current_i2: float,
                              current_tp: List[float], current_sl: float) -> Optional[Dict]:
        """Quick optimization on lookback period"""
        best_score = float('-inf')
        best_params = {}
        
        # Create temp config
        temp_config = BacktestConfig()
        temp_config.__dict__.update(self.config.__dict__)
        
        if mode in ["indicator", "all"]:
            i1_range = [30, 40, 45, 50, 60, 80]
            i2_range = [2, 3, 4, 5, 6]
            
            for i1 in i1_range:
                for i2 in i2_range:
                    try:
                        test_df = df.copy()
                        test_df = calculate_trg(test_df, i1, i2)
                        if self.config.use_supertrend:
                            test_df = calculate_supertrend(
                                test_df, self.config.supertrend_period,
                                self.config.supertrend_multiplier
                            )
                        test_df = generate_signals(test_df, self.config)
                        
                        temp_config.trg_atr_length = i1
                        temp_config.trg_multiplier = i2
                        
                        quick_bt = TRGBacktest(temp_config)
                        trades = quick_bt.run_quick(test_df)
                        
                        if len(trades) >= 3:
                            pnl = sum([t['pnl'] for t in trades])
                            wins = len([t for t in trades if t['pnl'] > 0])
                            wr = wins / len(trades)
                            score = pnl * (0.5 + wr * 0.5)
                            
                            if score > best_score:
                                best_score = score
                                best_params['i1'] = i1
                                best_params['i2'] = i2
                    except Exception:
                        continue
        
        if mode in ["tp", "all"]:
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
                        test_df = generate_signals(test_df, self.config)
                    
                    temp_config.tp_percents = tp_cfg + [0.0] * (10 - len(tp_cfg))
                    temp_config.tp_count = len(tp_cfg)
                    
                    quick_bt = TRGBacktest(temp_config)
                    trades = quick_bt.run_quick(test_df, tp_levels=tp_cfg)
                    
                    if len(trades) >= 3:
                        pnl = sum([t['pnl'] for t in trades])
                        if pnl > best_tp_score:
                            best_tp_score = pnl
                            best_params['tp_levels'] = tp_cfg
                except Exception:
                    continue
        
        if mode == "all":
            sl_range = [3, 4, 5, 6, 8]
            best_sl_score = float('-inf')
            
            for sl in sl_range:
                try:
                    test_df = df.copy()
                    if 'trg_trend' not in test_df.columns:
                        test_df = calculate_trg(test_df, current_i1, current_i2)
                        test_df = generate_signals(test_df, self.config)
                    
                    quick_bt = TRGBacktest(temp_config)
                    trades = quick_bt.run_quick(test_df, sl_pct=sl)
                    
                    if len(trades) >= 3:
                        pnl = sum([t['pnl'] for t in trades])
                        if pnl > best_sl_score:
                            best_sl_score = pnl
                            best_params['sl'] = sl
                except Exception:
                    continue
        
        return best_params if best_params else None
    
    def _calculate_statistics(self, trades: List[Dict], 
                              equity_curve: List[Dict],
                              monthly_stats: Dict[str, MonthlyStats]) -> BacktestResult:
        """Calculate comprehensive statistics"""
        result = BacktestResult()
        result.initial_capital = self.config.initial_capital
        
        if not trades:
            return result
        
        pnls = [t['pnl'] for t in trades]
        pnl_amounts = [t.get('pnl_amount', 0) for t in trades]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p < 0]
        
        result.total_trades = len(trades)
        result.winning_trades = len(wins)
        result.losing_trades = len(losses)
        result.win_rate = (len(wins) / len(trades) * 100) if trades else 0
        result.total_pnl = round(sum(pnls), 2)
        result.avg_win = round(sum(wins) / len(wins), 2) if wins else 0
        result.avg_loss = round(sum(losses) / len(losses), 2) if losses else 0
        result.profit_factor = round(sum(wins) / abs(sum(losses)), 2) if losses and sum(losses) != 0 else 999
        
        # Capital
        if equity_curve:
            result.final_capital = equity_curve[-1]['value']
            result.profit_pct = round((result.final_capital / result.initial_capital - 1) * 100, 2)
        
        # Max drawdown
        if equity_curve:
            peak = result.initial_capital
            max_dd = 0
            for eq in equity_curve:
                if eq['value'] > peak:
                    peak = eq['value']
                dd = (peak - eq['value']) / peak * 100
                if dd > max_dd:
                    max_dd = dd
            result.max_drawdown = round(max_dd, 2)
        
        # Sharpe ratio
        if len(pnls) > 1:
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
                    result.sharpe_ratio = round((avg_return / std_return) * (252 ** 0.5), 2)
        
        # Recovery factor
        total_profit = result.final_capital - result.initial_capital
        if result.max_drawdown > 0:
            result.recovery_factor = round(total_profit / (result.initial_capital * result.max_drawdown / 100), 2)
        
        # Long/Short breakdown
        long_trades = [t for t in trades if t['type'] == 'long']
        short_trades = [t for t in trades if t['type'] == 'short']
        reentry_trades = [t for t in trades if t.get('is_reentry', False)]
        
        result.long_trades = len(long_trades)
        result.long_wins = len([t for t in long_trades if t['pnl'] > 0])
        result.long_win_rate = round(result.long_wins / len(long_trades) * 100, 2) if long_trades else 0
        
        result.short_trades = len(short_trades)
        result.short_wins = len([t for t in short_trades if t['pnl'] > 0])
        result.short_win_rate = round(result.short_wins / len(short_trades) * 100, 2) if short_trades else 0
        
        result.reentry_trades = len(reentry_trades)
        result.reentry_wins = len([t for t in reentry_trades if t['pnl'] > 0])
        result.reentry_win_rate = round(result.reentry_wins / len(reentry_trades) * 100, 2) if reentry_trades else 0
        
        # TP accuracy
        result.accuracy = {}
        for tp_num in range(1, self.config.tp_count + 1):
            tp_hit_trades = [t for t in trades if tp_num in t.get('tp_hit', [])]
            result.accuracy[f"tp{tp_num}"] = round(len(tp_hit_trades) / len(trades) * 100, 2) if trades else 0
        
        # Profit panel
        tp_percents, tp_amounts_list = self.config.get_active_tp_levels()
        
        for tp_num in range(1, self.config.tp_count + 1):
            tp_hit_trades = [t for t in trades if tp_num in t.get('tp_hit', [])]
            tp_missed_trades = [t for t in trades if tp_num not in t.get('tp_hit', [])]
            
            tp_profit = 0
            for t in tp_hit_trades:
                tp_profit += tp_percents[tp_num - 1] * (tp_amounts_list[tp_num - 1] / 100)
            
            tp_loss = 0
            for t in tp_missed_trades:
                if t['pnl'] < 0:
                    tp_loss += t['pnl'] * (tp_amounts_list[tp_num - 1] / 100)
            
            result.profit_panel[f"tp{tp_num}"] = {
                "winning": len(tp_hit_trades),
                "total": len(trades),
                "profit": round(tp_profit, 2),
                "loss": round(tp_loss, 2),
                "final": round(tp_profit + tp_loss, 2)
            }
        
        return result


# ============================================================================
# UI DATA PREPARATION
# ============================================================================

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


def prepare_indicators(df: pd.DataFrame, config: BacktestConfig) -> Dict:
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
    
    # Sort all
    for key in indicators:
        indicators[key].sort(key=lambda x: x['time'])
    
    if config.use_supertrend and 'supertrend' in df.columns:
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
# PARALLEL BACKTEST FUNCTIONS (for optimizer)
# ============================================================================

def run_parallel_backtest(params: Dict) -> Dict:
    """
    Run single backtest for parallel optimization.
    
    Args:
        params: Dict with 'df', 'config', etc.
    
    Returns:
        Dict with score, profit, win_rate, trades count
    """
    try:
        df = params['df'].copy()
        config_dict = params.get('config', {})
        metric = params.get('metric', 'profit')
        
        # Create config
        config = BacktestConfig.from_dict(config_dict)
        
        # Calculate indicators if needed
        if 'trg_trend' not in df.columns:
            df = calculate_trg(df, config.trg_atr_length, config.trg_multiplier)
        
        if config.use_supertrend and 'supertrend' not in df.columns:
            df = calculate_supertrend(df, config.supertrend_period, config.supertrend_multiplier)
        
        if config.use_rsi_filter and 'rsi' not in df.columns:
            df = calculate_rsi(df, config.rsi_period)
        
        if config.use_adx_filter and 'adx' not in df.columns:
            df = calculate_adx(df, config.adx_period)
        
        # Generate signals
        df = generate_signals(df, config)
        
        # Run backtest
        backtest = TRGBacktest(config)
        result = backtest.run(df)
        
        # Calculate score
        score = calculate_score(result, metric)
        
        return {
            "config": config_dict,
            "score": round(score, 2),
            "profit": result.profit_pct,
            "win_rate": result.win_rate,
            "trades": result.total_trades,
            "max_dd": result.max_drawdown,
            "tp1_hit": result.accuracy.get('tp1', 0)
        }
    
    except Exception as e:
        return {
            "config": params.get('config', {}),
            "score": -999,
            "error": str(e)
        }


def calculate_score(result: BacktestResult, metric: str = 'profit') -> float:
    """Calculate optimization score"""
    if result.total_trades < 5:
        return float('-inf')
    
    if metric == 'profit':
        return result.profit_pct
    elif metric == 'winrate':
        return result.win_rate
    elif metric == 'sharpe':
        return result.sharpe_ratio or 0
    elif metric == 'profit_factor':
        return min(result.profit_factor, 100)
    else:
        # Combined score
        score = (
            result.profit_pct * 0.25 +
            result.win_rate * 0.15 +
            min(result.profit_factor, 10) * 2 +
            (100 - result.max_drawdown) * 0.15 +
            result.accuracy.get('tp1', 0) * 0.1
        )
        
        # Penalties
        if result.total_trades < 20:
            score *= 0.7
        if result.max_drawdown > 40:
            score *= 0.7
        
        return score


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Config
    'BacktestConfig',
    
    # Data classes
    'MonthlyStats',
    'TPStats', 
    'BacktestResult',
    
    # Main class
    'TRGBacktest',
    
    # Indicator functions
    'calculate_atr',
    'calculate_trg',
    'calculate_supertrend',
    'calculate_rsi',
    'calculate_adx',
    'generate_signals',
    
    # UI helpers
    'prepare_candles',
    'prepare_indicators',
    'prepare_trade_markers',
    'get_current_signal',
    
    # Parallel
    'run_parallel_backtest',
    'calculate_score',
]
