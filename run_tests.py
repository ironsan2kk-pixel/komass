"""
Test runner for KOMAS Dominant Indicator tests
Runs all SL mode tests and reports results

Usage: python run_tests.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'app'))

# Run basic tests first (no pytest required)
def run_basic_tests():
    """Run basic tests without pytest"""
    print("=" * 60)
    print("KOMAS Dominant SL Modes - Basic Tests")
    print("=" * 60)
    print()
    
    errors = []
    passed = 0
    
    try:
        from indicators.dominant import (
            # Constants
            SL_MODE_FIXED,
            SL_MODE_AFTER_TP1,
            SL_MODE_AFTER_TP2,
            SL_MODE_AFTER_TP3,
            SL_MODE_CASCADE,
            SL_MODE_NAMES,
            SIGNAL_LONG,
            SIGNAL_SHORT,
            
            # Functions
            validate_sl_mode,
            calculate_tp_levels,
            calculate_initial_sl,
            calculate_sl_level,
            get_sl_mode_info,
            track_position,
            generate_signals,
        )
        print("[OK] Import successful")
        passed += 1
    except Exception as e:
        errors.append(f"Import failed: {e}")
        print(f"[FAIL] Import failed: {e}")
        return
    
    # Test 1: SL Mode Constants
    print("\n--- Test: SL Mode Constants ---")
    try:
        assert SL_MODE_FIXED == 0
        assert SL_MODE_AFTER_TP1 == 1
        assert SL_MODE_AFTER_TP2 == 2
        assert SL_MODE_AFTER_TP3 == 3
        assert SL_MODE_CASCADE == 4
        assert len(SL_MODE_NAMES) == 5
        print("[OK] SL mode constants correct")
        passed += 1
    except AssertionError as e:
        errors.append(f"SL mode constants: {e}")
        print(f"[FAIL] {e}")
    
    # Test 2: validate_sl_mode
    print("\n--- Test: validate_sl_mode ---")
    try:
        assert validate_sl_mode(0) == 0
        assert validate_sl_mode(4) == 4
        assert validate_sl_mode(-1) == 0
        assert validate_sl_mode(10) == 4
        assert validate_sl_mode(None) == 0
        print("[OK] validate_sl_mode works correctly")
        passed += 1
    except AssertionError as e:
        errors.append(f"validate_sl_mode: {e}")
        print(f"[FAIL] {e}")
    
    # Test 3: calculate_tp_levels
    print("\n--- Test: calculate_tp_levels ---")
    try:
        # Long TPs above entry
        tps = calculate_tp_levels(100.0, SIGNAL_LONG, [1.0, 2.0, 3.0])
        assert tps[0] == 101.0
        assert tps[1] == 102.0
        assert tps[2] == 103.0
        
        # Short TPs below entry
        tps = calculate_tp_levels(100.0, SIGNAL_SHORT, [1.0, 2.0, 3.0])
        assert tps[0] == 99.0
        assert tps[1] == 98.0
        assert tps[2] == 97.0
        
        print("[OK] calculate_tp_levels works correctly")
        passed += 1
    except AssertionError as e:
        errors.append(f"calculate_tp_levels: {e}")
        print(f"[FAIL] {e}")
    
    # Test 4: calculate_initial_sl
    print("\n--- Test: calculate_initial_sl ---")
    try:
        # Long SL below entry
        sl = calculate_initial_sl(100.0, SIGNAL_LONG, 2.0)
        assert sl == 98.0
        
        # Short SL above entry
        sl = calculate_initial_sl(100.0, SIGNAL_SHORT, 2.0)
        assert sl == 102.0
        
        print("[OK] calculate_initial_sl works correctly")
        passed += 1
    except AssertionError as e:
        errors.append(f"calculate_initial_sl: {e}")
        print(f"[FAIL] {e}")
    
    # Test 5: SL Mode Fixed
    print("\n--- Test: SL Mode Fixed (Mode 0) ---")
    try:
        sl = calculate_sl_level(
            entry_price=100.0,
            direction=SIGNAL_LONG,
            sl_percent=2.0,
            sl_mode=SL_MODE_FIXED,
            tps_hit=[True, True, True, True]
        )
        assert sl == 98.0, f"Expected 98.0, got {sl}"
        print("[OK] Fixed mode: SL never moves")
        passed += 1
    except AssertionError as e:
        errors.append(f"SL Mode Fixed: {e}")
        print(f"[FAIL] {e}")
    
    # Test 6: SL Mode After TP1
    print("\n--- Test: SL Mode After TP1 (Mode 1) ---")
    try:
        # Before TP1
        sl = calculate_sl_level(100.0, SIGNAL_LONG, 2.0, SL_MODE_AFTER_TP1, [False, False])
        assert sl == 98.0, f"Before TP1: expected 98.0, got {sl}"
        
        # After TP1
        sl = calculate_sl_level(100.0, SIGNAL_LONG, 2.0, SL_MODE_AFTER_TP1, [True, False])
        assert sl == 100.0, f"After TP1: expected 100.0 (breakeven), got {sl}"
        
        print("[OK] After TP1 mode: moves to breakeven")
        passed += 1
    except AssertionError as e:
        errors.append(f"SL Mode After TP1: {e}")
        print(f"[FAIL] {e}")
    
    # Test 7: SL Mode After TP2
    print("\n--- Test: SL Mode After TP2 (Mode 2) ---")
    try:
        # After TP1 only - no move
        sl = calculate_sl_level(100.0, SIGNAL_LONG, 2.0, SL_MODE_AFTER_TP2, [True, False])
        assert sl == 98.0, f"After TP1 only: expected 98.0, got {sl}"
        
        # After TP2
        sl = calculate_sl_level(100.0, SIGNAL_LONG, 2.0, SL_MODE_AFTER_TP2, [True, True])
        assert sl == 100.0, f"After TP2: expected 100.0, got {sl}"
        
        print("[OK] After TP2 mode: moves only after TP2")
        passed += 1
    except AssertionError as e:
        errors.append(f"SL Mode After TP2: {e}")
        print(f"[FAIL] {e}")
    
    # Test 8: SL Mode After TP3
    print("\n--- Test: SL Mode After TP3 (Mode 3) ---")
    try:
        # After TP2 only - no move
        sl = calculate_sl_level(100.0, SIGNAL_LONG, 2.0, SL_MODE_AFTER_TP3, [True, True, False])
        assert sl == 98.0, f"After TP2 only: expected 98.0, got {sl}"
        
        # After TP3
        sl = calculate_sl_level(100.0, SIGNAL_LONG, 2.0, SL_MODE_AFTER_TP3, [True, True, True])
        assert sl == 100.0, f"After TP3: expected 100.0, got {sl}"
        
        print("[OK] After TP3 mode: moves only after TP3")
        passed += 1
    except AssertionError as e:
        errors.append(f"SL Mode After TP3: {e}")
        print(f"[FAIL] {e}")
    
    # Test 9: SL Mode Cascade
    print("\n--- Test: SL Mode Cascade (Mode 4) ---")
    try:
        tp_levels = [101.0, 102.0, 103.0, 105.0]
        
        # No TPs - original SL
        sl = calculate_sl_level(100.0, SIGNAL_LONG, 2.0, SL_MODE_CASCADE, 
                               [False, False, False, False], tp_levels)
        assert sl == 98.0, f"No TPs: expected 98.0, got {sl}"
        
        # After TP1 - breakeven
        sl = calculate_sl_level(100.0, SIGNAL_LONG, 2.0, SL_MODE_CASCADE,
                               [True, False, False, False], tp_levels)
        assert sl == 100.0, f"After TP1: expected 100.0, got {sl}"
        
        # After TP2 - trail to TP1
        sl = calculate_sl_level(100.0, SIGNAL_LONG, 2.0, SL_MODE_CASCADE,
                               [True, True, False, False], tp_levels)
        assert sl == 101.0, f"After TP2: expected 101.0, got {sl}"
        
        # After TP3 - trail to TP2
        sl = calculate_sl_level(100.0, SIGNAL_LONG, 2.0, SL_MODE_CASCADE,
                               [True, True, True, False], tp_levels)
        assert sl == 102.0, f"After TP3: expected 102.0, got {sl}"
        
        print("[OK] Cascade mode: trails correctly")
        passed += 1
    except AssertionError as e:
        errors.append(f"SL Mode Cascade: {e}")
        print(f"[FAIL] {e}")
    
    # Test 10: get_sl_mode_info
    print("\n--- Test: get_sl_mode_info ---")
    try:
        # Single mode
        info = get_sl_mode_info(SL_MODE_CASCADE)
        assert info['id'] == 4
        assert info['trails'] == True
        assert 'trail_logic' in info
        
        # All modes
        all_info = get_sl_mode_info()
        assert len(all_info) == 5
        
        print("[OK] get_sl_mode_info works correctly")
        passed += 1
    except AssertionError as e:
        errors.append(f"get_sl_mode_info: {e}")
        print(f"[FAIL] {e}")
    
    # Test 11: track_position
    print("\n--- Test: track_position ---")
    try:
        import pandas as pd
        import numpy as np
        
        # Create simple uptrend data
        n = 20
        prices = [100 + i * 0.3 for i in range(n)]
        
        df = pd.DataFrame({
            'open': prices,
            'high': [p + 0.2 for p in prices],
            'low': [p - 0.1 for p in prices],
            'close': prices,
            'volume': [5000] * n
        })
        
        result = track_position(
            df=df,
            entry_idx=0,
            direction=SIGNAL_LONG,
            entry_price=100.0,
            sl_percent=2.0,
            tp_percents=[1.0, 2.0],
            sl_mode=SL_MODE_FIXED
        )
        
        assert 'exit_reason' in result
        assert 'pnl_percent' in result
        assert 'tps_hit' in result
        assert 'sl_history' in result
        assert 'duration' in result
        
        print("[OK] track_position works correctly")
        passed += 1
    except Exception as e:
        errors.append(f"track_position: {e}")
        print(f"[FAIL] {e}")
    
    # Test 12: Short position SL modes
    print("\n--- Test: Short Position SL Modes ---")
    try:
        # Short position - SL above entry
        sl = calculate_initial_sl(100.0, SIGNAL_SHORT, 2.0)
        assert sl == 102.0, f"Short initial SL: expected 102.0, got {sl}"
        
        # Short cascade
        tp_levels = [99.0, 98.0, 97.0]  # Short TPs below entry
        sl = calculate_sl_level(100.0, SIGNAL_SHORT, 2.0, SL_MODE_CASCADE,
                               [True, True, False], tp_levels)
        assert sl == 99.0, f"Short cascade after TP2: expected 99.0, got {sl}"
        
        print("[OK] Short position SL modes work correctly")
        passed += 1
    except AssertionError as e:
        errors.append(f"Short Position SL Modes: {e}")
        print(f"[FAIL] {e}")
    
    # Summary
    print()
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {len(errors)} failed")
    print("=" * 60)
    
    if errors:
        print("\nErrors:")
        for err in errors:
            print(f"  - {err}")
        return 1
    else:
        print("\nAll basic tests passed!")
        return 0


def run_pytest_tests():
    """Run full pytest test suite if pytest is available"""
    try:
        import pytest
        print("\n" + "=" * 60)
        print("Running pytest test suite...")
        print("=" * 60 + "\n")
        
        # Run tests
        exit_code = pytest.main([
            'tests/test_dominant_sl_modes.py',
            '-v',
            '--tb=short'
        ])
        
        return exit_code
    except ImportError:
        print("\npytest not installed, skipping full test suite")
        print("Install with: pip install pytest")
        return 0


if __name__ == '__main__':
    # Run basic tests
    basic_result = run_basic_tests()
    
    # Run pytest if available
    pytest_result = run_pytest_tests()
    
    # Exit with appropriate code
    sys.exit(basic_result or pytest_result)
