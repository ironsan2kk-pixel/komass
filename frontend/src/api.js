import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Data API - полный набор методов
export const dataApi = {
  // Получить список символов
  getSymbols: () => api.get('/api/data/symbols'),
  
  // Скачать данные (ОРИГИНАЛЬНОЕ ИМЯ)
  downloadData: (params) => api.post('/api/data/download', params),
  
  // Скачать данные (АЛИАС для совместимости)
  download: (params) => api.post('/api/data/download', params),
  
  // Получить информацию о загруженных данных
  getDataInfo: (symbol, timeframe) => api.get(`/api/data/info/${symbol}/${timeframe}`),
  
  // Получить список загруженных файлов
  getAvailable: () => api.get('/api/data/available'),
  
  // Получить прогресс загрузки
  getProgress: () => api.get('/api/data/download/progress'),
  
  // Отменить загрузку
  cancel: (taskId) => api.post(`/api/data/download/cancel/${taskId}`),
  
  // Синхронизировать последние данные
  sync: (params) => api.post('/api/data/sync', params),
  
  // Удалить файл
  deleteFile: (filename) => api.delete(`/api/data/file/${filename}`),
  
  // Продолжить загрузку
  continue: (symbol, timeframe) => api.post(`/api/data/continue/${symbol}/${timeframe}`),
  
  // Debug endpoint
  debug: () => api.get('/api/data/debug'),
};

// Symbols API
export const symbolsApi = {
  getAll: () => api.get('/api/data/symbols'),
  getInfo: (symbol) => api.get(`/api/data/symbol/${symbol}`),
};

// Indicator API
export const indicatorApi = {
  calculate: (params) => api.post('/api/indicator/calculate', params),
  backtest: (params) => api.post('/api/indicator/backtest', params),
  autoOptimize: (params) => api.post('/api/indicator/auto-optimize', params),
  autoOptimizeStream: (params) => 
    fetch(`${API_BASE}/api/indicator/auto-optimize-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    }),
  getSchema: () => api.get('/api/indicator/ui-schema'),
  heatmap: (params) => api.post('/api/indicator/heatmap', params),
};

// Backtest API
export const backtestApi = {
  run: (params) => api.post('/api/indicator/backtest', params),
  getResults: (id) => api.get(`/api/backtest/${id}`),
  getHistory: () => api.get('/api/backtest/history'),
};

// Presets API
export const presetsApi = {
  getAll: () => api.get('/api/settings/presets'),
  get: (id) => api.get(`/api/settings/presets/${id}`),
  save: (params) => api.post('/api/settings/presets', params),
  update: (id, params) => api.put(`/api/settings/presets/${id}`, params),
  delete: (id) => api.delete(`/api/settings/presets/${id}`),
};

// Signals API
export const signalsApi = {
  getSignals: (params) => api.get('/api/signals', { params }),
  getLatest: () => api.get('/api/signals/latest'),
};

// Trades API
export const tradesApi = {
  getTrades: (params) => api.get('/api/trades', { params }),
  getStats: () => api.get('/api/trades/stats'),
};

// Performance API
export const performanceApi = {
  getSummary: () => api.get('/api/performance/summary'),
  getMonthly: () => api.get('/api/performance/monthly'),
  getEquity: () => api.get('/api/performance/equity'),
};

// Settings API
export const settingsApi = {
  getAll: () => api.get('/api/settings'),
  save: (params) => api.post('/api/settings', params),
  getPresets: () => api.get('/api/settings/presets'),
  savePreset: (params) => api.post('/api/settings/presets', params),
  deletePreset: (id) => api.delete(`/api/settings/presets/${id}`),
};

// Calendar API
export const calendarApi = {
  getEvents: (params) => api.get('/api/calendar/events', { params }),
  refresh: () => api.post('/api/calendar/refresh'),
};

// ============ BOTS API ============

export const botsApi = {
  // CRUD
  list: (params) => api.get('/api/bots/', { params }),
  create: (config) => api.post('/api/bots/', { config }),
  get: (botId) => api.get(`/api/bots/${botId}`),
  update: (botId, update) => api.patch(`/api/bots/${botId}`, update),
  delete: (botId) => api.delete(`/api/bots/${botId}`),
  
  // Summary
  getSummary: () => api.get('/api/bots/summary'),
  
  // Control
  start: (botId) => api.post(`/api/bots/${botId}/start`),
  stop: (botId) => api.post(`/api/bots/${botId}/stop`),
  pause: (botId) => api.post(`/api/bots/${botId}/pause`),
  resume: (botId) => api.post(`/api/bots/${botId}/resume`),
  forceCheck: (botId) => api.post(`/api/bots/${botId}/force-check`),
  
  // Runner
  getRunnerStatus: () => api.get('/api/bots/runner/status'),
  startRunner: () => api.post('/api/bots/runner/start'),
  stopRunner: () => api.post('/api/bots/runner/stop'),
  
  // Positions
  getOpenPositions: (botId) => api.get(`/api/bots/${botId}/positions/open`),
  getClosedPositions: (botId, limit = 50) => api.get(`/api/bots/${botId}/positions/closed`, { params: { limit } }),
  closePosition: (botId, positionId, partialPercent = null) => 
    api.post(`/api/bots/${botId}/positions/close`, { position_id: positionId, partial_percent: partialPercent }),
  
  // Statistics
  getStatistics: (botId) => api.get(`/api/bots/${botId}/statistics`),
  recalculateStatistics: (botId) => api.post(`/api/bots/${botId}/statistics/recalculate`),
  
  // Equity
  getEquity: (botId, limit = 100) => api.get(`/api/bots/${botId}/equity`, { params: { limit } }),
  
  // Logs
  getLogs: (botId, params = {}) => api.get(`/api/bots/${botId}/logs`, { params }),
  
  // SSE Stream
  streamEvents: (botId) => new EventSource(`${API_BASE}/api/bots/${botId}/stream`),
  
  // Bulk operations
  startAll: () => api.post('/api/bots/start-all'),
  stopAll: () => api.post('/api/bots/stop-all'),
  
  // Presets
  getStrategyPresets: () => api.get('/api/bots/presets/strategies'),
  
  // Duplicate
  duplicate: (botId, newName) => api.post(`/api/bots/${botId}/duplicate`, null, { params: { new_name: newName } }),
  
  // Export/Import
  exportConfig: (botId) => api.get(`/api/bots/${botId}/export`),
  importConfig: (config, nameOverride = null) => 
    api.post('/api/bots/import', { config, name_override: nameOverride }),
};

export default api;
