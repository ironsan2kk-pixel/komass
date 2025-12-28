"""
KOMAS v4.0 — Filter API Routes
===============================

API endpoints for filter configuration management.

Endpoints:
- GET  /api/filters/available          - List all available filters
- GET  /api/filters/categories         - List filter categories
- GET  /api/filters/profiles           - List filter profiles
- GET  /api/filters/bot/{bot_id}       - Get filter config for bot
- POST /api/filters/bot/{bot_id}       - Save filter config for bot
- PUT  /api/filters/bot/{bot_id}/{filter_name} - Update single filter
- DELETE /api/filters/bot/{bot_id}/{filter_name} - Delete filter config
- POST /api/filters/validate           - Validate filter configuration
- GET  /api/filters/bot/{bot_id}/stats - Get filter statistics
- GET  /api/filters/bot/{bot_id}/log   - Get filter decision log
- POST /api/filters/bot/{bot_id}/reset - Reset filter stats

Chat #43: Filters Integration
Author: KOMAS Team
Version: 4.0
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging
import os
import json

# Database path
DB_PATH = os.environ.get("KOMAS_DB_PATH", "data/komas.db")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/filters", tags=["filters"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class FilterConfigUpdate(BaseModel):
    """Single filter configuration."""
    enabled: bool = True
    params: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"


class BotFilterConfigRequest(BaseModel):
    """Full filter configuration for a bot."""
    filters: Dict[str, FilterConfigUpdate]
    
    class Config:
        json_schema_extra = {
            "example": {
                "filters": {
                    "session_filter": {
                        "enabled": True,
                        "params": {
                            "sessions": ["europe", "us"]
                        }
                    },
                    "atr_filter": {
                        "enabled": True,
                        "params": {
                            "min_atr": 1.0,
                            "max_atr": 5.0
                        }
                    }
                }
            }
        }


class FilterValidationRequest(BaseModel):
    """Request to validate filter configuration."""
    filter_name: str
    config: Dict[str, Any]


class FilterValidationResponse(BaseModel):
    """Validation result."""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []


class FilterStatsResponse(BaseModel):
    """Filter statistics."""
    bot_id: str
    loaded: bool
    filter_count: int
    enabled_count: int
    statistics: Dict[str, Any]
    log_entries: int


class FilterLogResponse(BaseModel):
    """Filter decision log."""
    entries: List[Dict[str, Any]]
    total: int


class AvailableFilterResponse(BaseModel):
    """Available filter info."""
    name: str
    description: str
    category: str
    priority: str
    config_schema: Dict[str, Any]


class FilterCategoryResponse(BaseModel):
    """Filter category info."""
    name: str
    display_name: str
    filter_count: int
    filters: List[str]


class FilterProfileResponse(BaseModel):
    """Filter profile info."""
    name: str
    description: str
    filter_count: int
    filters: List[str]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_manager_for_bot(bot_id: str):
    """
    Get or create FilterManager for a bot.
    
    In a production system, these would be cached/pooled.
    """
    from app.filters.manager import FilterManager
    
    manager = FilterManager(bot_id)
    
    # Try to load from database
    if os.path.exists(DB_PATH):
        try:
            manager.load_config(DB_PATH)
        except Exception as e:
            logger.warning(f"Could not load config for bot {bot_id}: {e}")
            # Initialize with empty config
            manager.load_config_from_dict({})
    else:
        manager.load_config_from_dict({})
    
    return manager


def ensure_db_path():
    """Ensure database directory exists."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)


# =============================================================================
# ENDPOINTS - Available Filters
# =============================================================================

@router.get("/available", response_model=Dict[str, AvailableFilterResponse])
async def get_available_filters():
    """
    Get all available filters from registry.
    
    Returns dict of filter_name -> filter info including config schema.
    """
    from app.filters.manager import FilterManager
    
    try:
        available = FilterManager.get_available_filters()
        
        result = {}
        for name, info in available.items():
            result[name] = AvailableFilterResponse(
                name=name,
                description=info.get("description", ""),
                category=info.get("category", "unknown"),
                priority=info.get("priority", "MEDIUM"),
                config_schema=info.get("config_schema", {})
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting available filters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories", response_model=List[FilterCategoryResponse])
async def get_filter_categories():
    """
    Get all filter categories with their filters.
    """
    from app.filters.manager import get_filter_categories
    
    try:
        categories = get_filter_categories()
        
        return [
            FilterCategoryResponse(
                name=cat["name"],
                display_name=cat["display_name"],
                filter_count=cat["filter_count"],
                filters=cat["filters"]
            )
            for cat in categories
        ]
        
    except Exception as e:
        logger.error(f"Error getting filter categories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles")
async def get_filter_profiles():
    """
    Get available filter profiles.
    
    Profiles are predefined filter configurations for different trading styles.
    """
    from app.filters.manager import get_filter_profiles
    
    try:
        profiles = get_filter_profiles()
        
        result = []
        descriptions = {
            "minimal": "Minimal filtering - only basic time restrictions",
            "conservative": "Conservative filtering - strict risk control",
            "balanced": "Balanced filtering - moderate restrictions",
            "aggressive": "Aggressive filtering - fewer restrictions for more signals"
        }
        
        for name, config in profiles.items():
            result.append({
                "name": name,
                "description": descriptions.get(name, ""),
                "filter_count": len(config),
                "filters": list(config.keys())
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting filter profiles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{profile_name}")
async def get_filter_profile(profile_name: str):
    """
    Get detailed configuration for a specific profile.
    """
    from app.filters.manager import get_filter_profiles
    
    profiles = get_filter_profiles()
    if profile_name not in profiles:
        raise HTTPException(status_code=404, detail=f"Profile not found: {profile_name}")
    
    return {
        "name": profile_name,
        "config": profiles[profile_name]
    }


# =============================================================================
# ENDPOINTS - Bot Filter Config
# =============================================================================

@router.get("/bot/{bot_id}")
async def get_bot_filter_config(bot_id: str):
    """
    Get filter configuration for a bot.
    """
    try:
        manager = get_manager_for_bot(bot_id)
        
        return {
            "bot_id": bot_id,
            "filters": manager.export_config(),
            "summary": manager.get_filter_summary()
        }
        
    except Exception as e:
        logger.error(f"Error getting bot filter config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bot/{bot_id}")
async def save_bot_filter_config(bot_id: str, request: BotFilterConfigRequest):
    """
    Save filter configuration for a bot.
    
    Replaces all existing filter configs for this bot.
    """
    try:
        ensure_db_path()
        
        # Convert to internal format
        config = {}
        for name, cfg in request.filters.items():
            config[name] = {
                "enabled": cfg.enabled,
                **cfg.params
            }
        
        # Create manager and load config
        from app.filters.manager import FilterManager
        manager = FilterManager(bot_id)
        manager.load_config_from_dict(config)
        
        # Save to database
        manager.save_config(DB_PATH)
        
        return {
            "success": True,
            "bot_id": bot_id,
            "filter_count": len(manager.filters),
            "message": f"Saved {len(manager.filters)} filter configurations"
        }
        
    except Exception as e:
        logger.error(f"Error saving bot filter config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bot/{bot_id}/profile/{profile_name}")
async def apply_profile_to_bot(bot_id: str, profile_name: str):
    """
    Apply a filter profile to a bot.
    """
    from app.filters.manager import FilterManager, get_filter_profiles
    
    profiles = get_filter_profiles()
    if profile_name not in profiles:
        raise HTTPException(status_code=404, detail=f"Profile not found: {profile_name}")
    
    try:
        ensure_db_path()
        
        manager = FilterManager(bot_id)
        success = manager.apply_profile(profile_name)
        
        if success:
            manager.save_config(DB_PATH)
            
            return {
                "success": True,
                "bot_id": bot_id,
                "profile": profile_name,
                "filter_count": len(manager.filters),
                "message": f"Applied profile '{profile_name}' with {len(manager.filters)} filters"
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to apply profile")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error applying profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/bot/{bot_id}/{filter_name}")
async def update_bot_filter(
    bot_id: str, 
    filter_name: str, 
    config: FilterConfigUpdate
):
    """
    Update a single filter configuration for a bot.
    """
    try:
        ensure_db_path()
        
        manager = get_manager_for_bot(bot_id)
        
        # Merge enabled flag into params
        full_config = {
            "enabled": config.enabled,
            **config.params
        }
        
        success = manager.update_filter_config(filter_name, full_config)
        
        if success:
            manager.save_config(DB_PATH)
            
            return {
                "success": True,
                "bot_id": bot_id,
                "filter_name": filter_name,
                "message": f"Updated filter '{filter_name}'"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Failed to update filter: {filter_name}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating filter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/bot/{bot_id}/{filter_name}")
async def delete_bot_filter(bot_id: str, filter_name: str):
    """
    Delete a filter configuration from a bot.
    """
    try:
        import sqlite3
        ensure_db_path()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM bot_filter_configs 
            WHERE bot_id = ? AND filter_name = ?
        """, (bot_id, filter_name))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            return {
                "success": True,
                "bot_id": bot_id,
                "filter_name": filter_name,
                "message": f"Deleted filter '{filter_name}'"
            }
        else:
            raise HTTPException(status_code=404, detail=f"Filter not found: {filter_name}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting filter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINTS - Validation
# =============================================================================

@router.post("/validate", response_model=FilterValidationResponse)
async def validate_filter_config(request: FilterValidationRequest):
    """
    Validate filter configuration without saving.
    """
    from app.filters.manager import validate_filter_config as do_validate
    
    try:
        result = do_validate(request.filter_name, request.config)
        
        return FilterValidationResponse(
            valid=result["valid"],
            errors=result["errors"],
            warnings=result["warnings"]
        )
        
    except Exception as e:
        logger.error(f"Error validating filter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINTS - Statistics and Logging
# =============================================================================

@router.get("/bot/{bot_id}/stats")
async def get_bot_filter_stats(bot_id: str):
    """
    Get filter statistics for a bot.
    
    Note: Stats are session-based and reset when server restarts.
    For persistent stats, use the decision log.
    """
    try:
        manager = get_manager_for_bot(bot_id)
        
        return manager.get_stats()
        
    except Exception as e:
        logger.error(f"Error getting filter stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/bot/{bot_id}/log")
async def get_bot_filter_log(
    bot_id: str,
    n: int = Query(default=100, ge=1, le=1000),
    symbol: Optional[str] = None,
    blocked_only: bool = False
):
    """
    Get filter decision log for a bot.
    
    Args:
        bot_id: Bot identifier
        n: Number of entries to return (1-1000, default 100)
        symbol: Filter by symbol (optional)
        blocked_only: Only return blocked decisions
    """
    try:
        manager = get_manager_for_bot(bot_id)
        
        entries = manager.get_decision_log(
            n=n,
            symbol=symbol,
            blocked_only=blocked_only
        )
        
        return {
            "bot_id": bot_id,
            "entries": entries,
            "total": len(entries),
            "filters": {
                "symbol": symbol,
                "blocked_only": blocked_only
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting filter log: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bot/{bot_id}/reset")
async def reset_bot_filter_stats(bot_id: str):
    """
    Reset filter statistics for a bot.
    """
    try:
        manager = get_manager_for_bot(bot_id)
        manager.reset_stats()
        
        return {
            "success": True,
            "bot_id": bot_id,
            "message": "Filter statistics reset"
        }
        
    except Exception as e:
        logger.error(f"Error resetting filter stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINTS - Filter Info
# =============================================================================

@router.get("/bot/{bot_id}/list")
async def list_bot_filters(bot_id: str):
    """
    Get detailed list of all configured filters for a bot.
    
    Includes status, pass rates, and block counts.
    """
    try:
        manager = get_manager_for_bot(bot_id)
        
        return {
            "bot_id": bot_id,
            "filters": manager.get_filter_list(),
            "summary": manager.get_filter_summary()
        }
        
    except Exception as e:
        logger.error(f"Error listing bot filters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bot/{bot_id}/enable/{filter_name}")
async def enable_bot_filter(bot_id: str, filter_name: str):
    """
    Enable a filter for a bot.
    """
    try:
        ensure_db_path()
        
        manager = get_manager_for_bot(bot_id)
        success = manager.enable_filter(filter_name)
        
        if success:
            manager.save_config(DB_PATH)
            return {
                "success": True,
                "bot_id": bot_id,
                "filter_name": filter_name,
                "enabled": True
            }
        else:
            raise HTTPException(status_code=404, detail=f"Filter not found: {filter_name}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling filter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bot/{bot_id}/disable/{filter_name}")
async def disable_bot_filter(bot_id: str, filter_name: str):
    """
    Disable a filter for a bot.
    """
    try:
        ensure_db_path()
        
        manager = get_manager_for_bot(bot_id)
        success = manager.disable_filter(filter_name)
        
        if success:
            manager.save_config(DB_PATH)
            return {
                "success": True,
                "bot_id": bot_id,
                "filter_name": filter_name,
                "enabled": False
            }
        else:
            raise HTTPException(status_code=404, detail=f"Filter not found: {filter_name}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling filter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# ENDPOINTS - Testing
# =============================================================================

@router.post("/test")
async def test_filter_on_signal(
    filter_name: str,
    config: Dict[str, Any],
    signal: Dict[str, Any],
    context: Dict[str, Any]
):
    """
    Test a filter configuration on a sample signal.
    
    Useful for testing filter behavior before saving configuration.
    """
    from app.filters.base import Signal, SignalContext
    from app.filters.registry import FilterRegistry, discover_filters
    from datetime import datetime
    
    discover_filters()
    
    filter_class = FilterRegistry.get(filter_name)
    if filter_class is None:
        raise HTTPException(status_code=404, detail=f"Filter not found: {filter_name}")
    
    try:
        # Create filter instance
        filter_instance = filter_class(config)
        
        # Parse signal
        test_signal = Signal(
            symbol=signal.get("symbol", "BTCUSDT"),
            direction=signal.get("direction", "long"),
            entry_price=signal.get("entry_price", 50000.0),
            timestamp=datetime.fromisoformat(signal.get("timestamp", datetime.now().isoformat())),
            timeframe=signal.get("timeframe", "1h"),
        )
        
        # Parse context
        test_context = SignalContext(
            current_time=datetime.fromisoformat(context.get("current_time", datetime.now().isoformat())),
            current_price=context.get("current_price", 50000.0),
            atr=context.get("atr"),
            volume=context.get("volume"),
            avg_volume=context.get("avg_volume"),
            open_positions=context.get("open_positions", []),
            recent_trades=context.get("recent_trades", []),
            equity_curve=context.get("equity_curve", []),
            current_equity=context.get("current_equity", 0.0),
            starting_equity=context.get("starting_equity", 0.0),
        )
        
        # Apply filter
        decision = filter_instance.should_allow(test_signal, test_context)
        
        return {
            "filter_name": filter_name,
            "result": decision.result.value,
            "reason": decision.reason,
            "details": decision.details,
            "passed": decision.is_passed
        }
        
    except Exception as e:
        logger.error(f"Error testing filter: {e}")
        raise HTTPException(status_code=500, detail=str(e))
