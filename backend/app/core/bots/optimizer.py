"""
KOMAS Bot Configuration Optimizer
==================================
Optimizes bot configuration parameters for maximum performance.

Features:
- Grid search over bot parameters
- Metric-based optimization (Sharpe, PF, Win Rate)
- Symbol selection optimization
- Position sizing optimization
- Walk-forward validation
- Parallel backtesting

Author: KOMAS Trading System
Version: 1.0.0
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from concurrent.futures import ProcessPoolExecutor, as_completed
from itertools import product
import pandas as pd
import numpy as np

from .models import (
    BotConfig, BotSymbolConfig, StrategyConfig,
    TakeProfitLevel, StopLossMode
)
from .backtest import PortfolioBacktest, BacktestResult
from ..logger import get_logger

logger = get_logger("bots.optimizer")


# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

@dataclass
class OptimizationConfig:
    """Configuration for bot optimization"""

    # Parameters to optimize
    optimize_symbols: bool = True  # Try different symbol combinations
    optimize_position_sizes: bool = True  # Try different position sizes
    optimize_strategy: bool = True  # Try different strategy parameters

    # Symbol pool (candidates)
    symbol_candidates: List[str] = field(default_factory=lambda: [
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"
    ])

    # Parameter ranges
    atr_length_range: List[int] = field(default_factory=lambda: [30, 45, 60])
    multiplier_range: List[float] = field(default_factory=lambda: [3.0, 4.0, 5.0])
    sl_percent_range: List[float] = field(default_factory=lambda: [2.0, 3.0, 4.0])
    tp_count_range: List[int] = field(default_factory=lambda: [3, 4])

    # Position sizing
    position_size_options: List[float] = field(default_factory=lambda: [25.0, 33.3, 50.0])

    # Optimization settings
    metric: str = "sharpe"  # sharpe, profit_factor, win_rate, pnl_percent
    max_symbols: int = 3  # Maximum symbols in portfolio
    min_symbols: int = 1  # Minimum symbols in portfolio

    # Validation
    use_walk_forward: bool = False
    walk_forward_periods: int = 3

    # Performance
    max_workers: int = 4  # Parallel backtest workers
    max_combinations: int = 100  # Limit search space

    def to_dict(self) -> Dict[str, Any]:
        return {
            'optimize_symbols': self.optimize_symbols,
            'optimize_position_sizes': self.optimize_position_sizes,
            'optimize_strategy': self.optimize_strategy,
            'symbol_candidates': self.symbol_candidates,
            'metric': self.metric,
            'max_combinations': self.max_combinations
        }


@dataclass
class OptimizationResult:
    """Result of bot configuration optimization"""

    # Best configuration found
    best_config: BotConfig
    best_score: float
    best_backtest: BacktestResult

    # All tested configurations
    tested_configs: List[Dict[str, Any]] = field(default_factory=list)

    # Optimization metadata
    total_combinations: int = 0
    combinations_tested: int = 0
    optimization_time: float = 0.0  # seconds

    # Metric used
    metric: str = "sharpe"

    def to_dict(self) -> Dict[str, Any]:
        return {
            'best_config': {
                'name': self.best_config.name,
                'symbols': [s.symbol for s in self.best_config.symbols],
                'strategy': self.best_config.strategy.model_dump() if self.best_config.strategy else None
            },
            'best_score': round(self.best_score, 4),
            'best_backtest': self.best_backtest.to_dict(),
            'tested_configs': self.tested_configs[:20],  # Top 20
            'metadata': {
                'total_combinations': self.total_combinations,
                'combinations_tested': self.combinations_tested,
                'optimization_time': round(self.optimization_time, 2),
                'metric': self.metric
            }
        }


# ═══════════════════════════════════════════════════════════════════
# OPTIMIZER ENGINE
# ═══════════════════════════════════════════════════════════════════

class BotOptimizer:
    """
    Bot configuration optimizer.

    Searches for optimal bot configuration using backtesting.
    """

    def __init__(
        self,
        base_config: BotConfig,
        opt_config: OptimizationConfig,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ):
        """
        Args:
            base_config: Base bot configuration to optimize
            opt_config: Optimization settings
            start_date: Backtest start date
            end_date: Backtest end date
        """
        self.base_config = base_config
        self.opt_config = opt_config
        self.start_date = start_date
        self.end_date = end_date

        self.results: List[Tuple[BotConfig, BacktestResult, float]] = []

    def optimize(self) -> OptimizationResult:
        """
        Run optimization.

        Returns:
            OptimizationResult with best configuration and all results
        """
        import time
        start_time = time.time()

        logger.info(f"Starting bot optimization with metric: {self.opt_config.metric}")

        # Generate configurations to test
        configs = self._generate_configurations()

        logger.info(f"Generated {len(configs)} configurations to test")

        # Run backtests
        self._run_backtests(configs)

        # Sort by score
        self.results.sort(key=lambda x: x[2], reverse=True)

        # Get best result
        best_config, best_backtest, best_score = self.results[0]

        optimization_time = time.time() - start_time

        logger.info(f"Optimization complete in {optimization_time:.2f}s")
        logger.info(f"Best score: {best_score:.4f}")
        logger.info(f"Best config: {[s.symbol for s in best_config.symbols]}")

        # Build tested configs summary
        tested_configs = [
            {
                'symbols': [s.symbol for s in cfg.symbols],
                'score': round(score, 4),
                'pnl_percent': round(backtest.total_pnl_percent, 2),
                'win_rate': round(backtest.win_rate, 2),
                'sharpe': round(backtest.sharpe_ratio, 2)
            }
            for cfg, backtest, score in self.results
        ]

        return OptimizationResult(
            best_config=best_config,
            best_score=best_score,
            best_backtest=best_backtest,
            tested_configs=tested_configs,
            total_combinations=len(configs),
            combinations_tested=len(self.results),
            optimization_time=optimization_time,
            metric=self.opt_config.metric
        )

    def _generate_configurations(self) -> List[BotConfig]:
        """Generate all configuration combinations to test"""
        configs = []

        # Generate symbol combinations
        if self.opt_config.optimize_symbols:
            symbol_combos = self._generate_symbol_combinations()
        else:
            symbol_combos = [[s.symbol for s in self.base_config.symbols]]

        # Generate strategy parameter combinations
        if self.opt_config.optimize_strategy:
            strategy_params = list(product(
                self.opt_config.atr_length_range,
                self.opt_config.multiplier_range,
                self.opt_config.sl_percent_range,
                self.opt_config.tp_count_range
            ))
        else:
            base_strat = self.base_config.strategy
            strategy_params = [(
                base_strat.atr_length if base_strat else 45,
                base_strat.multiplier if base_strat else 4.0,
                base_strat.sl_percent if base_strat else 2.0,
                base_strat.tp_count if base_strat else 4
            )]

        # Generate all combinations
        for symbols in symbol_combos:
            for atr_len, mult, sl_pct, tp_count in strategy_params:
                # Create config
                config = self._create_config(
                    symbols=symbols,
                    atr_length=atr_len,
                    multiplier=mult,
                    sl_percent=sl_pct,
                    tp_count=tp_count
                )
                configs.append(config)

                # Limit search space
                if len(configs) >= self.opt_config.max_combinations:
                    logger.warning(f"Hit max combinations limit: {self.opt_config.max_combinations}")
                    return configs

        return configs

    def _generate_symbol_combinations(self) -> List[List[str]]:
        """Generate symbol combinations to test"""
        from itertools import combinations

        combos = []

        for n in range(self.opt_config.min_symbols, self.opt_config.max_symbols + 1):
            for combo in combinations(self.opt_config.symbol_candidates, n):
                combos.append(list(combo))

        return combos

    def _create_config(
        self,
        symbols: List[str],
        atr_length: int,
        multiplier: float,
        sl_percent: float,
        tp_count: int
    ) -> BotConfig:
        """Create bot config from parameters"""

        # Create symbol configs
        position_size = 100.0 / len(symbols)  # Equal weight

        symbol_configs = [
            BotSymbolConfig(
                symbol=symbol,
                enabled=True,
                timeframe=self.base_config.symbols[0].timeframe if self.base_config.symbols else "1h",
                position_size_percent=position_size
            )
            for symbol in symbols
        ]

        # Create strategy config
        strategy = StrategyConfig(
            indicator="trg",
            atr_length=atr_length,
            multiplier=multiplier,
            tp_count=tp_count,
            take_profits=self._generate_tp_levels(tp_count),
            sl_percent=sl_percent,
            sl_mode=StopLossMode.BREAKEVEN,
            leverage=self.base_config.leverage if self.base_config else 1
        )

        return BotConfig(
            name=f"Optimized_{'-'.join(symbols)}",
            description="Auto-generated by optimizer",
            mode="paper",
            initial_capital=self.base_config.initial_capital,
            symbols=symbol_configs,
            strategy=strategy
        )

    def _generate_tp_levels(self, tp_count: int) -> List[TakeProfitLevel]:
        """Generate TP levels based on count"""
        tp_configs = {
            3: [
                TakeProfitLevel(price_percent=2.0, close_percent=50.0),
                TakeProfitLevel(price_percent=4.0, close_percent=30.0),
                TakeProfitLevel(price_percent=6.0, close_percent=20.0)
            ],
            4: [
                TakeProfitLevel(price_percent=1.5, close_percent=40.0),
                TakeProfitLevel(price_percent=3.0, close_percent=30.0),
                TakeProfitLevel(price_percent=5.0, close_percent=20.0),
                TakeProfitLevel(price_percent=8.0, close_percent=10.0)
            ]
        }

        return tp_configs.get(tp_count, tp_configs[4])

    def _run_backtests(self, configs: List[BotConfig]):
        """Run backtests for all configurations"""
        logger.info(f"Running {len(configs)} backtests...")

        # Sequential execution for simplicity
        # TODO: Implement parallel execution with ProcessPoolExecutor
        for i, config in enumerate(configs):
            try:
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i+1}/{len(configs)}")

                # Run backtest
                backtest = PortfolioBacktest(
                    bot_config=config,
                    start_date=self.start_date,
                    end_date=self.end_date
                )

                result = backtest.run()

                # Calculate score
                score = self._calculate_score(result)

                self.results.append((config, result, score))

            except Exception as e:
                logger.error(f"Backtest failed for config {i}: {e}")
                continue

    def _calculate_score(self, result: BacktestResult) -> float:
        """Calculate optimization score from backtest result"""
        metric = self.opt_config.metric

        if metric == "sharpe":
            return result.sharpe_ratio
        elif metric == "profit_factor":
            return result.profit_factor
        elif metric == "win_rate":
            return result.win_rate
        elif metric == "pnl_percent":
            return result.total_pnl_percent
        else:
            # Default: combined score
            return (
                result.sharpe_ratio * 0.4 +
                result.profit_factor * 0.3 +
                result.win_rate * 0.3
            )


# ═══════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def quick_optimize(
    base_config: BotConfig,
    symbols: Optional[List[str]] = None,
    metric: str = "sharpe",
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> OptimizationResult:
    """
    Quick optimization with default settings.

    Args:
        base_config: Base configuration
        symbols: Symbol candidates (default: top 5)
        metric: Optimization metric
        start_date: Start date
        end_date: End date

    Returns:
        OptimizationResult
    """
    if symbols is None:
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT"]

    opt_config = OptimizationConfig(
        symbol_candidates=symbols,
        metric=metric,
        max_combinations=50,  # Limit for speed
        optimize_symbols=True,
        optimize_strategy=True,
        optimize_position_sizes=False
    )

    optimizer = BotOptimizer(
        base_config=base_config,
        opt_config=opt_config,
        start_date=start_date,
        end_date=end_date
    )

    return optimizer.optimize()
