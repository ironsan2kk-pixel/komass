"""
Komas Trading Server - Dominant Presets Seed
=============================================
Migration of 125 presets from GG Pine Script to database.

Categories:
- Scalp: 5m timeframe
- Short-Term: 15m timeframe
- Mid-Term: 30m, 1h timeframes
- Long-Term: 3h, 4h timeframes

Run:
    python -m app.migrations.seed_dominant_presets
    
Or via API:
    POST /api/presets/dominant/seed
"""
import logging
from typing import List, Dict, Any

from app.database.presets_db import bulk_create_presets, ensure_presets_table

logger = logging.getLogger(__name__)


# ============ ALL 125 PRESETS FROM GG PINE SCRIPT ============

GG_PRESETS: List[Dict[str, Any]] = [
    # === SCALP (5m) ===
    {
        "name": "ETH/USDT 5m Scalp",
        "symbol": "ETHUSDT",
        "timeframe": "5m",
        "category": "scalp",
        "sensitivity": 48.8,
        "tp_percents": [0.3, 0.6, 0.9, 1.8],
        "sl_percent": 0.8,
        "filter_type": 0,
        "fixed_stop": False
    },
    {
        "name": "BTC/USDT 5m Scalp",
        "symbol": "BTCUSDT",
        "timeframe": "5m",
        "category": "scalp",
        "sensitivity": 46,
        "tp_percents": [0.15, 0.3, 0.5, 1.0],
        "sl_percent": 0.5,
        "filter_type": 0,
        "fixed_stop": False
    },
    {
        "name": "ADA/USDT 5m Scalp",
        "symbol": "ADAUSDT",
        "timeframe": "5m",
        "category": "scalp",
        "sensitivity": 22,
        "tp_percents": [0.5, 1.0, 2.0, 4.0],
        "sl_percent": 1.5,
        "filter_type": 0,
        "fixed_stop": False
    },
    
    # === SHORT-TERM (15m) ===
    {
        "name": "DYDX/USDT 15m Short-Term",
        "symbol": "DYDXUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 16,
        "tp_percents": [1.0, 2.5, 5.0, 8.0],
        "sl_percent": 1.5,
        "filter_type": 6
    },
    {
        "name": "LRC/USDT 15m Short-Term",
        "symbol": "LRCUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 52,
        "tp_percents": [1.5, 3.4, 5.5, 9.0],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "BTC/USDT 15m Short-Term",
        "symbol": "BTCUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 34,
        "tp_percents": [0.7, 1.4, 2.5, 4.3],
        "sl_percent": 1.0,
        "filter_type": 1
    },
    {
        "name": "GALA/USDT 15m Short-Term",
        "symbol": "GALAUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 21,
        "tp_percents": [1.0, 2.5, 5.0, 8.0],
        "sl_percent": 1.5,
        "filter_type": 6
    },
    {
        "name": "BRETT/USDT 15m Short-Term",
        "symbol": "BRETTUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 27,
        "tp_percents": [1.5, 2.5, 5.0, 8.0],
        "sl_percent": 1.5,
        "filter_type": 6
    },
    {
        "name": "1INCH/USDT 15m Short-Term",
        "symbol": "1INCHUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 23,
        "tp_percents": [1.0, 2.5, 5.0, 8.0],
        "sl_percent": 1.5,
        "filter_type": 6
    },
    {
        "name": "SNX/USDT 15m Short-Term",
        "symbol": "SNXUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 34,
        "tp_percents": [1.3, 3.6, 6.2, 9.5],
        "sl_percent": 1.6,
        "filter_type": 0
    },
    {
        "name": "ROSE/USDT 15m Short-Term",
        "symbol": "ROSEUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 53.2,
        "tp_percents": [1.2, 2.4, 4.2, 6.2],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "ZRX/USDT 15m Short-Term",
        "symbol": "ZRXUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 53.2,
        "tp_percents": [1.2, 2.4, 4.2, 6.2],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "W/USDT 15m Short-Term",
        "symbol": "WUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 53.2,
        "tp_percents": [1.2, 2.4, 4.2, 6.2],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "INJ/USDT 15m Short-Term",
        "symbol": "INJUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 29,
        "tp_percents": [1.0, 2.5, 4.0, 8.0],
        "sl_percent": 1.2,
        "filter_type": 4
    },
    {
        "name": "THETA/USDT 15m Short-Term",
        "symbol": "THETAUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 53.2,
        "tp_percents": [1.2, 2.4, 4.2, 6.2],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "AEVO/USDT 15m Short-Term",
        "symbol": "AEVOUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 26,
        "tp_percents": [1.3, 2.8, 4.3, 8.6],
        "sl_percent": 1.6,
        "filter_type": 1
    },
    {
        "name": "SEI/USDT 15m Short-Term",
        "symbol": "SEIUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 24,
        "tp_percents": [1.0, 2.5, 5.0, 8.0],
        "sl_percent": 1.5,
        "filter_type": 6
    },
    {
        "name": "ETH/USDT 15m Short-Term",
        "symbol": "ETHUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 26,
        "tp_percents": [0.8, 1.5, 3.5, 6.5],
        "sl_percent": 1.5,
        "filter_type": 0,
        "fixed_stop": False
    },
    {
        "name": "APT/USDT 15m Short-Term",
        "symbol": "APTUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 29,
        "tp_percents": [1.2, 2.4, 5.0, 9.0],
        "sl_percent": 1.6,
        "filter_type": 0
    },
    {
        "name": "LDO/USDT 15m Short-Term",
        "symbol": "LDOUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 24,
        "tp_percents": [1.0, 2.5, 4.0, 7.5],
        "sl_percent": 1.2,
        "filter_type": 4
    },
    {
        "name": "NEAR/USDT 15m Short-Term",
        "symbol": "NEARUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 31,
        "tp_percents": [1.0, 2.5, 5.0, 8.0],
        "sl_percent": 1.5,
        "filter_type": 6
    },
    {
        "name": "RENDER/USDT 15m Short-Term",
        "symbol": "RENDERUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 24,
        "tp_percents": [1.0, 2.5, 5.0, 8.0],
        "sl_percent": 1.5,
        "filter_type": 6
    },
    {
        "name": "AAVE/USDT 15m Short-Term",
        "symbol": "AAVEUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 16,
        "tp_percents": [1.0, 2.2, 3.6, 7.5],
        "sl_percent": 1.6,
        "filter_type": 1
    },
    {
        "name": "WLD/USDT 15m Short-Term",
        "symbol": "WLDUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 24,
        "tp_percents": [1.0, 2.5, 4.0, 7.5],
        "sl_percent": 1.2,
        "filter_type": 4
    },
    {
        "name": "ENA/USDT 15m Short-Term",
        "symbol": "ENAUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 24,
        "tp_percents": [1.0, 2.2, 3.5, 6.0],
        "sl_percent": 1.5,
        "filter_type": 1
    },
    {
        "name": "WOO/USDT 15m Short-Term",
        "symbol": "WOOUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 30,
        "tp_percents": [1.0, 2.5, 4.0, 7.0],
        "sl_percent": 1.2,
        "filter_type": 4
    },
    {
        "name": "XLM/USDT 15m Short-Term",
        "symbol": "XLMUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 28,
        "tp_percents": [1.1, 2.5, 4.2, 6.8],
        "sl_percent": 1.0,
        "filter_type": 3
    },
    {
        "name": "NEO/USDT 15m Short-Term",
        "symbol": "NEOUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 13,
        "tp_percents": [1.2, 2.4, 3.8, 6.3],
        "sl_percent": 1.6,
        "filter_type": 0
    },
    {
        "name": "BAT/USDT 15m Short-Term",
        "symbol": "BATUSDT",
        "timeframe": "15m",
        "category": "short-term",
        "sensitivity": 13,
        "tp_percents": [1.2, 2.4, 3.8, 6.3],
        "sl_percent": 1.6,
        "filter_type": 0
    },
    
    # === MID-TERM (30m) ===
    {
        "name": "NOT/USDT 30m Mid-Term",
        "symbol": "NOTUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 48.3,
        "tp_percents": [1.3, 2.6, 4.3, 8.0],
        "sl_percent": 1.5,
        "filter_type": 1
    },
    {
        "name": "SNX/USDT 30m Mid-Term",
        "symbol": "SNXUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 20,
        "tp_percents": [1.5, 3.0, 4.5, 9.0],
        "sl_percent": 1.5,
        "filter_type": 0
    },
    {
        "name": "THETA/USDT 30m Mid-Term",
        "symbol": "THETAUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 35,
        "tp_percents": [1.5, 3.0, 4.5, 9.0],
        "sl_percent": 1.4,
        "filter_type": 1
    },
    {
        "name": "AVAX/USDT 30m Mid-Term",
        "symbol": "AVAXUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 21,
        "tp_percents": [1.5, 3.5, 5.5, 10.5],
        "sl_percent": 1.8,
        "filter_type": 3
    },
    {
        "name": "GALA/USDT 30m Mid-Term",
        "symbol": "GALAUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 26,
        "tp_percents": [1.2, 2.5, 4.0, 7.6],
        "sl_percent": 1.4,
        "filter_type": 0
    },
    {
        "name": "ROSE/USDT 30m Mid-Term",
        "symbol": "ROSEUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 19,
        "tp_percents": [1.5, 3.5, 5.5, 9.0],
        "sl_percent": 2.0,
        "filter_type": 6
    },
    {
        "name": "TAO/USDT 30m Mid-Term",
        "symbol": "TAOUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 13,
        "tp_percents": [1.3, 2.8, 4.5, 8.4],
        "sl_percent": 1.5,
        "filter_type": 1
    },
    {
        "name": "DYDX/USDT 30m Mid-Term",
        "symbol": "DYDXUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 25,
        "tp_percents": [1.8, 3.6, 7.1, 9.6],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "ATOM/USDT 30m Mid-Term",
        "symbol": "ATOMUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 32,
        "tp_percents": [1.2, 3.5, 5.5, 9.5],
        "sl_percent": 2.0,
        "filter_type": 6
    },
    {
        "name": "ENS/USDT 30m Mid-Term",
        "symbol": "ENSUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 31,
        "tp_percents": [1.5, 3.5, 5.5, 10.5],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "SEI/USDT 30m Mid-Term",
        "symbol": "SEIUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 24,
        "tp_percents": [1.5, 3.5, 5.5, 9.0],
        "sl_percent": 1.7,
        "filter_type": 5
    },
    {
        "name": "KSM/USDT 30m Mid-Term",
        "symbol": "KSMUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 28,
        "tp_percents": [1.5, 2.4, 3.6, 5.7],
        "sl_percent": 1.5,
        "filter_type": 0
    },
    {
        "name": "LDO/USDT 30m Mid-Term",
        "symbol": "LDOUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 15,
        "tp_percents": [1.5, 3.5, 5.5, 9.0],
        "sl_percent": 2.0,
        "filter_type": 6
    },
    {
        "name": "BTC/USDT 30m Mid-Term",
        "symbol": "BTCUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 46,
        "tp_percents": [0.8, 1.5, 3.3, 6.6],
        "sl_percent": 1.6,
        "filter_type": 1
    },
    {
        "name": "SOL/USDT 30m Mid-Term",
        "symbol": "SOLUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 35,
        "tp_percents": [1.3, 3.0, 4.5, 9.0],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "XRP/USDT 30m Mid-Term",
        "symbol": "XRPUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 16,
        "tp_percents": [1.0, 2.5, 4.0, 8.0],
        "sl_percent": 1.6,
        "filter_type": 6
    },
    {
        "name": "ADA/USDT 30m Mid-Term",
        "symbol": "ADAUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 30,
        "tp_percents": [1.2, 3.0, 4.5, 9.0],
        "sl_percent": 1.8,
        "filter_type": 1
    },
    {
        "name": "LINK/USDT 30m Mid-Term",
        "symbol": "LINKUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 40,
        "tp_percents": [1.3, 2.6, 4.0, 7.4],
        "sl_percent": 1.4,
        "filter_type": 0
    },
    {
        "name": "COMP/USDT 30m Mid-Term",
        "symbol": "COMPUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 28,
        "tp_percents": [1.3, 2.6, 4.0, 7.4],
        "sl_percent": 1.4,
        "filter_type": 0
    },
    {
        "name": "W/USDT 30m Mid-Term",
        "symbol": "WUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 32,
        "tp_percents": [1.3, 3.6, 6.2, 9.5],
        "sl_percent": 1.5,
        "filter_type": 0
    },
    {
        "name": "ENA/USDT 30m Mid-Term",
        "symbol": "ENAUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 32,
        "tp_percents": [1.3, 3.6, 6.2, 9.5],
        "sl_percent": 1.5,
        "filter_type": 0
    },
    {
        "name": "API3/USDT 30m Mid-Term",
        "symbol": "API3USDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 32,
        "tp_percents": [1.3, 3.6, 6.2, 9.5],
        "sl_percent": 1.5,
        "filter_type": 0
    },
    {
        "name": "ETC/USDT 30m Mid-Term",
        "symbol": "ETCUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 35.5,
        "tp_percents": [1.2, 3.0, 4.5, 9.0],
        "sl_percent": 1.8,
        "filter_type": 3
    },
    {
        "name": "ETHFI/USDT 30m Mid-Term",
        "symbol": "ETHFIUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 31,
        "tp_percents": [1.5, 3.5, 5.5, 9.5],
        "sl_percent": 1.6,
        "filter_type": 5
    },
    {
        "name": "ETH/USDT 30m Mid-Term",
        "symbol": "ETHUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 34,
        "tp_percents": [1.0, 2.5, 5.0, 8.0],
        "sl_percent": 1.6,
        "filter_type": 0,
        "fixed_stop": False
    },
    {
        "name": "1INCH/USDT 30m Mid-Term",
        "symbol": "1INCHUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 15,
        "tp_percents": [1.5, 3.0, 4.5, 9.0],
        "sl_percent": 2.0,
        "filter_type": 6
    },
    {
        "name": "APE/USDT 30m Mid-Term",
        "symbol": "APEUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 25,
        "tp_percents": [1.5, 3.5, 5.5, 9.0],
        "sl_percent": 2.0,
        "filter_type": 6
    },
    {
        "name": "MYRO/USDT 30m Mid-Term",
        "symbol": "MYROUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 25,
        "tp_percents": [1.5, 3.5, 5.5, 10.5],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "AEVO/USDT 30m Mid-Term",
        "symbol": "AEVOUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 42,
        "tp_percents": [1.5, 3.0, 4.5, 9.0],
        "sl_percent": 1.6,
        "filter_type": 4
    },
    {
        "name": "CFX/USDT 30m Mid-Term",
        "symbol": "CFXUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 25,
        "tp_percents": [1.5, 3.0, 4.5, 9.0],
        "sl_percent": 2.0,
        "filter_type": 6
    },
    {
        "name": "ZRX/USDT 30m Mid-Term",
        "symbol": "ZRXUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 34,
        "tp_percents": [1.5, 3.5, 5.5, 9.0],
        "sl_percent": 2.0,
        "filter_type": 6
    },
    {
        "name": "BRETT/USDT 30m Mid-Term",
        "symbol": "BRETTUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 29,
        "tp_percents": [1.5, 3.5, 5.5, 10.5],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "INJ/USDT 30m Mid-Term",
        "symbol": "INJUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 23.7,
        "tp_percents": [1.5, 3.5, 5.5, 10.5],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "NEAR/USDT 30m Mid-Term",
        "symbol": "NEARUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 27,
        "tp_percents": [1.5, 3.0, 4.5, 9.0],
        "sl_percent": 1.6,
        "filter_type": 1
    },
    {
        "name": "AAVE/USDT 30m Mid-Term",
        "symbol": "AAVEUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 38,
        "tp_percents": [1.5, 3.5, 5.5, 10.5],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "WLD/USDT 30m Mid-Term",
        "symbol": "WLDUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 25.8,
        "tp_percents": [1.5, 3.5, 5.5, 10.5],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "BAKE/USDT 30m Mid-Term",
        "symbol": "BAKEUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 25,
        "tp_percents": [1.5, 3.3, 4.8, 9.0],
        "sl_percent": 2.0,
        "filter_type": 0
    },
    {
        "name": "CHZ/USDT 30m Mid-Term",
        "symbol": "CHZUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 27,
        "tp_percents": [1.5, 3.5, 5.5, 10.5],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "ORDI/USDT 30m Mid-Term",
        "symbol": "ORDIUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 31,
        "tp_percents": [1.5, 3.5, 5.5, 10.5],
        "sl_percent": 1.8,
        "filter_type": 1
    },
    {
        "name": "SAND/USDT 30m Mid-Term",
        "symbol": "SANDUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 33,
        "tp_percents": [1.8, 3.6, 7.1, 10.0],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "ARC/USDT 30m Mid-Term",
        "symbol": "ARCUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 13,
        "tp_percents": [1.6, 3.6, 6.8, 10.0],
        "sl_percent": 1.6,
        "filter_type": 0
    },
    {
        "name": "AR/USDT 30m Mid-Term",
        "symbol": "ARUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 18.7,
        "tp_percents": [1.3, 2.6, 4.0, 7.6],
        "sl_percent": 1.8,
        "filter_type": 1
    },
    {
        "name": "HBAR/USDT 30m Mid-Term",
        "symbol": "HBARUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 34,
        "tp_percents": [1.6, 3.2, 4.7, 9.5],
        "sl_percent": 1.8,
        "filter_type": 1
    },
    {
        "name": "AXS/USDT 30m Mid-Term",
        "symbol": "AXSUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 27,
        "tp_percents": [1.5, 3.0, 4.8, 9.6],
        "sl_percent": 2.0,
        "filter_type": 6
    },
    {
        "name": "WIF/USDT 30m Mid-Term",
        "symbol": "WIFUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 41.4,
        "tp_percents": [1.3, 2.5, 4.0, 7.2],
        "sl_percent": 1.6,
        "filter_type": 1
    },
    {
        "name": "DOT/USDT 30m Mid-Term",
        "symbol": "DOTUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 33.4,
        "tp_percents": [1.5, 3.5, 5.5, 10.5],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "GMT/USDT 30m Mid-Term",
        "symbol": "GMTUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 41.9,
        "tp_percents": [1.6, 3.2, 4.7, 9.5],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "BIGTIME/USDT 30m Mid-Term",
        "symbol": "BIGTIMEUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 36,
        "tp_percents": [1.5, 3.2, 4.8, 11.0],
        "sl_percent": 3.0,
        "filter_type": 1
    },
    {
        "name": "OP/USDT 30m Mid-Term",
        "symbol": "OPUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 28,
        "tp_percents": [1.2, 2.8, 4.5, 8.7],
        "sl_percent": 2.3,
        "filter_type": 0
    },
    {
        "name": "ONE/USDT 30m Mid-Term v1",
        "symbol": "ONEUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 26,
        "tp_percents": [1.5, 3.0, 4.5, 9.0],
        "sl_percent": 1.4,
        "filter_type": 1
    },
    {
        "name": "ONE/USDT 30m Mid-Term v2",
        "symbol": "ONEUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 18,
        "tp_percents": [1.5, 3.2, 6.2, 9.5],
        "sl_percent": 2.3,
        "filter_type": 0
    },
    {
        "name": "JUP/USDT 30m Mid-Term",
        "symbol": "JUPUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 34,
        "tp_percents": [1.5, 3.5, 5.5, 10.5],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "NEO/USDT 30m Mid-Term",
        "symbol": "NEOUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 26,
        "tp_percents": [1.5, 3.0, 4.5, 9.0],
        "sl_percent": 2.2,
        "filter_type": 1
    },
    {
        "name": "APT/USDT 30m Mid-Term",
        "symbol": "APTUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 18,
        "tp_percents": [1.5, 3.5, 5.5, 9.0],
        "sl_percent": 2.0,
        "filter_type": 6
    },
    {
        "name": "RUNE/USDT 30m Mid-Term",
        "symbol": "RUNEUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 29,
        "tp_percents": [1.5, 3.0, 4.5, 9.0],
        "sl_percent": 1.6,
        "filter_type": 0
    },
    {
        "name": "BRETT/USDT 30m Mid-Term v2",
        "symbol": "BRETTUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 25,
        "tp_percents": [1.4, 3.0, 5.3, 9.5],
        "sl_percent": 2.6,
        "filter_type": 0
    },
    {
        "name": "SUI/USDT 30m Mid-Term",
        "symbol": "SUIUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 30,
        "tp_percents": [1.3, 2.6, 4.0, 7.6],
        "sl_percent": 1.8,
        "filter_type": 6
    },
    {
        "name": "ZRO/USDT 30m Mid-Term",
        "symbol": "ZROUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 23,
        "tp_percents": [1.8, 3.7, 5.6, 11.8],
        "sl_percent": 2.0,
        "filter_type": 0
    },
    {
        "name": "FLM/USDT 30m Mid-Term",
        "symbol": "FLMUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 26,
        "tp_percents": [1.5, 3.5, 5.5, 10.0],
        "sl_percent": 3.0,
        "filter_type": 0
    },
    {
        "name": "MAGIC/USDT 30m Mid-Term",
        "symbol": "MAGICUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 14,
        "tp_percents": [1.5, 3.5, 5.5, 10.0],
        "sl_percent": 2.0,
        "filter_type": 0
    },
    {
        "name": "LEVER/USDT 30m Mid-Term",
        "symbol": "LEVERUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 26,
        "tp_percents": [1.5, 3.5, 6.0, 10.0],
        "sl_percent": 2.0,
        "filter_type": 0
    },
    {
        "name": "PYTH/USDT 30m Mid-Term",
        "symbol": "PYTHUSDT",
        "timeframe": "30m",
        "category": "mid-term",
        "sensitivity": 32,
        "tp_percents": [1.5, 3.5, 5.5, 9.0],
        "sl_percent": 2.0,
        "filter_type": 6
    },
    
    # === MID-TERM (1h) ===
    {
        "name": "INJ/USDT 1h Mid-Term",
        "symbol": "INJUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 12,
        "tp_percents": [2.0, 4.0, 6.0, 8.0],
        "sl_percent": 3.0,
        "filter_type": 0
    },
    {
        "name": "SNX/USDT 1h Mid-Term",
        "symbol": "SNXUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 14,
        "tp_percents": [1.7, 3.0, 4.8, 9.0],
        "sl_percent": 2.0,
        "filter_type": 0
    },
    {
        "name": "THETA/USDT 1h Mid-Term",
        "symbol": "THETAUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 30,
        "tp_percents": [2.0, 4.5, 7.0, 11.0],
        "sl_percent": 2.4,
        "filter_type": 4
    },
    {
        "name": "AEVO/USDT 1h Mid-Term",
        "symbol": "AEVOUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 14,
        "tp_percents": [2.0, 4.5, 7.0, 10.5],
        "sl_percent": 3.0,
        "filter_type": 0
    },
    {
        "name": "VANRY/USDT 1h Mid-Term",
        "symbol": "VANRYUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 42.3,
        "tp_percents": [2.5, 5.0, 8.5, 12.0],
        "sl_percent": 2.3,
        "filter_type": 0
    },
    {
        "name": "ALGO/USDT 1h Mid-Term",
        "symbol": "ALGOUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 17,
        "tp_percents": [1.5, 3.5, 6.0, 10.5],
        "sl_percent": 2.6,
        "filter_type": 0
    },
    {
        "name": "PEOPLE/USDT 1h Mid-Term",
        "symbol": "PEOPLEUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 27,
        "tp_percents": [1.5, 3.5, 5.5, 10.5],
        "sl_percent": 2.6,
        "filter_type": 0
    },
    {
        "name": "EGLD/USDT 1h Mid-Term",
        "symbol": "EGLDUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 13,
        "tp_percents": [1.5, 3.5, 5.6, 10.0],
        "sl_percent": 2.6,
        "filter_type": 0
    },
    {
        "name": "ETH/USDT 1h Mid-Term",
        "symbol": "ETHUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 29,
        "tp_percents": [1.5, 3.5, 5.5, 10.0],
        "sl_percent": 2.6,
        "filter_type": 0,
        "fixed_stop": False
    },
    {
        "name": "APE/USDT 1h Mid-Term",
        "symbol": "APEUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 12,
        "tp_percents": [1.5, 3.5, 6.0, 10.0],
        "sl_percent": 2.0,
        "filter_type": 0
    },
    {
        "name": "MKR/USDT 1h Mid-Term",
        "symbol": "MKRUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 39,
        "tp_percents": [2.0, 4.5, 7.0, 10.5],
        "sl_percent": 3.0,
        "filter_type": 0
    },
    {
        "name": "BTC/USDT 1h Mid-Term",
        "symbol": "BTCUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 33,
        "tp_percents": [1.5, 3.0, 4.5, 9.0],
        "sl_percent": 2.2,
        "filter_type": 1
    },
    {
        "name": "ONG/USDT 1h Mid-Term",
        "symbol": "ONGUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 33,
        "tp_percents": [1.5, 3.0, 4.5, 9.0],
        "sl_percent": 2.2,
        "filter_type": 1
    },
    {
        "name": "WIF/USDT 1h Mid-Term",
        "symbol": "WIFUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 31,
        "tp_percents": [2.0, 4.5, 7.0, 10.5],
        "sl_percent": 3.0,
        "filter_type": 0
    },
    {
        "name": "KAVA/USDT 1h Mid-Term",
        "symbol": "KAVAUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 26,
        "tp_percents": [1.5, 3.5, 6.0, 10.5],
        "sl_percent": 2.0,
        "filter_type": 0
    },
    {
        "name": "TIA/USDT 1h Mid-Term",
        "symbol": "TIAUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 18,
        "tp_percents": [1.7, 3.6, 6.0, 9.2],
        "sl_percent": 3.0,
        "filter_type": 1
    },
    {
        "name": "ALT/USDT 1h Mid-Term",
        "symbol": "ALTUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 23,
        "tp_percents": [1.5, 3.5, 6.0, 10.5],
        "sl_percent": 2.0,
        "filter_type": 0
    },
    {
        "name": "BNB/USDT 1h Mid-Term",
        "symbol": "BNBUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 33,
        "tp_percents": [1.2, 2.7, 5.4, 8.0],
        "sl_percent": 2.0,
        "filter_type": 1
    },
    {
        "name": "KNC/USDT 1h Mid-Term",
        "symbol": "KNCUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 29,
        "tp_percents": [1.5, 3.5, 7.0, 10.5],
        "sl_percent": 2.6,
        "filter_type": 3
    },
    {
        "name": "PEPE/USDT 1h Mid-Term",
        "symbol": "PEPEUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 24,
        "tp_percents": [1.5, 3.5, 7.0, 10.5],
        "sl_percent": 3.0,
        "filter_type": 0
    },
    {
        "name": "ENA/USDT 1h Mid-Term",
        "symbol": "ENAUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 14,
        "tp_percents": [1.5, 3.0, 4.5, 9.0],
        "sl_percent": 1.5,
        "filter_type": 0
    },
    {
        "name": "SUI/USDT 1h Mid-Term",
        "symbol": "SUIUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 15,
        "tp_percents": [2.5, 5.5, 8.0, 10.5],
        "sl_percent": 3.0,
        "filter_type": 0
    },
    {
        "name": "NMR/USDT 1h Mid-Term",
        "symbol": "NMRUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 16,
        "tp_percents": [1.5, 3.5, 5.5, 10.0],
        "sl_percent": 3.0,
        "filter_type": 5
    },
    {
        "name": "BCH/USDT 1h Mid-Term",
        "symbol": "BCHUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 20,
        "tp_percents": [1.2, 2.5, 4.0, 8.0],
        "sl_percent": 2.0,
        "filter_type": 5
    },
    {
        "name": "LPT/USDT 1h Mid-Term",
        "symbol": "LPTUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 22,
        "tp_percents": [1.2, 2.5, 4.0, 8.0],
        "sl_percent": 2.0,
        "filter_type": 0
    },
    {
        "name": "MANA/USDT 1h Mid-Term",
        "symbol": "MANAUSDT",
        "timeframe": "1h",
        "category": "mid-term",
        "sensitivity": 17,
        "tp_percents": [1.5, 3.5, 6.0, 12.0],
        "sl_percent": 2.0,
        "filter_type": 0
    },
    
    # === LONG-TERM (3h, 4h) ===
    {
        "name": "ETH/USDT 3h Long-Term",
        "symbol": "ETHUSDT",
        "timeframe": "3h",
        "category": "long-term",
        "sensitivity": 14,
        "tp_percents": [2.0, 4.0, 6.5, 21.0],
        "sl_percent": 3.0,
        "filter_type": 0,
        "fixed_stop": False
    },
    {
        "name": "ETH/USDT 4h Long-Term",
        "symbol": "ETHUSDT",
        "timeframe": "4h",
        "category": "long-term",
        "sensitivity": 30,
        "tp_percents": [2.0, 4.0, 6.5, 12.0],
        "sl_percent": 3.0,
        "filter_type": 0,
        "fixed_stop": False
    },
    {
        "name": "BTC/USDT 3h Long-Term",
        "symbol": "BTCUSDT",
        "timeframe": "3h",
        "category": "long-term",
        "sensitivity": 32,
        "tp_percents": [3.6, 7.2, 15.0, 32.0],
        "sl_percent": 1.8,
        "filter_type": 0
    },
    {
        "name": "BTC/USDT 4h Long-Term",
        "symbol": "BTCUSDT",
        "timeframe": "4h",
        "category": "long-term",
        "sensitivity": 22,
        "tp_percents": [4.0, 6.6, 9.7, 14.2],
        "sl_percent": 3.3,
        "filter_type": 0
    },
    {
        "name": "SOL/USDT 4h Long-Term",
        "symbol": "SOLUSDT",
        "timeframe": "4h",
        "category": "long-term",
        "sensitivity": 20,
        "tp_percents": [3.4, 7.8, 13.1, 19.0],
        "sl_percent": 3.6,
        "filter_type": 1
    },
    {
        "name": "XLM/USDT 4h Long-Term",
        "symbol": "XLMUSDT",
        "timeframe": "4h",
        "category": "long-term",
        "sensitivity": 20,
        "tp_percents": [3.0, 6.2, 10.3, 15.8],
        "sl_percent": 3.6,
        "filter_type": 0
    },
    {
        "name": "PEPE/USDT 3h Long-Term",
        "symbol": "PEPEUSDT",
        "timeframe": "3h",
        "category": "long-term",
        "sensitivity": 18,
        "tp_percents": [3.5, 6.8, 10.3, 15.8],
        "sl_percent": 3.0,
        "filter_type": 3
    },
    {
        "name": "GTC/USDT 4h Long-Term",
        "symbol": "GTCUSDT",
        "timeframe": "4h",
        "category": "long-term",
        "sensitivity": 18,
        "tp_percents": [3.5, 6.8, 10.3, 15.8],
        "sl_percent": 2.6,
        "filter_type": 3
    },
]


def _convert_preset_to_db_format(preset: dict) -> dict:
    """Convert GG preset format to database format"""
    tp_percents = preset.get("tp_percents", [1.0, 2.0, 3.0, 5.0])
    
    return {
        "name": preset["name"],
        "indicator_type": "dominant",
        "category": preset.get("category", "mid-term"),
        "symbol": preset.get("symbol"),
        "timeframe": preset.get("timeframe"),
        "source": "pine_script",
        "description": f"Imported from GG Pine Script - {preset['name']}",
        "params": {
            "sensitivity": preset["sensitivity"],
            "tp1_percent": tp_percents[0] if len(tp_percents) > 0 else 1.0,
            "tp2_percent": tp_percents[1] if len(tp_percents) > 1 else 2.0,
            "tp3_percent": tp_percents[2] if len(tp_percents) > 2 else 3.0,
            "tp4_percent": tp_percents[3] if len(tp_percents) > 3 else 5.0,
            "sl_percent": preset["sl_percent"],
            "filter_type": preset.get("filter_type", 0),
            "sl_mode": preset.get("sl_mode", 0),
            "fixed_stop": preset.get("fixed_stop", True)
        }
    }


def seed_all_dominant_presets() -> dict:
    """Seed all 125 Dominant presets to database"""
    ensure_presets_table()
    
    logger.info(f"Seeding {len(GG_PRESETS)} Dominant presets...")
    
    # Convert to DB format
    db_presets = [_convert_preset_to_db_format(p) for p in GG_PRESETS]
    
    # Bulk create
    result = bulk_create_presets(db_presets, skip_duplicates=True)
    
    logger.info(f"Seeding complete: {result}")
    return result


# ============ CLI ENTRY POINT ============

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )
    
    print("=" * 60)
    print("KOMAS Dominant Presets Seeder")
    print("=" * 60)
    print(f"Total presets to seed: {len(GG_PRESETS)}")
    print()
    
    result = seed_all_dominant_presets()
    
    print()
    print("Results:")
    print(f"  Created: {result.get('created', 0)}")
    print(f"  Skipped: {result.get('skipped', 0)}")
    print(f"  Errors:  {result.get('errors', 0)}")
    print()
    print("Done!")
