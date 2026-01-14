"""
Unit Tests for Portfolio Backtest
==================================
Tests for portfolio backtesting engine
"""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import numpy as np
import tempfile
import shutil

from app.core.bots.backtest import (
    PortfolioBacktest,
    BacktestPosition,
    BacktestResult
)
from app.core.bots.models import (
    BotConfig,
    BotSymbolConfig,
    StrategyConfig,
    TakeProfitLevel,
    SignalDirection,
    StopLossMode
)


@pytest.fixture
def temp_data_dir():
    """Create temporary data directory with test OHLCV"""
    temp_dir = Path(tempfile.mkdtemp())

    # Create realistic test data (trending up)
    dates = pd.date_range(start='2024-01-01', periods=500, freq='1h')

    # BTC trending up from 40000 to 50000
    btc_prices = np.linspace(40000, 50000, 500)
    btc_noise = np.random.normal(0, 500, 500)
    btc_close = btc_prices + btc_noise

    df_btc = pd.DataFrame({
        'open': btc_close * 0.999,
        'high': btc_close * 1.005,
        'low': btc_close * 0.995,
        'close': btc_close,
        'volume': np.random.uniform(1000, 5000, 500)
    }, index=dates)

    # ETH trending up from 2000 to 3000
    eth_prices = np.linspace(2000, 3000, 500)
    eth_noise = np.random.normal(0, 50, 500)
    eth_close = eth_prices + eth_noise

    df_eth = pd.DataFrame({
        'open': eth_close * 0.999,
        'high': eth_close * 1.005,
        'low': eth_close * 0.995,
        'close': eth_close,
        'volume': np.random.uniform(5000, 15000, 500)
    }, index=dates)

    df_btc.to_parquet(temp_dir / "BTCUSDT_1h.parquet")
    df_eth.to_parquet(temp_dir / "ETHUSDT_1h.parquet")

    yield temp_dir

    shutil.rmtree(temp_dir)


def test_backtest_initialization(temp_data_dir):
    """Test backtest engine initialization"""
    config = BotConfig(
        name="Test Bot",
        description="Test",
        mode="paper",
        initial_capital=10000.0,
        symbols=[
            BotSymbolConfig(symbol="BTCUSDT", enabled=True, timeframe="1h")
        ],
        strategy=StrategyConfig()
    )

    backtest = PortfolioBacktest(
        bot_config=config,
        start_date="2024-01-01",
        end_date="2024-01-10",
        data_dir=temp_data_dir
    )

    assert backtest.bot_config == config
    assert backtest.capital == 10000.0
    assert len(backtest.positions) == 0


def test_backtest_data_loading(temp_data_dir):
    """Test OHLCV data loading"""
    config = BotConfig(
        name="Test Bot",
        description="Test",
        mode="paper",
        initial_capital=10000.0,
        symbols=[
            BotSymbolConfig(symbol="BTCUSDT", enabled=True, timeframe="1h"),
            BotSymbolConfig(symbol="ETHUSDT", enabled=True, timeframe="1h")
        ],
        strategy=StrategyConfig()
    )

    backtest = PortfolioBacktest(
        bot_config=config,
        data_dir=temp_data_dir
    )

    # Load data
    success = backtest._load_data()

    assert success is True
    assert "BTCUSDT" in backtest.data_cache
    assert "ETHUSDT" in backtest.data_cache
    assert len(backtest.data_cache["BTCUSDT"]) > 0
    assert len(backtest.data_cache["ETHUSDT"]) > 0


def test_backtest_single_symbol(temp_data_dir):
    """Test backtest with single symbol"""
    config = BotConfig(
        name="BTC Bot",
        description="Test",
        mode="paper",
        initial_capital=10000.0,
        symbols=[
            BotSymbolConfig(
                symbol="BTCUSDT",
                enabled=True,
                timeframe="1h",
                position_size_percent=100.0
            )
        ],
        strategy=StrategyConfig(
            atr_length=45,
            multiplier=4.0,
            tp_count=3,
            take_profits=[
                TakeProfitLevel(price_percent=2.0, close_percent=50.0),
                TakeProfitLevel(price_percent=4.0, close_percent=30.0),
                TakeProfitLevel(price_percent=6.0, close_percent=20.0)
            ],
            sl_percent=3.0
        )
    )

    backtest = PortfolioBacktest(
        bot_config=config,
        start_date="2024-01-01",
        end_date="2024-01-20",
        data_dir=temp_data_dir
    )

    result = backtest.run()

    # Check result structure
    assert isinstance(result, BacktestResult)
    assert result.initial_capital == 10000.0
    assert result.final_capital > 0
    assert result.total_trades >= 0
    assert 'BTCUSDT' in result.symbol_stats


def test_backtest_multi_symbol_portfolio(temp_data_dir):
    """Test portfolio backtest with multiple symbols"""
    config = BotConfig(
        name="Portfolio Bot",
        description="Multi-symbol test",
        mode="paper",
        initial_capital=10000.0,
        symbols=[
            BotSymbolConfig(
                symbol="BTCUSDT",
                enabled=True,
                timeframe="1h",
                position_size_percent=50.0
            ),
            BotSymbolConfig(
                symbol="ETHUSDT",
                enabled=True,
                timeframe="1h",
                position_size_percent=50.0
            )
        ],
        strategy=StrategyConfig(
            atr_length=20,
            multiplier=3.0,
            tp_count=2,
            take_profits=[
                TakeProfitLevel(price_percent=3.0, close_percent=60.0),
                TakeProfitLevel(price_percent=6.0, close_percent=40.0)
            ],
            sl_percent=4.0
        )
    )

    backtest = PortfolioBacktest(
        bot_config=config,
        start_date="2024-01-01",
        end_date="2024-01-20",
        data_dir=temp_data_dir
    )

    result = backtest.run()

    # Check both symbols tracked
    assert 'BTCUSDT' in result.symbol_stats
    assert 'ETHUSDT' in result.symbol_stats

    # Check portfolio metrics
    assert result.total_pnl_percent != 0  # Should have some performance
    assert len(result.equity_curve) > 0


def test_backtest_tp_levels():
    """Test TP level calculations"""
    from app.core.bots.backtest import PortfolioBacktest

    config = BotConfig(
        name="TP Test",
        description="Test",
        mode="paper",
        initial_capital=10000.0,
        symbols=[BotSymbolConfig(symbol="BTCUSDT", enabled=True, timeframe="1h")],
        strategy=StrategyConfig(
            tp_count=3,
            take_profits=[
                TakeProfitLevel(price_percent=2.0, close_percent=50.0),
                TakeProfitLevel(price_percent=4.0, close_percent=30.0),
                TakeProfitLevel(price_percent=6.0, close_percent=20.0)
            ]
        )
    )

    backtest = PortfolioBacktest(bot_config=config)

    # Test LONG TPs
    entry_price = 50000.0
    tp_levels = backtest._calculate_tp_levels(
        entry_price,
        SignalDirection.LONG,
        config.strategy
    )

    assert len(tp_levels) == 3
    assert tp_levels[0][0] == pytest.approx(51000.0)  # +2%
    assert tp_levels[1][0] == pytest.approx(52000.0)  # +4%
    assert tp_levels[2][0] == pytest.approx(53000.0)  # +6%

    # Test SHORT TPs
    tp_levels_short = backtest._calculate_tp_levels(
        entry_price,
        SignalDirection.SHORT,
        config.strategy
    )

    assert tp_levels_short[0][0] == pytest.approx(49000.0)  # -2%
    assert tp_levels_short[1][0] == pytest.approx(48000.0)  # -4%


def test_backtest_sl_calculation():
    """Test SL price calculation"""
    from app.core.bots.backtest import PortfolioBacktest

    config = BotConfig(
        name="SL Test",
        description="Test",
        mode="paper",
        initial_capital=10000.0,
        symbols=[BotSymbolConfig(symbol="BTCUSDT", enabled=True, timeframe="1h")],
        strategy=StrategyConfig(sl_percent=3.0)
    )

    backtest = PortfolioBacktest(bot_config=config)

    entry_price = 50000.0

    # Test LONG SL
    sl_long = backtest._calculate_sl_price(
        entry_price,
        SignalDirection.LONG,
        config.strategy
    )
    assert sl_long == pytest.approx(48500.0)  # -3%

    # Test SHORT SL
    sl_short = backtest._calculate_sl_price(
        entry_price,
        SignalDirection.SHORT,
        config.strategy
    )
    assert sl_short == pytest.approx(51500.0)  # +3%


def test_backtest_position_tracking():
    """Test position opening and tracking"""
    position = BacktestPosition(
        id="test_1",
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        entry_price=50000.0,
        entry_time=datetime.now(),
        size=10000.0,
        leverage=1,
        tp_levels=[(51000.0, 50.0), (52000.0, 50.0)],
        sl_price=48500.0
    )

    assert position.remaining_size == 10000.0

    # Hit TP1
    position.tp_levels_hit.append(0)
    assert position.remaining_size == pytest.approx(5000.0)  # 50% closed

    # Hit TP2
    position.tp_levels_hit.append(1)
    assert position.remaining_size == pytest.approx(0.0)  # 100% closed


def test_backtest_result_to_dict():
    """Test result conversion to dictionary"""
    config = BotConfig(
        name="Test",
        description="Test",
        mode="paper",
        initial_capital=10000.0,
        symbols=[BotSymbolConfig(symbol="BTCUSDT", enabled=True, timeframe="1h")],
        strategy=StrategyConfig()
    )

    result = BacktestResult(
        bot_config=config,
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 1, 31),
        initial_capital=10000.0,
        final_capital=11500.0,
        total_pnl=1500.0,
        total_pnl_percent=15.0,
        total_trades=20,
        winning_trades=12,
        losing_trades=8,
        win_rate=60.0,
        max_drawdown=500.0,
        max_drawdown_percent=5.0,
        sharpe_ratio=1.5,
        profit_factor=2.0
    )

    result_dict = result.to_dict()

    assert result_dict['capital']['initial'] == 10000.0
    assert result_dict['capital']['final'] == 11500.0
    assert result_dict['capital']['pnl'] == 1500.0
    assert result_dict['statistics']['total_trades'] == 20
    assert result_dict['statistics']['win_rate'] == 60.0


def test_backtest_drawdown_calculation(temp_data_dir):
    """Test maximum drawdown calculation"""
    config = BotConfig(
        name="DD Test",
        description="Test",
        mode="paper",
        initial_capital=10000.0,
        symbols=[
            BotSymbolConfig(symbol="BTCUSDT", enabled=True, timeframe="1h")
        ],
        strategy=StrategyConfig()
    )

    backtest = PortfolioBacktest(
        bot_config=config,
        start_date="2024-01-01",
        end_date="2024-01-10",
        data_dir=temp_data_dir
    )

    # Simulate equity curve with drawdown
    backtest.equity_curve = [
        (datetime(2024, 1, 1), 10000.0),
        (datetime(2024, 1, 2), 10500.0),  # Peak
        (datetime(2024, 1, 3), 9800.0),   # Drawdown -700
        (datetime(2024, 1, 4), 10200.0),
    ]

    dd, dd_pct = backtest._calculate_drawdown()

    assert dd == pytest.approx(700.0)
    assert dd_pct == pytest.approx(7.0)


def test_backtest_profit_factor():
    """Test profit factor calculation"""
    config = BotConfig(
        name="PF Test",
        description="Test",
        mode="paper",
        initial_capital=10000.0,
        symbols=[BotSymbolConfig(symbol="BTCUSDT", enabled=True, timeframe="1h")],
        strategy=StrategyConfig()
    )

    backtest = PortfolioBacktest(bot_config=config)

    # Add some closed positions
    backtest.closed_positions = [
        BacktestPosition(
            id="1", symbol="BTCUSDT", direction=SignalDirection.LONG,
            entry_price=50000, entry_time=datetime.now(), size=10000, leverage=1,
            tp_levels=[], sl_price=48000,
            realized_pnl=1000.0  # Win
        ),
        BacktestPosition(
            id="2", symbol="BTCUSDT", direction=SignalDirection.LONG,
            entry_price=50000, entry_time=datetime.now(), size=10000, leverage=1,
            tp_levels=[], sl_price=48000,
            realized_pnl=-500.0  # Loss
        ),
        BacktestPosition(
            id="3", symbol="BTCUSDT", direction=SignalDirection.LONG,
            entry_price=50000, entry_time=datetime.now(), size=10000, leverage=1,
            tp_levels=[], sl_price=48000,
            realized_pnl=500.0  # Win
        ),
    ]

    pf = backtest._calculate_profit_factor()

    # Gross profit = 1000 + 500 = 1500
    # Gross loss = 500
    # PF = 1500 / 500 = 3.0
    assert pf == pytest.approx(3.0)


def test_backtest_with_disabled_symbols(temp_data_dir):
    """Test backtest skips disabled symbols"""
    config = BotConfig(
        name="Disabled Test",
        description="Test",
        mode="paper",
        initial_capital=10000.0,
        symbols=[
            BotSymbolConfig(symbol="BTCUSDT", enabled=True, timeframe="1h"),
            BotSymbolConfig(symbol="ETHUSDT", enabled=False, timeframe="1h")  # Disabled
        ],
        strategy=StrategyConfig()
    )

    backtest = PortfolioBacktest(
        bot_config=config,
        start_date="2024-01-01",
        end_date="2024-01-05",
        data_dir=temp_data_dir
    )

    backtest._load_data()

    # Only BTCUSDT should be loaded
    assert "BTCUSDT" in backtest.data_cache
    assert "ETHUSDT" not in backtest.data_cache


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
