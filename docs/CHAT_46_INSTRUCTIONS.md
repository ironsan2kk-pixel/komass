# Chat #46 — Preset Optimizer Modes

> **Phase:** 6 — Preset Optimization  
> **Previous:** #45 Preset Optimizer Core ✅  
> **Next:** #47 Preset Optimizer Results

---

## 🎯 GOAL

Implement optimization modes for different use cases:
- Quick mode for fast preliminary testing
- Standard mode for balanced optimization
- Smart mode with adaptive preset/pair selection
- Full mode for comprehensive optimization

---

## 📋 TASKS

- [ ] Add optimization modes to PresetOptimizer
- [ ] Quick mode: Top 20 presets × 5 most liquid pairs
- [ ] Standard mode: All presets × 10 pairs
- [ ] Smart mode: Correlation-based adaptive selection
- [ ] Full mode: All presets × all pairs
- [ ] Estimated time calculation based on mode
- [ ] Mode configuration in API
- [ ] Update frontend with mode selector
- [ ] Unit tests for each mode

### Optimization Modes

```python
class OptimizationMode(Enum):
    QUICK = "quick"      # ~100 combinations, < 1 min
    STANDARD = "standard"  # ~1000 combinations, < 5 min
    SMART = "smart"      # Adaptive, variable time
    FULL = "full"        # All combinations, 10+ min

class ModeConfig:
    QUICK = {
        "max_presets": 20,
        "max_pairs": 5,
        "pair_selection": "liquidity",  # Most liquid pairs
        "preset_selection": "top_performers"  # Previously best
    }
    
    STANDARD = {
        "max_presets": 100,
        "max_pairs": 10,
        "pair_selection": "diversity",  # Mix of majors + alts
        "preset_selection": "all"
    }
    
    SMART = {
        "correlation_threshold": 0.7,
        "min_diversity": 5,
        "preset_clustering": True
    }
    
    FULL = {
        "max_presets": None,  # All
        "max_pairs": None,    # All
    }
```

### Time Estimation

```python
def estimate_time(mode: str, num_presets: int, num_pairs: int) -> float:
    """Estimate optimization time in seconds"""
    base_time_per_backtest = 0.5  # seconds
    total_combinations = num_presets * num_pairs
    parallelization_factor = min(num_workers, 8)
    
    estimated_seconds = (total_combinations * base_time_per_backtest) / parallelization_factor
    return estimated_seconds
```

---

## 📁 FILES

```
backend/app/services/
├── preset_optimizer.py     # Update with modes
└── optimization_modes.py   # NEW: Mode configurations

backend/app/api/
└── optimizer_routes.py     # Update with mode parameter

frontend/src/
└── components/Optimizer/
    └── ModeSelector.jsx    # NEW: Mode selection UI
```

---

## 📝 GIT COMMIT

```
feat: Add optimization modes (quick/standard/smart/full)

- Add OptimizationMode enum
- Add ModeConfig with preset/pair selection strategies
- Add time estimation function
- Add liquidity-based pair ranking
- Add preset clustering for smart mode
- Add ModeSelector UI component
- Update API with mode parameter
- Add 15+ unit tests

Chat #46: Preset Optimizer Modes
```

---

**Next chat:** #47 — Preset Optimizer Results
