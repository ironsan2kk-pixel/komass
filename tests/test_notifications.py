"""
Komas Trading Server - Telegram Notifications Tests
====================================================
Comprehensive tests for notification system
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

# Import modules to test
import sys
sys.path.insert(0, 'backend/app')

from core.notifications.models import (
    NotificationFormat,
    NotificationTrigger,
    TelegramSettings,
    SignalData,
    TPHitData,
    SLHitData,
    SignalClosedData,
    NotificationMessage,
    NotificationResult
)
from core.notifications.formatters import (
    SimpleFormatter,
    CornixFormatter,
    CustomFormatter,
    get_formatter,
    format_error_message,
    format_test_message
)
from core.notifications.telegram import (
    TelegramNotifier,
    get_notifier,
    init_notifier
)


# ============ FIXTURES ============

@pytest.fixture
def sample_signal():
    """Create sample signal for testing"""
    return SignalData(
        id=1,
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
        indicator_name="TRG",
        created_at=datetime.now()
    )


@pytest.fixture
def sample_tp_hit():
    """Create sample TP hit data"""
    return TPHitData(
        signal_id=1,
        symbol="BTCUSDT",
        direction="LONG",
        tp_level=1,
        tp_price=43500.0,
        entry_price=42500.0,
        profit_percent=2.35,
        amount_closed=50,
        remaining_position=50,
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_sl_hit():
    """Create sample SL hit data"""
    return SLHitData(
        signal_id=1,
        symbol="BTCUSDT",
        direction="LONG",
        sl_price=41000.0,
        entry_price=42500.0,
        loss_percent=-3.5,
        sl_mode="trailing",
        timestamp=datetime.now()
    )


@pytest.fixture
def sample_closed():
    """Create sample signal closed data"""
    return SignalClosedData(
        signal_id=1,
        symbol="BTCUSDT",
        direction="LONG",
        entry_price=42500.0,
        exit_price=44500.0,
        pnl_percent=4.7,
        pnl_usd=470.0,
        duration_hours=12.5,
        close_reason="tp_all",
        tp_hits=[1, 2],
        timestamp=datetime.now()
    )


@pytest.fixture
def default_settings():
    """Create default telegram settings"""
    return TelegramSettings(
        enabled=True,
        bot_token="test_token",
        chat_id="123456789",
        message_format=NotificationFormat.SIMPLE,
        notify_new_signal=True,
        notify_tp_hit=True,
        notify_sl_hit=True,
        notify_signal_closed=True,
        include_entry_zone=True,
        include_leverage=True,
        show_all_targets=True
    )


# ============ MODEL TESTS ============

class TestModels:
    """Test Pydantic models"""
    
    def test_telegram_settings_defaults(self):
        """Test default settings values"""
        settings = TelegramSettings()
        assert settings.enabled == False
        assert settings.message_format == NotificationFormat.SIMPLE
        assert settings.notify_new_signal == True
    
    def test_signal_data_serialization(self, sample_signal):
        """Test signal data can be serialized"""
        data = sample_signal.model_dump()
        assert data['symbol'] == 'BTCUSDT'
        assert data['direction'] == 'LONG'
        assert len(data['tp_targets']) == 4
    
    def test_notification_format_enum(self):
        """Test notification format enum values"""
        assert NotificationFormat.SIMPLE.value == 'simple'
        assert NotificationFormat.CORNIX.value == 'cornix'
        assert NotificationFormat.CUSTOM.value == 'custom'
    
    def test_notification_trigger_enum(self):
        """Test notification trigger enum values"""
        assert NotificationTrigger.NEW_SIGNAL.value == 'new_signal'
        assert NotificationTrigger.TP_HIT.value == 'tp_hit'
        assert NotificationTrigger.SL_HIT.value == 'sl_hit'
    
    def test_notification_result(self):
        """Test notification result model"""
        result = NotificationResult(success=True, message_id=12345)
        assert result.success == True
        assert result.message_id == 12345
        assert result.error is None


# ============ FORMATTER TESTS ============

class TestSimpleFormatter:
    """Test Simple message formatter"""
    
    def test_format_signal(self, sample_signal, default_settings):
        """Test signal formatting"""
        formatter = SimpleFormatter()
        notification = formatter.format_signal(sample_signal, default_settings)
        
        assert notification.trigger == NotificationTrigger.NEW_SIGNAL
        assert 'LONG BTCUSDT' in notification.body
        assert 'Entry Zone' in notification.body
        assert 'TP1' in notification.body
        assert 'Stop Loss' in notification.body
        assert 'Leverage: 10x' in notification.body
    
    def test_format_signal_short(self, default_settings):
        """Test SHORT signal formatting"""
        signal = SignalData(
            symbol="ETHUSDT",
            direction="SHORT",
            entry_price=2500.0,
            tp_targets=[2400.0, 2300.0],
            tp_amounts=[70, 30],
            sl_price=2600.0,
            leverage=5
        )
        
        formatter = SimpleFormatter()
        notification = formatter.format_signal(signal, default_settings)
        
        assert 'SHORT ETHUSDT' in notification.body
        assert notification.emoji == '📉'
    
    def test_format_tp_hit(self, sample_tp_hit, default_settings):
        """Test TP hit formatting"""
        formatter = SimpleFormatter()
        notification = formatter.format_tp_hit(sample_tp_hit, default_settings)
        
        assert notification.trigger == NotificationTrigger.TP_HIT
        assert 'TP1 reached' in notification.body
        assert 'Profit' in notification.body
        assert '+2.35%' in notification.body
    
    def test_format_sl_hit(self, sample_sl_hit, default_settings):
        """Test SL hit formatting"""
        formatter = SimpleFormatter()
        notification = formatter.format_sl_hit(sample_sl_hit, default_settings)
        
        assert notification.trigger == NotificationTrigger.SL_HIT
        assert 'STOP LOSS HIT' in notification.body
        assert 'Loss' in notification.body
    
    def test_format_signal_closed(self, sample_closed, default_settings):
        """Test signal closed formatting"""
        formatter = SimpleFormatter()
        notification = formatter.format_signal_closed(sample_closed, default_settings)
        
        assert notification.trigger == NotificationTrigger.SIGNAL_CLOSED
        assert 'SIGNAL CLOSED' in notification.body
        assert '+4.70%' in notification.body
        assert 'TP1, TP2' in notification.body


class TestCornixFormatter:
    """Test Cornix-compatible formatter"""
    
    def test_format_signal(self, sample_signal, default_settings):
        """Test Cornix signal format"""
        settings = default_settings.model_copy()
        settings.message_format = NotificationFormat.CORNIX
        
        formatter = CornixFormatter()
        notification = formatter.format_signal(sample_signal, settings)
        
        assert 'LONG BTCUSDT' in notification.body
        assert 'Entry:' in notification.body
        assert 'Targets:' in notification.body
        assert '1)' in notification.body  # Cornix numbering
        assert 'SL:' in notification.body
        assert 'Leverage:' in notification.body
        assert 'Exchange:' in notification.body
    
    def test_format_tp_hit(self, sample_tp_hit, default_settings):
        """Test Cornix TP format"""
        formatter = CornixFormatter()
        notification = formatter.format_tp_hit(sample_tp_hit, default_settings)
        
        assert 'Target 1 reached' in notification.body


class TestCustomFormatter:
    """Test custom template formatter"""
    
    def test_format_with_template(self, sample_signal, default_settings):
        """Test custom template formatting"""
        settings = default_settings.model_copy()
        settings.message_format = NotificationFormat.CUSTOM
        settings.custom_template = "🚀 {direction} {symbol} @ {entry_price}"
        
        formatter = CustomFormatter()
        notification = formatter.format_signal(sample_signal, settings)
        
        assert '🚀 LONG BTCUSDT @ 42500' in notification.body
    
    def test_format_without_template_fallback(self, sample_signal, default_settings):
        """Test fallback to Simple when no template"""
        settings = default_settings.model_copy()
        settings.message_format = NotificationFormat.CUSTOM
        settings.custom_template = ""
        
        formatter = CustomFormatter()
        notification = formatter.format_signal(sample_signal, settings)
        
        # Should fallback to Simple format
        assert 'NEW SIGNAL' in notification.body


class TestFormatterFactory:
    """Test formatter factory function"""
    
    def test_get_simple_formatter(self):
        """Test getting Simple formatter"""
        formatter = get_formatter(NotificationFormat.SIMPLE)
        assert isinstance(formatter, SimpleFormatter)
    
    def test_get_cornix_formatter(self):
        """Test getting Cornix formatter"""
        formatter = get_formatter(NotificationFormat.CORNIX)
        assert isinstance(formatter, CornixFormatter)
    
    def test_get_custom_formatter(self):
        """Test getting Custom formatter"""
        formatter = get_formatter(NotificationFormat.CUSTOM)
        assert isinstance(formatter, CustomFormatter)


class TestUtilityFormatters:
    """Test utility formatter functions"""
    
    def test_format_error_message(self):
        """Test error message formatting"""
        notification = format_error_message("Connection failed", {"host": "api.binance.com"})
        
        assert notification.trigger == NotificationTrigger.ERROR
        assert 'ERROR' in notification.body
        assert 'Connection failed' in notification.body
        assert 'host' in notification.body
    
    def test_format_test_message(self):
        """Test test message formatting"""
        message = format_test_message()
        
        assert 'KOMAS TRADING SERVER' in message
        assert 'successfully' in message
        assert '/start' in message


# ============ NOTIFIER TESTS ============

class TestTelegramNotifier:
    """Test Telegram notifier"""
    
    def test_init_with_settings(self, default_settings):
        """Test notifier initialization"""
        notifier = TelegramNotifier(default_settings)
        assert notifier.settings.enabled == True
        assert notifier.settings.bot_token == "test_token"
    
    def test_update_settings(self, default_settings):
        """Test settings update"""
        notifier = TelegramNotifier()
        notifier.update_settings(default_settings)
        assert notifier.settings.enabled == True
    
    def test_get_settings(self, default_settings):
        """Test get settings"""
        notifier = TelegramNotifier(default_settings)
        settings = notifier.get_settings()
        assert settings.enabled == True
    
    def test_get_stats(self):
        """Test get statistics"""
        notifier = TelegramNotifier()
        stats = notifier.get_stats()
        assert stats.total_sent == 0
        assert stats.successful == 0
    
    @pytest.mark.asyncio
    async def test_notify_disabled(self, sample_signal):
        """Test notification when disabled"""
        notifier = TelegramNotifier()
        notifier.settings.enabled = False
        
        result = await notifier.notify_new_signal(sample_signal)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_notify_trigger_disabled(self, sample_signal, default_settings):
        """Test notification when specific trigger disabled"""
        settings = default_settings.model_copy()
        settings.notify_new_signal = False
        
        notifier = TelegramNotifier(settings)
        result = await notifier.notify_new_signal(sample_signal)
        assert result is None


class TestGlobalNotifier:
    """Test global notifier functions"""
    
    def test_get_notifier(self):
        """Test get global notifier"""
        notifier = get_notifier()
        assert isinstance(notifier, TelegramNotifier)
    
    def test_init_notifier(self, default_settings):
        """Test initialize global notifier"""
        notifier = init_notifier(default_settings)
        assert notifier.settings.enabled == True


# ============ INTEGRATION TESTS ============

class TestIntegration:
    """Integration tests (require mocking)"""
    
    @pytest.mark.asyncio
    async def test_send_message_no_token(self):
        """Test send message without token"""
        notifier = TelegramNotifier()
        result = await notifier.send_message("Test")
        
        assert result.success == False
        assert "not configured" in result.error
    
    @pytest.mark.asyncio
    async def test_validate_bot_no_token(self):
        """Test validate bot without token"""
        notifier = TelegramNotifier()
        valid, info, error = await notifier.validate_bot()
        
        assert valid == False
        assert info is None
        assert "not configured" in error


# ============ RUN TESTS ============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
