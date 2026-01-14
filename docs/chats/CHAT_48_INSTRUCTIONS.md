# Chat #48 — Preset Optimizer Heatmap

> **Phase:** 6 — Preset Optimization  
> **Previous:** #47 Preset Optimizer Results ✅  
> **Next:** #49 QA Checkpoint #8

---

## 🎯 GOAL

Implement a heatmap visualization for preset optimization results, showing performance matrix of presets × pairs with interactive features.

---

## 📋 TASKS

### Backend
- [ ] Add `/api/optimizer/results/{run_id}/heatmap` endpoint
- [ ] Matrix generation by metric (PnL/WinRate/DD/Sharpe)
- [ ] Color scale calculation (min/max normalization)
- [ ] Export heatmap data as CSV

### Frontend
- [ ] HeatmapPanel.jsx component
- [ ] Matrix grid visualization
- [ ] Color scale legend (green-yellow-red)
- [ ] Metric selector (PnL/WinRate/DD/Sharpe)
- [ ] Interactive tooltips with full metrics
- [ ] Row/column highlighting on hover
- [ ] Zoom controls for large matrices
- [ ] Export button

### Integration
- [ ] Integrate with ResultsPanel
- [ ] Tab switching between table and heatmap views
- [ ] Sync filters (search, grade) with heatmap

### Tests
- [ ] Matrix generation tests
- [ ] Color scale tests
- [ ] Export tests

---

## 📁 FILES

```
backend/app/api/optimizer_routes.py     # Add heatmap endpoint
frontend/src/components/Optimizer/
├── HeatmapPanel.jsx                    # NEW - Heatmap visualization
├── HeatmapLegend.jsx                   # NEW - Color scale legend
├── HeatmapCell.jsx                     # NEW - Interactive cell
└── index.js                            # UPDATE - Export new components
tests/test_optimizer_heatmap.py         # NEW - Tests
```

---

## 🎨 UI MOCKUP

```
┌─────────────────────────────────────────────────────────────────┐
│  🗺️ HEATMAP VIEW                    [Metric: PnL% ▼] [Export]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Legend:  ████ -20%  ████ 0%  ████ +20%  ████ +40%  ████ +60%  │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│         │ BTC   │ ETH   │ SOL   │ BNB   │ LINK  │ AVAX  │ ... │
│─────────┼───────┼───────┼───────┼───────┼───────┼───────┼─────│
│ T_60_40 │ ████  │ ████  │ ████  │ ████  │ ████  │ ████  │     │
│         │ +45%  │ +38%  │ +31%  │ +28%  │ +25%  │ +22%  │     │
│─────────┼───────┼───────┼───────┼───────┼───────┼───────┼─────│
│ S_80_55 │ ████  │ ████  │ ████  │ ████  │ ████  │ ████  │     │
│         │ +38%  │ +32%  │ +25%  │ +21%  │ +18%  │ +15%  │     │
│─────────┼───────┼───────┼───────┼───────┼───────┼───────┼─────│
│ M_45_30 │ ████  │ ████  │ ████  │ ████  │ ████  │ ████  │     │
│         │ +32%  │ +28%  │ +22%  │ +18%  │ +14%  │ +10%  │     │
│─────────┼───────┼───────┼───────┼───────┼───────┼───────┼─────│
│  ...    │       │       │       │       │       │       │     │
└─────────────────────────────────────────────────────────────────┘

Tooltip (on hover):
┌─────────────────────────┐
│ T_60_40 × BTCUSDT       │
│ ─────────────────────── │
│ PnL: +45.2%             │
│ Win Rate: 68.5%         │
│ Max DD: 12.3%           │
│ Sharpe: 2.1             │
│ Trades: 45              │
└─────────────────────────┘
```

---

## 📊 METRICS FOR HEATMAP

| Metric | Description | Color Scale |
|--------|-------------|-------------|
| PnL % | Total profit/loss | Red (-) → Green (+) |
| Win Rate | Percentage of winning trades | Red (<50%) → Green (>70%) |
| Max DD | Maximum drawdown | Green (low) → Red (high) |
| Sharpe | Risk-adjusted return | Red (<1) → Green (>2) |

---

## 📝 GIT COMMIT

```
feat: add heatmap visualization for optimization results

- Add matrix generation endpoint
- Add HeatmapPanel with interactive grid
- Add color scale legend and metric selector
- Add tooltips with full metrics
- Add zoom controls and export
- Add unit tests

Chat #48: Preset Optimizer Heatmap
```

---

**Next chat:** #49 — QA Checkpoint #8
