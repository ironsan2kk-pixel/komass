"""
Komas Trading System - Volume Filter
=====================================

Volume фильтр для TRG индикатора.

Логика фильтра:
- Сигналы разрешены только при объёме выше среднего
- Volume > MA(Volume) * threshold

Это помогает избежать входов при низкой ликвидности
и торговать только при повышенной активности рынка.

Алгоритм:
1. Рассчитать MA объёма
2. Сравнить текущий объём с MA * threshold
3. Если объём достаточный → разрешить сигнал
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class VolumeResult:
    """Результат анализа объёма"""
    volume: float           # Текущий объём
    volume_ma: float        # Скользящее среднее объёма
    volume_ratio: float     # Отношение объёма к MA
    high_volume: bool       # Объём выше порога
    relative_volume: float  # Volume / Average (%)


@dataclass
class FilterDecision:
    """Решение фильтра по сигналу"""
    allow: bool
    reason: str = ""
    values: Dict[str, Any] = field(default_factory=dict)


class VolumeFilter:
    """
    Volume фильтр.
    
    Фильтрует сигналы на основе объёма:
    - Сигналы разрешены только при объёме > MA * threshold
    
    Attributes:
        ma_period: Период для MA объёма (default: 20)
        threshold: Множитель MA (default: 1.5)
        enabled: Включён ли фильтр
    """
    
    name = "Volume"
    description = "Filter signals based on volume above average"
    
    def __init__(
        self,
        ma_period: int = 20,
        threshold: float = 1.5,
        enabled: bool = True
    ):
        """
        Инициализация фильтра.
        
        Args:
            ma_period: Период для скользящего среднего объёма
            threshold: Множитель (объём должен быть > MA * threshold)
            enabled: Включён ли фильтр
        """
        self.ma_period = max(5, ma_period)
        self.threshold = max(0.5, threshold)
        self.enabled = enabled
        
        self.output_columns = ['volume_ma', 'volume_ratio', 'high_volume']
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Рассчитать индикаторы объёма для DataFrame.
        
        Добавляет колонки:
        - volume_ma: Скользящее среднее объёма
        - volume_ratio: Текущий объём / MA
        - high_volume: Булево (объём выше порога)
        
        Args:
            df: DataFrame с OHLCV данными
            
        Returns:
            DataFrame с добавленными колонками
        """
        if not self.enabled:
            return df
        
        df = df.copy()
        
        volume = df['volume']
        
        # Moving average of volume
        volume_ma = volume.rolling(window=self.ma_period, min_periods=1).mean()
        
        # Volume ratio
        volume_ratio = volume / volume_ma.replace(0, np.nan)
        volume_ratio = volume_ratio.fillna(1.0)
        
        # High volume flag
        high_volume = volume_ratio >= self.threshold
        
        df['volume_ma'] = volume_ma
        df['volume_ratio'] = volume_ratio
        df['high_volume'] = high_volume
        
        return df
    
    def calculate_ema(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Рассчитать индикаторы объёма используя EMA.
        
        Args:
            df: DataFrame с OHLCV данными
            
        Returns:
            DataFrame с индикаторами объёма
        """
        if not self.enabled:
            return df
        
        df = df.copy()
        
        volume = df['volume']
        
        # EMA of volume
        volume_ma = volume.ewm(span=self.ma_period, adjust=False).mean()
        
        # Volume ratio
        volume_ratio = volume / volume_ma.replace(0, np.nan)
        volume_ratio = volume_ratio.fillna(1.0)
        
        # High volume flag
        high_volume = volume_ratio >= self.threshold
        
        df['volume_ma'] = volume_ma
        df['volume_ratio'] = volume_ratio
        df['high_volume'] = high_volume
        
        return df
    
    def check(self, row: pd.Series, signal_type: str) -> FilterDecision:
        """
        Проверить условия фильтра для сигнала.
        
        Volume фильтр не зависит от типа сигнала.
        
        Args:
            row: Строка DataFrame с данными
            signal_type: Тип сигнала ('long' или 'short') - не используется
            
        Returns:
            FilterDecision с результатом проверки
        """
        if not self.enabled:
            return FilterDecision(allow=True, reason="Filter disabled")
        
        # Проверяем наличие колонок
        if 'volume_ratio' not in row.index and 'volume' not in row.index:
            return FilterDecision(allow=True, reason="Volume data not available")
        
        # Если есть предрасчитанные данные
        if 'volume_ratio' in row.index:
            volume_ratio = row.get('volume_ratio', 1.0)
            volume = row.get('volume', 0)
            volume_ma = row.get('volume_ma', 0)
        else:
            # Иначе нужен только текущий объём
            # (MA не можем посчитать из одной строки)
            return FilterDecision(allow=True, reason="Need pre-calculated volume data")
        
        # Handle NaN
        if pd.isna(volume_ratio):
            volume_ratio = 1.0
        
        values = {
            'volume': round(volume, 2) if not pd.isna(volume) else 0,
            'volume_ma': round(volume_ma, 2) if not pd.isna(volume_ma) else 0,
            'volume_ratio': round(volume_ratio, 2),
            'threshold': self.threshold,
        }
        
        # Check volume against threshold
        if volume_ratio < self.threshold:
            return FilterDecision(
                allow=False,
                reason=f"Volume ratio={volume_ratio:.2f} < {self.threshold}x, blocking {signal_type.upper()}",
                values=values
            )
        
        return FilterDecision(allow=True, values=values)
    
    def check_df(self, df: pd.DataFrame, signal_type: str) -> pd.Series:
        """
        Проверить условия фильтра для всего DataFrame.
        
        Args:
            df: DataFrame с рассчитанными индикаторами объёма
            signal_type: Тип сигнала (не используется для Volume)
            
        Returns:
            pd.Series с булевыми значениями (True = разрешено)
        """
        if not self.enabled:
            return pd.Series(True, index=df.index)
        
        if 'high_volume' in df.columns:
            return df['high_volume']
        
        if 'volume_ratio' in df.columns:
            return df['volume_ratio'] >= self.threshold
        
        return pd.Series(True, index=df.index)
    
    def get_value(self, row: pd.Series) -> Optional[VolumeResult]:
        """
        Получить значения объёма для конкретной строки.
        
        Args:
            row: Строка DataFrame
            
        Returns:
            VolumeResult или None
        """
        if 'volume' not in row.index:
            return None
        
        volume = row.get('volume', 0)
        volume_ma = row.get('volume_ma', 0)
        volume_ratio = row.get('volume_ratio', 1.0)
        
        # Handle NaN
        if pd.isna(volume):
            volume = 0
        if pd.isna(volume_ma):
            volume_ma = volume
        if pd.isna(volume_ratio):
            volume_ratio = 1.0
        
        return VolumeResult(
            volume=float(volume),
            volume_ma=float(volume_ma),
            volume_ratio=float(volume_ratio),
            high_volume=volume_ratio >= self.threshold,
            relative_volume=float(volume_ratio * 100)
        )
    
    def get_volume_level(self, volume_ratio: float) -> str:
        """
        Интерпретация уровня объёма.
        
        Returns:
            'very_high', 'high', 'normal', 'low', 'very_low'
        """
        if volume_ratio >= 3.0:
            return 'very_high'
        elif volume_ratio >= 2.0:
            return 'high'
        elif volume_ratio >= 1.0:
            return 'normal'
        elif volume_ratio >= 0.5:
            return 'low'
        return 'very_low'
    
    def get_config(self) -> Dict[str, Any]:
        """Получить конфигурацию фильтра"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'ma_period': self.ma_period,
            'threshold': self.threshold,
        }
    
    def set_config(self, **kwargs):
        """Установить конфигурацию фильтра"""
        if 'ma_period' in kwargs:
            self.ma_period = max(5, kwargs['ma_period'])
        if 'threshold' in kwargs:
            self.threshold = max(0.5, kwargs['threshold'])
        if 'enabled' in kwargs:
            self.enabled = kwargs['enabled']
    
    def __repr__(self) -> str:
        status = "ON" if self.enabled else "OFF"
        return f"VolumeFilter(period={self.ma_period}, threshold={self.threshold}x, {status})"


def calculate_volume_indicators(
    df: pd.DataFrame,
    ma_period: int = 20,
    threshold: float = 1.5
) -> pd.DataFrame:
    """
    Удобная функция для расчёта индикаторов объёма.
    
    Args:
        df: DataFrame с OHLCV данными
        ma_period: Период MA
        threshold: Множитель для определения высокого объёма
        
    Returns:
        DataFrame с добавленными колонками
    """
    filter_obj = VolumeFilter(ma_period=ma_period, threshold=threshold)
    return filter_obj.calculate(df)
