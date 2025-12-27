"""
Test Runner for Signal Score Module
===================================

Run: python run_tests.py
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set PYTHONPATH
os.environ['PYTHONPATH'] = str(project_root)


def main():
    """Run all tests"""
    import pytest
    
    # Run tests with verbose output
    exit_code = pytest.main([
        'tests/test_signal_score.py',
        '-v',
        '-s',
        '--tb=short',
    ])
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
