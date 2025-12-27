"""
Komas Trading Server - TRG Preset API Routes
=============================================
REST API for TRG indicator presets.

Separate from Dominant presets (/api/presets).

Table: trg_presets

Endpoints:
- GET    /api/trg-presets/list              - List TRG presets
- GET    /api/trg-presets/stats             - Get TRG preset statistics
- GET    /api/trg-presets/{id}              - Get single preset
- POST   /api/trg-presets/create            - Create new preset
- PUT    /api/trg-presets/{id}              - Update preset
- DELETE /api/trg-presets/{id}              - Delete preset
- GET    /api/trg-presets/generate-stream   - Generate 200 TRG (SSE)
- GET    /api/trg-presets/verify            - Verify system presets
- POST   /api/trg-presets/reset             - Reset system presets
- GET    /api/trg-presets/grid              - Get generation grid info

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

# Import TRG preset module
from app.presets import (
    TRGPreset,
    FilterProfile,
)
from app.database.trg_presets_db import (
    ensure_trg_presets_table,
    create_trg_preset,
    get_trg_preset,
    list_trg_presets,
    count_trg_presets,
    update_trg_preset,
    delete_trg_preset,
    delete_trg_system_presets,
    bulk_create_trg_presets,
    get_trg_preset_stats,
    verify_trg_system_presets,
)

router = APIRouter(prefix="/api/trg-presets", tags=["trg-presets"])
logger = logging.getLogger(__name__)


# ==================== REQUEST/RESPONSE MODELS ====================

class TRGPresetCreateRequest(BaseModel):
    """Request for creating a TRG preset"""
    name: str = Field(..., min_length=1, max_length=100)
    params: dict = Field(...)
    category: Optional[str] = Field(default="mid-term")
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = Field(default=None)


class TRGPresetUpdateRequest(BaseModel):
    """Request for updating a TRG preset"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = None
    params: Optional[dict] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_favorite: Optional[bool] = None


class ResetRequest(BaseModel):
    """Request for resetting presets"""
    confirm: bool = Field(default=False)


# ==================== SSE EVENT GENERATOR ====================

async def generate_sse_event(event: str, data: dict) -> str:
    """Generate SSE event string"""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def generate_trg_presets_stream(replace_existing: bool = False) -> AsyncGenerator[str, None]:
    """
    Generator for SSE streaming of TRG preset generation.
    
    Yields SSE events:
    - start: Generation started
    - progress: Progress update (every preset)
    - complete: Generation complete
    - error: Error occurred
    """
    try:
        # Start event
        total = len(TRGPreset.I1_VALUES) * len(TRGPreset.I2_VALUES) * len(TRGPreset.FILTER_PROFILES)
        yield await generate_sse_event("start", {
            "total": total,
            "replace_existing": replace_existing,
            "timestamp": datetime.utcnow().isoformat()
        })
        await asyncio.sleep(0.01)
        
        # Delete existing if requested
        if replace_existing:
            deleted = delete_trg_system_presets()
            yield await generate_sse_event("progress", {
                "phase": "cleanup",
                "deleted": deleted,
                "message": f"Deleted {deleted} existing presets"
            })
            await asyncio.sleep(0.01)
        
        ensure_trg_presets_table()
        
        # Generate presets
        created = 0
        skipped = 0
        errors = 0
        current = 0
        
        for i1 in TRGPreset.I1_VALUES:
            for i2 in TRGPreset.I2_VALUES:
                for profile in TRGPreset.FILTER_PROFILES:
                    current += 1
                    
                    try:
                        # Create preset
                        preset = TRGPreset.create_system_preset(i1, i2, profile)
                        
                        # Validate
                        is_valid, validation_errors = preset.validate()
                        if not is_valid:
                            errors += 1
                            yield await generate_sse_event("progress", {
                                "current": current,
                                "total": total,
                                "preset_id": preset.id,
                                "status": "error",
                                "error": validation_errors[0] if validation_errors else "Validation failed"
                            })
                            continue
                        
                        # Save to database
                        try:
                            create_trg_preset(
                                preset_id=preset.id,
                                name=preset.name,
                                params=preset.params,
                                category=preset.config.category,
                                description=preset.config.description,
                                source=preset.config.source,
                                tags=preset.config.tags,
                            )
                            created += 1
                            status = "created"
                        except ValueError as e:
                            if "already exists" in str(e):
                                skipped += 1
                                status = "skipped"
                            else:
                                errors += 1
                                status = "error"
                        
                        # Progress event (every 5th preset to reduce traffic)
                        if current % 5 == 0 or current == total:
                            yield await generate_sse_event("progress", {
                                "current": current,
                                "total": total,
                                "percent": round(current / total * 100, 1),
                                "created": created,
                                "skipped": skipped,
                                "errors": errors,
                                "last_preset": {
                                    "id": preset.id,
                                    "name": preset.name,
                                    "i1": i1,
                                    "i2": i2,
                                    "filter": profile.value,
                                    "status": status
                                }
                            })
                            await asyncio.sleep(0.01)
                    
                    except Exception as e:
                        errors += 1
                        logger.error(f"Error creating preset i1={i1}, i2={i2}, filter={profile.value}: {e}")
        
        # Complete event
        yield await generate_sse_event("complete", {
            "total_generated": total,
            "created": created,
            "skipped": skipped,
            "errors": errors,
            "timestamp": datetime.utcnow().isoformat(),
            "message": f"Generated {created} presets, skipped {skipped}, errors {errors}"
        })
    
    except Exception as e:
        logger.error(f"TRG generation failed: {e}")
        yield await generate_sse_event("error", {
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })


# ==================== LIST/STATS ENDPOINTS ====================

@router.get("/list")
async def get_trg_presets_list(
    category: Optional[str] = Query(None, description="Filter by category"),
    source: Optional[str] = Query(None, description="Filter by source: system, user, optimizer"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_favorite: Optional[bool] = Query(None, description="Filter by favorite"),
    limit: Optional[int] = Query(None, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List TRG presets with filters"""
    try:
        presets = list_trg_presets(
            category=category,
            source=source,
            is_active=is_active,
            is_favorite=is_favorite,
            search=search,
            limit=limit,
            offset=offset
        )
        
        total = count_trg_presets(source=source, category=category)
        
        return {
            "presets": presets,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error listing TRG presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_trg_stats():
    """Get TRG preset statistics"""
    try:
        stats = get_trg_preset_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting TRG stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CRUD ENDPOINTS ====================

@router.get("/{preset_id}")
async def get_single_trg_preset(preset_id: str):
    """Get a single TRG preset by ID"""
    try:
        preset = get_trg_preset(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
        return preset
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preset {preset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_new_trg_preset(data: TRGPresetCreateRequest):
    """Create a new TRG preset"""
    try:
        # Validate params
        preset = TRGPreset(name=data.name, params=data.params)
        is_valid, errors = preset.validate()
        
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid parameters", "details": errors}
            )
        
        # Create in database
        result = create_trg_preset(
            preset_id=f"TRG_USER_{data.name.replace(' ', '_')[:20]}",
            name=data.name,
            params=data.params,
            category=data.category or "mid-term",
            description=data.description,
            source="user",
            tags=data.tags
        )
        
        return {"status": "created", "preset": result}
    
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error creating preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{preset_id}")
async def update_existing_trg_preset(preset_id: str, data: TRGPresetUpdateRequest):
    """Update a TRG preset"""
    try:
        # Check exists
        existing = get_trg_preset(preset_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
        
        # Don't allow editing system presets
        if existing.get("source") == "system":
            return JSONResponse(
                status_code=403,
                content={"error": "Cannot edit system presets. Clone it first."}
            )
        
        # Update
        result = update_trg_preset(
            preset_id=preset_id,
            name=data.name,
            description=data.description,
            category=data.category,
            params=data.params,
            is_active=data.is_active,
            is_favorite=data.is_favorite,
            tags=data.tags
        )
        
        return {"status": "updated", "preset": result}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preset {preset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{preset_id}")
async def delete_single_trg_preset(preset_id: str):
    """Delete a TRG preset"""
    try:
        existing = get_trg_preset(preset_id)
        if not existing:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")
        
        # Don't allow deleting system presets via this endpoint
        if existing.get("source") == "system":
            return JSONResponse(
                status_code=403,
                content={"error": "Cannot delete system presets. Use /reset endpoint."}
            )
        
        deleted = delete_trg_preset(preset_id)
        return {"status": "deleted" if deleted else "not_found", "id": preset_id}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting preset {preset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== GENERATION ENDPOINTS ====================

@router.get("/generate-stream")
async def generate_trg_stream(replace: bool = Query(False)):
    """Generate all 200 TRG system presets with SSE streaming"""
    return StreamingResponse(
        generate_trg_presets_stream(replace_existing=replace),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/generate")
async def generate_trg_sync(replace: bool = Body(False, embed=True)):
    """Generate all 200 TRG system presets (synchronous)"""
    try:
        if replace:
            deleted = delete_trg_system_presets()
            logger.info(f"Deleted {deleted} existing TRG system presets")
        
        ensure_trg_presets_table()
        
        # Generate all presets
        presets_to_create = []
        for i1 in TRGPreset.I1_VALUES:
            for i2 in TRGPreset.I2_VALUES:
                for profile in TRGPreset.FILTER_PROFILES:
                    preset = TRGPreset.create_system_preset(i1, i2, profile)
                    presets_to_create.append({
                        "id": preset.id,
                        "name": preset.name,
                        "params": preset.params,
                        "category": preset.config.category,
                        "description": preset.config.description,
                        "source": preset.config.source,
                        "tags": preset.config.tags
                    })
        
        # Bulk create
        result = bulk_create_trg_presets(presets_to_create, skip_duplicates=True)
        
        return {
            "status": "complete",
            "total": len(presets_to_create),
            "created": result["created"],
            "skipped": result["skipped"],
            "errors": result["errors"]
        }
    
    except Exception as e:
        logger.error(f"TRG generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== VERIFICATION ENDPOINTS ====================

@router.get("/verify")
async def verify_trg_presets():
    """Verify all TRG system presets exist and are valid"""
    try:
        result = verify_trg_system_presets()
        return {
            "indicator": "trg",
            "expected": result["expected"],
            "found": result["found"],
            "missing_count": result["missing_count"],
            "invalid_count": result["invalid_count"],
            "is_valid": result["is_valid"],
            "missing_sample": result["missing"][:10],
            "invalid_sample": result["invalid"][:10],
            "message": "All TRG presets OK" if result["is_valid"] else "Some presets missing or invalid"
        }
    except Exception as e:
        logger.error(f"Error verifying TRG presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_trg_presets(data: ResetRequest):
    """Delete all TRG system presets"""
    try:
        if not data.confirm:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Confirmation required",
                    "message": "Set confirm=true to delete all TRG system presets"
                }
            )
        
        deleted = delete_trg_system_presets()
        
        return {
            "status": "reset",
            "deleted": deleted,
            "message": f"Deleted {deleted} TRG system presets"
        }
    
    except Exception as e:
        logger.error(f"Error resetting TRG presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INFO ENDPOINTS ====================

@router.get("/grid")
async def get_trg_grid_info():
    """Get TRG preset generation grid information"""
    return {
        "indicator": "trg",
        "total_presets": len(TRGPreset.I1_VALUES) * len(TRGPreset.I2_VALUES) * len(TRGPreset.FILTER_PROFILES),
        "i1_values": TRGPreset.I1_VALUES,
        "i1_count": len(TRGPreset.I1_VALUES),
        "i2_values": TRGPreset.I2_VALUES,
        "i2_count": len(TRGPreset.I2_VALUES),
        "filter_profiles": [p.value for p in TRGPreset.FILTER_PROFILES],
        "filter_count": len(TRGPreset.FILTER_PROFILES),
        "naming_convention": "{FILTER}_{i1}_{i2*10}",
        "examples": [
            "N_14_20 = None filter, i1=14, i2=2.0",
            "T_60_40 = Trend filter, i1=60, i2=4.0",
            "F_200_75 = Full filter, i1=200, i2=7.5"
        ]
    }


@router.get("/categories")
async def get_trg_categories():
    """Get available categories"""
    return {
        "categories": [
            {"value": "scalp", "label": "Scalp", "i1_range": "≤20"},
            {"value": "short-term", "label": "Short-Term", "i1_range": "21-40"},
            {"value": "mid-term", "label": "Mid-Term", "i1_range": "41-80"},
            {"value": "swing", "label": "Swing", "i1_range": "81-130"},
            {"value": "long-term", "label": "Long-Term", "i1_range": ">130"}
        ]
    }


@router.get("/filters")
async def get_trg_filter_profiles():
    """Get available filter profiles"""
    return {
        "profiles": [
            {
                "code": "N",
                "name": "None",
                "description": "No filters, maximum signals",
                "filters": []
            },
            {
                "code": "T",
                "name": "Trend",
                "description": "SuperTrend filter only",
                "filters": ["supertrend"]
            },
            {
                "code": "M",
                "name": "Momentum",
                "description": "RSI filter only",
                "filters": ["rsi"]
            },
            {
                "code": "S",
                "name": "Strength",
                "description": "ADX filter only",
                "filters": ["adx"]
            },
            {
                "code": "F",
                "name": "Full",
                "description": "All filters enabled",
                "filters": ["supertrend", "rsi", "adx", "volume"]
            }
        ]
    }
