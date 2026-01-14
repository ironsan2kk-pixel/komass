"""
Integration Tests for Bot Runner System
========================================
End-to-end tests for complete bot runner with data and notifications
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import tempfile
import shutil
import pandas as pd

from app.core.bots import get_bots_runner, get_bots_manager
from app.core.bots.data_integration import create_runner_data_fetcher
from app.core.bots.notification_integration import setup_notifications_for_runner
from app.core.bots.models import BotCreate, BotConfig, BotSymbolConfig, StrategyConfig


@pytest.fixture
def temp_bot_dir():
    """Create temporary bot storage directory"""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory with test OHLCV"""
    temp_dir = Path(tempfile.mkdtemp())

    # Create test data with enough candles for indicator calculation
    dates = pd.date_range(start='2024-01-01', periods=300, freq='1h')
    df = pd.DataFrame({
        'open': [50000.0 + i * 10 for i in range(300)],
        'high': [50100.0 + i * 10 for i in range(300)],
        'low': [49900.0 + i * 10 for i in range(300)],
        'close': [50000.0 + i * 10 for i in range(300)],
        'volume': [1000000.0] * 300
    }, index=dates)

    df.to_parquet(temp_dir / "BTCUSDT_1h.parquet")
    df.to_parquet(temp_dir / "ETHUSDT_1h.parquet")

    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_runner_initialization():
    """Test runner can be initialized"""
    runner = get_bots_runner()

    assert runner is not None
    assert not runner.is_running()


def test_runner_with_data_fetcher(temp_data_dir):
    """Test runner can fetch data successfully"""
    runner = get_bots_runner()

    # Setup data fetcher
    data_fetcher = create_runner_data_fetcher(data_dir=temp_data_dir)
    runner.set_data_fetcher(data_fetcher)

    # Test data fetch
    candles = data_fetcher("BTCUSDT", "1h")

    assert len(candles) > 0
    assert len(candles) >= 100  # Should have enough data for indicators


def test_manager_create_bot(temp_bot_dir):
    """Test creating a bot through manager"""
    from app.core.bots.manager import BotsManager

    manager = BotsManager(data_dir=str(temp_bot_dir))

    bot_config = BotConfig(
        name="Test Bot",
        description="Integration test bot",
        mode="paper",
        initial_capital=10000.0,
        symbols=[
            BotSymbolConfig(
                symbol="BTCUSDT",
                enabled=True,
                timeframe="1h",
                position_size_percent=10.0
            )
        ],
        strategy=StrategyConfig(
            atr_length=45,
            multiplier=4.0,
            tp_count=3,
            sl_percent=2.0
        )
    )

    bot = manager.create_bot(BotCreate(config=bot_config))

    assert bot is not None
    assert bot.config.name == "Test Bot"
    assert bot.status.value == "stopped"
    assert bot.current_capital == 10000.0


def test_manager_start_stop_bot(temp_bot_dir):
    """Test starting and stopping a bot"""
    from app.core.bots.manager import BotsManager

    manager = BotsManager(data_dir=str(temp_bot_dir))

    bot_config = BotConfig(
        name="Test Bot",
        description="Test",
        mode="paper",
        initial_capital=1000.0,
        symbols=[BotSymbolConfig(symbol="BTCUSDT", enabled=True, timeframe="1h")],
        strategy=StrategyConfig()
    )

    bot = manager.create_bot(BotCreate(config=bot_config))

    # Start bot
    bot = manager.start_bot(bot.id)
    assert bot.status.value == "running"

    # Stop bot
    bot = manager.stop_bot(bot.id)
    assert bot.status.value == "stopped"


def test_manager_persistence(temp_bot_dir):
    """Test that bots are persisted to disk"""
    from app.core.bots.manager import BotsManager

    # Create bot with first manager instance
    manager1 = BotsManager(data_dir=str(temp_bot_dir))

    bot_config = BotConfig(
        name="Persistent Bot",
        description="Test persistence",
        mode="paper",
        initial_capital=5000.0,
        symbols=[BotSymbolConfig(symbol="BTCUSDT", enabled=True, timeframe="1h")],
        strategy=StrategyConfig()
    )

    bot1 = manager1.create_bot(BotCreate(config=bot_config))
    bot_id = bot1.id

    # Create new manager instance (simulates restart)
    manager2 = BotsManager(data_dir=str(temp_bot_dir))

    # Check bot was loaded
    bot2 = manager2.get_bot(bot_id)

    assert bot2 is not None
    assert bot2.id == bot_id
    assert bot2.config.name == "Persistent Bot"
    assert bot2.current_capital == 5000.0


def test_runner_start_stop():
    """Test runner can start and stop"""
    runner = get_bots_runner()

    # Start
    runner.start()
    assert runner.is_running()

    # Stop
    runner.stop()
    assert not runner.is_running()


@pytest.mark.asyncio
async def test_notification_integration():
    """Test notification setup doesn't crash"""
    runner = get_bots_runner()

    with patch('app.core.bots.notification_integration.get_telegram_notifier'):
        with patch('app.core.bots.notification_integration.get_discord_notifier'):

            # Setup notifications
            runner = setup_notifications_for_runner(runner)

            # Should not crash
            assert runner is not None


def test_full_integration_flow(temp_bot_dir, temp_data_dir):
    """Test complete flow: create bot, setup runner, start"""
    from app.core.bots.manager import BotsManager

    # Create manager and runner
    manager = BotsManager(data_dir=str(temp_bot_dir))
    runner = get_bots_runner()

    # Setup data fetcher
    data_fetcher = create_runner_data_fetcher(data_dir=temp_data_dir)
    runner.set_data_fetcher(data_fetcher)

    # Create bot
    bot_config = BotConfig(
        name="Integration Test Bot",
        description="Full flow test",
        mode="paper",
        initial_capital=10000.0,
        symbols=[
            BotSymbolConfig(
                symbol="BTCUSDT",
                enabled=True,
                timeframe="1h",
                position_size_percent=10.0
            )
        ],
        strategy=StrategyConfig(
            atr_length=45,
            multiplier=4.0
        )
    )

    bot = manager.create_bot(BotCreate(config=bot_config))

    # Start bot
    bot = manager.start_bot(bot.id)
    assert bot.status.value == "running"

    # Start runner
    runner.start()
    assert runner.is_running()

    # Check runner can get running bots
    running_bots = manager.get_running_bots()
    assert len(running_bots) == 1
    assert running_bots[0].id == bot.id

    # Cleanup
    runner.stop()
    manager.stop_bot(bot.id)


def test_runner_multiple_bots(temp_bot_dir, temp_data_dir):
    """Test runner with multiple bots"""
    from app.core.bots.manager import BotsManager

    manager = BotsManager(data_dir=str(temp_bot_dir))
    runner = get_bots_runner()

    data_fetcher = create_runner_data_fetcher(data_dir=temp_data_dir)
    runner.set_data_fetcher(data_fetcher)

    # Create 3 bots
    for i in range(3):
        bot_config = BotConfig(
            name=f"Test Bot {i}",
            description=f"Bot {i}",
            mode="paper",
            initial_capital=10000.0,
            symbols=[BotSymbolConfig(symbol="BTCUSDT", enabled=True, timeframe="1h")],
            strategy=StrategyConfig()
        )

        bot = manager.create_bot(BotCreate(config=bot_config))
        manager.start_bot(bot.id)

    # Check all bots running
    running_bots = manager.get_running_bots()
    assert len(running_bots) == 3

    # Start runner
    runner.start()

    # Cleanup
    runner.stop()
    for bot in running_bots:
        manager.stop_bot(bot.id)


def test_bot_summary_statistics(temp_bot_dir):
    """Test getting summary statistics"""
    from app.core.bots.manager import BotsManager

    manager = BotsManager(data_dir=str(temp_bot_dir))

    # Create some bots
    for i in range(5):
        bot_config = BotConfig(
            name=f"Bot {i}",
            description="Test",
            mode="paper",
            initial_capital=10000.0,
            symbols=[BotSymbolConfig(symbol="BTCUSDT", enabled=True, timeframe="1h")],
            strategy=StrategyConfig()
        )

        bot = manager.create_bot(BotCreate(config=bot_config))

        if i < 3:
            manager.start_bot(bot.id)

    # Get summary
    summary = manager.get_summary()

    assert summary['total_bots'] == 5
    assert summary['running_bots'] == 3
    assert summary['stopped_bots'] == 2
    assert summary['total_capital'] == 50000.0  # 5 * 10000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
