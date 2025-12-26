# -*- coding: utf-8 -*-
"""
TRG Plugin
==========
Complete TRG (Trend Range Grid) trading indicator plugin.

Version: 1.5.0 (UI Schema added)
"""

__version__ = "1.5.0"
__author__ = "Komas Team"

# Re-export ui_schema functions for easy access
from .ui_schema import (
    get_ui_schema,
    get_schema_dict,
    get_defaults,
    validate_settings,
    TRGUISchema,
    FieldType,
    SectionType,
    TabType,
)


def get_plugin_info():
    """Get plugin metadata"""
    return {
        "id": "trg",
        "name": "TRG Indicator",
        "version": __version__,
        "author": __author__,
        "description": "Trend Range Grid indicator with full trading system",
        "components": [
            "TRGIndicator",
            "TRGSignalGenerator",
            "TRGTradingSystem",
            "TRGFilterManager",
            "TRGOptimizer",
            "TRGBacktest",
            "TRGUISchema",
        ],
    }


__all__ = [
    "__version__",
    "__author__",
    "get_plugin_info",
    "get_ui_schema",
    "get_schema_dict",
    "get_defaults",
    "validate_settings",
    "TRGUISchema",
    "FieldType",
    "SectionType",
    "TabType",
]
