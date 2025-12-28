"""
KOMAS v4.0 — Portfolio Filters Test Runner
===========================================

Run all portfolio filter tests with detailed output.

Chat #41: Filters Portfolio
"""

import sys
import os
import unittest
from datetime import datetime

# Ensure proper path
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(script_dir, 'backend', 'app')
tests_path = os.path.join(script_dir, 'tests')

sys.path.insert(0, backend_path)
sys.path.insert(0, tests_path)

def run_tests():
    """Run all portfolio filter tests."""
    print("="*70)
    print("KOMAS v4.0 - Portfolio Filters Unit Tests")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    print()
    
    # Discover and run tests
    loader = unittest.TestLoader()
    
    try:
        # Try to import test module directly
        from test_portfolio_filters import (
            TestSectorHelpers,
            TestCorrelationHelpers,
            TestDirectionHelpers,
            TestSectorCounts,
            TestCorrelationFilter,
            TestDirectionFilter,
            TestSectorFilter,
            TestPortfolioSummary,
            TestConfigValidation,
            TestPortfolioProfiles,
            TestPortfolioFilterChain,
            TestPortfolioFiltersIntegration,
        )
        
        suite = unittest.TestSuite()
        
        # Add all test classes
        test_classes = [
            TestSectorHelpers,
            TestCorrelationHelpers,
            TestDirectionHelpers,
            TestSectorCounts,
            TestCorrelationFilter,
            TestDirectionFilter,
            TestSectorFilter,
            TestPortfolioSummary,
            TestConfigValidation,
            TestPortfolioProfiles,
            TestPortfolioFilterChain,
            TestPortfolioFiltersIntegration,
        ]
        
        for test_class in test_classes:
            suite.addTests(loader.loadTestsFromTestCase(test_class))
        
    except ImportError as e:
        print(f"Error importing tests: {e}")
        print("Trying to discover tests from directory...")
        suite = loader.discover(tests_path, pattern='test_portfolio*.py')
    
    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures:  {len(result.failures)}")
    print(f"Errors:    {len(result.errors)}")
    print(f"Skipped:   {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print()
    
    if result.wasSuccessful():
        print("[SUCCESS] All tests passed!")
        return 0
    else:
        print("[FAILED] Some tests failed!")
        
        if result.failures:
            print("\nFailed tests:")
            for test, traceback in result.failures:
                print(f"  - {test}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}")
        
        return 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
