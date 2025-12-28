/**
 * KOMAS Trading Server - API Client Additions for Heatmap
 * ========================================================
 * Add these methods to the optimizerApi object in api.js
 * 
 * Chat #48: Preset Optimizer Heatmap
 */

// ============ HEATMAP METHODS (Chat #48) ============

// Get heatmap data for visualization
// metric: 'pnl' | 'win_rate' | 'max_dd' | 'sharpe' | 'profit_factor' | 'trades'
getHeatmap: (runId, metric = 'pnl', limitPresets = null, limitPairs = null) => {
  const params = { metric };
  if (limitPresets) params.limit_presets = limitPresets;
  if (limitPairs) params.limit_pairs = limitPairs;
  return api.get(`/api/optimizer/results/${runId}/heatmap`, { params });
},

// Get available metrics for heatmap
getHeatmapMetrics: (runId) => 
  api.get(`/api/optimizer/results/${runId}/heatmap/metrics`),

// Export heatmap as CSV
exportHeatmapCsv: (runId, metric = 'pnl') =>
  api.get(`/api/optimizer/results/${runId}/heatmap/export`, {
    params: { metric },
    responseType: 'blob'
  }),

// Get detailed cell metrics (for tooltip)
getHeatmapCell: (runId, presetId, pair) =>
  api.get(`/api/optimizer/results/${runId}/heatmap/cell/${presetId}/${pair}`),

// ============ HISTORY METHODS (Chat #47) ============

// Get optimization history with pagination
getHistory: (limit = 20, offset = 0, mode = null, status = null) => {
  const params = { limit, offset };
  if (mode) params.mode = mode;
  if (status) params.status = status;
  return api.get('/api/optimizer/history', { params });
},

// Delete optimization run
deleteRun: (runId) =>
  api.delete(`/api/optimizer/results/${runId}`),

// Get preset scores for a run with pagination
getPresetScores: (runId, limit = 50, offset = 0, sortBy = 'overall_score', sortOrder = 'desc') =>
  api.get(`/api/optimizer/results/${runId}/scores`, {
    params: { limit, offset, sort_by: sortBy, sort_order: sortOrder }
  }),

// Export as CSV
exportCsv: (runId) =>
  api.get(`/api/optimizer/results/${runId}/export/csv`, {
    responseType: 'blob'
  }),

// Export as JSON
exportJson: (runId) =>
  api.get(`/api/optimizer/results/${runId}/export/json`),

// Aggregate by preset
aggregateByPreset: (presetId) =>
  api.get(`/api/optimizer/aggregation/preset/${presetId}`),

// Aggregate by pair
aggregateByPair: () =>
  api.get('/api/optimizer/aggregation/pair'),
