# KOMAS - Advanced Cryptocurrency Trading System

Professional-grade cryptocurrency trading platform with automated bots, technical indicators, backtesting, and portfolio management.

> **⚠️ IMPORTANT: PAPER TRADING ONLY**
> KOMAS v4.0 operates **exclusively in paper trading mode** (simulation).
> All trades are executed on historical data for backtesting purposes only.
> **NO REAL TRADING** - API keys are NOT used for live order execution.

## 🚀 Features

### Trading Bots System (Paper Trading)
- **Paper Trading Engine** - Automated strategy simulation on historical data
- **Backtest Engine** - Test strategies across multiple symbols and timeframes
- **Position Risk Manager** - Multi-layered risk control with drawdown protection
- **State Persistence** - Automatic state saving and recovery
- **Configuration Optimizer** - Find optimal bot settings using grid search

### Technical Indicators
- **Dominant Strategy** - Advanced trend-following system
- **TRG Indicator** - Trend Recognition Gauge with multiple timeframes
- **Custom Indicators** - Extensible indicator framework

### Portfolio Management
- Multi-symbol position tracking
- Real-time P&L calculations
- Equity curve visualization
- Risk metrics and statistics

### Data & Analytics
- Historical data management
- Economic calendar integration
- Advanced filtering system
- Performance heatmaps

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Bot System](#bot-system)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

## 🔧 Installation

### Prerequisites
- Python 3.11+
- Node.js 16+ (for frontend)
- Git

### Quick Install

**Windows:**
```bash
# Clone repository
git clone https://github.com/yourusername/komass.git
cd komass

# Install dependencies
install.bat

# Start system
start.bat
```

**Linux/Mac:**
```bash
# Clone repository
git clone https://github.com/yourusername/komass.git
cd komass

# Install backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt

# Install frontend
cd ../frontend
npm install

# Start services
# Terminal 1:
cd backend
uvicorn app.main:app --reload

# Terminal 2:
cd frontend
npm start
```

## 🎯 Quick Start

### 1. Create Your First Bot

```python
from app.core.bots.models import BotConfig, BotSymbolConfig, StrategyConfig, TakeProfitLevel

# Create bot configuration
config = BotConfig(
    name="My First Bot",
    initial_capital=10000.0,
    leverage=1,
    symbols=[
        BotSymbolConfig(symbol="BTCUSDT", allocation_percent=50.0),
        BotSymbolConfig(symbol="ETHUSDT", allocation_percent=50.0)
    ],
    strategy=StrategyConfig(
        name="Dominant",
        stop_loss_percent=2.0,
        take_profit_levels=[
            TakeProfitLevel(level=1, percent=2.0, amount=50.0),
            TakeProfitLevel(level=2, percent=4.0, amount=50.0)
        ]
    )
)
```

### 2. Run Backtest

```python
from app.core.bots.backtest import PortfolioBacktest

# Test on historical data
backtest = PortfolioBacktest(
    bot_config=config,
    start_date="2024-01-01",
    end_date="2024-02-01"
)

result = backtest.run()
print(f"Total P&L: {result.total_pnl_percent:.2f}%")
print(f"Win Rate: {result.win_rate:.2f}%")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

### 3. Optimize Configuration

```python
from app.core.bots.optimizer import quick_optimize

# Find best symbol combination
result = quick_optimize(
    base_config=config,
    symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT"],
    metric="sharpe",
    start_date="2024-01-01",
    end_date="2024-02-01"
)

print(f"Best configuration: {result.best_config}")
print(f"Sharpe Ratio: {result.best_score:.2f}")
```

### 4. Run Live Trading

```python
from app.core.bots.risk_manager import PositionRiskManager, RiskLimits

# Create risk manager
risk_limits = RiskLimits(
    max_positions=5,
    max_position_size_percent=20.0,
    max_drawdown_percent=15.0,
    max_daily_loss_percent=5.0
)

risk_manager = PositionRiskManager(config, risk_limits)

# Bot will automatically check risk before opening positions
```

## 🤖 Bot System

### Position Risk Manager

Comprehensive risk management system:
- **Position Limits** - Max 5 concurrent positions (configurable)
- **Size Limits** - Max 20% capital per position
- **Drawdown Protection** - Stop at 15% portfolio drawdown
- **Daily Loss Limits** - Max 5% daily loss
- **Symbol Exposure** - Max 30% in single symbol
- **Trading Limits** - Max 50 trades/day, 10 per symbol

[Full Documentation](docs/components/bot-system.md#position-risk-manager)

### State Persistence

Automatic state saving and recovery:
- JSON-based state files
- Automatic timestamped backups (last 10)
- Recover all active bots after restart
- Complete position and capital tracking

[Full Documentation](docs/components/bot-system.md#state-persistence)

### Portfolio Backtest

Test strategies on historical data:
- Multi-symbol testing with shared capital
- Realistic commission and slippage
- Complete performance metrics
- Daily equity curve
- Per-symbol statistics

[Full Documentation](docs/components/bot-system.md#portfolio-backtest-engine)

### Configuration Optimizer

Find optimal bot settings:
- Grid search optimization
- Multiple metrics (Sharpe, profit factor, win rate, P&L)
- Symbol combination testing
- Parallel backtesting

[Full Documentation](docs/components/bot-system.md#bot-configuration-optimizer)

## 📡 API Documentation

### Backtest Endpoints

```bash
# Run backtest
POST /api/bots/backtest
{
  "bot_id": "bot_123",
  "start_date": "2024-01-01",
  "end_date": "2024-02-01"
}

# Quick backtest (last 30 days)
GET /api/bots/{bot_id}/backtest-quick?days=30
```

### Optimizer Endpoints

```bash
# Optimize configuration
POST /api/bots/optimize
{
  "bot_id": "bot_123",
  "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT"],
  "metric": "sharpe",
  "start_date": "2024-01-01",
  "end_date": "2024-02-01"
}

# Quick optimize
GET /api/bots/{bot_id}/optimize-quick?metric=sharpe&days=30
```

### Bot Management

```bash
# List all bots
GET /api/bots/

# Get bot details
GET /api/bots/{bot_id}

# Create bot
POST /api/bots/

# Start/Stop bot
POST /api/bots/{bot_id}/start
POST /api/bots/{bot_id}/stop

# Get statistics
GET /api/bots/{bot_id}/statistics

# Get open positions
GET /api/bots/{bot_id}/positions/open
```

Full API documentation: [API Reference](docs/api/bots-api.md)

## 🧪 Testing

### Run All Tests

```bash
cd backend
pytest -v
```

### Test Coverage

**Bot System Tests:**
- Integration Tests: 7 tests ✅
- API Tests: 11 tests ✅
- Risk Manager: 14 tests ✅
- State Persistence: 11 tests ✅
- Portfolio Backtest: 10 tests ✅
- Optimizer: 8 tests ✅

**Total: 61+ tests passing**

---

## 📈 Project Status (Updated: January 14, 2026)

### Current Phase: **v4.0 (70% Complete)**

| Phase | Status | Details |
|-------|--------|---------|
| **Phase 1-6** | ✅ Complete | Stabilization, Dominant, Presets, Filters, Optimization |
| **Phase 7** | ✅ Complete | Bot Configuration System (883 lines) |
| **Phase 8** | ✅ Complete | Bot Backtest Engine (747 lines) |
| **Phase 9** | ✅ Complete | Bot Optimizer (427 lines) |
| **Phase 10** | ✅ Complete | Live Trading Engine (771 lines) |
| **Phase 11** | ⚠️ Partial | Telegram Integration (infrastructure ready) |
| **Phase 12-15** | ⏳ Pending | Design, QA, Deployment, Finalization |

### Key Achievements:
- 🚀 **Full Bot System** implemented with risk management
- 🔄 **Live Trading Engine** with APScheduler
- 💾 **State Persistence** with automatic recovery
- 📊 **Portfolio Backtest** across multiple symbols
- ⚡ **Bot Optimizer** for configuration tuning
- 🎯 **Signal Scoring** (A-F grades)
- 🎨 **Modern UI** with React + TailwindCSS

### What's Next:
1. Complete Telegram integration configuration
2. UI/UX redesign (Phase 12)
3. Comprehensive QA & testing (Phase 13)
4. GitHub Actions CI/CD (Phase 14)
5. Production release v4.0 (Phase 15)

### Run Specific Test Suites

```bash
# Integration tests
pytest app/tests/test_bot_integration.py -v

# API tests
pytest app/tests/test_bot_api.py -v

# Component tests
pytest app/tests/test_risk_manager.py -v
pytest app/tests/test_state_persistence.py -v
pytest app/tests/test_portfolio_backtest.py -v
pytest app/tests/test_optimizer.py -v
```

## 📁 Project Structure

```
komass/
├── backend/
│   ├── app/
│   │   ├── api/              # REST API endpoints
│   │   │   ├── bots_routes.py
│   │   │   ├── data_routes.py
│   │   │   └── indicator_routes.py
│   │   ├── core/
│   │   │   └── bots/         # Bot system components
│   │   │       ├── models.py
│   │   │       ├── risk_manager.py
│   │   │       ├── state_persistence.py
│   │   │       ├── backtest.py
│   │   │       ├── optimizer.py
│   │   │       └── runner.py
│   │   ├── indicators/       # Technical indicators
│   │   ├── filters/          # Signal filters
│   │   ├── database/         # Database models
│   │   └── tests/            # Test suite
│   │       ├── test_bot_integration.py
│   │       ├── test_bot_api.py
│   │       ├── test_risk_manager.py
│   │       ├── test_state_persistence.py
│   │       ├── test_portfolio_backtest.py
│   │       └── test_optimizer.py
│   ├── data/
│   │   └── bot_states/       # Persistent bot states
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API clients
│   │   └── utils/            # Utilities
│   └── package.json
│
├── docs/
│   ├── components/           # Component documentation
│   │   └── bot-system.md
│   ├── plans/                # Development plans
│   └── chats/                # Chat logs
│
├── scripts/
│   ├── install/              # Installation scripts
│   ├── tests/                # Test runners
│   ├── management/           # System management
│   └── utils/                # Utilities
│
├── install.bat               # Main installer
├── start.bat                 # Main launcher
└── README.md
```

## 🎨 Features Showcase

### Risk Management Dashboard
```
Capital: $10,000 → $10,500 (+5.0%)
Peak: $10,600
Drawdown: 0.9% / 15.0% limit ✅

Active Positions: 2 / 5
Total Exposure: $3,200 (32%)

Daily Stats:
├─ P&L: +$150 (+1.5%)
├─ Trades: 8 / 50 limit
└─ Loss Limit: OK ✅
```

### Backtest Results
```
Period: 2024-01-01 to 2024-02-01 (32 days)
═══════════════════════════════════════
Total Trades: 25
Winning: 15 (60.0%)
Losing: 10 (40.0%)

P&L: $550 (+5.5%)
Profit Factor: 2.5
Sharpe Ratio: 1.8
Max Drawdown: 2.5%

Symbol Stats:
├─ BTCUSDT: 15 trades, +$350 (+3.5%)
└─ ETHUSDT: 10 trades, +$200 (+2.0%)
```

### Optimization Results
```
Tested 10 combinations
Best Score: 2.5 (Sharpe Ratio)

Best Configuration:
├─ Symbols: BTCUSDT, ETHUSDT
├─ Allocation: 50% / 50%
├─ Win Rate: 65%
├─ P&L: +8.5%
└─ Max Drawdown: 3.2%

Top 3 Configs:
1. [BTC, ETH] - Sharpe: 2.5 ⭐
2. [BTC] - Sharpe: 2.2
3. [BTC, ETH, BNB] - Sharpe: 2.0
```

## 🛠️ Configuration

### Environment Variables

Create `.env` in backend directory:
```bash
# Database
DATABASE_URL=sqlite:///./komas.db

# API Keys (optional)
BINANCE_API_KEY=your_key
BINANCE_SECRET_KEY=your_secret

# Trading
DEFAULT_LEVERAGE=1
DEFAULT_COMMISSION=0.075

# Risk Limits
MAX_POSITIONS=5
MAX_POSITION_SIZE_PERCENT=20.0
MAX_DRAWDOWN_PERCENT=15.0
MAX_DAILY_LOSS_PERCENT=5.0
```

### Bot Configuration File

```json
{
  "name": "My Bot",
  "initial_capital": 10000,
  "leverage": 1,
  "symbols": [
    {"symbol": "BTCUSDT", "allocation_percent": 50.0},
    {"symbol": "ETHUSDT", "allocation_percent": 50.0}
  ],
  "strategy": {
    "name": "Dominant",
    "stop_loss_percent": 2.0,
    "take_profit_levels": [
      {"level": 1, "percent": 2.0, "amount": 50.0},
      {"level": 2, "percent": 4.0, "amount": 50.0}
    ]
  }
}
```

## 📚 Documentation

- [Bot System Documentation](docs/components/bot-system.md)
- [API Reference](docs/api/bots-api.md)
- [Development Plans](docs/plans/)
- [Scripts README](scripts/README.md)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Workflow

```bash
# Create new feature branch
git checkout -b feature/my-feature

# Make changes and test
pytest -v

# Commit with descriptive message
git commit -m "feat: add new feature"

# Push to your fork
git push origin feature/my-feature

# Create PR on GitHub
```

## 📊 Performance

### System Requirements
- **Minimum**: 2GB RAM, 2 CPU cores
- **Recommended**: 4GB RAM, 4 CPU cores
- **Storage**: 1GB for application + market data

### Typical Performance
- Backtest (30 days, 2 symbols): ~2-5 seconds
- Optimization (10 combinations): ~20-50 seconds
- State save/load: < 100ms
- Risk checks: < 1ms

## 🔒 Security

- API keys stored in environment variables
- State files saved with restricted permissions
- SQL injection protection via ORM
- Rate limiting on API endpoints
- Input validation and sanitization

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Built with FastAPI, React, and Python
- Market data from Binance
- Technical indicators based on industry standards

## 📧 Contact

- GitHub Issues: [Report a bug](https://github.com/yourusername/komass/issues)
- Documentation: [Read the docs](https://docs.komass.io)
- Email: support@komass.io

---

**Made with ❤️ for algorithmic traders**

*Last updated: January 2026*
