"""
Komas Trading Server - Preset Generator
=======================================
Abstract interface for preset generators.

Features:
- Define generation strategy
- Batch generation with progress
- Export generated presets
- Validation before saving

Version: 1.0
Chat: #29 — Presets Architecture
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Iterator, Callable
from dataclasses import dataclass
import logging

from .base import BasePreset, PresetConfig, PresetSource
from .trg_preset import TRGPreset
from .dominant_preset import DominantPreset

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result of preset generation"""
    total_generated: int
    total_saved: int
    total_skipped: int
    total_errors: int
    errors: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_generated": self.total_generated,
            "total_saved": self.total_saved,
            "total_skipped": self.total_skipped,
            "total_errors": self.total_errors,
            "errors": self.errors[:10],  # Limit error list
        }


class BasePresetGenerator(ABC):
    """
    Abstract base class for preset generators.
    
    Subclasses implement specific generation strategies:
    - SystemPresetGenerator: Generate all 200 TRG / 125 Dominant presets
    - OptimizedPresetGenerator: Generate from optimization results
    - CustomPresetGenerator: User-defined generation rules
    """
    
    def __init__(self, save_to_db: bool = True):
        """
        Initialize generator.
        
        Args:
            save_to_db: Whether to save generated presets to database
        """
        self.save_to_db = save_to_db
        self._db = None
        self._progress_callback: Optional[Callable[[int, int], None]] = None
    
    @abstractmethod
    def get_generator_name(self) -> str:
        """Return generator name for logging"""
        pass
    
    @abstractmethod
    def generate_all(self) -> Iterator[BasePreset]:
        """
        Generate all presets.
        
        Yields:
            BasePreset instances one by one
        """
        pass
    
    @abstractmethod
    def get_total_count(self) -> int:
        """
        Get total number of presets to generate.
        Used for progress tracking.
        """
        pass
    
    def set_progress_callback(self, callback: Callable[[int, int], None]) -> None:
        """
        Set progress callback.
        
        Args:
            callback: Function(current, total) called during generation
        """
        self._progress_callback = callback
    
    def run(self, replace_existing: bool = False) -> GenerationResult:
        """
        Run full generation process.
        
        Args:
            replace_existing: If True, delete existing presets first
            
        Returns:
            GenerationResult with statistics
        """
        total = self.get_total_count()
        generated = 0
        saved = 0
        skipped = 0
        errors_list = []
        
        logger.info(f"[{self.get_generator_name()}] Starting generation of {total} presets")
        
        # Get database
        if self.save_to_db:
            try:
                from app.database import presets_db
                self._db = presets_db
                presets_db.ensure_presets_table()
            except ImportError as e:
                logger.error(f"Database not available: {e}")
                self._db = None
        
        # Generate presets
        for preset in self.generate_all():
            generated += 1
            
            # Progress callback
            if self._progress_callback:
                self._progress_callback(generated, total)
            
            # Validate
            is_valid, validation_errors = preset.validate()
            if not is_valid:
                errors_list.append(f"{preset.id}: {validation_errors}")
                skipped += 1
                continue
            
            # Save
            if self.save_to_db and self._db:
                try:
                    self._db.create_preset(
                        preset_id=preset.id,
                        name=preset.name,
                        indicator_type=preset.config.indicator_type,
                        params=preset.params,
                        category=preset.config.category,
                        source=preset.config.source,
                        description=preset.config.description,
                        tags=preset.config.tags,
                    )
                    saved += 1
                except ValueError as e:
                    # Already exists
                    if replace_existing:
                        try:
                            self._db.delete_preset(preset.id)
                            self._db.create_preset(
                                preset_id=preset.id,
                                name=preset.name,
                                indicator_type=preset.config.indicator_type,
                                params=preset.params,
                                category=preset.config.category,
                                source=preset.config.source,
                                description=preset.config.description,
                                tags=preset.config.tags,
                            )
                            saved += 1
                        except Exception as e2:
                            errors_list.append(f"{preset.id}: {e2}")
                            skipped += 1
                    else:
                        skipped += 1
                except Exception as e:
                    errors_list.append(f"{preset.id}: {e}")
                    skipped += 1
            else:
                saved += 1  # Consider generated as "saved" if no DB
        
        result = GenerationResult(
            total_generated=generated,
            total_saved=saved,
            total_skipped=skipped,
            total_errors=len(errors_list),
            errors=errors_list
        )
        
        logger.info(f"[{self.get_generator_name()}] Generation complete: {result}")
        
        return result


class TRGSystemGenerator(BasePresetGenerator):
    """
    Generator for 200 TRG system presets.
    
    Grid:
    - 8 i1 values: [14, 25, 40, 60, 80, 110, 150, 200]
    - 5 i2 values: [2.0, 3.0, 4.0, 5.5, 7.5]
    - 5 filter profiles: [N, T, M, S, F]
    
    Total: 8 × 5 × 5 = 200 presets
    """
    
    def get_generator_name(self) -> str:
        return "TRG System Generator"
    
    def get_total_count(self) -> int:
        return len(TRGPreset.I1_VALUES) * len(TRGPreset.I2_VALUES) * len(TRGPreset.FILTER_PROFILES)
    
    def generate_all(self) -> Iterator[BasePreset]:
        """Generate all 200 TRG presets"""
        from .base import FilterProfile
        
        for i1 in TRGPreset.I1_VALUES:
            for i2 in TRGPreset.I2_VALUES:
                for profile in TRGPreset.FILTER_PROFILES:
                    preset = TRGPreset.create_system_preset(i1, i2, profile)
                    yield preset


class DominantSystemGenerator(BasePresetGenerator):
    """
    Generator for Dominant system presets from GG Pine Script strategies.
    
    Total: 125 presets (loaded via seed_dominant_presets.py)
    Note: get_system_presets_data() contains only examples.
    """
    
    def get_generator_name(self) -> str:
        return "Dominant System Generator"
    
    def get_total_count(self) -> int:
        return len(DominantPreset.get_system_presets_data())
    
    def generate_all(self) -> Iterator[BasePreset]:
        """Generate all Dominant presets"""
        for preset in DominantPreset.generate_system_presets():
            yield preset


class CombinedSystemGenerator(BasePresetGenerator):
    """
    Generator for all system presets (TRG + Dominant).
    
    Total: 200 TRG + 125 Dominant = 325 presets
    """
    
    def get_generator_name(self) -> str:
        return "Combined System Generator"
    
    def get_total_count(self) -> int:
        return (
            len(TRGPreset.I1_VALUES) * len(TRGPreset.I2_VALUES) * len(TRGPreset.FILTER_PROFILES) +
            len(DominantPreset.get_system_presets_data())
        )
    
    def generate_all(self) -> Iterator[BasePreset]:
        """Generate all system presets"""
        # Generate TRG presets
        trg_gen = TRGSystemGenerator(save_to_db=False)
        for preset in trg_gen.generate_all():
            yield preset
        
        # Generate Dominant presets
        dom_gen = DominantSystemGenerator(save_to_db=False)
        for preset in dom_gen.generate_all():
            yield preset


# ==================== HELPER FUNCTIONS ====================

def generate_trg_presets(
    save_to_db: bool = True,
    replace_existing: bool = False,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> GenerationResult:
    """
    Generate all TRG system presets.
    
    Args:
        save_to_db: Save to database
        replace_existing: Replace existing presets
        progress_callback: Progress callback function
        
    Returns:
        GenerationResult
    """
    generator = TRGSystemGenerator(save_to_db=save_to_db)
    if progress_callback:
        generator.set_progress_callback(progress_callback)
    return generator.run(replace_existing=replace_existing)


def generate_dominant_presets(
    save_to_db: bool = True,
    replace_existing: bool = False,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> GenerationResult:
    """
    Generate all Dominant system presets.
    
    Args:
        save_to_db: Save to database
        replace_existing: Replace existing presets
        progress_callback: Progress callback function
        
    Returns:
        GenerationResult
    """
    generator = DominantSystemGenerator(save_to_db=save_to_db)
    if progress_callback:
        generator.set_progress_callback(progress_callback)
    return generator.run(replace_existing=replace_existing)


def generate_all_system_presets(
    save_to_db: bool = True,
    replace_existing: bool = False,
    progress_callback: Optional[Callable[[int, int], None]] = None
) -> GenerationResult:
    """
    Generate all system presets (TRG + Dominant).
    
    Args:
        save_to_db: Save to database
        replace_existing: Replace existing presets
        progress_callback: Progress callback function
        
    Returns:
        GenerationResult
    """
    generator = CombinedSystemGenerator(save_to_db=save_to_db)
    if progress_callback:
        generator.set_progress_callback(progress_callback)
    return generator.run(replace_existing=replace_existing)


# ==================== EXPORTS ====================

__all__ = [
    "GenerationResult",
    "BasePresetGenerator",
    "TRGSystemGenerator",
    "DominantSystemGenerator",
    "CombinedSystemGenerator",
    "generate_trg_presets",
    "generate_dominant_presets",
    "generate_all_system_presets",
]
