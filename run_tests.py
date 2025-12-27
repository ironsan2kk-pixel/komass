#!/usr/bin/env python
"""
KOMAS Test Runner
Run tests for Dominant indicator filters

Usage:
    python run_tests.py          # Run all tests
    python run_tests.py filters  # Run only filter tests
    python run_tests.py quick    # Run quick smoke tests
"""

import sys
import os
import subprocess

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'app'))
sys.path.insert(0, os.path.dirname(__file__))


def run_pytest(args=None):
    """Run pytest with given arguments"""
    if args is None:
        args = []
    
    cmd = [sys.executable, '-m', 'pytest', 'tests/test_dominant.py', '-v'] + args
    
    print("=" * 60)
    print("KOMAS Test Runner")
    print("=" * 60)
    print(f"Command: {' '.join(cmd)}")
    print("=" * 60)
    print()
    
    result = subprocess.run(cmd, cwd=os.path.dirname(__file__))
    return result.returncode


def run_filter_tests():
    """Run only filter-related tests"""
    return run_pytest(['-k', 'Filter'])


def run_quick_tests():
    """Run quick smoke tests"""
    return run_pytest(['-k', 'test_calculate_returns_dataframe or test_all_signals_pass', '--tb=line'])


def run_all_tests():
    """Run all tests"""
    return run_pytest(['--tb=short'])


def main():
    """Main entry point"""
    if len(sys.argv) > 1:
        # Handle both "quick" and "--quick" formats
        mode = sys.argv[1].lower().lstrip('-')
        
        if mode == 'filters':
            print("Running filter tests only...")
            return run_filter_tests()
        
        elif mode == 'quick':
            print("Running quick smoke tests...")
            return run_quick_tests()
        
        elif mode == 'all':
            print("Running all tests...")
            return run_all_tests()
        
        elif mode in ('h', 'help'):
            print("Usage: python run_tests.py [all|filters|quick]")
            print("  all     - Run all tests")
            print("  filters - Run only filter tests")
            print("  quick   - Run quick smoke tests")
            return 0
        
        else:
            print(f"Unknown mode: {mode}")
            print("Usage: python run_tests.py [all|filters|quick]")
            return 1
    
    else:
        # Default: run all
        print("Running all tests...")
        return run_all_tests()


if __name__ == '__main__':
    sys.exit(main())
