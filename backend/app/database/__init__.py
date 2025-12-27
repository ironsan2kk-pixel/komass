"""
Komas Trading Server - Database Module
======================================
Database operations for presets.

Tables:
- dominant_presets: 125 Dominant indicator presets (existing in repo)
- trg_presets: 200 TRG indicator presets (new)

Chat: #30 — Presets TRG Generator
"""

# TRG Presets (new table: trg_presets)
from .trg_presets_db import (
    ensure_trg_presets_table,
    create_trg_preset,
    get_trg_preset,
    get_trg_preset_by_name,
    list_trg_presets,
    count_trg_presets,
    update_trg_preset,
    delete_trg_preset,
    delete_trg_system_presets,
    bulk_create_trg_presets,
    get_trg_preset_stats,
    verify_trg_system_presets,
)

__all__ = [
    # TRG presets
    "ensure_trg_presets_table",
    "create_trg_preset",
    "get_trg_preset",
    "get_trg_preset_by_name",
    "list_trg_presets",
    "count_trg_presets",
    "update_trg_preset",
    "delete_trg_preset",
    "delete_trg_system_presets",
    "bulk_create_trg_presets",
    "get_trg_preset_stats",
    "verify_trg_system_presets",
]
