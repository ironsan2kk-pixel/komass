"""
Test runner for KOMAS Filter Architecture
=========================================

Run this script to execute all filter tests.
"""

import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent / "backend" / "app"
sys.path.insert(0, str(backend_path))

# Run pytest
if __name__ == "__main__":
    import pytest
    
    test_dir = Path(__file__).parent / "tests"
    
    # Run with verbose output
    exit_code = pytest.main([
        str(test_dir),
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure
    ])
    
    sys.exit(exit_code)
