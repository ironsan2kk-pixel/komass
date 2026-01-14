# KOMAS Trading Bot System Documentation

Comprehensive documentation for the KOMAS trading bot system components.

## Table of Contents
1. [Position Risk Manager](#position-risk-manager)
2. [State Persistence](#state-persistence)
3. [Portfolio Backtest Engine](#portfolio-backtest-engine)
4. [Bot Configuration Optimizer](#bot-configuration-optimizer)
5. [Integration Examples](#integration-examples)

---

## Position Risk Manager

The Position Risk Manager provides multi-layered risk control for trading bots to prevent excessive losses and over-trading.

### Features

**Position Limits:**
- Max concurrent positions (default: 5)
- Max position size (default: 20% of capital)
- Max symbol exposure (default: 30% of capital)

**Drawdown Protection:**
- Max portfolio drawdown (default: 15%)
- Max daily loss limit (default: 5%)
- Real-time drawdown monitoring

**Trading Limits:**
- Max trades per day (default: 50)
- Max trades per symbol per day (default: 10)
- Capital reserve requirement (default: 10%)

### Usage

```python
from app.core.bots.risk_manager import PositionRiskManager, RiskLimits

# Create risk limits
risk_limits = RiskLimits(
    max_positions=5,
    max_position_size_percent=20.0,
    max_drawdown_percent=15.0,
    max_daily_loss_percent=5.0,
    max_symbol_exposure_percent=30.0,
    min_capital_reserve_percent=10.0
)

# Initialize risk manager
risk_manager = PositionRiskManager(bot_config, risk_limits)

# Check if position can be opened
can_open, violation, msg = risk_manager.can_open_position(
    symbol="BTCUSDT",
    direction=SignalDirection.LONG,
    position_size=0.1,
    current_price=50000.0
)

if can_open:
    # Add position
    risk_manager.add_position(
        symbol="BTCUSDT",
        direction=SignalDirection.LONG,
        size=0.1,
        entry_price=50000.0
    )

    # Update prices
    risk_manager.update_position_prices("BTCUSDT", 51000.0)

    # Close position
    risk_manager.remove_position(
        symbol="BTCUSDT",
        close_price=51000.0,
        pnl=100.0
    )
```

### Risk Checks Performed

1. **Max Positions Check** - Ensures total positions don't exceed limit
2. **Position Size Check** - Validates position value vs capital percentage
3. **Symbol Exposure Check** - Limits total exposure to any single symbol
4. **Capital Reserve Check** - Ensures minimum capital reserve is maintained
5. **Daily Loss Check** - Stops trading if daily loss limit is reached
6. **Daily Trades Check** - Limits total number of trades per day
7. **Symbol Trades Check** - Limits trades per symbol per day

---

## State Persistence

State Persistence enables bots to save their state to disk and recover after server restarts or crashes.

### Features

**State Storage:**
- JSON-based state files
- Automatic timestamped backups
- Keeps last 10 backups per bot

**Bot State Includes:**
- All active positions with current P&L
- Capital and equity metrics
- Trading statistics
- Daily P&L history
- Timestamps and metadata

**Recovery Options:**
- Load specific bot state
- Restore all active bots
- List all saved states

### Usage

```python
from app.core.bots.state_persistence import (
    StatePersistence,
    BotState,
    PositionState,
    save_bot_state,
    load_bot_state,
    restore_all_active_bots
)

# Create bot state
bot_state = BotState(
    bot_id="my_bot_1",
    name="My Trading Bot",
    status="running",
    initial_capital=10000.0,
    current_capital=10500.0,
    peak_capital=10600.0,
    positions=[...],  # List of PositionState objects
    total_trades=25,
    winning_trades=15,
    losing_trades=10,
    total_pnl=500.0,
    total_pnl_percent=5.0,
    max_drawdown=2.5,
    current_drawdown=0.0,
    started_at="2024-01-01T00:00:00",
    last_updated="2024-01-15T12:30:00"
)

# Save state (using helper function)
success = save_bot_state("my_bot_1", bot_state)

# Load state
loaded_state = load_bot_state("my_bot_1")

# Restore all active bots (on server restart)
active_bots = restore_all_active_bots()  # Returns only running/paused bots
```

### State Directory Structure

```
backend/data/bot_states/
├── bot_1.json                    # Current state
├── backup_bot_1_20240115_123000.json
├── backup_bot_1_20240115_120000.json
└── ...                           # Up to 10 backups
```

### State File Format

```json
{
  "bot_id": "my_bot_1",
  "name": "My Trading Bot",
  "status": "running",
  "initial_capital": 10000.0,
  "current_capital": 10500.0,
  "peak_capital": 10600.0,
  "positions": [
    {
      "symbol": "BTCUSDT",
      "direction": "long",
      "size": 0.1,
      "entry_price": 50000.0,
      "current_price": 51000.0,
      "entry_time": "2024-01-15T10:00:00",
      "take_profit_levels": [
        {"price": 52000.0, "amount": 50.0},
        {"price": 54000.0, "amount": 50.0}
      ],
      "stop_loss_price": 48000.0,
      "pnl": 100.0,
      "pnl_percent": 2.0
    }
  ],
  "total_trades": 25,
  "winning_trades": 15,
  "losing_trades": 10,
  "total_pnl": 500.0,
  "total_pnl_percent": 5.0,
  "max_drawdown": 2.5,
  "current_drawdown": 0.0,
  "started_at": "2024-01-01T00:00:00",
  "last_updated": "2024-01-15T12:30:00",
  "_metadata": {
    "version": "1.0",
    "saved_at": "2024-01-15T12:30:00",
    "bot_id": "my_bot_1"
  }
}
```

---

## Portfolio Backtest Engine

The Portfolio Backtest Engine allows testing bot configurations on historical data across multiple symbols.

### Features

**Multi-Symbol Testing:**
- Test multiple symbols simultaneously
- Shared capital management
- Realistic position sizing

**Comprehensive Metrics:**
- Win rate and profit factor
- Sharpe ratio
- Maximum drawdown
- Total P&L and P&L percentage
- Per-symbol statistics
- Daily equity curve

**Realistic Simulation:**
- Commission calculation
- Slippage simulation
- Stop-loss and take-profit execution
- Position management

### Usage

```python
from app.core.bots.backtest import PortfolioBacktest

# Create backtest
backtest = PortfolioBacktest(
    bot_config=bot_config,
    start_date="2024-01-01",
    end_date="2024-02-01"
)

# Run backtest
result = backtest.run()

# Access results
print(f"Total Trades: {result.total_trades}")
print(f"Win Rate: {result.win_rate:.2f}%")
print(f"Total P&L: ${result.total_pnl:.2f} ({result.total_pnl_percent:.2f}%)")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.2f}%")
print(f"Profit Factor: {result.profit_factor:.2f}")

# Per-symbol statistics
for symbol_stat in result.symbol_stats:
    print(f"{symbol_stat['symbol']}: {symbol_stat['trades']} trades, "
          f"{symbol_stat['pnl_percent']:.2f}% P&L")

# Equity curve
for point in result.equity_curve:
    print(f"{point['date']}: ${point['equity']:.2f}")
```

### API Usage

```bash
# Run backtest via API
POST /api/bots/backtest
{
  "bot_id": "my_bot_123",
  "start_date": "2024-01-01",
  "end_date": "2024-02-01"
}

# Quick backtest (last 30 days)
GET /api/bots/{bot_id}/backtest-quick?days=30
```

### Result Format

```json
{
  "success": true,
  "result": {
    "total_trades": 25,
    "winning_trades": 15,
    "losing_trades": 10,
    "win_rate": 60.0,
    "total_pnl": 550.0,
    "total_pnl_percent": 5.5,
    "profit_factor": 2.5,
    "sharpe_ratio": 1.8,
    "max_drawdown": 2.5,
    "symbol_stats": [
      {
        "symbol": "BTCUSDT",
        "trades": 15,
        "pnl": 350.0,
        "pnl_percent": 3.5
      },
      {
        "symbol": "ETHUSDT",
        "trades": 10,
        "pnl": 200.0,
        "pnl_percent": 2.0
      }
    ],
    "equity_curve": [
      {"date": "2024-01-01", "equity": 10000.0},
      {"date": "2024-01-02", "equity": 10050.0},
      ...
    ]
  }
}
```

---

## Bot Configuration Optimizer

The Optimizer finds the best bot configuration by testing different symbol combinations and parameters.

### Features

**Grid Search Optimization:**
- Test multiple symbol combinations
- Optimize for different metrics
- Parallel backtesting

**Optimization Metrics:**
- Sharpe ratio (risk-adjusted returns)
- Profit factor (wins/losses ratio)
- Win rate (percentage of winning trades)
- Total P&L percentage

**Smart Testing:**
- Tests symbol combinations
- Limits max combinations tested
- Returns all results sorted by score

### Usage

```python
from app.core.bots.optimizer import BotConfigOptimizer, quick_optimize

# Full optimizer
optimizer = BotConfigOptimizer(
    base_config=bot_config,
    symbol_candidates=["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT"],
    metric="sharpe"  # or "profit_factor", "win_rate", "pnl_percent"
)

result = optimizer.optimize(
    start_date="2024-01-01",
    end_date="2024-02-01",
    max_combinations=50
)

# Quick optimize helper
result = quick_optimize(
    base_config=bot_config,
    symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
    metric="sharpe",
    start_date="2024-01-01",
    end_date="2024-02-01"
)

# Access results
print(f"Best Score: {result.best_score:.4f}")
print(f"Best Config: {result.best_config}")
print(f"Tested Combinations: {result.tested_combinations}")

# All results sorted by score
for combo_result in result.all_results[:5]:  # Top 5
    print(f"Score: {combo_result['score']:.4f}, "
          f"Symbols: {combo_result['symbols']}")
```

### API Usage

```bash
# Optimize configuration
POST /api/bots/optimize
{
  "bot_id": "my_bot_123",
  "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
  "metric": "sharpe",
  "start_date": "2024-01-01",
  "end_date": "2024-02-01",
  "max_combinations": 50
}

# Quick optimize (last 30 days)
GET /api/bots/{bot_id}/optimize-quick?metric=sharpe&days=30
```

### Result Format

```json
{
  "success": true,
  "result": {
    "best_score": 2.5,
    "best_config": {
      "symbols": ["BTCUSDT", "ETHUSDT"],
      "allocation": {"BTCUSDT": 50.0, "ETHUSDT": 50.0}
    },
    "tested_combinations": 10,
    "all_results": [
      {
        "score": 2.5,
        "symbols": ["BTCUSDT", "ETHUSDT"],
        "backtest": {
          "total_pnl_percent": 8.5,
          "win_rate": 65.0,
          "sharpe_ratio": 2.5
        }
      },
      {
        "score": 2.2,
        "symbols": ["BTCUSDT"],
        "backtest": {
          "total_pnl_percent": 6.0,
          "win_rate": 60.0,
          "sharpe_ratio": 2.2
        }
      }
    ]
  }
}
```

---

## Integration Examples

### Complete Bot Lifecycle with All Components

```python
from app.core.bots.models import BotConfig, BotSymbolConfig, StrategyConfig
from app.core.bots.risk_manager import PositionRiskManager, RiskLimits
from app.core.bots.state_persistence import save_bot_state, load_bot_state, BotState
from app.core.bots.backtest import PortfolioBacktest
from app.core.bots.optimizer import quick_optimize

# 1. Optimize configuration
print("Step 1: Optimizing configuration...")
result = quick_optimize(
    base_config=base_config,
    symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT"],
    metric="sharpe",
    start_date="2024-01-01",
    end_date="2024-02-01"
)
optimized_config = result.best_config
print(f"Best configuration found with Sharpe: {result.best_score:.2f}")

# 2. Run backtest on optimized config
print("\nStep 2: Running backtest...")
backtest = PortfolioBacktest(
    bot_config=optimized_config,
    start_date="2024-01-01",
    end_date="2024-03-01"
)
backtest_result = backtest.run()
print(f"Backtest results: {backtest_result.total_trades} trades, "
      f"{backtest_result.total_pnl_percent:.2f}% P&L, "
      f"Sharpe: {backtest_result.sharpe_ratio:.2f}")

# 3. Initialize bot with risk management
print("\nStep 3: Initializing bot with risk management...")
risk_limits = RiskLimits(
    max_positions=5,
    max_position_size_percent=20.0,
    max_drawdown_percent=15.0,
    max_daily_loss_percent=5.0
)
risk_manager = PositionRiskManager(optimized_config, risk_limits)

# 4. Simulate trading with risk checks and state persistence
print("\nStep 4: Simulating trading...")
# Open position
can_open, violation, msg = risk_manager.can_open_position(
    symbol="BTCUSDT",
    direction=SignalDirection.LONG,
    position_size=0.1,
    current_price=50000.0
)

if can_open:
    risk_manager.add_position("BTCUSDT", SignalDirection.LONG, 0.1, 50000.0)

    # Save state
    bot_state = create_bot_state_from_risk_manager(risk_manager, "my_bot_1", "running")
    save_bot_state("my_bot_1", bot_state)
    print("Bot state saved successfully")

    # Update prices
    risk_manager.update_position_prices("BTCUSDT", 51000.0)

    # Check drawdown
    is_violated, drawdown = risk_manager.check_drawdown()
    if is_violated:
        print(f"WARNING: Drawdown limit exceeded: {drawdown:.2f}%")

    # Close position
    pnl = 100.0
    risk_manager.remove_position("BTCUSDT", 51000.0, pnl)

    # Save updated state
    final_state = create_bot_state_from_risk_manager(risk_manager, "my_bot_1", "stopped")
    save_bot_state("my_bot_1", final_state)
    print(f"Trading complete. Final capital: ${risk_manager.current_capital:.2f}")

# 5. Demonstrate recovery
print("\nStep 5: Demonstrating recovery...")
loaded_state = load_bot_state("my_bot_1")
if loaded_state:
    print(f"Recovered bot state: {loaded_state.name}")
    print(f"Capital: ${loaded_state.current_capital:.2f}")
    print(f"Total trades: {loaded_state.total_trades}")
```

### Error Handling Best Practices

```python
try:
    # Check risk before opening position
    can_open, violation, msg = risk_manager.can_open_position(
        symbol=symbol,
        direction=direction,
        position_size=size,
        current_price=price
    )

    if not can_open:
        logger.warning(f"Position rejected: {violation.value} - {msg}")
        return False

    # Open position
    risk_manager.add_position(symbol, direction, size, price)

    # Save state after each position change
    state = create_bot_state(risk_manager, bot_id, "running")
    success = save_bot_state(bot_id, state)

    if not success:
        logger.error("Failed to save bot state")
        # Could trigger emergency shutdown

    return True

except Exception as e:
    logger.error(f"Error opening position: {e}", exc_info=True)
    # Save error state
    error_state = create_error_state(risk_manager, bot_id, str(e))
    save_bot_state(bot_id, error_state)
    return False
```

---

## Testing

All components have comprehensive test coverage:

### Integration Tests (7 tests)
- Bot with Risk Manager integration
- Risk Manager with State Persistence
- Multiple positions risk management
- Complete position lifecycle
- Drawdown protection
- State restoration after crash
- Concurrent positions risk limits

### API Tests (11 tests)
- Backtest endpoints (success, errors, defaults)
- Optimizer endpoints (success, errors, metrics)
- Quick endpoints
- Bot not found scenarios
- Error handling

Run tests:
```bash
# All bot system tests
pytest backend/app/tests/test_bot_integration.py -v
pytest backend/app/tests/test_bot_api.py -v

# Specific components
pytest backend/app/tests/test_risk_manager.py -v
pytest backend/app/tests/test_state_persistence.py -v
pytest backend/app/tests/test_portfolio_backtest.py -v
pytest backend/app/tests/test_optimizer.py -v
```

---

## Configuration Reference

### RiskLimits Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_positions` | 5 | Maximum concurrent positions |
| `max_position_size_percent` | 20.0 | Max position size as % of capital |
| `max_drawdown_percent` | 15.0 | Max portfolio drawdown % |
| `max_daily_loss_percent` | 5.0 | Max daily loss % |
| `max_symbol_exposure_percent` | 30.0 | Max exposure to single symbol % |
| `min_capital_reserve_percent` | 10.0 | Min capital to keep in reserve % |
| `max_trades_per_day` | 50 | Max trades per day |
| `max_trades_per_symbol` | 10 | Max trades per symbol per day |

### Optimization Metrics

| Metric | Description | Best For |
|--------|-------------|----------|
| `sharpe` | Risk-adjusted returns | Balanced strategies |
| `profit_factor` | Gross profit / Gross loss | High win rate strategies |
| `win_rate` | Percentage of winning trades | Conservative strategies |
| `pnl_percent` | Total P&L percentage | Aggressive strategies |

---

## Performance Considerations

### State Persistence
- States are saved synchronously (blocking)
- Backups cleanup happens automatically
- Large position counts may slow down saves
- Consider async saving for high-frequency bots

### Backtesting
- Memory usage scales with date range
- Parallel symbol backtesting not implemented
- Consider chunking long date ranges
- Cache market data for repeated backtests

### Optimization
- Computational cost grows exponentially with symbol count
- Use `max_combinations` to limit search space
- Consider pre-filtering symbol candidates
- Run optimization during off-hours

---

## Troubleshooting

### Common Issues

**1. Risk checks failing unexpectedly**
- Check current capital hasn't decreased below limits
- Verify daily statistics are being reset properly
- Ensure position prices are being updated

**2. State loading returns None**
- Check file exists in state directory
- Verify JSON format is valid
- Check file permissions

**3. Backtest running slowly**
- Reduce date range
- Use fewer symbols
- Check market data availability

**4. Optimizer not finding good results**
- Increase `max_combinations`
- Try different metrics
- Expand symbol candidates
- Adjust date range

---

## Migration Guide

### Upgrading from Previous Versions

**Adding Risk Management to Existing Bot:**
```python
# Before
bot = TradingBot(config)
bot.start()

# After
from app.core.bots.risk_manager import PositionRiskManager, RiskLimits

risk_limits = RiskLimits()  # Use defaults
risk_manager = PositionRiskManager(config, risk_limits)

bot = TradingBot(config, risk_manager=risk_manager)
bot.start()
```

**Adding State Persistence:**
```python
from app.core.bots.state_persistence import save_bot_state, BotState

# In bot's main loop
def save_current_state(self):
    state = BotState(
        bot_id=self.id,
        name=self.config.name,
        status=self.status,
        # ... other fields
    )
    save_bot_state(self.id, state)

# Call periodically or on position changes
self.save_current_state()
```

---

## API Reference

See [API Documentation](../api/bots-api.md) for complete REST API reference.

## Support

For issues or questions:
- GitHub Issues: https://github.com/yourusername/komass/issues
- Documentation: https://docs.komass.io
