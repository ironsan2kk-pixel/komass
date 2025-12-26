"""
Komas Trading System - Plugin Loader

Загрузчик плагинов с поддержкой:
- Динамический импорт модулей
- Парсинг manifest.json
- Автодискавери плагинов
- Валидация структуры

Автор: Komas Team
Версия: 1.0.0
"""

import os
import sys
import json
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Any, Type, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .registry import (
    PluginRegistry, 
    PluginBundle, 
    PluginInfo, 
    PluginType,
    registry
)

# Попытка импорта централизованного логгера
try:
    from ..core.logger import get_logger
    logger = get_logger("plugin_loader")
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("plugin_loader")


@dataclass
class ManifestEntryPoint:
    """Точка входа из manifest.json"""
    module_path: str  # Относительный путь: "indicator.core"
    class_name: str   # Имя класса: "TRGIndicator"
    
    @classmethod
    def from_string(cls, entry: str) -> 'ManifestEntryPoint':
        """
        Парсинг строки формата "module.path:ClassName"
        
        Пример: "indicator.core:TRGIndicator"
        """
        if ':' not in entry:
            raise ValueError(f"Invalid entry point format: {entry}. Expected 'module.path:ClassName'")
        
        parts = entry.rsplit(':', 1)
        return cls(module_path=parts[0], class_name=parts[1])
    
    def to_string(self) -> str:
        return f"{self.module_path}:{self.class_name}"


@dataclass
class PluginManifest:
    """
    Манифест плагина (manifest.json)
    
    Пример manifest.json:
    {
        "id": "trg",
        "name": "TRG Indicator",
        "version": "1.0.0",
        "description": "TRG Trading Indicator with advanced TP/SL",
        "author": "Komas Team",
        "entry_points": {
            "indicator": "indicator.core:TRGIndicator",
            "trading_system": "trading.system:TRGTradingSystem",
            "filters": [
                "filters.supertrend:SuperTrendFilter",
                "filters.rsi:RSIFilter",
                "filters.adx:ADXFilter",
                "filters.volume:VolumeFilter"
            ],
            "optimizer": "optimizer.main:TRGOptimizer",
            "backtest": "backtest.engine:TRGBacktest"
        },
        "dependencies": [],
        "settings": {
            "default_timeframe": "1h",
            "supported_exchanges": ["binance", "bybit", "okx"]
        }
    }
    """
    id: str
    name: str
    version: str
    description: str
    author: str
    
    # Точки входа
    indicator: Optional[ManifestEntryPoint] = None
    trading_system: Optional[ManifestEntryPoint] = None
    optimizer: Optional[ManifestEntryPoint] = None
    backtest: Optional[ManifestEntryPoint] = None
    filters: List[ManifestEntryPoint] = field(default_factory=list)
    
    # Дополнительно
    dependencies: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)
    
    # Путь к манифесту
    manifest_path: Optional[str] = None
    plugin_dir: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], manifest_path: Optional[str] = None) -> 'PluginManifest':
        """Создание манифеста из словаря"""
        entry_points = data.get("entry_points", {})
        
        # Парсим точки входа
        indicator = None
        if "indicator" in entry_points:
            indicator = ManifestEntryPoint.from_string(entry_points["indicator"])
        
        trading_system = None
        if "trading_system" in entry_points:
            trading_system = ManifestEntryPoint.from_string(entry_points["trading_system"])
        
        optimizer = None
        if "optimizer" in entry_points:
            optimizer = ManifestEntryPoint.from_string(entry_points["optimizer"])
        
        backtest = None
        if "backtest" in entry_points:
            backtest = ManifestEntryPoint.from_string(entry_points["backtest"])
        
        filters = []
        if "filters" in entry_points:
            for filter_entry in entry_points["filters"]:
                filters.append(ManifestEntryPoint.from_string(filter_entry))
        
        plugin_dir = None
        if manifest_path:
            plugin_dir = str(Path(manifest_path).parent)
        
        return cls(
            id=data["id"],
            name=data["name"],
            version=data.get("version", "1.0.0"),
            description=data.get("description", ""),
            author=data.get("author", "Unknown"),
            indicator=indicator,
            trading_system=trading_system,
            optimizer=optimizer,
            backtest=backtest,
            filters=filters,
            dependencies=data.get("dependencies", []),
            settings=data.get("settings", {}),
            manifest_path=manifest_path,
            plugin_dir=plugin_dir
        )
    
    @classmethod
    def from_file(cls, manifest_path: str) -> 'PluginManifest':
        """Загрузка манифеста из файла"""
        with open(manifest_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data, manifest_path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация в словарь"""
        entry_points = {}
        
        if self.indicator:
            entry_points["indicator"] = self.indicator.to_string()
        if self.trading_system:
            entry_points["trading_system"] = self.trading_system.to_string()
        if self.optimizer:
            entry_points["optimizer"] = self.optimizer.to_string()
        if self.backtest:
            entry_points["backtest"] = self.backtest.to_string()
        if self.filters:
            entry_points["filters"] = [f.to_string() for f in self.filters]
        
        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "entry_points": entry_points,
            "dependencies": self.dependencies,
            "settings": self.settings,
            "manifest_path": self.manifest_path,
            "plugin_dir": self.plugin_dir
        }
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Валидация манифеста
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        
        if not self.id:
            errors.append("Missing required field: id")
        if not self.name:
            errors.append("Missing required field: name")
        
        # Проверка что есть хотя бы одна точка входа
        has_entry = (
            self.indicator or 
            self.trading_system or 
            self.optimizer or 
            self.backtest or 
            self.filters
        )
        if not has_entry:
            errors.append("Plugin must have at least one entry point")
        
        return len(errors) == 0, errors


@dataclass
class LoadResult:
    """Результат загрузки плагина"""
    success: bool
    manifest: Optional[PluginManifest] = None
    bundle: Optional[PluginBundle] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    loaded_components: Dict[str, str] = field(default_factory=dict)  # type -> class_name
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "plugin_id": self.manifest.id if self.manifest else None,
            "plugin_name": self.manifest.name if self.manifest else None,
            "errors": self.errors,
            "warnings": self.warnings,
            "loaded_components": self.loaded_components
        }


class PluginLoader:
    """
    Загрузчик плагинов
    
    Функциональность:
    - Загрузка плагина из директории с manifest.json
    - Динамический импорт модулей
    - Автодискавери плагинов в папке plugins/
    - Валидация и логирование
    """
    
    def __init__(
        self, 
        plugins_dir: Optional[str] = None,
        registry_instance: Optional[PluginRegistry] = None
    ):
        """
        Args:
            plugins_dir: Путь к папке с плагинами (по умолчанию ./plugins)
            registry_instance: Экземпляр реестра (по умолчанию глобальный)
        """
        self._plugins_dir = plugins_dir or self._get_default_plugins_dir()
        self._registry = registry_instance or registry
        self._loaded_manifests: Dict[str, PluginManifest] = {}
        
        logger.info(f"PluginLoader initialized. Plugins dir: {self._plugins_dir}")
    
    @staticmethod
    def _get_default_plugins_dir() -> str:
        """Получить путь к plugins/ по умолчанию"""
        # Относительно текущего файла: indicators/../plugins
        current_dir = Path(__file__).parent
        plugins_dir = current_dir.parent / "plugins"
        return str(plugins_dir)
    
    def _add_to_path(self, plugin_dir: str) -> None:
        """Добавить директорию плагина в sys.path"""
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
    
    def _remove_from_path(self, plugin_dir: str) -> None:
        """Удалить директорию плагина из sys.path"""
        if plugin_dir in sys.path:
            sys.path.remove(plugin_dir)
    
    def _import_class(
        self, 
        entry_point: ManifestEntryPoint, 
        plugin_dir: str
    ) -> Tuple[Optional[Type], Optional[str]]:
        """
        Динамический импорт класса
        
        Args:
            entry_point: Точка входа (module.path:ClassName)
            plugin_dir: Директория плагина
            
        Returns:
            (class, error_message)
        """
        try:
            # Добавляем путь плагина
            self._add_to_path(plugin_dir)
            
            # Импортируем модуль
            module = importlib.import_module(entry_point.module_path)
            
            # Получаем класс
            if not hasattr(module, entry_point.class_name):
                return None, f"Class '{entry_point.class_name}' not found in module '{entry_point.module_path}'"
            
            cls = getattr(module, entry_point.class_name)
            return cls, None
            
        except ImportError as e:
            return None, f"Failed to import '{entry_point.module_path}': {e}"
        except Exception as e:
            return None, f"Error importing '{entry_point.to_string()}': {e}"
    
    def _load_component(
        self,
        entry_point: ManifestEntryPoint,
        plugin_dir: str,
        plugin_type: PluginType,
        manifest: PluginManifest,
        component_id: Optional[str] = None
    ) -> Tuple[Optional[PluginInfo], Optional[str]]:
        """
        Загрузить один компонент плагина
        
        Returns:
            (PluginInfo, error_message)
        """
        cls, error = self._import_class(entry_point, plugin_dir)
        if error:
            return None, error
        
        # ID компонента
        if component_id is None:
            component_id = f"{manifest.id}_{entry_point.class_name.lower()}"
        
        # Регистрируем в реестре
        reg = self._registry.get_registry(plugin_type)
        info = reg.register(
            plugin_id=component_id,
            cls=cls,
            name=f"{manifest.name} - {entry_point.class_name}",
            version=manifest.version,
            description=manifest.description,
            author=manifest.author,
            dependencies=manifest.dependencies,
            metadata={"manifest_id": manifest.id, "entry_point": entry_point.to_string()}
        )
        
        return info, None
    
    def load_from_manifest(self, manifest_path: str) -> LoadResult:
        """
        Загрузить плагин из manifest.json
        
        Args:
            manifest_path: Путь к manifest.json
            
        Returns:
            LoadResult с результатом загрузки
        """
        result = LoadResult(success=False)
        
        # Проверяем файл
        if not os.path.exists(manifest_path):
            result.errors.append(f"Manifest not found: {manifest_path}")
            return result
        
        # Парсим манифест
        try:
            manifest = PluginManifest.from_file(manifest_path)
            result.manifest = manifest
        except json.JSONDecodeError as e:
            result.errors.append(f"Invalid JSON in manifest: {e}")
            return result
        except KeyError as e:
            result.errors.append(f"Missing required field in manifest: {e}")
            return result
        except Exception as e:
            result.errors.append(f"Error parsing manifest: {e}")
            return result
        
        # Валидация
        is_valid, errors = manifest.validate()
        if not is_valid:
            result.errors.extend(errors)
            return result
        
        # Проверяем не загружен ли уже
        if manifest.id in self._loaded_manifests:
            result.errors.append(f"Plugin '{manifest.id}' is already loaded")
            return result
        
        logger.info(f"Loading plugin: {manifest.name} v{manifest.version}")
        
        plugin_dir = manifest.plugin_dir
        
        # Создаём бандл
        bundle = PluginBundle(
            id=manifest.id,
            name=manifest.name,
            version=manifest.version,
            description=manifest.description,
            author=manifest.author,
            manifest_path=manifest_path,
            metadata=manifest.settings
        )
        
        # Загружаем компоненты
        
        # Indicator
        if manifest.indicator:
            info, error = self._load_component(
                manifest.indicator, 
                plugin_dir, 
                PluginType.INDICATOR,
                manifest,
                manifest.id  # ID индикатора = ID плагина
            )
            if error:
                result.errors.append(f"Indicator: {error}")
            else:
                bundle.indicator = info
                result.loaded_components["indicator"] = info.id
                logger.info(f"  ✓ Indicator: {info.id}")
        
        # Trading System
        if manifest.trading_system:
            info, error = self._load_component(
                manifest.trading_system, 
                plugin_dir, 
                PluginType.TRADING_SYSTEM,
                manifest,
                f"{manifest.id}_trading"
            )
            if error:
                result.errors.append(f"TradingSystem: {error}")
            else:
                bundle.trading_system = info
                result.loaded_components["trading_system"] = info.id
                logger.info(f"  ✓ TradingSystem: {info.id}")
        
        # Optimizer
        if manifest.optimizer:
            info, error = self._load_component(
                manifest.optimizer, 
                plugin_dir, 
                PluginType.OPTIMIZER,
                manifest,
                f"{manifest.id}_optimizer"
            )
            if error:
                result.errors.append(f"Optimizer: {error}")
            else:
                bundle.optimizer = info
                result.loaded_components["optimizer"] = info.id
                logger.info(f"  ✓ Optimizer: {info.id}")
        
        # Backtest
        if manifest.backtest:
            info, error = self._load_component(
                manifest.backtest, 
                plugin_dir, 
                PluginType.BACKTEST,
                manifest,
                f"{manifest.id}_backtest"
            )
            if error:
                result.errors.append(f"Backtest: {error}")
            else:
                bundle.backtest = info
                result.loaded_components["backtest"] = info.id
                logger.info(f"  ✓ Backtest: {info.id}")
        
        # Filters
        for filter_entry in manifest.filters:
            filter_id = f"{manifest.id}_{filter_entry.class_name.lower()}"
            info, error = self._load_component(
                filter_entry, 
                plugin_dir, 
                PluginType.FILTER,
                manifest,
                filter_id
            )
            if error:
                result.warnings.append(f"Filter {filter_entry.class_name}: {error}")
            else:
                bundle.filters[filter_id] = info
                result.loaded_components[f"filter_{filter_entry.class_name}"] = info.id
                logger.info(f"  ✓ Filter: {info.id}")
        
        # Если были критические ошибки — откатываем
        if result.errors:
            self._rollback_load(bundle)
            return result
        
        # Регистрируем бандл
        self._registry.register_bundle(bundle)
        self._loaded_manifests[manifest.id] = manifest
        result.bundle = bundle
        result.success = True
        
        logger.info(f"Plugin '{manifest.name}' loaded successfully. Components: {bundle.component_count}")
        
        return result
    
    def _rollback_load(self, bundle: PluginBundle) -> None:
        """Откатить частично загруженный плагин"""
        logger.warning(f"Rolling back plugin: {bundle.id}")
        
        if bundle.indicator:
            self._registry.indicators.unregister(bundle.indicator.id)
        if bundle.trading_system:
            self._registry.trading_systems.unregister(bundle.trading_system.id)
        if bundle.optimizer:
            self._registry.optimizers.unregister(bundle.optimizer.id)
        if bundle.backtest:
            self._registry.backtests.unregister(bundle.backtest.id)
        for filter_id in bundle.filters:
            self._registry.filters.unregister(filter_id)
    
    def load_from_directory(self, plugin_dir: str) -> LoadResult:
        """
        Загрузить плагин из директории
        
        Args:
            plugin_dir: Путь к папке плагина
            
        Returns:
            LoadResult
        """
        manifest_path = os.path.join(plugin_dir, "manifest.json")
        return self.load_from_manifest(manifest_path)
    
    def discover_and_load(self, plugins_dir: Optional[str] = None) -> Dict[str, LoadResult]:
        """
        Найти и загрузить все плагины в директории
        
        Args:
            plugins_dir: Путь к папке с плагинами
            
        Returns:
            Словарь {plugin_id: LoadResult}
        """
        plugins_dir = plugins_dir or self._plugins_dir
        results: Dict[str, LoadResult] = {}
        
        if not os.path.exists(plugins_dir):
            logger.warning(f"Plugins directory not found: {plugins_dir}")
            return results
        
        logger.info(f"Discovering plugins in: {plugins_dir}")
        
        # Ищем папки с manifest.json
        for item in os.listdir(plugins_dir):
            item_path = os.path.join(plugins_dir, item)
            
            if not os.path.isdir(item_path):
                continue
            
            manifest_path = os.path.join(item_path, "manifest.json")
            
            if os.path.exists(manifest_path):
                logger.info(f"Found plugin: {item}")
                result = self.load_from_manifest(manifest_path)
                plugin_id = result.manifest.id if result.manifest else item
                results[plugin_id] = result
        
        # Статистика
        success_count = sum(1 for r in results.values() if r.success)
        logger.info(f"Discovery complete. Loaded: {success_count}/{len(results)} plugins")
        
        return results
    
    def unload(self, plugin_id: str) -> bool:
        """
        Выгрузить плагин
        
        Args:
            plugin_id: ID плагина
            
        Returns:
            True если успешно
        """
        if plugin_id not in self._loaded_manifests:
            logger.warning(f"Plugin not loaded: {plugin_id}")
            return False
        
        manifest = self._loaded_manifests[plugin_id]
        
        # Удаляем бандл (он сам удалит компоненты)
        success = self._registry.unregister_bundle(plugin_id)
        
        if success:
            del self._loaded_manifests[plugin_id]
            
            # Удаляем из sys.path
            if manifest.plugin_dir:
                self._remove_from_path(manifest.plugin_dir)
            
            logger.info(f"Plugin unloaded: {plugin_id}")
        
        return success
    
    def reload(self, plugin_id: str) -> LoadResult:
        """
        Перезагрузить плагин
        
        Args:
            plugin_id: ID плагина
            
        Returns:
            LoadResult
        """
        if plugin_id not in self._loaded_manifests:
            return LoadResult(
                success=False, 
                errors=[f"Plugin not loaded: {plugin_id}"]
            )
        
        manifest = self._loaded_manifests[plugin_id]
        manifest_path = manifest.manifest_path
        
        # Выгружаем
        self.unload(plugin_id)
        
        # Инвалидируем кэш импортов
        if manifest.plugin_dir:
            self._invalidate_import_cache(manifest.plugin_dir)
        
        # Загружаем заново
        return self.load_from_manifest(manifest_path)
    
    def _invalidate_import_cache(self, plugin_dir: str) -> None:
        """Очистить кэш импортов для плагина"""
        plugin_path = Path(plugin_dir)
        modules_to_remove = []
        
        for name, module in sys.modules.items():
            if hasattr(module, '__file__') and module.__file__:
                try:
                    module_path = Path(module.__file__)
                    if plugin_path in module_path.parents or module_path == plugin_path:
                        modules_to_remove.append(name)
                except Exception:
                    pass
        
        for name in modules_to_remove:
            del sys.modules[name]
        
        # Очищаем кэш importlib
        importlib.invalidate_caches()
    
    def list_loaded(self) -> List[Dict[str, Any]]:
        """Список загруженных плагинов"""
        return [m.to_dict() for m in self._loaded_manifests.values()]
    
    def get_manifest(self, plugin_id: str) -> Optional[PluginManifest]:
        """Получить манифест плагина"""
        return self._loaded_manifests.get(plugin_id)
    
    def is_loaded(self, plugin_id: str) -> bool:
        """Проверить, загружен ли плагин"""
        return plugin_id in self._loaded_manifests


# === Глобальный загрузчик ===

_loader: Optional[PluginLoader] = None


def get_loader(plugins_dir: Optional[str] = None) -> PluginLoader:
    """Получить глобальный экземпляр загрузчика"""
    global _loader
    if _loader is None:
        _loader = PluginLoader(plugins_dir)
    return _loader


def load_plugin(manifest_path: str) -> LoadResult:
    """Загрузить плагин (shortcut)"""
    return get_loader().load_from_manifest(manifest_path)


def discover_plugins(plugins_dir: Optional[str] = None) -> Dict[str, LoadResult]:
    """Автодискавери плагинов (shortcut)"""
    return get_loader().discover_and_load(plugins_dir)


def unload_plugin(plugin_id: str) -> bool:
    """Выгрузить плагин (shortcut)"""
    return get_loader().unload(plugin_id)


def reload_plugin(plugin_id: str) -> LoadResult:
    """Перезагрузить плагин (shortcut)"""
    return get_loader().reload(plugin_id)
