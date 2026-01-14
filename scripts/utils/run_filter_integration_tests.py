#!/usr/bin/env python
"""
KOMAS v4.0 — Filter Integration Test Runner
=============================================

Run filter integration tests from command line.

Usage:
    python run_filter_integration_tests.py
    python run_filter_integration_tests.py -v  # verbose
    python run_filter_integration_tests.py --filter "TestFilterManager"  # specific class

Chat #43: Filters Integration
"""

import sys
import os

# Add paths
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(project_root, 'backend', 'app'))
sys.path.insert(0, os.path.join(project_root, 'backend'))
sys.path.insert(0, project_root)

# Run tests
if __name__ == "__main__":
    import pytest
    
    # Default arguments
    args = [
        os.path.join(project_root, 'tests', 'test_filter_integration.py'),
        '-v',
        '--tb=short',
        '-x',  # Stop on first failure
    ]
    
    # Add any additional arguments from command line
    if len(sys.argv) > 1:
        args.extend(sys.argv[1:])
    
    # Run pytest
    exit_code = pytest.main(args)
    sys.exit(exit_code)
