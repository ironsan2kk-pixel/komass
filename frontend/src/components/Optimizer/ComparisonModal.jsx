/**
 * KOMAS Trading Server - Comparison Modal Component
 * ==================================================
 * Side-by-side comparison of 2-5 presets.
 * 
 * Features:
 * - Visual comparison of key metrics
 * - Bar charts for metrics
 * - Highlight best values
 * - Per-pair breakdown (expandable)
 * - Export comparison
 * 
 * Chat #47: Preset Optimizer Results
 */

import React, { useState, useEffect, useMemo } from 'react';
import { GradeBadge, GRADE_CONFIG } from './ResultsPanel';
import { optimizerApi } from '../../api';

/**
 * Metrics to compare
 */
const COMPARISON_METRICS = [
  { key: 'overall_score', label: 'Overall Score', format: 'score', higherIsBetter: true },
  { key: 'avg_pnl', label: 'Average PnL %', format: 'percent', higherIsBetter: true },
  { key: 'avg_win_rate', label: 'Win Rate', format: 'ratio', higherIsBetter: true },
  { key: 'avg_sharpe', label: 'Sharpe Ratio', format: 'number', higherIsBetter: true },
  { key: 'avg_profit_factor', label: 'Profit Factor', format: 'number', higherIsBetter: true },
  { key: 'avg_max_dd', label: 'Max Drawdown', format: 'percent', higherIsBetter: false },
  { key: 'positive_ratio', label: 'Consistency', format: 'ratio', higherIsBetter: true },
  { key: 'avg_trades', label: 'Avg Trades', format: 'integer', higherIsBetter: null },
  { key: 'profitability_score', label: 'Profitability Score', format: 'score', higherIsBetter: true },
  { key: 'stability_score', label: 'Stability Score', format: 'score', higherIsBetter: true },
  { key: 'universality_score', label: 'Universality Score', format: 'score', higherIsBetter: true },
];

/**
 * Format value based on type
 */
const formatValue = (value, format) => {
  if (value === undefined || value === null) return '—';
  
  switch (format) {
    case 'score':
      return value.toFixed(1);
    case 'percent':
      return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
    case 'ratio':
      return `${(value * 100).toFixed(1)}%`;
    case 'number':
      return value.toFixed(2);
    case 'integer':
      return Math.round(value).toString();
    default:
      return value.toString();
  }
};

/**
 * Get bar color based on metric and value
 */
const getBarColor = (value, metric, isBest, isWorst) => {
  if (isBest) return 'bg-green-500';
  if (isWorst) return 'bg-red-500';
  
  // Default colors based on metric type
  if (metric.key === 'avg_pnl' || metric.key === 'overall_score') {
    return value >= 0 ? 'bg-blue-500' : 'bg-orange-500';
  }
  
  return 'bg-blue-500';
};

/**
 * Calculate best and worst for a metric
 */
const findBestWorst = (presets, metric) => {
  const values = presets.map(p => p[metric.key]).filter(v => v !== undefined && v !== null);
  if (values.length === 0) return { best: null, worst: null };
  
  if (metric.higherIsBetter === null) {
    return { best: null, worst: null };
  }
  
  const best = metric.higherIsBetter ? Math.max(...values) : Math.min(...values);
  const worst = metric.higherIsBetter ? Math.min(...values) : Math.max(...values);
  
  return { best, worst };
};

/**
 * Metric row component with comparison bars
 */
const MetricRow = ({ metric, presets }) => {
  const { best, worst } = findBestWorst(presets, metric);
  
  // Calculate max for bar scaling
  const values = presets.map(p => Math.abs(p[metric.key] || 0));
  const maxValue = Math.max(...values, 1);
  
  return (
    <tr className="border-b border-gray-800 hover:bg-gray-800/30">
      {/* Metric name */}
      <td className="px-4 py-3 text-sm text-gray-400 font-medium whitespace-nowrap">
        {metric.label}
      </td>
      
      {/* Values for each preset */}
      {presets.map((preset, idx) => {
        const value = preset[metric.key];
        const isBest = value === best && metric.higherIsBetter !== null;
        const isWorst = value === worst && metric.higherIsBetter !== null && presets.length > 2;
        const barWidth = maxValue > 0 ? (Math.abs(value || 0) / maxValue) * 100 : 0;
        
        return (
          <td key={idx} className="px-4 py-3">
            <div className="flex flex-col gap-1">
              {/* Value */}
              <span className={`
                text-sm font-medium
                ${isBest ? 'text-green-400' : isWorst ? 'text-red-400' : 'text-white'}
              `}>
                {formatValue(value, metric.format)}
                {isBest && <span className="ml-1 text-green-400">★</span>}
              </span>
              
              {/* Bar */}
              <div className="w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${getBarColor(value, metric, isBest, isWorst)}`}
                  style={{ width: `${barWidth}%` }}
                />
              </div>
            </div>
          </td>
        );
      })}
    </tr>
  );
};

/**
 * Preset header card
 */
const PresetHeader = ({ preset, index }) => {
  const grade = preset.grade || calculateGrade(preset.overall_score || 0);
  const colors = ['bg-blue-500', 'bg-purple-500', 'bg-green-500', 'bg-orange-500', 'bg-pink-500'];
  
  return (
    <th className="px-4 py-4 min-w-[180px]">
      <div className={`
        rounded-lg p-3 border-2 ${colors[index]}/20 border-${colors[index].replace('bg-', '')}/30
      `}>
        <div className="flex items-center gap-2 mb-2">
          <div className={`w-2 h-2 rounded-full ${colors[index]}`} />
          <span className="text-white font-medium truncate" title={preset.preset_name}>
            {preset.preset_name || preset.preset_id}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <GradeBadge grade={grade} score={preset.overall_score} size="sm" />
          <span className={`text-xs uppercase px-1.5 py-0.5 rounded
            ${preset.indicator_type === 'trg' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'}
          `}>
            {preset.indicator_type || '?'}
          </span>
        </div>
      </div>
    </th>
  );
};

/**
 * Per-pair comparison section
 */
const PairComparison = ({ presets, runId }) => {
  const [expanded, setExpanded] = useState(false);
  const [selectedPair, setSelectedPair] = useState(null);
  const [pairData, setPairData] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Get common pairs from all presets
  const commonPairs = useMemo(() => {
    if (!presets.length) return [];
    
    // Get pairs from first preset's pair_results
    const firstPairs = new Set(presets[0].pair_results?.map(r => r.symbol) || []);
    
    // Filter to common pairs
    for (let i = 1; i < presets.length; i++) {
      const currentPairs = new Set(presets[i].pair_results?.map(r => r.symbol) || []);
      for (const pair of firstPairs) {
        if (!currentPairs.has(pair)) {
          firstPairs.delete(pair);
        }
      }
    }
    
    return Array.from(firstPairs).sort();
  }, [presets]);
  
  // Load pair data when selected
  useEffect(() => {
    if (!selectedPair || !runId) return;
    
    const loadPairData = async () => {
      setLoading(true);
      try {
        // Get pair data for each preset
        const data = presets.map(preset => {
          const pairResult = preset.pair_results?.find(r => r.symbol === selectedPair);
          return {
            preset_id: preset.preset_id,
            preset_name: preset.preset_name,
            ...pairResult
          };
        });
        setPairData(data);
      } catch (err) {
        console.error('Failed to load pair data:', err);
      } finally {
        setLoading(false);
      }
    };
    
    loadPairData();
  }, [selectedPair, presets, runId]);
  
  if (commonPairs.length === 0) return null;
  
  return (
    <div className="mt-4 border-t border-gray-700 pt-4">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm text-gray-400 hover:text-white"
      >
        <span>{expanded ? '▼' : '▶'}</span>
        <span>Per-Pair Comparison ({commonPairs.length} pairs)</span>
      </button>
      
      {expanded && (
        <div className="mt-3">
          {/* Pair selector */}
          <select
            value={selectedPair || ''}
            onChange={(e) => setSelectedPair(e.target.value)}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white mb-3"
          >
            <option value="">Select a pair...</option>
            {commonPairs.map(pair => (
              <option key={pair} value={pair}>{pair}</option>
            ))}
          </select>
          
          {/* Pair data table */}
          {loading ? (
            <div className="text-gray-400 text-sm">Loading...</div>
          ) : pairData ? (
            <div className="overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-700">
                    <th className="px-3 py-2 text-left text-gray-400">Preset</th>
                    <th className="px-3 py-2 text-right text-gray-400">PnL %</th>
                    <th className="px-3 py-2 text-right text-gray-400">Win Rate</th>
                    <th className="px-3 py-2 text-right text-gray-400">Trades</th>
                    <th className="px-3 py-2 text-right text-gray-400">Max DD</th>
                    <th className="px-3 py-2 text-right text-gray-400">Sharpe</th>
                  </tr>
                </thead>
                <tbody>
                  {pairData.map((data, idx) => (
                    <tr key={idx} className="border-b border-gray-800">
                      <td className="px-3 py-2 text-white">{data.preset_name}</td>
                      <td className={`px-3 py-2 text-right ${data.profit_pct >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {formatValue(data.profit_pct, 'percent')}
                      </td>
                      <td className="px-3 py-2 text-right text-gray-300">
                        {formatValue(data.win_rate, 'ratio')}
                      </td>
                      <td className="px-3 py-2 text-right text-gray-300">
                        {data.total_trades || 0}
                      </td>
                      <td className="px-3 py-2 text-right text-orange-400">
                        -{Math.abs(data.max_drawdown || 0).toFixed(2)}%
                      </td>
                      <td className="px-3 py-2 text-right text-blue-400">
                        {(data.sharpe_ratio || 0).toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
};

/**
 * Main Comparison Modal Component
 */
const ComparisonModal = ({ presets, runId, onClose }) => {
  if (!presets || presets.length < 2) {
    return null;
  }
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70">
      <div className="bg-gray-900 rounded-xl border border-gray-700 w-full max-w-6xl max-h-[90vh] overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <div>
            <h2 className="text-lg font-semibold text-white">
              Preset Comparison
            </h2>
            <p className="text-sm text-gray-400">
              Comparing {presets.length} presets
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white p-2 rounded-lg hover:bg-gray-800"
          >
            ✕
          </button>
        </div>
        
        {/* Content */}
        <div className="overflow-auto p-4" style={{ maxHeight: 'calc(90vh - 120px)' }}>
          <div className="overflow-x-auto">
            <table className="min-w-full border-collapse">
              {/* Preset headers */}
              <thead>
                <tr className="border-b border-gray-700">
                  <th className="px-4 py-3 text-left text-xs text-gray-500 uppercase">
                    Metric
                  </th>
                  {presets.map((preset, idx) => (
                    <PresetHeader key={idx} preset={preset} index={idx} />
                  ))}
                </tr>
              </thead>
              
              {/* Metric rows */}
              <tbody>
                {COMPARISON_METRICS.map(metric => (
                  <MetricRow
                    key={metric.key}
                    metric={metric}
                    presets={presets}
                  />
                ))}
                
                {/* Best/Worst pair info */}
                <tr className="border-b border-gray-800">
                  <td className="px-4 py-3 text-sm text-gray-400 font-medium">Best Pair</td>
                  {presets.map((preset, idx) => (
                    <td key={idx} className="px-4 py-3">
                      <div className="text-sm">
                        <span className="text-white">{preset.best_pair || '—'}</span>
                        <span className="text-green-400 ml-1">
                          +{(preset.best_pnl || 0).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                  ))}
                </tr>
                
                <tr className="border-b border-gray-800">
                  <td className="px-4 py-3 text-sm text-gray-400 font-medium">Worst Pair</td>
                  {presets.map((preset, idx) => (
                    <td key={idx} className="px-4 py-3">
                      <div className="text-sm">
                        <span className="text-white">{preset.worst_pair || '—'}</span>
                        <span className="text-red-400 ml-1">
                          {(preset.worst_pnl || 0).toFixed(1)}%
                        </span>
                      </div>
                    </td>
                  ))}
                </tr>
                
                {/* Positive/Total pairs */}
                <tr className="border-b border-gray-800">
                  <td className="px-4 py-3 text-sm text-gray-400 font-medium">Pairs +/-</td>
                  {presets.map((preset, idx) => (
                    <td key={idx} className="px-4 py-3">
                      <span className="text-green-400">{preset.positive_pairs || 0}</span>
                      <span className="text-gray-500"> / </span>
                      <span className="text-gray-400">{preset.total_pairs || 0}</span>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
          
          {/* Per-pair comparison */}
          <PairComparison presets={presets} runId={runId} />
        </div>
        
        {/* Footer */}
        <div className="flex justify-end gap-3 p-4 border-t border-gray-700">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-400 hover:text-white"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

// Helper function
function calculateGrade(score) {
  if (score >= 85) return 'A';
  if (score >= 70) return 'B';
  if (score >= 55) return 'C';
  if (score >= 40) return 'D';
  return 'F';
}

export default ComparisonModal;
export { MetricRow, PresetHeader, COMPARISON_METRICS };
