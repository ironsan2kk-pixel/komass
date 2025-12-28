/**
 * KOMAS Trading Server - Optimization History Panel
 * ==================================================
 * Display and manage past optimization runs.
 * 
 * Features:
 * - List of past runs with summary
 * - Filter by mode, status
 * - Load results from history
 * - Delete old runs
 * 
 * Chat #47: Preset Optimizer Results
 */

import React, { useState, useEffect, useCallback } from 'react';
import { optimizerApi } from '../../api';
import { GradeBadge, MODE_ICONS } from './ResultsPanel';

/**
 * Status badge component
 */
const StatusBadge = ({ status }) => {
  const config = {
    completed: { bg: 'bg-green-500/20', text: 'text-green-400', label: 'Completed' },
    running: { bg: 'bg-blue-500/20', text: 'text-blue-400', label: 'Running' },
    pending: { bg: 'bg-yellow-500/20', text: 'text-yellow-400', label: 'Pending' },
    error: { bg: 'bg-red-500/20', text: 'text-red-400', label: 'Error' },
    cancelled: { bg: 'bg-gray-500/20', text: 'text-gray-400', label: 'Cancelled' }
  };
  
  const c = config[status] || config.completed;
  
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${c.bg} ${c.text}`}>
      {c.label}
    </span>
  );
};

/**
 * Format duration
 */
const formatDuration = (seconds) => {
  if (!seconds) return '—';
  if (seconds < 60) return `${seconds.toFixed(1)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}m ${secs}s`;
};

/**
 * Format date
 */
const formatDate = (dateStr) => {
  if (!dateStr) return '—';
  try {
    const date = new Date(dateStr);
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  } catch {
    return dateStr;
  }
};

/**
 * History item card
 */
const HistoryItem = ({ run, onLoad, onDelete, isLoading }) => {
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);
  
  return (
    <div className={`
      bg-gray-800/50 rounded-lg border border-gray-700 p-4
      hover:border-gray-600 transition-all
      ${isLoading ? 'opacity-50' : ''}
    `}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{MODE_ICONS[run.mode] || '📊'}</span>
          <div>
            <div className="text-white font-medium capitalize">
              {run.mode} Optimization
            </div>
            <div className="text-xs text-gray-500">{run.run_id}</div>
          </div>
        </div>
        <StatusBadge status={run.status} />
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm mb-3">
        <div>
          <span className="text-gray-500">Timeframe: </span>
          <span className="text-gray-300">{run.timeframe}</span>
        </div>
        <div>
          <span className="text-gray-500">Combinations: </span>
          <span className="text-gray-300">{run.total_combinations?.toLocaleString() || 0}</span>
        </div>
        <div>
          <span className="text-gray-500">Duration: </span>
          <span className="text-gray-300">{formatDuration(run.duration_seconds)}</span>
        </div>
        <div>
          <span className="text-gray-500">Date: </span>
          <span className="text-gray-300">{formatDate(run.created_at)}</span>
        </div>
      </div>
      
      {/* Best preset info */}
      {run.best_preset_name && (
        <div className="flex items-center gap-2 mb-3 text-sm">
          <span className="text-gray-500">🏆 Best:</span>
          <span className="text-white">{run.best_preset_name}</span>
          {run.best_overall_score && (
            <GradeBadge 
              grade={calculateGrade(run.best_overall_score)} 
              score={run.best_overall_score} 
              size="sm" 
            />
          )}
          {run.best_avg_pnl !== undefined && (
            <span className={run.best_avg_pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
              {run.best_avg_pnl >= 0 ? '+' : ''}{run.best_avg_pnl.toFixed(2)}%
            </span>
          )}
        </div>
      )}
      
      {/* Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-700">
        {showConfirmDelete ? (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Delete this run?</span>
            <button
              onClick={() => {
                onDelete(run.run_id);
                setShowConfirmDelete(false);
              }}
              className="px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs rounded"
            >
              Yes, delete
            </button>
            <button
              onClick={() => setShowConfirmDelete(false)}
              className="px-2 py-1 text-gray-400 hover:text-white text-xs"
            >
              Cancel
            </button>
          </div>
        ) : (
          <>
            <button
              onClick={() => setShowConfirmDelete(true)}
              className="text-gray-500 hover:text-red-400 text-sm"
            >
              🗑️ Delete
            </button>
            <button
              onClick={() => onLoad(run.run_id)}
              disabled={run.status !== 'completed'}
              className="px-4 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50
                disabled:cursor-not-allowed text-white text-sm rounded-lg"
            >
              Load Results →
            </button>
          </>
        )}
      </div>
    </div>
  );
};

/**
 * Calculate grade from score
 */
function calculateGrade(score) {
  if (score >= 85) return 'A';
  if (score >= 70) return 'B';
  if (score >= 55) return 'C';
  if (score >= 40) return 'D';
  return 'F';
}

/**
 * Main History Panel Component
 */
const HistoryPanel = ({ onLoadRun }) => {
  const [runs, setRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({ total: 0, offset: 0, limit: 10, hasMore: false });
  const [filters, setFilters] = useState({ mode: '', status: '' });
  const [deleteLoading, setDeleteLoading] = useState(null);
  
  // Load history
  const loadHistory = useCallback(async (reset = false) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await optimizerApi.getHistory?.({
        limit: pagination.limit,
        offset: reset ? 0 : pagination.offset,
        mode: filters.mode || undefined,
        status: filters.status || undefined
      }) || { data: { runs: [], total: 0 } };
      
      const data = response.data;
      setRuns(data.runs || []);
      setPagination(p => ({
        ...p,
        total: data.total || 0,
        offset: reset ? 0 : p.offset,
        hasMore: data.has_more || false
      }));
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  }, [pagination.limit, pagination.offset, filters]);
  
  // Initial load
  useEffect(() => {
    loadHistory(true);
  }, [filters]);
  
  // Handle delete
  const handleDelete = async (runId) => {
    setDeleteLoading(runId);
    try {
      await optimizerApi.deleteResult?.(runId);
      setRuns(r => r.filter(run => run.run_id !== runId));
      setPagination(p => ({ ...p, total: p.total - 1 }));
    } catch (err) {
      setError(`Delete failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setDeleteLoading(null);
    }
  };
  
  // Handle clear all
  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to delete ALL optimization history?')) {
      return;
    }
    
    setLoading(true);
    try {
      await optimizerApi.clearHistory?.();
      setRuns([]);
      setPagination(p => ({ ...p, total: 0 }));
    } catch (err) {
      setError(`Clear failed: ${err.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-white">Optimization History</h3>
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-400">{pagination.total} runs</span>
          {pagination.total > 0 && (
            <button
              onClick={handleClearAll}
              className="text-sm text-red-400 hover:text-red-300"
            >
              Clear All
            </button>
          )}
        </div>
      </div>
      
      {/* Filters */}
      <div className="flex gap-3">
        <select
          value={filters.mode}
          onChange={(e) => setFilters(f => ({ ...f, mode: e.target.value }))}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
        >
          <option value="">All Modes</option>
          <option value="quick">⚡ Quick</option>
          <option value="standard">⚖️ Standard</option>
          <option value="smart">🧠 Smart</option>
          <option value="full">🔬 Full</option>
        </select>
        
        <select
          value={filters.status}
          onChange={(e) => setFilters(f => ({ ...f, status: e.target.value }))}
          className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm"
        >
          <option value="">All Status</option>
          <option value="completed">✅ Completed</option>
          <option value="error">❌ Error</option>
          <option value="cancelled">⏹️ Cancelled</option>
        </select>
        
        <button
          onClick={() => loadHistory(true)}
          className="px-3 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white text-sm
            hover:bg-gray-700"
        >
          🔄 Refresh
        </button>
      </div>
      
      {/* Error */}
      {error && (
        <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-3 text-red-400 text-sm">
          {error}
        </div>
      )}
      
      {/* Loading */}
      {loading && runs.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin h-8 w-8 border-2 border-blue-500 border-t-transparent rounded-full" />
        </div>
      )}
      
      {/* Empty state */}
      {!loading && runs.length === 0 && (
        <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-8 text-center text-gray-400">
          <span className="text-4xl block mb-2">📊</span>
          <p>No optimization runs found.</p>
          <p className="text-sm mt-1">Run an optimization to see history here.</p>
        </div>
      )}
      
      {/* History list */}
      <div className="space-y-3">
        {runs.map(run => (
          <HistoryItem
            key={run.run_id}
            run={run}
            onLoad={onLoadRun}
            onDelete={handleDelete}
            isLoading={deleteLoading === run.run_id}
          />
        ))}
      </div>
      
      {/* Pagination */}
      {pagination.total > pagination.limit && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-400">
            Showing {pagination.offset + 1} - {Math.min(pagination.offset + runs.length, pagination.total)} of {pagination.total}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => {
                setPagination(p => ({ ...p, offset: Math.max(0, p.offset - p.limit) }));
                loadHistory();
              }}
              disabled={pagination.offset === 0}
              className="px-3 py-1 bg-gray-800 border border-gray-700 rounded
                hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              ← Prev
            </button>
            <button
              onClick={() => {
                setPagination(p => ({ ...p, offset: p.offset + p.limit }));
                loadHistory();
              }}
              disabled={!pagination.hasMore}
              className="px-3 py-1 bg-gray-800 border border-gray-700 rounded
                hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next →
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default HistoryPanel;
export { HistoryItem, StatusBadge };
