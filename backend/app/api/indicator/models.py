"""
Indicator API Models
====================
Pydantic models for indicator endpoints.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class IndicatorSettings(BaseModel):
    """Settings for indicator calculation and backtest"""

    # Data
    symbol: str = "BTCUSDT"
    timeframe: str = "1h"
    start_date: Optional[str] = None
    end_date: Optional[str] = None

    # Indicator type selector
    indicator_type: str = "trg"  # "trg" or "dominant"

    # TRG parameters
    trg_atr_length: int = 45
    trg_multiplier: float = 4.0

    # Dominant parameters
    dominant_sensitivity: int = 21
    dominant_filter_type: int = 0  # 0=None, 1=ATR, 2=RSI, 3=ATR+RSI, 4=Volatility
    dominant_sl_mode: int = 0  # 0=Fixed, 1=After TP1, 2=After TP2, 3=After TP3, 4=Cascade
    dominant_fixed_stop: bool = False
    dominant_tp1_percent: float = 1.0
    dominant_tp2_percent: float = 2.0
    dominant_tp3_percent: float = 3.0
    dominant_tp4_percent: float = 5.0
    dominant_tp1_amount: float = 40.0
    dominant_tp2_amount: float = 30.0
    dominant_tp3_amount: float = 20.0
    dominant_tp4_amount: float = 10.0
    dominant_sl_percent: float = 2.0

    # Take Profits (TRG)
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

    # Cache control
    force_recalculate: bool = False


class ReplayRequest(BaseModel):
    """Request for step-by-step replay"""
    settings: IndicatorSettings
    step: int = 0  # 0 = all, >0 = up to candle N


class AutoOptimizeMode(BaseModel):
    """Settings for auto-optimization"""
    settings: IndicatorSettings
    mode: str = "indicator"  # indicator, sl, tp, all, filters, tp_custom
    metric: str = "pnl"  # pnl, sharpe, sortino, winrate
    depth: str = "medium"  # shallow, medium, deep
    use_parallel: bool = True
    max_workers: int = 4

    # Adaptive mode settings
    adaptive_enabled: bool = False
    lookback_months: int = 6
    reoptimize_period: str = "monthly"  # monthly, quarterly


class HeatmapRequest(BaseModel):
    """Request for heatmap generation"""
    settings: IndicatorSettings
    i1_min: int = 10
    i1_max: int = 100
    i1_step: int = 10
    i2_min: float = 1.0
    i2_max: float = 10.0
    i2_step: float = 1.0
