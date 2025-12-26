"""
Komas Trading System - SuperTrend Filter
=========================================

SuperTrend фильтр для TRG индикатора.

SuperTrend определяет направление тренда и используется как фильтр:
- Long сигналы разрешены только при SuperTrend UP (direction = 1)
- Short сигналы разрешены только при SuperTrend DOWN (direction = -1)

Алгоритм:
1. Рассчитывается ATR
2. Upper band = HL2 + (Multiplier * ATR)
3. Lower band = HL2 - (Multiplier * ATR)
4. Если Close > Upper band → тренд UP
5. Если Close < Lower band → тренд DOWN
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple


@dataclass
class SuperTrendResult:
    """Результат расчёта SuperTrend"""
    supertrend: float  # Линия SuperTrend
    direction: int     # 1 = UP (bullish), -1 = DOWN (bearish)
    upper_band: float  # Верхняя полоса
    lower_band: float  # Нижняя полоса
    atr: float         # ATR на этом баре


@dataclass
class FilterDecision:
    """Решение фильтра по сигналу"""
    allow: bool                           # Разрешить сигнал
    reason: str = ""                      # Причина блокировки
    values: Dict[str, Any] = field(default_factory=dict)  # Значения индикатора


class SuperTrendFilter:
    """
    SuperTrend фильтр.
    
    Фильтрует сигналы на основе направления SuperTrend:
    - Long только при SuperTrend UP
    - Short только при SuperTrend DOWN
    
    Attributes:
        period: Период ATR (default: 10)
        multiplier: Множитель ATR (default: 3.0)
        enabled: Включён ли фильтр
    """
    
    name = "SuperTrend"
    description = "Filter signals based on SuperTrend direction"
    
    def __init__(
        self,
        period: int = 10,
        multiplier: float = 3.0,
        enabled: bool = True
    ):
        """
        Инициализация фильтра.
        
        Args:
            period: Период ATR для расчёта
            multiplier: Множитель ATR для полос
            enabled: Включён ли фильтр
        """
        self.period = max(1, period)
        self.multiplier = max(0.1, multiplier)
        self.enabled = enabled
        
        # Колонки, которые добавляет фильтр
        self.output_columns = ['supertrend', 'supertrend_dir', 'supertrend_upper', 'supertrend_lower']
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Рассчитать SuperTrend для DataFrame.
        
        Добавляет колонки:
        - supertrend: Линия SuperTrend
        - supertrend_dir: Направление (1 = UP, -1 = DOWN)
        - supertrend_upper: Верхняя полоса
        - supertrend_lower: Нижняя полоса
        
        Args:
            df: DataFrame с OHLCV данными
            
        Returns:
            DataFrame с добавленными колонками
        """
        if not self.enabled:
            return df
        
        df = df.copy()
        
        high = df['high']
        low = df['low']
        close = df['close']
        
        # True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # ATR (Simple Moving Average)
        atr = tr.rolling(window=self.period, min_periods=1).mean()
        
        # HL2 (midpoint)
        hl2 = (high + low) / 2
        
        # Basic bands
        upper_basic = hl2 + (self.multiplier * atr)
        lower_basic = hl2 - (self.multiplier * atr)
        
        # Initialize arrays
        n = len(df)
        supertrend = np.zeros(n)
        direction = np.zeros(n, dtype=int)
        upper_band = np.zeros(n)
        lower_band = np.zeros(n)
        
        # First values
        upper_band[0] = upper_basic.iloc[0]
        lower_band[0] = lower_basic.iloc[0]
        direction[0] = 1  # Start bullish
        supertrend[0] = lower_band[0]
        
        # Calculate SuperTrend iteratively
        for i in range(1, n):
            # Update bands with trailing logic
            # Lower band: only rises (support)
            if lower_basic.iloc[i] > lower_band[i-1] or close.iloc[i-1] < lower_band[i-1]:
                lower_band[i] = lower_basic.iloc[i]
            else:
                lower_band[i] = lower_band[i-1]
            
            # Upper band: only falls (resistance)
            if upper_basic.iloc[i] < upper_band[i-1] or close.iloc[i-1] > upper_band[i-1]:
                upper_band[i] = upper_basic.iloc[i]
            else:
                upper_band[i] = upper_band[i-1]
            
            # Determine direction
            if direction[i-1] == 1:  # Was bullish
                if close.iloc[i] < lower_band[i]:
                    direction[i] = -1  # Turn bearish
                    supertrend[i] = upper_band[i]
                else:
                    direction[i] = 1  # Stay bullish
                    supertrend[i] = lower_band[i]
            else:  # Was bearish
                if close.iloc[i] > upper_band[i]:
                    direction[i] = 1  # Turn bullish
                    supertrend[i] = lower_band[i]
                else:
                    direction[i] = -1  # Stay bearish
                    supertrend[i] = upper_band[i]
        
        # Add columns
        df['supertrend'] = supertrend
        df['supertrend_dir'] = direction
        df['supertrend_upper'] = upper_band
        df['supertrend_lower'] = lower_band
        
        return df
    
    def check(self, row: pd.Series, signal_type: str) -> FilterDecision:
        """
        Проверить условия фильтра для сигнала.
        
        Args:
            row: Строка DataFrame с данными
            signal_type: Тип сигнала ('long' или 'short')
            
        Returns:
            FilterDecision с результатом проверки
        """
        if not self.enabled:
            return FilterDecision(allow=True, reason="Filter disabled")
        
        # Get direction
        if 'supertrend_dir' not in row.index:
            return FilterDecision(
                allow=True,
                reason="SuperTrend not calculated"
            )
        
        direction = row.get('supertrend_dir', 0)
        supertrend = row.get('supertrend', 0)
        
        values = {
            'supertrend': supertrend,
            'direction': direction,
        }
        
        # Check signal against direction
        if signal_type.lower() == 'long':
            if direction != 1:
                return FilterDecision(
                    allow=False,
                    reason="SuperTrend bearish (direction=-1), blocking LONG",
                    values=values
                )
        elif signal_type.lower() == 'short':
            if direction != -1:
                return FilterDecision(
                    allow=False,
                    reason="SuperTrend bullish (direction=1), blocking SHORT",
                    values=values
                )
        
        return FilterDecision(allow=True, values=values)
    
    def check_df(self, df: pd.DataFrame, signal_type: str) -> pd.Series:
        """
        Проверить условия фильтра для всего DataFrame.
        
        Возвращает Series с булевыми значениями (True = сигнал разрешён).
        
        Args:
            df: DataFrame с рассчитанным SuperTrend
            signal_type: Тип сигнала ('long' или 'short')
            
        Returns:
            pd.Series с булевыми значениями
        """
        if not self.enabled:
            return pd.Series(True, index=df.index)
        
        if 'supertrend_dir' not in df.columns:
            return pd.Series(True, index=df.index)
        
        if signal_type.lower() == 'long':
            return df['supertrend_dir'] == 1
        elif signal_type.lower() == 'short':
            return df['supertrend_dir'] == -1
        
        return pd.Series(True, index=df.index)
    
    def get_value(self, row: pd.Series) -> Optional[SuperTrendResult]:
        """
        Получить значения SuperTrend для конкретной строки.
        
        Args:
            row: Строка DataFrame
            
        Returns:
            SuperTrendResult или None
        """
        if 'supertrend' not in row.index:
            return None
        
        return SuperTrendResult(
            supertrend=row.get('supertrend', 0),
            direction=int(row.get('supertrend_dir', 0)),
            upper_band=row.get('supertrend_upper', 0),
            lower_band=row.get('supertrend_lower', 0),
            atr=0  # Not stored per-row in simplified version
        )
    
    def get_config(self) -> Dict[str, Any]:
        """Получить конфигурацию фильтра"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'period': self.period,
            'multiplier': self.multiplier,
        }
    
    def set_config(self, **kwargs):
        """Установить конфигурацию фильтра"""
        if 'period' in kwargs:
            self.period = max(1, kwargs['period'])
        if 'multiplier' in kwargs:
            self.multiplier = max(0.1, kwargs['multiplier'])
        if 'enabled' in kwargs:
            self.enabled = kwargs['enabled']
    
    def __repr__(self) -> str:
        status = "ON" if self.enabled else "OFF"
        return f"SuperTrendFilter(period={self.period}, mult={self.multiplier}, {status})"


def calculate_supertrend(
    df: pd.DataFrame,
    period: int = 10,
    multiplier: float = 3.0
) -> pd.DataFrame:
    """
    Удобная функция для расчёта SuperTrend.
    
    Совместима с legacy indicator_routes.py API.
    
    Args:
        df: DataFrame с OHLCV данными
        period: Период ATR
        multiplier: Множитель ATR
        
    Returns:
        DataFrame с добавленными колонками supertrend и supertrend_dir
    """
    filter_obj = SuperTrendFilter(period=period, multiplier=multiplier)
    return filter_obj.calculate(df)
