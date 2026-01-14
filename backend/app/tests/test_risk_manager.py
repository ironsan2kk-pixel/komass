"""
Tests for Position Risk Manager
"""
import pytest
from datetime import datetime
from app.core.bots.risk_manager import (
    PositionRiskManager,
    RiskLimits,
    RiskViolation
)
from app.core.bots.models import (
    BotConfig,
    BotSymbolConfig,
    SignalDirection
)


@pytest.fixture
def bot_config():
    """Create test bot config"""
    return BotConfig(
        name="Test Bot",
        initial_capital=10000.0,
        leverage=1,
        symbols=[
            BotSymbolConfig(symbol="BTCUSDT", allocation_percent=50.0),
            BotSymbolConfig(symbol="ETHUSDT", allocation_percent=50.0)
        ]
    )


@pytest.fixture
def risk_limits():
    """Create test risk limits"""
    return RiskLimits(
        max_positions=5,
        max_position_size_percent=20.0,
        max_drawdown_percent=15.0,
        max_daily_loss_percent=5.0,
        max_symbol_exposure_percent=30.0,
        min_capital_reserve_percent=10.0
    )


def test_risk_manager_initialization(bot_config, risk_limits):
    """Test risk manager initialization"""
    rm = PositionRiskManager(bot_config, risk_limits)

    assert rm.initial_capital == 10000.0
    assert rm.current_capital == 10000.0
    assert rm.peak_capital == 10000.0
    assert len(rm.active_positions) == 0


def test_can_open_position_success(bot_config, risk_limits):
    """Test successful position opening"""
    rm = PositionRiskManager(bot_config, risk_limits)

    # Position size: 0.03 BTC * 50000 = 1500 USD (within 20% limit of 2000)
    can_open, violation, msg = rm.can_open_position(
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        position_size=0.03,
        current_price=50000.0
    )

    assert can_open is True
    assert violation is None
    assert msg == "OK"


def test_max_positions_limit(bot_config, risk_limits):
    """Test max positions limit"""
    rm = PositionRiskManager(bot_config, risk_limits)

    # Add max positions
    for i in range(risk_limits.max_positions):
        rm.add_position(
            symbol=f"BTC{i}",
            direction=SignalDirection.LONG,
            size=0.01,
            entry_price=50000.0
        )

    # Try to add one more
    can_open, violation, msg = rm.can_open_position(
        symbol="NEWBTC",
        direction=SignalDirection.LONG,
        position_size=0.01,
        current_price=50000.0
    )

    assert can_open is False
    assert violation == RiskViolation.MAX_POSITIONS
    assert "Max positions" in msg


def test_max_position_size_limit(bot_config, risk_limits):
    """Test max position size limit"""
    rm = PositionRiskManager(bot_config, risk_limits)

    # Max position size is 20% of 10000 = 2000
    # Position: 0.05 BTC * 50000 = 2500 > 2000
    can_open, violation, msg = rm.can_open_position(
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        position_size=0.05,
        current_price=50000.0
    )

    assert can_open is False
    assert violation == RiskViolation.MAX_POSITION_SIZE


def test_max_symbol_exposure(bot_config, risk_limits):
    """Test max symbol exposure limit"""
    rm = PositionRiskManager(bot_config, risk_limits)

    # Add first position (1500 USD)
    rm.add_position(
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        size=0.03,
        entry_price=50000.0
    )
    rm.update_position_prices("BTCUSDT", 50000.0)

    # Max symbol exposure is 30% of 10000 = 3000
    # Already have 1500, can't add more than 1500
    # Trying to add 2000 = FAIL
    can_open, violation, msg = rm.can_open_position(
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        position_size=0.04,  # 2000 USD
        current_price=50000.0
    )

    assert can_open is False
    assert violation == RiskViolation.MAX_SYMBOL_EXPOSURE


def test_insufficient_capital_reserve(bot_config, risk_limits):
    """Test capital reserve limit"""
    rm = PositionRiskManager(bot_config, risk_limits)

    # Add several positions to consume capital
    # Position 1: 1800 USD
    rm.add_position("BTCUSDT", SignalDirection.LONG, 0.036, 50000.0)
    rm.update_position_prices("BTCUSDT", 50000.0)

    # Position 2: 1800 USD
    rm.add_position("ETHUSDT", SignalDirection.LONG, 0.6, 3000.0)
    rm.update_position_prices("ETHUSDT", 3000.0)

    # Position 3: 1800 USD
    rm.add_position("ADAUSDT", SignalDirection.LONG, 3600, 0.5)
    rm.update_position_prices("ADAUSDT", 0.5)

    # Position 4: 1800 USD
    rm.add_position("SOLUSDT", SignalDirection.LONG, 18, 100.0)
    rm.update_position_prices("SOLUSDT", 100.0)

    # Total exposure: 7200, Available: 2800
    # Min reserve is 10% of 10000 = 1000
    # Try to add 2000 more (would leave only 800 < 1000)
    can_open, violation, msg = rm.can_open_position(
        symbol="BNBUSDT",
        direction=SignalDirection.LONG,
        position_size=4.0,  # 2000 USD at 500
        current_price=500.0
    )

    assert can_open is False
    assert violation == RiskViolation.INSUFFICIENT_CAPITAL


def test_add_and_remove_position(bot_config, risk_limits):
    """Test adding and removing positions"""
    rm = PositionRiskManager(bot_config, risk_limits)

    # Add position
    rm.add_position(
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        size=0.1,
        entry_price=50000.0
    )

    assert len(rm.active_positions) == 1
    assert rm.active_positions[0].symbol == "BTCUSDT"

    # Remove position with profit
    rm.remove_position(
        symbol="BTCUSDT",
        close_price=51000.0,
        pnl=100.0
    )

    assert len(rm.active_positions) == 0
    assert rm.current_capital == 10100.0
    assert rm.peak_capital == 10100.0


def test_update_position_prices_long(bot_config, risk_limits):
    """Test updating position prices for LONG"""
    rm = PositionRiskManager(bot_config, risk_limits)

    rm.add_position(
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        size=0.1,
        entry_price=50000.0
    )

    # Price goes up
    rm.update_position_prices("BTCUSDT", 51000.0)

    pos = rm.active_positions[0]
    assert pos.current_price == 51000.0
    assert pos.pnl == 100.0  # (51000 - 50000) * 0.1
    assert pos.pnl_percent == pytest.approx(2.0, 0.01)


def test_update_position_prices_short(bot_config, risk_limits):
    """Test updating position prices for SHORT"""
    rm = PositionRiskManager(bot_config, risk_limits)

    rm.add_position(
        symbol="BTCUSDT",
        direction=SignalDirection.SHORT,
        size=0.1,
        entry_price=50000.0
    )

    # Price goes down (profit for short)
    rm.update_position_prices("BTCUSDT", 49000.0)

    pos = rm.active_positions[0]
    assert pos.current_price == 49000.0
    assert pos.pnl == 100.0  # (50000 - 49000) * 0.1
    assert pos.pnl_percent == pytest.approx(2.0, 0.01)


def test_drawdown_check(bot_config, risk_limits):
    """Test drawdown monitoring"""
    rm = PositionRiskManager(bot_config, risk_limits)

    # Simulate loss
    rm.current_capital = 8600.0  # 14% drawdown
    is_violated, drawdown = rm.check_drawdown()

    assert is_violated is False
    assert drawdown == pytest.approx(14.0, 0.1)

    # Exceed limit
    rm.current_capital = 8400.0  # 16% drawdown
    is_violated, drawdown = rm.check_drawdown()

    assert is_violated is True
    assert drawdown == pytest.approx(16.0, 0.1)


def test_daily_loss_limit(bot_config, risk_limits):
    """Test daily loss limit"""
    rm = PositionRiskManager(bot_config, risk_limits)

    # Max daily loss is 5% of 10000 = 500
    today = datetime.now().strftime("%Y-%m-%d")
    rm.daily_pnl[today] = -500.0

    can_open, violation, msg = rm.can_open_position(
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        position_size=0.01,
        current_price=50000.0
    )

    assert can_open is False
    assert violation == RiskViolation.MAX_DAILY_LOSS


def test_daily_trades_limit(bot_config, risk_limits):
    """Test daily trades limit"""
    rm = PositionRiskManager(bot_config, risk_limits)

    today = datetime.now().strftime("%Y-%m-%d")
    rm.daily_trades[today] = risk_limits.max_trades_per_day

    can_open, violation, msg = rm.can_open_position(
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        position_size=0.01,
        current_price=50000.0
    )

    assert can_open is False
    assert violation == RiskViolation.MAX_DAILY_LOSS


def test_portfolio_status(bot_config, risk_limits):
    """Test portfolio status reporting"""
    rm = PositionRiskManager(bot_config, risk_limits)

    # Add some positions
    rm.add_position("BTCUSDT", SignalDirection.LONG, 0.1, 50000.0)
    rm.update_position_prices("BTCUSDT", 51000.0)

    status = rm.get_portfolio_status()

    assert status["capital"]["initial"] == 10000.0
    assert status["capital"]["unrealized_pnl"] == 100.0
    assert status["positions"]["count"] == 1
    assert status["positions"]["max"] == 5
    assert status["risk"]["drawdown_percent"] == 0.0


def test_reset_daily_stats(bot_config, risk_limits):
    """Test daily stats cleanup"""
    rm = PositionRiskManager(bot_config, risk_limits)

    # Add old data
    old_date = "2020-01-01"
    rm.daily_pnl[old_date] = 100.0
    rm.daily_trades[old_date] = 5

    today = datetime.now().strftime("%Y-%m-%d")
    rm.daily_pnl[today] = 50.0

    rm.reset_daily_stats()

    # Old data should be removed
    assert old_date not in rm.daily_pnl
    # Recent data should be kept
    assert today in rm.daily_pnl
