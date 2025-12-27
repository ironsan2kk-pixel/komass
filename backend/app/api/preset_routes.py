"""
Komas Trading Server - Preset API Routes
========================================
REST API for managing indicator presets.

Endpoints:
- GET    /api/presets/list              - List all presets
- GET    /api/presets/stats             - Get preset statistics
- GET    /api/presets/{id}              - Get single preset
- POST   /api/presets/create            - Create new preset
- PUT    /api/presets/{id}              - Update preset
- DELETE /api/presets/{id}              - Delete preset
- POST   /api/presets/import            - Import preset from JSON
- GET    /api/presets/export/{id}       - Export preset to JSON

Dominant-specific:
- GET    /api/presets/dominant/list     - List Dominant presets only
- POST   /api/presets/dominant/create   - Create Dominant preset (simplified)
- POST   /api/presets/dominant/seed     - Seed system presets (125+ from GG)
"""
import json
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse

from app.database.presets_db import (
    ensure_presets_table,
    create_preset,
    get_preset,
    get_preset_by_name,
    list_presets,
    count_presets,
    update_preset,
    delete_preset,
    delete_presets_by_source,
    bulk_create_presets,
    get_preset_stats
)
from app.models.preset_models import (
    PresetCreate,
    PresetUpdate,
    PresetResponse,
    PresetListResponse,
    PresetStatsResponse,
    DominantPresetCreate,
    DominantPresetResponse
)

router = APIRouter(prefix="/api/presets", tags=["presets"])
logger = logging.getLogger(__name__)


# ============ GENERAL ENDPOINTS ============

@router.get("/list", response_model=PresetListResponse)
async def list_all_presets(
    indicator_type: Optional[str] = Query(None, description="Filter by indicator: trg, dominant"),
    category: Optional[str] = Query(None, description="Filter by category"),
    source: Optional[str] = Query(None, description="Filter by source"),
    symbol: Optional[str] = Query(None, description="Filter by symbol"),
    timeframe: Optional[str] = Query(None, description="Filter by timeframe"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_favorite: Optional[bool] = Query(None, description="Filter by favorite"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List all presets with optional filters"""
    try:
        presets = list_presets(
            indicator_type=indicator_type,
            category=category,
            source=source,
            symbol=symbol,
            timeframe=timeframe,
            is_active=is_active,
            is_favorite=is_favorite,
            search=search,
            limit=limit,
            offset=offset
        )
        
        total = count_presets(
            indicator_type=indicator_type,
            category=category,
            source=source,
            is_active=is_active
        )
        
        return PresetListResponse(
            total=total,
            presets=[_dict_to_response(p) for p in presets]
        )
    except Exception as e:
        logger.error(f"Error listing presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=PresetStatsResponse)
async def get_stats():
    """Get preset statistics"""
    try:
        stats = get_preset_stats()
        return PresetStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting preset stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{preset_id}", response_model=PresetResponse)
async def get_single_preset(preset_id: str):
    """Get single preset by ID"""
    preset = get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
    return _dict_to_response(preset)


@router.post("/create", response_model=PresetResponse)
async def create_new_preset(data: PresetCreate):
    """Create a new preset"""
    try:
        preset = create_preset(
            name=data.name,
            indicator_type=data.indicator_type,
            params=data.params,
            category=data.category,
            description=data.description,
            symbol=data.symbol,
            timeframe=data.timeframe,
            source=data.source,
            tags=data.tags
        )
        return _dict_to_response(preset)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{preset_id}", response_model=PresetResponse)
async def update_existing_preset(preset_id: str, data: PresetUpdate):
    """Update an existing preset"""
    try:
        # Convert to dict, exclude None values
        update_data = data.model_dump(exclude_none=True)
        
        preset = update_preset(preset_id, **update_data)
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
        
        return _dict_to_response(preset)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{preset_id}")
async def delete_existing_preset(preset_id: str):
    """Delete a preset"""
    deleted = delete_preset(preset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
    return {"success": True, "deleted": preset_id}


@router.post("/import")
async def import_preset(preset_json: dict = Body(...)):
    """Import preset from JSON"""
    try:
        # Validate required fields
        required = ["name", "indicator_type", "params"]
        for field in required:
            if field not in preset_json:
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        preset = create_preset(
            name=preset_json.get("name"),
            indicator_type=preset_json.get("indicator_type"),
            params=preset_json.get("params"),
            category=preset_json.get("category", "mid-term"),
            description=preset_json.get("description"),
            symbol=preset_json.get("symbol"),
            timeframe=preset_json.get("timeframe"),
            source="imported",
            tags=preset_json.get("tags")
        )
        
        return {"success": True, "preset": _dict_to_response(preset)}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{preset_id}")
async def export_preset(preset_id: str):
    """Export preset to JSON"""
    preset = get_preset(preset_id)
    if not preset:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
    
    # Remove internal fields
    export_data = {
        "name": preset["name"],
        "description": preset.get("description"),
        "indicator_type": preset["indicator_type"],
        "category": preset.get("category"),
        "symbol": preset.get("symbol"),
        "timeframe": preset.get("timeframe"),
        "params": preset["params"],
        "tags": preset.get("tags", [])
    }
    
    return JSONResponse(
        content=export_data,
        headers={
            "Content-Disposition": f'attachment; filename="{preset_id}.json"'
        }
    )


# ============ DOMINANT-SPECIFIC ENDPOINTS ============

@router.get("/dominant/list")
async def list_dominant_presets(
    category: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    symbol: Optional[str] = Query(None),
    timeframe: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List Dominant presets only"""
    try:
        presets = list_presets(
            indicator_type="dominant",
            category=category,
            source=source,
            symbol=symbol,
            timeframe=timeframe,
            search=search,
            limit=limit,
            offset=offset
        )
        
        total = count_presets(indicator_type="dominant", category=category, source=source)
        
        # Convert to DominantPresetResponse
        dominant_presets = []
        for p in presets:
            resp = _dict_to_response(p)
            dom_resp = DominantPresetResponse.from_preset_response(resp)
            dominant_presets.append(dom_resp.model_dump())
        
        return {
            "total": total,
            "presets": dominant_presets
        }
    except Exception as e:
        logger.error(f"Error listing Dominant presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dominant/categories")
async def get_dominant_categories():
    """Get available categories with counts"""
    try:
        stats = get_preset_stats()
        return {
            "categories": stats.get("by_category", {}),
            "total": stats.get("total_presets", 0)
        }
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dominant/create")
async def create_dominant_preset(data: DominantPresetCreate):
    """Create Dominant preset with simplified schema"""
    try:
        generic = data.to_preset_create()
        
        preset = create_preset(
            name=generic.name,
            indicator_type=generic.indicator_type,
            params=generic.params,
            category=generic.category,
            description=generic.description,
            symbol=generic.symbol,
            timeframe=generic.timeframe,
            source=generic.source,
            tags=generic.tags
        )
        
        resp = _dict_to_response(preset)
        return DominantPresetResponse.from_preset_response(resp).model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating Dominant preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dominant/seed")
async def seed_dominant_presets(
    force: bool = Query(False, description="Delete existing pine_script presets and re-seed")
):
    """Seed Dominant presets from GG Pine Script (125+ presets)"""
    try:
        from app.migrations.seed_dominant_presets import seed_all_dominant_presets
        
        if force:
            # Delete existing pine_script presets
            deleted = delete_presets_by_source("pine_script")
            logger.info(f"Deleted {deleted} existing pine_script presets")
        
        result = seed_all_dominant_presets()
        
        return {
            "success": True,
            "created": result.get("created", 0),
            "skipped": result.get("skipped", 0),
            "errors": result.get("errors", 0),
            "total_dominant": count_presets(indicator_type="dominant")
        }
    except Exception as e:
        logger.error(f"Error seeding presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/dominant/clear")
async def clear_dominant_presets(
    source: str = Query("pine_script", description="Source to clear")
):
    """Clear Dominant presets by source (for re-migration)"""
    try:
        deleted = delete_presets_by_source(source)
        return {
            "success": True,
            "deleted": deleted,
            "remaining": count_presets(indicator_type="dominant")
        }
    except Exception as e:
        logger.error(f"Error clearing presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ HELPERS ============

def _dict_to_response(d: dict) -> PresetResponse:
    """Convert dict to PresetResponse"""
    return PresetResponse(
        id=d["id"],
        name=d["name"],
        description=d.get("description"),
        indicator_type=d.get("indicator_type", "dominant"),
        category=d.get("category", "mid-term"),
        symbol=d.get("symbol"),
        timeframe=d.get("timeframe"),
        params=d.get("params", {}),
        source=d.get("source", "manual"),
        is_active=d.get("is_active", True),
        is_favorite=d.get("is_favorite", False),
        tags=d.get("tags", []),
        win_rate=d.get("win_rate"),
        profit_factor=d.get("profit_factor"),
        total_profit_percent=d.get("total_profit_percent"),
        max_drawdown_percent=d.get("max_drawdown_percent"),
        sharpe_ratio=d.get("sharpe_ratio"),
        created_at=datetime.fromisoformat(d.get("created_at", datetime.utcnow().isoformat())),
        updated_at=datetime.fromisoformat(d.get("updated_at", datetime.utcnow().isoformat()))
    )


# ============ EXPORT ============

__all__ = ["router"]
