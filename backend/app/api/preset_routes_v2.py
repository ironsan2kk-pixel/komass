"""
Komas Trading Server - Preset API Routes (v2)
=============================================
REST API for managing indicator presets using new architecture.

Endpoints:
- GET    /api/presets/list              - List all presets
- GET    /api/presets/stats             - Get preset statistics
- GET    /api/presets/{id}              - Get single preset
- POST   /api/presets/create            - Create new preset
- PUT    /api/presets/{id}              - Update preset
- DELETE /api/presets/{id}              - Delete preset
- POST   /api/presets/import            - Import preset from JSON
- GET    /api/presets/export/{id}       - Export preset to JSON
- POST   /api/presets/validate          - Validate preset params
- GET    /api/presets/schema/{type}     - Get parameter schema

Generation:
- POST   /api/presets/generate/trg      - Generate 200 TRG presets
- POST   /api/presets/generate/dominant - Generate Dominant presets
- POST   /api/presets/generate/all      - Generate all system presets

Chat: #29 — Presets Architecture
"""

import json
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

# Import preset module
from app.presets import (
    get_registry,
    TRGPreset,
    DominantPreset,
    validate_params,
    validate_import,
    generate_trg_presets,
    generate_dominant_presets,
    generate_all_system_presets,
    IndicatorType,
    PresetCategory,
    PresetSource,
)

router = APIRouter(prefix="/api/presets", tags=["presets"])
logger = logging.getLogger(__name__)


# ==================== REQUEST/RESPONSE MODELS ====================

class PresetCreateRequest(BaseModel):
    """Request for creating a preset"""
    name: str = Field(..., min_length=1, max_length=100)
    indicator_type: str = Field(default="trg")
    params: dict = Field(...)
    category: Optional[str] = Field(default=None)
    description: Optional[str] = Field(None, max_length=500)
    symbol: Optional[str] = Field(None, max_length=20)
    timeframe: Optional[str] = Field(None, max_length=10)
    source: Optional[str] = Field(default="manual")
    tags: Optional[List[str]] = Field(default=None)


class PresetUpdateRequest(BaseModel):
    """Request for updating a preset"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = None
    symbol: Optional[str] = Field(None, max_length=20)
    timeframe: Optional[str] = Field(None, max_length=10)
    params: Optional[dict] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_favorite: Optional[bool] = None


class ValidateRequest(BaseModel):
    """Request for validating parameters"""
    indicator_type: str = Field(default="trg")
    params: dict = Field(...)


class GenerateRequest(BaseModel):
    """Request for generating presets"""
    replace_existing: bool = Field(default=False)


# ==================== ENDPOINTS ====================

@router.get("/list")
async def list_presets(
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
        registry = get_registry()
        
        presets = registry.list(
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
        
        total = registry.count(
            indicator_type=indicator_type,
            category=category,
            source=source,
            is_active=is_active,
        )
        
        return {
            "total": total,
            "presets": [p.to_dict() for p in presets]
        }
    except Exception as e:
        logger.error(f"Error listing presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """Get preset statistics"""
    try:
        registry = get_registry()
        stats = registry.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting preset stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/{indicator_type}")
async def get_param_schema(indicator_type: str):
    """Get parameter schema for indicator type"""
    try:
        registry = get_registry()
        preset_class = registry.get_preset_class(indicator_type)
        
        if not preset_class:
            raise HTTPException(status_code=404, detail=f"Unknown indicator type: {indicator_type}")
        
        # Create temp instance to get schema
        from app.presets import PresetConfig
        temp_config = PresetConfig(
            id="temp",
            name="temp",
            indicator_type=indicator_type,
            params={}
        )
        temp_preset = preset_class(temp_config)
        
        return {
            "indicator_type": indicator_type,
            "schema": temp_preset.get_param_schema(),
            "defaults": temp_preset.get_default_params(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{preset_id}")
async def get_preset(preset_id: str):
    """Get single preset by ID"""
    try:
        registry = get_registry()
        preset = registry.get(preset_id)
        
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
        
        return preset.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_preset(data: PresetCreateRequest):
    """Create a new preset"""
    try:
        registry = get_registry()
        
        preset = registry.create(
            indicator_type=data.indicator_type,
            params=data.params,
            name=data.name,
            category=data.category,
            source=data.source or "manual",
            description=data.description,
            symbol=data.symbol,
            timeframe=data.timeframe,
            tags=data.tags,
        )
        
        return {"success": True, "preset": preset.to_dict()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{preset_id}")
async def update_preset(preset_id: str, data: PresetUpdateRequest):
    """Update an existing preset"""
    try:
        registry = get_registry()
        
        # Build update dict
        updates = data.model_dump(exclude_none=True)
        
        preset = registry.update(preset_id, **updates)
        
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
        
        return {"success": True, "preset": preset.to_dict()}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{preset_id}")
async def delete_preset(preset_id: str):
    """Delete a preset"""
    try:
        registry = get_registry()
        deleted = registry.delete(preset_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
        
        return {"success": True, "deleted": preset_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_preset_params(data: ValidateRequest):
    """Validate preset parameters"""
    try:
        result = validate_params(data.indicator_type, data.params)
        return result.to_dict()
    except Exception as e:
        logger.error(f"Error validating params: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_preset(preset_json: dict = Body(...)):
    """Import preset from JSON"""
    try:
        # Validate first
        validation = validate_import(preset_json)
        if not validation.is_valid:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "validation": validation.to_dict()
                }
            )
        
        # Import
        registry = get_registry()
        presets = registry.import_from_json(json.dumps(preset_json))
        
        if not presets:
            raise HTTPException(status_code=400, detail="Failed to import preset")
        
        return {
            "success": True,
            "imported": len(presets),
            "presets": [p.to_dict() for p in presets]
        }
    except HTTPException:
        raise
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")
    except Exception as e:
        logger.error(f"Error importing preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/export/{preset_id}")
async def export_preset(preset_id: str, pretty: bool = Query(True)):
    """Export preset to JSON"""
    try:
        registry = get_registry()
        preset = registry.get(preset_id)
        
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
        
        json_str = registry.export_to_json([preset_id], pretty=pretty)
        
        return JSONResponse(
            content=json.loads(json_str)[0],
            headers={
                "Content-Disposition": f"attachment; filename={preset_id}.json"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/bulk")
async def export_bulk(
    preset_ids: Optional[List[str]] = Body(None),
    indicator_type: Optional[str] = Body(None),
    pretty: bool = Body(True)
):
    """Export multiple presets to JSON"""
    try:
        registry = get_registry()
        json_str = registry.export_to_json(
            preset_ids=preset_ids,
            indicator_type=indicator_type,
            pretty=pretty
        )
        
        return JSONResponse(
            content=json.loads(json_str),
            headers={
                "Content-Disposition": "attachment; filename=presets_export.json"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== GENERATION ENDPOINTS ====================

@router.post("/generate/trg")
async def generate_trg(data: GenerateRequest):
    """Generate all 200 TRG system presets"""
    try:
        result = generate_trg_presets(
            save_to_db=True,
            replace_existing=data.replace_existing
        )
        return {
            "success": True,
            "result": result.to_dict()
        }
    except Exception as e:
        logger.error(f"Error generating TRG presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/dominant")
async def generate_dominant(data: GenerateRequest):
    """Generate all Dominant system presets"""
    try:
        result = generate_dominant_presets(
            save_to_db=True,
            replace_existing=data.replace_existing
        )
        return {
            "success": True,
            "result": result.to_dict()
        }
    except Exception as e:
        logger.error(f"Error generating Dominant presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/all")
async def generate_all(data: GenerateRequest):
    """Generate all system presets (TRG + Dominant)"""
    try:
        result = generate_all_system_presets(
            save_to_db=True,
            replace_existing=data.replace_existing
        )
        return {
            "success": True,
            "result": result.to_dict()
        }
    except Exception as e:
        logger.error(f"Error generating all presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== UTILITY ENDPOINTS ====================

@router.get("/types")
async def get_indicator_types():
    """Get list of supported indicator types"""
    registry = get_registry()
    return {
        "types": registry.get_registered_types(),
        "details": {
            IndicatorType.TRG.value: {
                "name": "TRG",
                "full_name": "Trend Range Grid",
                "system_presets": 200,
                "description": "ATR-based trend detection with 10 TP levels"
            },
            IndicatorType.DOMINANT.value: {
                "name": "Dominant",
                "full_name": "Dominant Channel",
                "system_presets": 125,
                "description": "Channel + Fibonacci based signals"
            }
        }
    }


@router.get("/categories")
async def get_categories():
    """Get list of preset categories"""
    return {
        "categories": [
            {"value": c.value, "label": c.value.replace("-", " ").title()}
            for c in PresetCategory
        ]
    }


@router.get("/sources")
async def get_sources():
    """Get list of preset sources"""
    return {
        "sources": [
            {"value": s.value, "label": s.value.replace("_", " ").title()}
            for s in PresetSource
        ]
    }


# ==================== LEGACY COMPATIBILITY ====================

# Keep old endpoints working for backward compatibility

@router.get("/dominant/list")
async def list_dominant_presets(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100),
    offset: int = Query(0)
):
    """List Dominant presets only (legacy endpoint)"""
    return await list_presets(
        indicator_type="dominant",
        category=category,
        search=search,
        limit=limit,
        offset=offset
    )


@router.post("/dominant/seed")
async def seed_dominant_presets(replace: bool = Query(False)):
    """Seed Dominant system presets (legacy endpoint)"""
    return await generate_dominant(GenerateRequest(replace_existing=replace))
