# Chat #45 — Preset Optimizer Core

> **Phase:** 6 — Preset Optimization  
> **Previous:** #44 Filters UI ✅  
> **Next:** #46 Preset Optimizer Modes

---

## 🎯 GOAL

Create the core preset optimization engine:
- Multi-pair backtest runner
- Preset scoring system
- Matrix generation (preset × pair)
- SSE streaming for progress updates
- Aggregation of results across pairs

---

## 📋 TASKS

- [ ] `preset_optimizer.py` — Main optimizer class
- [ ] Multi-pair parallel backtest runner
- [ ] Preset scoring metrics calculation
- [ ] Result matrix generation
- [ ] SSE streaming endpoint
- [ ] API routes for preset optimization
- [ ] Unit tests

### PresetOptimizer Class
```python
class PresetOptimizer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    async def run_optimization(
        self,
        presets: List[str],
        pairs: List[str],
        timeframe: str,
        start_date: str,
        end_date: str,
        progress_callback: Callable = None
    ) -> OptimizationResult:
        """Run backtest for all preset × pair combinations"""
        pass
        
    def calculate_scores(self, results: Dict) -> Dict:
        """Calculate aggregate scores for each preset"""
        pass
        
    def generate_matrix(self, results: Dict) -> pd.DataFrame:
        """Generate result matrix"""
        pass
```

### Scoring Metrics
```python
# Per preset aggregate metrics:
- avg_pnl: Average PnL across all pairs
- avg_win_rate: Average win rate
- avg_sharpe: Average Sharpe ratio
- consistency: Standard deviation of PnL
- positive_pairs: Number of pairs with positive PnL
- max_dd_avg: Average max drawdown
- stability_score: Combined metric (0-100)
```

### API Endpoints
```
POST /api/optimizer/presets/run         - Start optimization
GET  /api/optimizer/presets/stream      - SSE progress stream
GET  /api/optimizer/presets/results     - Get results
POST /api/optimizer/presets/cancel      - Cancel running optimization
```

- [ ] Integration with existing backtest engine
- [ ] ProcessPoolExecutor for parallelization

---

## 📁 FILES

```
backend/app/
├── services/
│   └── preset_optimizer.py    # Main optimizer class
├── api/
│   └── optimizer_routes.py    # API endpoints
└── tests/
    └── test_preset_optimizer.py

frontend/src/
└── api.js                     # Add optimizer API methods
```

---

## 📝 GIT COMMIT

```
feat: Add preset optimizer core

- Add PresetOptimizer class for multi-pair backtest
- Add preset scoring system with stability metrics
- Add result matrix generation
- Add SSE streaming for optimization progress
- Add optimizer API routes
- Add ProcessPoolExecutor parallelization
- Add 30+ unit tests

Chat #45: Preset Optimizer Core
```

---

**Next chat:** #46 — Preset Optimizer Modes
