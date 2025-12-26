"""
Komas Trading System - Plugin Registry

Глобальный реестр для индикаторов, фильтров, оптимизаторов и других компонентов.
Позволяет регистрировать и получать плагины по ID.

Автор: Komas Team
Версия: 1.0.0
"""

from typing import Dict, List, Optional, Type, Any, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading

# Для типизации
T = TypeVar('T')


class PluginType(Enum):
    """Типы плагинов в системе"""
    INDICATOR = "indicator"
    TRADING_SYSTEM = "trading_system"
    FILTER = "filter"
    OPTIMIZER = "optimizer"
    BACKTEST = "backtest"


@dataclass
class PluginInfo:
    """Информация о зарегистрированном плагине"""
    id: str
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    cls: Type[Any]  # Класс плагина
    enabled: bool = True
    loaded_at: datetime = field(default_factory=datetime.now)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "plugin_type": self.plugin_type.value,
            "enabled": self.enabled,
            "loaded_at": self.loaded_at.isoformat(),
            "dependencies": self.dependencies,
            "metadata": self.metadata
        }


@dataclass
class PluginBundle:
    """
    Бандл плагина — все компоненты одного плагина
    Например: TRG плагин содержит indicator, trading_system, filters и т.д.
    """
    id: str
    name: str
    version: str
    description: str
    author: str
    manifest_path: Optional[str] = None
    loaded_at: datetime = field(default_factory=datetime.now)
    
    # Компоненты
    indicator: Optional[PluginInfo] = None
    trading_system: Optional[PluginInfo] = None
    optimizer: Optional[PluginInfo] = None
    backtest: Optional[PluginInfo] = None
    filters: Dict[str, PluginInfo] = field(default_factory=dict)
    
    # Дополнительные метаданные
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def component_count(self) -> int:
        """Количество загруженных компонентов"""
        count = 0
        if self.indicator: count += 1
        if self.trading_system: count += 1
        if self.optimizer: count += 1
        if self.backtest: count += 1
        count += len(self.filters)
        return count
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь"""
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "manifest_path": self.manifest_path,
            "loaded_at": self.loaded_at.isoformat(),
            "component_count": self.component_count,
            "components": {
                "indicator": self.indicator.id if self.indicator else None,
                "trading_system": self.trading_system.id if self.trading_system else None,
                "optimizer": self.optimizer.id if self.optimizer else None,
                "backtest": self.backtest.id if self.backtest else None,
                "filters": list(self.filters.keys())
            },
            "metadata": self.metadata
        }


class TypedRegistry(Generic[T]):
    """
    Типизированный реестр для конкретного типа плагинов
    Потокобезопасный доступ
    """
    
    def __init__(self, plugin_type: PluginType):
        self._plugin_type = plugin_type
        self._registry: Dict[str, PluginInfo] = {}
        self._lock = threading.RLock()
    
    def register(
        self,
        plugin_id: str,
        cls: Type[T],
        name: str,
        version: str = "1.0.0",
        description: str = "",
        author: str = "Unknown",
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PluginInfo:
        """
        Регистрация плагина в реестре
        
        Args:
            plugin_id: Уникальный идентификатор
            cls: Класс плагина
            name: Человекочитаемое имя
            version: Версия
            description: Описание
            author: Автор
            dependencies: Зависимости
            metadata: Дополнительные данные
            
        Returns:
            PluginInfo с информацией о зарегистрированном плагине
        """
        with self._lock:
            info = PluginInfo(
                id=plugin_id,
                name=name,
                version=version,
                description=description,
                author=author,
                plugin_type=self._plugin_type,
                cls=cls,
                dependencies=dependencies or [],
                metadata=metadata or {}
            )
            self._registry[plugin_id] = info
            return info
    
    def get(self, plugin_id: str) -> Optional[Type[T]]:
        """Получить класс плагина по ID"""
        with self._lock:
            info = self._registry.get(plugin_id)
            return info.cls if info else None
    
    def get_info(self, plugin_id: str) -> Optional[PluginInfo]:
        """Получить полную информацию о плагине"""
        with self._lock:
            return self._registry.get(plugin_id)
    
    def unregister(self, plugin_id: str) -> bool:
        """
        Удалить плагин из реестра
        
        Returns:
            True если плагин был удалён, False если не найден
        """
        with self._lock:
            if plugin_id in self._registry:
                del self._registry[plugin_id]
                return True
            return False
    
    def list_all(self) -> List[PluginInfo]:
        """Получить список всех зарегистрированных плагинов"""
        with self._lock:
            return list(self._registry.values())
    
    def list_ids(self) -> List[str]:
        """Получить список ID всех плагинов"""
        with self._lock:
            return list(self._registry.keys())
    
    def exists(self, plugin_id: str) -> bool:
        """Проверить, зарегистрирован ли плагин"""
        with self._lock:
            return plugin_id in self._registry
    
    def count(self) -> int:
        """Количество зарегистрированных плагинов"""
        with self._lock:
            return len(self._registry)
    
    def enable(self, plugin_id: str) -> bool:
        """Включить плагин"""
        with self._lock:
            if plugin_id in self._registry:
                self._registry[plugin_id].enabled = True
                return True
            return False
    
    def disable(self, plugin_id: str) -> bool:
        """Выключить плагин"""
        with self._lock:
            if plugin_id in self._registry:
                self._registry[plugin_id].enabled = False
                return True
            return False
    
    def is_enabled(self, plugin_id: str) -> bool:
        """Проверить, включён ли плагин"""
        with self._lock:
            info = self._registry.get(plugin_id)
            return info.enabled if info else False
    
    def clear(self) -> int:
        """
        Очистить реестр
        
        Returns:
            Количество удалённых плагинов
        """
        with self._lock:
            count = len(self._registry)
            self._registry.clear()
            return count


class PluginRegistry:
    """
    Главный реестр всех плагинов системы
    Синглтон для глобального доступа
    """
    
    _instance: Optional['PluginRegistry'] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'PluginRegistry':
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Типизированные реестры для каждого типа плагинов
        self.indicators: TypedRegistry = TypedRegistry(PluginType.INDICATOR)
        self.trading_systems: TypedRegistry = TypedRegistry(PluginType.TRADING_SYSTEM)
        self.filters: TypedRegistry = TypedRegistry(PluginType.FILTER)
        self.optimizers: TypedRegistry = TypedRegistry(PluginType.OPTIMIZER)
        self.backtests: TypedRegistry = TypedRegistry(PluginType.BACKTEST)
        
        # Бандлы плагинов (полные плагины с несколькими компонентами)
        self._bundles: Dict[str, PluginBundle] = {}
        self._bundles_lock = threading.RLock()
        
        # Маппинг типов на реестры
        self._type_map: Dict[PluginType, TypedRegistry] = {
            PluginType.INDICATOR: self.indicators,
            PluginType.TRADING_SYSTEM: self.trading_systems,
            PluginType.FILTER: self.filters,
            PluginType.OPTIMIZER: self.optimizers,
            PluginType.BACKTEST: self.backtests
        }
        
        self._initialized = True
    
    @classmethod
    def get_instance(cls) -> 'PluginRegistry':
        """Получить экземпляр реестра (альтернатива __new__)"""
        return cls()
    
    def get_registry(self, plugin_type: PluginType) -> TypedRegistry:
        """Получить типизированный реестр по типу плагина"""
        return self._type_map[plugin_type]
    
    # === Bundles ===
    
    def register_bundle(self, bundle: PluginBundle) -> None:
        """Зарегистрировать бандл плагина"""
        with self._bundles_lock:
            self._bundles[bundle.id] = bundle
    
    def get_bundle(self, bundle_id: str) -> Optional[PluginBundle]:
        """Получить бандл по ID"""
        with self._bundles_lock:
            return self._bundles.get(bundle_id)
    
    def list_bundles(self) -> List[PluginBundle]:
        """Список всех бандлов"""
        with self._bundles_lock:
            return list(self._bundles.values())
    
    def unregister_bundle(self, bundle_id: str) -> bool:
        """
        Удалить бандл и все его компоненты
        
        Returns:
            True если бандл был удалён
        """
        with self._bundles_lock:
            bundle = self._bundles.get(bundle_id)
            if not bundle:
                return False
            
            # Удаляем компоненты из типизированных реестров
            if bundle.indicator:
                self.indicators.unregister(bundle.indicator.id)
            if bundle.trading_system:
                self.trading_systems.unregister(bundle.trading_system.id)
            if bundle.optimizer:
                self.optimizers.unregister(bundle.optimizer.id)
            if bundle.backtest:
                self.backtests.unregister(bundle.backtest.id)
            for filter_id in bundle.filters:
                self.filters.unregister(filter_id)
            
            del self._bundles[bundle_id]
            return True
    
    # === Statistics ===
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика реестра"""
        return {
            "indicators": self.indicators.count(),
            "trading_systems": self.trading_systems.count(),
            "filters": self.filters.count(),
            "optimizers": self.optimizers.count(),
            "backtests": self.backtests.count(),
            "bundles": len(self._bundles),
            "total_components": (
                self.indicators.count() +
                self.trading_systems.count() +
                self.filters.count() +
                self.optimizers.count() +
                self.backtests.count()
            )
        }
    
    def list_all(self) -> Dict[str, List[PluginInfo]]:
        """Получить все плагины по типам"""
        return {
            "indicators": self.indicators.list_all(),
            "trading_systems": self.trading_systems.list_all(),
            "filters": self.filters.list_all(),
            "optimizers": self.optimizers.list_all(),
            "backtests": self.backtests.list_all()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация реестра в словарь"""
        all_plugins = self.list_all()
        return {
            "stats": self.get_stats(),
            "bundles": [b.to_dict() for b in self.list_bundles()],
            "indicators": [p.to_dict() for p in all_plugins["indicators"]],
            "trading_systems": [p.to_dict() for p in all_plugins["trading_systems"]],
            "filters": [p.to_dict() for p in all_plugins["filters"]],
            "optimizers": [p.to_dict() for p in all_plugins["optimizers"]],
            "backtests": [p.to_dict() for p in all_plugins["backtests"]]
        }
    
    def clear_all(self) -> Dict[str, int]:
        """
        Очистить все реестры
        
        Returns:
            Количество удалённых плагинов по типам
        """
        result = {
            "indicators": self.indicators.clear(),
            "trading_systems": self.trading_systems.clear(),
            "filters": self.filters.clear(),
            "optimizers": self.optimizers.clear(),
            "backtests": self.backtests.clear()
        }
        with self._bundles_lock:
            result["bundles"] = len(self._bundles)
            self._bundles.clear()
        return result


# === Глобальный экземпляр ===

registry = PluginRegistry.get_instance()


# === Декораторы для удобной регистрации ===

def register_indicator(
    plugin_id: str,
    name: str,
    version: str = "1.0.0",
    description: str = "",
    author: str = "Unknown",
    dependencies: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Декоратор для регистрации индикатора
    
    Пример:
        @register_indicator("trg", "TRG Indicator", version="1.0.0")
        class TRGIndicator(BaseIndicator):
            ...
    """
    def decorator(cls):
        registry.indicators.register(
            plugin_id=plugin_id,
            cls=cls,
            name=name,
            version=version,
            description=description,
            author=author,
            dependencies=dependencies,
            metadata=metadata
        )
        return cls
    return decorator


def register_trading_system(
    plugin_id: str,
    name: str,
    version: str = "1.0.0",
    description: str = "",
    author: str = "Unknown",
    dependencies: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Декоратор для регистрации торговой системы"""
    def decorator(cls):
        registry.trading_systems.register(
            plugin_id=plugin_id,
            cls=cls,
            name=name,
            version=version,
            description=description,
            author=author,
            dependencies=dependencies,
            metadata=metadata
        )
        return cls
    return decorator


def register_filter(
    plugin_id: str,
    name: str,
    version: str = "1.0.0",
    description: str = "",
    author: str = "Unknown",
    dependencies: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Декоратор для регистрации фильтра"""
    def decorator(cls):
        registry.filters.register(
            plugin_id=plugin_id,
            cls=cls,
            name=name,
            version=version,
            description=description,
            author=author,
            dependencies=dependencies,
            metadata=metadata
        )
        return cls
    return decorator


def register_optimizer(
    plugin_id: str,
    name: str,
    version: str = "1.0.0",
    description: str = "",
    author: str = "Unknown",
    dependencies: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Декоратор для регистрации оптимизатора"""
    def decorator(cls):
        registry.optimizers.register(
            plugin_id=plugin_id,
            cls=cls,
            name=name,
            version=version,
            description=description,
            author=author,
            dependencies=dependencies,
            metadata=metadata
        )
        return cls
    return decorator


def register_backtest(
    plugin_id: str,
    name: str,
    version: str = "1.0.0",
    description: str = "",
    author: str = "Unknown",
    dependencies: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Декоратор для регистрации бэктеста"""
    def decorator(cls):
        registry.backtests.register(
            plugin_id=plugin_id,
            cls=cls,
            name=name,
            version=version,
            description=description,
            author=author,
            dependencies=dependencies,
            metadata=metadata
        )
        return cls
    return decorator


# === Хелперы ===

def get_indicator(plugin_id: str):
    """Получить класс индикатора по ID"""
    return registry.indicators.get(plugin_id)


def get_trading_system(plugin_id: str):
    """Получить класс торговой системы по ID"""
    return registry.trading_systems.get(plugin_id)


def get_filter(plugin_id: str):
    """Получить класс фильтра по ID"""
    return registry.filters.get(plugin_id)


def get_optimizer(plugin_id: str):
    """Получить класс оптимизатора по ID"""
    return registry.optimizers.get(plugin_id)


def get_backtest(plugin_id: str):
    """Получить класс бэктеста по ID"""
    return registry.backtests.get(plugin_id)


def list_indicators() -> List[str]:
    """Список ID всех индикаторов"""
    return registry.indicators.list_ids()


def list_filters() -> List[str]:
    """Список ID всех фильтров"""
    return registry.filters.list_ids()
