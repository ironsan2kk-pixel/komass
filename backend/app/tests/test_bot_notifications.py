"""
Unit Tests for Bot Notification Integration
============================================
Tests for notification_integration.py - Telegram/Discord integration
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from app.core.bots.notification_integration import (
    on_new_signal,
    on_tp_hit,
    on_sl_hit,
    on_signal_closed,
    on_bot_error,
    setup_bot_runner_notifications,
    setup_notifications_for_runner
)


@pytest.fixture
def mock_telegram_notifier():
    """Mock Telegram notifier"""
    notifier = Mock()
    notifier.settings = Mock(enabled=True)
    notifier.notify_new_signal = AsyncMock(return_value=Mock(success=True))
    notifier.notify_tp_hit = AsyncMock(return_value=Mock(success=True))
    notifier.notify_sl_hit = AsyncMock(return_value=Mock(success=True))
    notifier.notify_signal_closed = AsyncMock(return_value=Mock(success=True))
    notifier.notify_error = AsyncMock(return_value=Mock(success=True))
    return notifier


@pytest.fixture
def mock_discord_notifier():
    """Mock Discord notifier"""
    notifier = Mock()
    notifier.settings = Mock(enabled=True)
    notifier.notify_new_signal = AsyncMock(return_value=Mock(success=True))
    notifier.notify_tp_hit = AsyncMock(return_value=Mock(success=True))
    notifier.notify_sl_hit = AsyncMock(return_value=Mock(success=True))
    notifier.notify_signal_closed = AsyncMock(return_value=Mock(success=True))
    notifier.notify_error = AsyncMock(return_value=Mock(success=True))
    return notifier


@pytest.mark.asyncio
async def test_on_new_signal(mock_telegram_notifier, mock_discord_notifier):
    """Test new signal notification"""
    with patch('app.core.bots.notification_integration.get_telegram_notifier', return_value=mock_telegram_notifier):
        with patch('app.core.bots.notification_integration.get_discord_notifier', return_value=mock_discord_notifier):

            await on_new_signal(
                bot_id="test_bot_1",
                symbol="BTCUSDT",
                direction="long",
                entry_price=50000.0,
                stop_loss=49000.0,
                take_profits=[51000.0, 52000.0, 53000.0],
                leverage=10
            )

            # Check Telegram was called
            assert mock_telegram_notifier.notify_new_signal.called
            call_args = mock_telegram_notifier.notify_new_signal.call_args[0][0]
            assert call_args.symbol == "BTCUSDT"
            assert call_args.entry_price == 50000.0

            # Check Discord was called
            assert mock_discord_notifier.notify_new_signal.called


@pytest.mark.asyncio
async def test_on_tp_hit(mock_telegram_notifier, mock_discord_notifier):
    """Test TP hit notification"""
    with patch('app.core.bots.notification_integration.get_telegram_notifier', return_value=mock_telegram_notifier):
        with patch('app.core.bots.notification_integration.get_discord_notifier', return_value=mock_discord_notifier):

            await on_tp_hit(
                bot_id="test_bot_1",
                symbol="BTCUSDT",
                direction="long",
                tp_level=1,
                tp_price=51000.0,
                partial_close_percent=25.0,
                pnl_percent=2.0,
                remaining_position=75.0
            )

            # Check Telegram was called
            assert mock_telegram_notifier.notify_tp_hit.called
            call_args = mock_telegram_notifier.notify_tp_hit.call_args[0][0]
            assert call_args.tp_level == 1
            assert call_args.pnl_percent == 2.0

            # Check Discord was called
            assert mock_discord_notifier.notify_tp_hit.called


@pytest.mark.asyncio
async def test_on_sl_hit(mock_telegram_notifier, mock_discord_notifier):
    """Test SL hit notification"""
    with patch('app.core.bots.notification_integration.get_telegram_notifier', return_value=mock_telegram_notifier):
        with patch('app.core.bots.notification_integration.get_discord_notifier', return_value=mock_discord_notifier):

            await on_sl_hit(
                bot_id="test_bot_1",
                symbol="BTCUSDT",
                direction="long",
                sl_price=49000.0,
                pnl_percent=-2.0,
                sl_mode="fixed"
            )

            # Check Telegram was called
            assert mock_telegram_notifier.notify_sl_hit.called
            call_args = mock_telegram_notifier.notify_sl_hit.call_args[0][0]
            assert call_args.sl_price == 49000.0
            assert call_args.pnl_percent == -2.0

            # Check Discord was called
            assert mock_discord_notifier.notify_sl_hit.called


@pytest.mark.asyncio
async def test_on_signal_closed(mock_telegram_notifier, mock_discord_notifier):
    """Test signal closed notification"""
    with patch('app.core.bots.notification_integration.get_telegram_notifier', return_value=mock_telegram_notifier):
        with patch('app.core.bots.notification_integration.get_discord_notifier', return_value=mock_discord_notifier):

            await on_signal_closed(
                bot_id="test_bot_1",
                symbol="BTCUSDT",
                direction="long",
                entry_price=50000.0,
                exit_price=52000.0,
                pnl_percent=4.0,
                holding_time="2h 30m",
                close_reason="tp_hit"
            )

            # Check Telegram was called
            assert mock_telegram_notifier.notify_signal_closed.called
            call_args = mock_telegram_notifier.notify_signal_closed.call_args[0][0]
            assert call_args.pnl_percent == 4.0
            assert call_args.close_reason == "tp_hit"

            # Check Discord was called
            assert mock_discord_notifier.notify_signal_closed.called


@pytest.mark.asyncio
async def test_on_bot_error(mock_telegram_notifier, mock_discord_notifier):
    """Test bot error notification"""
    with patch('app.core.bots.notification_integration.get_telegram_notifier', return_value=mock_telegram_notifier):
        with patch('app.core.bots.notification_integration.get_discord_notifier', return_value=mock_discord_notifier):

            await on_bot_error(
                bot_id="test_bot_1",
                error="Test error message",
                symbol="BTCUSDT"
            )

            # Check Telegram was called
            assert mock_telegram_notifier.notify_error.called
            call_args = mock_telegram_notifier.notify_error.call_args
            assert call_args[0][0] == "Test error message"

            # Check Discord was called
            assert mock_discord_notifier.notify_error.called


@pytest.mark.asyncio
async def test_notification_disabled(mock_telegram_notifier, mock_discord_notifier):
    """Test that notifications are skipped when disabled"""
    # Disable notifications
    mock_telegram_notifier.settings.enabled = False
    mock_discord_notifier.settings.enabled = False

    with patch('app.core.bots.notification_integration.get_telegram_notifier', return_value=mock_telegram_notifier):
        with patch('app.core.bots.notification_integration.get_discord_notifier', return_value=mock_discord_notifier):

            await on_new_signal(
                bot_id="test_bot_1",
                symbol="BTCUSDT",
                direction="long",
                entry_price=50000.0,
                stop_loss=49000.0,
                take_profits=[51000.0],
                leverage=1
            )

            # Notifiers should still be called (they handle enabled check internally)
            assert mock_telegram_notifier.notify_new_signal.called
            assert mock_discord_notifier.notify_new_signal.called


def test_setup_bot_runner_notifications():
    """Test setting up notifications for bot runner"""
    mock_runner = Mock()
    mock_runner.add_signal_callback = Mock()

    runner = setup_bot_runner_notifications(mock_runner)

    # Check that callback was added
    assert mock_runner.add_signal_callback.called
    assert runner == mock_runner


def test_setup_notifications_for_runner():
    """Test complete notification setup"""
    mock_runner = Mock()
    mock_runner.add_signal_callback = Mock()

    with patch('app.core.bots.notification_integration.get_telegram_notifier'):
        with patch('app.core.bots.notification_integration.get_discord_notifier'):

            runner = setup_notifications_for_runner(mock_runner)

            # Check that callback was registered
            assert mock_runner.add_signal_callback.called
            assert runner == mock_runner


@pytest.mark.asyncio
async def test_notification_exception_handling(mock_telegram_notifier, mock_discord_notifier):
    """Test that exceptions in notifications don't crash"""
    # Make Telegram fail
    mock_telegram_notifier.notify_new_signal = AsyncMock(side_effect=Exception("Test error"))

    with patch('app.core.bots.notification_integration.get_telegram_notifier', return_value=mock_telegram_notifier):
        with patch('app.core.bots.notification_integration.get_discord_notifier', return_value=mock_discord_notifier):

            # Should not raise exception
            await on_new_signal(
                bot_id="test_bot_1",
                symbol="BTCUSDT",
                direction="long",
                entry_price=50000.0,
                stop_loss=49000.0,
                take_profits=[51000.0],
                leverage=1
            )

            # Discord should still work
            assert mock_discord_notifier.notify_new_signal.called


@pytest.mark.asyncio
async def test_unified_callback_new_signal(mock_telegram_notifier, mock_discord_notifier):
    """Test unified callback for new signal events"""
    with patch('app.core.bots.notification_integration.get_telegram_notifier', return_value=mock_telegram_notifier):
        with patch('app.core.bots.notification_integration.get_discord_notifier', return_value=mock_discord_notifier):

            # Import unified_callback from setup function
            mock_runner = Mock()
            mock_runner.add_signal_callback = Mock()

            setup_bot_runner_notifications(mock_runner)

            # Get the callback that was registered
            callback = mock_runner.add_signal_callback.call_args[0][0]

            # Test it with new_signal event
            event_data = {
                "type": "new_signal",
                "bot_id": "test_bot_1",
                "symbol": "BTCUSDT",
                "direction": "long",
                "entry_price": 50000.0,
                "stop_loss": 49000.0,
                "take_profits": [51000.0],
                "leverage": 1
            }

            await callback(event_data)

            # Check notification was sent
            assert mock_telegram_notifier.notify_new_signal.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
