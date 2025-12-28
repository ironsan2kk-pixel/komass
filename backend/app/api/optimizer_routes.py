"""
KOMAS Trading Server - Preset Optimizer API Routes
===================================================
REST API and SSE endpoints for preset optimization.

Endpoints:
- POST   /api/optimizer/presets/run         - Start optimization
- GET    /api/optimizer/presets/stream      - SSE progress stream
- GET    /api/optimizer/presets/results     - Get results by run_id
- POST   /api/optimizer/presets/cancel      - Cancel running optimization
- GET    /api/optimizer/presets/active      - List active optimizations
- GET    /api/optimizer/presets/status/{id} - Get status of specific run

Chat #45: Preset Optimizer Core
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional, List
from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
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


class OptimizationStartResponse(BaseModel):
    """Response when optimization starts"""
    run_id: str
    status: str
    total_combinations: int
    workers: int
    message: str


class OptimizationStatusResponse(BaseModel):
    """Response for optimization status"""
    run_id: str
    status: str
    progress: float
    completed: int
    total: int


class PresetScoreResponse(BaseModel):
    """Response for a single preset's aggregate score"""
    preset_id: str
    preset_name: str
    indicator_type: str
    rank: int
    overall_score: float
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


class OptimizationResultResponse(BaseModel):
    """Full optimization result response"""
    run_id: str
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_seconds: float
    total_combinations: int
    completed_combinations: int
    num_workers: int
    top_10_presets: List[dict]
    result_matrix: dict
    errors: List[str]


# ============================================================================
# OPTIMIZATION RESULTS STORAGE
# ============================================================================

# In-memory storage for completed results
_completed_results = {}
MAX_STORED_RESULTS = 50


def store_result(run_id: str, result: dict):
    """Store completed optimization result"""
    global _completed_results
    _completed_results[run_id] = result
    
    # Keep only last N results
    if len(_completed_results) > MAX_STORED_RESULTS:
        oldest_key = next(iter(_completed_results))
        del _completed_results[oldest_key]


def get_stored_result(run_id: str) -> Optional[dict]:
    """Get stored optimization result"""
    return _completed_results.get(run_id)


# ============================================================================
# SSE STREAMING
# ============================================================================

async def optimization_stream_generator(
    preset_ids: List[str],
    pairs: List[str],
    timeframe: str,
    start_date: Optional[str],
    end_date: Optional[str]
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
            'started_at': result.started_at,
            'completed_at': result.completed_at,
            'duration_seconds': result.duration_seconds,
            'total_combinations': result.total_combinations,
            'completed_combinations': result.completed_combinations,
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
# API ENDPOINTS
# ============================================================================

@router.post("/presets/run", response_model=OptimizationStartResponse)
async def start_preset_optimization(request: OptimizationRequest):
    """
    Start preset optimization.
    
    Returns immediately with run_id for tracking.
    Use /stream endpoint for real-time progress.
    """
    from app.services.preset_optimizer import get_preset_optimizer
    
    try:
        optimizer = get_preset_optimizer()
        
        # Validate inputs
        if not request.preset_ids:
            raise HTTPException(status_code=400, detail="No presets specified")
        if not request.pairs:
            raise HTTPException(status_code=400, detail="No pairs specified")
        
        # Generate run ID
        run_id = optimizer.generate_run_id()
        
        # Calculate total combinations
        total = len(request.preset_ids) * len(request.pairs)
        
        return OptimizationStartResponse(
            run_id=run_id,
            status="pending",
            total_combinations=total,
            workers=optimizer.num_workers,
            message=f"Optimization ready. Use /stream endpoint with run_id={run_id}"
        )
        
    except Exception as e:
        logger.error(f"Error starting optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/presets/stream")
async def stream_preset_optimization(request: OptimizationRequest):
    """
    Start optimization and stream progress via SSE.
    
    Returns Server-Sent Events stream with:
    - start: Initial configuration
    - progress: Progress updates (every 5 completions)
    - heartbeat: Keep-alive (every 30s)
    - complete: Final summary
    - result: Full result data
    """
    return StreamingResponse(
        optimization_stream_generator(
            preset_ids=request.preset_ids,
            pairs=request.pairs,
            timeframe=request.timeframe,
            start_date=request.start_date,
            end_date=request.end_date
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/presets/results/{run_id}")
async def get_optimization_results(run_id: str):
    """
    Get results of a completed optimization by run_id.
    """
    result = get_stored_result(run_id)
    
    if not result:
        raise HTTPException(
            status_code=404, 
            detail=f"Results for run_id {run_id} not found. May have expired or still running."
        )
    
    return result


@router.post("/presets/cancel/{run_id}")
async def cancel_optimization(run_id: str):
    """
    Cancel a running optimization.
    """
    from app.services.preset_optimizer import get_preset_optimizer
    
    optimizer = get_preset_optimizer()
    cancelled = optimizer.cancel_optimization(run_id)
    
    if cancelled:
        return {"success": True, "message": f"Optimization {run_id} cancelled"}
    else:
        return {"success": False, "message": f"Optimization {run_id} not found or already completed"}


@router.get("/presets/active")
async def list_active_optimizations():
    """
    List all currently running optimizations.
    """
    from app.services.preset_optimizer import get_preset_optimizer
    
    optimizer = get_preset_optimizer()
    active_runs = optimizer.get_active_runs()
    
    statuses = []
    for run_id in active_runs:
        status = optimizer.get_run_status(run_id)
        if status:
            statuses.append(status)
    
    return {
        "active_count": len(statuses),
        "runs": statuses
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
    
    return {
        "run_id": run_id,
        "matrix": result.get("result_matrix", {}),
        "presets_count": len(result.get("result_matrix", {})),
        "pairs_count": len(result.get("result_matrix", {}).get(next(iter(result.get("result_matrix", {})), ""), {}))
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
    
    return {
        "run_id": run_id,
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
            comparison.append(score)
    
    # Sort by overall score
    comparison.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
    
    return {
        "run_id": run_id,
        "compared_presets": len(comparison),
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
    """
    from app.services.preset_optimizer import get_preset_optimizer
    
    total_combinations = len(request.preset_ids) * len(request.pairs)
    
    if total_combinations > 100:
        raise HTTPException(
            status_code=400, 
            detail=f"Too many combinations ({total_combinations}). Use /stream for optimizations > 100 combinations."
        )
    
    optimizer = get_preset_optimizer()
    
    try:
        result = await optimizer.run_optimization(
            preset_ids=request.preset_ids,
            pairs=request.pairs,
            timeframe=request.timeframe,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Store result
        result_dict = {
            'run_id': result.run_id,
            'status': result.status.value,
            'started_at': result.started_at,
            'completed_at': result.completed_at,
            'duration_seconds': result.duration_seconds,
            'total_combinations': result.total_combinations,
            'completed_combinations': result.completed_combinations,
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
