#!/usr/bin/env python
"""
KOMAS Test Runner
Runs all unit tests for the Dominant indicator

Usage:
    python run_tests.py
    python run_tests.py -v          # Verbose
    python run_tests.py --signals   # Only signal tests
"""

import sys
import os
import argparse

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'app'))
sys.path.insert(0, os.path.dirname(__file__))

def run_all_tests(verbose=False, pattern=None):
    """Run all tests using pytest"""
    import pytest
    
    args = ['tests/test_dominant.py']
    
    if verbose:
        args.append('-v')
    else:
        args.append('-q')
    
    if pattern:
        args.extend(['-k', pattern])
    
    # Run pytest
    result = pytest.main(args)
    
    return result

def run_quick_test():
    """Run a quick test to verify imports work"""
    print("=" * 60)
    print("KOMAS Dominant Indicator - Quick Test")
    print("=" * 60)
    
    try:
        from indicators.dominant import (
            calculate_dominant,
            generate_signals,
            get_signal_summary,
            get_latest_signal,
            SIGNAL_LONG,
            SIGNAL_SHORT,
            SIGNAL_NONE,
        )
        print("[OK] Imports successful")
        
        import pandas as pd
        import numpy as np
        
        # Create test data
        np.random.seed(42)
        n = 100
        prices = 100 + np.cumsum(np.random.randn(n) * 0.5)
        
        df = pd.DataFrame({
            'open': prices,
            'high': prices + np.abs(np.random.randn(n) * 0.3),
            'low': prices - np.abs(np.random.randn(n) * 0.3),
            'close': prices + np.random.randn(n) * 0.2,
            'volume': np.random.randint(1000, 10000, n)
        })
        print(f"[OK] Test data created: {len(df)} rows")
        
        # Test calculate_dominant
        result = calculate_dominant(df, sensitivity=21)
        assert 'high_channel' in result.columns
        assert 'fib_236' in result.columns
        print("[OK] calculate_dominant works")
        
        # Test generate_signals
        result = generate_signals(df, sensitivity=21)
        assert 'can_long' in result.columns
        assert 'can_short' in result.columns
        assert 'signal' in result.columns
        assert 'is_long_trend' in result.columns
        assert 'is_short_trend' in result.columns
        print("[OK] generate_signals works")
        
        # Test signal summary
        summary = get_signal_summary(result)
        print(f"[OK] Signal summary: {summary['long_signals']} longs, {summary['short_signals']} shorts")
        
        # Test latest signal
        latest = get_latest_signal(result)
        print(f"[OK] Latest signal: {latest['signal']}")
        
        # Verify mutual exclusion
        both = (result['can_long'] & result['can_short']).sum()
        assert both == 0, "Mutual exclusion violated!"
        print("[OK] Mutual exclusion verified")
        
        # Verify trend exclusion
        both_trends = (result['is_long_trend'] & result['is_short_trend']).sum()
        assert both_trends == 0, "Trend exclusion violated!"
        print("[OK] Trend exclusion verified")
        
        print()
        print("=" * 60)
        print("All quick tests passed!")
        print("=" * 60)
        return 0
        
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    parser = argparse.ArgumentParser(description='Run KOMAS tests')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-q', '--quick', action='store_true', help='Quick test only')
    parser.add_argument('--signals', action='store_true', help='Only signal tests')
    parser.add_argument('--trends', action='store_true', help='Only trend tracking tests')
    
    args = parser.parse_args()
    
    if args.quick:
        return run_quick_test()
    
    pattern = None
    if args.signals:
        pattern = 'Signal'
    elif args.trends:
        pattern = 'Trend'
    
    return run_all_tests(verbose=args.verbose, pattern=pattern)

if __name__ == '__main__':
    sys.exit(main())
