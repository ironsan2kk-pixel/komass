#!/usr/bin/env python
"""
Test Runner for KOMAS Chat #36: Score UI
========================================

Runs all tests for the Signal Score UI integration.

Usage:
    python run_tests.py
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "app"))

def run_tests():
    """Run all Score UI tests"""
    import pytest
    
    test_path = Path(__file__).parent / "tests" / "test_score_ui.py"
    
    print("=" * 60)
    print("KOMAS Chat #36: Signal Score UI Tests")
    print("=" * 60)
    print()
    
    # Run pytest
    exit_code = pytest.main([
        str(test_path),
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
    ])
    
    print()
    if exit_code == 0:
        print("=" * 60)
        print("All tests PASSED!")
        print("=" * 60)
    else:
        print("=" * 60)
        print("Some tests FAILED!")
        print("=" * 60)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
