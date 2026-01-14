"""
Komas Trading Server - Notifications Module
============================================
Telegram and Discord notifications for trading signals
"""
from .models import (
    NotificationFormat,
    NotificationTrigger,
    TelegramSettings,
    DiscordSettings,
    SignalData,
    TPHitData,
    SLHitData,
    SignalClosedData,
    NotificationMessage,
    NotificationResult,
    NotificationTestRequest,
    NotificationTestResponse,
    TelegramBotInfo,
    NotificationStats
)

from .formatters import (
    get_formatter,
    format_error_message,
    format_test_message,
    SimpleFormatter,
    CornixFormatter,
    CustomFormatter
)

from .telegram import (
    TelegramNotifier,
    get_notifier,
    init_notifier
)

from .discord import (
    DiscordNotifier,
    get_discord_notifier,
    init_discord_notifier
)


__all__ = [
    # Models
    "NotificationFormat",
    "NotificationTrigger",
    "TelegramSettings",
    "DiscordSettings",
    "SignalData",
    "TPHitData",
    "SLHitData",
    "SignalClosedData",
    "NotificationMessage",
    "NotificationResult",
    "NotificationTestRequest",
    "NotificationTestResponse",
    "TelegramBotInfo",
    "NotificationStats",

    # Formatters
    "get_formatter",
    "format_error_message",
    "format_test_message",
    "SimpleFormatter",
    "CornixFormatter",
    "CustomFormatter",

    # Telegram
    "TelegramNotifier",
    "get_notifier",
    "init_notifier",

    # Discord
    "DiscordNotifier",
    "get_discord_notifier",
    "init_discord_notifier",
]
