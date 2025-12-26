"""
Komas Trading System - Base Optimizer
=====================================
Abstract base class for parameter optimization.
Supports grid search, random search, and genetic algorithms.

Version: 1.0
Author: Komas Team
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable, Tuple, Generator
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
import multiprocessing
import pandas as pd
import numpy as np
import json


class OptimizationMode(Enum):
    """Optimization scope"""
    INDICATOR = "indicator"   # Optimize indicator params only
    TP = "tp"                 # Optimize TP levels only
    SL = "sl"                 # Optimize SL only
    FILTERS = "filters"       # Optimize filter params
    FULL = "full"            # Optimize everything
    ADAPTIVE = "adaptive"     # Walk-forward optimization


class OptimizationMetric(Enum):
    """Optimization target metric"""
    PROFIT = "profit"
    WIN_RATE = "winrate"
    SHARPE = "sharpe"
    PROFIT_FACTOR = "profit_factor"
    CALMAR = "calmar"
    ADVANCED = "advanced"


class SearchMethod(Enum):
    """Parameter search method"""
    GRID = "grid"           # Full grid search
    RANDOM = "random"       # Random sampling
    BAYESIAN = "bayesian"   # Bayesian optimization


@dataclass
class ParameterRange:
    """
    Parameter optimization range.
    Defines the search space for a parameter.
    """
    name: str
    min_value: float
    max_value: float
    step: float
    param_type: str = "float"  # "int", "float"
    
    def get_values(self) -> List[Any]:
        """Get all values in range"""
        if self.param_type == "int":
            return list(range(int(self.min_value), int(self.max_value) + 1, int(self.step)))
        else:
            values = []
            v = self.min_value
            while v <= self.max_value:
                values.append(round(v, 6))
                v += self.step
            return values
    
    def get_random_value(self) -> Any:
        """Get random value in range"""
        if self.param_type == "int":
            return np.random.randint(int(self.min_value), int(self.max_value) + 1)
        else:
            # Align to step
            steps = int((self.max_value - self.min_value) / self.step)
            random_step = np.random.randint(0, steps + 1)
            return round(self.min_value + random_step * self.step, 6)
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "min": self.min_value,
            "max": self.max_value,
            "step": self.step,
            "type": self.param_type
        }


@dataclass
class OptimizationResult:
    """
    Single optimization test result.
    """
    params: Dict[str, Any]
    score: float
    metrics: Dict[str, float] = field(default_factory=dict)
    trades_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "params": self.params,
            "score": round(self.score, 4),
            "metrics": {k: round(v, 4) for k, v in self.metrics.items()},
            "trades": self.trades_count
        }


@dataclass
class OptimizationProgress:
    """
    Optimization progress for streaming.
    """
    tested: int
    total: int
    progress_pct: float
    current_best: Optional[OptimizationResult] = None
    current_test: Optional[Dict[str, Any]] = None
    estimated_time_remaining: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            "tested": self.tested,
            "total": self.total,
            "progress": round(self.progress_pct, 1),
            "best": self.current_best.to_dict() if self.current_best else None,
            "current": self.current_test,
            "eta_seconds": round(self.estimated_time_remaining) if self.estimated_time_remaining else None
        }


@dataclass
class OptimizationConfig:
    """
    Optimization configuration.
    """
    mode: OptimizationMode = OptimizationMode.INDICATOR
    metric: OptimizationMetric = OptimizationMetric.ADVANCED
    method: SearchMethod = SearchMethod.GRID
    
    # Search parameters
    max_tests: int = 1000              # Max combinations to test
    random_samples: int = 100          # For random search
    parallel_workers: int = 0          # 0 = auto (use all cores)
    
    # Adaptive optimization
    lookback_period: int = 3           # Months
    reoptimize_frequency: str = "month"  # "week", "month", "quarter"
    
    # Minimum requirements
    min_trades: int = 20               # Min trades for valid result
    
    # Parameter ranges (filled by optimizer)
    param_ranges: List[ParameterRange] = field(default_factory=list)
    
    def get_worker_count(self) -> int:
        """Get number of parallel workers to use"""
        if self.parallel_workers > 0:
            return self.parallel_workers
        return max(1, multiprocessing.cpu_count() - 1)
    
    def to_dict(self) -> Dict:
        return {
            "mode": self.mode.value,
            "metric": self.metric.value,
            "method": self.method.value,
            "max_tests": self.max_tests,
            "random_samples": self.random_samples,
            "workers": self.get_worker_count(),
            "min_trades": self.min_trades,
            "param_ranges": [p.to_dict() for p in self.param_ranges]
        }


class BaseOptimizer(ABC):
    """
    Abstract base class for parameter optimization.
    
    Subclasses must implement:
    - get_parameter_ranges(): Define optimization ranges
    - run_single_test(): Run backtest with given params
    - calculate_score(): Calculate optimization score
    
    Optional overrides:
    - get_default_config(): Default optimization config
    - on_test_complete(): Callback after each test
    - on_optimization_complete(): Callback when done
    """
    
    def __init__(self, config: Optional[OptimizationConfig] = None):
        self.config = config or self.get_default_config()
        self.results: List[OptimizationResult] = []
        self.best_result: Optional[OptimizationResult] = None
        self._start_time: Optional[datetime] = None
        self._tested_count = 0
        self._total_count = 0
    
    # ==================== ABSTRACT METHODS ====================
    
    @abstractmethod
    def get_parameter_ranges(self, mode: OptimizationMode) -> List[ParameterRange]:
        """
        Get parameter ranges for optimization mode.
        
        Args:
            mode: Optimization mode (indicator, tp, sl, etc.)
        
        Returns:
            List of parameter ranges to optimize
        """
        pass
    
    @abstractmethod
    def run_single_test(self, params: Dict[str, Any], df: pd.DataFrame) -> Tuple[List, List]:
        """
        Run single backtest with given parameters.
        
        Args:
            params: Parameter values to test
            df: OHLCV DataFrame
        
        Returns:
            Tuple of (trades list, equity curve list)
        """
        pass
    
    @abstractmethod
    def calculate_score(
        self,
        trades: List,
        equity_curve: List,
        metric: OptimizationMetric
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate optimization score from backtest results.
        
        Args:
            trades: List of trades
            equity_curve: Equity curve
            metric: Optimization metric
        
        Returns:
            Tuple of (score, metrics dict)
        """
        pass
    
    # ==================== OPTIONAL OVERRIDES ====================
    
    def get_default_config(self) -> OptimizationConfig:
        """Get default optimization configuration"""
        return OptimizationConfig()
    
    def on_test_complete(self, result: OptimizationResult, progress: OptimizationProgress) -> None:
        """Callback after each test completes. Override for custom logic."""
        pass
    
    def on_optimization_complete(self, best: OptimizationResult, all_results: List[OptimizationResult]) -> None:
        """Callback when optimization completes. Override for custom logic."""
        pass
    
    def validate_params(self, params: Dict[str, Any]) -> bool:
        """
        Validate parameter combination.
        Override to add custom validation rules.
        """
        return True
    
    # ==================== OPTIMIZATION METHODS ====================
    
    def generate_parameter_combinations(self) -> Generator[Dict[str, Any], None, None]:
        """Generate parameter combinations based on search method"""
        ranges = self.config.param_ranges
        
        if not ranges:
            return
        
        if self.config.method == SearchMethod.GRID:
            # Full grid search
            yield from self._generate_grid(ranges)
        
        elif self.config.method == SearchMethod.RANDOM:
            # Random sampling
            for _ in range(self.config.random_samples):
                params = {r.name: r.get_random_value() for r in ranges}
                if self.validate_params(params):
                    yield params
    
    def _generate_grid(self, ranges: List[ParameterRange]) -> Generator[Dict[str, Any], None, None]:
        """Generate full grid of parameter combinations"""
        if not ranges:
            yield {}
            return
        
        first_range = ranges[0]
        remaining_ranges = ranges[1:]
        
        for value in first_range.get_values():
            if remaining_ranges:
                for combo in self._generate_grid(remaining_ranges):
                    params = {first_range.name: value, **combo}
                    if self.validate_params(params):
                        yield params
            else:
                params = {first_range.name: value}
                if self.validate_params(params):
                    yield params
    
    def count_combinations(self) -> int:
        """Count total parameter combinations"""
        if self.config.method == SearchMethod.RANDOM:
            return self.config.random_samples
        
        count = 1
        for r in self.config.param_ranges:
            count *= len(r.get_values())
        
        return min(count, self.config.max_tests)
    
    def optimize(
        self,
        df: pd.DataFrame,
        progress_callback: Optional[Callable[[OptimizationProgress], None]] = None
    ) -> OptimizationResult:
        """
        Run optimization.
        
        Args:
            df: OHLCV DataFrame
            progress_callback: Optional callback for progress updates
        
        Returns:
            Best optimization result
        """
        # Initialize
        self.results = []
        self.best_result = None
        self._start_time = datetime.now()
        self._tested_count = 0
        
        # Set up parameter ranges
        self.config.param_ranges = self.get_parameter_ranges(self.config.mode)
        self._total_count = self.count_combinations()
        
        # Generate combinations
        combinations = list(self.generate_parameter_combinations())
        
        # Limit to max tests
        if len(combinations) > self.config.max_tests:
            np.random.shuffle(combinations)
            combinations = combinations[:self.config.max_tests]
            self._total_count = len(combinations)
        
        # Run tests
        workers = self.config.get_worker_count()
        
        if workers > 1 and len(combinations) > 10:
            # Parallel execution
            self._run_parallel(df, combinations, progress_callback)
        else:
            # Sequential execution
            self._run_sequential(df, combinations, progress_callback)
        
        # Sort results by score
        self.results.sort(key=lambda x: x.score, reverse=True)
        
        if self.results:
            self.best_result = self.results[0]
        
        # Callback
        if self.best_result:
            self.on_optimization_complete(self.best_result, self.results)
        
        return self.best_result
    
    def _run_sequential(
        self,
        df: pd.DataFrame,
        combinations: List[Dict],
        progress_callback: Optional[Callable]
    ) -> None:
        """Run tests sequentially"""
        for params in combinations:
            result = self._test_params(params, df)
            
            if result:
                self.results.append(result)
                
                if self.best_result is None or result.score > self.best_result.score:
                    self.best_result = result
            
            self._tested_count += 1
            
            # Progress callback
            if progress_callback:
                progress = self._create_progress()
                progress_callback(progress)
                self.on_test_complete(result, progress)
    
    def _run_parallel(
        self,
        df: pd.DataFrame,
        combinations: List[Dict],
        progress_callback: Optional[Callable]
    ) -> None:
        """Run tests in parallel"""
        workers = self.config.get_worker_count()
        
        # Prepare data for workers (need to pass df as pickle-able)
        df_dict = df.to_dict('list')
        df_index = df.index.tolist()
        
        with ProcessPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks
            futures = {}
            for params in combinations:
                future = executor.submit(
                    self._test_params_worker,
                    params, df_dict, df_index
                )
                futures[future] = params
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result_dict = future.result()
                    if result_dict:
                        result = OptimizationResult(
                            params=result_dict['params'],
                            score=result_dict['score'],
                            metrics=result_dict['metrics'],
                            trades_count=result_dict['trades_count']
                        )
                        
                        self.results.append(result)
                        
                        if self.best_result is None or result.score > self.best_result.score:
                            self.best_result = result
                
                except Exception as e:
                    print(f"Optimization error: {e}")
                
                self._tested_count += 1
                
                # Progress callback
                if progress_callback:
                    progress = self._create_progress()
                    progress_callback(progress)
    
    def _test_params(self, params: Dict[str, Any], df: pd.DataFrame) -> Optional[OptimizationResult]:
        """Test single parameter combination"""
        try:
            # Run backtest
            trades, equity = self.run_single_test(params, df)
            
            # Check minimum trades
            if len(trades) < self.config.min_trades:
                return None
            
            # Calculate score
            score, metrics = self.calculate_score(trades, equity, self.config.metric)
            
            return OptimizationResult(
                params=params,
                score=score,
                metrics=metrics,
                trades_count=len(trades)
            )
        
        except Exception as e:
            print(f"Test error for {params}: {e}")
            return None
    
    def _test_params_worker(
        self,
        params: Dict[str, Any],
        df_dict: Dict,
        df_index: List
    ) -> Optional[Dict]:
        """Worker function for parallel execution"""
        try:
            # Reconstruct DataFrame
            df = pd.DataFrame(df_dict, index=pd.DatetimeIndex(df_index))
            
            result = self._test_params(params, df)
            
            if result:
                return result.to_dict()
            return None
        
        except Exception as e:
            print(f"Worker error: {e}")
            return None
    
    def _create_progress(self) -> OptimizationProgress:
        """Create progress object"""
        progress_pct = (self._tested_count / self._total_count * 100) if self._total_count > 0 else 0
        
        # Estimate remaining time
        eta = None
        if self._start_time and self._tested_count > 0:
            elapsed = (datetime.now() - self._start_time).total_seconds()
            avg_time = elapsed / self._tested_count
            remaining = self._total_count - self._tested_count
            eta = avg_time * remaining
        
        return OptimizationProgress(
            tested=self._tested_count,
            total=self._total_count,
            progress_pct=progress_pct,
            current_best=self.best_result,
            estimated_time_remaining=eta
        )
    
    # ==================== STREAMING ====================
    
    def optimize_stream(
        self,
        df: pd.DataFrame
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Run optimization with streaming progress.
        Yields progress events for SSE.
        
        Usage:
            for event in optimizer.optimize_stream(df):
                yield f"data: {json.dumps(event)}\n\n"
        """
        # Initialize
        self.results = []
        self.best_result = None
        self._start_time = datetime.now()
        self._tested_count = 0
        
        # Set up parameter ranges
        self.config.param_ranges = self.get_parameter_ranges(self.config.mode)
        combinations = list(self.generate_parameter_combinations())
        
        if len(combinations) > self.config.max_tests:
            np.random.shuffle(combinations)
            combinations = combinations[:self.config.max_tests]
        
        self._total_count = len(combinations)
        
        # Start event
        yield {
            "event": "start",
            "data": {
                "total": self._total_count,
                "workers": self.config.get_worker_count(),
                "mode": self.config.mode.value,
                "metric": self.config.metric.value
            }
        }
        
        # Test each combination
        for params in combinations:
            result = self._test_params(params, df)
            
            if result:
                self.results.append(result)
                
                if self.best_result is None or result.score > self.best_result.score:
                    self.best_result = result
            
            self._tested_count += 1
            
            # Progress event
            yield {
                "event": "test",
                "data": self._create_progress().to_dict()
            }
        
        # Sort results
        self.results.sort(key=lambda x: x.score, reverse=True)
        
        # Complete event
        yield {
            "event": "complete",
            "data": {
                "best": self.best_result.to_dict() if self.best_result else None,
                "total_tested": len(self.results),
                "duration_seconds": (datetime.now() - self._start_time).total_seconds()
            }
        }
    
    # ==================== HEATMAP ====================
    
    def generate_heatmap(
        self,
        df: pd.DataFrame,
        param1: ParameterRange,
        param2: ParameterRange
    ) -> Dict[str, Any]:
        """
        Generate heatmap data for two parameters.
        
        Args:
            df: OHLCV DataFrame
            param1: First parameter (X axis)
            param2: Second parameter (Y axis)
        
        Returns:
            Heatmap data for visualization
        """
        results = []
        
        for v1 in param1.get_values():
            for v2 in param2.get_values():
                params = {param1.name: v1, param2.name: v2}
                
                result = self._test_params(params, df)
                
                results.append({
                    param1.name: v1,
                    param2.name: v2,
                    "score": result.score if result else float('-inf'),
                    "pnl": result.metrics.get('profit_pct', 0) if result else 0,
                    "win_rate": result.metrics.get('win_rate', 0) if result else 0,
                    "trades": result.trades_count if result else 0
                })
        
        return {
            "x_param": param1.name,
            "y_param": param2.name,
            "x_values": param1.get_values(),
            "y_values": param2.get_values(),
            "results": results
        }
    
    # ==================== UTILITIES ====================
    
    def get_top_results(self, n: int = 10) -> List[OptimizationResult]:
        """Get top N results"""
        return self.results[:n]
    
    def to_dict(self) -> Dict:
        """Convert optimizer state to dictionary"""
        return {
            "config": self.config.to_dict(),
            "results_count": len(self.results),
            "best": self.best_result.to_dict() if self.best_result else None,
            "tested": self._tested_count,
            "total": self._total_count
        }


# ==================== SCORE CALCULATORS ====================

def calculate_advanced_score(
    trades: List[Dict],
    equity_curve: List[Dict],
    initial_capital: float = 10000.0
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate advanced optimization score.
    Balances profit, risk, and consistency.
    
    Returns:
        Tuple of (score, metrics dict)
    """
    if not trades or len(trades) < 5:
        return float('-inf'), {}
    
    # Basic metrics
    pnls = [float(t.get('pnl', 0)) for t in trades]
    
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p < 0]
    
    total_trades = len(trades)
    win_count = len(wins)
    
    win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
    
    # Profit metrics
    total_profit = sum(wins) if wins else 0
    total_loss = abs(sum(losses)) if losses else 0
    net_profit = total_profit - total_loss
    
    profit_factor = (total_profit / total_loss) if total_loss > 0 else 999
    profit_factor = min(profit_factor, 100)
    
    # Max drawdown
    max_dd = 0
    peak = initial_capital
    for eq in equity_curve:
        value = eq.get('value', initial_capital)
        if value > peak:
            peak = value
        dd = (peak - value) / peak * 100
        if dd > max_dd:
            max_dd = dd
    
    # Final capital
    final_capital = equity_curve[-1].get('value', initial_capital) if equity_curve else initial_capital
    profit_pct = (final_capital / initial_capital - 1) * 100
    
    # Sharpe-like ratio
    if len(pnls) > 1:
        avg_return = np.mean(pnls)
        std_return = np.std(pnls)
        sharpe = (avg_return / std_return) if std_return > 0 else 0
    else:
        sharpe = 0
    
    # TP1 hit rate
    tp1_hits = sum(1 for t in trades if 1 in t.get('tp_hit', []))
    tp1_hit_rate = (tp1_hits / total_trades * 100) if total_trades > 0 else 0
    
    # Consistency (low std of returns is good)
    consistency_score = 100 / (1 + np.std(pnls)) if pnls else 0
    
    # Recovery factor
    recovery_factor = (profit_pct / max_dd) if max_dd > 0 else profit_pct
    
    # Calculate composite score
    score = (
        profit_pct * 0.30 +           # 30% weight on profit
        win_rate * 0.15 +             # 15% on win rate
        profit_factor * 5 * 0.15 +    # 15% on profit factor
        tp1_hit_rate * 0.10 +         # 10% on TP1 accuracy
        sharpe * 10 * 0.10 +          # 10% on risk-adjusted return
        consistency_score * 0.10 +    # 10% on consistency
        -max_dd * 0.10                # 10% penalty for drawdown
    )
    
    # Penalize if too few trades
    if total_trades < 30:
        score *= 0.8
    
    metrics = {
        "profit_pct": round(profit_pct, 2),
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 2),
        "max_drawdown": round(max_dd, 2),
        "sharpe": round(sharpe, 2),
        "tp1_hit_rate": round(tp1_hit_rate, 2),
        "total_trades": total_trades,
        "final_capital": round(final_capital, 2),
        "recovery_factor": round(recovery_factor, 2)
    }
    
    return float(score), metrics
