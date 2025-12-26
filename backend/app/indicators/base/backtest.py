"""
Komas Trading System - Base Backtest
====================================
Abstract base class for backtesting engine.
Runs historical simulation with indicators and trading system.

Version: 1.0
Author: Komas Team
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import numpy as np

from .indicator import BaseIndicator, IndicatorResult
from .trading import (
    BaseTradingSystem, TradingConfig, Position, Trade,
    PositionType, ExitReason
)
from .filter import BaseFilter, FilterChain, FilterResult


@dataclass
class BacktestConfig:
    """
    Backtest configuration.
    """
    # Data range
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    
    # Capital
    initial_capital: float = 10000.0
    
    # Trading settings (passed to TradingSystem)
    trading_config: Optional[TradingConfig] = None
    
    # Statistics
    calculate_monthly: bool = True
    calculate_tp_stats: bool = True
    
    # Adaptive mode
    adaptive_mode: Optional[str] = None  # "indicator", "tp", "all"
    reoptimize_every: int = 20  # Trades
    lookback_candles: int = 500
    
    def to_dict(self) -> Dict:
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "initial_capital": self.initial_capital,
            "trading_config": self.trading_config.to_dict() if self.trading_config else None,
            "calculate_monthly": self.calculate_monthly,
            "adaptive_mode": self.adaptive_mode
        }


@dataclass
class MonthlyStats:
    """
    Monthly performance statistics.
    """
    month: str
    trades: int = 0
    wins: int = 0
    losses: int = 0
    pnl: float = 0.0
    pnl_amount: float = 0.0
    long_trades: int = 0
    short_trades: int = 0
    tp_hits: Dict[str, int] = field(default_factory=dict)
    
    @property
    def win_rate(self) -> float:
        return (self.wins / self.trades * 100) if self.trades > 0 else 0
    
    def to_dict(self) -> Dict:
        return {
            "month": self.month,
            "trades": self.trades,
            "wins": self.wins,
            "losses": self.losses,
            "win_rate": round(self.win_rate, 2),
            "pnl": round(self.pnl, 2),
            "pnl_amount": round(self.pnl_amount, 2),
            "long_trades": self.long_trades,
            "short_trades": self.short_trades,
            "tp_hits": self.tp_hits
        }


@dataclass
class TPStats:
    """
    Take profit statistics.
    """
    tp_hits: Dict[str, int] = field(default_factory=dict)
    total_trades: int = 0
    
    def get_hit_rate(self, tp_level: int) -> float:
        """Get hit rate for specific TP level"""
        hits = self.tp_hits.get(f"tp{tp_level}_hits", 0)
        return (hits / self.total_trades * 100) if self.total_trades > 0 else 0
    
    def to_dict(self) -> Dict:
        result = {k: v for k, v in self.tp_hits.items()}
        result["total_trades"] = self.total_trades
        return result


@dataclass
class BacktestResult:
    """
    Complete backtest result.
    """
    # Core results
    trades: List[Dict] = field(default_factory=list)
    equity_curve: List[Dict] = field(default_factory=list)
    
    # Statistics
    stats: Dict[str, Any] = field(default_factory=dict)
    monthly_stats: Dict[str, MonthlyStats] = field(default_factory=dict)
    tp_stats: Optional[TPStats] = None
    
    # Indicator data for chart
    candles: List[Dict] = field(default_factory=list)
    indicators: Dict[str, List[Dict]] = field(default_factory=dict)
    trade_markers: List[Dict] = field(default_factory=list)
    
    # Adaptive optimization
    param_changes: List[Dict] = field(default_factory=list)
    
    # Meta
    config: Optional[BacktestConfig] = None
    duration_seconds: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "trades": self.trades,
            "equity_curve": self.equity_curve,
            "stats": self.stats,
            "monthly": {k: v.to_dict() for k, v in self.monthly_stats.items()},
            "tp_stats": self.tp_stats.to_dict() if self.tp_stats else None,
            "candles": self.candles,
            "indicators": self.indicators,
            "trade_markers": self.trade_markers,
            "param_changes": self.param_changes,
            "config": self.config.to_dict() if self.config else None,
            "duration_seconds": round(self.duration_seconds, 2)
        }


class BaseBacktest(ABC):
    """
    Abstract base class for backtesting engine.
    
    Subclasses must implement:
    - create_indicator(): Create indicator instance
    - create_trading_system(): Create trading system instance
    - create_filters(): Create filter chain
    
    Optional overrides:
    - pre_process(): Pre-process data before backtest
    - post_process(): Post-process results
    - on_bar(): Custom logic for each bar
    """
    
    def __init__(self, config: Optional[BacktestConfig] = None):
        self.config = config or BacktestConfig()
        
        # Components (created by subclasses)
        self.indicator: Optional[BaseIndicator] = None
        self.trading_system: Optional[BaseTradingSystem] = None
        self.filter_chain: Optional[FilterChain] = None
        
        # Results
        self.result: Optional[BacktestResult] = None
        
        # Internal state
        self._df: Optional[pd.DataFrame] = None
        self._monthly_stats: Dict[str, MonthlyStats] = {}
        self._tp_stats: TPStats = TPStats()
    
    # ==================== ABSTRACT METHODS ====================
    
    @abstractmethod
    def create_indicator(self, params: Dict[str, Any]) -> BaseIndicator:
        """
        Create indicator instance with given parameters.
        
        Args:
            params: Indicator parameters
        
        Returns:
            Configured indicator instance
        """
        pass
    
    @abstractmethod
    def create_trading_system(self, config: TradingConfig) -> BaseTradingSystem:
        """
        Create trading system instance.
        
        Args:
            config: Trading configuration
        
        Returns:
            Configured trading system instance
        """
        pass
    
    @abstractmethod
    def create_filters(self, params: Dict[str, Any]) -> FilterChain:
        """
        Create filter chain with given parameters.
        
        Args:
            params: Filter parameters
        
        Returns:
            Configured filter chain
        """
        pass
    
    # ==================== OPTIONAL OVERRIDES ====================
    
    def pre_process(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pre-process data before backtest.
        Override for custom data preparation.
        """
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Sort by time
        df = df.sort_index()
        
        return df
    
    def post_process(self, result: BacktestResult) -> BacktestResult:
        """
        Post-process results after backtest.
        Override for custom result processing.
        """
        return result
    
    def on_bar(self, index: int, bar: pd.Series, timestamp: datetime) -> None:
        """
        Called for each bar during backtest.
        Override for custom per-bar logic.
        """
        pass
    
    # ==================== PUBLIC API ====================
    
    def run(
        self,
        df: pd.DataFrame,
        indicator_params: Optional[Dict[str, Any]] = None,
        filter_params: Optional[Dict[str, Any]] = None
    ) -> BacktestResult:
        """
        Run complete backtest.
        
        Args:
            df: OHLCV DataFrame
            indicator_params: Indicator parameters
            filter_params: Filter parameters
        
        Returns:
            BacktestResult with all data
        """
        start_time = datetime.now()
        
        # Initialize result
        self.result = BacktestResult(config=self.config)
        self._monthly_stats = {}
        self._tp_stats = TPStats()
        
        # Pre-process data
        df = self.pre_process(df.copy())
        
        # Apply date filters
        if self.config.start_date:
            df = df[df.index >= self.config.start_date]
        if self.config.end_date:
            df = df[df.index <= self.config.end_date]
        
        if len(df) < 100:
            raise ValueError("Not enough data (need at least 100 candles)")
        
        self._df = df
        
        # Create components
        self.indicator = self.create_indicator(indicator_params or {})
        
        trading_config = self.config.trading_config or TradingConfig(
            initial_capital=self.config.initial_capital
        )
        self.trading_system = self.create_trading_system(trading_config)
        self.filter_chain = self.create_filters(filter_params or {})
        
        # Calculate indicator
        df = self.indicator.calculate(df)
        df = self.indicator.generate_signals(df)
        
        # Apply filters
        if self.filter_chain:
            df = self.filter_chain.calculate_all(df)
        
        # Store processed data
        self._df = df
        
        # Run backtest loop
        self._run_backtest_loop(df)
        
        # Collect results
        self._collect_results(df)
        
        # Post-process
        self.result = self.post_process(self.result)
        
        # Duration
        self.result.duration_seconds = (datetime.now() - start_time).total_seconds()
        
        return self.result
    
    def _run_backtest_loop(self, df: pd.DataFrame) -> None:
        """Run main backtest loop"""
        warmup = self.indicator.warmup_period() if self.indicator else 50
        
        for i in range(warmup, len(df)):
            timestamp = df.index[i]
            bar = df.iloc[i]
            
            # Get signal and trend
            signal = int(bar.get('signal', 0))
            trend = int(bar.get('trend', bar.get('trg_trend', 0)))
            
            # Apply filters
            if signal != 0 and self.filter_chain:
                allowed, outputs = self.filter_chain.check_signal(i, signal)
                if not allowed:
                    signal = 0
            
            # Update monthly stats
            if self.config.calculate_monthly:
                self._update_monthly_stats(timestamp)
            
            # Process bar in trading system
            self._process_bar(bar, timestamp, signal, trend)
            
            # Custom callback
            self.on_bar(i, bar, timestamp)
    
    def _process_bar(
        self,
        bar: pd.Series,
        timestamp: datetime,
        signal: int,
        trend: int
    ) -> None:
        """Process single bar through trading system"""
        ts = self.trading_system
        if not ts:
            return
        
        high = bar['high']
        low = bar['low']
        close = bar['close']
        
        position = ts.position
        
        # Update existing position
        if position:
            # Update price tracking
            ts.update_price_tracking(position, high, low)
            
            # Check TP hits
            ts.check_tp_hit(position, high, low, timestamp)
            
            # Check SL
            sl_hit = ts.check_sl_hit(position, high, low)
            
            # Check reverse signal
            reverse = False
            if signal != 0:
                if (position.type == PositionType.LONG and signal == -1) or \
                   (position.type == PositionType.SHORT and signal == 1):
                    reverse = True
            
            # Close if needed
            all_tp_closed = position.remaining_percent <= 0.01
            
            if all_tp_closed or sl_hit or reverse:
                if sl_hit:
                    exit_price = position.sl_price
                    exit_reason = ExitReason.STOP_LOSS
                elif all_tp_closed:
                    exit_price = position.tp_levels[-1].price if position.tp_levels else close
                    tp_count = len([tp for tp in position.tp_levels if tp.hit])
                    exit_reason = getattr(ExitReason, f"TP{tp_count}", ExitReason.TP4)
                else:
                    exit_price = close
                    exit_reason = ExitReason.REVERSE
                
                trade = ts.close_position(exit_price, timestamp, exit_reason)
                
                # Update stats
                self._update_trade_stats(trade, timestamp)
        
        # Check for new entry
        if ts.position is None and signal != 0:
            pos_type = PositionType.LONG if signal == 1 else PositionType.SHORT
            
            # Check re-entry rules
            should_enter = True
            is_reentry = False
            
            config = ts.config
            if ts.last_exit_reason:
                if ts.last_exit_reason == ExitReason.STOP_LOSS:
                    is_reentry = config.reentry_after_sl
                    should_enter = config.allow_reentry and config.reentry_after_sl
                elif ts.last_exit_reason in [ExitReason.TP1, ExitReason.TP2, ExitReason.TP3, ExitReason.TP4]:
                    is_reentry = config.reentry_after_tp
                    should_enter = config.allow_reentry and config.reentry_after_tp
            
            if should_enter:
                ts.open_position(
                    pos_type,
                    close,
                    timestamp,
                    is_reentry=is_reentry,
                    params_used=self.indicator.get_all_params() if self.indicator else {}
                )
    
    def _update_monthly_stats(self, timestamp: datetime) -> None:
        """Update or initialize monthly stats"""
        month_key = timestamp.strftime("%Y-%m")
        
        if month_key not in self._monthly_stats:
            self._monthly_stats[month_key] = MonthlyStats(month=month_key)
    
    def _update_trade_stats(self, trade: Trade, timestamp: datetime) -> None:
        """Update statistics after trade closes"""
        month_key = timestamp.strftime("%Y-%m")
        
        # Monthly stats
        if month_key in self._monthly_stats:
            stats = self._monthly_stats[month_key]
            stats.trades += 1
            stats.pnl += trade.pnl
            stats.pnl_amount += trade.pnl_amount
            
            if trade.pnl > 0:
                stats.wins += 1
            else:
                stats.losses += 1
            
            if trade.type == "long":
                stats.long_trades += 1
            else:
                stats.short_trades += 1
            
            # TP hits
            for tp_num in trade.tp_hit:
                key = f"tp{tp_num}_hits"
                stats.tp_hits[key] = stats.tp_hits.get(key, 0) + 1
        
        # Global TP stats
        if self.config.calculate_tp_stats:
            self._tp_stats.total_trades += 1
            for tp_num in trade.tp_hit:
                key = f"tp{tp_num}_hits"
                self._tp_stats.tp_hits[key] = self._tp_stats.tp_hits.get(key, 0) + 1
    
    def _collect_results(self, df: pd.DataFrame) -> None:
        """Collect all results into BacktestResult"""
        ts = self.trading_system
        
        if ts:
            self.result.trades = ts.get_trades()
            self.result.equity_curve = ts.get_equity_curve()
            self.result.stats = ts.get_statistics()
        
        # Monthly stats
        self.result.monthly_stats = self._monthly_stats
        
        # TP stats
        if self.config.calculate_tp_stats:
            self.result.tp_stats = self._tp_stats
        
        # Prepare chart data
        self.result.candles = self._prepare_candles(df)
        self.result.indicators = self._prepare_indicators(df)
        self.result.trade_markers = self._prepare_trade_markers()
    
    def _prepare_candles(self, df: pd.DataFrame) -> List[Dict]:
        """Prepare candle data for chart"""
        candles = []
        seen_times = set()
        
        for timestamp, row in df.iterrows():
            time_val = int(timestamp.timestamp())
            
            if time_val in seen_times:
                continue
            seen_times.add(time_val)
            
            candles.append({
                "time": time_val,
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": float(row.get('volume', 0))
            })
        
        candles.sort(key=lambda x: x['time'])
        return candles
    
    def _prepare_indicators(self, df: pd.DataFrame) -> Dict[str, List[Dict]]:
        """Prepare indicator data for chart"""
        indicators = {}
        
        # Get output columns from indicator
        if self.indicator:
            for col in self.indicator.get_output_columns():
                if col in df.columns:
                    data = []
                    seen_times = set()
                    
                    for timestamp, row in df.iterrows():
                        time_val = int(timestamp.timestamp())
                        
                        if time_val in seen_times:
                            continue
                        seen_times.add(time_val)
                        
                        value = row.get(col)
                        if pd.notna(value):
                            data.append({
                                "time": time_val,
                                "value": float(value)
                            })
                    
                    data.sort(key=lambda x: x['time'])
                    indicators[col] = data
        
        return indicators
    
    def _prepare_trade_markers(self) -> List[Dict]:
        """Prepare trade markers for chart"""
        markers = []
        
        for trade in self.result.trades:
            entry_time = int(datetime.fromisoformat(trade['entry_time']).timestamp())
            exit_time = int(datetime.fromisoformat(trade['exit_time']).timestamp())
            is_reentry = trade.get('is_reentry', False)
            
            # Entry marker
            entry_text = trade['type'].upper()
            if is_reentry:
                entry_text = f"RE-{entry_text}"
            
            markers.append({
                "time": entry_time,
                "position": "belowBar" if trade['type'] == 'long' else "aboveBar",
                "color": "#fbbf24" if is_reentry else ("#22c55e" if trade['type'] == 'long' else "#ef4444"),
                "shape": "arrowUp" if trade['type'] == 'long' else "arrowDown",
                "text": entry_text
            })
            
            # Exit marker
            markers.append({
                "time": exit_time,
                "position": "aboveBar" if trade['type'] == 'long' else "belowBar",
                "color": "#22c55e" if trade['pnl'] > 0 else "#ef4444",
                "shape": "circle",
                "text": f"{trade['pnl']:+.1f}%"
            })
        
        markers.sort(key=lambda x: x['time'])
        return markers
    
    # ==================== UTILITIES ====================
    
    def get_trades(self) -> List[Dict]:
        """Get trades from result"""
        return self.result.trades if self.result else []
    
    def get_equity_curve(self) -> List[Dict]:
        """Get equity curve from result"""
        return self.result.equity_curve if self.result else []
    
    def get_stats(self) -> Dict:
        """Get statistics from result"""
        return self.result.stats if self.result else {}
    
    def get_monthly_stats(self) -> Dict[str, Dict]:
        """Get monthly statistics"""
        if not self.result:
            return {}
        return {k: v.to_dict() for k, v in self.result.monthly_stats.items()}


# ==================== SIMPLE TRADING SYSTEM IMPLEMENTATION ====================

class SimpleTradingSystem(BaseTradingSystem):
    """
    Simple trading system implementation.
    Uses signals from indicator directly.
    """
    
    def process_bar(self, bar: pd.Series, timestamp: datetime, signal: int, trend: int) -> None:
        """Process single price bar"""
        # This is handled by BaseBacktest._process_bar
        pass
    
    def should_open_position(self, bar: pd.Series, signal: int, trend: int) -> Optional[PositionType]:
        """Check if should open position"""
        if signal == 1:
            return PositionType.LONG
        elif signal == -1:
            return PositionType.SHORT
        return None
    
    def should_close_position(self, bar: pd.Series, signal: int, trend: int) -> Optional[ExitReason]:
        """Check if should close position"""
        if not self.position:
            return None
        
        # Check reverse signal
        if signal != 0:
            if (self.position.type == PositionType.LONG and signal == -1) or \
               (self.position.type == PositionType.SHORT and signal == 1):
                return ExitReason.REVERSE
        
        return None
