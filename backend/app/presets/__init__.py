"""
Komas Trading Server - Presets Module
=====================================
Comprehensive preset management system for trading indicators.

Architecture:
- BasePreset: Abstract base class for all presets
- TRGPreset: TRG indicator preset (200 system presets)
- DominantPreset: Dominant indicator preset (125 system presets from GG)
- PresetRegistry: Central preset management
- PresetValidator: Parameter validation
- PresetGenerator: Bulk generation

Usage:
    from app.presets import (
        get_registry,
        TRGPreset,
        DominantPreset,
        validate_preset,
        generate_trg_presets,
    )
    
    # Get registry
    registry = get_registry()
    
    # Create preset
    preset = registry.create(
        indicator_type="trg",
        params={"i1": 45, "i2": 4.0},
        name="My Preset"
    )
    
    # Generate all system presets
    result = generate_trg_presets()
    print(f"Generated {result.total_saved} presets")

Version: 1.0
Chat: #29 — Presets Architecture
"""

# Base classes
from .base import (
    # Enums
    IndicatorType,
    PresetCategory,
    PresetSource,
    FilterProfile,
    
    # Data classes
    PresetMetrics,
    PresetConfig,
    
    # Base class
    BasePreset,
)

# Preset implementations
from .trg_preset import TRGPreset
from .dominant_preset import DominantPreset

# Registry
from .registry import (
    PresetRegistry,
    get_registry,
    register_preset_class,
)

# Validator
from .validator import (
    ValidationSeverity,
    ValidationError,
    ValidationResult,
    PresetValidator,
    validate_preset,
    validate_params,
    validate_import,
)

# Generator
from .generator import (
    GenerationResult,
    BasePresetGenerator,
    TRGSystemGenerator,
    DominantSystemGenerator,
    CombinedSystemGenerator,
    generate_trg_presets,
    generate_dominant_presets,
    generate_all_system_presets,
)


# ==================== EXPORTS ====================

__all__ = [
    # Enums
    "IndicatorType",
    "PresetCategory",
    "PresetSource",
    "FilterProfile",
    
    # Data classes
    "PresetMetrics",
    "PresetConfig",
    
    # Base class
    "BasePreset",
    
    # Implementations
    "TRGPreset",
    "DominantPreset",
    
    # Registry
    "PresetRegistry",
    "get_registry",
    "register_preset_class",
    
    # Validator
    "ValidationSeverity",
    "ValidationError",
    "ValidationResult",
    "PresetValidator",
    "validate_preset",
    "validate_params",
    "validate_import",
    
    # Generator
    "GenerationResult",
    "BasePresetGenerator",
    "TRGSystemGenerator",
    "DominantSystemGenerator",
    "CombinedSystemGenerator",
    "generate_trg_presets",
    "generate_dominant_presets",
    "generate_all_system_presets",
]

__version__ = "1.0.0"
