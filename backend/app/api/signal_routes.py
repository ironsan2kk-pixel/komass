"""
Signal Score API Routes - KOMAS v4.0
====================================

API endpoints for signal quality evaluation.

Endpoints:
- GET /api/signal-score/calculate - Calculate score for a signal
- POST /api/signal-score/batch - Score multiple trades
- GET /api/signal-score/grades - Get grade scale info
- GET /api/signal-score/multi-tf/analyze - Analyze multi-TF alignment

Chat #34: Signal Score Core
Chat #35: Multi-TF Integration
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

# Import signal scorer
from app.services.signal_score import (
    SignalScorer,
    score_trades,
    get_grade_from_score,
    get_grade_color,
    GRADE_THRESHOLDS,
    Grade,
)

# Import MultiTFLoader for enhanced multi-TF analysis
from app.services.multi_tf_loader import (
    MultiTFLoader,
    TrendDetectionMethod,
    aggregate_to_higher_tf,
    get_higher_tfs,
    TF_HIERARCHY,
    DEFAULT_TF_WEIGHTS,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/signal-score", tags=["Signal Score"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class SignalScoreRequest(BaseModel):
    """Request model for signal score calculation"""
    symbol: str = Field(..., description="Trading pair symbol (e.g., BTCUSDT)")
    timeframe: str = Field(..., description="Timeframe (e.g., 1h, 4h)")
    direction: str = Field(..., description="Trade direction: 'long' or 'short'")
    entry_price: float = Field(..., gt=0, description="Entry price for the trade")
    
    # Optional filter configuration
    supertrend_enabled: bool = Field(True, description="Enable SuperTrend filter")
    rsi_enabled: bool = Field(True, description="Enable RSI filter")
    adx_enabled: bool = Field(True, description="Enable ADX filter")
    volume_enabled: bool = Field(True, description="Enable Volume filter")
    
    # Multi-TF options
    auto_load_higher_tfs: bool = Field(True, description="Automatically load higher TF data")
    trend_detection_method: str = Field(
        "combined",
        description="Trend detection method: 'ema', 'supertrend', 'adx', 'combined'"
    )


class TradeScoreRequest(BaseModel):
    """Request model for batch trade scoring"""
    symbol: str
    timeframe: str
    trades: List[Dict[str, Any]] = Field(..., description="List of trades to score")
    filters: Optional[Dict[str, Any]] = None
    auto_load_higher_tfs: bool = Field(True, description="Automatically load higher TF data")


class MultiTFAnalyzeRequest(BaseModel):
    """Request model for multi-TF analysis"""
    symbol: str = Field(..., description="Trading pair symbol")
    timeframe: str = Field(..., description="Trading timeframe")
    direction: str = Field(..., description="Signal direction: 'long' or 'short'")
    detection_method: str = Field(
        "combined",
        description="Trend detection method: 'ema', 'supertrend', 'adx', 'combined'"
    )
    use_api_fallback: bool = Field(True, description="Load from Binance API if file not found")
    use_aggregation_fallback: bool = Field(True, description="Aggregate from lower TF if needed")


class SignalScoreResponse(BaseModel):
    """Response model for signal score"""
    total_score: int
    grade: str
    components: Dict[str, int]
    details: Dict[str, Any]
    recommendations: List[str]


class GradeInfo(BaseModel):
    """Grade information"""
    grade: str
    min_score: int
    max_score: int
    description: str
    color: str


# =============================================================================
# DATA LOADING HELPERS
# =============================================================================

def find_data_dir() -> Path:
    """Find data directory"""
    possible_paths = [
        Path(__file__).parent.parent.parent / "data",
        Path("data"),
        Path("backend/data"),
        Path("../data"),
        Path.cwd() / "data",
        Path.cwd() / "backend" / "data",
    ]
    
    for p in possible_paths:
        if p.exists():
            return p
    
    default = Path(__file__).parent.parent.parent / "data"
    default.mkdir(exist_ok=True)
    return default


DATA_DIR = find_data_dir()


def load_ohlcv_data(symbol: str, timeframe: str) -> pd.DataFrame:
    """
    Load OHLCV data from parquet/csv file
    
    Args:
        symbol: Trading pair symbol
        timeframe: Timeframe
        
    Returns:
        DataFrame with OHLCV data
    """
    # Try parquet first
    parquet_path = DATA_DIR / f"{symbol}_{timeframe}.parquet"
    csv_path = DATA_DIR / f"{symbol}_{timeframe}.csv"
    
    if parquet_path.exists():
        df = pd.read_parquet(parquet_path)
    elif csv_path.exists():
        df = pd.read_csv(csv_path, parse_dates=['timestamp'])
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)
    else:
        raise FileNotFoundError(f"No data file found for {symbol}_{timeframe}")
    
    # Ensure numeric columns
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df


async def load_higher_tf_data_async(
    symbol: str,
    timeframe: str,
    trading_data: Optional[pd.DataFrame] = None,
    use_api_fallback: bool = True,
    use_aggregation_fallback: bool = True,
    detection_method: str = 'combined',
) -> Dict[str, pd.DataFrame]:
    """
    Load higher timeframe data with fallback options
    
    Args:
        symbol: Trading pair symbol
        timeframe: Current timeframe
        trading_data: Trading TF data for aggregation fallback
        use_api_fallback: Whether to load from Binance API
        use_aggregation_fallback: Whether to aggregate from lower TF
        detection_method: Trend detection method
        
    Returns:
        Dict of higher TF DataFrames
    """
    try:
        method = TrendDetectionMethod(detection_method)
    except ValueError:
        method = TrendDetectionMethod.COMBINED
    
    loader = MultiTFLoader(
        detection_method=method,
        use_api_fallback=use_api_fallback,
        use_aggregation_fallback=use_aggregation_fallback,
    )
    
    return await loader.load_higher_tf_data(
        symbol=symbol,
        trading_tf=timeframe,
        trading_data=trading_data,
    )


def load_higher_tf_data_sync(
    symbol: str,
    timeframe: str,
    trading_data: Optional[pd.DataFrame] = None,
) -> Dict[str, pd.DataFrame]:
    """
    Synchronous version of higher TF data loading (file only)
    
    Args:
        symbol: Trading pair symbol
        timeframe: Current timeframe
        trading_data: Trading TF data for aggregation
        
    Returns:
        Dict of higher TF DataFrames
    """
    result = {}
    
    for tf in ['4h', '1d']:
        # Try loading from file
        try:
            df = load_ohlcv_data(symbol, tf)
            if len(df) >= 10:
                result[tf] = df
                continue
        except FileNotFoundError:
            pass
        
        # Try aggregation as fallback
        if trading_data is not None:
            aggregated = aggregate_to_higher_tf(trading_data, timeframe, tf)
            if aggregated is not None and len(aggregated) >= 10:
                result[tf] = aggregated
    
    return result


# =============================================================================
# API ENDPOINTS
# =============================================================================

@router.get("/calculate")
async def calculate_signal_score(
    symbol: str = Query(..., description="Trading pair symbol"),
    timeframe: str = Query(..., description="Timeframe"),
    direction: str = Query(..., description="Trade direction: 'long' or 'short'"),
    entry_price: float = Query(..., gt=0, description="Entry price"),
    supertrend_enabled: bool = Query(True),
    rsi_enabled: bool = Query(True),
    adx_enabled: bool = Query(True),
    volume_enabled: bool = Query(True),
    auto_load_higher_tfs: bool = Query(True, description="Auto-load higher TF data"),
    trend_detection_method: str = Query("combined", description="Trend detection method"),
) -> dict:
    """
    Calculate signal score for a trading signal
    
    Returns comprehensive score with breakdown by component:
    - Confluence (25 pts): Indicator agreement
    - Multi-TF Alignment (25 pts): Higher TF confirmation
    - Market Context (25 pts): Trend + volatility
    - Technical Levels (25 pts): S/R proximity
    
    Grades: A (85+), B (70-84), C (55-69), D (40-54), F (<40)
    
    Set auto_load_higher_tfs=true to automatically load 4h and 1d data
    for multi-TF analysis. Uses Binance API and data aggregation as fallbacks.
    """
    try:
        # Normalize inputs
        symbol = symbol.upper()
        direction = direction.lower()
        
        if direction not in ('long', 'short'):
            raise HTTPException(400, f"Invalid direction: {direction}. Use 'long' or 'short'")
        
        # Load trading TF data
        try:
            df = load_ohlcv_data(symbol, timeframe)
        except FileNotFoundError:
            raise HTTPException(404, f"No data found for {symbol}_{timeframe}")
        
        if len(df) < 20:
            raise HTTPException(400, f"Insufficient data: need at least 20 candles, got {len(df)}")
        
        # Load higher TF data for multi-TF analysis
        higher_tf_data = {}
        if auto_load_higher_tfs:
            higher_tf_data = await load_higher_tf_data_async(
                symbol=symbol,
                timeframe=timeframe,
                trading_data=df,
                use_api_fallback=True,
                use_aggregation_fallback=True,
                detection_method=trend_detection_method,
            )
        else:
            # Just try to load from files
            higher_tf_data = load_higher_tf_data_sync(symbol, timeframe, df)
        
        # Build filter config
        filters = {
            'supertrend_enabled': supertrend_enabled,
            'rsi_enabled': rsi_enabled,
            'adx_enabled': adx_enabled,
            'volume_enabled': volume_enabled,
        }
        
        # Create scorer with detection method
        scorer_params = {
            'multi_tf_detection_method': trend_detection_method,
        }
        scorer = SignalScorer(params=scorer_params)
        
        result = scorer.calculate_score(
            df=df,
            direction=direction,
            entry_price=entry_price,
            filters=filters,
            higher_tf_data=higher_tf_data,
        )
        
        return {
            'symbol': symbol,
            'timeframe': timeframe,
            'direction': direction,
            'entry_price': entry_price,
            'total_score': result.total_score,
            'grade': result.grade,
            'grade_color': get_grade_color(result.grade),
            'components': result.components,
            'details': result.details,
            'recommendations': result.recommendations,
            'higher_tfs_loaded': list(higher_tf_data.keys()),
            'auto_loaded': auto_load_higher_tfs,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating signal score: {e}")
        raise HTTPException(500, f"Error calculating score: {str(e)}")


@router.post("/batch")
async def batch_score_trades(request: TradeScoreRequest) -> dict:
    """
    Score multiple trades in batch
    
    Request body:
    - symbol: Trading pair
    - timeframe: Timeframe
    - trades: List of trade dicts with direction, entry_price, entry_idx
    - filters: Optional filter configuration
    - auto_load_higher_tfs: Whether to auto-load higher TF data
    
    Returns list of trades with signal_score and signal_grade added
    """
    try:
        symbol = request.symbol.upper()
        
        # Load data
        try:
            df = load_ohlcv_data(symbol, request.timeframe)
        except FileNotFoundError:
            raise HTTPException(404, f"No data found for {symbol}_{request.timeframe}")
        
        # Load higher TF data
        higher_tf_data = {}
        if request.auto_load_higher_tfs:
            higher_tf_data = await load_higher_tf_data_async(
                symbol=symbol,
                timeframe=request.timeframe,
                trading_data=df,
            )
        else:
            higher_tf_data = load_higher_tf_data_sync(symbol, request.timeframe, df)
        
        # Score trades
        scored_trades = score_trades(
            trades=request.trades,
            df=df,
            filters=request.filters,
            higher_tf_data=higher_tf_data,
        )
        
        # Calculate summary stats
        scores = [t.get('signal_score', 0) for t in scored_trades]
        grades = [t.get('signal_grade', 'F') for t in scored_trades]
        
        grade_counts = {g: grades.count(g) for g in ['A', 'B', 'C', 'D', 'F']}
        
        return {
            'symbol': symbol,
            'timeframe': request.timeframe,
            'trades_count': len(scored_trades),
            'trades': scored_trades,
            'summary': {
                'avg_score': round(sum(scores) / len(scores), 1) if scores else 0,
                'min_score': min(scores) if scores else 0,
                'max_score': max(scores) if scores else 0,
                'grade_distribution': grade_counts,
            },
            'higher_tfs_loaded': list(higher_tf_data.keys()),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error batch scoring trades: {e}")
        raise HTTPException(500, f"Error batch scoring: {str(e)}")


@router.get("/grades")
async def get_grade_scale() -> dict:
    """
    Get grade scale information
    
    Returns grade thresholds, descriptions, and colors
    """
    grades = [
        {
            'grade': 'A',
            'min_score': 85,
            'max_score': 100,
            'description': 'Excellent - High probability trade',
            'color': get_grade_color('A'),
        },
        {
            'grade': 'B',
            'min_score': 70,
            'max_score': 84,
            'description': 'Good - Solid setup',
            'color': get_grade_color('B'),
        },
        {
            'grade': 'C',
            'min_score': 55,
            'max_score': 69,
            'description': 'Average - Acceptable trade',
            'color': get_grade_color('C'),
        },
        {
            'grade': 'D',
            'min_score': 40,
            'max_score': 54,
            'description': 'Below Average - Caution advised',
            'color': get_grade_color('D'),
        },
        {
            'grade': 'F',
            'min_score': 0,
            'max_score': 39,
            'description': 'Poor - Avoid this trade',
            'color': get_grade_color('F'),
        },
    ]
    
    components = [
        {
            'name': 'Confluence',
            'max_points': 25,
            'description': 'Agreement between multiple technical indicators',
        },
        {
            'name': 'Multi-TF Alignment',
            'max_points': 25,
            'description': 'Higher timeframe trend confirmation (4h: 10pts, 1d: 15pts)',
        },
        {
            'name': 'Market Context',
            'max_points': 25,
            'description': 'Trend strength and volatility conditions',
        },
        {
            'name': 'Technical Levels',
            'max_points': 25,
            'description': 'Proximity to support/resistance levels',
        },
    ]
    
    return {
        'grades': grades,
        'components': components,
        'total_max_score': 100,
    }


@router.get("/multi-tf/hierarchy")
async def get_tf_hierarchy() -> dict:
    """
    Get timeframe hierarchy for multi-TF analysis
    
    Returns mapping of trading TF to relevant higher TFs
    """
    return {
        'hierarchy': TF_HIERARCHY,
        'default_weights': DEFAULT_TF_WEIGHTS,
        'detection_methods': ['ema', 'supertrend', 'adx', 'combined'],
    }


@router.post("/multi-tf/analyze")
async def analyze_multi_tf(request: MultiTFAnalyzeRequest) -> dict:
    """
    Analyze multi-TF alignment for a signal
    
    Provides detailed analysis of higher timeframe trends
    including trend direction, confidence, and data sources.
    """
    try:
        symbol = request.symbol.upper()
        direction = request.direction.lower()
        
        if direction not in ('long', 'short'):
            raise HTTPException(400, f"Invalid direction: {direction}")
        
        # Load trading TF data
        try:
            df = load_ohlcv_data(symbol, request.timeframe)
        except FileNotFoundError:
            raise HTTPException(404, f"No data found for {symbol}_{request.timeframe}")
        
        # Get trend detection method
        try:
            method = TrendDetectionMethod(request.detection_method)
        except ValueError:
            method = TrendDetectionMethod.COMBINED
        
        # Create loader with specified settings
        loader = MultiTFLoader(
            detection_method=method,
            use_api_fallback=request.use_api_fallback,
            use_aggregation_fallback=request.use_aggregation_fallback,
        )
        
        # Perform analysis
        result = await loader.analyze(
            symbol=symbol,
            trading_tf=request.timeframe,
            signal_direction=direction,
            trading_data=df,
        )
        
        return {
            'symbol': symbol,
            'timeframe': request.timeframe,
            'direction': direction,
            **result.to_dict(),
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing multi-TF: {e}")
        raise HTTPException(500, f"Error analyzing multi-TF: {str(e)}")


@router.get("/test")
async def test_signal_score() -> dict:
    """
    Test endpoint to verify signal score module is working
    
    Creates sample data and calculates score
    """
    import numpy as np
    
    # Create sample OHLCV data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
    np.random.seed(42)
    
    close = 45000 + np.cumsum(np.random.randn(100) * 100)
    high = close + np.random.rand(100) * 200
    low = close - np.random.rand(100) * 200
    open_ = close + np.random.randn(100) * 50
    volume = np.random.rand(100) * 1000000
    
    df = pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
    }, index=dates)
    
    # Create sample higher TF data (4h and 1d)
    df_4h = df.resample('4h').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
    }).dropna()
    
    df_1d = df.resample('1D').agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum',
    }).dropna()
    
    higher_tf_data = {'4h': df_4h, '1d': df_1d}
    
    # Calculate score
    scorer = SignalScorer()
    result = scorer.calculate_score(
        df=df,
        direction='long',
        entry_price=close[-1],
        higher_tf_data=higher_tf_data,
    )
    
    return {
        'status': 'ok',
        'message': 'Signal Score module is working',
        'test_result': result.to_dict(),
        'higher_tfs_used': list(higher_tf_data.keys()),
    }


@router.get("/test-multi-tf")
async def test_multi_tf_loader() -> dict:
    """
    Test endpoint for MultiTFLoader functionality
    
    Creates sample data and tests all trend detection methods
    """
    import numpy as np
    
    # Create sample OHLCV data
    dates = pd.date_range(start='2024-01-01', periods=200, freq='1h')
    np.random.seed(42)
    
    # Create trending data
    trend = np.cumsum(np.random.randn(200) * 50 + 10)  # Slight upward bias
    close = 45000 + trend
    high = close + np.abs(np.random.randn(200) * 100)
    low = close - np.abs(np.random.randn(200) * 100)
    open_ = close + np.random.randn(200) * 30
    volume = np.abs(np.random.randn(200) * 500000) + 100000
    
    df = pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume,
    }, index=dates)
    
    results = {}
    
    # Test each detection method
    for method_name in ['ema', 'supertrend', 'adx', 'combined']:
        method = TrendDetectionMethod(method_name)
        loader = MultiTFLoader(detection_method=method)
        
        # Analyze with aggregation
        result = await loader.analyze(
            symbol='TEST',
            trading_tf='1h',
            signal_direction='long',
            trading_data=df,
        )
        
        results[method_name] = {
            'score': result.score,
            'max_score': result.max_score,
            'aligned_tfs': result.aligned_tfs,
            'analyses': {k: v.to_dict() for k, v in result.analyses.items()},
        }
    
    return {
        'status': 'ok',
        'message': 'MultiTFLoader test complete',
        'methods_tested': list(results.keys()),
        'results': results,
    }
