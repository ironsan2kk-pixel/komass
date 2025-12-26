"""
Komas Trading System - TRG Filter Configuration
================================================

Конфигурация фильтров для TRG индикатора.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class TRGFilterConfig:
    """
    Конфигурация всех фильтров для TRG индикатора.
    
    Все фильтры можно включать/выключать независимо.
    Каждый фильтр имеет свои параметры.
    
    Attributes:
        use_supertrend: Включить SuperTrend фильтр
        supertrend_period: Период ATR для SuperTrend
        supertrend_multiplier: Множитель ATR
        
        use_rsi: Включить RSI фильтр
        rsi_period: Период RSI
        rsi_overbought: Уровень перекупленности (блок long)
        rsi_oversold: Уровень перепроданности (блок short)
        
        use_adx: Включить ADX фильтр
        adx_period: Период ADX
        adx_threshold: Минимальный ADX для входа
        
        use_volume: Включить Volume фильтр
        volume_ma_period: Период MA для объёма
        volume_threshold: Множитель (объём > MA * threshold)
    """
    
    # SuperTrend Filter
    use_supertrend: bool = False
    supertrend_period: int = 10
    supertrend_multiplier: float = 3.0
    
    # RSI Filter
    use_rsi: bool = False
    rsi_period: int = 14
    rsi_overbought: float = 70.0
    rsi_oversold: float = 30.0
    
    # ADX Filter
    use_adx: bool = False
    adx_period: int = 14
    adx_threshold: float = 25.0
    
    # Volume Filter
    use_volume: bool = False
    volume_ma_period: int = 20
    volume_threshold: float = 1.5  # Объём должен быть > MA * 1.5
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразование в словарь"""
        return {
            'use_supertrend': self.use_supertrend,
            'supertrend_period': self.supertrend_period,
            'supertrend_multiplier': self.supertrend_multiplier,
            'use_rsi': self.use_rsi,
            'rsi_period': self.rsi_period,
            'rsi_overbought': self.rsi_overbought,
            'rsi_oversold': self.rsi_oversold,
            'use_adx': self.use_adx,
            'adx_period': self.adx_period,
            'adx_threshold': self.adx_threshold,
            'use_volume': self.use_volume,
            'volume_ma_period': self.volume_ma_period,
            'volume_threshold': self.volume_threshold,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TRGFilterConfig':
        """Создание из словаря"""
        return cls(
            use_supertrend=data.get('use_supertrend', False),
            supertrend_period=data.get('supertrend_period', 10),
            supertrend_multiplier=data.get('supertrend_multiplier', 3.0),
            use_rsi=data.get('use_rsi', data.get('use_rsi_filter', False)),
            rsi_period=data.get('rsi_period', 14),
            rsi_overbought=data.get('rsi_overbought', 70.0),
            rsi_oversold=data.get('rsi_oversold', 30.0),
            use_adx=data.get('use_adx', data.get('use_adx_filter', False)),
            adx_period=data.get('adx_period', 14),
            adx_threshold=data.get('adx_threshold', 25.0),
            use_volume=data.get('use_volume', data.get('use_volume_filter', False)),
            volume_ma_period=data.get('volume_ma_period', 20),
            volume_threshold=data.get('volume_threshold', 1.5),
        )
    
    def get_active_filters(self) -> list:
        """Получить список активных фильтров"""
        active = []
        if self.use_supertrend:
            active.append('supertrend')
        if self.use_rsi:
            active.append('rsi')
        if self.use_adx:
            active.append('adx')
        if self.use_volume:
            active.append('volume')
        return active
    
    def get_filter_summary(self) -> str:
        """Получить краткое описание активных фильтров"""
        parts = []
        if self.use_supertrend:
            parts.append(f"ST({self.supertrend_period},{self.supertrend_multiplier})")
        if self.use_rsi:
            parts.append(f"RSI({self.rsi_period},{self.rsi_overbought}/{self.rsi_oversold})")
        if self.use_adx:
            parts.append(f"ADX({self.adx_period},{self.adx_threshold})")
        if self.use_volume:
            parts.append(f"Vol({self.volume_ma_period},{self.volume_threshold}x)")
        
        return "+".join(parts) if parts else "No filters"
    
    def copy(self) -> 'TRGFilterConfig':
        """Создать копию конфигурации"""
        return TRGFilterConfig.from_dict(self.to_dict())
    
    def update(self, **kwargs) -> 'TRGFilterConfig':
        """Обновить параметры и вернуть новую конфигурацию"""
        data = self.to_dict()
        data.update(kwargs)
        return TRGFilterConfig.from_dict(data)


# Предустановленные конфигурации фильтров
FILTER_PRESETS = {
    'none': TRGFilterConfig(),
    
    'supertrend_only': TRGFilterConfig(
        use_supertrend=True,
        supertrend_period=10,
        supertrend_multiplier=3.0,
    ),
    
    'rsi_only': TRGFilterConfig(
        use_rsi=True,
        rsi_period=14,
        rsi_overbought=70,
        rsi_oversold=30,
    ),
    
    'adx_only': TRGFilterConfig(
        use_adx=True,
        adx_period=14,
        adx_threshold=25,
    ),
    
    'volume_only': TRGFilterConfig(
        use_volume=True,
        volume_ma_period=20,
        volume_threshold=1.5,
    ),
    
    'supertrend_rsi': TRGFilterConfig(
        use_supertrend=True,
        supertrend_period=10,
        supertrend_multiplier=3.0,
        use_rsi=True,
        rsi_period=14,
        rsi_overbought=70,
        rsi_oversold=30,
    ),
    
    'supertrend_adx': TRGFilterConfig(
        use_supertrend=True,
        supertrend_period=10,
        supertrend_multiplier=3.0,
        use_adx=True,
        adx_period=14,
        adx_threshold=25,
    ),
    
    'rsi_adx': TRGFilterConfig(
        use_rsi=True,
        rsi_period=14,
        rsi_overbought=70,
        rsi_oversold=30,
        use_adx=True,
        adx_period=14,
        adx_threshold=25,
    ),
    
    'all': TRGFilterConfig(
        use_supertrend=True,
        supertrend_period=10,
        supertrend_multiplier=3.0,
        use_rsi=True,
        rsi_period=14,
        rsi_overbought=70,
        rsi_oversold=30,
        use_adx=True,
        adx_period=14,
        adx_threshold=25,
        use_volume=True,
        volume_ma_period=20,
        volume_threshold=1.5,
    ),
    
    # Консервативный - только сильные тренды
    'conservative': TRGFilterConfig(
        use_supertrend=True,
        supertrend_period=14,
        supertrend_multiplier=3.0,
        use_adx=True,
        adx_period=14,
        adx_threshold=30,  # Более строгий
        use_volume=True,
        volume_ma_period=20,
        volume_threshold=1.5,
    ),
    
    # Агрессивный - меньше фильтрации
    'aggressive': TRGFilterConfig(
        use_supertrend=True,
        supertrend_period=7,
        supertrend_multiplier=2.0,  # Более чувствительный
        use_adx=True,
        adx_period=10,
        adx_threshold=20,  # Менее строгий
    ),
}


def get_preset(name: str) -> Optional[TRGFilterConfig]:
    """
    Получить предустановленную конфигурацию по имени.
    
    Args:
        name: Имя пресета (none, supertrend_only, rsi_only, all, etc.)
        
    Returns:
        Копия конфигурации или None если пресет не найден
    """
    preset = FILTER_PRESETS.get(name.lower())
    return preset.copy() if preset else None


def list_presets() -> list:
    """Получить список доступных пресетов"""
    return list(FILTER_PRESETS.keys())
