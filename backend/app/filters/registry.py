"""
KOMAS Trading System - Filter Registry
======================================

Registry for managing and instantiating filters.

Features:
- Register filter classes
- Get filter by name
- List all registered filters
- Create filter instances with config
- Filter discovery and metadata

Chat #37: Filters Architecture
Author: KOMAS Team
Version: 4.0
"""

from typing import Dict, List, Optional, Type, Any, Set
import logging
from .base import (
    BaseFilter,
    FilterCategory,
    FilterPriority,
    FilterConfig,
)

logger = logging.getLogger(__name__)


# =============================================================================
# FILTER REGISTRY
# =============================================================================

class FilterRegistry:
    """
    Registry for managing filter classes.
    
    Provides centralized management of all available filters:
    - Registration of filter classes
    - Lookup by name or category
    - Factory method for creating instances
    - Metadata and schema access
    
    Usage:
        registry = FilterRegistry()
        registry.register(SessionFilter)
        registry.register(ATRFilter)
        
        # Create filter instance
        session_filter = registry.create("session_filter", {"sessions": ["london"]})
        
        # List filters by category
        time_filters = registry.list_by_category(FilterCategory.TIME)
    """
    
    _instance: Optional["FilterRegistry"] = None
    
    def __new__(cls) -> "FilterRegistry":
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize registry"""
        if self._initialized:
            return
        
        self._filters: Dict[str, Type[BaseFilter]] = {}
        self._categories: Dict[FilterCategory, Set[str]] = {
            cat: set() for cat in FilterCategory
        }
        self._initialized = True
        logger.info("FilterRegistry initialized")
    
    def register(self, filter_class: Type[BaseFilter]) -> bool:
        """
        Register a filter class.
        
        Args:
            filter_class: Filter class to register
            
        Returns:
            True if registration successful
            
        Raises:
            ValueError: If filter_class is not a valid BaseFilter subclass
        """
        # Validate
        if not isinstance(filter_class, type):
            raise ValueError(f"Expected a class, got {type(filter_class)}")
        
        if not issubclass(filter_class, BaseFilter):
            raise ValueError(f"{filter_class} must be a subclass of BaseFilter")
        
        if filter_class is BaseFilter:
            raise ValueError("Cannot register abstract BaseFilter")
        
        # Get filter name
        name = filter_class.name
        
        if not name or name == "base_filter":
            raise ValueError(f"Filter must have a unique name, got: {name}")
        
        # Check for duplicate
        if name in self._filters:
            existing = self._filters[name]
            if existing is not filter_class:
                logger.warning(
                    f"Overwriting filter '{name}': {existing.__name__} -> {filter_class.__name__}"
                )
        
        # Register
        self._filters[name] = filter_class
        self._categories[filter_class.category].add(name)
        
        logger.debug(f"Registered filter: {name} ({filter_class.__name__})")
        return True
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a filter by name.
        
        Args:
            name: Filter name to unregister
            
        Returns:
            True if unregistered, False if not found
        """
        if name not in self._filters:
            logger.warning(f"Filter not found: {name}")
            return False
        
        filter_class = self._filters.pop(name)
        self._categories[filter_class.category].discard(name)
        
        logger.debug(f"Unregistered filter: {name}")
        return True
    
    def get(self, name: str) -> Optional[Type[BaseFilter]]:
        """
        Get filter class by name.
        
        Args:
            name: Filter name
            
        Returns:
            Filter class or None if not found
        """
        return self._filters.get(name)
    
    def create(self, name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseFilter]:
        """
        Create a filter instance.
        
        Args:
            name: Filter name
            config: Filter configuration
            
        Returns:
            Filter instance or None if not found
        """
        filter_class = self.get(name)
        if filter_class is None:
            logger.warning(f"Cannot create filter, not found: {name}")
            return None
        
        try:
            instance = filter_class(config or {})
            logger.debug(f"Created filter instance: {name}")
            return instance
        except Exception as e:
            logger.error(f"Error creating filter {name}: {e}")
            return None
    
    def create_from_config(self, filter_config: FilterConfig) -> Optional[BaseFilter]:
        """
        Create a filter instance from FilterConfig.
        
        Args:
            filter_config: FilterConfig object
            
        Returns:
            Filter instance or None if not found
        """
        instance = self.create(filter_config.name, filter_config.params)
        if instance:
            instance.enabled = filter_config.enabled
        return instance
    
    def has(self, name: str) -> bool:
        """Check if filter is registered"""
        return name in self._filters
    
    def list_all(self) -> List[str]:
        """
        List all registered filter names.
        
        Returns:
            List of filter names
        """
        return list(self._filters.keys())
    
    def list_by_category(self, category: FilterCategory) -> List[str]:
        """
        List filter names by category.
        
        Args:
            category: Filter category
            
        Returns:
            List of filter names in that category
        """
        return list(self._categories.get(category, set()))
    
    def list_by_priority(self, priority: FilterPriority) -> List[str]:
        """
        List filter names by priority.
        
        Args:
            priority: Filter priority
            
        Returns:
            List of filter names with that priority
        """
        return [
            name for name, cls in self._filters.items()
            if cls.priority == priority
        ]
    
    def get_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get filter information.
        
        Args:
            name: Filter name
            
        Returns:
            Dict with filter info or None
        """
        filter_class = self.get(name)
        if filter_class is None:
            return None
        
        return {
            "name": filter_class.name,
            "display_name": filter_class.display_name,
            "description": filter_class.description,
            "category": filter_class.category.value,
            "priority": filter_class.priority.value,
            "version": filter_class.version,
        }
    
    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get filter configuration schema.
        
        Args:
            name: Filter name
            
        Returns:
            JSON schema dict or None
        """
        filter_class = self.get(name)
        if filter_class is None:
            return None
        
        try:
            # Create temporary instance to get schema
            temp = filter_class({})
            return temp.get_config_schema()
        except Exception as e:
            logger.error(f"Error getting schema for {name}: {e}")
            return None
    
    def get_all_info(self) -> List[Dict[str, Any]]:
        """
        Get information for all registered filters.
        
        Returns:
            List of filter info dicts
        """
        result = []
        for name in self.list_all():
            info = self.get_info(name)
            if info:
                result.append(info)
        return result
    
    def get_categories_summary(self) -> Dict[str, int]:
        """
        Get count of filters per category.
        
        Returns:
            Dict mapping category name to filter count
        """
        return {
            cat.value: len(filters)
            for cat, filters in self._categories.items()
        }
    
    def clear(self) -> None:
        """Clear all registered filters (for testing)"""
        self._filters.clear()
        for cat in self._categories:
            self._categories[cat].clear()
        logger.info("FilterRegistry cleared")
    
    def __len__(self) -> int:
        """Number of registered filters"""
        return len(self._filters)
    
    def __contains__(self, name: str) -> bool:
        """Check if filter is registered"""
        return name in self._filters
    
    def __iter__(self):
        """Iterate over filter names"""
        return iter(self._filters)
    
    def __repr__(self) -> str:
        return f"FilterRegistry(filters={len(self._filters)})"


# =============================================================================
# GLOBAL REGISTRY INSTANCE
# =============================================================================

# Global singleton instance
_global_registry: Optional[FilterRegistry] = None


def get_registry() -> FilterRegistry:
    """
    Get the global filter registry instance.
    
    Returns:
        FilterRegistry singleton
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = FilterRegistry()
    return _global_registry


def register_filter(filter_class: Type[BaseFilter]) -> Type[BaseFilter]:
    """
    Decorator to register a filter class.
    
    Usage:
        @register_filter
        class MyFilter(BaseFilter):
            name = "my_filter"
            ...
    
    Args:
        filter_class: Filter class to register
        
    Returns:
        The same filter class (for decorator chaining)
    """
    get_registry().register(filter_class)
    return filter_class


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "FilterRegistry",
    "get_registry",
    "register_filter",
]
