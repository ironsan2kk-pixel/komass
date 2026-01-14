"""
Komas Trading Server - Channel Manager
======================================
Manages Telegram channels in database
"""
import logging
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import uuid

from .models import (
    TelegramChannel,
    TelegramChannelCreate,
    TelegramChannelUpdate,
    ChannelRoutingRules,
    NotificationFormat
)

logger = logging.getLogger(__name__)


class ChannelManager:
    """Manages Telegram channels storage"""

    def __init__(self, data_dir: Path = None):
        """
        Initialize channel manager

        Args:
            data_dir: Directory for storing channel data
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent.parent / "data"

        self.data_dir = data_dir
        self.channels_file = data_dir / "telegram_channels.json"
        self.channels: List[TelegramChannel] = []

        # Create data directory if needed
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Load existing channels
        self._load_channels()

    def _load_channels(self):
        """Load channels from file"""
        try:
            if self.channels_file.exists():
                with open(self.channels_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.channels = [TelegramChannel(**ch) for ch in data]
                logger.info(f"Loaded {len(self.channels)} channels from file")
            else:
                logger.info("No channels file found, starting with empty list")
        except Exception as e:
            logger.error(f"Failed to load channels: {e}")
            self.channels = []

    def _save_channels(self):
        """Save channels to file"""
        try:
            with open(self.channels_file, 'w', encoding='utf-8') as f:
                data = [ch.model_dump() for ch in self.channels]
                json.dump(data, f, indent=2, default=str)
            logger.info(f"Saved {len(self.channels)} channels to file")
        except Exception as e:
            logger.error(f"Failed to save channels: {e}")
            raise

    def create_channel(self, channel_data: TelegramChannelCreate) -> TelegramChannel:
        """
        Create a new channel

        Args:
            channel_data: Channel creation data

        Returns:
            Created channel

        Raises:
            ValueError: If channel with same name or chat_id exists
        """
        # Check for duplicates
        if any(ch.name == channel_data.name for ch in self.channels):
            raise ValueError(f"Channel with name '{channel_data.name}' already exists")

        if any(ch.chat_id == channel_data.chat_id for ch in self.channels):
            raise ValueError(
                f"Channel with chat_id '{channel_data.chat_id}' already exists"
            )

        # Create new channel
        channel = TelegramChannel(
            id=str(uuid.uuid4()),
            name=channel_data.name,
            chat_id=channel_data.chat_id,
            enabled=channel_data.enabled,
            message_format=channel_data.message_format,
            routing_rules=channel_data.routing_rules or ChannelRoutingRules(),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        self.channels.append(channel)
        self._save_channels()

        logger.info(f"Created channel '{channel.name}' with ID {channel.id}")
        return channel

    def get_channel(self, channel_id: str) -> Optional[TelegramChannel]:
        """
        Get channel by ID

        Args:
            channel_id: Channel ID

        Returns:
            Channel if found, None otherwise
        """
        for channel in self.channels:
            if channel.id == channel_id:
                return channel
        return None

    def get_all_channels(self) -> List[TelegramChannel]:
        """Get all channels"""
        return self.channels.copy()

    def get_enabled_channels(self) -> List[TelegramChannel]:
        """Get only enabled channels"""
        return [ch for ch in self.channels if ch.enabled]

    def update_channel(
        self, channel_id: str, update_data: TelegramChannelUpdate
    ) -> TelegramChannel:
        """
        Update channel

        Args:
            channel_id: Channel ID to update
            update_data: Update data

        Returns:
            Updated channel

        Raises:
            ValueError: If channel not found or duplicate name/chat_id
        """
        channel = self.get_channel(channel_id)
        if not channel:
            raise ValueError(f"Channel with ID '{channel_id}' not found")

        # Check for duplicate name
        if update_data.name and update_data.name != channel.name:
            if any(ch.name == update_data.name for ch in self.channels):
                raise ValueError(f"Channel with name '{update_data.name}' already exists")
            channel.name = update_data.name

        # Check for duplicate chat_id
        if update_data.chat_id and update_data.chat_id != channel.chat_id:
            if any(ch.chat_id == update_data.chat_id for ch in self.channels):
                raise ValueError(
                    f"Channel with chat_id '{update_data.chat_id}' already exists"
                )
            channel.chat_id = update_data.chat_id

        # Update other fields
        if update_data.enabled is not None:
            channel.enabled = update_data.enabled

        if update_data.message_format is not None:
            channel.message_format = update_data.message_format

        if update_data.routing_rules is not None:
            channel.routing_rules = update_data.routing_rules

        if update_data.include_chart_link is not None:
            channel.include_chart_link = update_data.include_chart_link

        if update_data.include_entry_zone is not None:
            channel.include_entry_zone = update_data.include_entry_zone

        if update_data.include_leverage is not None:
            channel.include_leverage = update_data.include_leverage

        if update_data.show_all_targets is not None:
            channel.show_all_targets = update_data.show_all_targets

        if update_data.custom_template is not None:
            channel.custom_template = update_data.custom_template

        # Update timestamp
        channel.updated_at = datetime.now()

        self._save_channels()
        logger.info(f"Updated channel '{channel.name}' (ID: {channel.id})")
        return channel

    def delete_channel(self, channel_id: str) -> bool:
        """
        Delete channel

        Args:
            channel_id: Channel ID to delete

        Returns:
            True if deleted, False if not found
        """
        for i, channel in enumerate(self.channels):
            if channel.id == channel_id:
                deleted_name = channel.name
                del self.channels[i]
                self._save_channels()
                logger.info(f"Deleted channel '{deleted_name}' (ID: {channel_id})")
                return True

        logger.warning(f"Channel with ID '{channel_id}' not found for deletion")
        return False

    def increment_message_count(self, channel_id: str):
        """
        Increment message count for a channel

        Args:
            channel_id: Channel ID
        """
        channel = self.get_channel(channel_id)
        if channel:
            channel.messages_sent += 1
            channel.last_sent = datetime.now()
            self._save_channels()

    def get_stats(self) -> dict:
        """Get channel statistics"""
        total = len(self.channels)
        enabled = len([ch for ch in self.channels if ch.enabled])
        total_messages = sum(ch.messages_sent for ch in self.channels)

        return {
            "total_channels": total,
            "enabled_channels": enabled,
            "disabled_channels": total - enabled,
            "total_messages_sent": total_messages,
            "channels": [
                {
                    "id": ch.id,
                    "name": ch.name,
                    "enabled": ch.enabled,
                    "messages_sent": ch.messages_sent,
                    "last_sent": ch.last_sent.isoformat() if ch.last_sent else None
                }
                for ch in self.channels
            ]
        }
