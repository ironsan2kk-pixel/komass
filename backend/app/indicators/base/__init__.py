"""
Komas Trading System - Base Classes

Базовые абстрактные классы для плагинов индикаторов.

Модули:
- indicator.py: BaseIndicator и хелперы
- trading.py: BaseTradingSystem, Position, Trade
- filter.py: BaseFilter, FilterChain и готовые фильтры
- optimizer.py: BaseOptimizer с параллельной оптимизацией
- backtest.py: BaseBacktest движок

Все эти файлы созданы в чате #05 и должны быть в этой папке.
"""

# === Indicator ===
from .indicator import (
    BaseIndicator,
    IndicatorParameter,
    IndicatorResult,
    SignalType,
    TrendDirection,
    calculate_atr,
    calculate_ema,
    calculate_sma,
    crossover,
    crossunder
)

# === Trading ===
from .trading import (
    BaseTradingSystem,
    Position,
    Trade,
    TradingConfig,
    TakeProfitLevel,
    TrailingMode
)

# === Filter ===
from .filter import (
    BaseFilter,
    FilterChain,
    FilterResult,
    SuperTrendFilter,
    RSIFilter,
    ADXFilter,
    VolumeFilter
)

# === Optimizer ===
from .optimizer import (
    BaseOptimizer,
    ParameterRange,
    OptimizationConfig,
    OptimizationResult,
    calculate_advanced_score
)

# === Backtest ===
from .backtest import (
    BaseBacktest,
    BacktestResult,
    MonthlyStats,
    TPStats,
    SimpleTradingSystem
)


__all__ = [
    # Indicator
    "BaseIndicator",
    "IndicatorParameter",
    "IndicatorResult",
    "SignalType",
    "TrendDirection",
    "calculate_atr",
    "calculate_ema",
    "calculate_sma",
    "crossover",
    "crossunder",
    
    # Trading
    "BaseTradingSystem",
    "Position",
    "Trade",
    "TradingConfig",
    "TakeProfitLevel",
    "TrailingMode",
    
    # Filter
    "BaseFilter",
    "FilterChain",
    "FilterResult",
    "SuperTrendFilter",
    "RSIFilter",
    "ADXFilter",
    "VolumeFilter",
    
    # Optimizer
    "BaseOptimizer",
    "ParameterRange",
    "OptimizationConfig",
    "OptimizationResult",
    "calculate_advanced_score",
    
    # Backtest
    "BaseBacktest",
    "BacktestResult",
    "MonthlyStats",
    "TPStats",
    "SimpleTradingSystem"
]
