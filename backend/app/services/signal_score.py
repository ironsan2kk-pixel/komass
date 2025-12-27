"""
Signal Score System - KOMAS v4.0
================================

Evaluates trade quality on a 0-100 scale with A-F grades.

Components (4 × 25 = 100 points):
- Confluence (25 pts): Multiple indicators agree on direction
- Multi-TF Alignment (25 pts): Higher timeframes confirm signal
- Market Context (25 pts): Trend strength + volatility conditions
- Technical Levels (25 pts): Distance from support/resistance

Grade Scale:
- A (85-100): Excellent - high probability trade
- B (70-84): Good - solid setup
- C (55-69): Average - acceptable trade
- D (40-54): Below Average - caution advised
- F (0-39): Poor - avoid this trade

Chat #34: Signal Score Core
Chat #35: Multi-TF Integration
Author: KOMAS Team
Version: 4.0
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

# Import MultiTFLoader for enhanced multi-TF analysis
# Import MultiTFLoader with fallback for different contexts
try:
    from .multi_tf_loader import (
        MultiTFLoader,
        TrendDetectionMethod,
        DEFAULT_TF_WEIGHTS,
    )
except ImportError:
    from multi_tf_loader import (
        MultiTFLoader,
        TrendDetectionMethod,
        DEFAULT_TF_WEIGHTS,
    )

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

class Grade(Enum):
    """Signal quality grades"""
    A = "A"  # Excellent (85-100)
    B = "B"  # Good (70-84)
    C = "C"  # Average (55-69)
    D = "D"  # Below Average (40-54)
    F = "F"  # Poor (0-39)


# Grade thresholds
GRADE_THRESHOLDS = {
    Grade.A: 85,
    Grade.B: 70,
    Grade.C: 55,
    Grade.D: 40,
    Grade.F: 0,
}

# Component max points
MAX_CONFLUENCE = 25
MAX_MULTI_TF = 25
MAX_MARKET_CONTEXT = 25
MAX_TECHNICAL_LEVELS = 25

# Default parameters
DEFAULT_PARAMS = {
    # ATR parameters
    'atr_period': 14,
    
    # RSI parameters
    'rsi_period': 14,
    'rsi_overbought': 70,
    'rsi_oversold': 30,
    
    # ADX parameters
    'adx_period': 14,
    'adx_threshold': 25,
    
    # Volume parameters
    'volume_ma_period': 20,
    
    # SuperTrend parameters
    'supertrend_period': 10,
    'supertrend_multiplier': 3.0,
    
    # S/R detection
    'sr_lookback': 50,
    'sr_threshold': 0.02,  # 2% proximity threshold
    
    # Volatility percentile
    'volatility_lookback': 100,
    
    # Trend strength
    'trend_atr_ma_period': 20,
    
    # Multi-TF settings
    'multi_tf_detection_method': 'combined',  # ema, supertrend, adx, combined
    'multi_tf_weights': None,  # Use DEFAULT_TF_WEIGHTS if None
}


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SignalScoreResult:
    """Result of signal score calculation"""
    total_score: int
    grade: str
    components: Dict[str, int]
    details: Dict[str, Any]
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'total_score': self.total_score,
            'grade': self.grade,
            'components': self.components,
            'details': self.details,
            'recommendations': self.recommendations,
        }


@dataclass
class FilterState:
    """State of technical filters for confluence scoring"""
    supertrend_agrees: bool = False
    rsi_agrees: bool = False
    adx_strong: bool = False
    volume_confirms: bool = False
    
    def active_count(self) -> int:
        """Count how many filters are active/enabled"""
        return sum([
            self.supertrend_agrees is not None,
            self.rsi_agrees is not None,
            self.adx_strong is not None,
            self.volume_confirms is not None,
        ])


# =============================================================================
# TECHNICAL INDICATOR CALCULATIONS
# =============================================================================

def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range
    
    Args:
        df: DataFrame with high, low, close columns
        period: ATR period
        
    Returns:
        ATR series
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period, min_periods=1).mean()
    
    return atr


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index
    
    Args:
        df: DataFrame with close column
        period: RSI period
        
    Returns:
        RSI series (0-100)
    """
    delta = df['close'].diff()
    
    gain = delta.where(delta > 0, 0)
    loss = (-delta).where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period, min_periods=1).mean()
    avg_loss = loss.rolling(window=period, min_periods=1).mean()
    
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.fillna(50)


def calculate_adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average Directional Index
    
    Args:
        df: DataFrame with high, low, close columns
        period: ADX period
        
    Returns:
        ADX series
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # True Range
    tr = pd.concat([
        high - low,
        abs(high - close.shift(1)),
        abs(low - close.shift(1))
    ], axis=1).max(axis=1)
    
    # Directional Movement
    plus_dm = high.diff()
    minus_dm = -low.diff()
    
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    
    # Smoothed TR and DM
    atr = tr.rolling(window=period, min_periods=1).mean()
    plus_di = 100 * (plus_dm.rolling(window=period, min_periods=1).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period, min_periods=1).mean() / atr)
    
    # DX and ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.rolling(window=period, min_periods=1).mean()
    
    return adx.fillna(0)


def calculate_supertrend(
    df: pd.DataFrame,
    period: int = 10,
    multiplier: float = 3.0
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate SuperTrend indicator
    
    Args:
        df: DataFrame with high, low, close columns
        period: ATR period
        multiplier: ATR multiplier
        
    Returns:
        Tuple of (supertrend_direction, supertrend_line)
        direction: 1 for uptrend, -1 for downtrend
    """
    hl2 = (df['high'] + df['low']) / 2
    atr = calculate_atr(df, period)
    
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    supertrend = pd.Series(index=df.index, dtype=float)
    direction = pd.Series(index=df.index, dtype=int)
    
    close = df['close']
    
    for i in range(len(df)):
        if i == 0:
            supertrend.iloc[i] = lower_band.iloc[i]
            direction.iloc[i] = 1
            continue
            
        if close.iloc[i] > supertrend.iloc[i-1]:
            supertrend.iloc[i] = max(lower_band.iloc[i], supertrend.iloc[i-1])
            direction.iloc[i] = 1
        else:
            supertrend.iloc[i] = min(upper_band.iloc[i], supertrend.iloc[i-1])
            direction.iloc[i] = -1
    
    return direction, supertrend


def calculate_support_resistance(
    df: pd.DataFrame,
    lookback: int = 50
) -> Tuple[float, float]:
    """
    Calculate support and resistance levels using pivot points
    
    Args:
        df: DataFrame with high, low, close columns
        lookback: Number of bars to look back
        
    Returns:
        Tuple of (support, resistance)
    """
    recent = df.tail(lookback)
    
    if len(recent) < 5:
        return recent['low'].min(), recent['high'].max()
    
    # Find local minima for support
    lows = recent['low'].values
    support_levels = []
    for i in range(2, len(lows) - 2):
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
           lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            support_levels.append(lows[i])
    
    # Find local maxima for resistance
    highs = recent['high'].values
    resistance_levels = []
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
           highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            resistance_levels.append(highs[i])
    
    # Get the most recent support/resistance
    current_price = df['close'].iloc[-1]
    
    # Support: highest level below current price
    support = max([s for s in support_levels if s < current_price], default=recent['low'].min())
    
    # Resistance: lowest level above current price
    resistance = min([r for r in resistance_levels if r > current_price], default=recent['high'].max())
    
    return support, resistance


def calculate_volatility_percentile(
    df: pd.DataFrame,
    atr_period: int = 14,
    lookback: int = 100
) -> float:
    """
    Calculate current volatility percentile compared to recent history
    
    Args:
        df: DataFrame with OHLC data
        atr_period: ATR calculation period
        lookback: Number of bars for percentile calculation
        
    Returns:
        Percentile value (0-100)
    """
    atr = calculate_atr(df, atr_period)
    
    if len(atr) < lookback:
        lookback = len(atr)
    
    recent_atr = atr.tail(lookback)
    current_atr = atr.iloc[-1]
    
    percentile = (recent_atr < current_atr).sum() / len(recent_atr) * 100
    
    return round(percentile, 1)


# =============================================================================
# SIGNAL SCORER CLASS
# =============================================================================

class SignalScorer:
    """
    Evaluates trade quality on a 0-100 scale with A-F grades.
    
    Usage:
        scorer = SignalScorer()
        result = scorer.calculate_score(
            df=ohlcv_data,
            direction='long',
            entry_price=45000,
            filters=filter_config
        )
        print(f"Score: {result.total_score} ({result.grade})")
    """
    
    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Initialize SignalScorer with optional custom parameters
        
        Args:
            params: Custom parameters to override defaults
        """
        self.params = {**DEFAULT_PARAMS}
        if params:
            self.params.update(params)
        
        # Initialize MultiTFLoader with configured settings
        detection_method_str = self.params.get('multi_tf_detection_method', 'combined')
        detection_method = TrendDetectionMethod(detection_method_str)
        
        tf_weights = self.params.get('multi_tf_weights') or DEFAULT_TF_WEIGHTS
        
        self.multi_tf_loader = MultiTFLoader(
            tf_weights=tf_weights,
            detection_method=detection_method,
        )
        
        logger.info(f"SignalScorer initialized with params: {self.params}")
    
    def calculate_score(
        self,
        df: pd.DataFrame,
        direction: str,
        entry_price: float,
        filters: Optional[Dict[str, Any]] = None,
        higher_tf_data: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> SignalScoreResult:
        """
        Calculate comprehensive signal score
        
        Args:
            df: OHLCV DataFrame for the trading timeframe
            direction: 'long' or 'short'
            entry_price: Entry price for the trade
            filters: Filter configuration (enabled filters and their params)
            higher_tf_data: Optional dict of higher TF DataFrames {'4h': df_4h, '1d': df_1d}
            
        Returns:
            SignalScoreResult with total score, grade, and component breakdown
        """
        if len(df) < 20:
            return SignalScoreResult(
                total_score=0,
                grade=Grade.F.value,
                components={
                    'confluence': 0,
                    'multi_tf': 0,
                    'market_context': 0,
                    'technical_levels': 0,
                },
                details={'error': 'Insufficient data'},
                recommendations=['Need at least 20 candles for scoring'],
            )
        
        direction = direction.lower()
        if direction not in ('long', 'short'):
            direction = 'long' if direction == '1' else 'short'
        
        # Calculate each component
        confluence_score, confluence_details = self._calculate_confluence(
            df, direction, filters
        )
        
        multi_tf_score, multi_tf_details = self._calculate_multi_tf(
            df, direction, higher_tf_data
        )
        
        context_score, context_details = self._calculate_market_context(df)
        
        levels_score, levels_details = self._calculate_technical_levels(
            df, direction, entry_price
        )
        
        # Total score
        total_score = confluence_score + multi_tf_score + context_score + levels_score
        total_score = min(100, max(0, total_score))
        
        # Determine grade
        grade = self._get_grade(total_score)
        
        # Compile details
        details = {
            'confluence': confluence_details,
            'multi_tf': multi_tf_details,
            'market_context': context_details,
            'technical_levels': levels_details,
        }
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            total_score, grade,
            confluence_score, multi_tf_score, context_score, levels_score,
            details
        )
        
        result = SignalScoreResult(
            total_score=round(total_score),
            grade=grade.value,
            components={
                'confluence': round(confluence_score),
                'multi_tf': round(multi_tf_score),
                'market_context': round(context_score),
                'technical_levels': round(levels_score),
            },
            details=details,
            recommendations=recommendations,
        )
        
        logger.debug(f"Signal score calculated: {total_score} ({grade.value})")
        
        return result
    
    def _calculate_confluence(
        self,
        df: pd.DataFrame,
        direction: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Confluence score (max 25 pts)
        
        Measures agreement between multiple technical indicators.
        
        Args:
            df: OHLCV DataFrame
            direction: 'long' or 'short'
            filters: Filter configuration
            
        Returns:
            Tuple of (score, details)
        """
        filters = filters or {}
        
        # Calculate indicators
        rsi = calculate_rsi(df, self.params['rsi_period'])
        adx = calculate_adx(df, self.params['adx_period'])
        st_direction, _ = calculate_supertrend(
            df, 
            self.params['supertrend_period'],
            self.params['supertrend_multiplier']
        )
        
        current_rsi = rsi.iloc[-1]
        current_adx = adx.iloc[-1]
        current_st = st_direction.iloc[-1]
        
        # Volume check
        volume = df['volume']
        volume_ma = volume.rolling(window=self.params['volume_ma_period'], min_periods=1).mean()
        current_volume = volume.iloc[-1]
        current_volume_ma = volume_ma.iloc[-1]
        
        # Check filter agreement
        filter_state = FilterState()
        
        # SuperTrend agreement
        if direction == 'long':
            filter_state.supertrend_agrees = current_st == 1
        else:
            filter_state.supertrend_agrees = current_st == -1
        
        # RSI agreement (not overbought for longs, not oversold for shorts)
        if direction == 'long':
            filter_state.rsi_agrees = current_rsi < self.params['rsi_overbought']
        else:
            filter_state.rsi_agrees = current_rsi > self.params['rsi_oversold']
        
        # ADX strength
        filter_state.adx_strong = current_adx > self.params['adx_threshold']
        
        # Volume confirmation
        filter_state.volume_confirms = current_volume > current_volume_ma
        
        # Calculate score based on enabled filters
        enabled_filters = []
        
        if filters.get('supertrend_enabled', True):
            enabled_filters.append(('supertrend', filter_state.supertrend_agrees))
        if filters.get('rsi_enabled', True):
            enabled_filters.append(('rsi', filter_state.rsi_agrees))
        if filters.get('adx_enabled', True):
            enabled_filters.append(('adx', filter_state.adx_strong))
        if filters.get('volume_enabled', True):
            enabled_filters.append(('volume', filter_state.volume_confirms))
        
        # If no filters enabled, use all
        if not enabled_filters:
            enabled_filters = [
                ('supertrend', filter_state.supertrend_agrees),
                ('rsi', filter_state.rsi_agrees),
                ('adx', filter_state.adx_strong),
                ('volume', filter_state.volume_confirms),
            ]
        
        # Calculate score
        agreements = sum(1 for _, agrees in enabled_filters if agrees)
        num_filters = len(enabled_filters)
        
        if num_filters > 0:
            score = (agreements / num_filters) * MAX_CONFLUENCE
        else:
            score = 0
        
        details = {
            'supertrend_agrees': filter_state.supertrend_agrees,
            'supertrend_direction': int(current_st),
            'rsi_agrees': filter_state.rsi_agrees,
            'rsi_value': round(current_rsi, 1),
            'adx_strong': filter_state.adx_strong,
            'adx_value': round(current_adx, 1),
            'volume_confirms': filter_state.volume_confirms,
            'volume_ratio': round(current_volume / current_volume_ma, 2) if current_volume_ma > 0 else 0,
            'agreements': agreements,
            'total_filters': num_filters,
        }
        
        return score, details
    
    def _calculate_multi_tf(
        self,
        df: pd.DataFrame,
        direction: str,
        higher_tf_data: Optional[Dict[str, pd.DataFrame]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Multi-TF Alignment score (max 25 pts)
        
        Uses MultiTFLoader for enhanced trend detection with multiple methods.
        
        Args:
            df: OHLCV DataFrame for trading timeframe
            direction: 'long' or 'short'
            higher_tf_data: Dict of higher TF DataFrames {'4h': df_4h, '1d': df_1d}
            
        Returns:
            Tuple of (score, details)
        """
        higher_tf_data = higher_tf_data or {}
        
        # Use MultiTFLoader for analysis
        score, details = self.multi_tf_loader.calculate_score_sync(
            signal_direction=direction,
            higher_tf_data=higher_tf_data,
        )
        
        return score, details
    
    def _calculate_market_context(
        self,
        df: pd.DataFrame
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Market Context score (max 25 pts)
        
        Evaluates trend strength and volatility conditions.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            Tuple of (score, details)
        """
        # Trend strength (0-15 pts)
        atr = calculate_atr(df, self.params['atr_period'])
        atr_ma = atr.rolling(window=self.params['trend_atr_ma_period'], min_periods=1).mean()
        
        current_atr = atr.iloc[-1]
        current_atr_ma = atr_ma.iloc[-1]
        
        if current_atr_ma > 0:
            atr_normalized = current_atr / current_atr_ma
        else:
            atr_normalized = 1.0
        
        if atr_normalized > 1.2:
            trend_score = 15  # Strong trend
            trend_status = 'strong'
        elif atr_normalized > 0.8:
            trend_score = 10  # Normal trend
            trend_status = 'normal'
        else:
            trend_score = 5   # Weak trend
            trend_status = 'weak'
        
        # Volatility regime (0-10 pts)
        volatility_percentile = calculate_volatility_percentile(
            df, 
            self.params['atr_period'],
            self.params['volatility_lookback']
        )
        
        if 30 <= volatility_percentile <= 70:
            vol_score = 10  # Normal volatility (optimal)
            vol_status = 'normal'
        elif 20 <= volatility_percentile <= 80:
            vol_score = 7   # Moderate volatility
            vol_status = 'moderate'
        else:
            vol_score = 3   # Extreme volatility (suboptimal)
            vol_status = 'extreme'
        
        score = trend_score + vol_score
        
        details = {
            'trend_strength': trend_status,
            'trend_score': trend_score,
            'atr_normalized': round(atr_normalized, 2),
            'volatility_status': vol_status,
            'volatility_score': vol_score,
            'volatility_percentile': volatility_percentile,
        }
        
        return score, details
    
    def _calculate_technical_levels(
        self,
        df: pd.DataFrame,
        direction: str,
        entry_price: float
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate Technical Levels score (max 25 pts)
        
        Evaluates proximity to support/resistance levels.
        
        Args:
            df: OHLCV DataFrame
            direction: 'long' or 'short'
            entry_price: Entry price for the trade
            
        Returns:
            Tuple of (score, details)
        """
        support, resistance = calculate_support_resistance(
            df, self.params['sr_lookback']
        )
        
        # Calculate distances as percentages
        dist_to_support = (entry_price - support) / entry_price if entry_price > 0 else 0
        dist_to_resistance = (resistance - entry_price) / entry_price if entry_price > 0 else 0
        
        # Score based on position relative to S/R
        if direction == 'long':
            # For longs: good if near support, far from resistance
            if dist_to_support < 0.02:  # Within 2% of support
                score = 25
                level_status = 'excellent_entry'
            elif dist_to_support < 0.05:  # Within 5% of support
                score = 20
                level_status = 'good_entry'
            elif dist_to_support < 0.10:  # Within 10% of support
                score = 15
                level_status = 'acceptable_entry'
            else:
                score = max(0, 25 - dist_to_support * 100)
                level_status = 'far_from_support'
            
            # Penalty if close to resistance (risk of reversal)
            if dist_to_resistance < 0.02:
                score = max(0, score - 5)  # Penalty for being near resistance
                level_status = 'near_resistance_risk'
        else:
            # For shorts: good if near resistance, far from support
            if dist_to_resistance < 0.02:  # Within 2% of resistance
                score = 25
                level_status = 'excellent_entry'
            elif dist_to_resistance < 0.05:  # Within 5% of resistance
                score = 20
                level_status = 'good_entry'
            elif dist_to_resistance < 0.10:  # Within 10% of resistance
                score = 15
                level_status = 'acceptable_entry'
            else:
                score = max(0, 25 - dist_to_resistance * 100)
                level_status = 'far_from_resistance'
            
            # Penalty if close to support (risk of bounce)
            if dist_to_support < 0.02:
                score = max(0, score - 5)
                level_status = 'near_support_risk'
        
        details = {
            'support': round(support, 2),
            'resistance': round(resistance, 2),
            'entry_price': round(entry_price, 2),
            'dist_to_support_pct': round(dist_to_support * 100, 2),
            'dist_to_resistance_pct': round(dist_to_resistance * 100, 2),
            'level_status': level_status,
        }
        
        return score, details
    
    def _get_grade(self, score: float) -> Grade:
        """Get grade based on score"""
        if score >= GRADE_THRESHOLDS[Grade.A]:
            return Grade.A
        elif score >= GRADE_THRESHOLDS[Grade.B]:
            return Grade.B
        elif score >= GRADE_THRESHOLDS[Grade.C]:
            return Grade.C
        elif score >= GRADE_THRESHOLDS[Grade.D]:
            return Grade.D
        else:
            return Grade.F
    
    def _generate_recommendations(
        self,
        total_score: float,
        grade: Grade,
        confluence_score: float,
        multi_tf_score: float,
        context_score: float,
        levels_score: float,
        details: Dict[str, Any],
    ) -> List[str]:
        """Generate recommendations based on score analysis"""
        recommendations = []
        
        # Overall grade recommendations
        if grade == Grade.A:
            recommendations.append("High quality setup - proceed with standard position size")
        elif grade == Grade.B:
            recommendations.append("Good setup - consider position sizing")
        elif grade == Grade.C:
            recommendations.append("Average setup - consider reduced position size")
        elif grade == Grade.D:
            recommendations.append("Below average - proceed with caution")
        else:
            recommendations.append("Poor setup - consider skipping this trade")
        
        # Specific component recommendations
        if confluence_score < 15:
            recommendations.append("Low confluence - multiple indicators disagree")
        
        if multi_tf_score < 15:
            multi_tf_details = details.get('multi_tf', {})
            misalignments = multi_tf_details.get('misalignments', [])
            if misalignments:
                recommendations.append(f"Weak multi-TF alignment - {', '.join(misalignments)} not confirming")
            else:
                recommendations.append("Weak multi-TF alignment - higher TFs not confirming")
        
        if context_score < 15:
            context_details = details.get('market_context', {})
            if context_details.get('volatility_status') == 'extreme':
                recommendations.append("Extreme volatility - consider wider stops")
            if context_details.get('trend_strength') == 'weak':
                recommendations.append("Weak trend - momentum may be lacking")
        
        if levels_score < 15:
            levels_details = details.get('technical_levels', {})
            status = levels_details.get('level_status', '')
            if 'resistance_risk' in status or 'support_risk' in status:
                recommendations.append("Price near key level - potential reversal zone")
        
        return recommendations


# =============================================================================
# BATCH SCORING
# =============================================================================

def score_trades(
    trades: List[Dict[str, Any]],
    df: pd.DataFrame,
    filters: Optional[Dict[str, Any]] = None,
    higher_tf_data: Optional[Dict[str, pd.DataFrame]] = None,
) -> List[Dict[str, Any]]:
    """
    Score a batch of trades
    
    Args:
        trades: List of trade dictionaries with 'direction', 'entry_price', 'entry_idx'
        df: Full OHLCV DataFrame
        filters: Filter configuration
        higher_tf_data: Higher timeframe data
        
    Returns:
        List of trades with 'signal_score' and 'signal_grade' added
    """
    scorer = SignalScorer()
    scored_trades = []
    
    for trade in trades:
        trade_copy = trade.copy()
        
        # Get data up to entry point
        entry_idx = trade.get('entry_idx', len(df) - 1)
        if isinstance(entry_idx, (int, float)) and entry_idx > 0:
            df_to_entry = df.iloc[:int(entry_idx) + 1].copy()
        else:
            df_to_entry = df.copy()
        
        direction = trade.get('direction', 'long')
        if isinstance(direction, int):
            direction = 'long' if direction == 1 else 'short'
        direction = str(direction).lower()
        
        entry_price = trade.get('entry_price', df_to_entry['close'].iloc[-1])
        
        # Calculate score
        result = scorer.calculate_score(
            df=df_to_entry,
            direction=direction,
            entry_price=entry_price,
            filters=filters,
            higher_tf_data=higher_tf_data,
        )
        
        # Add score to trade
        trade_copy['signal_score'] = result.total_score
        trade_copy['signal_grade'] = result.grade
        trade_copy['score_components'] = result.components
        
        scored_trades.append(trade_copy)
    
    return scored_trades


def get_grade_from_score(score: int) -> str:
    """Get grade letter from numeric score"""
    if score >= 85:
        return 'A'
    elif score >= 70:
        return 'B'
    elif score >= 55:
        return 'C'
    elif score >= 40:
        return 'D'
    else:
        return 'F'


def get_grade_color(grade: str) -> str:
    """Get color for grade (for UI display)"""
    colors = {
        'A': '#22c55e',  # Green
        'B': '#84cc16',  # Lime
        'C': '#eab308',  # Yellow
        'D': '#f97316',  # Orange
        'F': '#ef4444',  # Red
    }
    return colors.get(grade, '#6b7280')


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'SignalScorer',
    'SignalScoreResult',
    'Grade',
    'score_trades',
    'get_grade_from_score',
    'get_grade_color',
    'calculate_atr',
    'calculate_rsi',
    'calculate_adx',
    'calculate_supertrend',
    'calculate_support_resistance',
    'calculate_volatility_percentile',
    'GRADE_THRESHOLDS',
    'MAX_CONFLUENCE',
    'MAX_MULTI_TF',
    'MAX_MARKET_CONTEXT',
    'MAX_TECHNICAL_LEVELS',
]
