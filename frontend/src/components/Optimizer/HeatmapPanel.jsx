/**
 * KOMAS Trading Server - Optimizer Heatmap Panel
 * ===============================================
 * Interactive heatmap visualization for preset optimization results.
 * 
 * Features:
 * - Matrix grid (preset × pair)
 * - Color-coded cells by metric value
 * - Metric selector (PnL, WinRate, MaxDD, Sharpe)
 * - Interactive tooltips with full metrics
 * - Row/column highlighting on hover
 * - Zoom controls for large matrices
 * - Export to CSV
 * 
 * Chat #48: Preset Optimizer Heatmap
 */

import React, { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { optimizerApi } from '../../api';

// ============================================================================
// CONFIGURATION
// ============================================================================

const METRIC_OPTIONS = [
  { id: 'pnl', label: 'PnL %', icon: '📈' },
  { id: 'win_rate', label: 'Win Rate', icon: '🎯' },
  { id: 'max_dd', label: 'Max DD', icon: '📉' },
  { id: 'sharpe', label: 'Sharpe', icon: '⚖️' },
  { id: 'profit_factor', label: 'Profit Factor', icon: '💰' },
  { id: 'trades', label: 'Trades', icon: '📊' }
];

const ZOOM_LEVELS = [
  { id: 'compact', label: 'Compact', cellSize: 40, fontSize: 'text-xs' },
  { id: 'normal', label: 'Normal', cellSize: 60, fontSize: 'text-sm' },
  { id: 'large', label: 'Large', cellSize: 80, fontSize: 'text-base' }
];

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

/**
 * Color legend component
 */
const HeatmapLegend = ({ minValue, maxValue, metric, inverted }) => {
  const gradientColors = inverted
    ? 'from-green-500 via-yellow-500 to-red-500'
    : 'from-red-500 via-yellow-500 to-green-500';
  
  const formatValue = (val) => {
    if (metric === 'pnl') return `${val >= 0 ? '+' : ''}${val.toFixed(0)}%`;
    if (metric === 'win_rate') return `${val.toFixed(0)}%`;
    if (metric === 'max_dd') return `${val.toFixed(0)}%`;
    if (metric === 'sharpe') return val.toFixed(1);
    if (metric === 'profit_factor') return val.toFixed(1);
    return val.toFixed(0);
  };

  return (
    <div className="flex items-center gap-3 px-4 py-2 bg-gray-800/50 rounded-lg">
      <span className="text-gray-400 text-sm">Scale:</span>
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-300">{formatValue(minValue)}</span>
        <div className={`w-32 h-4 rounded bg-gradient-to-r ${gradientColors}`} />
        <span className="text-sm text-gray-300">{formatValue(maxValue)}</span>
      </div>
      {inverted && (
        <span className="text-xs text-gray-500 ml-2">(lower is better)</span>
      )}
    </div>
  );
};

/**
 * Cell tooltip component
 */
const CellTooltip = ({ cell, position }) => {
  if (!cell || !position) return null;

  const metrics = cell.raw_metrics || {};
  
  return (
    <div 
      className="fixed z-50 bg-gray-900 border border-gray-700 rounded-lg shadow-xl p-3 min-w-[200px]"
      style={{
        left: position.x + 10,
        top: position.y + 10,
        pointerEvents: 'none'
      }}
    >
      <div className="font-medium text-white mb-2 border-b border-gray-700 pb-2">
        {cell.preset_name} × {cell.pair?.replace('USDT', '')}
      </div>
      <div className="space-y-1 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-400">PnL:</span>
          <span className={metrics.total_pnl_percent >= 0 ? 'text-green-400' : 'text-red-400'}>
            {metrics.total_pnl_percent >= 0 ? '+' : ''}{(metrics.total_pnl_percent || 0).toFixed(2)}%
          </span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Win Rate:</span>
          <span className="text-white">{(metrics.win_rate || 0).toFixed(1)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Max DD:</span>
          <span className="text-orange-400">{(metrics.max_drawdown || 0).toFixed(1)}%</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Sharpe:</span>
          <span className="text-white">{(metrics.sharpe_ratio || 0).toFixed(2)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Trades:</span>
          <span className="text-white">{metrics.total_trades || 0}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-400">Profit Factor:</span>
          <span className="text-white">{(metrics.profit_factor || 0).toFixed(2)}</span>
        </div>
      </div>
    </div>
  );
};

/**
 * Single heatmap cell
 */
const HeatmapCell = ({ 
  cell, 
  cellSize, 
  fontSize,
  isRowHighlighted,
  isColHighlighted,
  onMouseEnter,
  onMouseLeave,
  metric
}) => {
  const formatValue = (val) => {
    if (metric === 'pnl') return `${val >= 0 ? '+' : ''}${val.toFixed(1)}`;
    if (metric === 'win_rate') return `${val.toFixed(0)}`;
    if (metric === 'max_dd') return `${val.toFixed(0)}`;
    if (metric === 'sharpe') return val.toFixed(1);
    if (metric === 'profit_factor') return val.toFixed(1);
    return val.toFixed(0);
  };

  const highlightClass = (isRowHighlighted || isColHighlighted) 
    ? 'ring-2 ring-white/50' 
    : '';

  return (
    <div
      className={`
        flex items-center justify-center cursor-pointer
        transition-all duration-150 rounded-sm
        ${fontSize} font-medium
        ${highlightClass}
        hover:ring-2 hover:ring-white hover:z-10
      `}
      style={{
        width: cellSize,
        height: cellSize,
        backgroundColor: cell.color,
        color: cell.normalized > 0.5 ? '#1a1a1a' : '#ffffff'
      }}
      onMouseEnter={(e) => onMouseEnter(cell, e)}
      onMouseLeave={onMouseLeave}
    >
      {formatValue(cell.value)}
    </div>
  );
};

/**
 * Row header (preset name)
 */
const RowHeader = ({ preset, indicator, avgValue, isHighlighted, metric }) => {
  const formatValue = (val) => {
    if (metric === 'pnl') return `${val >= 0 ? '+' : ''}${val.toFixed(1)}%`;
    if (metric === 'win_rate') return `${val.toFixed(0)}%`;
    if (metric === 'max_dd') return `${val.toFixed(0)}%`;
    if (metric === 'sharpe') return val.toFixed(2);
    return val.toFixed(1);
  };

  const indicatorBadge = indicator === 'trg' 
    ? 'bg-blue-500/30 text-blue-300 border-blue-500/40'
    : 'bg-purple-500/30 text-purple-300 border-purple-500/40';

  return (
    <div 
      className={`
        flex items-center gap-2 px-2 py-1 min-w-[150px]
        ${isHighlighted ? 'bg-gray-700' : 'bg-gray-800'}
        border-r border-gray-700
      `}
    >
      <span className={`px-1.5 py-0.5 text-xs rounded border ${indicatorBadge}`}>
        {indicator?.toUpperCase() || '?'}
      </span>
      <div className="flex-1 truncate">
        <div className="text-sm text-white font-medium truncate" title={preset}>
          {preset}
        </div>
        <div className="text-xs text-gray-500">
          Avg: {formatValue(avgValue)}
        </div>
      </div>
    </div>
  );
};

/**
 * Column header (pair name)
 */
const ColHeader = ({ pair, isHighlighted, cellSize }) => {
  const displayPair = pair?.replace('USDT', '') || pair;
  
  return (
    <div 
      className={`
        flex items-center justify-center text-xs font-medium
        ${isHighlighted ? 'bg-gray-700 text-white' : 'bg-gray-800 text-gray-400'}
        border-b border-gray-700 px-1
      `}
      style={{ 
        width: cellSize, 
        height: 36,
        writingMode: cellSize < 60 ? 'vertical-rl' : 'horizontal-tb',
        transform: cellSize < 60 ? 'rotate(180deg)' : 'none'
      }}
      title={pair}
    >
      {displayPair}
    </div>
  );
};


// ============================================================================
// MAIN COMPONENT
// ============================================================================

const HeatmapPanel = ({ runId, onClose }) => {
  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [heatmapData, setHeatmapData] = useState(null);
  const [metric, setMetric] = useState('pnl');
  const [zoomLevel, setZoomLevel] = useState('normal');
  const [hoveredCell, setHoveredCell] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState(null);
  const [highlightedRow, setHighlightedRow] = useState(null);
  const [highlightedCol, setHighlightedCol] = useState(null);
  const [exporting, setExporting] = useState(false);
  
  // Refs
  const containerRef = useRef(null);
  
  // Get current zoom config
  const zoomConfig = ZOOM_LEVELS.find(z => z.id === zoomLevel) || ZOOM_LEVELS[1];
  
  // Fetch heatmap data
  useEffect(() => {
    const fetchData = async () => {
      if (!runId) return;
      
      setLoading(true);
      setError(null);
      
      try {
        const response = await optimizerApi.getHeatmap(runId, metric);
        setHeatmapData(response.data);
      } catch (err) {
        console.error('Failed to load heatmap:', err);
        setError(err.response?.data?.detail || err.message || 'Failed to load heatmap');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [runId, metric]);
  
  // Handle cell hover
  const handleCellEnter = useCallback((cell, event) => {
    setHoveredCell(cell);
    setTooltipPosition({ x: event.clientX, y: event.clientY });
    setHighlightedRow(cell.preset_id);
    setHighlightedCol(cell.pair);
  }, []);
  
  const handleCellLeave = useCallback(() => {
    setHoveredCell(null);
    setTooltipPosition(null);
    setHighlightedRow(null);
    setHighlightedCol(null);
  }, []);
  
  // Handle export
  const handleExport = async () => {
    if (!runId) return;
    
    setExporting(true);
    try {
      const response = await optimizerApi.exportHeatmapCsv(runId, metric);
      
      // Create download link
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `heatmap_${runId}_${metric}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      setError('Failed to export CSV');
    } finally {
      setExporting(false);
    }
  };
  
  // Compute inverted flag for current metric
  const isInverted = useMemo(() => {
    return metric === 'max_dd';
  }, [metric]);
  
  // Loading state
  if (loading) {
    return (
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-8">
        <div className="flex items-center justify-center gap-3">
          <div className="animate-spin h-6 w-6 border-2 border-blue-500 border-t-transparent rounded-full" />
          <span className="text-gray-400">Loading heatmap...</span>
        </div>
      </div>
    );
  }
  
  // Error state
  if (error) {
    return (
      <div className="bg-gray-800/50 rounded-lg border border-red-700 p-6">
        <div className="flex items-center gap-3 text-red-400">
          <span className="text-2xl">⚠️</span>
          <div>
            <div className="font-medium">Failed to load heatmap</div>
            <div className="text-sm text-red-300">{error}</div>
          </div>
        </div>
      </div>
    );
  }
  
  // No data state
  if (!heatmapData || !heatmapData.rows?.length) {
    return (
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-8 text-center">
        <div className="text-gray-400">
          <span className="text-3xl mb-2 block">📊</span>
          No heatmap data available for this run
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-gray-800/50 rounded-lg border border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xl">🗺️</span>
            <h3 className="text-lg font-semibold text-white">Heatmap View</h3>
          </div>
          
          {/* Metric selector */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Metric:</span>
            <select
              value={metric}
              onChange={(e) => setMetric(e.target.value)}
              className="bg-gray-700 border border-gray-600 rounded px-2 py-1 text-sm text-white"
            >
              {METRIC_OPTIONS.map(opt => (
                <option key={opt.id} value={opt.id}>
                  {opt.icon} {opt.label}
                </option>
              ))}
            </select>
          </div>
          
          {/* Zoom controls */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Zoom:</span>
            <div className="flex rounded-md overflow-hidden border border-gray-600">
              {ZOOM_LEVELS.map(zoom => (
                <button
                  key={zoom.id}
                  onClick={() => setZoomLevel(zoom.id)}
                  className={`px-2 py-1 text-xs ${
                    zoomLevel === zoom.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                  }`}
                >
                  {zoom.label}
                </button>
              ))}
            </div>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Export button */}
          <button
            onClick={handleExport}
            disabled={exporting}
            className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 
                       text-white rounded text-sm disabled:opacity-50"
          >
            {exporting ? (
              <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              <span>📥</span>
            )}
            Export CSV
          </button>
          
          {/* Close button */}
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-white p-1"
            >
              ✕
            </button>
          )}
        </div>
      </div>
      
      {/* Legend */}
      <div className="p-3 border-b border-gray-700 bg-gray-900/30">
        <HeatmapLegend
          minValue={heatmapData.min_value}
          maxValue={heatmapData.max_value}
          metric={metric}
          inverted={isInverted}
        />
      </div>
      
      {/* Matrix grid */}
      <div 
        ref={containerRef}
        className="overflow-auto p-4"
        style={{ maxHeight: 'calc(100vh - 400px)' }}
      >
        <div className="inline-block">
          {/* Column headers */}
          <div className="flex sticky top-0 z-20 bg-gray-900">
            {/* Corner cell */}
            <div className="min-w-[150px] h-9 bg-gray-800 border-r border-b border-gray-700" />
            
            {/* Pair headers */}
            {heatmapData.pairs.map(pair => (
              <ColHeader
                key={pair}
                pair={pair}
                isHighlighted={highlightedCol === pair}
                cellSize={zoomConfig.cellSize}
              />
            ))}
          </div>
          
          {/* Data rows */}
          {heatmapData.rows.map(row => (
            <div key={row.preset_id} className="flex">
              {/* Row header */}
              <div className="sticky left-0 z-10">
                <RowHeader
                  preset={row.preset_name}
                  indicator={row.indicator_type}
                  avgValue={row.avg_value}
                  isHighlighted={highlightedRow === row.preset_id}
                  metric={metric}
                />
              </div>
              
              {/* Cells */}
              {row.cells.map(cell => (
                <HeatmapCell
                  key={`${cell.preset_id}-${cell.pair}`}
                  cell={cell}
                  cellSize={zoomConfig.cellSize}
                  fontSize={zoomConfig.fontSize}
                  isRowHighlighted={highlightedRow === cell.preset_id}
                  isColHighlighted={highlightedCol === cell.pair}
                  onMouseEnter={handleCellEnter}
                  onMouseLeave={handleCellLeave}
                  metric={metric}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
      
      {/* Summary footer */}
      <div className="p-3 border-t border-gray-700 bg-gray-900/30 flex items-center justify-between text-sm">
        <div className="flex items-center gap-4 text-gray-400">
          <span>
            <strong className="text-white">{heatmapData.rows?.length || 0}</strong> presets
          </span>
          <span>×</span>
          <span>
            <strong className="text-white">{heatmapData.pairs?.length || 0}</strong> pairs
          </span>
          <span>=</span>
          <span>
            <strong className="text-white">
              {(heatmapData.rows?.length || 0) * (heatmapData.pairs?.length || 0)}
            </strong> combinations
          </span>
        </div>
        
        <div className="flex items-center gap-4 text-gray-400">
          <span>
            Min: <strong className="text-red-400">{heatmapData.min_value?.toFixed(2)}</strong>
          </span>
          <span>
            Avg: <strong className="text-yellow-400">{heatmapData.avg_value?.toFixed(2)}</strong>
          </span>
          <span>
            Max: <strong className="text-green-400">{heatmapData.max_value?.toFixed(2)}</strong>
          </span>
        </div>
      </div>
      
      {/* Tooltip */}
      <CellTooltip cell={hoveredCell} position={tooltipPosition} />
    </div>
  );
};

export default HeatmapPanel;

// Export sub-components for external use
export { HeatmapLegend, HeatmapCell, CellTooltip };
