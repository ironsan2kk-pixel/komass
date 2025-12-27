# Chat #34 — Signal Score Core

> **Phase:** 4 — Signal Score  
> **Previous:** #31-33 Presets Full Module ✅  
> **Next:** #35 Score Multi-TF

---

## 🎯 GOAL

Implement the Signal Score system that evaluates trade quality on a 0-100 scale with A-F grades.

---

## 📋 TASKS

- [ ] Create `backend/app/services/signal_score.py`
- [ ] Implement SignalScorer class
- [ ] Component 1: Confluence (25 pts) — indicator agreement
- [ ] Component 2: Multi-TF Alignment (25 pts) — higher TF confirmation
- [ ] Component 3: Market Context (25 pts) — trend + volatility assessment
- [ ] Component 4: Technical Levels (25 pts) — S/R proximity
- [ ] Grade calculation: A (85+), B (70-84), C (55-69), D (40-54), F (<40)
- [ ] Integration with backtest trades (add score to each trade)
- [ ] API endpoint: GET /api/signal-score/calculate
- [ ] Unit tests

---

## 📝 SIGNAL SCORE SPECIFICATION

### Components (4 × 25 = 100 points)

| Component | Max Points | Criteria |
|-----------|------------|----------|
| **Confluence** | 25 | Multiple indicators agree on direction |
| **Multi-TF Alignment** | 25 | Higher timeframes confirm signal |
| **Market Context** | 25 | Trend strength + volatility conditions |
| **Technical Levels** | 25 | Distance from support/resistance |

### Grade Scale

| Score | Grade | Description |
|-------|-------|-------------|
| 85-100 | A | Excellent — high probability trade |
| 70-84 | B | Good — solid setup |
| 55-69 | C | Average — acceptable trade |
| 40-54 | D | Below Average — caution advised |
| 0-39 | F | Poor — avoid this trade |

### Confluence Scoring (25 pts)

```python
# TRG indicator
trg_direction = "long" if close > trend_line else "short"

# SuperTrend filter (if enabled)
supertrend_agrees = supertrend_direction == trg_direction

# RSI filter (if enabled)
rsi_agrees = (rsi < 70 and direction == "long") or (rsi > 30 and direction == "short")

# ADX filter (if enabled)
adx_strong = adx > 25

# Volume filter (if enabled)
volume_confirms = volume > volume_ma

# Calculate confluence score
confluence_score = 0
active_filters = count_active_filters()
if supertrend_agrees: confluence_score += 25 / active_filters
if rsi_agrees: confluence_score += 25 / active_filters
if adx_strong: confluence_score += 25 / active_filters
if volume_confirms: confluence_score += 25 / active_filters
```

### Multi-TF Alignment Scoring (25 pts)

```python
# Check higher timeframes (4H, 1D)
tf_scores = []
for tf in ["4h", "1d"]:
    tf_data = load_higher_tf(symbol, tf)
    tf_trend = calculate_trend(tf_data)
    if tf_trend == signal_direction:
        tf_scores.append(1)
    else:
        tf_scores.append(0)

# Weight: 4H = 10 pts, 1D = 15 pts
multi_tf_score = tf_scores[0] * 10 + tf_scores[1] * 15
```

### Market Context Scoring (25 pts)

```python
# Trend strength (0-15 pts)
atr_normalized = current_atr / sma(atr, 20)
if atr_normalized > 1.2:
    trend_score = 15  # Strong trend
elif atr_normalized > 0.8:
    trend_score = 10  # Normal trend
else:
    trend_score = 5   # Weak trend

# Volatility regime (0-10 pts)
volatility_percentile = calculate_volatility_percentile(atr, 100)
if 30 <= volatility_percentile <= 70:
    vol_score = 10  # Normal volatility
elif 20 <= volatility_percentile <= 80:
    vol_score = 7   # Moderate volatility
else:
    vol_score = 3   # Extreme volatility

market_context_score = trend_score + vol_score
```

### Technical Levels Scoring (25 pts)

```python
# Calculate support/resistance levels
support, resistance = calculate_sr_levels(df, lookback=50)

# Distance from levels
if direction == "long":
    dist_to_support = (close - support) / close
    dist_to_resistance = (resistance - close) / close
else:
    dist_to_support = (close - support) / close
    dist_to_resistance = (resistance - close) / close

# Score based on position
if direction == "long":
    # Good: near support, far from resistance
    if dist_to_support < 0.02:
        level_score = 25
    elif dist_to_support < 0.05:
        level_score = 20
    else:
        level_score = max(0, 25 - dist_to_support * 100)
else:
    # Good: near resistance, far from support
    if dist_to_resistance < 0.02:
        level_score = 25
    elif dist_to_resistance < 0.05:
        level_score = 20
    else:
        level_score = max(0, 25 - dist_to_resistance * 100)
```

---

## 📁 FILES

```
backend/app/
├── services/
│   └── signal_score.py       # NEW: SignalScorer class
├── api/
│   └── signal_routes.py      # NEW: API endpoint
└── main.py                   # Register router

tests/
└── test_signal_score.py      # NEW: Unit tests
```

---

## 🔧 API ENDPOINT

```python
# GET /api/signal-score/calculate
@router.get("/calculate")
async def calculate_signal_score(
    symbol: str,
    timeframe: str,
    direction: str,  # "long" or "short"
    entry_price: float,
    filters: Optional[dict] = None
) -> dict:
    return {
        "total_score": 78,
        "grade": "B",
        "components": {
            "confluence": 20,
            "multi_tf": 18,
            "market_context": 22,
            "technical_levels": 18
        },
        "details": {
            "supertrend_agrees": True,
            "rsi_agrees": True,
            "higher_tfs": {"4h": "long", "1d": "long"},
            "nearest_support": 45000,
            "nearest_resistance": 48000
        }
    }
```

---

## 📝 GIT COMMIT

```
feat: implement signal score core system

- Add SignalScorer class with 4 components
- Confluence scoring (25 pts)
- Multi-TF alignment (25 pts)
- Market context (25 pts)
- Technical levels (25 pts)
- Grade calculation (A-F)
- Unit tests

Chat #34: Signal Score Core
```

---

**Next chat:** #35 — Score Multi-TF
