"""
Komas Trading Server - Telegram Client
======================================
Telegram Bot integration for notifications
"""
import asyncio
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import json

from telegram import Bot, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from telegram.error import TelegramError

from .models import (
    TelegramSettings,
    NotificationResult,
    NotificationMessage,
    SignalData,
    TPHitData,
    SLHitData,
    SignalClosedData,
    TelegramBotInfo,
    NotificationStats,
    NotificationTrigger
)
from .formatters import (
    get_formatter,
    format_error_message,
    format_test_message
)


logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Telegram notification client"""
    
    def __init__(self, settings: Optional[TelegramSettings] = None):
        self.settings = settings or TelegramSettings()
        self._bot: Optional[Bot] = None
        self._app: Optional[Application] = None
        self._running = False
        
        # Statistics
        self._stats = NotificationStats()
        
        # Settings file path
        self._settings_file = Path(__file__).parent.parent.parent.parent / "data" / "telegram_settings.json"
        
        # Load saved settings
        self._load_settings()
    
    def _load_settings(self):
        """Load settings from file"""
        try:
            if self._settings_file.exists():
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.settings = TelegramSettings(**data)
                    logger.info("Telegram settings loaded from file")
        except Exception as e:
            logger.warning(f"Failed to load telegram settings: {e}")
    
    def _save_settings(self):
        """Save settings to file"""
        try:
            self._settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings.model_dump(), f, indent=2, default=str)
            logger.info("Telegram settings saved to file")
        except Exception as e:
            logger.error(f"Failed to save telegram settings: {e}")
    
    def update_settings(self, settings: TelegramSettings):
        """Update notification settings"""
        self.settings = settings
        self._save_settings()
        
        # Reinitialize bot if token changed
        if settings.bot_token and settings.bot_token != getattr(self._bot, 'token', ''):
            self._bot = None
    
    def get_settings(self) -> TelegramSettings:
        """Get current settings"""
        return self.settings
    
    def get_stats(self) -> NotificationStats:
        """Get notification statistics"""
        return self._stats
    
    def _get_bot(self) -> Optional[Bot]:
        """Get or create bot instance"""
        if not self.settings.bot_token:
            return None
        
        if self._bot is None:
            try:
                self._bot = Bot(token=self.settings.bot_token)
            except Exception as e:
                logger.error(f"Failed to create bot: {e}")
                return None
        
        return self._bot
    
    async def validate_bot(self) -> tuple[bool, Optional[TelegramBotInfo], Optional[str]]:
        """Validate bot token and get bot info"""
        bot = self._get_bot()
        if not bot:
            return False, None, "Bot token not configured"
        
        try:
            me = await bot.get_me()
            info = TelegramBotInfo(
                id=me.id,
                username=me.username or "",
                first_name=me.first_name,
                can_join_groups=me.can_join_groups or False,
                can_read_all_group_messages=me.can_read_all_group_messages or False,
                supports_inline_queries=me.supports_inline_queries or False
            )
            return True, info, None
        except TelegramError as e:
            return False, None, str(e)
    
    async def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: Optional[str] = "HTML",
        disable_notification: bool = False
    ) -> NotificationResult:
        """Send a text message"""
        bot = self._get_bot()
        if not bot:
            return NotificationResult(
                success=False,
                error="Bot not configured"
            )
        
        target_chat = chat_id or self.settings.chat_id
        if not target_chat:
            return NotificationResult(
                success=False,
                error="Chat ID not configured"
            )
        
        try:
            message = await bot.send_message(
                chat_id=target_chat,
                text=text,
                parse_mode=parse_mode,  # None = plain text
                disable_notification=disable_notification
            )
            
            # Update stats
            self._stats.total_sent += 1
            self._stats.successful += 1
            self._stats.last_sent = datetime.now()
            
            logger.info(f"Message sent to {target_chat}: {message.message_id}")
            
            return NotificationResult(
                success=True,
                message_id=message.message_id
            )
            
        except TelegramError as e:
            self._stats.total_sent += 1
            self._stats.failed += 1
            self._stats.last_error = str(e)
            
            logger.error(f"Failed to send message: {e}")
            return NotificationResult(
                success=False,
                error=str(e)
            )
    
    async def send_notification(self, notification: NotificationMessage) -> NotificationResult:
        """Send a formatted notification"""
        result = await self.send_message(
            text=notification.body,
            parse_mode=notification.parse_mode
        )
        
        # Update trigger stats
        trigger_key = notification.trigger.value
        if trigger_key in self._stats.by_trigger:
            self._stats.by_trigger[trigger_key] += 1
        
        return result
    
    async def send_test_notification(self) -> NotificationResult:
        """Send test notification"""
        text = format_test_message()
        return await self.send_message(text)
    
    async def notify_new_signal(self, signal: SignalData) -> Optional[NotificationResult]:
        """Send new signal notification"""
        if not self.settings.enabled or not self.settings.notify_new_signal:
            return None
        
        formatter = get_formatter(self.settings.message_format)
        notification = formatter.format_signal(signal, self.settings)
        return await self.send_notification(notification)
    
    async def notify_tp_hit(self, data: TPHitData) -> Optional[NotificationResult]:
        """Send TP hit notification"""
        if not self.settings.enabled or not self.settings.notify_tp_hit:
            return None
        
        formatter = get_formatter(self.settings.message_format)
        notification = formatter.format_tp_hit(data, self.settings)
        return await self.send_notification(notification)
    
    async def notify_sl_hit(self, data: SLHitData) -> Optional[NotificationResult]:
        """Send SL hit notification"""
        if not self.settings.enabled or not self.settings.notify_sl_hit:
            return None
        
        formatter = get_formatter(self.settings.message_format)
        notification = formatter.format_sl_hit(data, self.settings)
        return await self.send_notification(notification)
    
    async def notify_signal_closed(self, data: SignalClosedData) -> Optional[NotificationResult]:
        """Send signal closed notification"""
        if not self.settings.enabled or not self.settings.notify_signal_closed:
            return None
        
        formatter = get_formatter(self.settings.message_format)
        notification = formatter.format_signal_closed(data, self.settings)
        return await self.send_notification(notification)
    
    async def notify_error(self, error: str, context: Optional[dict] = None) -> Optional[NotificationResult]:
        """Send error notification"""
        if not self.settings.enabled or not self.settings.notify_errors:
            return None
        
        notification = format_error_message(error, context)
        return await self.send_notification(notification)
    
    # ============ BOT COMMANDS ============
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        await update.message.reply_text(
            "🤖 <b>KOMAS Trading Server Bot</b>\n\n"
            "Welcome! I'll send you trading signals and updates.\n\n"
            "📋 <b>Commands:</b>\n"
            "/status - System status\n"
            "/signals - Active signals\n"
            "/stop - Pause notifications\n"
            "/start - Resume notifications\n\n"
            "🔔 Notifications are now <b>enabled</b>",
            parse_mode="HTML"
        )
        
        # Save chat ID
        chat_id = str(update.effective_chat.id)
        if chat_id != self.settings.chat_id:
            self.settings.chat_id = chat_id
            self._save_settings()
            logger.info(f"Chat ID saved: {chat_id}")
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command"""
        stats = self._stats
        
        await update.message.reply_text(
            "📊 <b>System Status</b>\n\n"
            f"✅ Notifications: {'Enabled' if self.settings.enabled else 'Disabled'}\n"
            f"📝 Format: {self.settings.message_format.value}\n\n"
            f"📈 <b>Statistics:</b>\n"
            f"• Total sent: {stats.total_sent}\n"
            f"• Successful: {stats.successful}\n"
            f"• Failed: {stats.failed}\n"
            f"• Last sent: {stats.last_sent.strftime('%Y-%m-%d %H:%M') if stats.last_sent else 'Never'}\n\n"
            f"🎯 <b>By Type:</b>\n"
            f"• Signals: {stats.by_trigger.get('new_signal', 0)}\n"
            f"• TP Hits: {stats.by_trigger.get('tp_hit', 0)}\n"
            f"• SL Hits: {stats.by_trigger.get('sl_hit', 0)}\n"
            f"• Closed: {stats.by_trigger.get('signal_closed', 0)}",
            parse_mode="HTML"
        )
    
    async def _cmd_signals(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /signals command"""
        # This would be connected to signals API in real implementation
        await update.message.reply_text(
            "📋 <b>Active Signals</b>\n\n"
            "No active signals at the moment.\n\n"
            "You'll be notified when new signals appear.",
            parse_mode="HTML"
        )
    
    async def _cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stop command"""
        self.settings.enabled = False
        self._save_settings()
        
        await update.message.reply_text(
            "🔕 Notifications <b>paused</b>\n\n"
            "Use /start to resume notifications.",
            parse_mode="HTML"
        )
    
    def setup_handlers(self, app: Application):
        """Setup bot command handlers"""
        app.add_handler(CommandHandler("start", self._cmd_start))
        app.add_handler(CommandHandler("status", self._cmd_status))
        app.add_handler(CommandHandler("signals", self._cmd_signals))
        app.add_handler(CommandHandler("stop", self._cmd_stop))
    
    async def start_bot_polling(self):
        """Start bot in polling mode (for development)"""
        if not self.settings.bot_token:
            logger.warning("Cannot start bot: no token configured")
            return
        
        try:
            self._app = Application.builder().token(self.settings.bot_token).build()
            self.setup_handlers(self._app)
            
            await self._app.initialize()
            await self._app.start()
            await self._app.updater.start_polling()
            
            self._running = True
            logger.info("Telegram bot started in polling mode")
            
        except Exception as e:
            logger.error(f"Failed to start bot: {e}")
    
    async def stop_bot(self):
        """Stop bot"""
        if self._app and self._running:
            await self._app.updater.stop()
            await self._app.stop()
            await self._app.shutdown()
            self._running = False
            logger.info("Telegram bot stopped")


# Global notifier instance
_notifier: Optional[TelegramNotifier] = None


def get_notifier() -> TelegramNotifier:
    """Get global notifier instance"""
    global _notifier
    if _notifier is None:
        _notifier = TelegramNotifier()
    return _notifier


def init_notifier(settings: Optional[TelegramSettings] = None) -> TelegramNotifier:
    """Initialize global notifier with settings"""
    global _notifier
    _notifier = TelegramNotifier(settings)
    return _notifier
