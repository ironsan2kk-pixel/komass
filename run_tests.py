"""
Test Runner for KOMAS v4.0
==========================

Run all unit tests for Signal Score and Multi-TF Loader modules.

Chat #35: Score Multi-TF
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

# Set PYTHONPATH
os.environ["PYTHONPATH"] = str(backend_path / "app")


def run_tests():
    """Run all tests"""
    import pytest
    
    # Test file path
    tests_dir = Path(__file__).parent / "tests"
    
    print("=" * 60)
    print("KOMAS v4.0 - Unit Tests")
    print("Chat #35: Score Multi-TF")
    print("=" * 60)
    print()
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        str(tests_dir),
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
    ])
    
    print()
    print("=" * 60)
    if exit_code == 0:
        print("All tests PASSED!")
    else:
        print("Some tests FAILED!")
    print("=" * 60)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
