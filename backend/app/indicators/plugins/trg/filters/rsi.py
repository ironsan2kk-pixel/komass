"""
Komas Trading System - RSI Filter
==================================

RSI (Relative Strength Index) фильтр для TRG индикатора.

Логика фильтра:
- Long сигналы блокируются когда RSI > Overbought (рынок перекуплен)
- Short сигналы блокируются когда RSI < Oversold (рынок перепродан)

Это предотвращает входы в позиции против экстремальных значений RSI.

Алгоритм RSI:
1. Рассчитать изменения цены (delta)
2. Разделить на gains (положительные) и losses (отрицательные)
3. RS = Average Gain / Average Loss
4. RSI = 100 - (100 / (1 + RS))
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class RSIResult:
    """Результат расчёта RSI"""
    rsi: float              # Текущее значение RSI (0-100)
    overbought: bool        # RSI выше уровня перекупленности
    oversold: bool          # RSI ниже уровня перепроданности
    avg_gain: float = 0     # Средний прирост
    avg_loss: float = 0     # Средние потери


@dataclass
class FilterDecision:
    """Решение фильтра по сигналу"""
    allow: bool
    reason: str = ""
    values: Dict[str, Any] = field(default_factory=dict)


class RSIFilter:
    """
    RSI фильтр.
    
    Фильтрует сигналы на основе значений RSI:
    - Long блокируется при RSI > overbought
    - Short блокируется при RSI < oversold
    
    Attributes:
        period: Период RSI (default: 14)
        overbought: Уровень перекупленности (default: 70)
        oversold: Уровень перепроданности (default: 30)
        enabled: Включён ли фильтр
    """
    
    name = "RSI"
    description = "Filter signals based on RSI overbought/oversold levels"
    
    def __init__(
        self,
        period: int = 14,
        overbought: float = 70.0,
        oversold: float = 30.0,
        enabled: bool = True
    ):
        """
        Инициализация фильтра.
        
        Args:
            period: Период для расчёта RSI
            overbought: Уровень перекупленности (0-100)
            oversold: Уровень перепроданности (0-100)
            enabled: Включён ли фильтр
        """
        self.period = max(2, period)
        self.overbought = max(50, min(100, overbought))
        self.oversold = max(0, min(50, oversold))
        self.enabled = enabled
        
        # Validate levels
        if self.oversold >= self.overbought:
            self.oversold = 30
            self.overbought = 70
        
        self.output_columns = ['rsi']
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Рассчитать RSI для DataFrame.
        
        Добавляет колонки:
        - rsi: Значение RSI (0-100)
        
        Args:
            df: DataFrame с OHLCV данными
            
        Returns:
            DataFrame с добавленной колонкой rsi
        """
        if not self.enabled:
            return df
        
        df = df.copy()
        
        # Price changes
        close = df['close']
        delta = close.diff()
        
        # Separate gains and losses
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        # Calculate average gain and loss using SMA (можно также использовать EMA)
        avg_gain = gain.rolling(window=self.period, min_periods=1).mean()
        avg_loss = loss.rolling(window=self.period, min_periods=1).mean()
        
        # Calculate RS and RSI
        # Avoid division by zero
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        
        # Fill NaN with 50 (neutral)
        rsi = rsi.fillna(50)
        
        df['rsi'] = rsi
        
        return df
    
    def calculate_wilder(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Рассчитать RSI используя Wilder's smoothing (EMA).
        
        Это более точная версия, используемая в TradingView.
        
        Args:
            df: DataFrame с OHLCV данными
            
        Returns:
            DataFrame с RSI
        """
        if not self.enabled:
            return df
        
        df = df.copy()
        
        close = df['close']
        delta = close.diff()
        
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        # Wilder's smoothing (alpha = 1/period)
        alpha = 1 / self.period
        avg_gain = gain.ewm(alpha=alpha, adjust=False).mean()
        avg_loss = loss.ewm(alpha=alpha, adjust=False).mean()
        
        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.fillna(50)
        
        df['rsi'] = rsi
        
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
        
        if 'rsi' not in row.index:
            return FilterDecision(allow=True, reason="RSI not calculated")
        
        rsi = row.get('rsi', 50)
        
        # Handle NaN
        if pd.isna(rsi):
            rsi = 50
        
        values = {
            'rsi': round(rsi, 2),
            'overbought': self.overbought,
            'oversold': self.oversold,
        }
        
        # Check signal against RSI levels
        if signal_type.lower() == 'long':
            if rsi >= self.overbought:
                return FilterDecision(
                    allow=False,
                    reason=f"RSI={rsi:.1f} >= {self.overbought} (overbought), blocking LONG",
                    values=values
                )
        elif signal_type.lower() == 'short':
            if rsi <= self.oversold:
                return FilterDecision(
                    allow=False,
                    reason=f"RSI={rsi:.1f} <= {self.oversold} (oversold), blocking SHORT",
                    values=values
                )
        
        return FilterDecision(allow=True, values=values)
    
    def check_df(self, df: pd.DataFrame, signal_type: str) -> pd.Series:
        """
        Проверить условия фильтра для всего DataFrame.
        
        Args:
            df: DataFrame с рассчитанным RSI
            signal_type: Тип сигнала ('long' или 'short')
            
        Returns:
            pd.Series с булевыми значениями (True = разрешено)
        """
        if not self.enabled:
            return pd.Series(True, index=df.index)
        
        if 'rsi' not in df.columns:
            return pd.Series(True, index=df.index)
        
        if signal_type.lower() == 'long':
            # Long разрешён если RSI < overbought
            return df['rsi'] < self.overbought
        elif signal_type.lower() == 'short':
            # Short разрешён если RSI > oversold
            return df['rsi'] > self.oversold
        
        return pd.Series(True, index=df.index)
    
    def get_value(self, row: pd.Series) -> Optional[RSIResult]:
        """
        Получить значения RSI для конкретной строки.
        
        Args:
            row: Строка DataFrame
            
        Returns:
            RSIResult или None
        """
        if 'rsi' not in row.index:
            return None
        
        rsi = row.get('rsi', 50)
        if pd.isna(rsi):
            rsi = 50
        
        return RSIResult(
            rsi=float(rsi),
            overbought=rsi >= self.overbought,
            oversold=rsi <= self.oversold
        )
    
    def get_zone(self, rsi: float) -> str:
        """
        Определить зону RSI.
        
        Returns:
            'overbought', 'oversold', или 'neutral'
        """
        if rsi >= self.overbought:
            return 'overbought'
        elif rsi <= self.oversold:
            return 'oversold'
        return 'neutral'
    
    def get_config(self) -> Dict[str, Any]:
        """Получить конфигурацию фильтра"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'period': self.period,
            'overbought': self.overbought,
            'oversold': self.oversold,
        }
    
    def set_config(self, **kwargs):
        """Установить конфигурацию фильтра"""
        if 'period' in kwargs:
            self.period = max(2, kwargs['period'])
        if 'overbought' in kwargs:
            self.overbought = max(50, min(100, kwargs['overbought']))
        if 'oversold' in kwargs:
            self.oversold = max(0, min(50, kwargs['oversold']))
        if 'enabled' in kwargs:
            self.enabled = kwargs['enabled']
        
        # Validate
        if self.oversold >= self.overbought:
            self.oversold = 30
            self.overbought = 70
    
    def __repr__(self) -> str:
        status = "ON" if self.enabled else "OFF"
        return f"RSIFilter(period={self.period}, OB={self.overbought}, OS={self.oversold}, {status})"


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Удобная функция для расчёта RSI.
    
    Совместима с legacy indicator_routes.py API.
    
    Args:
        df: DataFrame с OHLCV данными
        period: Период RSI
        
    Returns:
        DataFrame с добавленной колонкой rsi
    """
    filter_obj = RSIFilter(period=period)
    return filter_obj.calculate(df)
