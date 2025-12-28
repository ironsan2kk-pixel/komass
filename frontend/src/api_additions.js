/**
 * KOMAS Trading Server - Optimizer API Methods
 * =============================================
 * Additional API methods for optimization results.
 * 
 * ADD these methods to optimizerApi object in api.js
 * 
 * Chat #47: Preset Optimizer Results
 */

// ============================================================================
// ADD to optimizerApi object in api.js:
// ============================================================================

// History endpoints
getHistory: (params = {}) => {
  const query = new URLSearchParams();
  if (params.limit) query.append('limit', params.limit);
  if (params.offset) query.append('offset', params.offset);
  if (params.mode) query.append('mode', params.mode);
  if (params.status) query.append('status', params.status);
  return api.get(`/api/optimizer/history?${query.toString()}`);
},

deleteResult: (runId) => 
  api.delete(`/api/optimizer/results/${runId}`),

clearHistory: (keepRecent = 0) => 
  api.delete(`/api/optimizer/history/clear?keep_recent=${keepRecent}`),

// Scores with pagination
getResultScores: (runId, params = {}) => {
  const query = new URLSearchParams();
  if (params.limit) query.append('limit', params.limit);
  if (params.offset) query.append('offset', params.offset);
  if (params.grade) query.append('grade', params.grade);
  if (params.indicator) query.append('indicator', params.indicator);
  if (params.search) query.append('search', params.search);
  if (params.sort_by) query.append('sort_by', params.sort_by);
  if (params.sort_order) query.append('sort_order', params.sort_order);
  return api.get(`/api/optimizer/results/${runId}/scores?${query.toString()}`);
},

// Export endpoints
exportCsv: (runId) => 
  api.get(`/api/optimizer/results/${runId}/export/csv`, { responseType: 'text' }),

exportJson: (runId) => 
  api.get(`/api/optimizer/results/${runId}/export/json`),

// Aggregation endpoints
aggregateByPreset: (presetId) => 
  api.get(`/api/optimizer/aggregation/preset/${presetId}`),

aggregateByPair: (pair, params = {}) => {
  const query = new URLSearchParams();
  if (params.run_id) query.append('run_id', params.run_id);
  return api.get(`/api/optimizer/aggregation/pair?pair=${pair}&${query.toString()}`);
},

// ============================================================================
// FULL optimizerApi object (REPLACE in api.js):
// ============================================================================

/*
export const optimizerApi = {
  // Mode endpoints (Chat #46)
  getModes: () => api.get('/api/optimizer/modes'),
  getModeConfig: (mode) => api.get(`/api/optimizer/modes/${mode}`),
  estimate: (data) => api.post('/api/optimizer/estimate', data),
  getLiquidity: () => api.get('/api/optimizer/liquidity'),
  
  // Run endpoints (Chat #45)
  runOptimization: (data) => api.post('/api/optimizer/presets/run', data),
  getResults: (runId) => api.get(`/api/optimizer/presets/results?run_id=${runId}`),
  cancelOptimization: (runId) => api.post('/api/optimizer/presets/cancel', { run_id: runId }),
  getActive: () => api.get('/api/optimizer/presets/active'),
  getStatus: (runId) => api.get(`/api/optimizer/presets/status/${runId}`),
  
  // SSE Stream (Chat #45)
  streamOptimization: (data, onEvent) => {
    const eventSource = new EventSource(
      `/api/optimizer/presets/stream?${new URLSearchParams(data).toString()}`
    );
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onEvent(data);
    };
    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
    };
    return eventSource;
  },
  
  // History endpoints (Chat #47 - NEW)
  getHistory: (params = {}) => {
    const query = new URLSearchParams();
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);
    if (params.mode) query.append('mode', params.mode);
    if (params.status) query.append('status', params.status);
    return api.get(`/api/optimizer/history?${query.toString()}`);
  },
  
  deleteResult: (runId) => 
    api.delete(`/api/optimizer/results/${runId}`),
  
  clearHistory: (keepRecent = 0) => 
    api.delete(`/api/optimizer/history/clear?keep_recent=${keepRecent}`),
  
  // Scores with pagination (Chat #47 - NEW)
  getResultScores: (runId, params = {}) => {
    const query = new URLSearchParams();
    if (params.limit) query.append('limit', params.limit);
    if (params.offset) query.append('offset', params.offset);
    if (params.grade) query.append('grade', params.grade);
    if (params.indicator) query.append('indicator', params.indicator);
    if (params.search) query.append('search', params.search);
    if (params.sort_by) query.append('sort_by', params.sort_by);
    if (params.sort_order) query.append('sort_order', params.sort_order);
    return api.get(`/api/optimizer/results/${runId}/scores?${query.toString()}`);
  },
  
  // Export endpoints (Chat #47 - NEW)
  exportCsv: (runId) => 
    api.get(`/api/optimizer/results/${runId}/export/csv`, { responseType: 'text' }),
  
  exportJson: (runId) => 
    api.get(`/api/optimizer/results/${runId}/export/json`),
  
  // Aggregation endpoints (Chat #47 - NEW)
  aggregateByPreset: (presetId) => 
    api.get(`/api/optimizer/aggregation/preset/${presetId}`),
  
  aggregateByPair: (pair, params = {}) => {
    const query = new URLSearchParams();
    if (params.run_id) query.append('run_id', params.run_id);
    return api.get(`/api/optimizer/aggregation/pair?pair=${pair}&${query.toString()}`);
  },
};
*/
