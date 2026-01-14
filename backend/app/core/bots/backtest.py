"""
KOMAS Bot Portfolio Backtest Engine
====================================
Backtesting engine for multi-symbol bot portfolios.

Features:
- Multi-pair portfolio simulation
- Shared capital management
- Portfolio-level equity curve
- Per-symbol statistics
- TP/SL tracking
- Commission simulation
- Detailed trade log

Author: KOMAS Trading System
Version: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from enum import Enum
import pandas as pd
import numpy as np
from pathlib import Path

from .models import (
    Bot, BotConfig, BotSymbolConfig, StrategyConfig,
    Position, BotStatistics, SignalDirection, StopLossMode
)
from ..data.storage import DataStorage
from ..logger import get_logger

logger = get_logger("bots.backtest")


# ═══════════════════════════════════════════════════════════════════
# MODELS
# ═══════════════════════════════════════════════════════════════════

@dataclass
class BacktestPosition:
    """Backtest position (separate from live Position)"""
    id: str
    symbol: str
    direction: SignalDirection
    entry_price: float
    entry_time: datetime
    size: float  # Position size in quote currency
    leverage: int

    # TP/SL levels
    tp_levels: List[Tuple[float, float]]  # [(price, percent), ...]
    tp_levels_hit: List[int] = field(default_factory=list)
    sl_price: float = 0.0
    sl_mode: StopLossMode = StopLossMode.FIXED

    # Exit tracking
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[str] = None

    # PnL
    realized_pnl: float = 0.0
    realized_pnl_percent: float = 0.0
    commission_paid: float = 0.0

    @property
    def is_closed(self) -> bool:
        return self.exit_price is not None

    @property
    def remaining_size(self) -> float:
        """Remaining position size after partial TPs"""
        if not self.tp_levels_hit:
            return self.size

        total_closed = sum(
            self.tp_levels[tp_idx][1] for tp_idx in self.tp_levels_hit
        )
        return self.size * (1.0 - total_closed / 100.0)


@dataclass
class BacktestResult:
    """Results of portfolio backtest"""

    # Configuration
    bot_config: BotConfig
    start_date: datetime
    end_date: datetime

    # Portfolio metrics
    initial_capital: float
    final_capital: float
    total_pnl: float
    total_pnl_percent: float

    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float

    # Performance
    max_drawdown: float
    max_drawdown_percent: float
    sharpe_ratio: float
    profit_factor: float

    # Per-symbol breakdown
    symbol_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Time series
    equity_curve: List[Tuple[datetime, float]] = field(default_factory=list)

    # Trades log
    trades: List[Dict[str, Any]] = field(default_factory=list)

    # Monthly breakdown
    monthly_stats: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'config': {
                'bot_name': self.bot_config.name,
                'symbols': [s.symbol for s in self.bot_config.symbols],
                'timeframe': self.bot_config.symbols[0].timeframe if self.bot_config.symbols else None,
                'strategy': self.bot_config.strategy.model_dump() if self.bot_config.strategy else None
            },
            'period': {
                'start': self.start_date.isoformat(),
                'end': self.end_date.isoformat(),
                'days': (self.end_date - self.start_date).days
            },
            'capital': {
                'initial': round(self.initial_capital, 2),
                'final': round(self.final_capital, 2),
                'pnl': round(self.total_pnl, 2),
                'pnl_percent': round(self.total_pnl_percent, 2)
            },
            'statistics': {
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': round(self.win_rate, 2),
                'max_drawdown': round(self.max_drawdown, 2),
                'max_drawdown_percent': round(self.max_drawdown_percent, 2),
                'sharpe_ratio': round(self.sharpe_ratio, 2),
                'profit_factor': round(self.profit_factor, 2)
            },
            'symbol_breakdown': self.symbol_stats,
            'equity_curve': [
                {'time': t.isoformat(), 'equity': round(e, 2)}
                for t, e in self.equity_curve
            ],
            'trades': self.trades,
            'monthly': self.monthly_stats
        }


# ═══════════════════════════════════════════════════════════════════
# BACKTEST ENGINE
# ═══════════════════════════════════════════════════════════════════

class PortfolioBacktest:
    """
    Portfolio backtest engine for bots.

    Simulates bot trading across multiple symbols with shared capital.
    """

    def __init__(
        self,
        bot_config: BotConfig,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        data_dir: Optional[Path] = None
    ):
        """
        Args:
            bot_config: Bot configuration to backtest
            start_date: Start date (YYYY-MM-DD) or None for all data
            end_date: End date (YYYY-MM-DD) or None for all data
            data_dir: Custom data directory
        """
        self.bot_config = bot_config
        self.start_date = pd.to_datetime(start_date) if start_date else None
        self.end_date = pd.to_datetime(end_date) if end_date else None

        self.storage = DataStorage(data_dir=data_dir)
        self.data_cache: Dict[str, pd.DataFrame] = {}

        # State
        self.capital = bot_config.initial_capital
        self.positions: List[BacktestPosition] = []
        self.closed_positions: List[BacktestPosition] = []

        # Equity tracking
        self.equity_curve: List[Tuple[datetime, float]] = []

        # Statistics
        self.total_commission = 0.0

    def run(self) -> BacktestResult:
        """
        Run portfolio backtest.

        Returns:
            BacktestResult with complete statistics
        """
        logger.info(f"Starting portfolio backtest: {self.bot_config.name}")
        logger.info(f"Symbols: {[s.symbol for s in self.bot_config.symbols]}")

        # Load data for all symbols
        if not self._load_data():
            raise ValueError("Failed to load data for backtest")

        # Run simulation
        self._run_simulation()

        # Calculate statistics
        result = self._calculate_results()

        logger.info(f"Backtest complete: {result.total_trades} trades, "
                   f"{result.total_pnl_percent:.2f}% PnL")

        return result

    def _load_data(self) -> bool:
        """Load OHLCV data for all symbols"""
        logger.info("Loading data...")

        for symbol_config in self.bot_config.symbols:
            if not symbol_config.enabled:
                continue

            symbol = symbol_config.symbol
            timeframe = symbol_config.timeframe

            # Load from storage
            df = self.storage.load(symbol, timeframe)

            if df is None or len(df) == 0:
                logger.error(f"No data for {symbol} {timeframe}")
                return False

            # Filter date range
            if self.start_date:
                df = df[df.index >= self.start_date]
            if self.end_date:
                df = df[df.index <= self.end_date]

            if len(df) < 100:
                logger.error(f"Insufficient data for {symbol}: {len(df)} candles")
                return False

            self.data_cache[symbol] = df
            logger.info(f"Loaded {symbol}: {len(df)} candles")

        return True

    def _run_simulation(self):
        """Run backtest simulation"""
        logger.info("Running simulation...")

        # Get all unique timestamps across symbols
        all_timestamps = set()
        for df in self.data_cache.values():
            all_timestamps.update(df.index)

        timestamps = sorted(all_timestamps)
        logger.info(f"Simulating {len(timestamps)} time periods...")

        for i, timestamp in enumerate(timestamps):
            # Process each symbol
            for symbol_config in self.bot_config.symbols:
                if not symbol_config.enabled:
                    continue

                symbol = symbol_config.symbol
                df = self.data_cache[symbol]

                if timestamp not in df.index:
                    continue

                # Get current candle
                candle = df.loc[timestamp]

                # Check existing positions for TP/SL
                self._check_positions(symbol, candle, timestamp)

                # Check for new signal
                self._check_signal(symbol, candle, timestamp, symbol_config)

            # Record equity snapshot every 100 periods
            if i % 100 == 0:
                self._record_equity(timestamp)

        # Final equity snapshot
        if timestamps:
            self._record_equity(timestamps[-1])

    def _check_signal(
        self,
        symbol: str,
        candle: pd.Series,
        timestamp: datetime,
        symbol_config: BotSymbolConfig
    ):
        """Check for trading signal"""
        # Check if already in position for this symbol
        if any(p.symbol == symbol and not p.is_closed for p in self.positions):
            return

        # Calculate TRG signal (simplified - you'd use actual indicator)
        signal = self._calculate_trg_signal(symbol, timestamp)

        if signal:
            self._open_position(symbol, signal, candle, timestamp, symbol_config)

    def _calculate_trg_signal(
        self,
        symbol: str,
        timestamp: datetime
    ) -> Optional[SignalDirection]:
        """
        Calculate TRG signal (simplified version).

        In production, this would use the full TRG indicator with filters.
        """
        df = self.data_cache[symbol]

        # Get data up to current timestamp
        historical = df.loc[:timestamp]

        if len(historical) < 50:
            return None

        # Simple trend detection using EMA crossover (placeholder)
        # In reality, you'd use TRG bands with ATR
        ema_fast = historical['close'].ewm(span=12).mean()
        ema_slow = historical['close'].ewm(span=26).mean()

        if len(ema_fast) < 2:
            return None

        # Check for crossover
        if ema_fast.iloc[-1] > ema_slow.iloc[-1] and ema_fast.iloc[-2] <= ema_slow.iloc[-2]:
            return SignalDirection.LONG
        elif ema_fast.iloc[-1] < ema_slow.iloc[-1] and ema_fast.iloc[-2] >= ema_slow.iloc[-2]:
            return SignalDirection.SHORT

        return None

    def _open_position(
        self,
        symbol: str,
        direction: SignalDirection,
        candle: pd.Series,
        timestamp: datetime,
        symbol_config: BotSymbolConfig
    ):
        """Open new position"""
        entry_price = float(candle['close'])

        # Calculate position size
        position_size = self.capital * (symbol_config.position_size_percent / 100.0)

        # Apply leverage
        leverage = self.bot_config.strategy.leverage if self.bot_config.strategy else 1
        position_size *= leverage

        # Calculate TP levels
        tp_levels = self._calculate_tp_levels(
            entry_price,
            direction,
            self.bot_config.strategy
        )

        # Calculate SL
        sl_price = self._calculate_sl_price(
            entry_price,
            direction,
            self.bot_config.strategy
        )

        # Create position
        position = BacktestPosition(
            id=f"{symbol}_{timestamp.strftime('%Y%m%d%H%M%S')}",
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            entry_time=timestamp,
            size=position_size,
            leverage=leverage,
            tp_levels=tp_levels,
            sl_price=sl_price,
            sl_mode=self.bot_config.strategy.sl_mode if self.bot_config.strategy else StopLossMode.FIXED
        )

        # Calculate commission
        commission = position_size * 0.001  # 0.1% taker fee
        self.total_commission += commission
        position.commission_paid = commission

        self.positions.append(position)

        logger.debug(f"Opened {direction.value} {symbol} @ {entry_price:.2f}, "
                    f"size={position_size:.2f}, SL={sl_price:.2f}")

    def _calculate_tp_levels(
        self,
        entry_price: float,
        direction: SignalDirection,
        strategy: Optional[StrategyConfig]
    ) -> List[Tuple[float, float]]:
        """Calculate TP price levels"""
        if not strategy or not strategy.take_profits:
            return []

        tp_levels = []

        for tp in strategy.take_profits:
            if direction == SignalDirection.LONG:
                tp_price = entry_price * (1 + tp.price_percent / 100)
            else:
                tp_price = entry_price * (1 - tp.price_percent / 100)

            tp_levels.append((tp_price, tp.close_percent))

        return tp_levels

    def _calculate_sl_price(
        self,
        entry_price: float,
        direction: SignalDirection,
        strategy: Optional[StrategyConfig]
    ) -> float:
        """Calculate SL price"""
        if not strategy:
            sl_percent = 2.0
        else:
            sl_percent = strategy.sl_percent

        if direction == SignalDirection.LONG:
            return entry_price * (1 - sl_percent / 100)
        else:
            return entry_price * (1 + sl_percent / 100)

    def _check_positions(
        self,
        symbol: str,
        candle: pd.Series,
        timestamp: datetime
    ):
        """Check open positions for TP/SL hits"""
        for position in self.positions:
            if position.symbol != symbol or position.is_closed:
                continue

            high = float(candle['high'])
            low = float(candle['low'])

            # Check SL first
            if self._check_sl_hit(position, high, low):
                self._close_position(position, position.sl_price, timestamp, "SL Hit")
                continue

            # Check TP levels
            self._check_tp_hits(position, high, low, timestamp)

    def _check_sl_hit(
        self,
        position: BacktestPosition,
        high: float,
        low: float
    ) -> bool:
        """Check if SL was hit"""
        if position.direction == SignalDirection.LONG:
            return low <= position.sl_price
        else:
            return high >= position.sl_price

    def _check_tp_hits(
        self,
        position: BacktestPosition,
        high: float,
        low: float,
        timestamp: datetime
    ):
        """Check TP levels"""
        for i, (tp_price, tp_percent) in enumerate(position.tp_levels):
            # Skip already hit levels
            if i in position.tp_levels_hit:
                continue

            # Check if TP was hit
            hit = False
            if position.direction == SignalDirection.LONG:
                hit = high >= tp_price
            else:
                hit = low <= tp_price

            if hit:
                position.tp_levels_hit.append(i)
                logger.debug(f"{position.symbol} TP{i+1} hit @ {tp_price:.2f}")

                # Check if this closes the position
                total_closed = sum(
                    position.tp_levels[idx][1] for idx in position.tp_levels_hit
                )

                if total_closed >= 100.0:
                    self._close_position(position, tp_price, timestamp, f"TP{i+1}")
                    break

    def _close_position(
        self,
        position: BacktestPosition,
        exit_price: float,
        exit_time: datetime,
        exit_reason: str
    ):
        """Close position and calculate PnL"""
        position.exit_price = exit_price
        position.exit_time = exit_time
        position.exit_reason = exit_reason

        # Calculate PnL
        if position.direction == SignalDirection.LONG:
            pnl_percent = ((exit_price - position.entry_price) / position.entry_price) * 100
        else:
            pnl_percent = ((position.entry_price - exit_price) / position.entry_price) * 100

        # Apply leverage
        pnl_percent *= position.leverage

        # Calculate amount
        pnl_amount = position.size * (pnl_percent / 100)

        # Subtract commission
        pnl_amount -= position.commission_paid

        position.realized_pnl = pnl_amount
        position.realized_pnl_percent = pnl_percent

        # Update capital
        self.capital += pnl_amount

        self.closed_positions.append(position)

        logger.debug(f"Closed {position.symbol} {exit_reason}: "
                    f"{pnl_percent:.2f}% (${pnl_amount:.2f})")

    def _record_equity(self, timestamp: datetime):
        """Record current equity"""
        # Calculate unrealized PnL from open positions
        unrealized_pnl = 0.0
        # For simplicity, we don't calculate unrealized PnL in backtest

        total_equity = self.capital + unrealized_pnl
        self.equity_curve.append((timestamp, total_equity))

    def _calculate_results(self) -> BacktestResult:
        """Calculate final results"""
        # Basic metrics
        total_trades = len(self.closed_positions)
        winning_trades = sum(1 for p in self.closed_positions if p.realized_pnl > 0)
        losing_trades = sum(1 for p in self.closed_positions if p.realized_pnl < 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        total_pnl = self.capital - self.bot_config.initial_capital
        total_pnl_percent = (total_pnl / self.bot_config.initial_capital) * 100

        # Drawdown calculation
        max_drawdown, max_drawdown_percent = self._calculate_drawdown()

        # Sharpe ratio (simplified)
        sharpe_ratio = self._calculate_sharpe()

        # Profit factor
        profit_factor = self._calculate_profit_factor()

        # Per-symbol stats
        symbol_stats = self._calculate_symbol_stats()

        # Monthly breakdown
        monthly_stats = self._calculate_monthly_stats()

        # Trades log
        trades_log = [
            {
                'id': p.id,
                'symbol': p.symbol,
                'direction': p.direction.value,
                'entry_price': p.entry_price,
                'entry_time': p.entry_time.isoformat(),
                'exit_price': p.exit_price,
                'exit_time': p.exit_time.isoformat() if p.exit_time else None,
                'exit_reason': p.exit_reason,
                'pnl': round(p.realized_pnl, 2),
                'pnl_percent': round(p.realized_pnl_percent, 2),
                'commission': round(p.commission_paid, 2)
            }
            for p in self.closed_positions
        ]

        return BacktestResult(
            bot_config=self.bot_config,
            start_date=self.start_date or list(self.data_cache.values())[0].index[0],
            end_date=self.end_date or list(self.data_cache.values())[0].index[-1],
            initial_capital=self.bot_config.initial_capital,
            final_capital=self.capital,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            max_drawdown=max_drawdown,
            max_drawdown_percent=max_drawdown_percent,
            sharpe_ratio=sharpe_ratio,
            profit_factor=profit_factor,
            symbol_stats=symbol_stats,
            equity_curve=self.equity_curve,
            trades=trades_log,
            monthly_stats=monthly_stats
        )

    def _calculate_drawdown(self) -> Tuple[float, float]:
        """Calculate maximum drawdown"""
        if not self.equity_curve:
            return 0.0, 0.0

        equity_values = [e for _, e in self.equity_curve]
        peak = equity_values[0]
        max_dd = 0.0

        for equity in equity_values:
            if equity > peak:
                peak = equity
            dd = peak - equity
            if dd > max_dd:
                max_dd = dd

        max_dd_percent = (max_dd / self.bot_config.initial_capital) * 100 if self.bot_config.initial_capital > 0 else 0

        return max_dd, max_dd_percent

    def _calculate_sharpe(self) -> float:
        """Calculate Sharpe ratio (simplified)"""
        if len(self.closed_positions) < 2:
            return 0.0

        returns = [p.realized_pnl_percent for p in self.closed_positions]

        if not returns:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        # Annualized Sharpe (assuming daily returns)
        sharpe = (mean_return / std_return) * np.sqrt(252)

        return sharpe

    def _calculate_profit_factor(self) -> float:
        """Calculate profit factor"""
        gross_profit = sum(p.realized_pnl for p in self.closed_positions if p.realized_pnl > 0)
        gross_loss = abs(sum(p.realized_pnl for p in self.closed_positions if p.realized_pnl < 0))

        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0

        return gross_profit / gross_loss

    def _calculate_symbol_stats(self) -> Dict[str, Dict[str, Any]]:
        """Calculate per-symbol statistics"""
        stats = {}

        for symbol_config in self.bot_config.symbols:
            symbol = symbol_config.symbol
            symbol_trades = [p for p in self.closed_positions if p.symbol == symbol]

            if not symbol_trades:
                stats[symbol] = {
                    'trades': 0,
                    'pnl': 0.0,
                    'win_rate': 0.0
                }
                continue

            total_pnl = sum(p.realized_pnl for p in symbol_trades)
            wins = sum(1 for p in symbol_trades if p.realized_pnl > 0)
            win_rate = (wins / len(symbol_trades)) * 100

            stats[symbol] = {
                'trades': len(symbol_trades),
                'wins': wins,
                'losses': len(symbol_trades) - wins,
                'win_rate': round(win_rate, 2),
                'pnl': round(total_pnl, 2),
                'pnl_percent': round((total_pnl / self.bot_config.initial_capital) * 100, 2)
            }

        return stats

    def _calculate_monthly_stats(self) -> List[Dict[str, Any]]:
        """Calculate monthly breakdown"""
        monthly = {}

        for position in self.closed_positions:
            if not position.exit_time:
                continue

            month_key = position.exit_time.strftime('%Y-%m')

            if month_key not in monthly:
                monthly[month_key] = {
                    'month': month_key,
                    'trades': 0,
                    'wins': 0,
                    'losses': 0,
                    'pnl': 0.0
                }

            monthly[month_key]['trades'] += 1
            monthly[month_key]['pnl'] += position.realized_pnl

            if position.realized_pnl > 0:
                monthly[month_key]['wins'] += 1
            else:
                monthly[month_key]['losses'] += 1

        # Calculate win rates and round values
        for stats in monthly.values():
            stats['win_rate'] = (stats['wins'] / stats['trades'] * 100) if stats['trades'] > 0 else 0
            stats['pnl'] = round(stats['pnl'], 2)
            stats['win_rate'] = round(stats['win_rate'], 2)

        return sorted(monthly.values(), key=lambda x: x['month'])
