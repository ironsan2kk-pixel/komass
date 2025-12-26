"""
TRG Indicator Plugin
====================
Trend Reversal Gauge - ATR-based trend following indicator.

Components:
- TRGIndicator: Main indicator calculation
- TRGSignalGenerator: Signal generation
- TRGTradingSystem: Position management, TP/SL
- TRGFilterManager: SuperTrend, RSI, ADX, Volume filters
- TRGOptimizer: Multi-core parameter optimization
- TRGBacktest: Complete backtesting engine

Version: 1.4.0
Author: Komas Trading System
"""

# Import backtest components
from .backtest import (
    # Config
    BacktestConfig,
    
    # Data classes
    MonthlyStats,
    TPStats,
    BacktestResult,
    
    # Main class
    TRGBacktest,
    
    # Indicator functions
    calculate_atr,
    calculate_trg,
    calculate_supertrend,
    calculate_rsi,
    calculate_adx,
    generate_signals,
    
    # UI helpers
    prepare_candles,
    prepare_indicators,
    prepare_trade_markers,
    get_current_signal,
    
    # Parallel
    run_parallel_backtest,
    calculate_score,
)

# Try to import other components (may not be present in test environment)
try:
    from .indicator import TRGIndicator
except ImportError:
    TRGIndicator = None

try:
    from .signals import TRGSignalGenerator
except ImportError:
    TRGSignalGenerator = None

try:
    from .trading import TRGTradingSystem, TRGTradingConfig
except ImportError:
    TRGTradingSystem = None
    TRGTradingConfig = None

try:
    from .filters import TRGFilterManager
except ImportError:
    TRGFilterManager = None

try:
    from .optimizer import TRGOptimizer, TRGOptimizerConfig
except ImportError:
    TRGOptimizer = None
    TRGOptimizerConfig = None


__version__ = "1.4.0"
__author__ = "Komas Trading System"

__all__ = [
    # Version
    "__version__",
    "__author__",
    
    # Backtest
    "BacktestConfig",
    "MonthlyStats",
    "TPStats",
    "BacktestResult",
    "TRGBacktest",
    
    # Indicator functions
    "calculate_atr",
    "calculate_trg",
    "calculate_supertrend",
    "calculate_rsi",
    "calculate_adx",
    "generate_signals",
    
    # UI helpers
    "prepare_candles",
    "prepare_indicators",
    "prepare_trade_markers",
    "get_current_signal",
    
    # Parallel
    "run_parallel_backtest",
    "calculate_score",
    
    # Other components (optional)
    "TRGIndicator",
    "TRGSignalGenerator",
    "TRGTradingSystem",
    "TRGTradingConfig",
    "TRGFilterManager",
    "TRGOptimizer",
    "TRGOptimizerConfig",
]
