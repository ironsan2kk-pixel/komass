"""
Komas Trading Server - Discord Webhook Client
==============================================
Discord webhook integration for trading notifications with rich embeds
"""
import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json

import aiohttp

from .models import (
    DiscordSettings,
    NotificationResult,
    SignalData,
    TPHitData,
    SLHitData,
    SignalClosedData,
    NotificationStats,
    NotificationTrigger
)


logger = logging.getLogger(__name__)


class DiscordNotifier:
    """Discord webhook notification client"""

    def __init__(self, settings: Optional[DiscordSettings] = None):
        self.settings = settings or DiscordSettings()
        self._session: Optional[aiohttp.ClientSession] = None

        # Statistics
        self._stats = NotificationStats()

        # Settings file path
        self._settings_file = Path(__file__).parent.parent.parent.parent / "data" / "discord_settings.json"

        # Load saved settings
        self._load_settings()

    def _load_settings(self):
        """Load settings from file"""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings = DiscordSettings(**data)
                    logger.info("Discord settings loaded from file")
        except Exception as e:
            logger.warning(f"Failed to load discord settings: {e}")

    def _save_settings(self):
        """Save settings to file"""
        try:
            self._settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings.model_dump(), f, indent=2, default=str)
            logger.info("Discord settings saved to file")
        except Exception as e:
            logger.error(f"Failed to save discord settings: {e}")

    def update_settings(self, settings: DiscordSettings):
        """Update notification settings"""
        self.settings = settings
        self._save_settings()

    def get_settings(self) -> DiscordSettings:
        """Get current settings"""
        return self.settings

    def get_stats(self) -> NotificationStats:
        """Get notification statistics"""
        return self._stats

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close aiohttp session"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def validate_webhook(self, webhook_url: Optional[str] = None) -> tuple[bool, Optional[Dict], Optional[str]]:
        """Validate Discord webhook URL"""
        url = webhook_url or self.settings.webhook_url
        if not url:
            return False, None, "Webhook URL not configured"

        try:
            session = await self._get_session()
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    webhook_info = {
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "channel_id": data.get("channel_id"),
                        "guild_id": data.get("guild_id"),
                        "type": data.get("type")
                    }
                    return True, webhook_info, None
                else:
                    return False, None, f"Invalid webhook (HTTP {response.status})"
        except Exception as e:
            return False, None, str(e)

    def _create_embed_color(self, trigger: NotificationTrigger, pnl_percent: Optional[float] = None) -> int:
        """Create embed color based on trigger type and PnL"""
        # Discord colors in decimal format
        COLORS = {
            "green": 0x00FF00,      # Profit / TP Hit
            "red": 0xFF0000,        # Loss / SL Hit
            "blue": 0x3B82F6,       # New Signal
            "yellow": 0xFBBF24,     # Warning
            "purple": 0xA855F7,     # Closed position
            "gray": 0x6B7280        # Neutral
        }

        if trigger == NotificationTrigger.NEW_SIGNAL:
            return COLORS["blue"]
        elif trigger == NotificationTrigger.TP_HIT:
            return COLORS["green"]
        elif trigger == NotificationTrigger.SL_HIT:
            return COLORS["red"]
        elif trigger == NotificationTrigger.SIGNAL_CLOSED:
            if pnl_percent is not None:
                return COLORS["green"] if pnl_percent > 0 else COLORS["red"]
            return COLORS["purple"]
        elif trigger == NotificationTrigger.ERROR:
            return COLORS["yellow"]
        else:
            return COLORS["gray"]

    def _format_signal_embed(self, signal: SignalData) -> Dict[str, Any]:
        """Format new signal as Discord rich embed"""
        # Direction emoji
        direction_emoji = "🟢" if signal.direction == "LONG" else "🔴"

        # Build fields
        fields = []

        # Entry price / zone
        if self.settings.include_entry_zone and signal.entry_zone_low and signal.entry_zone_high:
            entry_text = f"{signal.entry_zone_low:.8g} - {signal.entry_zone_high:.8g}"
        else:
            entry_text = f"{signal.entry_price:.8g}"

        fields.append({
            "name": "📍 Entry",
            "value": entry_text,
            "inline": True
        })

        # Leverage
        if self.settings.include_leverage and signal.leverage > 1:
            fields.append({
                "name": "⚡ Leverage",
                "value": f"{signal.leverage}x",
                "inline": True
            })

        # Timeframe
        fields.append({
            "name": "⏰ Timeframe",
            "value": signal.timeframe.upper(),
            "inline": True
        })

        # Take Profit targets
        if self.settings.show_all_targets and signal.tp_targets:
            tp_lines = []
            for i, (tp_price, tp_amount) in enumerate(zip(signal.tp_targets, signal.tp_amounts or []), 1):
                if tp_amount:
                    tp_lines.append(f"TP{i}: {tp_price:.8g} ({tp_amount}%)")
                else:
                    tp_lines.append(f"TP{i}: {tp_price:.8g}")

            fields.append({
                "name": "🎯 Take Profits",
                "value": "\n".join(tp_lines) if tp_lines else "N/A",
                "inline": False
            })

        # Stop Loss
        sl_text = f"{signal.sl_price:.8g}"
        if signal.sl_percent:
            sl_text += f" (-{signal.sl_percent:.2f}%)"
        if signal.sl_mode != "fixed":
            sl_text += f" [{signal.sl_mode}]"

        fields.append({
            "name": "🛡️ Stop Loss",
            "value": sl_text,
            "inline": False
        })

        # Win rate
        if signal.winrate:
            fields.append({
                "name": "📊 Win Rate",
                "value": f"{signal.winrate:.1f}%",
                "inline": True
            })

        # Indicator
        fields.append({
            "name": "🔧 Indicator",
            "value": signal.indicator_name,
            "inline": True
        })

        # Exchange
        fields.append({
            "name": "🏦 Exchange",
            "value": signal.exchange.capitalize(),
            "inline": True
        })

        # Build embed
        embed = {
            "title": f"{direction_emoji} {signal.direction} {signal.symbol}",
            "description": f"**New trading signal detected**",
            "color": self._create_embed_color(NotificationTrigger.NEW_SIGNAL),
            "fields": fields,
            "timestamp": (signal.created_at or datetime.now()).isoformat(),
            "footer": {
                "text": "KOMAS Trading System"
            }
        }

        # Add chart link if enabled
        if self.settings.include_chart_link:
            embed["url"] = f"https://www.tradingview.com/chart/?symbol={signal.exchange.upper()}:{signal.symbol}"

        return embed

    def _format_tp_hit_embed(self, data: TPHitData) -> Dict[str, Any]:
        """Format TP hit as Discord rich embed"""
        direction_emoji = "🟢" if data.direction == "LONG" else "🔴"

        fields = [
            {
                "name": "📍 Entry Price",
                "value": f"{data.entry_price:.8g}",
                "inline": True
            },
            {
                "name": f"🎯 TP{data.tp_level} Price",
                "value": f"{data.tp_price:.8g}",
                "inline": True
            },
            {
                "name": "💰 Profit",
                "value": f"+{data.profit_percent:.2f}%",
                "inline": True
            },
            {
                "name": "📊 Closed",
                "value": f"{data.amount_closed:.1f}%",
                "inline": True
            },
            {
                "name": "📈 Remaining",
                "value": f"{data.remaining_position:.1f}%",
                "inline": True
            }
        ]

        embed = {
            "title": f"{direction_emoji} TP{data.tp_level} HIT - {data.symbol}",
            "description": f"**Take Profit level {data.tp_level} reached!**",
            "color": self._create_embed_color(NotificationTrigger.TP_HIT),
            "fields": fields,
            "timestamp": (data.timestamp or datetime.now()).isoformat(),
            "footer": {
                "text": f"Signal #{data.signal_id}"
            }
        }

        return embed

    def _format_sl_hit_embed(self, data: SLHitData) -> Dict[str, Any]:
        """Format SL hit as Discord rich embed"""
        direction_emoji = "🟢" if data.direction == "LONG" else "🔴"

        fields = [
            {
                "name": "📍 Entry Price",
                "value": f"{data.entry_price:.8g}",
                "inline": True
            },
            {
                "name": "🛡️ SL Price",
                "value": f"{data.sl_price:.8g}",
                "inline": True
            },
            {
                "name": "💸 Loss",
                "value": f"-{data.loss_percent:.2f}%",
                "inline": True
            },
            {
                "name": "🔧 SL Mode",
                "value": data.sl_mode.capitalize(),
                "inline": True
            }
        ]

        embed = {
            "title": f"{direction_emoji} STOP LOSS - {data.symbol}",
            "description": f"**Stop Loss triggered**",
            "color": self._create_embed_color(NotificationTrigger.SL_HIT),
            "fields": fields,
            "timestamp": (data.timestamp or datetime.now()).isoformat(),
            "footer": {
                "text": f"Signal #{data.signal_id}"
            }
        }

        return embed

    def _format_closed_embed(self, data: SignalClosedData) -> Dict[str, Any]:
        """Format signal closed as Discord rich embed"""
        direction_emoji = "🟢" if data.direction == "LONG" else "🔴"
        profit_emoji = "💚" if data.pnl_percent > 0 else "❤️"

        fields = [
            {
                "name": "📍 Entry Price",
                "value": f"{data.entry_price:.8g}",
                "inline": True
            },
            {
                "name": "🚪 Exit Price",
                "value": f"{data.exit_price:.8g}",
                "inline": True
            },
            {
                "name": f"{profit_emoji} PnL",
                "value": f"{'+' if data.pnl_percent > 0 else ''}{data.pnl_percent:.2f}%",
                "inline": True
            }
        ]

        # Add USD PnL if available
        if data.pnl_usd is not None:
            fields.append({
                "name": "💵 PnL USD",
                "value": f"${data.pnl_usd:,.2f}",
                "inline": True
            })

        # Add duration if available
        if data.duration_hours is not None:
            if data.duration_hours < 1:
                duration_text = f"{int(data.duration_hours * 60)}m"
            elif data.duration_hours < 24:
                duration_text = f"{data.duration_hours:.1f}h"
            else:
                duration_text = f"{data.duration_hours / 24:.1f}d"

            fields.append({
                "name": "⏱️ Duration",
                "value": duration_text,
                "inline": True
            })

        # Add close reason
        close_reasons = {
            "tp_all": "All TPs hit",
            "sl_hit": "Stop Loss",
            "manual": "Manual close",
            "signal_reversed": "Signal reversed"
        }
        fields.append({
            "name": "📋 Reason",
            "value": close_reasons.get(data.close_reason, data.close_reason),
            "inline": True
        })

        # Add TP hits if any
        if data.tp_hits:
            fields.append({
                "name": "🎯 TPs Hit",
                "value": ", ".join([f"TP{tp}" for tp in data.tp_hits]),
                "inline": False
            })

        embed = {
            "title": f"{direction_emoji} POSITION CLOSED - {data.symbol}",
            "description": f"**Signal #{data.signal_id} closed**",
            "color": self._create_embed_color(NotificationTrigger.SIGNAL_CLOSED, data.pnl_percent),
            "fields": fields,
            "timestamp": (data.timestamp or datetime.now()).isoformat(),
            "footer": {
                "text": f"Final PnL: {'+' if data.pnl_percent > 0 else ''}{data.pnl_percent:.2f}%"
            }
        }

        return embed

    def _format_error_embed(self, error: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Format error message as Discord rich embed"""
        fields = [
            {
                "name": "❌ Error",
                "value": error[:1024],  # Discord field value limit
                "inline": False
            }
        ]

        if context:
            context_text = "\n".join([f"**{k}**: {v}" for k, v in context.items()])
            if context_text:
                fields.append({
                    "name": "📋 Context",
                    "value": context_text[:1024],
                    "inline": False
                })

        embed = {
            "title": "⚠️ System Error",
            "description": "An error occurred in the trading system",
            "color": self._create_embed_color(NotificationTrigger.ERROR),
            "fields": fields,
            "timestamp": datetime.now().isoformat(),
            "footer": {
                "text": "KOMAS Trading System"
            }
        }

        return embed

    async def send_webhook(
        self,
        content: Optional[str] = None,
        embed: Optional[Dict] = None,
        embeds: Optional[list] = None
    ) -> NotificationResult:
        """Send webhook message to Discord"""
        if not self.settings.webhook_url:
            return NotificationResult(
                success=False,
                error="Webhook URL not configured"
            )

        try:
            payload = {}

            # Bot customization
            if self.settings.username:
                payload["username"] = self.settings.username
            if self.settings.avatar_url:
                payload["avatar_url"] = self.settings.avatar_url

            # Content
            if content:
                payload["content"] = content

            # Embeds
            if embed:
                payload["embeds"] = [embed]
            elif embeds:
                payload["embeds"] = embeds

            # Send webhook
            session = await self._get_session()
            async with session.post(self.settings.webhook_url, json=payload) as response:
                if response.status in (200, 204):
                    # Update stats
                    self._stats.total_sent += 1
                    self._stats.successful += 1
                    self._stats.last_sent = datetime.now()

                    logger.info(f"Discord webhook sent successfully")

                    return NotificationResult(
                        success=True,
                        message_id=None  # Discord webhooks don't return message ID by default
                    )
                else:
                    error_text = await response.text()
                    logger.error(f"Discord webhook failed: {response.status} - {error_text}")

                    # Update stats
                    self._stats.total_sent += 1
                    self._stats.failed += 1
                    self._stats.last_error = f"HTTP {response.status}: {error_text}"

                    return NotificationResult(
                        success=False,
                        error=f"HTTP {response.status}: {error_text}"
                    )

        except Exception as e:
            self._stats.total_sent += 1
            self._stats.failed += 1
            self._stats.last_error = str(e)

            logger.error(f"Failed to send Discord webhook: {e}")
            return NotificationResult(
                success=False,
                error=str(e)
            )

    async def send_test_notification(self) -> NotificationResult:
        """Send test notification"""
        embed = {
            "title": "✅ Test Notification",
            "description": "Discord webhook is configured correctly!",
            "color": 0x00FF00,
            "fields": [
                {
                    "name": "Status",
                    "value": "Connection successful",
                    "inline": True
                },
                {
                    "name": "Time",
                    "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "inline": True
                }
            ],
            "footer": {
                "text": "KOMAS Trading System"
            }
        }

        return await self.send_webhook(embed=embed)

    async def notify_new_signal(self, signal: SignalData) -> Optional[NotificationResult]:
        """Send new signal notification"""
        if not self.settings.enabled or not self.settings.notify_new_signal:
            return None

        if self.settings.use_rich_embeds:
            embed = self._format_signal_embed(signal)
            result = await self.send_webhook(embed=embed)
        else:
            # Simple text format
            content = f"🔔 **NEW SIGNAL** - {signal.direction} {signal.symbol}\n"
            content += f"Entry: {signal.entry_price:.8g} | SL: {signal.sl_price:.8g}"
            result = await self.send_webhook(content=content)

        # Update trigger stats
        if result.success:
            self._stats.by_trigger["new_signal"] = self._stats.by_trigger.get("new_signal", 0) + 1

        return result

    async def notify_tp_hit(self, data: TPHitData) -> Optional[NotificationResult]:
        """Send TP hit notification"""
        if not self.settings.enabled or not self.settings.notify_tp_hit:
            return None

        if self.settings.use_rich_embeds:
            embed = self._format_tp_hit_embed(data)
            result = await self.send_webhook(embed=embed)
        else:
            content = f"🎯 **TP{data.tp_level} HIT** - {data.symbol}\n"
            content += f"Profit: +{data.profit_percent:.2f}%"
            result = await self.send_webhook(content=content)

        # Update trigger stats
        if result.success:
            self._stats.by_trigger["tp_hit"] = self._stats.by_trigger.get("tp_hit", 0) + 1

        return result

    async def notify_sl_hit(self, data: SLHitData) -> Optional[NotificationResult]:
        """Send SL hit notification"""
        if not self.settings.enabled or not self.settings.notify_sl_hit:
            return None

        if self.settings.use_rich_embeds:
            embed = self._format_sl_hit_embed(data)
            result = await self.send_webhook(embed=embed)
        else:
            content = f"🛡️ **STOP LOSS** - {data.symbol}\n"
            content += f"Loss: -{data.loss_percent:.2f}%"
            result = await self.send_webhook(content=content)

        # Update trigger stats
        if result.success:
            self._stats.by_trigger["sl_hit"] = self._stats.by_trigger.get("sl_hit", 0) + 1

        return result

    async def notify_signal_closed(self, data: SignalClosedData) -> Optional[NotificationResult]:
        """Send signal closed notification"""
        if not self.settings.enabled or not self.settings.notify_signal_closed:
            return None

        if self.settings.use_rich_embeds:
            embed = self._format_closed_embed(data)
            result = await self.send_webhook(embed=embed)
        else:
            profit_sign = "+" if data.pnl_percent > 0 else ""
            content = f"📊 **POSITION CLOSED** - {data.symbol}\n"
            content += f"PnL: {profit_sign}{data.pnl_percent:.2f}%"
            result = await self.send_webhook(content=content)

        # Update trigger stats
        if result.success:
            self._stats.by_trigger["signal_closed"] = self._stats.by_trigger.get("signal_closed", 0) + 1

        return result

    async def notify_error(self, error: str, context: Optional[Dict] = None) -> Optional[NotificationResult]:
        """Send error notification"""
        if not self.settings.enabled or not self.settings.notify_errors:
            return None

        if self.settings.use_rich_embeds:
            embed = self._format_error_embed(error, context)
            result = await self.send_webhook(embed=embed)
        else:
            content = f"⚠️ **ERROR**: {error}"
            result = await self.send_webhook(content=content)

        # Update trigger stats
        if result.success:
            self._stats.by_trigger["error"] = self._stats.by_trigger.get("error", 0) + 1

        return result


# Global Discord notifier instance
_discord_notifier: Optional[DiscordNotifier] = None


def get_discord_notifier() -> DiscordNotifier:
    """Get global Discord notifier instance"""
    global _discord_notifier
    if _discord_notifier is None:
        _discord_notifier = DiscordNotifier()
    return _discord_notifier


def init_discord_notifier(settings: Optional[DiscordSettings] = None) -> DiscordNotifier:
    """Initialize global Discord notifier with settings"""
    global _discord_notifier
    _discord_notifier = DiscordNotifier(settings)
    return _discord_notifier
