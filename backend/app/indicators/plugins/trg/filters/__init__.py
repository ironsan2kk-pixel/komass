"""
Komas Trading System - TRG Plugin Filters
==========================================

Модуль фильтров для TRG индикатора.

Фильтры:
- SuperTrendFilter - направление SuperTrend
- RSIFilter - зоны перекупленности/перепроданности
- ADXFilter - сила тренда
- VolumeFilter - объёмы выше среднего

Использование:
    from .filters import TRGFilterManager, TRGFilterConfig
    
    config = TRGFilterConfig(
        use_supertrend=True,
        supertrend_period=10,
        supertrend_multiplier=3.0,
        use_rsi=True,
        rsi_period=14,
        rsi_overbought=70,
        rsi_oversold=30,
    )
    
    manager = TRGFilterManager(config)
    df = manager.calculate_all(df)
    result = manager.check_signal(row, 'long')
"""

from .supertrend import SuperTrendFilter
from .rsi import RSIFilter
from .adx import ADXFilter
from .volume import VolumeFilter
from .config import TRGFilterConfig
from .manager import TRGFilterManager

__all__ = [
    # Filters
    'SuperTrendFilter',
    'RSIFilter',
    'ADXFilter',
    'VolumeFilter',
    # Config
    'TRGFilterConfig',
    # Manager
    'TRGFilterManager',
]

__version__ = "1.0.0"
