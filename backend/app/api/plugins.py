"""
Komas Trading System - Plugins API

REST API для управления плагинами индикаторов.

Endpoints:
- GET  /api/plugins/          - Список всех плагинов
- GET  /api/plugins/{id}      - Информация о плагине
- POST /api/plugins/load      - Загрузить плагин
- POST /api/plugins/unload    - Выгрузить плагин
- POST /api/plugins/reload    - Перезагрузить плагин
- POST /api/plugins/discover  - Автодискавери
- GET  /api/plugins/registry  - Статус реестра

Автор: Komas Team
Версия: 1.0.0
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
import os

# Попытка импорта из indicators
try:
    from ..indicators import (
        registry,
        get_loader,
        load_plugin,
        discover_plugins,
        unload_plugin,
        reload_plugin,
        PluginLoader
    )
except ImportError:
    # Fallback если запускается отдельно
    registry = None
    get_loader = None


router = APIRouter(prefix="/api/plugins", tags=["Plugins"])


# === Pydantic Models ===

class LoadPluginRequest(BaseModel):
    """Запрос на загрузку плагина"""
    manifest_path: str = Field(..., description="Путь к manifest.json")


class UnloadPluginRequest(BaseModel):
    """Запрос на выгрузку плагина"""
    plugin_id: str = Field(..., description="ID плагина")


class ReloadPluginRequest(BaseModel):
    """Запрос на перезагрузку плагина"""
    plugin_id: str = Field(..., description="ID плагина")


class DiscoverPluginsRequest(BaseModel):
    """Запрос на автодискавери"""
    plugins_dir: Optional[str] = Field(None, description="Путь к папке плагинов")


class PluginInfoResponse(BaseModel):
    """Информация о плагине"""
    id: str
    name: str
    version: str
    description: str
    author: str
    manifest_path: Optional[str] = None
    plugin_dir: Optional[str] = None
    component_count: int = 0
    components: Dict[str, Any] = {}


class LoadResultResponse(BaseModel):
    """Результат загрузки"""
    success: bool
    plugin_id: Optional[str] = None
    plugin_name: Optional[str] = None
    errors: List[str] = []
    warnings: List[str] = []
    loaded_components: Dict[str, str] = {}


class RegistryStatsResponse(BaseModel):
    """Статистика реестра"""
    indicators: int = 0
    trading_systems: int = 0
    filters: int = 0
    optimizers: int = 0
    backtests: int = 0
    bundles: int = 0
    total_components: int = 0


# === Endpoints ===

@router.get("/", response_model=List[PluginInfoResponse])
async def list_plugins():
    """
    Список всех загруженных плагинов
    """
    if registry is None:
        raise HTTPException(status_code=500, detail="Registry not initialized")
    
    loader = get_loader()
    manifests = loader.list_loaded()
    
    result = []
    for m in manifests:
        bundle = registry.get_bundle(m["id"])
        result.append(PluginInfoResponse(
            id=m["id"],
            name=m["name"],
            version=m["version"],
            description=m["description"],
            author=m["author"],
            manifest_path=m.get("manifest_path"),
            plugin_dir=m.get("plugin_dir"),
            component_count=bundle.component_count if bundle else 0,
            components=bundle.to_dict().get("components", {}) if bundle else {}
        ))
    
    return result


@router.get("/registry", response_model=RegistryStatsResponse)
async def get_registry_stats():
    """
    Статистика реестра плагинов
    """
    if registry is None:
        raise HTTPException(status_code=500, detail="Registry not initialized")
    
    stats = registry.get_stats()
    return RegistryStatsResponse(**stats)


@router.get("/registry/full")
async def get_full_registry():
    """
    Полный дамп реестра (для отладки)
    """
    if registry is None:
        raise HTTPException(status_code=500, detail="Registry not initialized")
    
    return registry.to_dict()


@router.get("/{plugin_id}", response_model=PluginInfoResponse)
async def get_plugin_info(plugin_id: str):
    """
    Информация о конкретном плагине
    """
    if registry is None:
        raise HTTPException(status_code=500, detail="Registry not initialized")
    
    loader = get_loader()
    manifest = loader.get_manifest(plugin_id)
    
    if not manifest:
        raise HTTPException(status_code=404, detail=f"Plugin not found: {plugin_id}")
    
    bundle = registry.get_bundle(plugin_id)
    m = manifest.to_dict()
    
    return PluginInfoResponse(
        id=m["id"],
        name=m["name"],
        version=m["version"],
        description=m["description"],
        author=m["author"],
        manifest_path=m.get("manifest_path"),
        plugin_dir=m.get("plugin_dir"),
        component_count=bundle.component_count if bundle else 0,
        components=bundle.to_dict().get("components", {}) if bundle else {}
    )


@router.post("/load", response_model=LoadResultResponse)
async def load_plugin_endpoint(request: LoadPluginRequest):
    """
    Загрузить плагин из manifest.json
    """
    if not os.path.exists(request.manifest_path):
        raise HTTPException(
            status_code=400, 
            detail=f"Manifest not found: {request.manifest_path}"
        )
    
    result = load_plugin(request.manifest_path)
    
    return LoadResultResponse(
        success=result.success,
        plugin_id=result.manifest.id if result.manifest else None,
        plugin_name=result.manifest.name if result.manifest else None,
        errors=result.errors,
        warnings=result.warnings,
        loaded_components=result.loaded_components
    )


@router.post("/unload")
async def unload_plugin_endpoint(request: UnloadPluginRequest):
    """
    Выгрузить плагин
    """
    success = unload_plugin(request.plugin_id)
    
    if not success:
        raise HTTPException(
            status_code=404, 
            detail=f"Plugin not loaded: {request.plugin_id}"
        )
    
    return {
        "success": True,
        "message": f"Plugin '{request.plugin_id}' unloaded"
    }


@router.post("/reload", response_model=LoadResultResponse)
async def reload_plugin_endpoint(request: ReloadPluginRequest):
    """
    Перезагрузить плагин (hot reload)
    """
    result = reload_plugin(request.plugin_id)
    
    return LoadResultResponse(
        success=result.success,
        plugin_id=result.manifest.id if result.manifest else None,
        plugin_name=result.manifest.name if result.manifest else None,
        errors=result.errors,
        warnings=result.warnings,
        loaded_components=result.loaded_components
    )


@router.post("/discover")
async def discover_plugins_endpoint(request: DiscoverPluginsRequest):
    """
    Автоматически найти и загрузить все плагины
    """
    results = discover_plugins(request.plugins_dir)
    
    response = {
        "total": len(results),
        "success": sum(1 for r in results.values() if r.success),
        "failed": sum(1 for r in results.values() if not r.success),
        "plugins": {}
    }
    
    for plugin_id, result in results.items():
        response["plugins"][plugin_id] = LoadResultResponse(
            success=result.success,
            plugin_id=result.manifest.id if result.manifest else None,
            plugin_name=result.manifest.name if result.manifest else None,
            errors=result.errors,
            warnings=result.warnings,
            loaded_components=result.loaded_components
        ).dict()
    
    return response


# === Components Endpoints ===

@router.get("/indicators/list")
async def list_registered_indicators():
    """
    Список зарегистрированных индикаторов
    """
    if registry is None:
        raise HTTPException(status_code=500, detail="Registry not initialized")
    
    indicators = registry.indicators.list_all()
    return {
        "count": len(indicators),
        "indicators": [i.to_dict() for i in indicators]
    }


@router.get("/filters/list")
async def list_registered_filters():
    """
    Список зарегистрированных фильтров
    """
    if registry is None:
        raise HTTPException(status_code=500, detail="Registry not initialized")
    
    filters = registry.filters.list_all()
    return {
        "count": len(filters),
        "filters": [f.to_dict() for f in filters]
    }


@router.get("/trading-systems/list")
async def list_registered_trading_systems():
    """
    Список зарегистрированных торговых систем
    """
    if registry is None:
        raise HTTPException(status_code=500, detail="Registry not initialized")
    
    systems = registry.trading_systems.list_all()
    return {
        "count": len(systems),
        "trading_systems": [s.to_dict() for s in systems]
    }


@router.get("/optimizers/list")
async def list_registered_optimizers():
    """
    Список зарегистрированных оптимизаторов
    """
    if registry is None:
        raise HTTPException(status_code=500, detail="Registry not initialized")
    
    optimizers = registry.optimizers.list_all()
    return {
        "count": len(optimizers),
        "optimizers": [o.to_dict() for o in optimizers]
    }


@router.get("/backtests/list")
async def list_registered_backtests():
    """
    Список зарегистрированных бэктестов
    """
    if registry is None:
        raise HTTPException(status_code=500, detail="Registry not initialized")
    
    backtests = registry.backtests.list_all()
    return {
        "count": len(backtests),
        "backtests": [b.to_dict() for b in backtests]
    }


# === Enable/Disable ===

@router.post("/indicators/{indicator_id}/enable")
async def enable_indicator(indicator_id: str):
    """Включить индикатор"""
    if registry is None:
        raise HTTPException(status_code=500, detail="Registry not initialized")
    
    success = registry.indicators.enable(indicator_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Indicator not found: {indicator_id}")
    
    return {"success": True, "indicator_id": indicator_id, "enabled": True}


@router.post("/indicators/{indicator_id}/disable")
async def disable_indicator(indicator_id: str):
    """Выключить индикатор"""
    if registry is None:
        raise HTTPException(status_code=500, detail="Registry not initialized")
    
    success = registry.indicators.disable(indicator_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Indicator not found: {indicator_id}")
    
    return {"success": True, "indicator_id": indicator_id, "enabled": False}
