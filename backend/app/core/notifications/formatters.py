"""
Komas Trading Server - Message Formatters
==========================================
Format messages for different notification styles
"""
from typing import Optional
from datetime import datetime

from .models import (
    NotificationFormat,
    NotificationTrigger,
    NotificationMessage,
    SignalData,
    TPHitData,
    SLHitData,
    SignalClosedData,
    TelegramSettings
)


class BaseFormatter:
    """Base class for message formatters"""
    
    def format_signal(self, signal: SignalData, settings: TelegramSettings) -> NotificationMessage:
        raise NotImplementedError
    
    def format_tp_hit(self, data: TPHitData, settings: TelegramSettings) -> NotificationMessage:
        raise NotImplementedError
    
    def format_sl_hit(self, data: SLHitData, settings: TelegramSettings) -> NotificationMessage:
        raise NotImplementedError
    
    def format_signal_closed(self, data: SignalClosedData, settings: TelegramSettings) -> NotificationMessage:
        raise NotImplementedError


class SimpleFormatter(BaseFormatter):
    """Simple text format for messages"""
    
    def format_signal(self, signal: SignalData, settings: TelegramSettings) -> NotificationMessage:
        """Format new signal message - Simple style"""
        emoji = "📈" if signal.direction == "LONG" else "📉"
        direction_emoji = "🟢" if signal.direction == "LONG" else "🔴"
        
        lines = [
            f"{emoji} <b>NEW SIGNAL</b> {emoji}",
            "",
            f"{direction_emoji} <b>{signal.direction} {signal.symbol}</b>",
            "",
        ]
        
        # Entry zone
        if settings.include_entry_zone and signal.entry_zone_low and signal.entry_zone_high:
            lines.append(f"📍 Entry Zone: {signal.entry_zone_low:.4f} - {signal.entry_zone_high:.4f}")
        else:
            lines.append(f"📍 Entry: {signal.entry_price:.4f}")
        
        # Targets
        if signal.tp_targets:
            lines.append("")
            lines.append("🎯 <b>Targets:</b>")
            for i, tp in enumerate(signal.tp_targets, 1):
                if settings.show_all_targets or i <= 4:
                    percent = ((tp - signal.entry_price) / signal.entry_price * 100)
                    if signal.direction == "SHORT":
                        percent = -percent
                    amount = signal.tp_amounts[i-1] if i <= len(signal.tp_amounts) else 0
                    lines.append(f"  TP{i}: {tp:.4f} ({percent:+.2f}%) [{amount:.0f}%]")
        
        # Stop Loss
        sl_percent = ((signal.sl_price - signal.entry_price) / signal.entry_price * 100)
        if signal.direction == "SHORT":
            sl_percent = -sl_percent
        lines.append("")
        lines.append(f"🛑 Stop Loss: {signal.sl_price:.4f} ({sl_percent:.2f}%)")
        
        # Leverage
        if settings.include_leverage and signal.leverage > 1:
            lines.append(f"⚡ Leverage: {signal.leverage}x")
        
        # Footer
        lines.append("")
        lines.append(f"📊 {signal.indicator_name} | {signal.timeframe} | {signal.exchange.upper()}")
        
        return NotificationMessage(
            trigger=NotificationTrigger.NEW_SIGNAL,
            title=f"New {signal.direction} Signal",
            body="\n".join(lines),
            emoji=emoji,
            parse_mode="HTML",
            raw_data=signal.model_dump()
        )
    
    def format_tp_hit(self, data: TPHitData, settings: TelegramSettings) -> NotificationMessage:
        """Format TP hit message - Simple style"""
        emoji = "🎯"
        direction_emoji = "🟢" if data.direction == "LONG" else "🔴"
        
        lines = [
            f"{emoji} <b>TARGET HIT!</b> {emoji}",
            "",
            f"{direction_emoji} <b>{data.symbol}</b>",
            "",
            f"✅ TP{data.tp_level} reached at {data.tp_price:.4f}",
            f"💰 Profit: <b>+{data.profit_percent:.2f}%</b>",
            f"📦 Closed: {data.amount_closed:.0f}% of position",
            f"📊 Remaining: {data.remaining_position:.0f}%",
        ]
        
        return NotificationMessage(
            trigger=NotificationTrigger.TP_HIT,
            title=f"TP{data.tp_level} Hit",
            body="\n".join(lines),
            emoji=emoji,
            parse_mode="HTML",
            raw_data=data.model_dump()
        )
    
    def format_sl_hit(self, data: SLHitData, settings: TelegramSettings) -> NotificationMessage:
        """Format SL hit message - Simple style"""
        emoji = "🛑"
        
        lines = [
            f"{emoji} <b>STOP LOSS HIT</b> {emoji}",
            "",
            f"🔴 <b>{data.symbol}</b>",
            "",
            f"❌ SL triggered at {data.sl_price:.4f}",
            f"💸 Loss: <b>{data.loss_percent:.2f}%</b>",
            f"📊 Mode: {data.sl_mode}",
        ]
        
        return NotificationMessage(
            trigger=NotificationTrigger.SL_HIT,
            title="Stop Loss Hit",
            body="\n".join(lines),
            emoji=emoji,
            parse_mode="HTML",
            raw_data=data.model_dump()
        )
    
    def format_signal_closed(self, data: SignalClosedData, settings: TelegramSettings) -> NotificationMessage:
        """Format signal closed message - Simple style"""
        is_profit = data.pnl_percent >= 0
        emoji = "✅" if is_profit else "❌"
        pnl_emoji = "💰" if is_profit else "💸"
        
        lines = [
            f"{emoji} <b>SIGNAL CLOSED</b> {emoji}",
            "",
            f"<b>{data.symbol}</b> ({data.direction})",
            "",
            f"📍 Entry: {data.entry_price:.4f}",
            f"📍 Exit: {data.exit_price:.4f}",
            f"{pnl_emoji} PnL: <b>{data.pnl_percent:+.2f}%</b>",
        ]
        
        if data.pnl_usd:
            lines.append(f"💵 PnL: ${data.pnl_usd:+.2f}")
        
        if data.duration_hours:
            if data.duration_hours < 1:
                duration_str = f"{int(data.duration_hours * 60)}m"
            elif data.duration_hours < 24:
                duration_str = f"{data.duration_hours:.1f}h"
            else:
                duration_str = f"{data.duration_hours / 24:.1f}d"
            lines.append(f"⏱️ Duration: {duration_str}")
        
        if data.tp_hits:
            tp_str = ", ".join([f"TP{tp}" for tp in data.tp_hits])
            lines.append(f"🎯 Hits: {tp_str}")
        
        lines.append(f"📋 Reason: {data.close_reason}")
        
        return NotificationMessage(
            trigger=NotificationTrigger.SIGNAL_CLOSED,
            title="Signal Closed",
            body="\n".join(lines),
            emoji=emoji,
            parse_mode="HTML",
            raw_data=data.model_dump()
        )


class CornixFormatter(BaseFormatter):
    """Cornix-compatible format for signals"""
    
    def format_signal(self, signal: SignalData, settings: TelegramSettings) -> NotificationMessage:
        """Format new signal message - Cornix style
        
        Output format:
        #NEAR/USDT 30m
        Long Entry: 1.545
        
         Winrate: 79%
        Targets:
        Target 1: 1.557
        Target 2: 1.576
        Stop-Loss: 1.499
        
        💡 Leverage: 10x Cross.
        """
        # Format symbol with / separator (BTCUSDT -> BTC/USDT)
        symbol = signal.symbol
        if symbol.endswith("USDT"):
            symbol = symbol[:-4] + "/USDT"
        elif symbol.endswith("USD"):
            symbol = symbol[:-3] + "/USD"
        
        direction = "Long" if signal.direction.upper() == "LONG" else "Short"
        timeframe = signal.timeframe or "1h"
        
        lines = [
            f"#{symbol} {timeframe}",
            f"{direction} Entry: {signal.entry_price:.4f}",
            ""
        ]
        
        # Add winrate if available
        if signal.winrate:
            lines.append(f" Winrate: {signal.winrate}%")
        
        # Targets
        lines.append("Targets:")
        if signal.tp_targets:
            for i, tp in enumerate(signal.tp_targets, 1):
                lines.append(f"Target {i}: {tp:.4f}")
        
        # Stop Loss
        lines.append(f"Stop-Loss: {signal.sl_price:.4f}")
        
        # Leverage
        if settings.include_leverage and signal.leverage > 1:
            lines.extend(["", f"💡 Leverage: {signal.leverage}x Cross."])
        
        return NotificationMessage(
            trigger=NotificationTrigger.NEW_SIGNAL,
            title=f"{direction} {symbol}",
            body="\n".join(lines),
            emoji="📈" if signal.direction.upper() == "LONG" else "📉",
            parse_mode=None,  # Plain text for Cornix
            raw_data=signal.model_dump()
        )
    
    def format_tp_hit(self, data: TPHitData, settings: TelegramSettings) -> NotificationMessage:
        """Format TP hit - Cornix style update"""
        lines = [
            f"🎯 <b>Target {data.tp_level} reached</b>",
            "",
            f"{data.symbol}",
            f"Price: {data.tp_price:.4f}",
            f"Profit: +{data.profit_percent:.2f}%",
        ]
        
        return NotificationMessage(
            trigger=NotificationTrigger.TP_HIT,
            title=f"Target {data.tp_level}",
            body="\n".join(lines),
            emoji="🎯",
            parse_mode="HTML",
            raw_data=data.model_dump()
        )
    
    def format_sl_hit(self, data: SLHitData, settings: TelegramSettings) -> NotificationMessage:
        """Format SL hit - Cornix style"""
        lines = [
            f"🛑 <b>Stop Loss reached</b>",
            "",
            f"{data.symbol}",
            f"Price: {data.sl_price:.4f}",
            f"Loss: {data.loss_percent:.2f}%",
        ]
        
        return NotificationMessage(
            trigger=NotificationTrigger.SL_HIT,
            title="Stop Loss",
            body="\n".join(lines),
            emoji="🛑",
            parse_mode="HTML",
            raw_data=data.model_dump()
        )
    
    def format_signal_closed(self, data: SignalClosedData, settings: TelegramSettings) -> NotificationMessage:
        """Format signal closed - Cornix style"""
        is_profit = data.pnl_percent >= 0
        emoji = "✅" if is_profit else "❌"
        
        lines = [
            f"{emoji} <b>Trade Closed</b>",
            "",
            f"{data.symbol}",
            f"Entry: {data.entry_price:.4f}",
            f"Exit: {data.exit_price:.4f}",
            f"PnL: {data.pnl_percent:+.2f}%",
        ]
        
        return NotificationMessage(
            trigger=NotificationTrigger.SIGNAL_CLOSED,
            title="Trade Closed",
            body="\n".join(lines),
            emoji=emoji,
            parse_mode="HTML",
            raw_data=data.model_dump()
        )


class CustomFormatter(BaseFormatter):
    """Custom template-based formatter"""
    
    def __init__(self, template: str = ""):
        self.template = template
    
    def _apply_template(self, template: str, data: dict) -> str:
        """Apply template with data substitution"""
        result = template
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                if isinstance(value, float):
                    result = result.replace(placeholder, f"{value:.4f}")
                elif isinstance(value, list):
                    result = result.replace(placeholder, ", ".join(map(str, value)))
                else:
                    result = result.replace(placeholder, str(value))
        return result
    
    def format_signal(self, signal: SignalData, settings: TelegramSettings) -> NotificationMessage:
        """Format using custom template or fallback to Simple"""
        if settings.custom_template:
            body = self._apply_template(settings.custom_template, signal.model_dump())
            return NotificationMessage(
                trigger=NotificationTrigger.NEW_SIGNAL,
                title=f"New {signal.direction} Signal",
                body=body,
                emoji="📈" if signal.direction == "LONG" else "📉",
                parse_mode="HTML",
                raw_data=signal.model_dump()
            )
        # Fallback to Simple
        return SimpleFormatter().format_signal(signal, settings)
    
    def format_tp_hit(self, data: TPHitData, settings: TelegramSettings) -> NotificationMessage:
        return SimpleFormatter().format_tp_hit(data, settings)
    
    def format_sl_hit(self, data: SLHitData, settings: TelegramSettings) -> NotificationMessage:
        return SimpleFormatter().format_sl_hit(data, settings)
    
    def format_signal_closed(self, data: SignalClosedData, settings: TelegramSettings) -> NotificationMessage:
        return SimpleFormatter().format_signal_closed(data, settings)


def get_formatter(format_type: NotificationFormat) -> BaseFormatter:
    """Factory function to get the appropriate formatter"""
    formatters = {
        NotificationFormat.SIMPLE: SimpleFormatter,
        NotificationFormat.CORNIX: CornixFormatter,
        NotificationFormat.CUSTOM: CustomFormatter,
    }
    return formatters.get(format_type, SimpleFormatter)()


def format_error_message(error: str, context: Optional[dict] = None) -> NotificationMessage:
    """Format error notification"""
    lines = [
        "⚠️ <b>ERROR</b> ⚠️",
        "",
        f"❌ {error}",
    ]
    
    if context:
        lines.append("")
        lines.append("<b>Context:</b>")
        for key, value in context.items():
            lines.append(f"• {key}: {value}")
    
    lines.append("")
    lines.append(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return NotificationMessage(
        trigger=NotificationTrigger.ERROR,
        title="Error",
        body="\n".join(lines),
        emoji="⚠️",
        parse_mode="HTML",
        raw_data={"error": error, "context": context}
    )


def format_test_message() -> str:
    """Format test notification message"""
    return """🔔 <b>KOMAS TRADING SERVER</b> 🔔

✅ Telegram notifications configured successfully!

📊 You will receive:
• 📈 New trading signals
• 🎯 Take Profit notifications
• 🛑 Stop Loss alerts
• ✅ Position closed updates

🤖 Bot Commands:
/start - Welcome message
/status - System status
/signals - Active signals
/stop - Pause notifications

⏰ {timestamp}""".format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
