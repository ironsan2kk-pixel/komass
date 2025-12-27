"""
Komas Trading Server - Preset Registry
======================================
Central registry for managing all presets.

Features:
- Register preset classes (TRG, Dominant, etc.)
- CRUD operations with database backend
- Search and filtering
- Bulk operations (generate, import, export)
- Cache layer for performance

Version: 1.0
Chat: #29 — Presets Architecture
"""

import logging
from typing import Dict, List, Optional, Any, Type, Callable
from datetime import datetime
from functools import lru_cache
import json

from .base import (
    BasePreset, PresetConfig, PresetMetrics,
    IndicatorType, PresetCategory, PresetSource
)
from .trg_preset import TRGPreset
from .dominant_preset import DominantPreset

logger = logging.getLogger(__name__)


class PresetRegistry:
    """
    Central registry for all presets.
    
    Singleton pattern - use get_registry() to get instance.
    
    Features:
    - Register preset classes by indicator type
    - CRUD operations with database
    - Advanced filtering and search
    - Bulk generation and import
    - Caching for performance
    """
    
    _instance: Optional["PresetRegistry"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Preset class registry
        self._preset_classes: Dict[str, Type[BasePreset]] = {}
        
        # In-memory cache
        self._cache: Dict[str, BasePreset] = {}
        self._cache_dirty = True
        
        # Database interface
        self._db = None
        
        # Register built-in preset classes
        self.register_preset_class(IndicatorType.TRG.value, TRGPreset)
        self.register_preset_class(IndicatorType.DOMINANT.value, DominantPreset)
        
        self._initialized = True
        logger.info("PresetRegistry initialized")
    
    # ==================== CLASS REGISTRATION ====================
    
    def register_preset_class(self, indicator_type: str, preset_class: Type[BasePreset]) -> None:
        """
        Register a preset class for an indicator type.
        
        Args:
            indicator_type: Indicator type string (e.g., "trg", "dominant")
            preset_class: Preset class (must inherit from BasePreset)
        """
        if not issubclass(preset_class, BasePreset):
            raise TypeError(f"{preset_class} must inherit from BasePreset")
        
        self._preset_classes[indicator_type] = preset_class
        logger.info(f"Registered preset class for {indicator_type}: {preset_class.__name__}")
    
    def get_preset_class(self, indicator_type: str) -> Optional[Type[BasePreset]]:
        """Get preset class for indicator type"""
        return self._preset_classes.get(indicator_type)
    
    def get_registered_types(self) -> List[str]:
        """Get list of registered indicator types"""
        return list(self._preset_classes.keys())
    
    # ==================== DATABASE INTERFACE ====================
    
    def set_database(self, db) -> None:
        """
        Set database interface for persistence.
        
        Args:
            db: Database module with CRUD functions
        """
        self._db = db
        self._cache_dirty = True
    
    def _get_db(self):
        """Get database interface, lazy import if needed"""
        if self._db is None:
            try:
                from app.database import presets_db
                self._db = presets_db
                presets_db.ensure_presets_table()
            except ImportError:
                logger.warning("Database module not available")
                return None
        return self._db
    
    # ==================== CRUD OPERATIONS ====================
    
    def create(
        self,
        indicator_type: str,
        params: Dict[str, Any],
        name: Optional[str] = None,
        category: Optional[str] = None,
        source: str = "manual",
        **kwargs
    ) -> BasePreset:
        """
        Create a new preset.
        
        Args:
            indicator_type: Type of indicator
            params: Indicator parameters
            name: Optional preset name
            category: Optional category
            source: Preset source
            **kwargs: Additional PresetConfig fields
            
        Returns:
            Created preset instance
        """
        # Get preset class
        preset_class = self.get_preset_class(indicator_type)
        if not preset_class:
            raise ValueError(f"Unknown indicator type: {indicator_type}")
        
        # Create preset
        preset = preset_class.create_from_params(
            params=params,
            name=name,
            category=category,
            source=source,
            **kwargs
        )
        
        # Validate
        is_valid, errors = preset.validate()
        if not is_valid:
            raise ValueError(f"Invalid preset: {errors}")
        
        # Save to database
        db = self._get_db()
        if db:
            db.create_preset(
                preset_id=preset.id,
                name=preset.name,
                indicator_type=indicator_type,
                params=preset.params,
                category=preset.config.category,
                source=source,
                description=kwargs.get('description'),
                symbol=kwargs.get('symbol'),
                timeframe=kwargs.get('timeframe'),
                tags=kwargs.get('tags', []),
            )
        
        # Update cache
        self._cache[preset.id] = preset
        logger.info(f"Created preset: {preset.id}")
        
        return preset
    
    def get(self, preset_id: str) -> Optional[BasePreset]:
        """
        Get preset by ID.
        
        Args:
            preset_id: Preset ID
            
        Returns:
            Preset instance or None if not found
        """
        # Check cache first
        if preset_id in self._cache:
            return self._cache[preset_id]
        
        # Load from database
        db = self._get_db()
        if db:
            data = db.get_preset(preset_id)
            if data:
                preset = self._dict_to_preset(data)
                self._cache[preset_id] = preset
                return preset
        
        return None
    
    def get_by_name(self, name: str, indicator_type: Optional[str] = None) -> Optional[BasePreset]:
        """
        Get preset by name.
        
        Args:
            name: Preset name
            indicator_type: Optional filter by indicator type
            
        Returns:
            Preset instance or None if not found
        """
        db = self._get_db()
        if db:
            data = db.get_preset_by_name(name)
            if data:
                if indicator_type is None or data['indicator_type'] == indicator_type:
                    return self._dict_to_preset(data)
        return None
    
    def update(self, preset_id: str, **updates) -> Optional[BasePreset]:
        """
        Update preset.
        
        Args:
            preset_id: Preset ID
            **updates: Fields to update
            
        Returns:
            Updated preset or None if not found
        """
        preset = self.get(preset_id)
        if not preset:
            return None
        
        # Update params if provided
        if 'params' in updates:
            if not preset.update_params(updates['params']):
                raise ValueError(f"Invalid params: {preset.get_validation_errors()}")
        
        # Update in database
        db = self._get_db()
        if db:
            db.update_preset(preset_id, **updates)
        
        # Update cache
        self._cache[preset_id] = preset
        
        return preset
    
    def delete(self, preset_id: str) -> bool:
        """
        Delete preset.
        
        Args:
            preset_id: Preset ID
            
        Returns:
            True if deleted, False if not found
        """
        db = self._get_db()
        if db:
            deleted = db.delete_preset(preset_id)
            if deleted:
                self._cache.pop(preset_id, None)
                logger.info(f"Deleted preset: {preset_id}")
                return True
        return False
    
    # ==================== QUERY OPERATIONS ====================
    
    def list(
        self,
        indicator_type: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_favorite: Optional[bool] = None,
        search: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[BasePreset]:
        """
        List presets with filtering.
        
        Args:
            indicator_type: Filter by indicator type
            category: Filter by category
            source: Filter by source
            symbol: Filter by symbol
            timeframe: Filter by timeframe
            is_active: Filter by active status
            is_favorite: Filter by favorite status
            search: Search in name/description
            tags: Filter by tags (any match)
            limit: Maximum results
            offset: Result offset
            
        Returns:
            List of matching presets
        """
        db = self._get_db()
        if not db:
            return []
        
        results = db.list_presets(
            indicator_type=indicator_type,
            category=category,
            source=source,
            symbol=symbol,
            timeframe=timeframe,
            is_active=is_active,
            is_favorite=is_favorite,
            search=search,
            limit=limit,
            offset=offset,
        )
        
        presets = []
        for data in results:
            # Filter by tags if specified
            if tags:
                preset_tags = data.get('tags', '').split(',') if data.get('tags') else []
                if not any(t in preset_tags for t in tags):
                    continue
            
            preset = self._dict_to_preset(data)
            presets.append(preset)
        
        return presets
    
    def count(
        self,
        indicator_type: Optional[str] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> int:
        """
        Count presets matching filters.
        
        Returns:
            Count of matching presets
        """
        db = self._get_db()
        if not db:
            return 0
        
        return db.count_presets(
            indicator_type=indicator_type,
            category=category,
            source=source,
            is_active=is_active,
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get preset statistics.
        
        Returns:
            Dictionary with statistics
        """
        db = self._get_db()
        if not db:
            return {}
        
        return db.get_preset_stats()
    
    # ==================== BULK OPERATIONS ====================
    
    def generate_system_presets(
        self,
        indicator_type: str,
        replace_existing: bool = False
    ) -> int:
        """
        Generate all system presets for an indicator type.
        
        Args:
            indicator_type: Indicator type (trg, dominant)
            replace_existing: If True, delete existing system presets first
            
        Returns:
            Number of presets generated
        """
        preset_class = self.get_preset_class(indicator_type)
        if not preset_class:
            raise ValueError(f"Unknown indicator type: {indicator_type}")
        
        # Delete existing if requested
        if replace_existing:
            db = self._get_db()
            if db:
                db.delete_presets_by_source(PresetSource.SYSTEM.value, indicator_type)
        
        # Generate presets based on indicator type
        if indicator_type == IndicatorType.TRG.value:
            presets = TRGPreset.generate_all_system_presets()
        elif indicator_type == IndicatorType.DOMINANT.value:
            presets = DominantPreset.generate_system_presets()
        else:
            presets = []
        
        # Save to database
        db = self._get_db()
        if db:
            for preset in presets:
                try:
                    db.create_preset(
                        preset_id=preset.id,
                        name=preset.name,
                        indicator_type=indicator_type,
                        params=preset.params,
                        category=preset.config.category,
                        source=PresetSource.SYSTEM.value,
                        description=preset.config.description,
                        tags=preset.config.tags,
                    )
                except ValueError as e:
                    # Preset already exists, skip
                    logger.debug(f"Skipping existing preset: {preset.id}")
                    continue
        
        logger.info(f"Generated {len(presets)} system presets for {indicator_type}")
        return len(presets)
    
    def import_from_json(
        self,
        json_data: str,
        source: str = "imported"
    ) -> List[BasePreset]:
        """
        Import presets from JSON.
        
        Args:
            json_data: JSON string with preset(s)
            source: Source tag for imported presets
            
        Returns:
            List of imported presets
        """
        data = json.loads(json_data)
        
        # Handle single preset or list
        if isinstance(data, dict):
            preset_list = [data]
        else:
            preset_list = data
        
        imported = []
        for item in preset_list:
            try:
                indicator_type = item.get('indicator_type', 'trg')
                preset_class = self.get_preset_class(indicator_type)
                if not preset_class:
                    logger.warning(f"Unknown indicator type: {indicator_type}")
                    continue
                
                # Create config
                config = PresetConfig.from_dict({
                    'id': item.get('id', ''),
                    'name': item['name'],
                    'indicator_type': indicator_type,
                    'category': item.get('category', 'mid-term'),
                    'source': source,
                    'params': item.get('params', {}),
                    'description': item.get('description'),
                    'symbol': item.get('symbol'),
                    'timeframe': item.get('timeframe'),
                    'tags': item.get('tags', []),
                })
                
                # Generate ID if not provided
                if not config.id:
                    preset = preset_class(config)
                    config.id = preset._generate_id(config.name)
                
                preset = preset_class(config)
                
                # Validate
                is_valid, errors = preset.validate()
                if not is_valid:
                    logger.warning(f"Invalid preset {config.name}: {errors}")
                    continue
                
                # Save
                db = self._get_db()
                if db:
                    db.create_preset(
                        preset_id=preset.id,
                        name=preset.name,
                        indicator_type=indicator_type,
                        params=preset.params,
                        category=config.category,
                        source=source,
                        description=config.description,
                        symbol=config.symbol,
                        timeframe=config.timeframe,
                        tags=config.tags,
                    )
                
                imported.append(preset)
                
            except Exception as e:
                logger.error(f"Error importing preset: {e}")
                continue
        
        logger.info(f"Imported {len(imported)} presets")
        return imported
    
    def export_to_json(
        self,
        preset_ids: Optional[List[str]] = None,
        indicator_type: Optional[str] = None,
        pretty: bool = True
    ) -> str:
        """
        Export presets to JSON.
        
        Args:
            preset_ids: Optional list of specific preset IDs
            indicator_type: Optional filter by indicator type
            pretty: Pretty print JSON
            
        Returns:
            JSON string
        """
        if preset_ids:
            presets = [self.get(pid) for pid in preset_ids if self.get(pid)]
        else:
            presets = self.list(indicator_type=indicator_type, limit=10000)
        
        data = [p.to_dict() for p in presets]
        
        if pretty:
            return json.dumps(data, indent=2, ensure_ascii=False)
        return json.dumps(data, ensure_ascii=False)
    
    # ==================== HELPER METHODS ====================
    
    def _dict_to_preset(self, data: Dict[str, Any]) -> BasePreset:
        """Convert database dict to preset instance"""
        indicator_type = data.get('indicator_type', 'trg')
        preset_class = self.get_preset_class(indicator_type)
        
        if not preset_class:
            # Fallback to TRG
            preset_class = TRGPreset
            logger.warning(f"Unknown indicator type {indicator_type}, using TRG")
        
        # Parse params if string
        params = data.get('params', {})
        if isinstance(params, str):
            params = json.loads(params)
        
        # Parse tags
        tags = data.get('tags', [])
        if isinstance(tags, str):
            tags = tags.split(',') if tags else []
        
        # Build config
        config = PresetConfig(
            id=data['id'],
            name=data['name'],
            indicator_type=indicator_type,
            category=data.get('category', 'mid-term'),
            source=data.get('source', 'manual'),
            symbol=data.get('symbol'),
            timeframe=data.get('timeframe'),
            params=params,
            description=data.get('description'),
            tags=tags,
            is_active=bool(data.get('is_active', True)),
            is_favorite=bool(data.get('is_favorite', False)),
            created_at=data.get('created_at', datetime.utcnow().isoformat()),
            updated_at=data.get('updated_at', datetime.utcnow().isoformat()),
        )
        
        # Add metrics if available
        if any(k in data for k in ['win_rate', 'profit_factor', 'total_profit_percent']):
            config.metrics = PresetMetrics(
                win_rate=data.get('win_rate'),
                profit_factor=data.get('profit_factor'),
                total_profit_percent=data.get('total_profit_percent'),
                max_drawdown_percent=data.get('max_drawdown_percent'),
                sharpe_ratio=data.get('sharpe_ratio'),
            )
        
        return preset_class(config)
    
    def clear_cache(self) -> None:
        """Clear the preset cache"""
        self._cache.clear()
        self._cache_dirty = True
    
    def get_cache_size(self) -> int:
        """Get number of cached presets"""
        return len(self._cache)


# ==================== MODULE-LEVEL FUNCTIONS ====================

_registry: Optional[PresetRegistry] = None


def get_registry() -> PresetRegistry:
    """
    Get the global preset registry instance.
    
    Returns:
        PresetRegistry singleton
    """
    global _registry
    if _registry is None:
        _registry = PresetRegistry()
    return _registry


def register_preset_class(indicator_type: str, preset_class: Type[BasePreset]) -> None:
    """Register a preset class for an indicator type"""
    get_registry().register_preset_class(indicator_type, preset_class)


# ==================== EXPORTS ====================

__all__ = [
    "PresetRegistry",
    "get_registry",
    "register_preset_class",
]
