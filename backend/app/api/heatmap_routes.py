"""
KOMAS Trading Server - Optimizer Heatmap API Routes
=====================================================
REST API endpoints for heatmap visualization of optimization results.

Endpoints:
- GET /api/optimizer/results/{run_id}/heatmap - Get heatmap data for visualization
- GET /api/optimizer/results/{run_id}/heatmap/export - Export heatmap as CSV

Metrics supported:
- pnl: Total profit/loss %
- win_rate: Win rate %
- max_dd: Maximum drawdown %
- sharpe: Sharpe ratio

Color scales:
- pnl: Red (-) to Green (+)
- win_rate: Red (<50%) to Green (>70%)
- max_dd: Green (low) to Red (high) - inverted
- sharpe: Red (<1) to Green (>2)

Chat #48: Preset Optimizer Heatmap
"""

import logging
from typing import Optional, List, Dict, Any
from io import StringIO
import csv

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/optimizer/results", tags=["optimizer-heatmap"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class HeatmapCell(BaseModel):
    """Single cell in the heatmap matrix"""
    preset_id: str
    preset_name: str
    pair: str
    value: float
    normalized: float  # 0-1 normalized value for color
    color: str  # Hex color
    raw_metrics: Dict[str, Any]  # All metrics for tooltip


class HeatmapRow(BaseModel):
    """Row in the heatmap (one preset)"""
    preset_id: str
    preset_name: str
    indicator_type: str
    avg_value: float
    cells: List[HeatmapCell]


class HeatmapResponse(BaseModel):
    """Response for heatmap data"""
    run_id: str
    metric: str
    metric_label: str
    presets: List[str]  # Row headers
    pairs: List[str]    # Column headers
    rows: List[HeatmapRow]
    min_value: float
    max_value: float
    avg_value: float
    color_scale: Dict[str, str]  # Legend colors


class HeatmapExportResponse(BaseModel):
    """Response info for CSV export"""
    run_id: str
    metric: str
    filename: str
    rows: int
    cols: int


# ============================================================================
# METRICS CONFIGURATION
# ============================================================================

METRIC_CONFIG = {
    'pnl': {
        'label': 'PnL %',
        'field': 'total_pnl_percent',
        'format': lambda x: f"{x:+.2f}%",
        'inverted': False,  # Higher is better
        'thresholds': {
            'bad': -10,
            'neutral': 0,
            'good': 20,
            'excellent': 50
        }
    },
    'win_rate': {
        'label': 'Win Rate %',
        'field': 'win_rate',
        'format': lambda x: f"{x:.1f}%",
        'inverted': False,  # Higher is better
        'thresholds': {
            'bad': 40,
            'neutral': 50,
            'good': 60,
            'excellent': 75
        }
    },
    'max_dd': {
        'label': 'Max Drawdown %',
        'field': 'max_drawdown',
        'format': lambda x: f"{x:.1f}%",
        'inverted': True,  # Lower is better (invert colors)
        'thresholds': {
            'bad': 30,
            'neutral': 20,
            'good': 10,
            'excellent': 5
        }
    },
    'sharpe': {
        'label': 'Sharpe Ratio',
        'field': 'sharpe_ratio',
        'format': lambda x: f"{x:.2f}",
        'inverted': False,  # Higher is better
        'thresholds': {
            'bad': 0,
            'neutral': 1,
            'good': 1.5,
            'excellent': 2.5
        }
    },
    'trades': {
        'label': 'Total Trades',
        'field': 'total_trades',
        'format': lambda x: f"{int(x)}",
        'inverted': False,  # Higher = more data
        'thresholds': {
            'bad': 5,
            'neutral': 20,
            'good': 50,
            'excellent': 100
        }
    },
    'profit_factor': {
        'label': 'Profit Factor',
        'field': 'profit_factor',
        'format': lambda x: f"{x:.2f}",
        'inverted': False,
        'thresholds': {
            'bad': 0.8,
            'neutral': 1.0,
            'good': 1.5,
            'excellent': 2.5
        }
    }
}


# ============================================================================
# COLOR GENERATION
# ============================================================================

def value_to_color(value: float, min_val: float, max_val: float, inverted: bool = False) -> tuple:
    """
    Convert value to color based on min/max range.
    Returns (normalized_value, hex_color)
    
    Color scale: Red -> Yellow -> Green
    If inverted: Green -> Yellow -> Red (for metrics where lower is better)
    """
    if max_val == min_val:
        normalized = 0.5
    else:
        normalized = (value - min_val) / (max_val - min_val)
        normalized = max(0, min(1, normalized))  # Clamp to 0-1
    
    if inverted:
        normalized = 1 - normalized
    
    # Generate color using HSL-like approach
    # 0 = Red (hue 0), 0.5 = Yellow (hue 60), 1 = Green (hue 120)
    if normalized < 0.5:
        # Red to Yellow
        r = 255
        g = int(255 * (normalized * 2))
        b = 50
    else:
        # Yellow to Green
        r = int(255 * (1 - (normalized - 0.5) * 2))
        g = 255
        b = 50
    
    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    return normalized, hex_color


def get_color_scale_legend() -> Dict[str, str]:
    """Generate legend colors for the scale"""
    steps = [-20, 0, 20, 40, 60]
    legend = {}
    for step in steps:
        _, color = value_to_color(step, -20, 60, False)
        legend[str(step)] = color
    return legend


# ============================================================================
# HEATMAP DATA EXTRACTION
# ============================================================================

def extract_heatmap_data(
    result_matrix: Dict[str, Dict[str, Dict]],
    preset_scores: List[Dict],
    metric: str = 'pnl'
) -> Dict:
    """
    Extract heatmap data from optimization result matrix.
    
    Args:
        result_matrix: Dict[preset_id][pair] -> metrics dict
        preset_scores: List of preset aggregate scores (for ordering/names)
        metric: Which metric to visualize
    
    Returns:
        Dict with heatmap data structure
    """
    metric_config = METRIC_CONFIG.get(metric, METRIC_CONFIG['pnl'])
    field = metric_config['field']
    inverted = metric_config['inverted']
    
    # Build lookup for preset names and indicator types
    preset_info = {}
    for score in preset_scores:
        preset_info[score['preset_id']] = {
            'name': score.get('preset_name', score['preset_id']),
            'indicator_type': score.get('indicator_type', 'unknown'),
            'overall_score': score.get('overall_score', 0)
        }
    
    # Collect all values for normalization
    all_values = []
    for preset_id, pairs_data in result_matrix.items():
        for pair, metrics in pairs_data.items():
            value = metrics.get(field, 0)
            if value is not None:
                all_values.append(value)
    
    if not all_values:
        return {
            'error': 'No data available',
            'presets': [],
            'pairs': [],
            'rows': [],
            'min_value': 0,
            'max_value': 0,
            'avg_value': 0
        }
    
    min_val = min(all_values)
    max_val = max(all_values)
    avg_val = sum(all_values) / len(all_values)
    
    # Get ordered presets (by overall score descending)
    ordered_presets = sorted(
        result_matrix.keys(),
        key=lambda p: preset_info.get(p, {}).get('overall_score', 0),
        reverse=True
    )
    
    # Get all pairs (sorted alphabetically)
    all_pairs = set()
    for pairs_data in result_matrix.values():
        all_pairs.update(pairs_data.keys())
    ordered_pairs = sorted(all_pairs)
    
    # Build rows
    rows = []
    for preset_id in ordered_presets:
        info = preset_info.get(preset_id, {})
        pairs_data = result_matrix.get(preset_id, {})
        
        cells = []
        row_values = []
        
        for pair in ordered_pairs:
            metrics = pairs_data.get(pair, {})
            value = metrics.get(field, 0) or 0
            row_values.append(value)
            
            normalized, color = value_to_color(value, min_val, max_val, inverted)
            
            cells.append({
                'preset_id': preset_id,
                'preset_name': info.get('name', preset_id),
                'pair': pair,
                'value': value,
                'normalized': normalized,
                'color': color,
                'raw_metrics': metrics
            })
        
        avg_value = sum(row_values) / len(row_values) if row_values else 0
        
        rows.append({
            'preset_id': preset_id,
            'preset_name': info.get('name', preset_id),
            'indicator_type': info.get('indicator_type', 'unknown'),
            'avg_value': avg_value,
            'cells': cells
        })
    
    return {
        'metric': metric,
        'metric_label': metric_config['label'],
        'presets': [preset_info.get(p, {}).get('name', p) for p in ordered_presets],
        'pairs': ordered_pairs,
        'rows': rows,
        'min_value': min_val,
        'max_value': max_val,
        'avg_value': avg_val,
        'color_scale': get_color_scale_legend()
    }


def generate_csv(heatmap_data: Dict, metric: str) -> str:
    """Generate CSV content from heatmap data"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Header row: Preset | Pair1 | Pair2 | ... | Average
    header = ['Preset', 'Indicator'] + heatmap_data['pairs'] + ['Average']
    writer.writerow(header)
    
    # Data rows
    for row in heatmap_data['rows']:
        row_data = [
            row['preset_name'],
            row['indicator_type']
        ]
        for cell in row['cells']:
            row_data.append(f"{cell['value']:.2f}")
        row_data.append(f"{row['avg_value']:.2f}")
        writer.writerow(row_data)
    
    # Summary row
    writer.writerow([])
    writer.writerow(['Statistics'])
    writer.writerow(['Min', heatmap_data['min_value']])
    writer.writerow(['Max', heatmap_data['max_value']])
    writer.writerow(['Average', heatmap_data['avg_value']])
    
    return output.getvalue()


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/{run_id}/heatmap")
async def get_heatmap_data(
    run_id: str,
    metric: str = Query(default='pnl', description="Metric: pnl, win_rate, max_dd, sharpe, trades, profit_factor"),
    limit_presets: Optional[int] = Query(default=None, ge=1, le=200, description="Limit number of presets"),
    limit_pairs: Optional[int] = Query(default=None, ge=1, le=50, description="Limit number of pairs")
):
    """
    Get heatmap visualization data for optimization results.
    
    Returns a matrix of preset × pair with color-coded values
    for the selected metric.
    """
    # Import here to avoid circular imports
    try:
        # Try to get from memory cache first
        from app.api.optimizer_routes import get_stored_result
        result = get_stored_result(run_id)
    except ImportError:
        result = None
    
    # Try SQLite if not in memory
    if not result:
        try:
            from app.db.optimizer_db import OptimizationResultsManager
            result_detail = OptimizationResultsManager.get_run(run_id)
            if result_detail:
                result = {
                    'run_id': result_detail.run_id,
                    'mode': result_detail.mode,
                    'timeframe': result_detail.timeframe,
                    'result_matrix': result_detail.result_matrix or {},
                    'preset_scores': result_detail.preset_scores or []
                }
        except Exception as e:
            logger.error(f"Failed to load result from SQLite: {e}")
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Results for {run_id} not found")
    
    # Validate metric
    if metric not in METRIC_CONFIG:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid metric '{metric}'. Available: {list(METRIC_CONFIG.keys())}"
        )
    
    result_matrix = result.get('result_matrix', {})
    preset_scores = result.get('preset_scores', [])
    
    if not result_matrix:
        raise HTTPException(status_code=404, detail="No result matrix found for this run")
    
    # Extract heatmap data
    heatmap_data = extract_heatmap_data(result_matrix, preset_scores, metric)
    
    # Apply limits if specified
    if limit_presets and len(heatmap_data['rows']) > limit_presets:
        heatmap_data['rows'] = heatmap_data['rows'][:limit_presets]
        heatmap_data['presets'] = heatmap_data['presets'][:limit_presets]
    
    if limit_pairs and len(heatmap_data['pairs']) > limit_pairs:
        heatmap_data['pairs'] = heatmap_data['pairs'][:limit_pairs]
        for row in heatmap_data['rows']:
            row['cells'] = row['cells'][:limit_pairs]
    
    return {
        'run_id': run_id,
        'mode': result.get('mode', 'standard'),
        'timeframe': result.get('timeframe', '1h'),
        **heatmap_data
    }


@router.get("/{run_id}/heatmap/metrics")
async def get_available_metrics():
    """
    Get list of available metrics for heatmap visualization.
    """
    metrics = []
    for key, config in METRIC_CONFIG.items():
        metrics.append({
            'id': key,
            'label': config['label'],
            'inverted': config['inverted'],
            'thresholds': config['thresholds']
        })
    return {'metrics': metrics}


@router.get("/{run_id}/heatmap/export")
async def export_heatmap_csv(
    run_id: str,
    metric: str = Query(default='pnl', description="Metric to export")
):
    """
    Export heatmap data as CSV file.
    """
    # Get heatmap data
    try:
        from app.api.optimizer_routes import get_stored_result
        result = get_stored_result(run_id)
    except ImportError:
        result = None
    
    if not result:
        try:
            from app.db.optimizer_db import OptimizationResultsManager
            result_detail = OptimizationResultsManager.get_run(run_id)
            if result_detail:
                result = {
                    'result_matrix': result_detail.result_matrix or {},
                    'preset_scores': result_detail.preset_scores or []
                }
        except Exception as e:
            logger.error(f"Failed to load result from SQLite: {e}")
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Results for {run_id} not found")
    
    if metric not in METRIC_CONFIG:
        raise HTTPException(status_code=400, detail=f"Invalid metric '{metric}'")
    
    result_matrix = result.get('result_matrix', {})
    preset_scores = result.get('preset_scores', [])
    
    heatmap_data = extract_heatmap_data(result_matrix, preset_scores, metric)
    csv_content = generate_csv(heatmap_data, metric)
    
    filename = f"heatmap_{run_id}_{metric}.csv"
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )


@router.get("/{run_id}/heatmap/cell/{preset_id}/{pair}")
async def get_cell_details(
    run_id: str,
    preset_id: str,
    pair: str
):
    """
    Get detailed metrics for a specific cell (preset × pair combination).
    
    Returns all available metrics for the tooltip.
    """
    try:
        from app.api.optimizer_routes import get_stored_result
        result = get_stored_result(run_id)
    except ImportError:
        result = None
    
    if not result:
        try:
            from app.db.optimizer_db import OptimizationResultsManager
            result_detail = OptimizationResultsManager.get_run(run_id)
            if result_detail:
                result = {'result_matrix': result_detail.result_matrix or {}}
        except Exception as e:
            logger.error(f"Failed to load result: {e}")
    
    if not result:
        raise HTTPException(status_code=404, detail=f"Results for {run_id} not found")
    
    result_matrix = result.get('result_matrix', {})
    
    if preset_id not in result_matrix:
        raise HTTPException(status_code=404, detail=f"Preset {preset_id} not found")
    
    pairs_data = result_matrix[preset_id]
    if pair not in pairs_data:
        raise HTTPException(status_code=404, detail=f"Pair {pair} not found for preset {preset_id}")
    
    metrics = pairs_data[pair]
    
    # Format all metrics for display
    formatted = {}
    for key, config in METRIC_CONFIG.items():
        field = config['field']
        value = metrics.get(field, 0)
        if value is not None:
            formatted[key] = {
                'label': config['label'],
                'value': value,
                'formatted': config['format'](value) if value else 'N/A'
            }
    
    return {
        'run_id': run_id,
        'preset_id': preset_id,
        'pair': pair,
        'metrics': metrics,
        'formatted': formatted
    }
