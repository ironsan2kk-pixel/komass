"""
Komas Trading System - ADX Filter
==================================

ADX (Average Directional Index) фильтр для TRG индикатора.

ADX измеряет силу тренда (не направление):
- ADX > threshold → тренд сильный, входы разрешены
- ADX < threshold → тренд слабый/флэт, входы заблокированы

Алгоритм:
1. Рассчитать +DM и -DM (Directional Movement)
2. Рассчитать +DI и -DI (Directional Indicators)
3. DX = |+DI - -DI| / (+DI + -DI) * 100
4. ADX = SMA(DX, period)

Дополнительно:
- +DI показывает силу восходящего движения
- -DI показывает силу нисходящего движения
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple


@dataclass
class ADXResult:
    """Результат расчёта ADX"""
    adx: float          # Значение ADX (0-100)
    plus_di: float      # +DI (сила быков)
    minus_di: float     # -DI (сила медведей)
    trending: bool      # ADX > threshold (тренд есть)
    dx: float = 0       # DX (без сглаживания)


@dataclass
class FilterDecision:
    """Решение фильтра по сигналу"""
    allow: bool
    reason: str = ""
    values: Dict[str, Any] = field(default_factory=dict)


class ADXFilter:
    """
    ADX фильтр.
    
    Фильтрует сигналы на основе силы тренда:
    - Сигналы разрешены только при ADX > threshold
    - При низком ADX (флэт) входы блокируются
    
    Attributes:
        period: Период ADX (default: 14)
        threshold: Минимальный ADX для входа (default: 25)
        enabled: Включён ли фильтр
    """
    
    name = "ADX"
    description = "Filter signals based on trend strength (ADX)"
    
    def __init__(
        self,
        period: int = 14,
        threshold: float = 25.0,
        enabled: bool = True
    ):
        """
        Инициализация фильтра.
        
        Args:
            period: Период для расчёта ADX
            threshold: Минимальный ADX для разрешения входа
            enabled: Включён ли фильтр
        """
        self.period = max(2, period)
        self.threshold = max(10, min(50, threshold))
        self.enabled = enabled
        
        self.output_columns = ['adx', 'plus_di', 'minus_di']
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Рассчитать ADX для DataFrame.
        
        Добавляет колонки:
        - adx: Average Directional Index (0-100)
        - plus_di: +DI (сила восходящего движения)
        - minus_di: -DI (сила нисходящего движения)
        
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
        
        # Calculate True Range
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # Calculate Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        # +DM: up move > down move AND up move > 0
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
        
        # -DM: down move > up move AND down move > 0
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)
        
        # Smooth TR and DM
        atr = tr.rolling(window=self.period, min_periods=1).mean()
        smooth_plus_dm = plus_dm.rolling(window=self.period, min_periods=1).mean()
        smooth_minus_dm = minus_dm.rolling(window=self.period, min_periods=1).mean()
        
        # Calculate +DI and -DI
        plus_di = 100 * (smooth_plus_dm / atr.replace(0, np.nan))
        minus_di = 100 * (smooth_minus_dm / atr.replace(0, np.nan))
        
        # Fill NaN
        plus_di = plus_di.fillna(0)
        minus_di = minus_di.fillna(0)
        
        # Calculate DX
        di_sum = plus_di + minus_di
        dx = 100 * abs(plus_di - minus_di) / di_sum.replace(0, np.nan)
        dx = dx.fillna(0)
        
        # Calculate ADX (smooth DX)
        adx = dx.rolling(window=self.period, min_periods=1).mean()
        
        # Store results
        df['adx'] = adx
        df['plus_di'] = plus_di
        df['minus_di'] = minus_di
        
        return df
    
    def calculate_wilder(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Рассчитать ADX используя Wilder's smoothing.
        
        Более точная версия, соответствующая оригинальному алгоритму.
        
        Args:
            df: DataFrame с OHLCV данными
            
        Returns:
            DataFrame с ADX
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
        
        # Directional Movement
        up_move = high - high.shift(1)
        down_move = low.shift(1) - low
        
        plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
        minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)
        
        # Wilder's smoothing (alpha = 1/period)
        alpha = 1 / self.period
        atr = tr.ewm(alpha=alpha, adjust=False).mean()
        smooth_plus_dm = plus_dm.ewm(alpha=alpha, adjust=False).mean()
        smooth_minus_dm = minus_dm.ewm(alpha=alpha, adjust=False).mean()
        
        # +DI and -DI
        plus_di = 100 * (smooth_plus_dm / atr.replace(0, np.nan)).fillna(0)
        minus_di = 100 * (smooth_minus_dm / atr.replace(0, np.nan)).fillna(0)
        
        # DX and ADX
        di_sum = plus_di + minus_di
        dx = 100 * abs(plus_di - minus_di) / di_sum.replace(0, np.nan)
        dx = dx.fillna(0)
        
        adx = dx.ewm(alpha=alpha, adjust=False).mean()
        
        df['adx'] = adx
        df['plus_di'] = plus_di
        df['minus_di'] = minus_di
        
        return df
    
    def check(self, row: pd.Series, signal_type: str) -> FilterDecision:
        """
        Проверить условия фильтра для сигнала.
        
        ADX фильтр не зависит от типа сигнала - проверяет только силу тренда.
        
        Args:
            row: Строка DataFrame с данными
            signal_type: Тип сигнала ('long' или 'short') - не используется
            
        Returns:
            FilterDecision с результатом проверки
        """
        if not self.enabled:
            return FilterDecision(allow=True, reason="Filter disabled")
        
        if 'adx' not in row.index:
            return FilterDecision(allow=True, reason="ADX not calculated")
        
        adx = row.get('adx', 0)
        plus_di = row.get('plus_di', 0)
        minus_di = row.get('minus_di', 0)
        
        # Handle NaN
        if pd.isna(adx):
            adx = 0
        
        values = {
            'adx': round(adx, 2),
            'plus_di': round(plus_di, 2) if not pd.isna(plus_di) else 0,
            'minus_di': round(minus_di, 2) if not pd.isna(minus_di) else 0,
            'threshold': self.threshold,
        }
        
        # Check ADX against threshold
        if adx < self.threshold:
            return FilterDecision(
                allow=False,
                reason=f"ADX={adx:.1f} < {self.threshold} (weak trend), blocking {signal_type.upper()}",
                values=values
            )
        
        return FilterDecision(allow=True, values=values)
    
    def check_df(self, df: pd.DataFrame, signal_type: str) -> pd.Series:
        """
        Проверить условия фильтра для всего DataFrame.
        
        Args:
            df: DataFrame с рассчитанным ADX
            signal_type: Тип сигнала (не используется для ADX)
            
        Returns:
            pd.Series с булевыми значениями (True = разрешено)
        """
        if not self.enabled:
            return pd.Series(True, index=df.index)
        
        if 'adx' not in df.columns:
            return pd.Series(True, index=df.index)
        
        # ADX фильтр одинаков для long и short - просто проверяем силу тренда
        return df['adx'] >= self.threshold
    
    def get_value(self, row: pd.Series) -> Optional[ADXResult]:
        """
        Получить значения ADX для конкретной строки.
        
        Args:
            row: Строка DataFrame
            
        Returns:
            ADXResult или None
        """
        if 'adx' not in row.index:
            return None
        
        adx = row.get('adx', 0)
        if pd.isna(adx):
            adx = 0
        
        plus_di = row.get('plus_di', 0)
        minus_di = row.get('minus_di', 0)
        
        return ADXResult(
            adx=float(adx),
            plus_di=float(plus_di) if not pd.isna(plus_di) else 0,
            minus_di=float(minus_di) if not pd.isna(minus_di) else 0,
            trending=adx >= self.threshold
        )
    
    def get_trend_strength(self, adx: float) -> str:
        """
        Интерпретация силы тренда по ADX.
        
        Returns:
            'strong', 'moderate', 'weak', или 'no_trend'
        """
        if adx >= 50:
            return 'strong'
        elif adx >= 25:
            return 'moderate'
        elif adx >= 15:
            return 'weak'
        return 'no_trend'
    
    def get_config(self) -> Dict[str, Any]:
        """Получить конфигурацию фильтра"""
        return {
            'name': self.name,
            'enabled': self.enabled,
            'period': self.period,
            'threshold': self.threshold,
        }
    
    def set_config(self, **kwargs):
        """Установить конфигурацию фильтра"""
        if 'period' in kwargs:
            self.period = max(2, kwargs['period'])
        if 'threshold' in kwargs:
            self.threshold = max(10, min(50, kwargs['threshold']))
        if 'enabled' in kwargs:
            self.enabled = kwargs['enabled']
    
    def __repr__(self) -> str:
        status = "ON" if self.enabled else "OFF"
        return f"ADXFilter(period={self.period}, threshold={self.threshold}, {status})"


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    Удобная функция для расчёта ADX.
    
    Совместима с legacy indicator_routes.py API.
    
    Args:
        df: DataFrame с OHLCV данными
        period: Период ADX
        
    Returns:
        DataFrame с добавленной колонкой adx
    """
    filter_obj = ADXFilter(period=period)
    return filter_obj.calculate(df)
