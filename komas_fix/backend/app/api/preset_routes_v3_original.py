"""
Komas Trading Server - Preset API Routes (v3)
=============================================
REST API for managing indicator presets with SSE streaming.

Changes in Chat #30:
- Added SSE streaming for preset generation (/generate/trg-stream)
- Added verification endpoint (/verify)
- Added reset endpoint (/reset)
- Added batch validation (/validate/batch)
- Improved error handling

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

Generation with SSE:
- GET    /api/presets/generate/trg-stream      - Generate 200 TRG (SSE)
- GET    /api/presets/generate/dominant-stream - Generate Dominant (SSE)
- GET    /api/presets/generate/all-stream      - Generate all (SSE)

Verification:
- GET    /api/presets/verify            - Verify system presets
- POST   /api/presets/reset             - Reset (delete) system presets

Chat: #30 — Presets TRG Generator
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, List, AsyncGenerator

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
    IndicatorType,
    PresetCategory,
    PresetSource,
    FilterProfile,
)
from app.database.presets_db import (
    get_preset_stats,
    verify_system_presets,
    reset_system_presets,
    delete_presets_by_indicator,
    create_preset,
    list_presets,
    count_presets,
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


class ResetRequest(BaseModel):
    """Request for resetting presets"""
    indicator_type: Optional[str] = Field(default=None)
    confirm: bool = Field(default=False)


# ==================== SSE EVENT GENERATOR ====================

async def generate_sse_event(event: str, data: dict) -> str:
    """Generate SSE event string"""
    json_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {json_data}\n\n"


async def generate_trg_presets_stream(replace_existing: bool = False) -> AsyncGenerator[str, None]:
    """Generate 200 TRG presets with SSE progress"""
    from app.presets.base import PresetConfig, PresetSource
    
    total = len(TRGPreset.I1_VALUES) * len(TRGPreset.I2_VALUES) * len(TRGPreset.FILTER_PROFILES)
    
    # Start event
    yield await generate_sse_event("start", {
        "total": total,
        "indicator_type": "trg",
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Delete existing if requested
    if replace_existing:
        deleted = delete_presets_by_indicator("trg", source="system")
        yield await generate_sse_event("cleanup", {
            "deleted": deleted,
            "message": f"Deleted {deleted} existing TRG system presets"
        })
        await asyncio.sleep(0.01)
    
    created = 0
    skipped = 0
    errors = 0
    error_list = []
    
    for i1_idx, i1 in enumerate(TRGPreset.I1_VALUES):
        for i2_idx, i2 in enumerate(TRGPreset.I2_VALUES):
            for profile_idx, profile in enumerate(TRGPreset.FILTER_PROFILES):
                current = (i1_idx * len(TRGPreset.I2_VALUES) * len(TRGPreset.FILTER_PROFILES) +
                          i2_idx * len(TRGPreset.FILTER_PROFILES) + 
                          profile_idx + 1)
                
                try:
                    # Create preset
                    preset = TRGPreset.create_system_preset(i1, i2, profile)
                    
                    # Validate
                    is_valid, validation_errors = preset.validate()
                    if not is_valid:
                        errors += 1
                        error_list.append(f"{preset.id}: {validation_errors}")
                        continue
                    
                    # Save to database
                    try:
                        create_preset(
                            preset_id=preset.id,
                            name=preset.name,
                            indicator_type=preset.config.indicator_type,
                            params=preset.params,
                            category=preset.config.category,
                            source=preset.config.source,
                            description=preset.config.description,
                            tags=preset.config.tags,
                        )
                        created += 1
                    except ValueError as e:
                        if "already exists" in str(e):
                            skipped += 1
                        else:
                            errors += 1
                            error_list.append(f"{preset.id}: {e}")
                    except Exception as e:
                        errors += 1
                        error_list.append(f"{preset.id}: {e}")
                
                except Exception as e:
                    errors += 1
                    error_list.append(f"i1={i1}, i2={i2}, filter={profile.value}: {e}")
                
                # Progress event (every preset)
                yield await generate_sse_event("progress", {
                    "current": current,
                    "total": total,
                    "percent": round(current / total * 100, 1),
                    "preset_id": f"TRG_SYS_{profile.value}_{i1}_{int(i2*10)}",
                    "i1": i1,
                    "i2": i2,
                    "filter": profile.value,
                    "created": created,
                    "skipped": skipped,
                    "errors": errors
                })
                
                # Small delay for smoother streaming
                await asyncio.sleep(0.005)
    
    # Complete event
    yield await generate_sse_event("complete", {
        "total_generated": total,
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "error_list": error_list[:10],  # First 10 errors
        "duration_hint": "Check stats for final count",
        "timestamp": datetime.utcnow().isoformat()
    })


async def generate_dominant_presets_stream(replace_existing: bool = False) -> AsyncGenerator[str, None]:
    """Generate Dominant presets with SSE progress"""
    from app.presets import DominantPreset
    
    # Get preset data
    preset_data_list = DominantPreset.get_system_presets_data()
    total = len(preset_data_list)
    
    # Start event
    yield await generate_sse_event("start", {
        "total": total,
        "indicator_type": "dominant",
        "timestamp": datetime.utcnow().isoformat()
    })
    
    # Delete existing if requested
    if replace_existing:
        deleted = delete_presets_by_indicator("dominant", source="system")
        yield await generate_sse_event("cleanup", {
            "deleted": deleted,
            "message": f"Deleted {deleted} existing Dominant system presets"
        })
        await asyncio.sleep(0.01)
    
    created = 0
    skipped = 0
    errors = 0
    error_list = []
    
    for i, preset in enumerate(DominantPreset.generate_system_presets()):
        current = i + 1
        
        try:
            # Validate
            is_valid, validation_errors = preset.validate()
            if not is_valid:
                errors += 1
                error_list.append(f"{preset.id}: {validation_errors}")
                continue
            
            # Save to database
            try:
                create_preset(
                    preset_id=preset.id,
                    name=preset.name,
                    indicator_type=preset.config.indicator_type,
                    params=preset.params,
                    category=preset.config.category,
                    source=preset.config.source,
                    description=preset.config.description,
                    tags=preset.config.tags,
                )
                created += 1
            except ValueError as e:
                if "already exists" in str(e):
                    skipped += 1
                else:
                    errors += 1
                    error_list.append(f"{preset.id}: {e}")
            except Exception as e:
                errors += 1
                error_list.append(f"{preset.id}: {e}")
        
        except Exception as e:
            errors += 1
            error_list.append(f"preset {i}: {e}")
        
        # Progress event
        yield await generate_sse_event("progress", {
            "current": current,
            "total": total,
            "percent": round(current / total * 100, 1),
            "preset_id": preset.id if 'preset' in dir() else f"DOM_{i}",
            "created": created,
            "skipped": skipped,
            "errors": errors
        })
        
        await asyncio.sleep(0.01)
    
    # Complete event
    yield await generate_sse_event("complete", {
        "total_generated": total,
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "error_list": error_list[:10],
        "timestamp": datetime.utcnow().isoformat()
    })


# ==================== ENDPOINTS ====================

@router.get("/list")
async def list_presets_endpoint(
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
            offset=offset,
        )
        
        total = count_presets(
            indicator_type=indicator_type,
            category=category,
            source=source,
            is_active=is_active,
        )
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "presets": presets
        }
    except Exception as e:
        logger.error(f"Error listing presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats_endpoint():
    """Get preset statistics"""
    try:
        stats = get_preset_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting preset stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/verify")
async def verify_presets():
    """Verify all system presets exist and are valid"""
    try:
        results = verify_system_presets()
        
        # Calculate summary
        trg_ok = results["trg"]["found"] == results["trg"]["expected"] and results["trg"]["invalid"] == 0
        dominant_ok = results["dominant"]["found"] >= 100  # At least 100 Dominant presets
        
        results["summary"] = {
            "all_ok": trg_ok and dominant_ok,
            "trg_ok": trg_ok,
            "dominant_ok": dominant_ok,
            "message": "All system presets verified" if (trg_ok and dominant_ok) else "Some presets missing or invalid"
        }
        
        return results
    except Exception as e:
        logger.error(f"Error verifying presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_presets(data: ResetRequest):
    """Reset (delete) system presets"""
    if not data.confirm:
        return {
            "success": False,
            "message": "Set confirm=true to proceed with deletion",
            "warning": "This will delete all system presets!"
        }
    
    try:
        result = reset_system_presets(data.indicator_type)
        return {
            "success": True,
            "result": result,
            "message": f"Deleted {result['deleted']} system presets"
        }
    except Exception as e:
        logger.error(f"Error resetting presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/{indicator_type}")
async def get_param_schema(indicator_type: str):
    """Get parameter schema for indicator type"""
    try:
        if indicator_type == "trg":
            preset_class = TRGPreset
        elif indicator_type == "dominant":
            preset_class = DominantPreset
        else:
            raise HTTPException(status_code=404, detail=f"Unknown indicator type: {indicator_type}")
        
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
async def get_preset_endpoint(preset_id: str):
    """Get single preset by ID"""
    try:
        from app.database.presets_db import get_preset
        preset = get_preset(preset_id)
        
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
        
        return preset
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_preset_endpoint(data: PresetCreateRequest):
    """Create a new preset"""
    try:
        preset = create_preset(
            name=data.name,
            indicator_type=data.indicator_type,
            params=data.params,
            category=data.category,
            source=data.source or "manual",
            description=data.description,
            symbol=data.symbol,
            timeframe=data.timeframe,
            tags=data.tags,
        )
        
        return {"success": True, "preset": preset}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{preset_id}")
async def update_preset_endpoint(preset_id: str, data: PresetUpdateRequest):
    """Update an existing preset"""
    try:
        from app.database.presets_db import update_preset
        
        updates = data.model_dump(exclude_none=True)
        preset = update_preset(preset_id, **updates)
        
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
        
        return {"success": True, "preset": preset}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{preset_id}")
async def delete_preset_endpoint(preset_id: str):
    """Delete a preset"""
    try:
        from app.database.presets_db import delete_preset
        deleted = delete_preset(preset_id)
        
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


# ==================== SSE GENERATION ENDPOINTS ====================

@router.get("/generate/trg-stream")
async def generate_trg_stream(replace: bool = Query(False)):
    """Generate all 200 TRG system presets with SSE progress"""
    return StreamingResponse(
        generate_trg_presets_stream(replace_existing=replace),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/generate/dominant-stream")
async def generate_dominant_stream(replace: bool = Query(False)):
    """Generate all Dominant system presets with SSE progress"""
    return StreamingResponse(
        generate_dominant_presets_stream(replace_existing=replace),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/generate/all-stream")
async def generate_all_stream(replace: bool = Query(False)):
    """Generate all system presets (TRG + Dominant) with SSE progress"""
    async def combined_generator():
        # First generate TRG
        yield await generate_sse_event("phase", {
            "phase": "trg",
            "message": "Starting TRG preset generation"
        })
        
        async for event in generate_trg_presets_stream(replace_existing=replace):
            yield event
        
        # Then generate Dominant
        yield await generate_sse_event("phase", {
            "phase": "dominant",
            "message": "Starting Dominant preset generation"
        })
        
        async for event in generate_dominant_presets_stream(replace_existing=replace):
            yield event
        
        # Final summary
        stats = get_preset_stats()
        yield await generate_sse_event("final", {
            "total_presets": stats["total_presets"],
            "trg_count": stats.get("by_indicator", {}).get("trg", 0),
            "dominant_count": stats.get("by_indicator", {}).get("dominant", 0),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    return StreamingResponse(
        combined_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ==================== SYNC GENERATION (no streaming) ====================

@router.post("/generate/trg")
async def generate_trg_sync(data: GenerateRequest):
    """Generate all 200 TRG system presets (synchronous)"""
    try:
        created = 0
        skipped = 0
        errors = 0
        
        if data.replace_existing:
            delete_presets_by_indicator("trg", source="system")
        
        for i1 in TRGPreset.I1_VALUES:
            for i2 in TRGPreset.I2_VALUES:
                for profile in TRGPreset.FILTER_PROFILES:
                    try:
                        preset = TRGPreset.create_system_preset(i1, i2, profile)
                        is_valid, _ = preset.validate()
                        if not is_valid:
                            errors += 1
                            continue
                        
                        create_preset(
                            preset_id=preset.id,
                            name=preset.name,
                            indicator_type=preset.config.indicator_type,
                            params=preset.params,
                            category=preset.config.category,
                            source=preset.config.source,
                            description=preset.config.description,
                            tags=preset.config.tags,
                        )
                        created += 1
                    except ValueError:
                        skipped += 1
                    except Exception as e:
                        errors += 1
                        logger.error(f"Error creating preset: {e}")
        
        return {
            "success": True,
            "result": {
                "total_generated": 200,
                "created": created,
                "skipped": skipped,
                "errors": errors
            }
        }
    except Exception as e:
        logger.error(f"Error generating TRG presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/dominant")
async def generate_dominant_sync(data: GenerateRequest):
    """Generate all Dominant system presets (synchronous)"""
    try:
        created = 0
        skipped = 0
        errors = 0
        
        if data.replace_existing:
            delete_presets_by_indicator("dominant", source="system")
        
        for preset in DominantPreset.generate_system_presets():
            try:
                is_valid, _ = preset.validate()
                if not is_valid:
                    errors += 1
                    continue
                
                create_preset(
                    preset_id=preset.id,
                    name=preset.name,
                    indicator_type=preset.config.indicator_type,
                    params=preset.params,
                    category=preset.config.category,
                    source=preset.config.source,
                    description=preset.config.description,
                    tags=preset.config.tags,
                )
                created += 1
            except ValueError:
                skipped += 1
            except Exception as e:
                errors += 1
                logger.error(f"Error creating preset: {e}")
        
        return {
            "success": True,
            "result": {
                "created": created,
                "skipped": skipped,
                "errors": errors
            }
        }
    except Exception as e:
        logger.error(f"Error generating Dominant presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== UTILITY ENDPOINTS ====================

@router.get("/types")
async def get_indicator_types():
    """Get list of supported indicator types"""
    return {
        "types": ["trg", "dominant"],
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


@router.get("/grid/trg")
async def get_trg_grid():
    """Get TRG preset generation grid (8×5×5=200)"""
    return {
        "i1_values": TRGPreset.I1_VALUES,
        "i2_values": TRGPreset.I2_VALUES,
        "filter_profiles": [
            {"code": fp.value, "name": fp.name}
            for fp in FilterProfile
        ],
        "total_presets": len(TRGPreset.I1_VALUES) * len(TRGPreset.I2_VALUES) * len(list(FilterProfile)),
        "naming_convention": "{FILTER}_{i1}_{i2*10}",
        "examples": [
            "N_14_20", "T_40_40", "M_60_55", "S_110_30", "F_200_75"
        ]
    }
