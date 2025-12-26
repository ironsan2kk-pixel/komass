"""
Komas Trading Server - Notifications API Routes
================================================
REST API endpoints for Telegram notifications
"""
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from app.core.notifications import (
    TelegramSettings,
    SignalData,
    TPHitData,
    SLHitData,
    SignalClosedData,
    NotificationFormat,
    NotificationStats,
    TelegramBotInfo,
    get_notifier
)


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/notifications", tags=["notifications"])


# ============ REQUEST/RESPONSE MODELS ============

class SettingsResponse(BaseModel):
    """Response with telegram settings"""
    success: bool = True
    settings: TelegramSettings


class TestNotificationRequest(BaseModel):
    """Request to test notification"""
    bot_token: Optional[str] = None
    chat_id: Optional[str] = None


class TestNotificationResponse(BaseModel):
    """Response from test notification"""
    success: bool
    message: str
    message_id: Optional[int] = None
    bot_info: Optional[Dict[str, Any]] = None


class BotValidationResponse(BaseModel):
    """Response from bot validation"""
    valid: bool
    bot_info: Optional[TelegramBotInfo] = None
    error: Optional[str] = None


class StatsResponse(BaseModel):
    """Response with notification stats"""
    success: bool = True
    stats: NotificationStats


class SendSignalRequest(BaseModel):
    """Request to send signal notification"""
    symbol: str
    direction: str
    entry_price: float
    entry_zone_low: Optional[float] = None
    entry_zone_high: Optional[float] = None
    tp_targets: list[float] = []
    tp_amounts: list[float] = []
    sl_price: float
    sl_percent: Optional[float] = None
    sl_mode: str = "fixed"
    leverage: int = 1
    timeframe: str = "1h"
    exchange: str = "binance"
    indicator_name: str = "TRG"


class SendTPHitRequest(BaseModel):
    """Request to send TP hit notification"""
    signal_id: int
    symbol: str
    direction: str
    tp_level: int
    tp_price: float
    entry_price: float
    profit_percent: float
    amount_closed: float
    remaining_position: float


class SendSLHitRequest(BaseModel):
    """Request to send SL hit notification"""
    signal_id: int
    symbol: str
    direction: str
    sl_price: float
    entry_price: float
    loss_percent: float
    sl_mode: str = "fixed"


class SendClosedRequest(BaseModel):
    """Request to send signal closed notification"""
    signal_id: int
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    pnl_percent: float
    pnl_usd: Optional[float] = None
    duration_hours: Optional[float] = None
    close_reason: str
    tp_hits: list[int] = []


class NotificationResultResponse(BaseModel):
    """Response from sending notification"""
    success: bool
    message_id: Optional[int] = None
    error: Optional[str] = None


# ============ SETTINGS ENDPOINTS ============

@router.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """Get current Telegram notification settings"""
    notifier = get_notifier()
    settings = notifier.get_settings()
    
    # Mask bot token for security
    masked_settings = settings.model_copy()
    if masked_settings.bot_token:
        token = masked_settings.bot_token
        if len(token) > 10:
            masked_settings.bot_token = token[:5] + "..." + token[-5:]
    
    return SettingsResponse(settings=masked_settings)


@router.post("/settings", response_model=SettingsResponse)
async def update_settings(settings: TelegramSettings):
    """Update Telegram notification settings"""
    notifier = get_notifier()
    
    # If token is masked, keep the old one
    if settings.bot_token and "..." in settings.bot_token:
        settings.bot_token = notifier.get_settings().bot_token
    
    notifier.update_settings(settings)
    logger.info("Telegram settings updated")
    
    return SettingsResponse(settings=settings)


@router.get("/settings/full")
async def get_full_settings():
    """Get full settings (including unmasked token) - for internal use"""
    notifier = get_notifier()
    return {"success": True, "settings": notifier.get_settings().model_dump()}


# ============ BOT VALIDATION ============

@router.post("/validate-bot", response_model=BotValidationResponse)
async def validate_bot(
    bot_token: Optional[str] = Body(None, embed=True)
):
    """Validate Telegram bot token"""
    notifier = get_notifier()
    
    # Use provided token or existing one
    if bot_token and "..." not in bot_token:
        from app.core.notifications import TelegramSettings
        temp_settings = notifier.get_settings().model_copy()
        temp_settings.bot_token = bot_token
        notifier.update_settings(temp_settings)
    
    valid, bot_info, error = await notifier.validate_bot()
    
    return BotValidationResponse(
        valid=valid,
        bot_info=bot_info,
        error=error
    )


# ============ TEST NOTIFICATION ============

@router.post("/test", response_model=TestNotificationResponse)
async def send_test_notification(request: TestNotificationRequest = None):
    """Send a test notification"""
    notifier = get_notifier()
    settings = notifier.get_settings()
    
    # Update settings temporarily if provided
    if request:
        if request.bot_token and "..." not in request.bot_token:
            settings = settings.model_copy()
            settings.bot_token = request.bot_token
            notifier.update_settings(settings)
        
        if request.chat_id:
            settings = settings.model_copy()
            settings.chat_id = request.chat_id
            notifier.update_settings(settings)
    
    # Validate bot first
    valid, bot_info, error = await notifier.validate_bot()
    if not valid:
        return TestNotificationResponse(
            success=False,
            message=f"Bot validation failed: {error}",
            bot_info=bot_info.model_dump() if bot_info else None
        )
    
    # Send test message
    result = await notifier.send_test_notification()
    
    return TestNotificationResponse(
        success=result.success,
        message="Test notification sent successfully!" if result.success else f"Failed: {result.error}",
        message_id=result.message_id,
        bot_info=bot_info.model_dump() if bot_info else None
    )


# ============ STATISTICS ============

@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get notification statistics"""
    notifier = get_notifier()
    return StatsResponse(stats=notifier.get_stats())


@router.post("/stats/reset")
async def reset_stats():
    """Reset notification statistics"""
    notifier = get_notifier()
    notifier._stats = NotificationStats()
    return {"success": True, "message": "Statistics reset"}


# ============ SEND NOTIFICATIONS ============

@router.post("/send/signal", response_model=NotificationResultResponse)
async def send_signal_notification(request: SendSignalRequest):
    """Send new signal notification"""
    notifier = get_notifier()
    
    signal = SignalData(
        symbol=request.symbol,
        direction=request.direction,
        entry_price=request.entry_price,
        entry_zone_low=request.entry_zone_low,
        entry_zone_high=request.entry_zone_high,
        tp_targets=request.tp_targets,
        tp_amounts=request.tp_amounts,
        sl_price=request.sl_price,
        sl_percent=request.sl_percent,
        sl_mode=request.sl_mode,
        leverage=request.leverage,
        timeframe=request.timeframe,
        exchange=request.exchange,
        indicator_name=request.indicator_name,
        created_at=datetime.now()
    )
    
    result = await notifier.notify_new_signal(signal)
    
    if result is None:
        return NotificationResultResponse(
            success=False,
            error="Notifications disabled or new_signal notifications off"
        )
    
    return NotificationResultResponse(
        success=result.success,
        message_id=result.message_id,
        error=result.error
    )


@router.post("/send/tp-hit", response_model=NotificationResultResponse)
async def send_tp_hit_notification(request: SendTPHitRequest):
    """Send TP hit notification"""
    notifier = get_notifier()
    
    data = TPHitData(
        signal_id=request.signal_id,
        symbol=request.symbol,
        direction=request.direction,
        tp_level=request.tp_level,
        tp_price=request.tp_price,
        entry_price=request.entry_price,
        profit_percent=request.profit_percent,
        amount_closed=request.amount_closed,
        remaining_position=request.remaining_position,
        timestamp=datetime.now()
    )
    
    result = await notifier.notify_tp_hit(data)
    
    if result is None:
        return NotificationResultResponse(
            success=False,
            error="Notifications disabled or tp_hit notifications off"
        )
    
    return NotificationResultResponse(
        success=result.success,
        message_id=result.message_id,
        error=result.error
    )


@router.post("/send/sl-hit", response_model=NotificationResultResponse)
async def send_sl_hit_notification(request: SendSLHitRequest):
    """Send SL hit notification"""
    notifier = get_notifier()
    
    data = SLHitData(
        signal_id=request.signal_id,
        symbol=request.symbol,
        direction=request.direction,
        sl_price=request.sl_price,
        entry_price=request.entry_price,
        loss_percent=request.loss_percent,
        sl_mode=request.sl_mode,
        timestamp=datetime.now()
    )
    
    result = await notifier.notify_sl_hit(data)
    
    if result is None:
        return NotificationResultResponse(
            success=False,
            error="Notifications disabled or sl_hit notifications off"
        )
    
    return NotificationResultResponse(
        success=result.success,
        message_id=result.message_id,
        error=result.error
    )


@router.post("/send/closed", response_model=NotificationResultResponse)
async def send_closed_notification(request: SendClosedRequest):
    """Send signal closed notification"""
    notifier = get_notifier()
    
    data = SignalClosedData(
        signal_id=request.signal_id,
        symbol=request.symbol,
        direction=request.direction,
        entry_price=request.entry_price,
        exit_price=request.exit_price,
        pnl_percent=request.pnl_percent,
        pnl_usd=request.pnl_usd,
        duration_hours=request.duration_hours,
        close_reason=request.close_reason,
        tp_hits=request.tp_hits,
        timestamp=datetime.now()
    )
    
    result = await notifier.notify_signal_closed(data)
    
    if result is None:
        return NotificationResultResponse(
            success=False,
            error="Notifications disabled or signal_closed notifications off"
        )
    
    return NotificationResultResponse(
        success=result.success,
        message_id=result.message_id,
        error=result.error
    )


@router.post("/send/error", response_model=NotificationResultResponse)
async def send_error_notification(
    error: str = Body(..., embed=True),
    context: Optional[Dict[str, Any]] = Body(None, embed=True)
):
    """Send error notification"""
    notifier = get_notifier()
    
    result = await notifier.notify_error(error, context)
    
    if result is None:
        return NotificationResultResponse(
            success=False,
            error="Notifications disabled or error notifications off"
        )
    
    return NotificationResultResponse(
        success=result.success,
        message_id=result.message_id,
        error=result.error
    )


# ============ MESSAGE FORMATS ============

@router.get("/formats")
async def get_formats():
    """Get available message formats"""
    return {
        "formats": [
            {
                "id": "simple",
                "name": "Simple",
                "description": "Clean, readable format with emojis"
            },
            {
                "id": "cornix",
                "name": "Cornix",
                "description": "Compatible with Cornix trading bot"
            },
            {
                "id": "custom",
                "name": "Custom",
                "description": "Use your own template"
            }
        ]
    }


@router.get("/preview/{format_id}")
async def preview_format(format_id: str):
    """Preview message format with sample data"""
    from app.core.notifications import get_formatter, NotificationFormat
    
    # Create sample signal
    sample_signal = SignalData(
        symbol="BTCUSDT",
        direction="LONG",
        entry_price=42500.0,
        entry_zone_low=42000.0,
        entry_zone_high=42500.0,
        tp_targets=[43500.0, 44500.0, 46000.0, 48000.0],
        tp_amounts=[50, 30, 15, 5],
        sl_price=41000.0,
        sl_percent=3.5,
        sl_mode="trailing",
        leverage=10,
        timeframe="4h",
        exchange="binance",
        indicator_name="TRG"
    )
    
    try:
        format_enum = NotificationFormat(format_id)
    except ValueError:
        raise HTTPException(400, f"Invalid format: {format_id}")
    
    formatter = get_formatter(format_enum)
    settings = TelegramSettings(message_format=format_enum)
    
    notification = formatter.format_signal(sample_signal, settings)
    
    return {
        "format": format_id,
        "preview": notification.body,
        "parse_mode": notification.parse_mode
    }


# ============ CUSTOM TEMPLATE ============

@router.post("/template/validate")
async def validate_template(
    template: str = Body(..., embed=True)
):
    """Validate custom template"""
    # Check for required placeholders
    required = ["{symbol}", "{direction}"]
    optional = [
        "{entry_price}", "{entry_zone_low}", "{entry_zone_high}",
        "{sl_price}", "{sl_percent}", "{leverage}", "{timeframe}",
        "{exchange}", "{indicator_name}", "{tp_targets}"
    ]
    
    missing_required = [p for p in required if p not in template]
    used_optional = [p for p in optional if p in template]
    
    if missing_required:
        return {
            "valid": False,
            "error": f"Missing required placeholders: {', '.join(missing_required)}",
            "required": required,
            "optional": optional
        }
    
    return {
        "valid": True,
        "used_placeholders": required + used_optional,
        "available_placeholders": optional
    }


# ============ ENABLE/DISABLE ============

@router.post("/enable")
async def enable_notifications():
    """Enable notifications"""
    notifier = get_notifier()
    settings = notifier.get_settings()
    settings.enabled = True
    notifier.update_settings(settings)
    return {"success": True, "enabled": True}


@router.post("/disable")
async def disable_notifications():
    """Disable notifications"""
    notifier = get_notifier()
    settings = notifier.get_settings()
    settings.enabled = False
    notifier.update_settings(settings)
    return {"success": True, "enabled": False}
