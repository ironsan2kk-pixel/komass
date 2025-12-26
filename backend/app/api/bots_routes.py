"""
Komas Trading Server - Bots API Routes
======================================
REST API for trading bots management
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import asyncio

from app.core.bots import (
    get_bots_manager,
    get_bots_runner,
    BotCreate,
    BotUpdate,
    BotResponse,
    BotDetailResponse,
    Bot,
    BotStatus,
    BotStatistics,
    Position,
    PositionCloseRequest,
    BotConfig,
    BotSymbolConfig,
    StrategyConfig,
    EquityCurve,
    BotLogEntry,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/bots", tags=["Bots"])


# ============ RESPONSE MODELS ============

class BotListResponse(BaseModel):
    """Response for bot list"""
    bots: List[BotResponse]
    total: int


class SummaryResponse(BaseModel):
    """Bots summary response"""
    total_bots: int
    running_bots: int
    paused_bots: int
    stopped_bots: int
    error_bots: int
    total_capital: float
    total_pnl: float
    total_open_positions: int
    total_trades: int


class RunnerStatusResponse(BaseModel):
    """Runner status response"""
    running: bool
    scheduled_jobs: int
    active_bots: int


class PositionResponse(BaseModel):
    """Position list response"""
    positions: List[Position]
    total: int


class LogsResponse(BaseModel):
    """Logs response"""
    logs: List[BotLogEntry]
    total: int


class EquityResponse(BaseModel):
    """Equity curve response"""
    bot_id: str
    points: List[Dict[str, Any]]


# ============ BOTS CRUD ============

@router.get("/", response_model=BotListResponse)
async def list_bots(
    status: Optional[BotStatus] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """List all bots with optional filtering"""
    manager = get_bots_manager()
    all_bots = manager.get_all_bots()
    
    # Filter by status
    if status:
        all_bots = [b for b in all_bots if b.status == status]
    
    # Sort by created_at descending
    all_bots = sorted(all_bots, key=lambda b: b.created_at, reverse=True)
    
    # Paginate
    total = len(all_bots)
    bots = all_bots[offset:offset + limit]
    
    return BotListResponse(
        bots=[BotResponse.from_bot(b) for b in bots],
        total=total
    )


@router.post("/", response_model=BotResponse, status_code=201)
async def create_bot(request: BotCreate):
    """Create a new trading bot"""
    manager = get_bots_manager()
    
    try:
        bot = manager.create_bot(request)
        logger.info(f"Created bot: {bot.config.name}")
        return BotResponse.from_bot(bot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary", response_model=SummaryResponse)
async def get_summary():
    """Get summary of all bots"""
    manager = get_bots_manager()
    summary = manager.get_summary()
    return SummaryResponse(**summary)


@router.get("/runner/status", response_model=RunnerStatusResponse)
async def get_runner_status():
    """Get runner status"""
    runner = get_bots_runner()
    manager = get_bots_manager()
    
    return RunnerStatusResponse(
        running=runner.is_running(),
        scheduled_jobs=len(runner._jobs),
        active_bots=len(manager.get_running_bots())
    )


@router.post("/runner/start")
async def start_runner(background_tasks: BackgroundTasks):
    """Start the bots runner"""
    runner = get_bots_runner()
    
    if runner.is_running():
        return {"status": "already_running"}
    
    runner.start()
    return {"status": "started"}


@router.post("/runner/stop")
async def stop_runner():
    """Stop the bots runner"""
    runner = get_bots_runner()
    
    if not runner.is_running():
        return {"status": "not_running"}
    
    runner.stop()
    return {"status": "stopped"}


@router.get("/{bot_id}", response_model=BotDetailResponse)
async def get_bot(bot_id: str):
    """Get bot details"""
    manager = get_bots_manager()
    bot = manager.get_bot(bot_id)
    
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    stats = bot.statistics or BotStatistics(bot_id=bot_id)
    recent = manager.get_closed_positions(bot_id, limit=20)
    
    return BotDetailResponse(
        bot=bot,
        statistics=stats,
        recent_positions=recent
    )


@router.patch("/{bot_id}", response_model=BotResponse)
async def update_bot(bot_id: str, update: BotUpdate):
    """Update bot configuration"""
    manager = get_bots_manager()
    
    try:
        bot = manager.update_bot(bot_id, update)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        return BotResponse.from_bot(bot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{bot_id}")
async def delete_bot(bot_id: str):
    """Delete a bot"""
    manager = get_bots_manager()
    
    try:
        deleted = manager.delete_bot(bot_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Bot not found")
        return {"status": "deleted", "bot_id": bot_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ BOT CONTROL ============

@router.post("/{bot_id}/start", response_model=BotResponse)
async def start_bot(bot_id: str):
    """Start a bot"""
    manager = get_bots_manager()
    
    bot = manager.start_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return BotResponse.from_bot(bot)


@router.post("/{bot_id}/stop", response_model=BotResponse)
async def stop_bot(bot_id: str):
    """Stop a bot"""
    manager = get_bots_manager()
    
    bot = manager.stop_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return BotResponse.from_bot(bot)


@router.post("/{bot_id}/pause", response_model=BotResponse)
async def pause_bot(bot_id: str):
    """Pause a bot"""
    manager = get_bots_manager()
    
    try:
        bot = manager.pause_bot(bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        return BotResponse.from_bot(bot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{bot_id}/resume", response_model=BotResponse)
async def resume_bot(bot_id: str):
    """Resume a paused bot"""
    manager = get_bots_manager()
    
    try:
        bot = manager.resume_bot(bot_id)
        if not bot:
            raise HTTPException(status_code=404, detail="Bot not found")
        return BotResponse.from_bot(bot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{bot_id}/force-check")
async def force_check_bot(bot_id: str, background_tasks: BackgroundTasks):
    """Force immediate strategy check for a bot"""
    manager = get_bots_manager()
    runner = get_bots_runner()
    
    bot = manager.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    if bot.status != BotStatus.RUNNING:
        raise HTTPException(status_code=400, detail="Bot must be running")
    
    # Run in background
    background_tasks.add_task(runner.force_check, bot_id)
    
    return {"status": "check_scheduled", "bot_id": bot_id}


# ============ POSITIONS ============

@router.get("/{bot_id}/positions/open", response_model=PositionResponse)
async def get_open_positions(bot_id: str):
    """Get open positions for a bot"""
    manager = get_bots_manager()
    
    bot = manager.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    positions = manager.get_open_positions(bot_id)
    
    return PositionResponse(
        positions=positions,
        total=len(positions)
    )


@router.get("/{bot_id}/positions/closed", response_model=PositionResponse)
async def get_closed_positions(
    bot_id: str,
    limit: int = Query(50, ge=1, le=200)
):
    """Get closed positions for a bot"""
    manager = get_bots_manager()
    
    bot = manager.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    positions = manager.get_closed_positions(bot_id, limit=limit)
    
    return PositionResponse(
        positions=positions,
        total=len(positions)
    )


@router.post("/{bot_id}/positions/close")
async def close_position(bot_id: str, request: PositionCloseRequest):
    """Manually close a position"""
    manager = get_bots_manager()
    runner = get_bots_runner()
    
    bot = manager.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Find position
    position = None
    for pos in bot.open_positions:
        if pos.id == request.position_id:
            position = pos
            break
    
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    
    # Get current price (for now use entry price, in real scenario fetch market price)
    current_price = position.current_price or position.entry_price
    
    closed = await runner.manual_close_position(
        bot_id,
        request.position_id,
        exit_price=current_price,
        partial_percent=request.partial_percent
    )
    
    if not closed:
        raise HTTPException(status_code=500, detail="Failed to close position")
    
    return {"status": "closed", "position": closed.model_dump()}


# ============ STATISTICS ============

@router.get("/{bot_id}/statistics", response_model=BotStatistics)
async def get_statistics(bot_id: str):
    """Get bot statistics"""
    manager = get_bots_manager()
    
    stats = manager.get_statistics(bot_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return stats


@router.post("/{bot_id}/statistics/recalculate")
async def recalculate_statistics(bot_id: str):
    """Recalculate bot statistics from positions"""
    manager = get_bots_manager()
    
    bot = manager.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    manager.recalculate_statistics(bot_id)
    
    return {"status": "recalculated", "statistics": manager.get_statistics(bot_id)}


# ============ EQUITY CURVE ============

@router.get("/{bot_id}/equity", response_model=EquityResponse)
async def get_equity_curve(
    bot_id: str,
    limit: int = Query(100, ge=10, le=1000)
):
    """Get bot equity curve"""
    manager = get_bots_manager()
    
    curve = manager.get_equity_curve(bot_id)
    if not curve:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    points = curve.points[-limit:] if len(curve.points) > limit else curve.points
    
    return EquityResponse(
        bot_id=bot_id,
        points=[{
            "timestamp": p.timestamp.isoformat(),
            "equity": p.equity,
            "drawdown": p.drawdown,
            "position_count": p.position_count
        } for p in points]
    )


# ============ LOGS ============

@router.get("/{bot_id}/logs", response_model=LogsResponse)
async def get_bot_logs(
    bot_id: str,
    level: Optional[str] = Query(None, description="Filter by level: info, warning, error, trade"),
    limit: int = Query(100, ge=1, le=500)
):
    """Get bot logs"""
    manager = get_bots_manager()
    
    bot = manager.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    logs = manager.get_logs(bot_id, limit=limit, level=level)
    
    return LogsResponse(
        logs=logs,
        total=len(logs)
    )


# ============ SSE STREAMING ============

async def bot_events_generator(bot_id: str):
    """Generate SSE events for a bot"""
    manager = get_bots_manager()
    
    last_updated = datetime.min
    
    while True:
        try:
            bot = manager.get_bot(bot_id)
            if not bot:
                yield f"event: error\ndata: {json.dumps({'error': 'Bot not found'})}\n\n"
                break
            
            if bot.updated_at > last_updated:
                last_updated = bot.updated_at
                
                event_data = {
                    "status": bot.status.value,
                    "current_capital": bot.current_capital,
                    "open_positions": len(bot.open_positions),
                    "last_signal_time": bot.last_signal_time.isoformat() if bot.last_signal_time else None,
                    "statistics": bot.statistics.model_dump() if bot.statistics else None,
                    "updated_at": bot.updated_at.isoformat()
                }
                
                yield f"event: update\ndata: {json.dumps(event_data)}\n\n"
            
            await asyncio.sleep(2)  # Check every 2 seconds
            
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"SSE error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
            break


@router.get("/{bot_id}/stream")
async def stream_bot_events(bot_id: str):
    """Stream bot events via SSE"""
    manager = get_bots_manager()
    
    bot = manager.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return StreamingResponse(
        bot_events_generator(bot_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============ BULK OPERATIONS ============

@router.post("/start-all")
async def start_all_bots():
    """Start all stopped bots"""
    manager = get_bots_manager()
    
    started = []
    for bot in manager.get_all_bots():
        if bot.status == BotStatus.STOPPED:
            manager.start_bot(bot.id)
            started.append(bot.id)
    
    return {"status": "started", "count": len(started), "bot_ids": started}


@router.post("/stop-all")
async def stop_all_bots():
    """Stop all running bots"""
    manager = get_bots_manager()
    
    stopped = []
    for bot in manager.get_all_bots():
        if bot.status in [BotStatus.RUNNING, BotStatus.PAUSED]:
            manager.stop_bot(bot.id)
            stopped.append(bot.id)
    
    return {"status": "stopped", "count": len(stopped), "bot_ids": stopped}


# ============ PRESETS ============

class StrategyPreset(BaseModel):
    """Strategy preset"""
    name: str
    description: str
    strategy: StrategyConfig


STRATEGY_PRESETS = [
    StrategyPreset(
        name="Conservative",
        description="Low risk, high TP accuracy",
        strategy=StrategyConfig(
            atr_length=60,
            multiplier=5.0,
            tp_count=2,
            sl_percent=1.5,
            sl_mode="fixed",
            use_rsi=True,
            use_adx=True
        )
    ),
    StrategyPreset(
        name="Balanced",
        description="Balanced risk/reward",
        strategy=StrategyConfig(
            atr_length=45,
            multiplier=4.0,
            tp_count=4,
            sl_percent=2.0,
            sl_mode="breakeven",
            use_supertrend=True
        )
    ),
    StrategyPreset(
        name="Aggressive",
        description="High risk, high reward",
        strategy=StrategyConfig(
            atr_length=30,
            multiplier=3.0,
            tp_count=6,
            sl_percent=3.0,
            sl_mode="cascade",
            use_volume=True
        )
    ),
    StrategyPreset(
        name="Scalper",
        description="Quick trades, small profits",
        strategy=StrategyConfig(
            atr_length=20,
            multiplier=2.5,
            tp_count=2,
            sl_percent=1.0,
            sl_mode="fixed",
            use_rsi=True,
            rsi_overbought=65,
            rsi_oversold=35
        )
    ),
]


@router.get("/presets/strategies")
async def get_strategy_presets():
    """Get available strategy presets"""
    return {
        "presets": [p.model_dump() for p in STRATEGY_PRESETS]
    }


# ============ DUPLICATE BOT ============

@router.post("/{bot_id}/duplicate", response_model=BotResponse)
async def duplicate_bot(bot_id: str, new_name: str = Query(..., min_length=1)):
    """Duplicate an existing bot with a new name"""
    manager = get_bots_manager()
    
    bot = manager.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    # Create new config with new name
    new_config = bot.config.model_copy(deep=True)
    new_config.name = new_name
    
    try:
        new_bot = manager.create_bot(BotCreate(config=new_config))
        return BotResponse.from_bot(new_bot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============ EXPORT/IMPORT ============

@router.get("/{bot_id}/export")
async def export_bot_config(bot_id: str):
    """Export bot configuration as JSON"""
    manager = get_bots_manager()
    
    bot = manager.get_bot(bot_id)
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    export_data = {
        "config": bot.config.model_dump(),
        "exported_at": datetime.now().isoformat(),
        "version": "1.0"
    }
    
    return export_data


class ImportBotRequest(BaseModel):
    """Import bot request"""
    config: BotConfig
    name_override: Optional[str] = None


@router.post("/import", response_model=BotResponse)
async def import_bot_config(request: ImportBotRequest):
    """Import bot from exported configuration"""
    manager = get_bots_manager()
    
    config = request.config
    if request.name_override:
        config.name = request.name_override
    
    try:
        bot = manager.create_bot(BotCreate(config=config))
        return BotResponse.from_bot(bot)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
