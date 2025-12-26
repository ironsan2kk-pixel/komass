"""
Komas Trading System - TRG Optimizer
=====================================
Multi-core parameter optimization for TRG indicator.

Modes:
- indicator: Optimize TRG parameters (i1, i2)
- tp: Optimize Take Profit levels
- sl: Optimize Stop Loss settings
- filters: Optimize filter parameters
- all: Combined optimization (i1, i2, TP, SL)
- full: Full optimization (all parameters)

Features:
- Parallel processing with ProcessPoolExecutor
- SSE streaming for real-time progress
- Heatmap generation for i1/i2 visualization
- Advanced scoring system with multiple metrics
- Walk-forward validation support

Author: Komas Trading System
Version: 1.0.0
"""

from __future__ import annotations

import os
import time
import json
import numpy as np
import pandas as pd
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import (
    Dict, List, Optional, Any, Callable, 
    Generator, Tuple, Union
)
from concurrent.futures import ProcessPoolExecutor, as_completed
import multiprocessing


# ============================================================
# ENUMS
# ============================================================

class OptimizationMode(Enum):
    """Optimization mode"""
    INDICATOR = "indicator"      # TRG i1, i2 only
    TP = "tp"                    # Take Profit levels
    SL = "sl"                    # Stop Loss settings
    FILTERS = "filters"          # Filter parameters
    ALL = "all"                  # Combined (i1, i2, TP, SL)
    FULL = "full"                # All parameters
    TP_CUSTOM = "tp_custom"      # Custom TP range from current
    ADAPTIVE = "adaptive"        # Walk-forward optimization


class OptimizationMetric(Enum):
    """Optimization metric for scoring"""
    PROFIT = "profit"
    WIN_RATE = "winrate"
    PROFIT_FACTOR = "profit_factor"
    SHARPE = "sharpe"
    ADVANCED = "advanced"        # Combined score


class SearchMethod(Enum):
    """Search method for optimization"""
    GRID = "grid"                # Full grid search
    RANDOM = "random"            # Random sampling


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class ParameterRange:
    """Parameter range for optimization"""
    name: str
    min_value: float
    max_value: float
    step: float
    param_type: str = "float"    # int, float
    
    def get_values(self) -> List[float]:
        """Generate all values in range"""
        values = []
        current = self.min_value
        while current <= self.max_value:
            if self.param_type == "int":
                values.append(int(current))
            else:
                values.append(round(current, 4))
            current += self.step
        return values
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "min": self.min_value,
            "max": self.max_value,
            "step": self.step,
            "type": self.param_type,
            "values_count": len(self.get_values())
        }


@dataclass
class OptimizationResult:
    """Single optimization result"""
    params: Dict[str, Any]
    score: float
    metrics: Dict[str, float] = field(default_factory=dict)
    trades_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "params": self.params,
            "score": round(self.score, 4),
            "metrics": {k: round(v, 4) if isinstance(v, float) else v 
                       for k, v in self.metrics.items()},
            "trades": self.trades_count
        }


@dataclass
class OptimizationProgress:
    """Progress event for SSE streaming"""
    tested: int
    total: int
    progress_pct: float
    current_best: Optional[OptimizationResult] = None
    current_test: Optional[Dict[str, Any]] = None
    eta_seconds: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "tested": self.tested,
            "total": self.total,
            "progress": round(self.progress_pct, 1),
            "best": self.current_best.to_dict() if self.current_best else None,
            "current": self.current_test,
            "eta_seconds": round(self.eta_seconds) if self.eta_seconds else None
        }


@dataclass
class HeatmapCell:
    """Single cell in heatmap"""
    i1: int
    i2: float
    pnl: float
    win_rate: float
    trades: int
    score: float = 0.0


@dataclass
class HeatmapResult:
    """Heatmap generation result"""
    i1_range: List[int]
    i2_range: List[float]
    cells: List[HeatmapCell]
    best_cell: Optional[HeatmapCell] = None
    workers_used: int = 1
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "i1_range": self.i1_range,
            "i2_range": self.i2_range,
            "results": [
                {
                    "i1": c.i1, "i2": c.i2,
                    "pnl": round(c.pnl, 2),
                    "win_rate": round(c.win_rate, 2),
                    "trades": c.trades,
                    "score": round(c.score, 2)
                }
                for c in self.cells
            ],
            "best": {
                "i1": self.best_cell.i1,
                "i2": self.best_cell.i2,
                "pnl": round(self.best_cell.pnl, 2),
                "win_rate": round(self.best_cell.win_rate, 2)
            } if self.best_cell else None,
            "workers_used": self.workers_used,
            "duration_seconds": round(self.duration_seconds, 2)
        }


@dataclass
class TRGOptimizerConfig:
    """Configuration for TRG optimizer"""
    mode: OptimizationMode = OptimizationMode.INDICATOR
    metric: OptimizationMetric = OptimizationMetric.ADVANCED
    method: SearchMethod = SearchMethod.GRID
    
    # Search parameters
    max_tests: int = 5000           # Max combinations to test
    random_samples: int = 500       # For random search
    parallel_workers: int = 0       # 0 = auto (use all cores - 1)
    
    # For tp_custom mode
    tp_range_percent: float = 50.0  # ±50% from current TP values
    tp_step_percent: float = 10.0   # Step 10%
    
    # For full mode
    full_mode_depth: str = "medium"  # fast, medium, deep
    
    # Adaptive optimization
    lookback_months: int = 3
    reoptimize_period: str = "month"  # week, month, quarter
    
    # Minimum requirements
    min_trades: int = 10            # Min trades for valid result
    
    def get_worker_count(self) -> int:
        """Get number of parallel workers to use"""
        if self.parallel_workers > 0:
            return min(self.parallel_workers, multiprocessing.cpu_count())
        return max(1, multiprocessing.cpu_count() - 1)
    
    def to_dict(self) -> Dict:
        return {
            "mode": self.mode.value,
            "metric": self.metric.value,
            "method": self.method.value,
            "max_tests": self.max_tests,
            "workers": self.get_worker_count(),
            "min_trades": self.min_trades,
            "full_mode_depth": self.full_mode_depth
        }


# ============================================================
# SCORING FUNCTIONS
# ============================================================

def calculate_advanced_score(
    trades: List[Dict],
    equity_curve: List[Dict],
    initial_capital: float = 10000.0,
    detailed: bool = False
) -> Tuple[float, Dict[str, Any]]:
    """
    Advanced scoring system for optimization.
    
    Considers:
    - Profit/Loss (weight: 25%)
    - Win rate (weight: 15%)
    - Profit factor (weight: 20%)
    - Max drawdown (weight: 15%)
    - TP1 hit rate (weight: 10%)
    - Sharpe ratio (weight: 10%)
    - Consistency (weight: 5%)
    
    Returns:
        Tuple of (score, metrics_dict)
    """
    if not trades or len(trades) < 5:
        return float('-inf'), {"error": "Not enough trades"}
    
    # Basic metrics
    pnls = [float(t.get('pnl', 0)) for t in trades]
    
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    
    total_trades = len(trades)
    win_count = len(wins)
    loss_count = len(losses)
    
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    
    # Profit metrics
    total_profit = sum(wins) if wins else 0
    total_loss = abs(sum(losses)) if losses else 0
    net_profit_pct = total_profit - total_loss
    
    profit_factor = (total_profit / total_loss) if total_loss > 0 else 999
    profit_factor = min(profit_factor, 100)
    
    avg_win = (sum(wins) / len(wins)) if wins else 0
    avg_loss = (abs(sum(losses)) / len(losses)) if losses else 0
    
    # Risk/Reward ratio
    rr_ratio = (avg_win / avg_loss) if avg_loss > 0 else 999
    rr_ratio = min(rr_ratio, 100)
    
    # TP1 Hit Rate (critical for BE strategy)
    tp1_hits = sum(1 for t in trades if 'exit_reason' in t and 'TP1' in str(t.get('exit_reason', '')))
    tp1_count = sum(1 for t in trades if t.get('pnl', 0) != 0)
    tp1_hit_rate = (tp1_hits / tp1_count * 100) if tp1_count > 0 else 0
    
    # TP2+ hit rate
    tp2_hits = sum(1 for t in trades if 'exit_reason' in t and any(
        f'TP{i}' in str(t.get('exit_reason', '')) for i in range(2, 11)
    ))
    tp2_hit_rate = (tp2_hits / tp1_count * 100) if tp1_count > 0 else 0
    
    # Max Drawdown from equity curve
    max_dd = 0.0
    if equity_curve:
        peak = initial_capital
        for point in equity_curve:
            value = point.get('value', initial_capital)
            if value > peak:
                peak = value
            dd = ((peak - value) / peak * 100) if peak > 0 else 0
            max_dd = max(max_dd, dd)
    
    # Sharpe Ratio approximation
    if len(pnls) > 1:
        returns_std = np.std(pnls)
        returns_mean = np.mean(pnls)
        sharpe = (returns_mean / returns_std) if returns_std > 0 else 0
    else:
        sharpe = 0
    
    # Final capital
    final_capital = equity_curve[-1].get('value', initial_capital) if equity_curve else initial_capital
    capital_gain_pct = ((final_capital / initial_capital) - 1) * 100
    
    # Recovery factor
    recovery_factor = (capital_gain_pct / max_dd) if max_dd > 1 else capital_gain_pct
    recovery_factor = min(recovery_factor, 100)
    
    # Consistency (std of returns)
    consistency = 100 - min(np.std(pnls) * 10, 100) if pnls else 0
    
    # Exit analysis
    sl_exits = sum(1 for t in trades if 'SL' in str(t.get('exit_reason', '')))
    tp_exits = sum(1 for t in trades if 'TP' in str(t.get('exit_reason', '')))
    reverse_exits = sum(1 for t in trades if 'reverse' in str(t.get('exit_reason', '')).lower())
    sl_rate = (sl_exits / total_trades * 100) if total_trades > 0 else 0
    
    # Re-entry performance
    reentry_trades = [t for t in trades if t.get('is_reentry', False)]
    reentry_count = len(reentry_trades)
    reentry_wins = sum(1 for t in reentry_trades if t.get('pnl', 0) > 0)
    reentry_win_rate = (reentry_wins / reentry_count * 100) if reentry_count > 0 else 0
    reentry_profit = sum(t.get('pnl', 0) for t in reentry_trades)
    
    # Long/Short breakdown
    long_trades = [t for t in trades if t.get('type', '').upper() == 'LONG']
    short_trades = [t for t in trades if t.get('type', '').upper() == 'SHORT']
    long_wins = sum(1 for t in long_trades if t.get('pnl', 0) > 0)
    short_wins = sum(1 for t in short_trades if t.get('pnl', 0) > 0)
    long_win_rate = (long_wins / len(long_trades) * 100) if long_trades else 0
    short_win_rate = (short_wins / len(short_trades) * 100) if short_trades else 0
    
    # ==================== SCORING ====================
    
    # Normalize components to 0-100 scale
    profit_score = min(max(capital_gain_pct, -100), 500) / 5 + 20  # -100% to +500% → 0-120
    win_rate_score = win_rate  # 0-100%
    tp1_score = tp1_hit_rate  # 0-100%
    dd_score = max(0, 100 - max_dd * 2)  # Lower is better
    pf_score = min(profit_factor * 20, 100)  # 0-5 → 0-100
    sharpe_score = min(max(sharpe * 25 + 50, 0), 100)  # -2 to +2 → 0-100
    recovery_score = min(max(recovery_factor + 50, 0), 100)
    consistency_score = consistency
    reentry_score = reentry_win_rate if reentry_count > 5 else 50  # Neutral if few re-entries
    
    # Weights (total = 100%)
    weights = {
        "profit": 0.25,
        "win_rate": 0.15,
        "profit_factor": 0.20,
        "drawdown": 0.15,
        "tp1_hit": 0.10,
        "sharpe": 0.10,
        "consistency": 0.05
    }
    
    # Calculate final score
    final_score = (
        weights["profit"] * profit_score +
        weights["win_rate"] * win_rate_score +
        weights["profit_factor"] * pf_score +
        weights["drawdown"] * dd_score +
        weights["tp1_hit"] * tp1_score +
        weights["sharpe"] * sharpe_score +
        weights["consistency"] * consistency_score
    )
    
    # Penalties
    if total_trades < 10:
        final_score *= 0.5  # Penalty for too few trades
    if max_dd > 50:
        final_score *= 0.7  # Penalty for excessive drawdown
    if win_rate < 30:
        final_score *= 0.8  # Penalty for very low win rate
    
    # Bonuses
    if profit_factor > 2 and win_rate > 50:
        final_score *= 1.1  # Bonus for strong performance
    if tp1_hit_rate > 70 and max_dd < 20:
        final_score *= 1.05  # Bonus for consistent TP1 hits
    
    # Build metrics dict
    metrics = {
        # Core
        "total_trades": total_trades,
        "win_rate": round(win_rate, 2),
        "profit_pct": round(capital_gain_pct, 2),
        "profit_factor": round(min(profit_factor, 99.99), 2),
        
        # Risk
        "max_drawdown": round(max_dd, 2),
        "sharpe": round(sharpe, 2),
        "recovery_factor": round(recovery_factor, 2),
        
        # TP analysis
        "tp1_hit_rate": round(tp1_hit_rate, 2),
        "tp2_hit_rate": round(tp2_hit_rate, 2),
        
        # Trade breakdown
        "avg_win": round(avg_win, 2),
        "avg_loss": round(avg_loss, 2),
        "rr_ratio": round(min(rr_ratio, 99.99), 2),
        
        # Exit analysis
        "sl_exits": sl_exits,
        "tp_exits": tp_exits,
        "reverse_exits": reverse_exits,
        "sl_rate": round(sl_rate, 2),
        
        # Re-entry
        "reentry_count": reentry_count,
        "reentry_win_rate": round(reentry_win_rate, 2),
        "reentry_profit": round(reentry_profit, 2),
        
        # Long/Short
        "long_trades": len(long_trades),
        "short_trades": len(short_trades),
        "long_win_rate": round(long_win_rate, 2),
        "short_win_rate": round(short_win_rate, 2),
        
        # Capital
        "final_capital": round(final_capital, 2),
    }
    
    if detailed:
        metrics["score_breakdown"] = {
            "profit_score": round(profit_score, 2),
            "win_rate_score": round(win_rate_score, 2),
            "tp1_score": round(tp1_score, 2),
            "dd_score": round(dd_score, 2),
            "pf_score": round(pf_score, 2),
            "sharpe_score": round(sharpe_score, 2),
            "consistency_score": round(consistency_score, 2),
        }
    
    return round(final_score, 2), metrics


def calculate_simple_score(
    trades: List[Dict],
    equity_curve: List[Dict],
    metric: OptimizationMetric,
    initial_capital: float = 10000.0
) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate score based on single metric.
    """
    if not trades or len(trades) < 5:
        return float('-inf'), {"error": "Not enough trades"}
    
    pnls = [float(t.get('pnl', 0)) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    
    total_profit = sum(wins) if wins else 0
    total_loss = abs(sum(losses)) if losses else 0
    
    win_rate = (len(wins) / len(trades) * 100) if trades else 0
    profit_factor = (total_profit / total_loss) if total_loss > 0 else 999
    
    final_capital = equity_curve[-1].get('value', initial_capital) if equity_curve else initial_capital
    capital_gain_pct = ((final_capital / initial_capital) - 1) * 100
    
    # Sharpe
    sharpe = 0
    if len(pnls) > 1:
        returns_std = np.std(pnls)
        returns_mean = np.mean(pnls)
        sharpe = (returns_mean / returns_std) if returns_std > 0 else 0
    
    metrics = {
        "total_trades": len(trades),
        "win_rate": round(win_rate, 2),
        "profit_pct": round(capital_gain_pct, 2),
        "profit_factor": round(min(profit_factor, 99.99), 2),
    }
    
    if metric == OptimizationMetric.PROFIT:
        score = capital_gain_pct
    elif metric == OptimizationMetric.WIN_RATE:
        score = win_rate
    elif metric == OptimizationMetric.PROFIT_FACTOR:
        score = min(profit_factor, 100)
    elif metric == OptimizationMetric.SHARPE:
        score = sharpe * 100
    else:
        # ADVANCED
        score, metrics = calculate_advanced_score(trades, equity_curve, initial_capital)
    
    return round(score, 2), metrics


# ============================================================
# PARAMETER PRESETS
# ============================================================

class TRGParameterPresets:
    """Predefined parameter ranges for TRG optimization"""
    
    # TRG Indicator - from Pine Script sensitivity presets
    I1_FULL = [20, 25, 30, 35, 40, 45, 50, 55, 60, 70, 80, 100, 120, 150]
    I1_FAST = [30, 40, 45, 50, 60, 80]
    I1_DEEP = [20, 25, 30, 35, 40, 45, 50, 55, 60, 62, 68, 70, 74, 78, 80, 
               95, 115, 140, 155, 170, 185, 200]
    
    I2_FULL = [1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 7, 8, 10]
    I2_FAST = [2, 3, 4, 5, 6]
    I2_DEEP = [1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5, 5.5, 6, 7, 8, 9, 10, 12]
    
    # Take Profit presets
    TP_CONFIGS = [
        {"tp1": 0.5, "tp2": 1.0, "tp3": 1.5, "tp4": 2.0, "a1": 40, "a2": 30, "a3": 20, "a4": 10},
        {"tp1": 0.75, "tp2": 1.25, "tp3": 2.0, "tp4": 3.0, "a1": 50, "a2": 25, "a3": 15, "a4": 10},
        {"tp1": 1.0, "tp2": 1.5, "tp3": 2.5, "tp4": 4.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
        {"tp1": 1.0, "tp2": 2.0, "tp3": 3.5, "tp4": 5.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},
        {"tp1": 1.05, "tp2": 1.95, "tp3": 3.75, "tp4": 6.0, "a1": 50, "a2": 30, "a3": 15, "a4": 5},  # Default
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
    
    # Stop Loss presets
    SL_PERCENTS = [2, 3, 4, 5, 6, 7, 8, 10, 12, 15]
    SL_MODES = ["fixed", "breakeven", "cascade"]  # no, breakeven, moving in legacy
    
    # SuperTrend filter
    ST_PERIODS = [7, 10, 12, 14, 17, 20]
    ST_MULTIPLIERS = [1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
    
    # RSI filter
    RSI_PERIODS = [7, 10, 14, 21]
    RSI_OVERBOUGHT = [65, 70, 75, 80]
    RSI_OVERSOLD = [20, 25, 30, 35]
    
    # ADX filter
    ADX_PERIODS = [10, 14, 20]
    ADX_THRESHOLDS = [20, 25, 30, 35]
    
    # Volume filter
    VOL_MA_PERIODS = [10, 20, 30]
    VOL_THRESHOLDS = [1.0, 1.2, 1.5, 2.0]
    
    @classmethod
    def get_filter_configs(cls, depth: str = "medium") -> List[Dict]:
        """Generate filter configurations for optimization"""
        configs = []
        
        # No filters baseline
        configs.append({
            "use_supertrend": False,
            "use_rsi": False,
            "use_adx": False,
            "use_volume": False
        })
        
        if depth == "fast":
            # Quick scan - 5 configs
            configs.extend([
                {"use_supertrend": True, "st_period": 10, "st_mult": 3.0,
                 "use_rsi": False, "use_adx": False, "use_volume": False},
                {"use_supertrend": False, "use_rsi": True, "rsi_period": 14,
                 "rsi_ob": 70, "rsi_os": 30, "use_adx": False, "use_volume": False},
                {"use_supertrend": False, "use_rsi": False,
                 "use_adx": True, "adx_period": 14, "adx_thresh": 25, "use_volume": False},
            ])
        
        elif depth == "medium":
            # Balanced - 15 configs
            for st_p in [10, 14]:
                for st_m in [2.5, 3.0]:
                    configs.append({
                        "use_supertrend": True, "st_period": st_p, "st_mult": st_m,
                        "use_rsi": False, "use_adx": False, "use_volume": False
                    })
            
            for rsi_p in [14]:
                configs.append({
                    "use_supertrend": False, "use_rsi": True, "rsi_period": rsi_p,
                    "rsi_ob": 70, "rsi_os": 30, "use_adx": False, "use_volume": False
                })
            
            for adx_t in [25, 30]:
                configs.append({
                    "use_supertrend": False, "use_rsi": False,
                    "use_adx": True, "adx_period": 14, "adx_thresh": adx_t, "use_volume": False
                })
            
            # Combined
            configs.extend([
                {"use_supertrend": True, "st_period": 10, "st_mult": 3.0,
                 "use_rsi": True, "rsi_period": 14, "rsi_ob": 70, "rsi_os": 30,
                 "use_adx": False, "use_volume": False},
                {"use_supertrend": True, "st_period": 10, "st_mult": 3.0,
                 "use_rsi": False, "use_adx": True, "adx_period": 14, "adx_thresh": 25,
                 "use_volume": False},
            ])
        
        else:  # deep
            # Thorough - 45+ configs
            for st_p in cls.ST_PERIODS:
                for st_m in cls.ST_MULTIPLIERS:
                    configs.append({
                        "use_supertrend": True, "st_period": st_p, "st_mult": st_m,
                        "use_rsi": False, "use_adx": False, "use_volume": False
                    })
            
            for rsi_p in cls.RSI_PERIODS:
                for rsi_ob in cls.RSI_OVERBOUGHT[:2]:
                    configs.append({
                        "use_supertrend": False, "use_rsi": True, "rsi_period": rsi_p,
                        "rsi_ob": rsi_ob, "rsi_os": 100 - rsi_ob, "use_adx": False, "use_volume": False
                    })
            
            for adx_p in cls.ADX_PERIODS:
                for adx_t in cls.ADX_THRESHOLDS:
                    configs.append({
                        "use_supertrend": False, "use_rsi": False,
                        "use_adx": True, "adx_period": adx_p, "adx_thresh": adx_t, "use_volume": False
                    })
        
        return configs


# ============================================================
# TRG OPTIMIZER CLASS
# ============================================================

class TRGOptimizer:
    """
    Multi-core optimizer for TRG indicator.
    
    Supports multiple optimization modes:
    - indicator: Optimize TRG parameters (i1, i2)
    - tp: Optimize Take Profit levels
    - sl: Optimize Stop Loss settings
    - filters: Optimize filter parameters
    - all: Combined optimization
    - full: Full parameter optimization
    
    Usage:
        optimizer = TRGOptimizer(TRGOptimizerConfig(
            mode=OptimizationMode.INDICATOR,
            metric=OptimizationMetric.ADVANCED
        ))
        
        # With backtest function
        result = optimizer.optimize(df, settings, backtest_fn)
        
        # SSE streaming
        for event in optimizer.optimize_stream(df, settings, backtest_fn):
            yield f"data: {json.dumps(event)}\\n\\n"
        
        # Heatmap
        heatmap = optimizer.generate_heatmap(df, settings, backtest_fn)
    """
    
    def __init__(self, config: Optional[TRGOptimizerConfig] = None):
        self.config = config or TRGOptimizerConfig()
        
        # State
        self.results: List[OptimizationResult] = []
        self.best_result: Optional[OptimizationResult] = None
        self._start_time: Optional[datetime] = None
        self._tested_count: int = 0
        self._total_count: int = 0
    
    # ==================== PARAMETER GENERATION ====================
    
    def get_parameter_ranges(
        self,
        mode: OptimizationMode,
        current_settings: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate parameter combinations for given mode.
        
        Args:
            mode: Optimization mode
            current_settings: Current settings for tp_custom mode
            
        Returns:
            List of parameter dictionaries
        """
        presets = TRGParameterPresets
        depth = self.config.full_mode_depth
        
        if mode == OptimizationMode.INDICATOR:
            # i1/i2 grid
            i1_range = presets.I1_FAST if depth == "fast" else (
                presets.I1_DEEP if depth == "deep" else presets.I1_FULL
            )
            i2_range = presets.I2_FAST if depth == "fast" else (
                presets.I2_DEEP if depth == "deep" else presets.I2_FULL
            )
            
            return [
                {"i1": i1, "i2": i2}
                for i1 in i1_range
                for i2 in i2_range
            ]
        
        elif mode == OptimizationMode.TP:
            return [{"tp_config": cfg} for cfg in presets.TP_CONFIGS]
        
        elif mode == OptimizationMode.SL:
            return [
                {"sl_percent": sl, "sl_mode": mode}
                for sl in presets.SL_PERCENTS
                for mode in presets.SL_MODES
            ]
        
        elif mode == OptimizationMode.FILTERS:
            return presets.get_filter_configs(depth)
        
        elif mode == OptimizationMode.ALL:
            # Combined: i1, i2, TP, SL
            i1_range = presets.I1_FAST
            i2_range = presets.I2_FAST
            tp_configs = presets.TP_CONFIGS[:6]  # First 6
            sl_configs = [
                {"sl_percent": 4, "sl_mode": "breakeven"},
                {"sl_percent": 6, "sl_mode": "breakeven"},
                {"sl_percent": 8, "sl_mode": "cascade"},
            ]
            
            return [
                {
                    "i1": i1, "i2": i2,
                    "tp_config": tp,
                    "sl_percent": sl["sl_percent"],
                    "sl_mode": sl["sl_mode"]
                }
                for i1 in i1_range
                for i2 in i2_range
                for tp in tp_configs
                for sl in sl_configs
            ]
        
        elif mode == OptimizationMode.FULL:
            return self._generate_full_configs(depth, current_settings)
        
        elif mode == OptimizationMode.TP_CUSTOM:
            return self._generate_tp_custom_configs(current_settings)
        
        else:
            return []
    
    def _generate_full_configs(
        self,
        depth: str,
        current_settings: Optional[Dict] = None
    ) -> List[Dict]:
        """Generate full optimization configurations"""
        presets = TRGParameterPresets
        configs = []
        
        # Depth-based ranges
        if depth == "fast":
            i1_range = [35, 45, 60]
            i2_range = [3, 4, 5]
            tp1_range = [0.8, 1.0, 1.5]
            sl_range = [4, 6, 8]
            sl_modes = ["breakeven", "cascade"]
            filter_presets = presets.get_filter_configs("fast")[:3]
            reentry_presets = [{"allow_reentry": True, "reentry_sl": True, "reentry_tp": False}]
            
        elif depth == "medium":
            i1_range = [30, 40, 45, 50, 60, 80]
            i2_range = [2, 3, 4, 5, 6]
            tp1_range = [0.6, 0.8, 1.0, 1.2, 1.5]
            sl_range = [3, 4, 5, 6, 8, 10]
            sl_modes = ["fixed", "breakeven", "cascade"]
            filter_presets = presets.get_filter_configs("medium")[:6]
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
            sl_modes = ["fixed", "breakeven", "cascade"]
            filter_presets = presets.get_filter_configs("deep")[:10]
            reentry_presets = [
                {"allow_reentry": False, "reentry_sl": False, "reentry_tp": False},
                {"allow_reentry": True, "reentry_sl": True, "reentry_tp": False},
                {"allow_reentry": True, "reentry_sl": False, "reentry_tp": True},
                {"allow_reentry": True, "reentry_sl": True, "reentry_tp": True},
            ]
        
        # Build combinations (limiting total)
        max_configs = {
            "fast": 200,
            "medium": 1000,
            "deep": 5000
        }
        
        count = 0
        for i1 in i1_range:
            for i2 in i2_range:
                for tp1 in tp1_range:
                    for sl in sl_range:
                        for sl_m in sl_modes:
                            for filters in filter_presets:
                                for reentry in reentry_presets:
                                    cfg = {
                                        "i1": i1,
                                        "i2": i2,
                                        "tp1": tp1,
                                        "tp2": tp1 * 2,
                                        "tp3": tp1 * 3.5,
                                        "tp4": tp1 * 5,
                                        "sl_percent": sl,
                                        "sl_mode": sl_m,
                                        **filters,
                                        **reentry
                                    }
                                    configs.append(cfg)
                                    count += 1
                                    
                                    if count >= max_configs[depth]:
                                        return configs
        
        return configs
    
    def _generate_tp_custom_configs(
        self,
        current_settings: Optional[Dict] = None
    ) -> List[Dict]:
        """Generate custom TP configurations based on current settings"""
        if not current_settings:
            return TRGParameterPresets.TP_CONFIGS
        
        configs = []
        range_pct = self.config.tp_range_percent / 100
        step_pct = self.config.tp_step_percent / 100
        
        # Get current TP values
        base_tp1 = current_settings.get("tp1_percent", 1.0)
        base_tp2 = current_settings.get("tp2_percent", 2.0)
        base_tp3 = current_settings.get("tp3_percent", 3.5)
        base_tp4 = current_settings.get("tp4_percent", 5.0)
        
        # Generate range
        multipliers = []
        m = 1 - range_pct
        while m <= 1 + range_pct:
            multipliers.append(round(m, 2))
            m += step_pct
        
        for m in multipliers:
            configs.append({
                "tp1": round(base_tp1 * m, 2),
                "tp2": round(base_tp2 * m, 2),
                "tp3": round(base_tp3 * m, 2),
                "tp4": round(base_tp4 * m, 2),
                "a1": current_settings.get("tp1_amount", 50),
                "a2": current_settings.get("tp2_amount", 30),
                "a3": current_settings.get("tp3_amount", 15),
                "a4": current_settings.get("tp4_amount", 5),
            })
        
        return [{"tp_config": cfg} for cfg in configs]
    
    # ==================== OPTIMIZATION ====================
    
    def optimize(
        self,
        df: pd.DataFrame,
        settings: Dict[str, Any],
        backtest_fn: Callable[[pd.DataFrame, Dict], Tuple[List, List]],
        progress_callback: Optional[Callable[[OptimizationProgress], None]] = None
    ) -> OptimizationResult:
        """
        Run optimization with parallel processing.
        
        Args:
            df: Price data DataFrame
            settings: Current indicator settings
            backtest_fn: Function(df, params) -> (trades, equity_curve)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Best optimization result
        """
        self._start_time = datetime.now()
        self.results = []
        self.best_result = None
        
        # Generate parameter combinations
        param_list = self.get_parameter_ranges(self.config.mode, settings)
        
        # Apply max_tests limit
        if len(param_list) > self.config.max_tests:
            if self.config.method == SearchMethod.RANDOM:
                np.random.shuffle(param_list)
            param_list = param_list[:self.config.max_tests]
        
        self._total_count = len(param_list)
        self._tested_count = 0
        
        num_workers = self.config.get_worker_count()
        
        # Prepare tasks for parallel execution
        # Note: We need to pass serializable data to workers
        tasks = []
        for params in param_list:
            merged_settings = {**settings, **params}
            tasks.append({
                "df_dict": df.to_dict(orient='split'),
                "params": merged_settings,
                "metric": self.config.metric.value
            })
        
        # Run parallel optimization
        results = []
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(_run_single_backtest, task, backtest_fn): task
                for task in tasks
            }
            
            for future in as_completed(futures):
                self._tested_count += 1
                
                try:
                    result = future.result()
                    if result and result.score > float('-inf'):
                        results.append(result)
                        
                        if self.best_result is None or result.score > self.best_result.score:
                            self.best_result = result
                except Exception as e:
                    pass  # Skip failed tests
                
                # Progress callback
                if progress_callback:
                    progress = self._create_progress()
                    progress_callback(progress)
        
        self.results = sorted(results, key=lambda x: x.score, reverse=True)
        
        return self.best_result or OptimizationResult(
            params={},
            score=float('-inf'),
            metrics={"error": "No valid results"}
        )
    
    def optimize_stream(
        self,
        df: pd.DataFrame,
        settings: Dict[str, Any],
        backtest_fn: Callable[[pd.DataFrame, Dict], Tuple[List, List]]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Run optimization with SSE streaming progress.
        
        Yields events:
        - start: {total, workers, mode, metric}
        - current: {profit, win_rate, trades} (current settings performance)
        - test: {tested, total, progress, best, current, eta_seconds}
        - complete: {best, total_tested, duration_seconds}
        - error: {message}
        
        Usage:
            for event in optimizer.optimize_stream(df, settings, backtest_fn):
                yield f"data: {json.dumps(event)}\\n\\n"
        """
        self._start_time = datetime.now()
        self.results = []
        self.best_result = None
        
        # First, calculate current performance
        try:
            current_trades, current_equity = backtest_fn(df, settings)
            current_score, current_metrics = calculate_advanced_score(
                current_trades, current_equity, settings.get("initial_capital", 10000)
            )
            
            yield {
                "type": "current",
                "profit": current_metrics.get("profit_pct", 0),
                "win_rate": current_metrics.get("win_rate", 0),
                "trades": current_metrics.get("total_trades", 0)
            }
        except Exception as e:
            yield {"type": "error", "message": f"Failed to calculate current: {str(e)}"}
        
        # Generate parameter combinations
        param_list = self.get_parameter_ranges(self.config.mode, settings)
        
        if len(param_list) > self.config.max_tests:
            if self.config.method == SearchMethod.RANDOM:
                np.random.shuffle(param_list)
            param_list = param_list[:self.config.max_tests]
        
        self._total_count = len(param_list)
        self._tested_count = 0
        
        num_workers = self.config.get_worker_count()
        
        # Start event
        yield {
            "type": "start",
            "total": self._total_count,
            "workers": num_workers,
            "mode": self.config.mode.value,
            "metric": self.config.metric.value
        }
        
        # Run optimization
        for params in param_list:
            merged_settings = {**settings, **params}
            
            try:
                trades, equity = backtest_fn(df, merged_settings)
                
                if self.config.metric == OptimizationMetric.ADVANCED:
                    score, metrics = calculate_advanced_score(
                        trades, equity, settings.get("initial_capital", 10000)
                    )
                else:
                    score, metrics = calculate_simple_score(
                        trades, equity, self.config.metric, 
                        settings.get("initial_capital", 10000)
                    )
                
                result = OptimizationResult(
                    params=params,
                    score=score,
                    metrics=metrics,
                    trades_count=len(trades)
                )
                
                self.results.append(result)
                
                is_best = False
                if self.best_result is None or score > self.best_result.score:
                    self.best_result = result
                    is_best = True
                
            except Exception as e:
                result = OptimizationResult(
                    params=params,
                    score=float('-inf'),
                    metrics={"error": str(e)}
                )
            
            self._tested_count += 1
            
            # Progress event (every test or every 10 for large runs)
            if self._total_count < 100 or self._tested_count % 10 == 0 or is_best:
                yield {
                    "type": "test",
                    **self._create_progress().to_dict(),
                    "is_new_best": is_best
                }
        
        # Sort results
        self.results.sort(key=lambda x: x.score, reverse=True)
        
        # Complete event
        duration = (datetime.now() - self._start_time).total_seconds()
        
        yield {
            "type": "complete",
            "best": self.best_result.to_dict() if self.best_result else None,
            "total_tested": len(self.results),
            "duration_seconds": round(duration, 2),
            "top_10": [r.to_dict() for r in self.results[:10]]
        }
    
    # ==================== HEATMAP ====================
    
    def generate_heatmap(
        self,
        df: pd.DataFrame,
        settings: Dict[str, Any],
        backtest_fn: Callable[[pd.DataFrame, Dict], Tuple[List, List]],
        i1_range: Optional[List[int]] = None,
        i2_range: Optional[List[float]] = None
    ) -> HeatmapResult:
        """
        Generate heatmap for i1/i2 parameters.
        
        Args:
            df: Price data
            settings: Current settings
            backtest_fn: Backtest function
            i1_range: Custom i1 range (optional)
            i2_range: Custom i2 range (optional)
            
        Returns:
            HeatmapResult with all cells and best cell
        """
        start_time = time.time()
        
        # Default ranges
        if i1_range is None:
            i1_range = [20, 30, 40, 45, 50, 60, 70, 80, 100]
        if i2_range is None:
            i2_range = [2, 3, 4, 5, 6, 7, 8, 10]
        
        num_workers = self.config.get_worker_count()
        
        # Build parameter grid
        param_list = [
            {"i1": i1, "i2": i2}
            for i1 in i1_range
            for i2 in i2_range
        ]
        
        # Run parallel tests
        cells = []
        best_cell = None
        
        for params in param_list:
            merged_settings = {**settings, "trg_atr_length": params["i1"], "trg_multiplier": params["i2"]}
            
            try:
                trades, equity = backtest_fn(df, merged_settings)
                
                score, metrics = calculate_advanced_score(
                    trades, equity, settings.get("initial_capital", 10000)
                )
                
                cell = HeatmapCell(
                    i1=params["i1"],
                    i2=params["i2"],
                    pnl=metrics.get("profit_pct", 0),
                    win_rate=metrics.get("win_rate", 0),
                    trades=metrics.get("total_trades", 0),
                    score=score
                )
                cells.append(cell)
                
                if best_cell is None or cell.score > best_cell.score:
                    best_cell = cell
                    
            except Exception as e:
                cells.append(HeatmapCell(
                    i1=params["i1"],
                    i2=params["i2"],
                    pnl=0, win_rate=0, trades=0, score=float('-inf')
                ))
        
        duration = time.time() - start_time
        
        return HeatmapResult(
            i1_range=i1_range,
            i2_range=i2_range,
            cells=cells,
            best_cell=best_cell,
            workers_used=num_workers,
            duration_seconds=duration
        )
    
    def generate_heatmap_parallel(
        self,
        df: pd.DataFrame,
        settings: Dict[str, Any],
        backtest_fn: Callable,
        i1_range: Optional[List[int]] = None,
        i2_range: Optional[List[float]] = None
    ) -> HeatmapResult:
        """
        Generate heatmap with parallel processing.
        
        Uses ProcessPoolExecutor for faster generation.
        """
        start_time = time.time()
        
        if i1_range is None:
            i1_range = [20, 30, 40, 45, 50, 60, 70, 80, 100]
        if i2_range is None:
            i2_range = [2, 3, 4, 5, 6, 7, 8, 10]
        
        num_workers = self.config.get_worker_count()
        
        # Prepare tasks
        param_list = [
            {"df": df, "settings": {**settings, "trg_atr_length": i1, "trg_multiplier": i2},
             "i1": i1, "i2": i2}
            for i1 in i1_range
            for i2 in i2_range
        ]
        
        cells = []
        best_cell = None
        
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(_run_heatmap_cell, p, backtest_fn): p
                for p in param_list
            }
            
            for future in as_completed(futures):
                params = futures[future]
                try:
                    result = future.result()
                    cell = HeatmapCell(
                        i1=params["i1"],
                        i2=params["i2"],
                        pnl=result.get("pnl", 0),
                        win_rate=result.get("win_rate", 0),
                        trades=result.get("trades", 0),
                        score=result.get("score", 0)
                    )
                    cells.append(cell)
                    
                    if best_cell is None or cell.score > best_cell.score:
                        best_cell = cell
                except:
                    cells.append(HeatmapCell(
                        i1=params["i1"], i2=params["i2"],
                        pnl=0, win_rate=0, trades=0, score=float('-inf')
                    ))
        
        duration = time.time() - start_time
        
        return HeatmapResult(
            i1_range=i1_range,
            i2_range=i2_range,
            cells=cells,
            best_cell=best_cell,
            workers_used=num_workers,
            duration_seconds=duration
        )
    
    # ==================== HELPER METHODS ====================
    
    def _create_progress(self) -> OptimizationProgress:
        """Create progress object for current state"""
        progress_pct = (self._tested_count / self._total_count * 100) if self._total_count > 0 else 0
        
        # ETA calculation
        eta = None
        if self._start_time and self._tested_count > 0:
            elapsed = (datetime.now() - self._start_time).total_seconds()
            rate = self._tested_count / elapsed if elapsed > 0 else 0
            remaining = self._total_count - self._tested_count
            eta = remaining / rate if rate > 0 else None
        
        return OptimizationProgress(
            tested=self._tested_count,
            total=self._total_count,
            progress_pct=progress_pct,
            current_best=self.best_result,
            eta_seconds=eta
        )
    
    def get_top_results(self, n: int = 10) -> List[OptimizationResult]:
        """Get top N results sorted by score"""
        return sorted(self.results, key=lambda x: x.score, reverse=True)[:n]
    
    def export_results_to_df(self) -> pd.DataFrame:
        """Export all results to DataFrame"""
        if not self.results:
            return pd.DataFrame()
        
        rows = []
        for r in self.results:
            row = {**r.params, "score": r.score, "trades": r.trades_count}
            row.update(r.metrics)
            rows.append(row)
        
        return pd.DataFrame(rows)


# ============================================================
# WORKER FUNCTIONS (for multiprocessing)
# ============================================================

def _run_single_backtest(
    task: Dict[str, Any],
    backtest_fn: Callable
) -> Optional[OptimizationResult]:
    """
    Worker function for parallel optimization.
    
    Note: This function must be at module level for pickling.
    """
    try:
        # Reconstruct DataFrame
        df = pd.DataFrame(**task["df_dict"])
        params = task["params"]
        metric = OptimizationMetric(task["metric"])
        
        # Run backtest
        trades, equity = backtest_fn(df, params)
        
        # Calculate score
        if metric == OptimizationMetric.ADVANCED:
            score, metrics = calculate_advanced_score(
                trades, equity, params.get("initial_capital", 10000)
            )
        else:
            score, metrics = calculate_simple_score(
                trades, equity, metric, params.get("initial_capital", 10000)
            )
        
        return OptimizationResult(
            params=params,
            score=score,
            metrics=metrics,
            trades_count=len(trades)
        )
    except Exception as e:
        return None


def _run_heatmap_cell(
    params: Dict[str, Any],
    backtest_fn: Callable
) -> Dict[str, float]:
    """Worker function for heatmap cell calculation"""
    try:
        df = params["df"]
        settings = params["settings"]
        
        trades, equity = backtest_fn(df, settings)
        
        score, metrics = calculate_advanced_score(
            trades, equity, settings.get("initial_capital", 10000)
        )
        
        return {
            "pnl": metrics.get("profit_pct", 0),
            "win_rate": metrics.get("win_rate", 0),
            "trades": metrics.get("total_trades", 0),
            "score": score
        }
    except:
        return {"pnl": 0, "win_rate": 0, "trades": 0, "score": float('-inf')}


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Enums
    "OptimizationMode",
    "OptimizationMetric",
    "SearchMethod",
    
    # Data classes
    "ParameterRange",
    "OptimizationResult",
    "OptimizationProgress",
    "HeatmapCell",
    "HeatmapResult",
    "TRGOptimizerConfig",
    
    # Main class
    "TRGOptimizer",
    
    # Presets
    "TRGParameterPresets",
    
    # Functions
    "calculate_advanced_score",
    "calculate_simple_score",
]
