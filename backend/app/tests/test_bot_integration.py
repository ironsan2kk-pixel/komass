"""
Integration Tests for Bot System
==================================
Test integration between Risk Manager, State Persistence, and Bot Runner
"""
import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import tempfile

from app.core.bots.models import (
    BotConfig,
    BotSymbolConfig,
    StrategyConfig,
    TakeProfitLevel,
    SignalDirection
)
from app.core.bots.risk_manager import (
    PositionRiskManager,
    RiskLimits
)
from app.core.bots.state_persistence import (
    StatePersistence,
    BotState,
    PositionState
)


@pytest.fixture
def bot_config():
    """Create test bot configuration"""
    return BotConfig(
        name="Integration Test Bot",
        initial_capital=10000.0,
        leverage=1,
        symbols=[
            BotSymbolConfig(symbol="BTCUSDT", allocation_percent=50.0),
            BotSymbolConfig(symbol="ETHUSDT", allocation_percent=50.0)
        ],
        strategy=StrategyConfig(
            name="TestStrategy",
            stop_loss_percent=2.0,
            take_profit_levels=[
                TakeProfitLevel(level=1, percent=2.0, amount=50.0),
                TakeProfitLevel(level=2, percent=4.0, amount=50.0)
            ]
        )
    )


@pytest.fixture
def risk_limits():
    """Create risk limits for testing"""
    return RiskLimits(
        max_positions=5,
        max_position_size_percent=20.0,
        max_drawdown_percent=15.0,
        max_daily_loss_percent=5.0,
        max_symbol_exposure_percent=30.0,
        min_capital_reserve_percent=10.0
    )


@pytest.fixture
def temp_state_dir():
    """Create temporary directory for state files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestBotIntegration:
    """Integration tests for bot system"""

    def test_bot_with_risk_manager(self, bot_config, risk_limits):
        """Test bot integration with risk manager"""
        # Initialize risk manager
        risk_manager = PositionRiskManager(bot_config, risk_limits)

        # Check initial state
        assert risk_manager.current_capital == 10000.0
        assert len(risk_manager.active_positions) == 0

        # Test opening position with risk checks
        can_open, violation, msg = risk_manager.can_open_position(
            symbol="BTCUSDT",
            direction=SignalDirection.LONG,
            position_size=0.03,
            current_price=50000.0
        )

        assert can_open is True
        assert violation is None

        # Add position
        risk_manager.add_position(
            symbol="BTCUSDT",
            direction=SignalDirection.LONG,
            size=0.03,
            entry_price=50000.0
        )

        assert len(risk_manager.active_positions) == 1

        # Update prices (simulate profit)
        risk_manager.update_position_prices("BTCUSDT", 51000.0)

        position = risk_manager.active_positions[0]
        assert position.current_price == 51000.0
        assert position.pnl == 30.0  # (51000 - 50000) * 0.03

        # Close position with profit
        risk_manager.remove_position(
            symbol="BTCUSDT",
            close_price=51000.0,
            pnl=30.0
        )

        assert len(risk_manager.active_positions) == 0
        assert risk_manager.current_capital == 10030.0
        assert risk_manager.peak_capital == 10030.0


    def test_risk_manager_with_state_persistence(
        self,
        bot_config,
        risk_limits,
        temp_state_dir
    ):
        """Test risk manager state saving and restoration"""
        # Initialize components
        risk_manager = PositionRiskManager(bot_config, risk_limits)
        persistence = StatePersistence(state_dir=temp_state_dir)

        # Add some positions
        risk_manager.add_position("BTCUSDT", SignalDirection.LONG, 0.02, 50000.0)
        risk_manager.update_position_prices("BTCUSDT", 51000.0)

        risk_manager.add_position("ETHUSDT", SignalDirection.LONG, 0.5, 3000.0)
        risk_manager.update_position_prices("ETHUSDT", 3100.0)

        # Create bot state snapshot
        positions = []
        for pos in risk_manager.active_positions:
            positions.append(PositionState(
                symbol=pos.symbol,
                direction=pos.direction.value,
                size=pos.size,
                entry_price=pos.entry_price,
                current_price=pos.current_price,
                entry_time=pos.timestamp.isoformat(),
                take_profit_levels=[],
                stop_loss_price=0.0,
                pnl=pos.pnl,
                pnl_percent=pos.pnl_percent
            ))

        bot_state = BotState(
            bot_id="test_bot_1",
            name="Integration Test Bot",
            status="running",
            initial_capital=risk_manager.initial_capital,
            current_capital=risk_manager.current_capital,
            peak_capital=risk_manager.peak_capital,
            positions=positions,
            total_trades=2,
            winning_trades=0,
            losing_trades=0,
            total_pnl=0.0,
            total_pnl_percent=0.0,
            max_drawdown=0.0,
            current_drawdown=0.0,
            started_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat()
        )

        # Save state
        success = persistence.save_bot_state("test_bot_1", bot_state)
        assert success is True

        # Load state
        loaded_state = persistence.load_bot_state("test_bot_1")
        assert loaded_state is not None
        assert loaded_state.bot_id == "test_bot_1"
        assert len(loaded_state.positions) == 2
        assert loaded_state.current_capital == 10000.0

        # Verify positions
        btc_pos = next(p for p in loaded_state.positions if p.symbol == "BTCUSDT")
        assert btc_pos.size == 0.02
        assert btc_pos.entry_price == 50000.0
        assert btc_pos.current_price == 51000.0


    def test_multiple_positions_risk_management(self, bot_config, risk_limits):
        """Test managing multiple positions with risk limits"""
        risk_manager = PositionRiskManager(bot_config, risk_limits)

        # Add multiple positions within limits
        positions_to_add = [
            ("BTCUSDT", 0.02, 50000.0),  # 1000 USD
            ("ETHUSDT", 0.4, 3000.0),     # 1200 USD
            ("BNBUSDT", 4.0, 400.0),      # 1600 USD
        ]

        for symbol, size, price in positions_to_add:
            can_open, violation, msg = risk_manager.can_open_position(
                symbol=symbol,
                direction=SignalDirection.LONG,
                position_size=size,
                current_price=price
            )

            assert can_open is True, f"Failed to open {symbol}: {msg}"

            risk_manager.add_position(
                symbol=symbol,
                direction=SignalDirection.LONG,
                size=size,
                entry_price=price
            )

        # Verify all positions added
        assert len(risk_manager.active_positions) == 3

        # Check portfolio status
        status = risk_manager.get_portfolio_status()
        assert status["positions"]["count"] == 3
        assert status["capital"]["current"] == 10000.0

        # Total exposure: 1000 + 1200 + 1600 = 3800
        total_exposure = status["positions"]["total_exposure"]
        assert 3700 <= total_exposure <= 3900


    def test_position_lifecycle_with_persistence(
        self,
        bot_config,
        risk_limits,
        temp_state_dir
    ):
        """Test complete position lifecycle with state persistence"""
        import time

        risk_manager = PositionRiskManager(bot_config, risk_limits)
        persistence = StatePersistence(state_dir=temp_state_dir)

        # 1. Open position
        risk_manager.add_position("BTCUSDT", SignalDirection.LONG, 0.1, 50000.0)

        # 2. Save state after opening
        state1 = self._create_bot_state(risk_manager, "bot_lifecycle", "running")
        persistence.save_bot_state("bot_lifecycle", state1)
        time.sleep(0.01)  # Ensure different timestamp

        # 3. Update prices (simulate price movement)
        risk_manager.update_position_prices("BTCUSDT", 52000.0)

        # 4. Save state after price update
        state2 = self._create_bot_state(risk_manager, "bot_lifecycle", "running")
        persistence.save_bot_state("bot_lifecycle", state2)
        time.sleep(0.01)  # Ensure different timestamp

        # 5. Close position with profit
        pnl = (52000.0 - 50000.0) * 0.1  # 200 USD profit
        risk_manager.remove_position("BTCUSDT", 52000.0, pnl)

        # 6. Save final state
        state3 = self._create_bot_state(risk_manager, "bot_lifecycle", "stopped")
        persistence.save_bot_state("bot_lifecycle", state3)

        # Verify final state
        final_state = persistence.load_bot_state("bot_lifecycle")
        assert final_state.status == "stopped"
        assert len(final_state.positions) == 0
        assert final_state.current_capital == 10200.0

        # Verify backups created (at least 1, possibly 3 with different timestamps)
        backups = list(temp_state_dir.glob("backup_bot_lifecycle_*.json"))
        assert len(backups) >= 1  # At least 1 backup exists


    def test_drawdown_protection(self, bot_config, risk_limits):
        """Test drawdown protection mechanism"""
        risk_manager = PositionRiskManager(bot_config, risk_limits)

        # Simulate losses
        risk_manager.add_position("BTCUSDT", SignalDirection.LONG, 0.1, 50000.0)

        # Simulate 10% loss
        loss_pnl = -1000.0
        risk_manager.remove_position("BTCUSDT", 49000.0, loss_pnl)

        assert risk_manager.current_capital == 9000.0

        # Check drawdown (should be 10%)
        is_violated, drawdown = risk_manager.check_drawdown()
        assert is_violated is False
        assert drawdown == pytest.approx(10.0, 0.1)

        # Simulate more losses to exceed limit
        risk_manager.add_position("ETHUSDT", SignalDirection.LONG, 2.0, 3000.0)
        loss_pnl2 = -600.0  # Additional 6% loss
        risk_manager.remove_position("ETHUSDT", 2700.0, loss_pnl2)

        assert risk_manager.current_capital == 8400.0

        # Check drawdown (should be 16%, exceeds 15% limit)
        is_violated, drawdown = risk_manager.check_drawdown()
        assert is_violated is True
        assert drawdown == pytest.approx(16.0, 0.1)


    def test_state_restoration_after_crash(
        self,
        bot_config,
        risk_limits,
        temp_state_dir
    ):
        """Test bot recovery after simulated crash"""
        # Simulate bot running
        persistence = StatePersistence(state_dir=temp_state_dir)

        # Create multiple bot states
        for i in range(3):
            bot_state = BotState(
                bot_id=f"bot_{i}",
                name=f"Bot {i}",
                status="running" if i < 2 else "stopped",
                initial_capital=10000.0,
                current_capital=10000.0 + (i * 100),
                peak_capital=10000.0 + (i * 100),
                positions=[],
                total_trades=i * 5,
                winning_trades=i * 3,
                losing_trades=i * 2,
                total_pnl=i * 100.0,
                total_pnl_percent=i * 1.0,
                max_drawdown=0.0,
                current_drawdown=0.0,
                started_at=datetime.now().isoformat(),
                last_updated=datetime.now().isoformat()
            )
            persistence.save_bot_state(f"bot_{i}", bot_state)

        # Simulate crash and restart
        # Restore only active bots
        active_bots = persistence.restore_all_active_bots()

        # Should restore only running/paused bots (not stopped)
        assert len(active_bots) == 2
        assert all(b.status == "running" for b in active_bots)
        assert active_bots[0].bot_id in ["bot_0", "bot_1"]


    def test_concurrent_positions_risk_limits(self, bot_config, risk_limits):
        """Test risk limits with concurrent positions on same symbol"""
        risk_manager = PositionRiskManager(bot_config, risk_limits)

        # Add first position on BTCUSDT (1500 USD)
        risk_manager.add_position("BTCUSDT", SignalDirection.LONG, 0.03, 50000.0)
        risk_manager.update_position_prices("BTCUSDT", 50000.0)

        # Try to add second position that would exceed symbol exposure limit
        # Max symbol exposure is 30% of 10000 = 3000
        # Already have 1500, can add max 1500 more
        # Trying to add 2000 should fail
        can_open, violation, msg = risk_manager.can_open_position(
            symbol="BTCUSDT",
            direction=SignalDirection.LONG,
            position_size=0.04,  # 2000 USD
            current_price=50000.0
        )

        assert can_open is False
        assert violation is not None
        assert "exposure" in msg.lower() or "symbol" in msg.lower()


    def _create_bot_state(
        self,
        risk_manager: PositionRiskManager,
        bot_id: str,
        status: str
    ) -> BotState:
        """Helper to create bot state from risk manager"""
        positions = []
        for pos in risk_manager.active_positions:
            positions.append(PositionState(
                symbol=pos.symbol,
                direction=pos.direction.value,
                size=pos.size,
                entry_price=pos.entry_price,
                current_price=pos.current_price,
                entry_time=pos.timestamp.isoformat(),
                take_profit_levels=[],
                stop_loss_price=0.0,
                pnl=pos.pnl,
                pnl_percent=pos.pnl_percent
            ))

        return BotState(
            bot_id=bot_id,
            name="Test Bot",
            status=status,
            initial_capital=risk_manager.initial_capital,
            current_capital=risk_manager.current_capital,
            peak_capital=risk_manager.peak_capital,
            positions=positions,
            total_trades=len(risk_manager.daily_trades),
            winning_trades=0,
            losing_trades=0,
            total_pnl=risk_manager.current_capital - risk_manager.initial_capital,
            total_pnl_percent=((risk_manager.current_capital - risk_manager.initial_capital) / risk_manager.initial_capital) * 100,
            max_drawdown=0.0,
            current_drawdown=0.0,
            started_at=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat()
        )
