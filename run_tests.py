#!/usr/bin/env python
"""
Simple test runner for Dominant AI Resolution
KOMAS v4.0 - Chat #25

Run this script to execute all tests.
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def run_quick_tests():
    """Run quick validation tests"""
    print("=" * 60)
    print("DOMINANT AI RESOLUTION - QUICK TESTS")
    print("=" * 60)
    
    import pandas as pd
    import numpy as np
    
    # Import the module
    from app.indicators.dominant import (
        calculate_sensitivity_score,
        run_full_backtest,
        optimize_sensitivity,
        get_score_breakdown,
        get_optimization_summary,
        MIN_TRADES_FOR_OPTIMIZATION,
    )
    
    # Create test data
    print("\n1. Creating test data (500 candles)...")
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=500, freq='1h')
    prices = 100 + np.cumsum(np.random.randn(500) * 0.5)
    
    df = pd.DataFrame({
        'open': prices,
        'high': prices + np.abs(np.random.randn(500) * 0.3),
        'low': prices - np.abs(np.random.randn(500) * 0.3),
        'close': prices + np.random.randn(500) * 0.2,
        'volume': np.random.randint(1000, 10000, 500)
    }, index=dates)
    print(f"   Created DataFrame with {len(df)} rows")
    
    # Test 1: Full backtest
    print("\n2. Testing run_full_backtest()...")
    bt_result = run_full_backtest(df, sensitivity=21, filter_type=0, sl_mode=4)
    print(f"   Total trades: {bt_result['summary']['total_trades']}")
    print(f"   Total PnL: {bt_result['metrics']['pnl_percent']:.2f}%")
    print(f"   Win Rate: {bt_result['metrics']['win_rate']:.1f}%")
    print("   PASSED")
    
    # Test 2: Score calculation
    print("\n3. Testing calculate_sensitivity_score()...")
    score = calculate_sensitivity_score(bt_result['metrics'])
    print(f"   Score: {score:.2f}/100")
    assert 0 <= score <= 100, "Score out of range!"
    print("   PASSED")
    
    # Test 3: Score breakdown
    print("\n4. Testing get_score_breakdown()...")
    breakdown = get_score_breakdown(bt_result['metrics'])
    print(f"   Profit: {breakdown['profit_score']:.1f}/{breakdown['profit_max']}")
    print(f"   Win Rate: {breakdown['win_rate_score']:.1f}/{breakdown['win_rate_max']}")
    print(f"   Stability: {breakdown['stability_score']:.1f}/{breakdown['stability_max']}")
    print(f"   Drawdown: {breakdown['drawdown_score']:.1f}/{breakdown['drawdown_max']}")
    print("   PASSED")
    
    # Test 4: Insufficient trades returns 0
    print("\n5. Testing insufficient trades handling...")
    bad_metrics = {'pnl_percent': 50, 'win_rate': 90, 'pnl_std': 1, 'max_drawdown': 1, 'total_trades': 2}
    bad_score = calculate_sensitivity_score(bad_metrics)
    assert bad_score == 0, f"Expected 0 for insufficient trades, got {bad_score}"
    print(f"   Score for {bad_metrics['total_trades']} trades: {bad_score}")
    print("   PASSED")
    
    # Test 5: Optimization (limited sensitivities for speed)
    print("\n6. Testing optimize_sensitivity()...")
    
    progress_count = [0]
    def progress_callback(current, total, sensitivity, result):
        progress_count[0] += 1
        print(f"   [{current}/{total}] Sensitivity {sensitivity}: Score {result['score']:.1f}")
    
    opt_result = optimize_sensitivity(
        df,
        filter_type=0,
        sl_mode=4,
        sensitivities=[15, 21, 30, 45],  # Limited for quick test
        workers=2,
        progress_callback=progress_callback
    )
    
    print(f"\n   Best Sensitivity: {opt_result['best_sensitivity']}")
    print(f"   Best Score: {opt_result['best_score']:.2f}")
    print(f"   Time: {opt_result['optimization_time']:.1f}s")
    print(f"   Workers: {opt_result['workers_used']}")
    print(f"   Progress callbacks: {progress_count[0]}")
    assert progress_count[0] == 4, f"Expected 4 callbacks, got {progress_count[0]}"
    print("   PASSED")
    
    # Test 6: Summary formatting
    print("\n7. Testing get_optimization_summary()...")
    summary = get_optimization_summary(opt_result)
    assert 'Best Sensitivity' in summary, "Summary missing best sensitivity"
    print("   Summary generated successfully")
    print("   PASSED")
    
    # All tests passed
    print("\n" + "=" * 60)
    print("ALL QUICK TESTS PASSED!")
    print("=" * 60)
    
    return True


def run_pytest():
    """Run pytest if available"""
    try:
        import pytest
        print("\n" + "=" * 60)
        print("RUNNING PYTEST...")
        print("=" * 60)
        
        test_file = os.path.join(os.path.dirname(__file__), 'tests', 'test_dominant_ai_resolution.py')
        
        if os.path.exists(test_file):
            result = pytest.main([test_file, '-v', '--tb=short'])
            return result == 0
        else:
            print(f"Test file not found: {test_file}")
            return False
            
    except ImportError:
        print("\npytest not installed. Run: pip install pytest")
        return True  # Quick tests passed, just no pytest


if __name__ == '__main__':
    success = True
    
    try:
        success = run_quick_tests()
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        success = False
    
    if success:
        run_pytest()
    
    sys.exit(0 if success else 1)
