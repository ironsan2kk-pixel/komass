/**
 * KOMAS Trading Server - Optimization Results Panel
 * ==================================================
 * Main component for displaying preset optimization results.
 * 
 * Features:
 * - Summary header with run info
 * - Sortable ranking table
 * - Filtering by grade, indicator, search
 * - Pagination
 * - Export buttons (CSV/JSON)
 * - Comparison modal
 * 
 * Chat #47: Preset Optimizer Results
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import ResultsTable from './ResultsTable';
import ComparisonModal from './ComparisonModal';
import ExportButtons from './ExportButtons';
import { optimizerApi } from '../../api';

// Grade configuration
const GRADE_CONFIG = {
  A: { color: 'text-green-400', bg: 'bg-green-500/20', border: 'border-green-500/30', label: 'Excellent' },
  B: { color: 'text-blue-400', bg: 'bg-blue-500/20', border: 'border-blue-500/30', label: 'Good' },
  C: { color: 'text-yellow-400', bg: 'bg-yellow-500/20', border: 'border-yellow-500/30', label: 'Average' },
  D: { color: 'text-orange-400', bg: 'bg-orange-500/20', border: 'border-orange-500/30', label: 'Below Avg' },
  F: { color: 'text-red-400', bg: 'bg-red-500/20', border: 'border-red-500/30', label: 'Poor' }
};

// Mode icons
const MODE_ICONS = {
  quick: '⚡',
  standard: '⚖️',
  smart: '🧠',
  full: '🔬'
};

/**
 * Format duration in seconds to human readable
 */
const formatDuration = (seconds) => {
  if (!seconds) return '—';
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}m ${secs}s`;
};

/**
 * Format date string
 */
const formatDate = (dateStr) => {
  if (!dateStr) return '—';
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
};

/**
 * Grade badge component
 */
const GradeBadge = ({ grade, score, size = 'md' }) => {
  const config = GRADE_CONFIG[grade] || GRADE_CONFIG.F;
  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-lg px-3 py-1.5 font-bold'
  };
  
  return (
    <span className={`
      inline-flex items-center gap-1 rounded-md font-medium
      ${config.bg} ${config.border} border ${config.color}
      ${sizeClasses[size]}
    `}>
      <span>{grade}</span>
      {score !== undefined && <span className="opacity-70">({score.toFixed(0)})</span>}
    </span>
  );
};

/**
 * Summary header component
 */
const ResultsSummary = ({ result, onClose }) => {
  if (!result) return null;
  
  const bestPreset = result.preset_scores?.[0];
  
  return (
    <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-4 mb-4">
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{MODE_ICONS[result.mode] || '📊'}</span>
          <div>
            <h3 className="text-lg font-semibold text-white">
              Optimization Results
            </h3>
            <p className="text-sm text-gray-400">
              Run ID: {result.run_id}
            </p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white p-1"
          >
            ✕
          </button>
        )}
      </div>
      
      {/* Stats grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {/* Mode */}
        <div className="bg-gray-900/50 rounded p-2">
          <div className="text-xs text-gray-500 uppercase">Mode</div>
          <div className="text-white font-medium capitalize">{result.mode}</div>
        </div>
        
        {/* Timeframe */}
        <div className="bg-gray-900/50 rounded p-2">
          <div className="text-xs text-gray-500 uppercase">Timeframe</div>
          <div className="text-white font-medium">{result.timeframe || '1h'}</div>
        </div>
        
        {/* Combinations */}
        <div className="bg-gray-900/50 rounded p-2">
          <div className="text-xs text-gray-500 uppercase">Combinations</div>
          <div className="text-white font-medium">
            {result.completed_combinations?.toLocaleString() || 0} / {result.total_combinations?.toLocaleString() || 0}
          </div>
        </div>
        
        {/* Duration */}
        <div className="bg-gray-900/50 rounded p-2">
          <div className="text-xs text-gray-500 uppercase">Duration</div>
          <div className="text-white font-medium">
            {formatDuration(result.duration_seconds)}
          </div>
        </div>
        
        {/* Presets/Pairs */}
        <div className="bg-gray-900/50 rounded p-2">
          <div className="text-xs text-gray-500 uppercase">Presets × Pairs</div>
          <div className="text-white font-medium">
            {result.effective_preset_count || 0} × {result.effective_pair_count || 0}
          </div>
        </div>
        
        {/* Workers */}
        <div className="bg-gray-900/50 rounded p-2">
          <div className="text-xs text-gray-500 uppercase">Workers</div>
          <div className="text-white font-medium">{result.num_workers || 1}</div>
        </div>
      </div>
      
      {/* Best preset */}
      {bestPreset && (
        <div className="mt-3 pt-3 border-t border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-gray-400 text-sm">🏆 Best Preset:</span>
              <span className="text-white font-medium">
                {bestPreset.preset_name || bestPreset.preset_id}
              </span>
              <GradeBadge grade={bestPreset.grade} score={bestPreset.overall_score} size="sm" />
            </div>
            <div className="flex items-center gap-4 text-sm">
              <span className={bestPreset.avg_pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                PnL: {bestPreset.avg_pnl >= 0 ? '+' : ''}{bestPreset.avg_pnl?.toFixed(2)}%
              </span>
              <span className="text-blue-400">
                WR: {(bestPreset.avg_win_rate * 100)?.toFixed(1)}%
              </span>
              <span className="text-purple-400">
                SR: {bestPreset.avg_sharpe?.toFixed(2)}
              </span>
            </div>
          </div>
        </div>
      )}
      
      {/* Errors if any */}
      {result.errors && result.errors.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-700">
          <div className="text-yellow-400 text-sm">
            ⚠️ {result.errors.length} error(s) during optimization
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Filters bar component
 */
const FiltersBar = ({ 
  filters, 
  onFilterChange, 
  selectedCount,
  onCompareClick,
  onClearSelection 
}) => {
  return (
    <div className="flex flex-wrap items-center gap-3 mb-4">
      {/* Search */}
      <div className="relative flex-1 min-w-[200px] max-w-[300px]">
        <input
          type="text"
          value={filters.search}
          onChange={(e) => onFilterChange('search', e.target.value)}
          placeholder="Search presets..."
          className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 pl-9
            text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">🔍</span>
      </div>
      
      {/* Grade filter */}
      <select
        value={filters.grade}
        onChange={(e) => onFilterChange('grade', e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
          text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">All Grades</option>
        <option value="A">A - Excellent</option>
        <option value="B">B - Good</option>
        <option value="C">C - Average</option>
        <option value="D">D - Below Avg</option>
        <option value="F">F - Poor</option>
      </select>
      
      {/* Indicator filter */}
      <select
        value={filters.indicator}
        onChange={(e) => onFilterChange('indicator', e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
          text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="">All Indicators</option>
        <option value="trg">TRG</option>
        <option value="dominant">Dominant</option>
      </select>
      
      {/* Sort */}
      <select
        value={filters.sortBy}
        onChange={(e) => onFilterChange('sortBy', e.target.value)}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
          text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        <option value="overall_score">Sort: Score</option>
        <option value="avg_pnl">Sort: PnL</option>
        <option value="avg_win_rate">Sort: Win Rate</option>
        <option value="avg_sharpe">Sort: Sharpe</option>
        <option value="positive_ratio">Sort: Consistency</option>
        <option value="avg_max_dd">Sort: Drawdown</option>
      </select>
      
      {/* Sort order toggle */}
      <button
        onClick={() => onFilterChange('sortOrder', filters.sortOrder === 'desc' ? 'asc' : 'desc')}
        className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2
          text-white hover:bg-gray-700 transition"
        title={filters.sortOrder === 'desc' ? 'Descending' : 'Ascending'}
      >
        {filters.sortOrder === 'desc' ? '↓' : '↑'}
      </button>
      
      {/* Spacer */}
      <div className="flex-1" />
      
      {/* Selection actions */}
      {selectedCount > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-gray-400 text-sm">
            {selectedCount} selected
          </span>
          <button
            onClick={onCompareClick}
            disabled={selectedCount < 2 || selectedCount > 5}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed
              text-white px-3 py-2 rounded-lg text-sm transition"
          >
            Compare ({selectedCount})
          </button>
          <button
            onClick={onClearSelection}
            className="text-gray-400 hover:text-white text-sm"
          >
            Clear
          </button>
        </div>
      )}
    </div>
  );
};

/**
 * Main Results Panel Component
 */
const ResultsPanel = ({ 
  result,
  runId,
  onClose,
  showHistory = false 
}) => {
  // State
  const [scores, setScores] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({ total: 0, filtered: 0, offset: 0, limit: 50 });
  const [selected, setSelected] = useState(new Set());
  const [showComparison, setShowComparison] = useState(false);
  
  const [filters, setFilters] = useState({
    search: '',
    grade: '',
    indicator: '',
    sortBy: 'overall_score',
    sortOrder: 'desc'
  });
  
  // Load result data if not provided
  const [resultData, setResultData] = useState(result);
  
  useEffect(() => {
    if (result) {
      setResultData(result);
      // Use preset_scores from result if available
      if (result.preset_scores) {
        setScores(result.preset_scores);
        setPagination(p => ({ ...p, total: result.preset_scores.length, filtered: result.preset_scores.length }));
      }
    } else if (runId) {
      loadResult();
    }
  }, [result, runId]);
  
  // Load result from API
  const loadResult = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await optimizerApi.getResults(runId);
      setResultData(response.data);
      if (response.data.preset_scores) {
        setScores(response.data.preset_scores);
        setPagination(p => ({ 
          ...p, 
          total: response.data.preset_scores.length, 
          filtered: response.data.preset_scores.length 
        }));
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Load scores with filters and pagination
  const loadScores = useCallback(async () => {
    if (!runId && !resultData?.run_id) return;
    
    const effectiveRunId = runId || resultData?.run_id;
    setLoading(true);
    
    try {
      const response = await optimizerApi.getPresetScores?.(effectiveRunId, {
        limit: pagination.limit,
        offset: pagination.offset,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder,
        min_score: filters.grade ? getMinScoreForGrade(filters.grade) : undefined,
        indicator_type: filters.indicator || undefined,
        search: filters.search || undefined
      });
      
      if (response?.data) {
        setScores(response.data.scores || []);
        setPagination(p => ({
          ...p,
          total: response.data.total,
          filtered: response.data.filtered
        }));
      }
    } catch (err) {
      // Fall back to client-side filtering if API fails
      applyClientFilters();
    } finally {
      setLoading(false);
    }
  }, [runId, resultData?.run_id, filters, pagination.limit, pagination.offset]);
  
  // Client-side filtering fallback
  const applyClientFilters = useCallback(() => {
    if (!resultData?.preset_scores) return;
    
    let filtered = [...resultData.preset_scores];
    
    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      filtered = filtered.filter(s => 
        s.preset_name?.toLowerCase().includes(searchLower) ||
        s.preset_id?.toLowerCase().includes(searchLower)
      );
    }
    
    // Grade filter
    if (filters.grade) {
      const minScore = getMinScoreForGrade(filters.grade);
      const maxScore = getMaxScoreForGrade(filters.grade);
      filtered = filtered.filter(s => 
        s.overall_score >= minScore && s.overall_score < maxScore
      );
    }
    
    // Indicator filter
    if (filters.indicator) {
      filtered = filtered.filter(s => 
        s.indicator_type?.toLowerCase() === filters.indicator.toLowerCase()
      );
    }
    
    // Sort
    filtered.sort((a, b) => {
      const aVal = a[filters.sortBy] || 0;
      const bVal = b[filters.sortBy] || 0;
      return filters.sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });
    
    // Paginate
    const paginated = filtered.slice(pagination.offset, pagination.offset + pagination.limit);
    
    setScores(paginated);
    setPagination(p => ({
      ...p,
      total: resultData.preset_scores.length,
      filtered: filtered.length
    }));
  }, [resultData?.preset_scores, filters, pagination.limit, pagination.offset]);
  
  // Apply filters when they change
  useEffect(() => {
    applyClientFilters();
    // Reset selection on filter change
    setSelected(new Set());
  }, [filters, applyClientFilters]);
  
  // Filter change handler
  const handleFilterChange = (key, value) => {
    setFilters(f => ({ ...f, [key]: value }));
    setPagination(p => ({ ...p, offset: 0 }));
  };
  
  // Selection handlers
  const handleSelect = (presetId) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(presetId)) {
        next.delete(presetId);
      } else {
        next.add(presetId);
      }
      return next;
    });
  };
  
  const handleSelectAll = () => {
    if (selected.size === scores.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(scores.map(s => s.preset_id)));
    }
  };
  
  // Pagination handlers
  const handlePageChange = (newOffset) => {
    setPagination(p => ({ ...p, offset: newOffset }));
  };
  
  // Compare handler
  const handleCompare = () => {
    if (selected.size >= 2 && selected.size <= 5) {
      setShowComparison(true);
    }
  };
  
  // Get selected presets data
  const selectedPresets = useMemo(() => {
    return scores.filter(s => selected.has(s.preset_id));
  }, [scores, selected]);
  
  if (loading && !resultData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4 text-red-400">
        <strong>Error:</strong> {error}
      </div>
    );
  }
  
  if (!resultData) {
    return (
      <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-8 text-center text-gray-400">
        <p>No optimization results to display.</p>
        <p className="text-sm mt-2">Run an optimization to see results here.</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      {/* Summary header */}
      <ResultsSummary result={resultData} onClose={onClose} />
      
      {/* Export buttons */}
      <div className="flex justify-end">
        <ExportButtons runId={resultData.run_id} />
      </div>
      
      {/* Filters */}
      <FiltersBar
        filters={filters}
        onFilterChange={handleFilterChange}
        selectedCount={selected.size}
        onCompareClick={handleCompare}
        onClearSelection={() => setSelected(new Set())}
      />
      
      {/* Results table */}
      <ResultsTable
        scores={scores}
        loading={loading}
        selected={selected}
        onSelect={handleSelect}
        onSelectAll={handleSelectAll}
        sortBy={filters.sortBy}
        sortOrder={filters.sortOrder}
        onSort={(field) => {
          if (filters.sortBy === field) {
            handleFilterChange('sortOrder', filters.sortOrder === 'desc' ? 'asc' : 'desc');
          } else {
            handleFilterChange('sortBy', field);
            handleFilterChange('sortOrder', 'desc');
          }
        }}
      />
      
      {/* Pagination */}
      {pagination.filtered > pagination.limit && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">
            Showing {pagination.offset + 1} - {Math.min(pagination.offset + pagination.limit, pagination.filtered)} of {pagination.filtered}
            {pagination.filtered !== pagination.total && ` (filtered from ${pagination.total})`}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => handlePageChange(Math.max(0, pagination.offset - pagination.limit))}
              disabled={pagination.offset === 0}
              className="px-3 py-1 bg-gray-800 border border-gray-700 rounded
                hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ← Prev
            </button>
            <button
              onClick={() => handlePageChange(pagination.offset + pagination.limit)}
              disabled={pagination.offset + pagination.limit >= pagination.filtered}
              className="px-3 py-1 bg-gray-800 border border-gray-700 rounded
                hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next →
            </button>
          </div>
        </div>
      )}
      
      {/* Comparison modal */}
      {showComparison && (
        <ComparisonModal
          presets={selectedPresets}
          runId={resultData.run_id}
          onClose={() => setShowComparison(false)}
        />
      )}
    </div>
  );
};

// Helper functions
function getMinScoreForGrade(grade) {
  const scores = { A: 85, B: 70, C: 55, D: 40, F: 0 };
  return scores[grade] ?? 0;
}

function getMaxScoreForGrade(grade) {
  const scores = { A: 100, B: 85, C: 70, D: 55, F: 40 };
  return scores[grade] ?? 100;
}

export default ResultsPanel;
export { ResultsSummary, GradeBadge, FiltersBar, GRADE_CONFIG, MODE_ICONS };
