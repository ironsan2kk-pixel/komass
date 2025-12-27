"""
Test runner for Dominant Indicator
Run this from project root with PYTHONPATH set to backend/app
"""

import sys
import os

# Add path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'app'))

def main():
    passed = 0
    failed = 0
    
    def run_test(name, test_func):
        nonlocal passed, failed
        try:
            test_func()
            print(f'  [PASS] {name}')
            passed += 1
        except Exception as e:
            print(f'  [FAIL] {name}: {e}')
            failed += 1
    
    # Import after path setup
    try:
        from indicators.dominant import (
            calculate_dominant, 
            get_current_levels, 
            validate_sensitivity,
            get_indicator_info
        )
        import pandas as pd
        import numpy as np
    except ImportError as e:
        print(f'Import error: {e}')
        return 1
    
    print('Running tests...')
    print()
    
    # Test 1: Basic calculation
    def test_basic():
        df = pd.DataFrame({
            'open': [100]*5, 
            'high': [110]*5, 
            'low': [90]*5, 
            'close': [100]*5, 
            'volume': [1000]*5
        })
        result = calculate_dominant(df, 21)
        assert 'high_channel' in result.columns
        assert 'fib_236' in result.columns
    
    run_test('Basic calculation', test_basic)
    
    # Test 2: Fibonacci levels
    def test_fibonacci():
        df = pd.DataFrame({
            'open': [150]*10, 
            'high': [200]*10, 
            'low': [100]*10, 
            'close': [150]*10, 
            'volume': [1000]*10
        })
        result = calculate_dominant(df, 3)
        assert abs(result['fib_236'].iloc[-1] - 123.6) < 0.1
        assert abs(result['fib_500'].iloc[-1] - 150.0) < 0.1
    
    run_test('Fibonacci levels', test_fibonacci)
    
    # Test 3: Sensitivity validation
    def test_validation():
        assert validate_sensitivity(5) == 12
        assert validate_sensitivity(100) == 60
        assert validate_sensitivity(21) == 21
    
    run_test('Sensitivity validation', test_validation)
    
    # Test 4: Channel calculation
    def test_channel():
        df = pd.DataFrame({
            'open': [100] * 10,
            'high': [100, 110, 105, 115, 108, 120, 112, 118, 115, 122],
            'low': [90, 95, 92, 98, 94, 100, 96, 102, 98, 104],
            'close': [100] * 10,
            'volume': [1000] * 10
        })
        result = calculate_dominant(df, 5)
        assert result['high_channel'].iloc[4] == 115
        assert result['low_channel'].iloc[4] == 90
    
    run_test('Channel calculation', test_channel)
    
    # Test 5: Get current levels
    def test_levels():
        df = pd.DataFrame({
            'open': [150]*10, 
            'high': [200]*10, 
            'low': [100]*10, 
            'close': [150]*10, 
            'volume': [1000]*10
        })
        result = calculate_dominant(df, 3)
        levels = get_current_levels(result)
        assert levels['high_channel'] == 200
        assert levels['low_channel'] == 100
    
    run_test('Get current levels', test_levels)
    
    # Test 6: Get indicator info
    def test_info():
        info = get_indicator_info()
        assert info['name'] == 'Dominant'
        assert info['parameters']['sensitivity']['min'] == 12
        assert info['parameters']['sensitivity']['max'] == 60
    
    run_test('Get indicator info', test_info)
    
    # Test 7: Fibonacci ordering
    def test_ordering():
        df = pd.DataFrame({
            'open': [150]*10, 
            'high': [200]*10, 
            'low': [100]*10, 
            'close': [150]*10, 
            'volume': [1000]*10
        })
        result = calculate_dominant(df, 3)
        low = result['low_channel'].iloc[-1]
        high = result['high_channel'].iloc[-1]
        f236 = result['fib_236'].iloc[-1]
        f382 = result['fib_382'].iloc[-1]
        f500 = result['fib_500'].iloc[-1]
        f618 = result['fib_618'].iloc[-1]
        assert low < f236 < f382 < f500 < f618 < high
    
    run_test('Fibonacci ordering', test_ordering)
    
    # Test 8: Price position zero range
    def test_price_position():
        df = pd.DataFrame({
            'open': [100]*5, 
            'high': [100]*5, 
            'low': [100]*5, 
            'close': [100]*5, 
            'volume': [1000]*5
        })
        result = calculate_dominant(df, 3)
        assert result['price_position'].iloc[-1] == 0.5
    
    run_test('Price position (zero range)', test_price_position)
    
    # Results
    print()
    print('=' * 40)
    print(f'Results: {passed} passed, {failed} failed')
    print('=' * 40)
    
    return 1 if failed > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
