"""
Run Time Filters Tests
======================

Comprehensive test runner for time filters.

Usage:
    python run_tests.py

Chat #38: Filters Time
Author: KOMAS Team
Version: 4.0
"""

import sys
import os
import unittest
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))


def run_tests():
    """Run all time filter tests"""
    print("=" * 60)
    print("KOMAS v4.0 - Time Filters Unit Tests")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=str(project_root / "tests"),
        pattern="test_time_filters.py"
    )
    
    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print()
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print()
        print("SUCCESS: All tests passed!")
        return 0
    else:
        print()
        print("FAILED: Some tests failed")
        
        if result.failures:
            print()
            print("Failures:")
            for test, traceback in result.failures:
                print(f"  - {test}")
        
        if result.errors:
            print()
            print("Errors:")
            for test, traceback in result.errors:
                print(f"  - {test}")
        
        return 1


if __name__ == "__main__":
    sys.exit(run_tests())
