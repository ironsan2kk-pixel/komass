"""
Komas Trading Server - Telegram Integration for Bots
====================================================
Integrates BotRunner with Telegram Multi-Channel notifications
"""
import logging
from typing import Optional
from datetime import datetime

from .models import SignalEvent, Position, Bot
from ..notifications import (
    SignalData,
    TPHitData,
    SLHitData,
    SignalClosedData,
    get_notifier,
)
from ..notifications.channel_manager import ChannelManager
from ..notifications.signal_router import SignalRouter

logger = logging.getLogger(__name__)


class TelegramBotIntegration:
    """
    Integrates BotRunner with Telegram notifications via Signal Router
    """

    def __init__(self):
        self.notifier = get_notifier()
        self.channel_manager = ChannelManager()
        self.signal_router = SignalRouter(self.channel_manager.get_enabled_channels())
        logger.info("TelegramBotIntegration initialized")

    def refresh_channels(self):
        """Refresh signal router with latest channels"""
        channels = self.channel_manager.get_enabled_channels()
        self.signal_router.update_channels(channels)
        logger.info(f"Signal router refreshed with {len(channels)} channels")

    async def handle_new_signal(self, event: SignalEvent):
        """
        Handle new signal event from BotRunner

        Args:
            event: SignalEvent from bot strategy
        """
        try:
            # Convert SignalEvent to SignalData
            signal_data = self._convert_signal_event(event)

            # Route to appropriate channels
            channels = self.signal_router.route_signal(signal_data)

            if not channels:
                logger.debug(f"No channels match routing rules for {signal_data.symbol}")
                return

            logger.info(
                f"Routing signal {signal_data.symbol} to {len(channels)} channels"
            )

            # Send to each channel
            for channel in channels:
                try:
                    # Update notifier settings for this channel
                    temp_settings = self.notifier.get_settings().model_copy()
                    temp_settings.chat_id = channel.chat_id
                    temp_settings.message_format = channel.message_format
                    temp_settings.include_chart_link = channel.include_chart_link
                    temp_settings.include_entry_zone = channel.include_entry_zone
                    temp_settings.include_leverage = channel.include_leverage
                    temp_settings.show_all_targets = channel.show_all_targets

                    # Temporarily update settings
                    original_settings = self.notifier.get_settings()
                    self.notifier.update_settings(temp_settings)

                    # Send notification
                    result = await self.notifier.notify_new_signal(signal_data)

                    # Restore original settings
                    self.notifier.update_settings(original_settings)

                    if result and result.success:
                        # Increment message count
                        self.channel_manager.increment_message_count(channel.id)
                        logger.info(
                            f"Signal sent to channel '{channel.name}' (message_id: {result.message_id})"
                        )
                    else:
                        logger.warning(
                            f"Failed to send to channel '{channel.name}': {result.error if result else 'No result'}"
                        )

                except Exception as e:
                    logger.error(
                        f"Error sending to channel '{channel.name}': {e}",
                        exc_info=True
                    )

        except Exception as e:
            logger.error(f"Error handling new signal: {e}", exc_info=True)

    async def handle_tp_hit(self, position: Position, tp_level: int, tp_price: float):
        """
        Handle Take Profit hit event

        Args:
            position: Position that hit TP
            tp_level: TP level (1-10)
            tp_price: Price at which TP was hit
        """
        try:
            # Calculate profit
            profit_percent = self._calculate_profit_percent(
                position.entry_price,
                tp_price,
                position.direction
            )

            # Create TPHitData
            tp_data = TPHitData(
                signal_id=0,  # Position doesn't have signal_id, use 0
                symbol=position.symbol,
                direction=position.direction.value,
                tp_level=tp_level,
                tp_price=tp_price,
                entry_price=position.entry_price,
                profit_percent=profit_percent,
                amount_closed=50.0,  # Default 50% per TP
                remaining_position=50.0 * (len(position.tp_targets) - tp_level) / len(position.tp_targets),
                timestamp=datetime.now()
            )

            # Route to channels
            channels = self.signal_router.route_tp_hit(tp_data)

            if not channels:
                return

            logger.info(f"Routing TP hit for {tp_data.symbol} to {len(channels)} channels")

            # Send to each channel
            for channel in channels:
                try:
                    temp_settings = self.notifier.get_settings().model_copy()
                    temp_settings.chat_id = channel.chat_id
                    temp_settings.message_format = channel.message_format

                    original_settings = self.notifier.get_settings()
                    self.notifier.update_settings(temp_settings)

                    result = await self.notifier.notify_tp_hit(tp_data)

                    self.notifier.update_settings(original_settings)

                    if result and result.success:
                        self.channel_manager.increment_message_count(channel.id)
                        logger.info(f"TP notification sent to '{channel.name}'")

                except Exception as e:
                    logger.error(f"Error sending TP to '{channel.name}': {e}")

        except Exception as e:
            logger.error(f"Error handling TP hit: {e}", exc_info=True)

    async def handle_sl_hit(self, position: Position, sl_price: float):
        """
        Handle Stop Loss hit event

        Args:
            position: Position that hit SL
            sl_price: Price at which SL was hit
        """
        try:
            # Calculate loss
            loss_percent = self._calculate_profit_percent(
                position.entry_price,
                sl_price,
                position.direction
            )

            # Create SLHitData
            sl_data = SLHitData(
                signal_id=0,
                symbol=position.symbol,
                direction=position.direction.value,
                sl_price=sl_price,
                entry_price=position.entry_price,
                loss_percent=loss_percent,
                sl_mode=position.sl_mode,
                timestamp=datetime.now()
            )

            # Route to channels
            channels = self.signal_router.route_sl_hit(sl_data)

            if not channels:
                return

            logger.info(f"Routing SL hit for {sl_data.symbol} to {len(channels)} channels")

            # Send to each channel
            for channel in channels:
                try:
                    temp_settings = self.notifier.get_settings().model_copy()
                    temp_settings.chat_id = channel.chat_id
                    temp_settings.message_format = channel.message_format

                    original_settings = self.notifier.get_settings()
                    self.notifier.update_settings(temp_settings)

                    result = await self.notifier.notify_sl_hit(sl_data)

                    self.notifier.update_settings(original_settings)

                    if result and result.success:
                        self.channel_manager.increment_message_count(channel.id)
                        logger.info(f"SL notification sent to '{channel.name}'")

                except Exception as e:
                    logger.error(f"Error sending SL to '{channel.name}': {e}")

        except Exception as e:
            logger.error(f"Error handling SL hit: {e}", exc_info=True)

    async def handle_signal_closed(self, position: Position, exit_price: float, close_reason: str):
        """
        Handle signal closed event

        Args:
            position: Closed position
            exit_price: Exit price
            close_reason: Reason for closing
        """
        try:
            # Calculate PnL
            pnl_percent = self._calculate_profit_percent(
                position.entry_price,
                exit_price,
                position.direction
            )
            pnl_usd = position.size * (pnl_percent / 100)

            # Calculate duration
            if position.closed_at and position.entry_time:
                duration = position.closed_at - position.entry_time
                duration_hours = duration.total_seconds() / 3600
            else:
                duration_hours = None

            # Get TP hits
            tp_hits = [i + 1 for i, hit in enumerate(position.tp_hits) if hit]

            # Create SignalClosedData
            closed_data = SignalClosedData(
                signal_id=0,
                symbol=position.symbol,
                direction=position.direction.value,
                entry_price=position.entry_price,
                exit_price=exit_price,
                pnl_percent=pnl_percent,
                pnl_usd=pnl_usd,
                duration_hours=duration_hours,
                close_reason=close_reason,
                tp_hits=tp_hits,
                timestamp=datetime.now()
            )

            # Route to channels
            channels = self.signal_router.route_signal_closed(closed_data)

            if not channels:
                return

            logger.info(f"Routing closed signal for {closed_data.symbol} to {len(channels)} channels")

            # Send to each channel
            for channel in channels:
                try:
                    temp_settings = self.notifier.get_settings().model_copy()
                    temp_settings.chat_id = channel.chat_id
                    temp_settings.message_format = channel.message_format

                    original_settings = self.notifier.get_settings()
                    self.notifier.update_settings(temp_settings)

                    result = await self.notifier.notify_signal_closed(closed_data)

                    self.notifier.update_settings(original_settings)

                    if result and result.success:
                        self.channel_manager.increment_message_count(channel.id)
                        logger.info(f"Closed notification sent to '{channel.name}'")

                except Exception as e:
                    logger.error(f"Error sending closed to '{channel.name}': {e}")

        except Exception as e:
            logger.error(f"Error handling signal closed: {e}", exc_info=True)

    def _convert_signal_event(self, event: SignalEvent) -> SignalData:
        """
        Convert SignalEvent to SignalData for notifications

        Args:
            event: Signal event from bot

        Returns:
            SignalData for telegram notifications
        """
        # Get indicator values
        indicator_vals = event.indicator_values or {}

        # Extract TP and SL from indicator values
        tp_targets = indicator_vals.get('tp_targets', [event.price * 1.02, event.price * 1.04])
        sl_price = indicator_vals.get('sl_price', event.price * 0.98 if event.direction.value == 'LONG' else event.price * 1.02)

        # Default TP amounts (equal split)
        tp_amounts = [100 / len(tp_targets)] * len(tp_targets)

        return SignalData(
            symbol=event.symbol,
            direction=event.direction.value,
            entry_price=event.price,
            tp_targets=tp_targets,
            tp_amounts=tp_amounts,
            sl_price=sl_price,
            leverage=indicator_vals.get('leverage', 10),
            timeframe=event.timeframe,
            indicator_name=indicator_vals.get('indicator_name', 'TRG'),
            winrate=indicator_vals.get('winrate'),
            score=indicator_vals.get('score'),
            grade=indicator_vals.get('grade'),
            created_at=event.timestamp
        )

    def _calculate_profit_percent(self, entry_price: float, exit_price: float, direction) -> float:
        """Calculate profit/loss percentage"""
        if direction.value == 'LONG':
            return ((exit_price - entry_price) / entry_price) * 100
        else:  # SHORT
            return ((entry_price - exit_price) / entry_price) * 100


# Singleton instance
_telegram_integration: Optional[TelegramBotIntegration] = None


def get_telegram_integration() -> TelegramBotIntegration:
    """Get or create telegram integration instance"""
    global _telegram_integration
    if _telegram_integration is None:
        _telegram_integration = TelegramBotIntegration()
    return _telegram_integration


def init_telegram_integration():
    """Initialize telegram integration"""
    global _telegram_integration
    _telegram_integration = TelegramBotIntegration()
    logger.info("Telegram integration initialized")
    return _telegram_integration
