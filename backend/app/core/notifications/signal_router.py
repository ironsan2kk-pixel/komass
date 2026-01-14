"""
Komas Trading Server - Signal Router
====================================
Routes signals to appropriate Telegram channels based on routing rules
"""
import logging
from typing import List
from .models import (
    SignalData,
    TelegramChannel,
    ChannelRoutingRules,
    TPHitData,
    SLHitData,
    SignalClosedData
)

logger = logging.getLogger(__name__)


class SignalRouter:
    """Routes signals to appropriate channels based on rules"""

    def __init__(self, channels: List[TelegramChannel] = None):
        """
        Initialize router with channels

        Args:
            channels: List of available Telegram channels
        """
        self.channels = channels or []

    def update_channels(self, channels: List[TelegramChannel]):
        """Update the list of available channels"""
        self.channels = channels
        logger.info(f"Updated router with {len(channels)} channels")

    def route_signal(self, signal: SignalData) -> List[TelegramChannel]:
        """
        Determine which channels should receive this signal

        Args:
            signal: The signal to route

        Returns:
            List of channels that match the routing rules
        """
        matching_channels = []

        for channel in self.channels:
            if not channel.enabled:
                continue

            # Check if channel wants new signals
            if not channel.routing_rules.notify_new_signal:
                continue

            # Check if signal matches channel's routing rules
            if self._matches_rules(signal, channel.routing_rules):
                matching_channels.append(channel)
                logger.debug(
                    f"Signal {signal.symbol} {signal.direction} matches channel '{channel.name}'"
                )

        logger.info(
            f"Routed signal {signal.symbol} to {len(matching_channels)} channels"
        )
        return matching_channels

    def route_tp_hit(self, tp_data: TPHitData) -> List[TelegramChannel]:
        """
        Route TP hit notification

        Args:
            tp_data: TP hit data

        Returns:
            List of channels that want TP notifications
        """
        matching_channels = []

        for channel in self.channels:
            if not channel.enabled:
                continue

            if channel.routing_rules.notify_tp_hit:
                # Note: We could add more sophisticated filtering here
                # For now, send to all channels that want TP notifications
                matching_channels.append(channel)

        logger.info(
            f"Routed TP hit for {tp_data.symbol} to {len(matching_channels)} channels"
        )
        return matching_channels

    def route_sl_hit(self, sl_data: SLHitData) -> List[TelegramChannel]:
        """
        Route SL hit notification

        Args:
            sl_data: SL hit data

        Returns:
            List of channels that want SL notifications
        """
        matching_channels = []

        for channel in self.channels:
            if not channel.enabled:
                continue

            if channel.routing_rules.notify_sl_hit:
                matching_channels.append(channel)

        logger.info(
            f"Routed SL hit for {sl_data.symbol} to {len(matching_channels)} channels"
        )
        return matching_channels

    def route_signal_closed(self, closed_data: SignalClosedData) -> List[TelegramChannel]:
        """
        Route signal closed notification

        Args:
            closed_data: Signal closed data

        Returns:
            List of channels that want closed notifications
        """
        matching_channels = []

        for channel in self.channels:
            if not channel.enabled:
                continue

            if channel.routing_rules.notify_signal_closed:
                matching_channels.append(channel)

        logger.info(
            f"Routed signal closed for {closed_data.symbol} to {len(matching_channels)} channels"
        )
        return matching_channels

    def route_error(self, error_msg: str) -> List[TelegramChannel]:
        """
        Route error notification

        Args:
            error_msg: Error message

        Returns:
            List of channels that want error notifications
        """
        matching_channels = []

        for channel in self.channels:
            if not channel.enabled:
                continue

            if channel.routing_rules.notify_errors:
                matching_channels.append(channel)

        logger.info(f"Routed error to {len(matching_channels)} channels")
        return matching_channels

    def _matches_rules(self, signal: SignalData, rules: ChannelRoutingRules) -> bool:
        """
        Check if signal matches channel routing rules

        Args:
            signal: The signal to check
            rules: Channel routing rules

        Returns:
            True if signal matches all rules, False otherwise
        """
        # Check indicator filter
        if rules.indicators and signal.indicator_name not in rules.indicators:
            logger.debug(
                f"Signal indicator '{signal.indicator_name}' not in {rules.indicators}"
            )
            return False

        # Check symbol filter
        if rules.symbols and signal.symbol not in rules.symbols:
            logger.debug(f"Signal symbol '{signal.symbol}' not in {rules.symbols}")
            return False

        # Check direction filter
        if rules.directions and signal.direction not in rules.directions:
            logger.debug(
                f"Signal direction '{signal.direction}' not in {rules.directions}"
            )
            return False

        # Check minimum score filter
        if rules.min_score is not None:
            if signal.score is None or signal.score < rules.min_score:
                logger.debug(
                    f"Signal score {signal.score} below minimum {rules.min_score}"
                )
                return False

        # Check grade filter
        if rules.score_grades and signal.grade:
            if signal.grade not in rules.score_grades:
                logger.debug(
                    f"Signal grade '{signal.grade}' not in {rules.score_grades}"
                )
                return False

        # All checks passed
        return True

    def get_channel_by_id(self, channel_id: str) -> TelegramChannel | None:
        """Get channel by ID"""
        for channel in self.channels:
            if channel.id == channel_id:
                return channel
        return None

    def get_active_channels(self) -> List[TelegramChannel]:
        """Get all enabled channels"""
        return [ch for ch in self.channels if ch.enabled]

    def get_channels_count(self) -> dict:
        """Get channel statistics"""
        return {
            "total": len(self.channels),
            "enabled": len([ch for ch in self.channels if ch.enabled]),
            "disabled": len([ch for ch in self.channels if not ch.enabled])
        }
