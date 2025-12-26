"""
Komas Trading Server - Database API Routes
==========================================
API endpoints for presets, settings, and data cache
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.core.database import (
    SettingsManager, PresetManager, DataCacheManager, DB_PATH
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/db", tags=["Database"])


# ============ REQUEST/RESPONSE MODELS ============

class SettingValue(BaseModel):
    key: str
    value: Any
    description: Optional[str] = None


class PresetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    indicator_type: str = "trg"
    settings: Dict[str, Any]
    tags: Optional[List[str]] = None


class PresetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    is_favorite: Optional[bool] = None
    tags: Optional[List[str]] = None


class PresetPerformance(BaseModel):
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    total_profit_percent: Optional[float] = None
    max_drawdown_percent: Optional[float] = None
    sharpe_ratio: Optional[float] = None


class PresetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    indicator_type: str
    settings: Dict[str, Any]
    is_default: bool
    is_favorite: bool
    tags: Optional[List[str]]
    win_rate: Optional[float]
    profit_factor: Optional[float]
    total_profit_percent: Optional[float]
    max_drawdown_percent: Optional[float]
    sharpe_ratio: Optional[float]
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class DataCacheResponse(BaseModel):
    id: int
    symbol: str
    timeframe: str
    source: str
    filename: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    candles_count: Optional[int]
    is_complete: bool
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============ DATABASE INFO ============

@router.get("/info")
async def get_db_info():
    """Get database information"""
    import os
    
    db_size = 0
    if DB_PATH.exists():
        db_size = os.path.getsize(DB_PATH)
    
    # Count records
    presets = await PresetManager.list_all()
    caches = await DataCacheManager.list_all()
    settings = await SettingsManager.get_all()
    
    return {
        "path": str(DB_PATH),
        "exists": DB_PATH.exists(),
        "size_bytes": db_size,
        "size_mb": round(db_size / (1024 * 1024), 2),
        "counts": {
            "presets": len(presets),
            "data_cache": len(caches),
            "settings": len(settings)
        }
    }


# ============ SETTINGS ENDPOINTS ============

@router.get("/settings")
async def list_settings():
    """Get all settings"""
    settings = await SettingsManager.get_all()
    return {"settings": settings}


@router.get("/settings/{key}")
async def get_setting(key: str):
    """Get specific setting"""
    value = await SettingsManager.get(key)
    if value is None:
        raise HTTPException(404, f"Setting '{key}' not found")
    return {"key": key, "value": value}


@router.post("/settings")
async def set_setting(data: SettingValue):
    """Set a setting value"""
    await SettingsManager.set(data.key, data.value, data.description)
    return {"status": "ok", "key": data.key, "value": data.value}


@router.delete("/settings/{key}")
async def delete_setting(key: str):
    """Delete a setting"""
    deleted = await SettingsManager.delete(key)
    if not deleted:
        raise HTTPException(404, f"Setting '{key}' not found")
    return {"status": "deleted", "key": key}


# ============ PRESETS ENDPOINTS ============

@router.get("/presets", response_model=List[PresetResponse])
async def list_presets(
    indicator_type: Optional[str] = None,
    favorites_only: bool = False,
    limit: int = Query(100, ge=1, le=500)
):
    """List all presets"""
    presets = await PresetManager.list_all(
        indicator_type=indicator_type,
        favorites_only=favorites_only,
        limit=limit
    )
    
    # Convert to response format
    result = []
    for p in presets:
        result.append({
            "id": p.id,
            "name": p.name,
            "description": p.description,
            "indicator_type": p.indicator_type,
            "settings": p.settings,
            "is_default": p.is_default,
            "is_favorite": p.is_favorite,
            "tags": p.get_tags_list(),
            "win_rate": p.win_rate,
            "profit_factor": p.profit_factor,
            "total_profit_percent": p.total_profit_percent,
            "max_drawdown_percent": p.max_drawdown_percent,
            "sharpe_ratio": p.sharpe_ratio,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "last_used_at": p.last_used_at
        })
    
    return result


@router.get("/presets/{preset_id}", response_model=PresetResponse)
async def get_preset(preset_id: int):
    """Get preset by ID"""
    preset = await PresetManager.get(preset_id)
    if not preset:
        raise HTTPException(404, f"Preset {preset_id} not found")
    
    return {
        "id": preset.id,
        "name": preset.name,
        "description": preset.description,
        "indicator_type": preset.indicator_type,
        "settings": preset.settings,
        "is_default": preset.is_default,
        "is_favorite": preset.is_favorite,
        "tags": preset.get_tags_list(),
        "win_rate": preset.win_rate,
        "profit_factor": preset.profit_factor,
        "total_profit_percent": preset.total_profit_percent,
        "max_drawdown_percent": preset.max_drawdown_percent,
        "sharpe_ratio": preset.sharpe_ratio,
        "created_at": preset.created_at,
        "updated_at": preset.updated_at,
        "last_used_at": preset.last_used_at
    }


@router.post("/presets", response_model=PresetResponse)
async def create_preset(data: PresetCreate):
    """Create new preset"""
    try:
        preset = await PresetManager.create(
            name=data.name,
            description=data.description,
            indicator_type=data.indicator_type,
            settings=data.settings,
            tags=data.tags
        )
        
        return {
            "id": preset.id,
            "name": preset.name,
            "description": preset.description,
            "indicator_type": preset.indicator_type,
            "settings": preset.settings,
            "is_default": preset.is_default,
            "is_favorite": preset.is_favorite,
            "tags": data.tags or [],
            "win_rate": None,
            "profit_factor": None,
            "total_profit_percent": None,
            "max_drawdown_percent": None,
            "sharpe_ratio": None,
            "created_at": preset.created_at,
            "updated_at": preset.updated_at,
            "last_used_at": None
        }
    except Exception as e:
        logger.error(f"Failed to create preset: {e}")
        raise HTTPException(500, f"Failed to create preset: {str(e)}")


@router.put("/presets/{preset_id}", response_model=PresetResponse)
async def update_preset(preset_id: int, data: PresetUpdate):
    """Update preset"""
    update_data = {}
    
    if data.name is not None:
        update_data["name"] = data.name
    if data.description is not None:
        update_data["description"] = data.description
    if data.settings is not None:
        update_data["settings"] = data.settings
    if data.is_favorite is not None:
        update_data["is_favorite"] = data.is_favorite
    if data.tags is not None:
        update_data["tags"] = ",".join(data.tags)
    
    preset = await PresetManager.update(preset_id, **update_data)
    if not preset:
        raise HTTPException(404, f"Preset {preset_id} not found")
    
    return await get_preset(preset_id)


@router.put("/presets/{preset_id}/performance")
async def update_preset_performance(preset_id: int, data: PresetPerformance):
    """Update preset performance metrics"""
    preset = await PresetManager.update_performance(
        preset_id,
        win_rate=data.win_rate,
        profit_factor=data.profit_factor,
        total_profit_percent=data.total_profit_percent,
        max_drawdown_percent=data.max_drawdown_percent,
        sharpe_ratio=data.sharpe_ratio
    )
    
    if not preset:
        raise HTTPException(404, f"Preset {preset_id} not found")
    
    return {"status": "ok", "preset_id": preset_id}


@router.post("/presets/{preset_id}/favorite")
async def toggle_preset_favorite(preset_id: int):
    """Toggle preset favorite status"""
    preset = await PresetManager.get(preset_id)
    if not preset:
        raise HTTPException(404, f"Preset {preset_id} not found")
    
    await PresetManager.update(preset_id, is_favorite=not preset.is_favorite)
    return {"status": "ok", "preset_id": preset_id, "is_favorite": not preset.is_favorite}


@router.delete("/presets/{preset_id}")
async def delete_preset(preset_id: int):
    """Delete preset"""
    deleted = await PresetManager.delete(preset_id)
    if not deleted:
        raise HTTPException(404, f"Preset {preset_id} not found")
    return {"status": "deleted", "preset_id": preset_id}


# ============ DATA CACHE ENDPOINTS ============

@router.get("/cache", response_model=List[DataCacheResponse])
async def list_data_cache(source: Optional[str] = None):
    """List all cached data"""
    caches = await DataCacheManager.list_all(source=source)
    
    result = []
    for c in caches:
        result.append({
            "id": c.id,
            "symbol": c.symbol,
            "timeframe": c.timeframe,
            "source": c.source,
            "filename": c.filename,
            "start_date": c.start_date,
            "end_date": c.end_date,
            "candles_count": c.candles_count,
            "is_complete": c.is_complete,
            "updated_at": c.updated_at
        })
    
    return result


@router.get("/cache/{symbol}/{timeframe}")
async def get_cache_info(symbol: str, timeframe: str, source: str = "binance"):
    """Get cache info for specific symbol/timeframe"""
    cache = await DataCacheManager.get(symbol, timeframe, source)
    if not cache:
        raise HTTPException(404, f"Cache not found for {symbol} {timeframe}")
    
    return {
        "id": cache.id,
        "symbol": cache.symbol,
        "timeframe": cache.timeframe,
        "source": cache.source,
        "filename": cache.filename,
        "filepath": cache.filepath,
        "start_date": cache.start_date,
        "end_date": cache.end_date,
        "candles_count": cache.candles_count,
        "is_complete": cache.is_complete,
        "updated_at": cache.updated_at,
        "last_accessed_at": cache.last_accessed_at
    }


@router.delete("/cache/{symbol}/{timeframe}")
async def delete_cache_info(symbol: str, timeframe: str, source: str = "binance"):
    """Delete cache info"""
    deleted = await DataCacheManager.delete(symbol, timeframe, source)
    if not deleted:
        raise HTTPException(404, f"Cache not found for {symbol} {timeframe}")
    return {"status": "deleted", "symbol": symbol, "timeframe": timeframe}
