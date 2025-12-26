"""
Komas Trading System - TRG Filter Manager
==========================================

Централизованный менеджер для управления всеми фильтрами TRG индикатора.

Функции:
- Создание фильтров из конфигурации
- Расчёт всех индикаторов для фильтров
- Проверка сигналов через все активные фильтры
- Генерация комбинаций фильтров для оптимизации
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple

try:
    # Relative imports (когда используется как часть пакета)
    from .config import TRGFilterConfig, FILTER_PRESETS
    from .supertrend import SuperTrendFilter
    from .rsi import RSIFilter
    from .adx import ADXFilter
    from .volume import VolumeFilter
except ImportError:
    # Absolute imports (когда запускается напрямую)
    from config import TRGFilterConfig, FILTER_PRESETS
    from supertrend import SuperTrendFilter
    from rsi import RSIFilter
    from adx import ADXFilter
    from volume import VolumeFilter


@dataclass
class FilterCheckResult:
    """
    Результат проверки всех фильтров.
    
    Attributes:
        allow: Итоговое решение (все фильтры пропустили)
        blocked_by: Список фильтров, заблокировавших сигнал
        filter_values: Значения всех фильтров
        reasons: Причины блокировки
    """
    allow: bool
    blocked_by: List[str] = field(default_factory=list)
    filter_values: Dict[str, Any] = field(default_factory=dict)
    reasons: List[str] = field(default_factory=list)


class TRGFilterManager:
    """
    Менеджер фильтров для TRG индикатора.
    
    Управляет всеми фильтрами:
    - SuperTrend
    - RSI
    - ADX
    - Volume
    
    Использование:
        config = TRGFilterConfig(
            use_supertrend=True,
            supertrend_period=10,
            supertrend_multiplier=3.0,
        )
        
        manager = TRGFilterManager(config)
        
        # Расчёт индикаторов
        df = manager.calculate_all(df)
        
        # Проверка сигнала
        result = manager.check_signal(row, 'long')
        if result.allow:
            # Сигнал разрешён
            pass
    """
    
    def __init__(self, config: Optional[TRGFilterConfig] = None):
        """
        Инициализация менеджера.
        
        Args:
            config: Конфигурация фильтров (или None для дефолтной)
        """
        self.config = config or TRGFilterConfig()
        
        # Создаём фильтры
        self._init_filters()
    
    def _init_filters(self):
        """Инициализация фильтров из конфигурации"""
        self.supertrend = SuperTrendFilter(
            period=self.config.supertrend_period,
            multiplier=self.config.supertrend_multiplier,
            enabled=self.config.use_supertrend
        )
        
        self.rsi = RSIFilter(
            period=self.config.rsi_period,
            overbought=self.config.rsi_overbought,
            oversold=self.config.rsi_oversold,
            enabled=self.config.use_rsi
        )
        
        self.adx = ADXFilter(
            period=self.config.adx_period,
            threshold=self.config.adx_threshold,
            enabled=self.config.use_adx
        )
        
        self.volume = VolumeFilter(
            ma_period=self.config.volume_ma_period,
            threshold=self.config.volume_threshold,
            enabled=self.config.use_volume
        )
        
        # Список всех фильтров
        self.filters = [
            self.supertrend,
            self.rsi,
            self.adx,
            self.volume
        ]
    
    def update_config(self, config: TRGFilterConfig):
        """
        Обновить конфигурацию и пересоздать фильтры.
        
        Args:
            config: Новая конфигурация
        """
        self.config = config
        self._init_filters()
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Рассчитать все активные фильтры для DataFrame.
        
        Args:
            df: DataFrame с OHLCV данными
            
        Returns:
            DataFrame с добавленными колонками всех фильтров
        """
        # Apply each filter sequentially
        for f in self.filters:
            if f.enabled:
                df = f.calculate(df)
        
        return df
    
    def check_signal(self, row: pd.Series, signal_type: str) -> FilterCheckResult:
        """
        Проверить сигнал через все активные фильтры.
        
        Args:
            row: Строка DataFrame с данными свечи
            signal_type: Тип сигнала ('long' или 'short')
            
        Returns:
            FilterCheckResult с итоговым решением
        """
        result = FilterCheckResult(allow=True)
        
        for f in self.filters:
            if not f.enabled:
                continue
            
            decision = f.check(row, signal_type)
            
            # Сохраняем значения
            result.filter_values[f.name.lower()] = decision.values
            
            # Если фильтр заблокировал
            if not decision.allow:
                result.allow = False
                result.blocked_by.append(f.name)
                result.reasons.append(decision.reason)
        
        return result
    
    def check_signal_df(self, df: pd.DataFrame, signal_type: str) -> pd.Series:
        """
        Проверить сигналы через все фильтры для всего DataFrame.
        
        Более эффективно чем проверка по строкам.
        
        Args:
            df: DataFrame с рассчитанными фильтрами
            signal_type: Тип сигнала ('long' или 'short')
            
        Returns:
            pd.Series с булевыми значениями (True = разрешено)
        """
        # Начинаем с True для всех
        allowed = pd.Series(True, index=df.index)
        
        for f in self.filters:
            if f.enabled:
                filter_result = f.check_df(df, signal_type)
                allowed &= filter_result
        
        return allowed
    
    def get_active_filters(self) -> List[str]:
        """Получить список имён активных фильтров"""
        return [f.name for f in self.filters if f.enabled]
    
    def get_filter_summary(self) -> str:
        """Получить краткое описание конфигурации"""
        return self.config.get_filter_summary()
    
    def get_all_configs(self) -> Dict[str, Any]:
        """Получить конфигурации всех фильтров"""
        return {
            f.name.lower(): f.get_config()
            for f in self.filters
        }
    
    def enable_filter(self, name: str, enabled: bool = True):
        """
        Включить/выключить фильтр по имени.
        
        Args:
            name: Имя фильтра (supertrend, rsi, adx, volume)
            enabled: Включить или выключить
        """
        name_lower = name.lower()
        
        if name_lower == 'supertrend':
            self.supertrend.enabled = enabled
            self.config.use_supertrend = enabled
        elif name_lower == 'rsi':
            self.rsi.enabled = enabled
            self.config.use_rsi = enabled
        elif name_lower == 'adx':
            self.adx.enabled = enabled
            self.config.use_adx = enabled
        elif name_lower == 'volume':
            self.volume.enabled = enabled
            self.config.use_volume = enabled
    
    def disable_all(self):
        """Выключить все фильтры"""
        for f in self.filters:
            f.enabled = False
        
        self.config.use_supertrend = False
        self.config.use_rsi = False
        self.config.use_adx = False
        self.config.use_volume = False
    
    def enable_all(self):
        """Включить все фильтры"""
        for f in self.filters:
            f.enabled = True
        
        self.config.use_supertrend = True
        self.config.use_rsi = True
        self.config.use_adx = True
        self.config.use_volume = True
    
    def __repr__(self) -> str:
        active = self.get_active_filters()
        if not active:
            return "TRGFilterManager(no active filters)"
        return f"TRGFilterManager({', '.join(active)})"


# ============================================================================
# Функции для оптимизации фильтров
# ============================================================================

def generate_filter_configs() -> List[Dict[str, Any]]:
    """
    Генерация конфигураций фильтров для оптимизации.
    
    Создаёт набор конфигураций для тестирования:
    - Без фильтров (baseline)
    - Отдельные фильтры с разными параметрами
    - Комбинации фильтров
    
    Returns:
        Список словарей с конфигурациями
    """
    configs = []
    
    # No filters (baseline)
    configs.append({
        "name": "No filters",
        "use_supertrend": False,
        "use_rsi": False,
        "use_adx": False,
        "use_volume": False
    })
    
    # SuperTrend only - various settings
    for period in [7, 10, 14, 20]:
        for mult in [2.0, 3.0, 4.0]:
            configs.append({
                "name": f"ST({period},{mult})",
                "use_supertrend": True,
                "supertrend_period": period,
                "supertrend_multiplier": mult,
                "use_rsi": False,
                "use_adx": False,
                "use_volume": False
            })
    
    # RSI only - various settings
    for period in [7, 14, 21]:
        for ob in [65, 70, 75]:
            os = 100 - ob
            configs.append({
                "name": f"RSI({period},{ob}/{os})",
                "use_supertrend": False,
                "use_rsi": True,
                "rsi_period": period,
                "rsi_overbought": ob,
                "rsi_oversold": os,
                "use_adx": False,
                "use_volume": False
            })
    
    # ADX only - various settings
    for period in [10, 14, 20]:
        for threshold in [20, 25, 30]:
            configs.append({
                "name": f"ADX({period},{threshold})",
                "use_supertrend": False,
                "use_rsi": False,
                "use_adx": True,
                "adx_period": period,
                "adx_threshold": threshold,
                "use_volume": False
            })
    
    # Volume only
    for period in [10, 20, 30]:
        for threshold in [1.2, 1.5, 2.0]:
            configs.append({
                "name": f"Vol({period},{threshold}x)",
                "use_supertrend": False,
                "use_rsi": False,
                "use_adx": False,
                "use_volume": True,
                "volume_ma_period": period,
                "volume_threshold": threshold
            })
    
    # Combinations
    # SuperTrend + RSI
    configs.append({
        "name": "ST(10,3)+RSI(14)",
        "use_supertrend": True,
        "supertrend_period": 10,
        "supertrend_multiplier": 3.0,
        "use_rsi": True,
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "use_adx": False,
        "use_volume": False
    })
    
    # SuperTrend + ADX
    configs.append({
        "name": "ST(10,3)+ADX(14,25)",
        "use_supertrend": True,
        "supertrend_period": 10,
        "supertrend_multiplier": 3.0,
        "use_rsi": False,
        "use_adx": True,
        "adx_period": 14,
        "adx_threshold": 25,
        "use_volume": False
    })
    
    # RSI + ADX
    configs.append({
        "name": "RSI(14)+ADX(14,25)",
        "use_supertrend": False,
        "use_rsi": True,
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "use_adx": True,
        "adx_period": 14,
        "adx_threshold": 25,
        "use_volume": False
    })
    
    # SuperTrend + Volume
    configs.append({
        "name": "ST(10,3)+Vol(20,1.5x)",
        "use_supertrend": True,
        "supertrend_period": 10,
        "supertrend_multiplier": 3.0,
        "use_rsi": False,
        "use_adx": False,
        "use_volume": True,
        "volume_ma_period": 20,
        "volume_threshold": 1.5
    })
    
    # All filters
    configs.append({
        "name": "ALL filters",
        "use_supertrend": True,
        "supertrend_period": 10,
        "supertrend_multiplier": 3.0,
        "use_rsi": True,
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30,
        "use_adx": True,
        "adx_period": 14,
        "adx_threshold": 25,
        "use_volume": True,
        "volume_ma_period": 20,
        "volume_threshold": 1.5
    })
    
    return configs


def apply_filter_config(
    df: pd.DataFrame,
    config: Dict[str, Any]
) -> Tuple[pd.DataFrame, TRGFilterManager]:
    """
    Применить конфигурацию фильтров к DataFrame.
    
    Args:
        df: DataFrame с OHLCV данными
        config: Словарь с конфигурацией фильтров
        
    Returns:
        Кортеж (DataFrame с фильтрами, FilterManager)
    """
    # Создаём конфигурацию из словаря
    filter_config = TRGFilterConfig(
        use_supertrend=config.get('use_supertrend', False),
        supertrend_period=config.get('supertrend_period', 10),
        supertrend_multiplier=config.get('supertrend_multiplier', 3.0),
        use_rsi=config.get('use_rsi', config.get('use_rsi_filter', False)),
        rsi_period=config.get('rsi_period', 14),
        rsi_overbought=config.get('rsi_overbought', 70),
        rsi_oversold=config.get('rsi_oversold', 30),
        use_adx=config.get('use_adx', config.get('use_adx_filter', False)),
        adx_period=config.get('adx_period', 14),
        adx_threshold=config.get('adx_threshold', 25),
        use_volume=config.get('use_volume', config.get('use_volume_filter', False)),
        volume_ma_period=config.get('volume_ma_period', 20),
        volume_threshold=config.get('volume_threshold', 1.5),
    )
    
    # Создаём менеджер
    manager = TRGFilterManager(filter_config)
    
    # Рассчитываем фильтры
    df = manager.calculate_all(df)
    
    return df, manager


def generate_signals_with_filters(
    df: pd.DataFrame,
    manager: TRGFilterManager,
    trend_column: str = 'trg_trend'
) -> pd.DataFrame:
    """
    Генерация сигналов с применением фильтров.
    
    Args:
        df: DataFrame с рассчитанным TRG и фильтрами
        manager: FilterManager для проверки
        trend_column: Название колонки с трендом
        
    Returns:
        DataFrame с колонкой 'signal' (1=long, -1=short, 0=нет)
    """
    df = df.copy()
    df['signal'] = 0
    
    # Определяем моменты смены тренда
    trend = df[trend_column]
    trend_change_long = (trend == 1) & (trend.shift(1) == -1)
    trend_change_short = (trend == -1) & (trend.shift(1) == 1)
    
    # Применяем фильтры
    long_filter = manager.check_signal_df(df, 'long')
    short_filter = manager.check_signal_df(df, 'short')
    
    # Генерируем сигналы
    df.loc[trend_change_long & long_filter, 'signal'] = 1
    df.loc[trend_change_short & short_filter, 'signal'] = -1
    
    return df
