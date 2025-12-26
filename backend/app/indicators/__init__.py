"""
Komas Trading System - Indicators Module

Модульная система индикаторов с поддержкой плагинов.

Компоненты:
- Base classes: BaseIndicator, BaseTradingSystem, BaseFilter, BaseOptimizer, BaseBacktest
- Registry: Глобальный реестр плагинов
- Loader: Загрузчик плагинов из manifest.json

Автор: Komas Team
Версия: 1.0.0
"""

# === Base Classes ===
# Импортируются из base/ подмодуля (из чата #05)

try:
    from .base import (
        # Indicator
        BaseIndicator,
        IndicatorParameter,
        IndicatorResult,
        SignalType,
        TrendDirection,
        calculate_atr,
        calculate_ema,
        calculate_sma,
        crossover,
        crossunder,
        
        # Trading
        BaseTradingSystem,
        Position,
        Trade,
        TradingConfig,
        TakeProfitLevel,
        TrailingMode,
        
        # Filter
        BaseFilter,
        FilterChain,
        FilterResult,
        SuperTrendFilter,
        RSIFilter,
        ADXFilter,
        VolumeFilter,
        
        # Optimizer
        BaseOptimizer,
        ParameterRange,
        OptimizationConfig,
        OptimizationResult,
        calculate_advanced_score,
        
        # Backtest
        BaseBacktest,
        BacktestResult,
        MonthlyStats,
        TPStats,
        SimpleTradingSystem
    )
    _BASE_AVAILABLE = True
except ImportError:
    _BASE_AVAILABLE = False


# === Registry ===

from .registry import (
    # Основной реестр
    PluginRegistry,
    registry,
    
    # Типы и данные
    PluginType,
    PluginInfo,
    PluginBundle,
    TypedRegistry,
    
    # Декораторы
    register_indicator,
    register_trading_system,
    register_filter,
    register_optimizer,
    register_backtest,
    
    # Хелперы
    get_indicator,
    get_trading_system,
    get_filter,
    get_optimizer,
    get_backtest,
    list_indicators,
    list_filters
)


# === Loader ===

from .loader import (
    # Основной загрузчик
    PluginLoader,
    get_loader,
    
    # Результаты
    LoadResult,
    PluginManifest,
    ManifestEntryPoint,
    
    # Shortcuts
    load_plugin,
    discover_plugins,
    unload_plugin,
    reload_plugin
)


__version__ = "1.0.0"
__author__ = "Komas Team"


# === Public API ===

__all__ = [
    # Registry
    "PluginRegistry",
    "registry",
    "PluginType",
    "PluginInfo",
    "PluginBundle",
    "TypedRegistry",
    "register_indicator",
    "register_trading_system",
    "register_filter",
    "register_optimizer",
    "register_backtest",
    "get_indicator",
    "get_trading_system",
    "get_filter",
    "get_optimizer",
    "get_backtest",
    "list_indicators",
    "list_filters",
    
    # Loader
    "PluginLoader",
    "get_loader",
    "LoadResult",
    "PluginManifest",
    "ManifestEntryPoint",
    "load_plugin",
    "discover_plugins",
    "unload_plugin",
    "reload_plugin",
    
    # Version
    "__version__",
    "__author__"
]

# Add base classes to __all__ if available
if _BASE_AVAILABLE:
    __all__.extend([
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
        "BaseTradingSystem",
        "Position",
        "Trade",
        "TradingConfig",
        "TakeProfitLevel",
        "TrailingMode",
        "BaseFilter",
        "FilterChain",
        "FilterResult",
        "SuperTrendFilter",
        "RSIFilter",
        "ADXFilter",
        "VolumeFilter",
        "BaseOptimizer",
        "ParameterRange",
        "OptimizationConfig",
        "OptimizationResult",
        "calculate_advanced_score",
        "BaseBacktest",
        "BacktestResult",
        "MonthlyStats",
        "TPStats",
        "SimpleTradingSystem",
    ])
