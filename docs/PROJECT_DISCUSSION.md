# KOMAS Trading System - Project Discussion

**Date:** 2026-01-14
**Status:** Architecture Review & Planning

---

## Current State Analysis

### What Was Built (v4.0)
- Full bot management system (CRUD, state management)
- Position tracking with TP/SL monitoring
- Paper trading simulation
- TRG indicator + filters (SuperTrend, RSI, ADX, Volume)
- Telegram/Discord notifications
- Backtesting engine
- React frontend with dashboards

### Problem
The system is **overcomplicated** for the actual use case:
- Cornix will execute trades from Telegram signals
- No need for internal position tracking
- No need for paper trading simulation
- But NEED robust **system-level** testing and risk management

---

## User Requirements (Clarified)

### Core Needs:
1. **All Binance pairs** - continuous live data download
2. **All timeframes** - 1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
3. **System-level testing** - not per-pair optimization
4. **Drawdown protection** - prevent large losses
5. **Signal to Telegram** → Cornix executes

### Key Insight:
> "Мне нужно тестировать не каждую пару а именно СИСТЕМУ в общем"

This means:
- Same strategy parameters across ALL pairs
- System performance = aggregate of all pairs
- Risk management at PORTFOLIO level, not individual trades

---

## Revised Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    KOMAS TRADING SYSTEM v5.0                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   DATA LAYER (Live)                      │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐               │   │
│  │  │ Binance  │  │ Binance  │  │ Local    │               │   │
│  │  │ REST API │  │WebSocket │  │ Parquet  │               │   │
│  │  │ (OHLCV)  │  │ (Ticker) │  │ (Cache)  │               │   │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘               │   │
│  │       └─────────────┼─────────────┘                      │   │
│  │                     ▼                                    │   │
│  │            ┌────────────────┐                            │   │
│  │            │  Data Manager  │  All pairs, all TFs        │   │
│  │            └────────┬───────┘                            │   │
│  └─────────────────────┼───────────────────────────────────┘   │
│                        │                                        │
│  ┌─────────────────────▼───────────────────────────────────┐   │
│  │                 STRATEGY ENGINE                          │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │              INDICATOR LIBRARY                    │   │   │
│  │  │  • TRG (ATR bands + trend)                       │   │   │
│  │  │  • SuperTrend                                    │   │   │
│  │  │  • RSI (overbought/oversold)                     │   │   │
│  │  │  • ADX (trend strength)                          │   │   │
│  │  │  • Volume Filter                                 │   │   │
│  │  │  • [Future: more indicators]                     │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │                         │                                │   │
│  │  ┌──────────────────────▼───────────────────────────┐   │   │
│  │  │           SIGNAL GENERATOR                        │   │   │
│  │  │  • Scans ALL pairs simultaneously                │   │   │
│  │  │  • Applies SAME strategy params to all           │   │   │
│  │  │  • Generates BUY/SELL signals                    │   │   │
│  │  └──────────────────────┬───────────────────────────┘   │   │
│  └─────────────────────────┼───────────────────────────────┘   │
│                            │                                    │
│  ┌─────────────────────────▼───────────────────────────────┐   │
│  │              RISK MANAGEMENT (System-Level)              │   │
│  │                                                          │   │
│  │  ┌────────────────┐  ┌────────────────┐                 │   │
│  │  │ Drawdown Guard │  │ Exposure Limit │                 │   │
│  │  │ • Max DD: 10%  │  │ • Max open: 5  │                 │   │
│  │  │ • Daily: 3%    │  │ • Per symbol:1 │                 │   │
│  │  │ • Pause system │  │ • Correlation  │                 │   │
│  │  └────────────────┘  └────────────────┘                 │   │
│  │                                                          │   │
│  │  ┌────────────────┐  ┌────────────────┐                 │   │
│  │  │ Signal Filter  │  │ Time Filter    │                 │   │
│  │  │ • Min quality  │  │ • News events  │                 │   │
│  │  │ • Confirmation │  │ • Weekends     │                 │   │
│  │  │ • Anti-spam    │  │ • Low volume   │                 │   │
│  │  └────────────────┘  └────────────────┘                 │   │
│  │                            │                             │   │
│  │         ┌──────────────────▼──────────────────┐         │   │
│  │         │     SYSTEM STATE TRACKER            │         │   │
│  │         │  • Current equity curve             │         │   │
│  │         │  • Open signals count               │         │   │
│  │         │  • Daily P&L (from Cornix webhook?) │         │   │
│  │         │  • Drawdown monitoring              │         │   │
│  │         └──────────────────┬──────────────────┘         │   │
│  └────────────────────────────┼────────────────────────────┘   │
│                               │                                 │
│  ┌────────────────────────────▼────────────────────────────┐   │
│  │                    OUTPUT LAYER                          │   │
│  │                                                          │   │
│  │  ┌─────────────┐         ┌─────────────────────────┐    │   │
│  │  │  Telegram   │ ──────> │       CORNIX            │    │   │
│  │  │  Signal Bot │         │  • Parses signal        │    │   │
│  │  │  (Cornix    │         │  • Opens position       │    │   │
│  │  │   format)   │         │  • Manages TP/SL        │    │   │
│  │  └─────────────┘         │  • Reports back         │    │   │
│  │                          └─────────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 BACKTESTING MODULE                       │   │
│  │                                                          │   │
│  │  Purpose: Find OPTIMAL (not best) parameters            │   │
│  │                                                          │   │
│  │  ┌────────────────────────────────────────────────┐     │   │
│  │  │            SYSTEM-LEVEL BACKTEST               │     │   │
│  │  │                                                │     │   │
│  │  │  Input:                                        │     │   │
│  │  │  • Historical data (all pairs, all TFs)       │     │   │
│  │  │  • Strategy parameters to test                │     │   │
│  │  │                                                │     │   │
│  │  │  Process:                                      │     │   │
│  │  │  • Run strategy on ALL pairs simultaneously   │     │   │
│  │  │  • Aggregate results as PORTFOLIO             │     │   │
│  │  │  • Calculate system-level metrics             │     │   │
│  │  │                                                │     │   │
│  │  │  Output:                                       │     │   │
│  │  │  • Total return                               │     │   │
│  │  │  • Max drawdown (CRITICAL)                    │     │   │
│  │  │  • Sharpe ratio                               │     │   │
│  │  │  • Win rate                                   │     │   │
│  │  │  • Profit factor                              │     │   │
│  │  │  • Equity curve                               │     │   │
│  │  └────────────────────────────────────────────────┘     │   │
│  │                                                          │   │
│  │  ┌────────────────────────────────────────────────┐     │   │
│  │  │           PARAMETER OPTIMIZER                  │     │   │
│  │  │                                                │     │   │
│  │  │  Goal: Find "golden middle" - stable params   │     │   │
│  │  │                                                │     │   │
│  │  │  Method:                                       │     │   │
│  │  │  • Grid search / Walk-forward optimization    │     │   │
│  │  │  • Prioritize LOW DRAWDOWN over high return   │     │   │
│  │  │  • Out-of-sample validation                   │     │   │
│  │  │  • Robustness testing (different periods)     │     │   │
│  │  │                                                │     │   │
│  │  │  Avoid:                                        │     │   │
│  │  │  • Overfitting to historical data             │     │   │
│  │  │  • "Best" params that work on 1 period only   │     │   │
│  │  └────────────────────────────────────────────────┘     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Principles

### 1. System-Level Thinking
- **NOT**: "Find best params for BTCUSDT"
- **YES**: "Find params that work across ALL pairs with minimal drawdown"

### 2. Stability Over Profit
- **NOT**: Max return at any cost
- **YES**: Consistent returns with controlled risk

### 3. Drawdown Protection
```
Priority order:
1. Max Drawdown < 10% (hard limit)
2. Daily Drawdown < 3% (pause if exceeded)
3. Profitable (secondary goal)
```

### 4. Anti-Overfitting
```
Testing methodology:
1. In-sample: 70% of data - find parameters
2. Out-of-sample: 30% of data - validate
3. Walk-forward: Rolling window validation
4. Stress test: Major market events (crashes)
```

---

## Implementation Priority

### Phase 1: Data Infrastructure
- [ ] Binance data fetcher (all pairs)
- [ ] WebSocket for live prices
- [ ] Parquet storage for historical data
- [ ] Data manager with caching

### Phase 2: Core Engine
- [ ] Indicator library (TRG, filters)
- [ ] Signal generator (system-wide scan)
- [ ] Risk manager (drawdown guards)

### Phase 3: Backtesting
- [ ] System-level backtester
- [ ] Portfolio equity calculation
- [ ] Parameter optimizer (grid search)
- [ ] Walk-forward validation

### Phase 4: Live Trading
- [ ] Telegram signal sender (Cornix format)
- [ ] System state tracking
- [ ] Drawdown monitoring
- [ ] Auto-pause on limits

### Phase 5: UI (Optional)
- [ ] Simplified dashboard
- [ ] Backtest results viewer
- [ ] System status monitor

---

## Questions to Resolve

1. **Cornix feedback**: Can we get trade results back from Cornix?
   - If yes: proper P&L tracking
   - If no: estimate based on signals sent

2. **Drawdown calculation**: How to track real drawdown if Cornix executes?
   - Option A: Track signals sent + estimated outcomes
   - Option B: Cornix webhook integration
   - Option C: Manual sync

3. **Correlation filter**: Avoid opening BTC + ETH + BNB (all correlated) at same time?

4. **Timeframe priority**: Which TF to prioritize for signals?
   - 4h for swing trading?
   - 1h for more signals?
   - Multi-TF confirmation?

---

## Next Steps

1. Review this document
2. Decide: refactor current code or rebuild core modules?
3. Start with data infrastructure (most critical)
4. Build system-level backtester
5. Find optimal parameters
6. Connect to Telegram/Cornix

---

*This document will be updated as we progress.*
