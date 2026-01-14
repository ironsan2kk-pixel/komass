"""
KOMAS Bot Runner - Notification Integration
============================================
Connects bot runner callbacks to Telegram/Discord notification systems.

Functions:
- setup_notifications: Initialize notification callbacks for bot runner
- Bridges runner events to Telegram/Discord notifiers

NEW: Multi-Channel Support
- Uses TelegramBotIntegration with SignalRouter for multi-channel routing
- Supports filtering by indicator, symbol, direction, score, grade
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from ..notifications.telegram import TelegramNotifier
from ..notifications.discord import DiscordNotifier
from ..notifications.models import (
    SignalData,
    TPHitData,
    SLHitData,
    SignalClosedData,
    SignalDirection
)
from ..logger import get_logger
from .telegram_integration import get_telegram_integration

logger = get_logger("bots.notifications")


# ═══════════════════════════════════════════════════════════════════
# GLOBAL NOTIFIERS
# ═══════════════════════════════════════════════════════════════════

_telegram_notifier: Optional[TelegramNotifier] = None
_discord_notifier: Optional[DiscordNotifier] = None


def get_telegram_notifier() -> TelegramNotifier:
    """Get or create global Telegram notifier instance"""
    global _telegram_notifier

    if _telegram_notifier is None:
        _telegram_notifier = TelegramNotifier()
        logger.info("Created Telegram notifier instance")

    return _telegram_notifier


def get_discord_notifier() -> DiscordNotifier:
    """Get or create global Discord notifier instance"""
    global _discord_notifier

    if _discord_notifier is None:
        _discord_notifier = DiscordNotifier()
        logger.info("Created Discord notifier instance")

    return _discord_notifier


# ═══════════════════════════════════════════════════════════════════
# SIGNAL EVENT HANDLERS
# ═══════════════════════════════════════════════════════════════════

async def on_new_signal(
    bot_id: str,
    symbol: str,
    direction: str,
    entry_price: float,
    stop_loss: float,
    take_profits: list,
    leverage: int = 1,
    **kwargs
):
    """
    Handle new signal event from bot runner.

    Called when bot opens a new position.
    """
    try:
        # Create signal data
        signal = SignalData(
            symbol=symbol,
            direction=SignalDirection(direction.lower()),
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profits=take_profits,
            leverage=leverage,
            timestamp=datetime.now()
        )

        # Send to Telegram
        telegram = get_telegram_notifier()
        if telegram.settings.enabled:
            result = await telegram.notify_new_signal(signal)
            if result and result.success:
                logger.info(f"[{bot_id}] Telegram notification sent for {symbol}")

        # Send to Discord
        discord = get_discord_notifier()
        if discord.settings.enabled:
            result = await discord.notify_new_signal(signal)
            if result and result.success:
                logger.info(f"[{bot_id}] Discord notification sent for {symbol}")

    except Exception as e:
        logger.error(f"Error sending new signal notification: {e}")


async def on_tp_hit(
    bot_id: str,
    symbol: str,
    direction: str,
    tp_level: int,
    tp_price: float,
    partial_close_percent: float,
    pnl_percent: float,
    remaining_position: float = 0.0,
    **kwargs
):
    """
    Handle TP hit event from bot runner.

    Called when a take profit level is hit.
    """
    try:
        # Create TP hit data
        tp_data = TPHitData(
            symbol=symbol,
            direction=SignalDirection(direction.lower()),
            tp_level=tp_level,
            tp_price=tp_price,
            partial_close_percent=partial_close_percent,
            pnl_percent=pnl_percent,
            remaining_position=remaining_position,
            timestamp=datetime.now()
        )

        # Send to Telegram
        telegram = get_telegram_notifier()
        if telegram.settings.enabled:
            result = await telegram.notify_tp_hit(tp_data)
            if result and result.success:
                logger.info(f"[{bot_id}] Telegram TP{tp_level} notification sent for {symbol}")

        # Send to Discord
        discord = get_discord_notifier()
        if discord.settings.enabled:
            result = await discord.notify_tp_hit(tp_data)
            if result and result.success:
                logger.info(f"[{bot_id}] Discord TP{tp_level} notification sent for {symbol}")

    except Exception as e:
        logger.error(f"Error sending TP hit notification: {e}")


async def on_sl_hit(
    bot_id: str,
    symbol: str,
    direction: str,
    sl_price: float,
    pnl_percent: float,
    sl_mode: str = "fixed",
    **kwargs
):
    """
    Handle SL hit event from bot runner.

    Called when stop loss is hit.
    """
    try:
        # Create SL hit data
        sl_data = SLHitData(
            symbol=symbol,
            direction=SignalDirection(direction.lower()),
            sl_price=sl_price,
            pnl_percent=pnl_percent,
            sl_mode=sl_mode,
            timestamp=datetime.now()
        )

        # Send to Telegram
        telegram = get_telegram_notifier()
        if telegram.settings.enabled:
            result = await telegram.notify_sl_hit(sl_data)
            if result and result.success:
                logger.info(f"[{bot_id}] Telegram SL notification sent for {symbol}")

        # Send to Discord
        discord = get_discord_notifier()
        if discord.settings.enabled:
            result = await discord.notify_sl_hit(sl_data)
            if result and result.success:
                logger.info(f"[{bot_id}] Discord SL notification sent for {symbol}")

    except Exception as e:
        logger.error(f"Error sending SL hit notification: {e}")


async def on_signal_closed(
    bot_id: str,
    symbol: str,
    direction: str,
    entry_price: float,
    exit_price: float,
    pnl_percent: float,
    holding_time: str,
    close_reason: str = "manual",
    **kwargs
):
    """
    Handle signal closed event from bot runner.

    Called when position is fully closed.
    """
    try:
        # Create signal closed data
        closed_data = SignalClosedData(
            symbol=symbol,
            direction=SignalDirection(direction.lower()),
            entry_price=entry_price,
            exit_price=exit_price,
            pnl_percent=pnl_percent,
            holding_time=holding_time,
            close_reason=close_reason,
            timestamp=datetime.now()
        )

        # Send to Telegram
        telegram = get_telegram_notifier()
        if telegram.settings.enabled:
            result = await telegram.notify_signal_closed(closed_data)
            if result and result.success:
                logger.info(f"[{bot_id}] Telegram close notification sent for {symbol}")

        # Send to Discord
        discord = get_discord_notifier()
        if discord.settings.enabled:
            result = await discord.notify_signal_closed(closed_data)
            if result and result.success:
                logger.info(f"[{bot_id}] Discord close notification sent for {symbol}")

    except Exception as e:
        logger.error(f"Error sending signal closed notification: {e}")


async def on_bot_error(
    bot_id: str,
    error: str,
    symbol: Optional[str] = None,
    **kwargs
):
    """
    Handle bot error event.

    Called when bot encounters an error during execution.
    """
    try:
        context = {
            "bot_id": bot_id,
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }

        # Send to Telegram
        telegram = get_telegram_notifier()
        if telegram.settings.enabled:
            result = await telegram.notify_error(error, context)
            if result and result.success:
                logger.info(f"[{bot_id}] Telegram error notification sent")

        # Send to Discord
        discord = get_discord_notifier()
        if discord.settings.enabled:
            result = await discord.notify_error(error, context)
            if result and result.success:
                logger.info(f"[{bot_id}] Discord error notification sent")

    except Exception as e:
        logger.error(f"Error sending bot error notification: {e}")


# ═══════════════════════════════════════════════════════════════════
# RUNNER INTEGRATION
# ═══════════════════════════════════════════════════════════════════

def setup_bot_runner_notifications(runner):
    """
    Setup notification callbacks for bot runner.

    Connects runner signal events to Telegram/Discord notifiers.

    Args:
        runner: BotsRunner instance
    """
    # Note: The current runner.py uses generic signal_callbacks
    # For now, we'll create a unified callback that handles all event types

    async def unified_callback(event_data: Dict[str, Any]):
        """Unified callback for all bot runner events"""
        event_type = event_data.get("type", "unknown")

        try:
            if event_type == "new_signal":
                await on_new_signal(**event_data)
            elif event_type == "tp_hit":
                await on_tp_hit(**event_data)
            elif event_type == "sl_hit":
                await on_sl_hit(**event_data)
            elif event_type == "signal_closed":
                await on_signal_closed(**event_data)
            elif event_type == "error":
                await on_bot_error(**event_data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
        except Exception as e:
            logger.error(f"Error in unified notification callback: {e}")

    # Add callback to runner
    runner.add_signal_callback(unified_callback)
    logger.info("Notification callbacks registered with bot runner")

    return runner


def setup_multi_channel_integration(runner):
    """
    Setup Multi-Channel Telegram integration with Signal Router.

    This enables routing signals to multiple Telegram channels based on
    filtering rules (indicator, symbol, direction, score, grade).

    Args:
        runner: BotsRunner instance
    """
    try:
        # Get telegram integration (singleton)
        telegram_integration = get_telegram_integration()

        # Register callback for new signals from runner
        async def on_signal_event(event):
            """Handle SignalEvent from BotRunner"""
            try:
                # Route to multi-channel system
                await telegram_integration.handle_new_signal(event)
            except Exception as e:
                logger.error(f"Error in multi-channel signal handler: {e}", exc_info=True)

        # Add callback to runner
        runner.add_signal_callback(on_signal_event)
        logger.info("✔ Multi-Channel Telegram integration configured")

    except Exception as e:
        logger.error(f"✗ Failed to setup multi-channel integration: {e}")


def setup_notifications_for_runner(runner):
    """
    Convenience function to setup all notification integrations.

    Sets up:
    - Legacy single-channel notifications (Telegram/Discord)
    - NEW: Multi-Channel Telegram with Signal Router

    Args:
        runner: BotsRunner instance

    Returns:
        Configured runner instance
    """
    try:
        # Initialize notifiers (they load saved settings automatically)
        get_telegram_notifier()
        get_discord_notifier()

        # Setup legacy callbacks (single-channel)
        setup_bot_runner_notifications(runner)

        # NEW: Setup Multi-Channel Telegram integration
        setup_multi_channel_integration(runner)

        logger.info("✔ Notification integration completed (single + multi-channel)")
        return runner

    except Exception as e:
        logger.error(f"✗ Failed to setup notifications: {e}")
        return runner
