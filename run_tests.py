"""
Test Runner for KOMAS v4.0
==========================

Run unit tests for Signal Score and Multi-TF Loader modules.

Chat #35: Score Multi-TF
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path / "app"))

# Set PYTHONPATH
os.environ["PYTHONPATH"] = str(backend_path / "app")


def run_tests():
    """Run multi-TF loader tests only"""
    import pytest
    
    # Specific test file path
    test_file = Path(__file__).parent / "tests" / "test_multi_tf_loader.py"
    
    print("=" * 60)
    print("KOMAS v4.0 - Unit Tests")
    print("Chat #35: Score Multi-TF")
    print("=" * 60)
    print()
    print(f"Running: {test_file.name}")
    print()
    
    # Run pytest with verbose output - specific file only
    exit_code = pytest.main([
        str(test_file),
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
