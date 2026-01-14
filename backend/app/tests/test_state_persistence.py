"""
Tests for Bot State Persistence
"""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from app.core.bots.state_persistence import (
    StatePersistence,
    BotState,
    PositionState,
    save_bot_state,
    load_bot_state,
    delete_bot_state
)


@pytest.fixture
def temp_state_dir():
    """Create temporary directory for state files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_position():
    """Create sample position state"""
    return PositionState(
        symbol="BTCUSDT",
        direction="long",
        size=0.1,
        entry_price=50000.0,
        current_price=51000.0,
        entry_time=datetime.now().isoformat(),
        take_profit_levels=[
            {"price": 52000.0, "amount": 50.0},
            {"price": 54000.0, "amount": 50.0}
        ],
        stop_loss_price=48000.0,
        pnl=100.0,
        pnl_percent=2.0
    )


@pytest.fixture
def sample_bot_state(sample_position):
    """Create sample bot state"""
    return BotState(
        bot_id="test_bot_1",
        name="Test Bot",
        status="running",
        initial_capital=10000.0,
        current_capital=10100.0,
        peak_capital=10150.0,
        positions=[sample_position],
        total_trades=5,
        winning_trades=3,
        losing_trades=2,
        total_pnl=100.0,
        total_pnl_percent=1.0,
        max_drawdown=2.5,
        current_drawdown=0.0,
        started_at=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat(),
        last_trade_at=datetime.now().isoformat(),
        daily_pnl={"2024-01-01": 50.0, "2024-01-02": 50.0},
        daily_trades={"2024-01-01": 3, "2024-01-02": 2}
    )


def test_state_persistence_initialization(temp_state_dir):
    """Test state persistence initialization"""
    persistence = StatePersistence(state_dir=temp_state_dir)

    assert persistence.state_dir == temp_state_dir
    assert temp_state_dir.exists()


def test_save_bot_state(temp_state_dir, sample_bot_state):
    """Test saving bot state"""
    persistence = StatePersistence(state_dir=temp_state_dir)

    success = persistence.save_bot_state("test_bot_1", sample_bot_state)

    assert success is True

    # Check file exists
    state_file = temp_state_dir / "test_bot_1.json"
    assert state_file.exists()

    # Verify content
    with open(state_file) as f:
        data = json.load(f)

    assert data["bot_id"] == "test_bot_1"
    assert data["name"] == "Test Bot"
    assert data["status"] == "running"
    assert data["current_capital"] == 10100.0
    assert len(data["positions"]) == 1
    assert "_metadata" in data


def test_load_bot_state(temp_state_dir, sample_bot_state):
    """Test loading bot state"""
    persistence = StatePersistence(state_dir=temp_state_dir)

    # Save first
    persistence.save_bot_state("test_bot_1", sample_bot_state)

    # Load
    loaded_state = persistence.load_bot_state("test_bot_1")

    assert loaded_state is not None
    assert loaded_state.bot_id == "test_bot_1"
    assert loaded_state.name == "Test Bot"
    assert loaded_state.current_capital == 10100.0
    assert len(loaded_state.positions) == 1
    assert loaded_state.positions[0].symbol == "BTCUSDT"
    assert loaded_state.total_trades == 5
    assert loaded_state.daily_pnl["2024-01-01"] == 50.0


def test_load_nonexistent_state(temp_state_dir):
    """Test loading nonexistent bot state"""
    persistence = StatePersistence(state_dir=temp_state_dir)

    loaded_state = persistence.load_bot_state("nonexistent_bot")

    assert loaded_state is None


def test_delete_bot_state(temp_state_dir, sample_bot_state):
    """Test deleting bot state"""
    persistence = StatePersistence(state_dir=temp_state_dir)

    # Save first
    persistence.save_bot_state("test_bot_1", sample_bot_state)

    # Delete
    success = persistence.delete_bot_state("test_bot_1")

    assert success is True

    # Verify deleted
    state_file = temp_state_dir / "test_bot_1.json"
    assert not state_file.exists()


def test_list_saved_states(temp_state_dir, sample_bot_state):
    """Test listing saved states"""
    persistence = StatePersistence(state_dir=temp_state_dir)

    # Save multiple bots
    state1 = sample_bot_state
    state1.bot_id = "bot_1"
    state1.name = "Bot 1"

    state2 = BotState(
        bot_id="bot_2",
        name="Bot 2",
        status="paused",
        initial_capital=5000.0,
        current_capital=5200.0,
        peak_capital=5300.0,
        positions=[],
        total_trades=10,
        winning_trades=6,
        losing_trades=4,
        total_pnl=200.0,
        total_pnl_percent=4.0,
        max_drawdown=1.5,
        current_drawdown=0.5,
        started_at=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat()
    )

    persistence.save_bot_state("bot_1", state1)
    persistence.save_bot_state("bot_2", state2)

    # List states
    states = persistence.list_saved_states()

    assert len(states) == 2
    assert any(s["bot_id"] == "bot_1" for s in states)
    assert any(s["bot_id"] == "bot_2" for s in states)

    # Check metadata
    bot1_meta = next(s for s in states if s["bot_id"] == "bot_1")
    assert bot1_meta["name"] == "Bot 1"
    assert bot1_meta["status"] == "running"
    assert bot1_meta["positions_count"] == 1
    assert bot1_meta["current_capital"] == 10100.0


def test_restore_all_active_bots(temp_state_dir, sample_bot_state):
    """Test restoring all active bots"""
    persistence = StatePersistence(state_dir=temp_state_dir)

    # Create and save active and stopped bots
    active_state = sample_bot_state
    active_state.bot_id = "active_bot"
    active_state.status = "running"

    paused_state = BotState(
        bot_id="paused_bot",
        name="Paused Bot",
        status="paused",
        initial_capital=5000.0,
        current_capital=5000.0,
        peak_capital=5000.0,
        positions=[],
        total_trades=0,
        winning_trades=0,
        losing_trades=0,
        total_pnl=0.0,
        total_pnl_percent=0.0,
        max_drawdown=0.0,
        current_drawdown=0.0,
        started_at=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat()
    )

    stopped_state = BotState(
        bot_id="stopped_bot",
        name="Stopped Bot",
        status="stopped",
        initial_capital=3000.0,
        current_capital=3000.0,
        peak_capital=3000.0,
        positions=[],
        total_trades=0,
        winning_trades=0,
        losing_trades=0,
        total_pnl=0.0,
        total_pnl_percent=0.0,
        max_drawdown=0.0,
        current_drawdown=0.0,
        started_at=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat()
    )

    persistence.save_bot_state("active_bot", active_state)
    persistence.save_bot_state("paused_bot", paused_state)
    persistence.save_bot_state("stopped_bot", stopped_state)

    # Restore active bots
    active_bots = persistence.restore_all_active_bots()

    # Should restore running and paused, but not stopped
    assert len(active_bots) == 2
    bot_ids = {bot.bot_id for bot in active_bots}
    assert "active_bot" in bot_ids
    assert "paused_bot" in bot_ids
    assert "stopped_bot" not in bot_ids


def test_backup_creation(temp_state_dir, sample_bot_state):
    """Test backup file creation"""
    persistence = StatePersistence(state_dir=temp_state_dir)

    # Save state (should create backup)
    persistence.save_bot_state("test_bot_1", sample_bot_state)

    # Check backup exists
    backups = list(temp_state_dir.glob("backup_test_bot_1_*.json"))
    assert len(backups) == 1


def test_old_backup_cleanup(temp_state_dir, sample_bot_state):
    """Test old backup cleanup (keeps last 10)"""
    import time
    persistence = StatePersistence(state_dir=temp_state_dir)

    # Create 15 backups with slight delays to get different timestamps
    for i in range(15):
        sample_bot_state.total_trades = i  # Make each state slightly different
        persistence.save_bot_state("test_bot_1", sample_bot_state)
        time.sleep(0.01)  # Small delay to ensure different timestamps

    # Should keep only last 10 backups
    backups = list(temp_state_dir.glob("backup_test_bot_1_*.json"))
    assert len(backups) <= 10  # Should be 10 or less due to cleanup


def test_helper_functions(temp_state_dir, sample_bot_state):
    """Test helper functions"""
    # Use helper functions
    success = save_bot_state("helper_bot", sample_bot_state)
    assert success is True

    loaded = load_bot_state("helper_bot")
    assert loaded is not None
    assert loaded.bot_id == "test_bot_1"  # From sample_bot_state

    deleted = delete_bot_state("helper_bot")
    assert deleted is True


def test_position_state_serialization(sample_position):
    """Test PositionState serialization"""
    # Convert to dict
    pos_dict = {
        "symbol": sample_position.symbol,
        "direction": sample_position.direction,
        "size": sample_position.size,
        "entry_price": sample_position.entry_price,
        "current_price": sample_position.current_price,
        "entry_time": sample_position.entry_time,
        "take_profit_levels": sample_position.take_profit_levels,
        "stop_loss_price": sample_position.stop_loss_price,
        "pnl": sample_position.pnl,
        "pnl_percent": sample_position.pnl_percent
    }

    # Create from dict
    restored_pos = PositionState(**pos_dict)

    assert restored_pos.symbol == "BTCUSDT"
    assert restored_pos.size == 0.1
    assert restored_pos.pnl == 100.0
