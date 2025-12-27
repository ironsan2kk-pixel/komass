"""
Pytest configuration for KOMAS v4.0 tests
==========================================

Sets up paths and fixtures for all tests.
"""

import sys
from pathlib import Path

# Add backend app and services to path
backend_app = Path(__file__).parent.parent / "backend" / "app"
services_path = backend_app / "services"

# Insert paths at the beginning
sys.path.insert(0, str(backend_app))
sys.path.insert(0, str(services_path))


def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
