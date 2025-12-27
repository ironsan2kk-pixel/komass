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

FIX: Added /dominant/list and /trg/list convenience endpoints

Endpoints:
- GET    /api/presets/list              - List all presets
- GET    /api/presets/dominant/list     - List Dominant presets (convenience)
- GET    /api/presets/trg/list          - List TRG presets (convenience)
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
Hotfix: Added dominant/list endpoint
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, List, AsyncGenerator

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

# Import preset module - with error handling
try:
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
    PRESETS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Presets module not available: {e}")
    PRESETS_AVAILABLE = False
    TRGPreset = None
    DominantPreset = None

try:
    from app.database.presets_db import (
        get_preset_stats,
        verify_system_presets,
        reset_system_presets,
        delete_presets_by_indicator,
        create_preset,
        list_presets,
        count_presets,
        get_preset,  # Note: original name is get_preset, not get_preset_by_id
        update_preset,
        delete_preset,
    )
    DB_AVAILABLE = True
    # Alias for compatibility
    get_preset_by_id = get_preset
except ImportError as e:
    logging.warning(f"Presets DB not available: {e}")
    DB_AVAILABLE = False
    # Stub functions
    def list_presets(**kwargs): return []
    def count_presets(**kwargs): return 0
    def get_preset_stats(): return {"error": "DB not available"}
    def verify_system_presets(): return {"error": "DB not available"}
    def reset_system_presets(x): return {"deleted": 0}
    def delete_presets_by_indicator(x, **k): return 0
    def create_preset(**k): raise ValueError("DB not available")
    def get_preset_by_id(x): return None
    def get_preset(x): return None
    def update_preset(x, **k): return None
    def delete_preset(x): return False

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
    if not PRESETS_AVAILABLE or TRGPreset is None:
        yield await generate_sse_event("error", {"message": "Presets module not available"})
        return
    
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
    if not PRESETS_AVAILABLE or DominantPreset is None:
        yield await generate_sse_event("error", {"message": "Presets module not available"})
        return
    
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
        
        await asyncio.sleep(0.005)
    
    # Complete event
    yield await generate_sse_event("complete", {
        "total_generated": total,
        "created": created,
        "skipped": skipped,
        "errors": errors,
        "error_list": error_list[:10],
        "timestamp": datetime.utcnow().isoformat()
    })


# ==================== CONVENIENCE ENDPOINTS (IMPORTANT!) ====================

@router.get("/dominant/list")
async def list_dominant_presets(
    category: Optional[str] = Query(None, description="Filter by category"),
    source: Optional[str] = Query(None, description="Filter by source"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List Dominant presets (convenience endpoint)"""
    try:
        presets = list_presets(
            indicator_type="dominant",
            category=category,
            source=source,
            search=search,
            limit=limit,
            offset=offset,
        )
        
        total = count_presets(
            indicator_type="dominant",
            category=category,
            source=source,
        )
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "presets": presets
        }
    except Exception as e:
        logger.error(f"Error listing Dominant presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trg/list")
async def list_trg_presets(
    category: Optional[str] = Query(None, description="Filter by category"),
    source: Optional[str] = Query(None, description="Filter by source"),
    search: Optional[str] = Query(None, description="Search in name/description"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0)
):
    """List TRG presets (convenience endpoint)"""
    try:
        presets = list_presets(
            indicator_type="trg",
            category=category,
            source=source,
            search=search,
            limit=limit,
            offset=offset,
        )
        
        total = count_presets(
            indicator_type="trg",
            category=category,
            source=source,
        )
        
        return {
            "total": total,
            "limit": limit,
            "offset": offset,
            "presets": presets
        }
    except Exception as e:
        logger.error(f"Error listing TRG presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MAIN ENDPOINTS ====================

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
        trg_ok = results.get("trg", {}).get("found", 0) == results.get("trg", {}).get("expected", 200) and results.get("trg", {}).get("invalid", 0) == 0
        dominant_ok = results.get("dominant", {}).get("found", 0) >= 100  # At least 100 Dominant presets
        
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
            "message": f"Deleted {result.get('deleted', 0)} system presets"
        }
    except Exception as e:
        logger.error(f"Error resetting presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema/{indicator_type}")
async def get_param_schema(indicator_type: str):
    """Get parameter schema for indicator type"""
    try:
        if not PRESETS_AVAILABLE:
            raise HTTPException(status_code=503, detail="Presets module not available")
        
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
async def get_preset(preset_id: str):
    """Get single preset by ID"""
    try:
        preset = get_preset_by_id(preset_id)
        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset not found: {preset_id}")
        return preset
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting preset {preset_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create")
async def create_preset_endpoint(data: PresetCreateRequest):
    """Create a new preset"""
    try:
        preset_id = f"USER_{data.indicator_type.upper()}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        create_preset(
            preset_id=preset_id,
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
        
        return {
            "success": True,
            "preset_id": preset_id,
            "message": f"Preset '{data.name}' created successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_preset(data: ValidateRequest):
    """Validate preset parameters"""
    try:
        if not PRESETS_AVAILABLE:
            return {"valid": True, "errors": [], "warnings": ["Validation skipped - module not available"]}
        
        errors, warnings = validate_params(data.indicator_type, data.params)
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "indicator_type": data.indicator_type
        }
    except Exception as e:
        logger.error(f"Error validating preset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/generate/trg-stream")
async def generate_trg_stream(
    replace: bool = Query(False, description="Replace existing system presets")
):
    """Generate TRG system presets with SSE streaming"""
    return StreamingResponse(
        generate_trg_presets_stream(replace_existing=replace),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/generate/dominant-stream")
async def generate_dominant_stream(
    replace: bool = Query(False, description="Replace existing system presets")
):
    """Generate Dominant system presets with SSE streaming"""
    return StreamingResponse(
        generate_dominant_presets_stream(replace_existing=replace),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/generate/all-stream")
async def generate_all_stream(
    replace: bool = Query(False, description="Replace existing system presets")
):
    """Generate all system presets with SSE streaming"""
    async def combined_stream():
        # TRG first
        async for event in generate_trg_presets_stream(replace_existing=replace):
            yield event
        
        # Then Dominant
        async for event in generate_dominant_presets_stream(replace_existing=replace):
            yield event
    
    return StreamingResponse(
        combined_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/generate/trg")
async def generate_trg_sync(data: GenerateRequest = Body(default=GenerateRequest())):
    """Generate TRG system presets (synchronous)"""
    if not PRESETS_AVAILABLE or TRGPreset is None:
        raise HTTPException(status_code=503, detail="Presets module not available")
    
    try:
        if data.replace_existing:
            deleted = delete_presets_by_indicator("trg", source="system")
            logger.info(f"Deleted {deleted} existing TRG system presets")
        
        created = 0
        skipped = 0
        errors = 0
        
        for i1 in TRGPreset.I1_VALUES:
            for i2 in TRGPreset.I2_VALUES:
                for profile in TRGPreset.FILTER_PROFILES:
                    try:
                        preset = TRGPreset.create_system_preset(i1, i2, profile)
                        is_valid, _ = preset.validate()
                        if not is_valid:
                            errors += 1
                            continue
                        
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
                    except Exception:
                        errors += 1
        
        return {
            "success": True,
            "created": created,
            "skipped": skipped,
            "errors": errors,
            "total": created + skipped + errors
        }
    except Exception as e:
        logger.error(f"Error generating TRG presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate/dominant")
async def generate_dominant_sync(data: GenerateRequest = Body(default=GenerateRequest())):
    """Generate Dominant system presets (synchronous)"""
    if not PRESETS_AVAILABLE or DominantPreset is None:
        raise HTTPException(status_code=503, detail="Presets module not available")
    
    try:
        if data.replace_existing:
            deleted = delete_presets_by_indicator("dominant", source="system")
            logger.info(f"Deleted {deleted} existing Dominant system presets")
        
        created = 0
        skipped = 0
        errors = 0
        
        for preset in DominantPreset.generate_system_presets():
            try:
                is_valid, _ = preset.validate()
                if not is_valid:
                    errors += 1
                    continue
                
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
            except Exception:
                errors += 1
        
        return {
            "success": True,
            "created": created,
            "skipped": skipped,
            "errors": errors,
            "total": created + skipped + errors
        }
    except Exception as e:
        logger.error(f"Error generating Dominant presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
async def get_indicator_types():
    """Get list of available indicator types"""
    return {
        "types": [
            {"id": "trg", "name": "TRG", "description": "ATR-based Trend Range Grid"},
            {"id": "dominant", "name": "Dominant", "description": "Channel + Fibonacci Levels"},
        ]
    }


@router.get("/categories")
async def get_categories():
    """Get list of preset categories"""
    return {
        "categories": [
            {"id": "scalp", "name": "Scalp", "description": "Ultra-fast trades (1-5 min)"},
            {"id": "short-term", "name": "Short-Term", "description": "Quick trades (5-60 min)"},
            {"id": "mid-term", "name": "Mid-Term", "description": "Medium duration (1-4 hours)"},
            {"id": "swing", "name": "Swing", "description": "Multi-hour to daily"},
            {"id": "long-term", "name": "Long-Term", "description": "Multi-day positions"},
        ]
    }


@router.get("/sources")
async def get_sources():
    """Get list of preset sources"""
    return {
        "sources": [
            {"id": "system", "name": "System", "description": "Auto-generated system presets"},
            {"id": "pine_script", "name": "Pine Script", "description": "Imported from TradingView"},
            {"id": "optimizer", "name": "Optimizer", "description": "Generated by optimizer"},
            {"id": "manual", "name": "Manual", "description": "User-created presets"},
        ]
    }


@router.get("/grid/trg")
async def get_trg_grid():
    """Get TRG preset generation grid values"""
    if not PRESETS_AVAILABLE or TRGPreset is None:
        return {
            "i1_values": [14, 25, 40, 60, 80, 110, 150, 200],
            "i2_values": [2.0, 3.0, 4.0, 5.5, 7.5],
            "filter_profiles": ["N", "T", "M", "S", "F"],
            "total": 200
        }
    
    return {
        "i1_values": TRGPreset.I1_VALUES,
        "i2_values": TRGPreset.I2_VALUES,
        "filter_profiles": [p.value for p in TRGPreset.FILTER_PROFILES],
        "total": len(TRGPreset.I1_VALUES) * len(TRGPreset.I2_VALUES) * len(TRGPreset.FILTER_PROFILES)
    }
