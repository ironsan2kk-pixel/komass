"""
KOMAS v4.0 — Filter Registry
=============================

Centralized registry for filter classes.
Supports decorator-based registration and dynamic filter discovery.

Usage:
    @register_filter
    class MyFilter(BaseFilter):
        name = "my_filter"
        ...
    
    # Get filter by name
    filter_class = FilterRegistry.get("my_filter")
    
    # Get all filters
    all_filters = FilterRegistry.get_all()
    
    # Get filters by category
    time_filters = FilterRegistry.get_by_category(FilterCategory.TIME)

Chat #37: Filters Architecture
Chat #38: Filters Time
Chat #39: Filters Volatility
Chat #41: Filters Portfolio
Author: KOMAS Team
Version: 4.0
"""

from typing import Dict, List, Optional, Type, Callable
import logging

from .base import BaseFilter, FilterCategory, FilterPriority

logger = logging.getLogger(__name__)


# =============================================================================
# FILTER REGISTRY
# =============================================================================

class FilterRegistry:
    """
    Singleton registry for filter classes.
    """
    _filters: Dict[str, Type[BaseFilter]] = {}
    _initialized: bool = False
    
    @classmethod
    def register(cls, filter_class: Type[BaseFilter]) -> Type[BaseFilter]:
        """
        Register a filter class.
        
        Args:
            filter_class: The filter class to register
            
        Returns:
            The registered filter class (for decorator use)
        """
        name = filter_class.name
        if name in cls._filters:
            logger.warning(f"Filter '{name}' already registered, overwriting")
        
        cls._filters[name] = filter_class
        logger.debug(f"Registered filter: {name} ({filter_class.__name__})")
        return filter_class
    
    @classmethod
    def get(cls, name: str) -> Optional[Type[BaseFilter]]:
        """
        Get a filter class by name.
        
        Args:
            name: Filter name
            
        Returns:
            Filter class or None if not found
        """
        return cls._filters.get(name)
    
    @classmethod
    def get_all(cls) -> Dict[str, Type[BaseFilter]]:
        """
        Get all registered filters.
        
        Returns:
            Dict of filter_name -> filter_class
        """
        return cls._filters.copy()
    
    @classmethod
    def get_names(cls) -> List[str]:
        """
        Get all registered filter names.
        
        Returns:
            List of filter names
        """
        return list(cls._filters.keys())
    
    @classmethod
    def get_by_category(cls, category: FilterCategory) -> Dict[str, Type[BaseFilter]]:
        """
        Get filters by category.
        
        Args:
            category: FilterCategory enum
            
        Returns:
            Dict of filter_name -> filter_class
        """
        return {
            name: fclass 
            for name, fclass in cls._filters.items() 
            if fclass.category == category
        }
    
    @classmethod
    def get_by_priority(cls, priority: FilterPriority) -> Dict[str, Type[BaseFilter]]:
        """
        Get filters by priority.
        
        Args:
            priority: FilterPriority enum
            
        Returns:
            Dict of filter_name -> filter_class
        """
        return {
            name: fclass 
            for name, fclass in cls._filters.items() 
            if fclass.priority == priority
        }
    
    @classmethod
    def get_sorted_by_priority(cls) -> List[Type[BaseFilter]]:
        """
        Get all filters sorted by priority (CRITICAL first).
        
        Returns:
            List of filter classes sorted by priority
        """
        return sorted(cls._filters.values(), key=lambda f: f.priority.value)
    
    @classmethod
    def create_instance(cls, name: str, config: Optional[Dict] = None) -> Optional[BaseFilter]:
        """
        Create a filter instance by name.
        
        Args:
            name: Filter name
            config: Filter configuration
            
        Returns:
            Filter instance or None if not found
        """
        filter_class = cls.get(name)
        if filter_class is None:
            logger.error(f"Filter not found: {name}")
            return None
        
        try:
            return filter_class(config)
        except Exception as e:
            logger.error(f"Failed to create filter '{name}': {e}")
            return None
    
    @classmethod
    def create_instances(cls, configs: Dict[str, Dict]) -> List[BaseFilter]:
        """
        Create multiple filter instances from config dict.
        
        Args:
            configs: Dict of filter_name -> config
            
        Returns:
            List of filter instances
        """
        instances = []
        for name, config in configs.items():
            instance = cls.create_instance(name, config)
            if instance:
                instances.append(instance)
        return instances
    
    @classmethod
    def get_schema(cls) -> Dict[str, Dict]:
        """
        Get combined schema for all filters.
        
        Returns:
            Dict of filter_name -> schema
        """
        return {
            name: {
                "description": fclass.description,
                "category": fclass.category.value,
                "priority": fclass.priority.name,
                "config_schema": fclass({}).get_config_schema()  # Create temp instance
            }
            for name, fclass in cls._filters.items()
        }
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered filters (for testing)."""
        cls._filters.clear()
        cls._initialized = False
    
    @classmethod
    def count(cls) -> int:
        """Get number of registered filters."""
        return len(cls._filters)
    
    @classmethod
    def get_category_summary(cls) -> Dict[str, List[str]]:
        """
        Get summary of filters by category.
        
        Returns:
            Dict of category_name -> list of filter names
        """
        summary = {}
        for category in FilterCategory:
            filters = cls.get_by_category(category)
            if filters:
                summary[category.value] = list(filters.keys())
        return summary


# =============================================================================
# DECORATOR
# =============================================================================

def register_filter(cls: Type[BaseFilter]) -> Type[BaseFilter]:
    """
    Decorator to register a filter class.
    
    Usage:
        @register_filter
        class MyFilter(BaseFilter):
            name = "my_filter"
            ...
    """
    return FilterRegistry.register(cls)


# =============================================================================
# AUTO-DISCOVERY
# =============================================================================

def discover_filters() -> int:
    """
    Discover and register all filters in the filters package.
    This is called automatically when filters are imported.
    
    Returns:
        Number of filters discovered
    """
    if FilterRegistry._initialized:
        return FilterRegistry.count()
    
    # Import filter modules to trigger registration
    from . import time_filters
    from . import volatility_filters
    from . import portfolio_filters
    # Future imports:
    # from . import trend_filters
    # from . import protection_filters
    
    FilterRegistry._initialized = True
    count = FilterRegistry.count()
    logger.info(f"Discovered {count} filters")
    return count
