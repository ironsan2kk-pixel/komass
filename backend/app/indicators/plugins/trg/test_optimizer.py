"""
Tests for TRG Optimizer
=======================
Run: python -m pytest test_optimizer.py -v
Or:  python test_optimizer.py
"""

import sys
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Tuple, Dict

# Add path for imports
sys.path.insert(0, 'backend/app/indicators/plugins/trg')

from optimizer import (
    # Enums
    OptimizationMode,
    OptimizationMetric,
    SearchMethod,
    
    # Data classes
    ParameterRange,
    OptimizationResult,
    OptimizationProgress,
    HeatmapCell,
    HeatmapResult,
    TRGOptimizerConfig,
    
    # Main class
    TRGOptimizer,
    
    # Presets
    TRGParameterPresets,
    
    # Functions
    calculate_advanced_score,
    calculate_simple_score,
)


# ============================================================
# TEST DATA GENERATORS
# ============================================================

def generate_test_df(days: int = 100) -> pd.DataFrame:
    """Generate test price data"""
    np.random.seed(42)
    
    dates = pd.date_range(end=datetime.now(), periods=days * 24, freq='1h')
    
    # Generate realistic price movement
    base_price = 50000
    returns = np.random.normal(0, 0.02, len(dates))
    prices = base_price * np.exp(np.cumsum(returns))
    
    # Create OHLCV
    data = {
        'open': prices * (1 + np.random.uniform(-0.005, 0.005, len(dates))),
        'high': prices * (1 + np.random.uniform(0, 0.02, len(dates))),
        'low': prices * (1 - np.random.uniform(0, 0.02, len(dates))),
        'close': prices,
        'volume': np.random.uniform(100, 1000, len(dates))
    }
    
    df = pd.DataFrame(data, index=dates)
    df['high'] = df[['open', 'high', 'close']].max(axis=1)
    df['low'] = df[['open', 'low', 'close']].min(axis=1)
    
    return df


def generate_test_trades(
    count: int = 50,
    win_rate: float = 0.6
) -> List[Dict]:
    """Generate test trades"""
    np.random.seed(42)
    
    trades = []
    for i in range(count):
        is_win = np.random.random() < win_rate
        
        pnl = np.random.uniform(1, 5) if is_win else np.random.uniform(-3, -0.5)
        
        trade = {
            "id": i + 1,
            "type": "LONG" if i % 2 == 0 else "SHORT",
            "entry_time": datetime.now() - timedelta(days=count - i),
            "exit_time": datetime.now() - timedelta(days=count - i - 1),
            "entry_price": 50000 + np.random.uniform(-1000, 1000),
            "exit_price": 50000 + np.random.uniform(-1000, 1000),
            "pnl": pnl,
            "exit_reason": f"TP{np.random.randint(1, 4)}" if is_win else "SL",
            "is_reentry": i % 5 == 0
        }
        trades.append(trade)
    
    return trades


def generate_test_equity(
    trades: List[Dict],
    initial_capital: float = 10000
) -> List[Dict]:
    """Generate equity curve from trades"""
    equity = [{"timestamp": datetime.now() - timedelta(days=len(trades) + 1), "value": initial_capital}]
    
    current_value = initial_capital
    for trade in trades:
        pnl_amount = current_value * (trade["pnl"] / 100)
        current_value += pnl_amount
        equity.append({
            "timestamp": trade["exit_time"],
            "value": current_value
        })
    
    return equity


def mock_backtest_fn(df: pd.DataFrame, settings: Dict) -> Tuple[List, List]:
    """Mock backtest function for testing"""
    # Simulate different performance based on parameters
    i1 = settings.get("trg_atr_length", 45)
    i2 = settings.get("trg_multiplier", 4)
    
    # Better params = better win rate
    win_rate = 0.4 + (i1 / 500) + (i2 / 50)
    win_rate = min(0.8, max(0.3, win_rate))
    
    trades = generate_test_trades(30, win_rate)
    equity = generate_test_equity(trades, settings.get("initial_capital", 10000))
    
    return trades, equity


# ============================================================
# TESTS
# ============================================================

def test_parameter_range():
    """Test ParameterRange class"""
    print("\n=== Test: ParameterRange ===")
    
    # Integer range
    int_range = ParameterRange("i1", 20, 100, 20, "int")
    values = int_range.get_values()
    print(f"  Int range values: {values}")
    assert len(values) == 5  # 20, 40, 60, 80, 100
    assert all(isinstance(v, int) for v in values)
    
    # Float range
    float_range = ParameterRange("i2", 2.0, 5.0, 0.5, "float")
    values = float_range.get_values()
    print(f"  Float range values: {values}")
    assert len(values) == 7  # 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0
    
    # to_dict
    d = int_range.to_dict()
    assert d["name"] == "i1"
    assert d["values_count"] == 5
    
    print("  ✅ ParameterRange passed")
    return True


def test_optimization_result():
    """Test OptimizationResult class"""
    print("\n=== Test: OptimizationResult ===")
    
    result = OptimizationResult(
        params={"i1": 45, "i2": 4.0},
        score=85.5,
        metrics={"win_rate": 65.5, "profit_pct": 25.3},
        trades_count=50
    )
    
    d = result.to_dict()
    print(f"  Result dict: {d}")
    
    assert d["score"] == 85.5
    assert d["params"]["i1"] == 45
    assert d["trades"] == 50
    
    print("  ✅ OptimizationResult passed")
    return True


def test_optimizer_config():
    """Test TRGOptimizerConfig class"""
    print("\n=== Test: TRGOptimizerConfig ===")
    
    # Default config
    config = TRGOptimizerConfig()
    assert config.mode == OptimizationMode.INDICATOR
    assert config.metric == OptimizationMetric.ADVANCED
    
    # Custom config
    config = TRGOptimizerConfig(
        mode=OptimizationMode.FULL,
        metric=OptimizationMetric.PROFIT_FACTOR,
        full_mode_depth="deep",
        max_tests=1000
    )
    
    workers = config.get_worker_count()
    print(f"  Worker count: {workers}")
    assert workers >= 1
    
    d = config.to_dict()
    print(f"  Config dict: {d}")
    assert d["mode"] == "full"
    assert d["max_tests"] == 1000
    
    print("  ✅ TRGOptimizerConfig passed")
    return True


def test_calculate_advanced_score():
    """Test advanced scoring function"""
    print("\n=== Test: calculate_advanced_score ===")
    
    # Good trades
    trades = generate_test_trades(50, win_rate=0.7)
    equity = generate_test_equity(trades)
    
    score, metrics = calculate_advanced_score(trades, equity)
    
    print(f"  Score: {score}")
    print(f"  Win rate: {metrics.get('win_rate')}")
    print(f"  Profit: {metrics.get('profit_pct')}")
    print(f"  Max DD: {metrics.get('max_drawdown')}")
    
    assert score > 0
    assert "win_rate" in metrics
    assert "profit_pct" in metrics
    assert "max_drawdown" in metrics
    
    # Bad trades
    bad_trades = generate_test_trades(50, win_rate=0.2)
    bad_equity = generate_test_equity(bad_trades)
    
    bad_score, bad_metrics = calculate_advanced_score(bad_trades, bad_equity)
    print(f"  Bad score: {bad_score}")
    
    assert bad_score < score  # Bad performance = lower score
    
    # Too few trades
    empty_score, _ = calculate_advanced_score([], [])
    assert empty_score == float('-inf')
    
    print("  ✅ calculate_advanced_score passed")
    return True


def test_calculate_simple_score():
    """Test simple scoring function"""
    print("\n=== Test: calculate_simple_score ===")
    
    trades = generate_test_trades(30, win_rate=0.6)
    equity = generate_test_equity(trades)
    
    # Test different metrics
    for metric in OptimizationMetric:
        score, metrics = calculate_simple_score(trades, equity, metric)
        print(f"  {metric.value}: score={score:.2f}")
        assert "total_trades" in metrics
    
    print("  ✅ calculate_simple_score passed")
    return True


def test_parameter_presets():
    """Test TRGParameterPresets"""
    print("\n=== Test: TRGParameterPresets ===")
    
    presets = TRGParameterPresets
    
    # Check ranges exist
    assert len(presets.I1_FULL) > 10
    assert len(presets.I2_FULL) > 5
    assert len(presets.TP_CONFIGS) >= 10
    assert len(presets.SL_PERCENTS) >= 5
    
    print(f"  I1 full range: {len(presets.I1_FULL)} values")
    print(f"  I2 full range: {len(presets.I2_FULL)} values")
    print(f"  TP configs: {len(presets.TP_CONFIGS)}")
    print(f"  SL percents: {len(presets.SL_PERCENTS)}")
    
    # Test filter configs
    for depth in ["fast", "medium", "deep"]:
        configs = presets.get_filter_configs(depth)
        print(f"  Filter configs ({depth}): {len(configs)}")
        assert len(configs) > 0
    
    print("  ✅ TRGParameterPresets passed")
    return True


def test_optimizer_parameter_generation():
    """Test parameter generation for different modes"""
    print("\n=== Test: Parameter Generation ===")
    
    optimizer = TRGOptimizer(TRGOptimizerConfig(full_mode_depth="fast"))
    settings = {"initial_capital": 10000}
    
    modes_expected = {
        OptimizationMode.INDICATOR: 25,   # ~i1 * i2 combinations (fast mode)
        OptimizationMode.TP: 10,          # TP configs
        OptimizationMode.SL: 20,          # SL * modes
        OptimizationMode.FILTERS: 3,      # Filter configs (fast mode)
    }
    
    for mode, min_expected in modes_expected.items():
        params = optimizer.get_parameter_ranges(mode, settings)
        print(f"  {mode.value}: {len(params)} combinations")
        assert len(params) >= min_expected, f"{mode.value} should have >= {min_expected} params"
    
    print("  ✅ Parameter generation passed")
    return True


def test_optimizer_create():
    """Test TRGOptimizer creation"""
    print("\n=== Test: TRGOptimizer Creation ===")
    
    # Default
    optimizer = TRGOptimizer()
    assert optimizer.config.mode == OptimizationMode.INDICATOR
    
    # Custom config
    config = TRGOptimizerConfig(
        mode=OptimizationMode.TP,
        metric=OptimizationMetric.PROFIT,
        max_tests=100
    )
    optimizer = TRGOptimizer(config)
    assert optimizer.config.mode == OptimizationMode.TP
    
    print("  ✅ TRGOptimizer creation passed")
    return True


def test_optimizer_stream():
    """Test optimization stream"""
    print("\n=== Test: Optimization Stream ===")
    
    df = generate_test_df(30)  # 30 days
    settings = {
        "initial_capital": 10000,
        "trg_atr_length": 45,
        "trg_multiplier": 4.0
    }
    
    config = TRGOptimizerConfig(
        mode=OptimizationMode.INDICATOR,
        metric=OptimizationMetric.ADVANCED,
        full_mode_depth="fast",
        max_tests=20  # Limit for testing
    )
    optimizer = TRGOptimizer(config)
    
    events = []
    for event in optimizer.optimize_stream(df, settings, mock_backtest_fn):
        events.append(event)
        if event.get("type") == "test":
            print(f"  Progress: {event.get('tested')}/{event.get('total')}")
    
    # Check events
    event_types = [e.get("type") for e in events]
    print(f"  Event types: {set(event_types)}")
    
    assert "start" in event_types
    assert "test" in event_types
    assert "complete" in event_types
    
    # Check complete event
    complete = [e for e in events if e.get("type") == "complete"][0]
    assert "best" in complete
    assert "total_tested" in complete
    assert complete["total_tested"] > 0
    
    print(f"  Best score: {complete['best']['score'] if complete['best'] else 'N/A'}")
    print(f"  Total tested: {complete['total_tested']}")
    
    print("  ✅ Optimization stream passed")
    return True


def test_heatmap_generation():
    """Test heatmap generation"""
    print("\n=== Test: Heatmap Generation ===")
    
    df = generate_test_df(30)
    settings = {
        "initial_capital": 10000,
        "trg_atr_length": 45,
        "trg_multiplier": 4.0
    }
    
    optimizer = TRGOptimizer()
    
    # Small heatmap for testing
    result = optimizer.generate_heatmap(
        df, settings, mock_backtest_fn,
        i1_range=[30, 45, 60],
        i2_range=[3, 4, 5]
    )
    
    print(f"  Cells: {len(result.cells)}")
    print(f"  I1 range: {result.i1_range}")
    print(f"  I2 range: {result.i2_range}")
    print(f"  Duration: {result.duration_seconds:.2f}s")
    
    assert len(result.cells) == 9  # 3 * 3
    assert result.best_cell is not None
    
    # Check best cell
    print(f"  Best: i1={result.best_cell.i1}, i2={result.best_cell.i2}")
    print(f"  Best PnL: {result.best_cell.pnl:.2f}%")
    
    # to_dict
    d = result.to_dict()
    assert "results" in d
    assert len(d["results"]) == 9
    
    print("  ✅ Heatmap generation passed")
    return True


def test_full_optimization_configs():
    """Test full mode configuration generation"""
    print("\n=== Test: Full Optimization Configs ===")
    
    optimizer = TRGOptimizer()
    settings = {"initial_capital": 10000}
    
    for depth in ["fast", "medium"]:
        optimizer.config.full_mode_depth = depth
        configs = optimizer.get_parameter_ranges(OptimizationMode.FULL, settings)
        print(f"  {depth}: {len(configs)} configs")
        assert len(configs) > 50
        
        # Check config structure
        first = configs[0]
        assert "i1" in first
        assert "i2" in first
    
    print("  ✅ Full optimization configs passed")
    return True


def test_tp_custom_configs():
    """Test custom TP configuration generation"""
    print("\n=== Test: TP Custom Configs ===")
    
    config = TRGOptimizerConfig(
        mode=OptimizationMode.TP_CUSTOM,
        tp_range_percent=30.0,
        tp_step_percent=15.0
    )
    optimizer = TRGOptimizer(config)
    
    current_settings = {
        "tp1_percent": 1.0,
        "tp2_percent": 2.0,
        "tp3_percent": 3.5,
        "tp4_percent": 5.0,
        "tp1_amount": 50,
        "tp2_amount": 30,
        "tp3_amount": 15,
        "tp4_amount": 5
    }
    
    configs = optimizer.get_parameter_ranges(OptimizationMode.TP_CUSTOM, current_settings)
    print(f"  Generated configs: {len(configs)}")
    
    assert len(configs) > 0
    
    # Check values are around current settings
    for cfg in configs[:3]:
        tp_cfg = cfg.get("tp_config", {})
        print(f"  TP1: {tp_cfg.get('tp1')}, TP2: {tp_cfg.get('tp2')}")
    
    print("  ✅ TP Custom configs passed")
    return True


def test_progress_tracking():
    """Test progress tracking"""
    print("\n=== Test: Progress Tracking ===")
    
    progress = OptimizationProgress(
        tested=50,
        total=100,
        progress_pct=50.0,
        eta_seconds=120.5
    )
    
    d = progress.to_dict()
    print(f"  Progress dict: {d}")
    
    assert d["tested"] == 50
    assert d["total"] == 100
    assert d["progress"] == 50.0
    assert d["eta_seconds"] == 120 or d["eta_seconds"] == 121  # Rounded
    
    # With best result
    progress.current_best = OptimizationResult(
        params={"i1": 45},
        score=75.0,
        metrics={}
    )
    d = progress.to_dict()
    assert d["best"] is not None
    assert d["best"]["score"] == 75.0
    
    print("  ✅ Progress tracking passed")
    return True


def test_export_results():
    """Test results export"""
    print("\n=== Test: Export Results ===")
    
    optimizer = TRGOptimizer()
    
    # Add some mock results
    optimizer.results = [
        OptimizationResult(
            params={"i1": 45, "i2": 4.0},
            score=80.0,
            metrics={"win_rate": 65.0, "profit_pct": 20.0},
            trades_count=50
        ),
        OptimizationResult(
            params={"i1": 60, "i2": 3.0},
            score=75.0,
            metrics={"win_rate": 60.0, "profit_pct": 15.0},
            trades_count=45
        )
    ]
    
    # Export to DataFrame
    df = optimizer.export_results_to_df()
    print(f"  DataFrame shape: {df.shape}")
    print(f"  Columns: {list(df.columns)}")
    
    assert len(df) == 2
    assert "i1" in df.columns
    assert "score" in df.columns
    
    # Get top results
    top = optimizer.get_top_results(1)
    assert len(top) == 1
    assert top[0].score == 80.0
    
    print("  ✅ Export results passed")
    return True


# ============================================================
# MAIN
# ============================================================

def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("TRG OPTIMIZER TESTS")
    print("=" * 60)
    
    tests = [
        test_parameter_range,
        test_optimization_result,
        test_optimizer_config,
        test_calculate_advanced_score,
        test_calculate_simple_score,
        test_parameter_presets,
        test_optimizer_parameter_generation,
        test_optimizer_create,
        test_optimizer_stream,
        test_heatmap_generation,
        test_full_optimization_configs,
        test_tp_custom_configs,
        test_progress_tracking,
        test_export_results,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ FAILED: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED!")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
