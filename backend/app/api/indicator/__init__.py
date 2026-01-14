"""
Indicator API Module
====================
Refactored indicator routes into modular structure.

Structure:
- models.py: Pydantic models (IndicatorSettings, etc.)
- cache.py: LRU cache for calculations
- calculate.py: Indicator calculation functions (TRG, SuperTrend, RSI, ADX)
- backtest.py: Backtest engine and statistics
- data.py: Data loading and preparation
- routes.py: FastAPI routes (main entry point)
"""

from fastapi import APIRouter

# Create router
router = APIRouter(prefix="/api/indicator", tags=["Indicator"])

# Import models
from .models import IndicatorSettings, ReplayRequest, AutoOptimizeMode

# Import cache
from .cache import calculation_cache, LRUCache

# Import calculation functions
from .calculate import (
    calculate_trg,
    calculate_supertrend,
    calculate_rsi,
    calculate_adx,
    generate_signals,
    prepare_indicators as prepare_indicator_data
)

# Import backtest functions
from .backtest import (
    run_backtest,
    quick_backtest,
    calculate_statistics,
    build_monthly_stats,
    optimize_on_lookback
)

# Import data functions
from .data import (
    DATA_DIR,
    find_data_dir,
    download_single_symbol,
    load_data,
    prepare_candles,
    prepare_indicators,
    prepare_trade_markers,
    get_current_signal,
    get_data_range
)

__all__ = [
    # Router
    'router',

    # Models
    'IndicatorSettings',
    'ReplayRequest',
    'AutoOptimizeMode',

    # Cache
    'calculation_cache',
    'LRUCache',

    # Calculate
    'calculate_trg',
    'calculate_supertrend',
    'calculate_rsi',
    'calculate_adx',
    'generate_signals',

    # Backtest
    'run_backtest',
    'quick_backtest',
    'calculate_statistics',
    'build_monthly_stats',

    # Data
    'DATA_DIR',
    'download_single_symbol',
    'load_data',
    'prepare_candles',
    'prepare_indicators',
    'prepare_trade_markers',
    'get_current_signal',
    'get_data_range'
]
