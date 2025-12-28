"""
KOMAS Trading Server - Preset Optimizer API Routes
===================================================
REST API and SSE endpoints for preset optimization.

Endpoints:
- POST   /api/optimizer/presets/run         - Start optimization
- POST   /api/optimizer/presets/stream      - SSE progress stream
- GET    /api/optimizer/presets/results     - Get results by run_id
- POST   /api/optimizer/presets/cancel      - Cancel running optimization
- GET    /api/optimizer/presets/active      - List active optimizations
- GET    /api/optimizer/presets/status/{id} - Get status of specific run

Mode endpoints (Chat #46):
- GET    /api/optimizer/modes               - List all optimization modes
- GET    /api/optimizer/modes/{mode}        - Get mode configuration
- POST   /api/optimizer/estimate            - Estimate optimization time
- GET    /api/optimizer/liquidity           - Get pair liquidity ranking

Results endpoints (NEW in Chat #47):
- GET    /api/optimizer/history             - List optimization history
- DELETE /api/optimizer/results/{run_id}    - Delete specific run
- GET    /api/optimizer/results/{run_id}/scores - Get preset scores with pagination
- GET    /api/optimizer/results/{run_id}/export/csv - Export as CSV
- GET    /api/optimizer/results/{run_id}/export/json - Export as JSON
- GET    /api/optimizer/aggregation/preset/{preset_id} - Aggregate by preset
- GET    /api/optimizer/aggregation/pair    - Aggregate by pair

Chat #45: Preset Optimizer Core
Chat #46: Preset Optimizer Modes
Chat #47: Preset Optimizer Results
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, List
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/optimizer", tags=["optimizer"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class OptimizationRequest(BaseModel):
    """Request to start preset optimization"""
    preset_ids: List[str] = Field(..., description="List of preset IDs to optimize")
    pairs: List[str] = Field(..., description="List of trading pairs")
    timeframe: str = Field(default="1h", description="Timeframe for backtest")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    mode: str = Field(default="standard", description="Optimization mode: quick/standard/smart/full")


class OptimizationStartResponse(BaseModel):
    """Response when optimization starts"""
    run_id: str
    status: str
    mode: str
    total_combinations: int
    effective_presets: int
    effective_pairs: int
    workers: int
    estimated_seconds: float
    estimated_time: str
    message: str


class OptimizationStatusResponse(BaseModel):
    """Response for optimization status"""
    run_id: str
    status: str
    mode: str
    progress: float
    completed: int
    total: int
    estimated_seconds: float


class PresetScoreResponse(BaseModel):
    """Response for a single preset's aggregate score"""
    preset_id: str
    preset_name: str
    indicator_type: str
    rank: int
    overall_score: float
    grade: str
    profitability_score: float
    stability_score: float
    universality_score: float
    avg_pnl: float
    avg_win_rate: float
    avg_sharpe: float
    avg_max_dd: float
    positive_pairs: int
    total_pairs: int
    positive_ratio: float
    best_pair: str
    best_pnl: float
    worst_pair: str
    worst_pnl: float


class OptimizationHistoryRequest(BaseModel):
    """Request for optimization history"""
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    mode: Optional[str] = None
    status: Optional[str] = None
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class PresetScoresRequest(BaseModel):
    """Request for preset scores with filters"""
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="overall_score")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")
    min_score: Optional[float] = Field(None, ge=0, le=100)
    indicator_type: Optional[str] = None
    search: Optional[str] = None


class TimeEstimateRequest(BaseModel):
    """Request for time estimation"""
    preset_count: int = Field(..., ge=1, description="Number of presets")
    pair_count: int = Field(..., ge=1, description="Number of pairs")
    mode: str = Field(default="standard", description="Optimization mode")


class TimeEstimateResponse(BaseModel):
    """Response for time estimation"""
    mode: str
    total_combinations: int
    effective_presets: int
    effective_pairs: int
    num_workers: int
    estimated_seconds: float
    estimated_minutes: float
    human_readable: str
    description: str


class ModeInfoResponse(BaseModel):
    """Response for mode information"""
    mode: str
    name: str
    description: str
    max_presets: Optional[int]
    max_pairs: Optional[int]
    preset_selection: str
    pair_selection: str
    use_clustering: bool


# ============================================================================
# OPTIMIZATION RESULTS STORAGE (hybrid: in-memory + SQLite)
# ============================================================================

# In-memory cache for active/recent results
_completed_results = {}
MAX_MEMORY_RESULTS = 20


def store_result(run_id: str, result: dict):
    """Store completed optimization result (memory + SQLite)"""
    global _completed_results
    
    # Store in memory cache
    _completed_results[run_id] = result
    
    # Keep only last N in memory
    if len(_completed_results) > MAX_MEMORY_RESULTS:
        oldest_key = next(iter(_completed_results))
        del _completed_results[oldest_key]
    
    # Persist to SQLite
    try:
        from app.db.optimizer_db import OptimizationResultsManager
        OptimizationResultsManager.save_run(result)
    except Exception as e:
        logger.error(f"Failed to persist result to SQLite: {e}")


def get_stored_result(run_id: str) -> Optional[dict]:
    """Get stored optimization result (memory first, then SQLite)"""
    # Check memory cache first
    if run_id in _completed_results:
        return _completed_results[run_id]
    
    # Try SQLite
    try:
        from app.db.optimizer_db import OptimizationResultsManager
        detail = OptimizationResultsManager.get_run(run_id)
        if detail:
            return asdict(detail)
    except Exception as e:
        logger.error(f"Failed to get result from SQLite: {e}")
    
    return None


def calculate_grade(score: float) -> str:
    """Calculate letter grade from score (0-100)"""
    if score >= 85:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 55:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F"


# ============================================================================
# SSE STREAMING
# ============================================================================

async def optimization_stream_generator(
    preset_ids: List[str],
    pairs: List[str],
    timeframe: str,
    start_date: Optional[str],
    end_date: Optional[str],
    mode: str
):
    """
    SSE generator for optimization progress.
    Yields events as they occur during optimization.
    """
    from app.services.preset_optimizer import get_preset_optimizer
    
    optimizer = get_preset_optimizer()
    
    # Queue for progress updates
    progress_queue = asyncio.Queue()
    
    async def progress_callback(event: dict):
        """Callback to push progress updates to queue"""
        await progress_queue.put(event)
    
    # Start optimization in background
    optimization_task = asyncio.create_task(
        optimizer.run_optimization(
            preset_ids=preset_ids,
            pairs=pairs,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            mode=mode,
            progress_callback=progress_callback
        )
    )
    
    try:
        # Stream progress updates
        while True:
            try:
                # Wait for progress update with timeout
                event = await asyncio.wait_for(progress_queue.get(), timeout=30.0)
                
                yield f"data: {json.dumps(event)}\n\n"
                
                # Check if complete
                if event.get('type') in ['complete', 'error', 'cancelled']:
                    break
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"
        
        # Get final result
        result = await optimization_task
        
        # Store result for later retrieval
        result_dict = {
            'run_id': result.run_id,
            'status': result.status.value,
            'mode': result.mode,
            'timeframe': result.timeframe,
            'start_date': result.start_date,
            'end_date': result.end_date,
            'started_at': result.started_at,
            'completed_at': result.completed_at,
            'duration_seconds': result.duration_seconds,
            'total_combinations': result.total_combinations,
            'completed_combinations': result.completed_combinations,
            'original_preset_count': result.original_preset_count,
            'original_pair_count': result.original_pair_count,
            'effective_preset_count': result.effective_preset_count,
            'effective_pair_count': result.effective_pair_count,
            'preset_ids': result.preset_ids,
            'pairs': result.pairs,
            'num_workers': result.num_workers,
            'top_10_presets': result.top_10_presets,
            'result_matrix': result.result_matrix,
            'preset_scores': [asdict(s) for s in result.preset_scores],
            'errors': result.errors
        }
        store_result(result.run_id, result_dict)
        
        # Send final result
        yield f"data: {json.dumps({'type': 'result', 'data': result_dict})}\n\n"
        
    except asyncio.CancelledError:
        optimization_task.cancel()
        yield f"data: {json.dumps({'type': 'cancelled'})}\n\n"
    except Exception as e:
        logger.error(f"Optimization stream error: {e}")
        yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"


# ============================================================================
# MODE ENDPOINTS (Chat #46)
# ============================================================================

@router.get("/modes")
async def list_optimization_modes():
    """
    List all available optimization modes with their configurations.
    """
    from app.services.optimization_modes import get_all_modes_info
    
    modes = get_all_modes_info()
    return {
        "modes": modes,
        "default": "standard",
        "recommended_for_quick_test": "quick",
        "recommended_for_production": "full"
    }


@router.get("/modes/{mode}")
async def get_mode_info(mode: str):
    """
    Get detailed information about a specific optimization mode.
    """
    from app.services.optimization_modes import get_mode_info, OptimizationMode
    
    try:
        info = get_mode_info(mode)
        return info
    except ValueError:
        valid_modes = [m.value for m in OptimizationMode]
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid mode: {mode}. Valid modes: {valid_modes}"
        )


@router.post("/estimate")
async def estimate_optimization_time(request: TimeEstimateRequest):
    """
    Estimate optimization time based on preset count, pair count, and mode.
    """
    from app.services.optimization_modes import estimate_optimization_time, get_mode_config
    
    try:
        config = get_mode_config(request.mode)
        estimate = estimate_optimization_time(
            request.preset_count,
            request.pair_count,
            request.mode
        )
        
        return {
            "mode": request.mode,
            "mode_name": config.name,
            "total_combinations": estimate["total_combinations"],
            "effective_presets": estimate["effective_presets"],
            "effective_pairs": estimate["effective_pairs"],
            "num_workers": estimate["num_workers"],
            "estimated_seconds": estimate["estimated_seconds"],
            "estimated_minutes": estimate["estimated_seconds"] / 60,
            "human_readable": estimate["human_readable"],
            "description": config.description
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/liquidity")
async def get_liquidity_ranking(pairs: Optional[str] = Query(None)):
    """
    Get liquidity ranking for trading pairs.
    """
    from app.services.optimization_modes import get_liquidity_ranking
    
    pair_list = pairs.split(",") if pairs else None
    ranking = get_liquidity_ranking(pair_list)
    
    return {
        "ranking": ranking,
        "total": len(ranking)
    }


@router.get("/correlation-groups")
async def get_correlation_groups():
    """
    Get correlation groups for trading pairs.
    """
    from app.services.optimization_modes import CORRELATION_GROUPS
    
    return {
        "groups": CORRELATION_GROUPS,
        "total_groups": len(CORRELATION_GROUPS)
    }


# ============================================================================
# HISTORY ENDPOINTS (NEW in Chat #47)
# ============================================================================

@router.get("/history")
async def get_optimization_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    mode: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$")
):
    """
    Get optimization run history with filtering and pagination.
    
    Query params:
    - limit: Max results (1-100)
    - offset: Skip first N results
    - mode: Filter by mode (quick/standard/smart/full)
    - status: Filter by status (completed/error/cancelled)
    - sort_by: Sort field (created_at, duration_seconds, best_overall_score)
    - sort_order: asc or desc
    """
    from app.db.optimizer_db import OptimizationResultsManager
    
    try:
        runs = OptimizationResultsManager.list_runs(
            limit=limit,
            offset=offset,
            mode=mode,
            status=status,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        total = OptimizationResultsManager.count_runs(mode=mode, status=status)
        
        return {
            "runs": [asdict(r) for r in runs],
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_more": offset + len(runs) < total
        }
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/results/{run_id}")
async def delete_optimization_result(run_id: str):
    """
    Delete a specific optimization result.
    """
    from app.db.optimizer_db import OptimizationResultsManager
    
    # Remove from memory cache
    if run_id in _completed_results:
        del _completed_results[run_id]
    
    # Remove from SQLite
    success = OptimizationResultsManager.delete_run(run_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    return {"success": True, "deleted": run_id}


@router.delete("/history/clear")
async def clear_optimization_history(keep_count: int = Query(default=0, ge=0)):
    """
    Clear optimization history.
    
    Query params:
    - keep_count: Number of recent runs to keep (0 = delete all)
    """
    from app.db.optimizer_db import OptimizationResultsManager
    
    if keep_count == 0:
        deleted = OptimizationResultsManager.clear_all()
    else:
        deleted = OptimizationResultsManager.delete_old_runs(keep_count=keep_count)
    
    # Clear memory cache
    global _completed_results
    _completed_results = {}
    
    return {"success": True, "deleted_count": deleted}


# ============================================================================
# RESULTS ENDPOINTS (Enhanced in Chat #47)
# ============================================================================

@router.get("/results/{run_id}")
async def get_optimization_result(run_id: str):
    """
    Get full optimization result by run ID.
    """
    result = get_stored_result(run_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Result {run_id} not found")
    
    return result


@router.get("/results/{run_id}/scores")
async def get_preset_scores(
    run_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    sort_by: str = Query(default="overall_score"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    min_score: Optional[float] = Query(default=None, ge=0, le=100),
    indicator_type: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None)
):
    """
    Get preset scores for a run with filtering, sorting, and pagination.
    
    Query params:
    - limit: Max results
    - offset: Skip first N
    - sort_by: Field to sort by (overall_score, avg_pnl, avg_win_rate, avg_sharpe, etc.)
    - sort_order: asc or desc
    - min_score: Minimum overall score filter
    - indicator_type: Filter by indicator (trg/dominant)
    - search: Search in preset name/id
    """
    from app.db.optimizer_db import OptimizationResultsManager
    
    try:
        result = OptimizationResultsManager.get_preset_scores(
            run_id=run_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
            min_score=min_score,
            indicator_type=indicator_type,
            search=search
        )
        
        # Add grades to scores
        for score in result["scores"]:
            score["grade"] = calculate_grade(score.get("overall_score", 0))
        
        return result
    except Exception as e:
        logger.error(f"Failed to get preset scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results/{run_id}/export/csv")
async def export_results_csv(run_id: str):
    """
    Export optimization results as CSV.
    """
    from app.db.optimizer_db import OptimizationResultsManager
    
    csv_content = OptimizationResultsManager.export_to_csv(run_id)
    
    if not csv_content:
        raise HTTPException(status_code=404, detail=f"Results for {run_id} not found")
    
    return PlainTextResponse(
        content=csv_content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=optimization_{run_id}.csv"
        }
    )


@router.get("/results/{run_id}/export/json")
async def export_results_json(run_id: str):
    """
    Export full optimization results as JSON file.
    """
    from app.db.optimizer_db import OptimizationResultsManager
    
    json_data = OptimizationResultsManager.export_to_json(run_id)
    
    if not json_data:
        raise HTTPException(status_code=404, detail=f"Results for {run_id} not found")
    
    return {
        "export_time": datetime.now().isoformat(),
        "run_id": run_id,
        "data": json_data
    }


# ============================================================================
# AGGREGATION ENDPOINTS (NEW in Chat #47)
# ============================================================================

@router.get("/aggregation/preset/{preset_id}")
async def get_preset_aggregation(
    preset_id: str,
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    Get aggregated results for a specific preset across multiple optimization runs.
    
    Shows how a preset performed in different runs/conditions.
    """
    from app.db.optimizer_db import OptimizationResultsManager
    
    results = OptimizationResultsManager.get_aggregated_by_preset(preset_id, limit=limit)
    
    if not results:
        return {
            "preset_id": preset_id,
            "runs": [],
            "message": "No optimization results found for this preset"
        }
    
    # Calculate averages across runs
    avg_pnl = sum(r["score"].get("avg_pnl", 0) for r in results) / len(results)
    avg_score = sum(r["score"].get("overall_score", 0) for r in results) / len(results)
    
    return {
        "preset_id": preset_id,
        "runs_count": len(results),
        "avg_pnl_across_runs": avg_pnl,
        "avg_score_across_runs": avg_score,
        "runs": results
    }


@router.get("/aggregation/pair")
async def get_pair_aggregation(
    run_id: str = Query(..., description="Run ID"),
    pair: str = Query(..., description="Trading pair (e.g., BTCUSDT)")
):
    """
    Get all preset results for a specific pair in a run.
    
    Shows how all presets performed on a specific trading pair.
    """
    from app.db.optimizer_db import OptimizationResultsManager
    
    results = OptimizationResultsManager.get_aggregated_by_pair(pair, run_id)
    
    if not results:
        return {
            "run_id": run_id,
            "pair": pair,
            "presets": [],
            "message": "No results found for this pair"
        }
    
    return {
        "run_id": run_id,
        "pair": pair,
        "preset_count": len(results),
        "presets": results
    }


# ============================================================================
# EXISTING ENDPOINTS (from Chat #45-46)
# ============================================================================

@router.post("/presets/run")
async def start_optimization(request: OptimizationRequest, background_tasks: BackgroundTasks):
    """
    Start preset optimization (non-streaming).
    Returns immediately with run_id, use /status endpoint to check progress.
    """
    from app.services.preset_optimizer import get_preset_optimizer
    from app.services.optimization_modes import get_mode_config, estimate_optimization_time
    
    optimizer = get_preset_optimizer()
    config = get_mode_config(request.mode)
    
    # Calculate effective counts
    estimate = estimate_optimization_time(
        len(request.preset_ids),
        len(request.pairs),
        request.mode
    )
    
    return {
        "run_id": f"pending_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "status": "use_streaming",
        "mode": request.mode,
        "total_combinations": estimate["total_combinations"],
        "effective_presets": estimate["effective_presets"],
        "effective_pairs": estimate["effective_pairs"],
        "workers": estimate["num_workers"],
        "estimated_seconds": estimate["estimated_seconds"],
        "estimated_time": estimate["human_readable"],
        "message": "Use /presets/stream endpoint for actual optimization with progress updates"
    }


@router.post("/presets/stream")
async def stream_optimization(request: OptimizationRequest):
    """
    Start preset optimization with SSE streaming.
    Returns a stream of progress events.
    """
    return StreamingResponse(
        optimization_stream_generator(
            preset_ids=request.preset_ids,
            pairs=request.pairs,
            timeframe=request.timeframe,
            start_date=request.start_date,
            end_date=request.end_date,
            mode=request.mode
        ),
        media_type="text/event-stream"
    )


@router.post("/presets/cancel/{run_id}")
async def cancel_optimization(run_id: str):
    """
    Cancel a running optimization.
    """
    from app.services.preset_optimizer import get_preset_optimizer
    
    optimizer = get_preset_optimizer()
    success = optimizer.cancel_run(run_id)
    
    if success:
        return {"success": True, "run_id": run_id, "message": "Optimization cancelled"}
    
    raise HTTPException(status_code=404, detail=f"Run {run_id} not found or already completed")


@router.get("/presets/active")
async def list_active_optimizations():
    """
    List currently running optimizations.
    """
    from app.services.preset_optimizer import get_preset_optimizer
    
    optimizer = get_preset_optimizer()
    active = optimizer.get_active_runs()
    
    return {
        "active_runs": active,
        "count": len(active)
    }


@router.get("/presets/status/{run_id}")
async def get_optimization_status(run_id: str):
    """
    Get status of a specific optimization run.
    """
    from app.services.preset_optimizer import get_preset_optimizer
    
    optimizer = get_preset_optimizer()
    status = optimizer.get_run_status(run_id)
    
    if status:
        return status
    
    # Check stored results
    result = get_stored_result(run_id)
    if result:
        return {
            "run_id": run_id,
            "status": result.get("status", "completed"),
            "mode": result.get("mode", "standard"),
            "progress": 100.0,
            "completed": result.get("completed_combinations", 0),
            "total": result.get("total_combinations", 0)
        }
    
    raise HTTPException(status_code=404, detail=f"Run {run_id} not found")


@router.get("/presets/matrix/{run_id}")
async def get_result_matrix(run_id: str):
    """
    Get the result matrix for a completed optimization.
    Matrix format: preset_id -> symbol -> metrics
    """
    result = get_stored_result(run_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Results for {run_id} not found")
    
    matrix = result.get("result_matrix", {})
    
    return {
        "run_id": run_id,
        "mode": result.get("mode", "standard"),
        "matrix": matrix,
        "presets_count": len(matrix),
        "pairs_count": len(matrix.get(next(iter(matrix), ""), {})) if matrix else 0
    }


@router.get("/presets/top/{run_id}")
async def get_top_presets(
    run_id: str,
    limit: int = Query(default=10, ge=1, le=50)
):
    """
    Get top performing presets from a completed optimization.
    """
    result = get_stored_result(run_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Results for {run_id} not found")
    
    preset_scores = result.get("preset_scores", [])
    
    # Sort by overall score and get top N
    sorted_scores = sorted(
        preset_scores, 
        key=lambda x: x.get("overall_score", 0), 
        reverse=True
    )[:limit]
    
    # Add grades
    for score in sorted_scores:
        score["grade"] = calculate_grade(score.get("overall_score", 0))
    
    return {
        "run_id": run_id,
        "mode": result.get("mode", "standard"),
        "total_presets": len(preset_scores),
        "top_presets": sorted_scores
    }


@router.get("/presets/comparison")
async def compare_presets(
    run_id: str,
    preset_ids: str = Query(..., description="Comma-separated preset IDs to compare")
):
    """
    Compare specific presets from a completed optimization.
    """
    result = get_stored_result(run_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Results for {run_id} not found")
    
    # Parse preset IDs
    ids_to_compare = [id.strip() for id in preset_ids.split(",")]
    
    preset_scores = result.get("preset_scores", [])
    
    # Filter to requested presets
    comparison = []
    for score in preset_scores:
        if score.get("preset_id") in ids_to_compare:
            score["grade"] = calculate_grade(score.get("overall_score", 0))
            comparison.append(score)
    
    # Sort by overall score
    comparison.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
    
    return {
        "run_id": run_id,
        "mode": result.get("mode", "standard"),
        "requested": ids_to_compare,
        "found": len(comparison),
        "presets": comparison
    }


@router.get("/presets/export/{run_id}")
async def export_optimization_results(run_id: str):
    """
    Export full optimization results as JSON.
    Suitable for downloading or external analysis.
    """
    result = get_stored_result(run_id)
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Results for {run_id} not found")
    
    return {
        "export_time": datetime.now().isoformat(),
        "run_id": run_id,
        "mode": result.get("mode", "standard"),
        "data": result
    }


# ============================================================================
# QUICK OPTIMIZATION (without SSE)
# ============================================================================

@router.post("/presets/quick")
async def quick_optimization(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks
):
    """
    Run quick optimization and return results directly.
    
    For small optimizations (< 50 combinations).
    For larger optimizations, use /stream endpoint.
    
    Note: Mode is forced to 'quick' regardless of request.
    """
    from app.services.preset_optimizer import get_preset_optimizer
    from app.services.optimization_modes import get_mode_config
    
    # Force quick mode
    mode = "quick"
    mode_config = get_mode_config(mode)
    
    # Calculate effective combinations
    effective_presets = min(len(request.preset_ids), mode_config.max_presets or 20)
    effective_pairs = min(len(request.pairs), mode_config.max_pairs or 5)
    total_combinations = effective_presets * effective_pairs
    
    if total_combinations > 200:
        raise HTTPException(
            status_code=400, 
            detail=f"Too many combinations ({total_combinations}). Use /stream for optimizations > 200 combinations."
        )
    
    optimizer = get_preset_optimizer()
    
    try:
        result = await optimizer.run_optimization(
            preset_ids=request.preset_ids,
            pairs=request.pairs,
            timeframe=request.timeframe,
            start_date=request.start_date,
            end_date=request.end_date,
            mode=mode
        )
        
        # Store result
        result_dict = {
            'run_id': result.run_id,
            'status': result.status.value,
            'mode': result.mode,
            'timeframe': result.timeframe,
            'start_date': result.start_date,
            'end_date': result.end_date,
            'started_at': result.started_at,
            'completed_at': result.completed_at,
            'duration_seconds': result.duration_seconds,
            'total_combinations': result.total_combinations,
            'completed_combinations': result.completed_combinations,
            'original_preset_count': result.original_preset_count,
            'original_pair_count': result.original_pair_count,
            'effective_preset_count': result.effective_preset_count,
            'effective_pair_count': result.effective_pair_count,
            'preset_ids': result.preset_ids,
            'pairs': result.pairs,
            'num_workers': result.num_workers,
            'top_10_presets': result.top_10_presets,
            'result_matrix': result.result_matrix,
            'preset_scores': [asdict(s) for s in result.preset_scores],
            'errors': result.errors
        }
        store_result(result.run_id, result_dict)
        
        return result_dict
        
    except Exception as e:
        logger.error(f"Quick optimization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
