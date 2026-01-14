#!/usr/bin/env python3
"""
KOMAS Project - Import and Dependency Test
==========================================
Tests all Python modules for import errors and dependency issues
"""

import sys
import os
import importlib
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

print("=" * 70)
print("KOMAS PROJECT - IMPORT TEST")
print("=" * 70)
print()

# Test results
results = {
    "success": [],
    "failed": [],
    "warnings": []
}

# Modules to test
modules_to_test = [
    # Core modules
    ("app.main", "Main Application"),

    # API Routes
    ("app.api.bots_routes", "Bots Routes"),
    ("app.api.calendar_routes", "Calendar Routes"),
    ("app.api.data_routes", "Data Routes"),
    ("app.api.db_routes", "Database Routes"),
    ("app.api.filter_routes", "Filter Routes"),
    ("app.api.heatmap_routes", "Heatmap Routes"),
    ("app.api.indicator_routes", "Indicator Routes"),
    ("app.api.notifications_routes", "Notifications Routes"),
    ("app.api.optimizer_routes", "Optimizer Routes"),
    ("app.api.preset_routes", "Preset Routes"),
    ("app.api.settings_routes", "Settings Routes"),
    ("app.api.signal_routes", "Signal Routes"),
    ("app.api.trg_preset_routes", "TRG Preset Routes"),
    ("app.api.ws", "WebSocket Routes"),

    # Models
    ("app.models.bot", "Bot Model"),
    ("app.models.position", "Position Model"),
    ("app.models.settings", "Settings Model"),

    # Services
    ("app.services.bot_service", "Bot Service"),
    ("app.services.market_service", "Market Service"),
    ("app.services.notification_service", "Notification Service"),
    ("app.services.calendar_service", "Calendar Service"),

    # Core
    ("app.core.database", "Database Core"),
    ("app.core.config", "Config Core"),
]

print("Testing Python module imports...")
print("-" * 70)

for module_name, description in modules_to_test:
    try:
        importlib.import_module(module_name)
        results["success"].append((module_name, description))
        print(f"✅ {description:30s} ({module_name})")
    except ImportError as e:
        results["failed"].append((module_name, description, str(e)))
        print(f"❌ {description:30s} ({module_name})")
        print(f"   Error: {str(e)}")
    except Exception as e:
        results["warnings"].append((module_name, description, str(e)))
        print(f"⚠️  {description:30s} ({module_name})")
        print(f"   Warning: {str(e)}")

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"✅ Successful: {len(results['success'])}")
print(f"❌ Failed:     {len(results['failed'])}")
print(f"⚠️  Warnings:   {len(results['warnings'])}")
print()

if results["failed"]:
    print("FAILED IMPORTS:")
    print("-" * 70)
    for module, desc, error in results["failed"]:
        print(f"  • {desc} ({module})")
        print(f"    {error}")
        print()

if results["warnings"]:
    print("WARNINGS:")
    print("-" * 70)
    for module, desc, error in results["warnings"]:
        print(f"  • {desc} ({module})")
        print(f"    {error}")
        print()

# Exit with error if any imports failed
sys.exit(len(results["failed"]))
