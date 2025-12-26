/**
 * Komas Trading Server - API Client
 * ==================================
 * Complete API client for all backend endpoints
 */

const API_BASE = 'http://localhost:8000/api'

// ============ HTTP HELPERS ============

async function request(url, options = {}) {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail || `HTTP ${response.status}`)
  }
  
  return response.json()
}

function get(url) {
  return request(url)
}

function post(url, data) {
  return request(url, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

function put(url, data) {
  return request(url, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

function del(url) {
  return request(url, { method: 'DELETE' })
}


// ============ DATA API ============

export const dataApi = {
  getSymbols: () => get('/data/symbols'),
  getTimeframes: () => get('/data/timeframes'),
  getAvailable: () => get('/data/available'),
  download: (params) => post('/data/download', params),
  getStatus: (symbol, timeframe) => get(`/data/status/${symbol}/${timeframe}`),
}


// ============ INDICATOR API ============

export const indicatorApi = {
  calculate: (params) => post('/indicator/calculate', params),
  getUISchema: () => get('/indicator/ui-schema'),
  getPresets: () => get('/indicator/presets'),
  
  // Heatmap
  heatmap: (params) => post('/indicator/heatmap', params),
  
  // SSE Optimization stream
  optimizeStream: (params) => {
    const queryParams = new URLSearchParams(params).toString()
    return new EventSource(`${API_BASE}/indicator/auto-optimize-stream?${queryParams}`)
  },
}


// ============ SIGNALS API ============

export const signalsApi = {
  getAll: (params = {}) => get(`/signals?${new URLSearchParams(params)}`),
  getById: (id) => get(`/signals/${id}`),
  create: (data) => post('/signals', data),
  update: (id, data) => put(`/signals/${id}`, data),
  delete: (id) => del(`/signals/${id}`),
  close: (id, data) => post(`/signals/${id}/close`, data),
  
  getActive: () => get('/signals/active'),
  getStats: () => get('/signals/stats'),
  export: (format) => get(`/signals/export?format=${format}`),
  
  // SSE Stream
  stream: () => new EventSource(`${API_BASE}/signals/sse/stream`),
}


// ============ PRESETS API ============

export const presetsApi = {
  getAll: () => ({ data: { items: [] } }), // Placeholder until backend ready
  getById: (id) => get(`/presets/${id}`),
  create: (data) => post('/presets', data),
  update: (id, data) => put(`/presets/${id}`, data),
  delete: (id) => del(`/presets/${id}`),
  duplicate: (id) => post(`/presets/${id}/duplicate`),
}


// ============ SYMBOLS API ============

export const symbolsApi = {
  getAll: () => ({ data: { items: [] } }), // Placeholder
}


// ============ NOTIFICATIONS API ============

export const notificationsApi = {
  // Settings
  getSettings: () => get('/notifications/settings'),
  updateSettings: (settings) => post('/notifications/settings', settings),
  
  // Bot validation
  validateBot: (token) => post('/notifications/validate-bot', { bot_token: token }),
  
  // Test notification
  test: (params) => post('/notifications/test', params),
  
  // Statistics
  getStats: () => get('/notifications/stats'),
  resetStats: () => post('/notifications/stats/reset'),
  
  // Send notifications
  sendSignal: (data) => post('/notifications/send/signal', data),
  sendTPHit: (data) => post('/notifications/send/tp-hit', data),
  sendSLHit: (data) => post('/notifications/send/sl-hit', data),
  sendClosed: (data) => post('/notifications/send/closed', data),
  sendError: (error, context) => post('/notifications/send/error', { error, context }),
  
  // Formats
  getFormats: () => get('/notifications/formats'),
  previewFormat: (format) => get(`/notifications/preview/${format}`),
  
  // Template validation
  validateTemplate: (template) => post('/notifications/template/validate', { template }),
  
  // Enable/Disable
  enable: () => post('/notifications/enable'),
  disable: () => post('/notifications/disable'),
}


// ============ CALENDAR API ============

export const calendarApi = {
  getEvents: (params = {}) => get(`/calendar/events?${new URLSearchParams(params)}`),
  getBlockedTimes: () => get('/calendar/blocked'),
  updateBlockSettings: (settings) => post('/calendar/settings', settings),
}


// ============ LOGS API ============

export const logsApi = {
  list: () => get('/logs/list'),
  getToday: (lines = 100) => get(`/logs/today?lines=${lines}`),
  getErrors: (lines = 50) => get(`/logs/errors?lines=${lines}`),
  download: (filename) => `${API_BASE}/logs/download/${filename}`,
  clear: (days = 7) => get(`/logs/clear?days=${days}`),
}


// ============ HEALTH API ============

export const healthApi = {
  check: () => fetch(`${API_BASE.replace('/api', '')}/health`).then(r => r.json()),
}


// ============ EXPORT DEFAULT ============

export default {
  data: dataApi,
  indicator: indicatorApi,
  signals: signalsApi,
  presets: presetsApi,
  symbols: symbolsApi,
  notifications: notificationsApi,
  calendar: calendarApi,
  logs: logsApi,
  health: healthApi,
}
