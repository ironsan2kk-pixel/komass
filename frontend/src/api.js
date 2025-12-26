/**
 * Komas Trading Server v3 - API Client
 * Полная интеграция со всеми backend endpoints
 */

import axios from 'axios';

const API_BASE = 'http://localhost:8000';

// Базовый экземпляр axios
export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

// Интерцептор для логирования ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ============================================
// Data API - Управление данными
// ============================================
export const dataApi = {
  // Список доступных символов
  getSymbols: () => api.get('/api/data/symbols'),
  
  // Список таймфреймов
  getTimeframes: () => api.get('/api/data/timeframes'),
  
  // Загрузка данных с биржи
  downloadData: (params) => api.post('/api/data/download', params),
  
  // Прогресс загрузки
  getDownloadProgress: (taskId) => api.get(`/api/data/download/progress/${taskId}`),
  
  // Информация о загруженных данных
  getDataInfo: (symbol, timeframe) => api.get(`/api/data/info/${symbol}/${timeframe}`),
  
  // Список загруженных файлов
  getAvailable: () => api.get('/api/data/available'),
  
  // Синхронизация данных
  sync: (params) => api.post('/api/data/sync', params),
  
  // Удаление данных
  deleteData: (symbol, timeframe) => api.delete(`/api/data/${symbol}/${timeframe}`),
};

// ============================================
// Symbols API - Работа с торговыми парами
// ============================================
export const symbolsApi = {
  getAll: () => api.get('/api/data/symbols'),
  getInfo: (symbol) => api.get(`/api/data/symbol/${symbol}`),
  search: (query) => api.get('/api/data/symbols/search', { params: { q: query } }),
};

// ============================================
// Indicator API - Расчёт индикатора и бэктест
// ============================================
export const indicatorApi = {
  // Основной расчёт индикатора + бэктест
  calculate: (params) => api.post('/api/indicator/calculate', params),
  
  // Полный бэктест
  backtest: (params) => api.post('/api/indicator/backtest', params),
  
  // Автооптимизация (обычный POST)
  autoOptimize: (params) => api.post('/api/indicator/auto-optimize', params),
  
  // Автооптимизация с SSE стримингом
  autoOptimizeStream: (params) => {
    const queryString = new URLSearchParams(params).toString();
    return new EventSource(`${API_BASE}/api/indicator/auto-optimize-stream?${queryString}`);
  },
  
  // Heatmap генерация
  heatmap: (params) => api.post('/api/indicator/heatmap', params),
  
  // UI Schema для динамической генерации форм
  getUISchema: (plugin = 'trg') => api.get(`/api/indicator/ui-schema/${plugin}`),
  
  // Пресеты настроек
  getPresets: () => api.get('/api/indicator/presets'),
  
  // Replay mode
  replay: (params) => api.post('/api/indicator/replay', params),
  
  // Статистика
  getStats: () => api.get('/api/indicator/stats'),
  
  // Экспорт результатов
  export: (params) => api.post('/api/indicator/export', params, { responseType: 'blob' }),
  
  // Доступные символы для индикатора
  getSymbols: () => api.get('/api/indicator/symbols'),
};

// ============================================
// Backtest API - История бэктестов
// ============================================
export const backtestApi = {
  run: (params) => api.post('/api/indicator/backtest', params),
  getResults: (id) => api.get(`/api/backtest/${id}`),
  getHistory: (params) => api.get('/api/backtest/history', { params }),
  delete: (id) => api.delete(`/api/backtest/${id}`),
};

// ============================================
// Signals API - Торговые сигналы
// ============================================
export const signalsApi = {
  // Список сигналов с фильтрацией
  getAll: (params) => api.get('/api/signals/', { params }),
  
  // Детали сигнала
  get: (id) => api.get(`/api/signals/${id}`),
  
  // Создать сигнал
  create: (data) => api.post('/api/signals/', data),
  
  // Обновить сигнал
  update: (id, data) => api.put(`/api/signals/${id}`, data),
  
  // Удалить сигнал
  delete: (id) => api.delete(`/api/signals/${id}`),
  
  // Закрыть сигнал
  close: (id, data = {}) => api.post(`/api/signals/${id}/close`, data),
  
  // Активные сигналы
  getActive: () => api.get('/api/signals/active'),
  
  // История сигналов
  getHistory: (params) => api.get('/api/signals/history', { params }),
  
  // Batch операции
  batch: (data) => api.post('/api/signals/batch', data),
  
  // Статистика сигналов
  getStats: () => api.get('/api/signals/stats'),
  
  // Экспорт
  export: (params) => api.post('/api/signals/export', params, { responseType: 'blob' }),
  
  // SSE стрим уведомлений (возвращает EventSource)
  streamSSE: () => new EventSource(`${API_BASE}/api/signals/sse/stream`),
  
  // Список символов с сигналами
  getSymbols: () => api.get('/api/signals/symbols'),
};

// ============================================
// Presets API - Пресеты настроек
// ============================================
export const presetsApi = {
  getAll: () => api.get('/api/db/presets'),
  get: (id) => api.get(`/api/db/presets/${id}`),
  create: (data) => api.post('/api/db/presets', data),
  update: (id, data) => api.put(`/api/db/presets/${id}`, data),
  delete: (id) => api.delete(`/api/db/presets/${id}`),
  duplicate: (id) => api.post(`/api/db/presets/${id}/duplicate`),
};

// ============================================
// Settings API - Системные настройки
// ============================================
export const settingsApi = {
  // Общие настройки
  getAll: () => api.get('/api/db/settings'),
  save: (data) => api.post('/api/db/settings', data),
  
  // API ключи
  getApiKeys: () => api.get('/api/settings/api-keys'),
  saveApiKey: (exchange, data) => api.post(`/api/settings/api-keys/${exchange}`, data),
  testConnection: (exchange) => api.post(`/api/settings/api-keys/${exchange}/test`),
  
  // Уведомления
  getNotifications: () => api.get('/api/settings/notifications'),
  saveNotifications: (data) => api.post('/api/settings/notifications', data),
  testNotification: (type) => api.post(`/api/settings/notifications/${type}/test`),
  
  // Системные настройки
  getSystem: () => api.get('/api/settings/system'),
  saveSystem: (data) => api.post('/api/settings/system', data),
  getSystemInfo: () => api.get('/api/settings/system/info'),
  clearCache: () => api.post('/api/settings/system/clear-cache'),
  
  // Настройки календаря
  getCalendarSettings: () => api.get('/api/settings/calendar'),
  saveCalendarSettings: (data) => api.post('/api/settings/calendar', data),
};

// ============================================
// Calendar API - Экономический календарь
// ============================================
export const calendarApi = {
  // События
  getEvents: (params) => api.get('/api/calendar/events', { params }),
  
  // Важные события сегодня
  getHighImpactToday: () => api.get('/api/calendar/high-impact-today'),
  
  // Обновить календарь
  refresh: () => api.post('/api/calendar/refresh'),
  
  // Статус блокировки торговли
  getBlockStatus: () => api.get('/api/calendar/block-status'),
};

// ============================================
// Trades API - Сделки
// ============================================
export const tradesApi = {
  getTrades: (params) => api.get('/api/trades', { params }),
  getStats: () => api.get('/api/trades/stats'),
  getMonthly: () => api.get('/api/trades/monthly'),
  export: (params) => api.post('/api/trades/export', params, { responseType: 'blob' }),
};

// ============================================
// Performance API - Производительность
// ============================================
export const performanceApi = {
  getSummary: () => api.get('/api/performance/summary'),
  getMonthly: () => api.get('/api/performance/monthly'),
  getEquity: () => api.get('/api/performance/equity'),
  getDrawdown: () => api.get('/api/performance/drawdown'),
};

// ============================================
// Plugins API - Управление плагинами
// ============================================
export const pluginsApi = {
  getAll: () => api.get('/api/plugins/'),
  get: (id) => api.get(`/api/plugins/${id}`),
  getParameters: (id) => api.get(`/api/plugins/${id}/parameters`),
  getUISchema: (id) => api.get(`/api/plugins/${id}/ui-schema`),
  reload: () => api.post('/api/plugins/reload'),
};

// ============================================
// WebSocket API - Real-time данные
// ============================================
export const wsApi = {
  getStatus: () => api.get('/api/ws/status'),
  connect: () => api.post('/api/ws/connect'),
  disconnect: () => api.post('/api/ws/disconnect'),
  subscribe: (params) => api.post('/api/ws/subscribe', params),
  unsubscribe: (params) => api.post('/api/ws/unsubscribe', params),
  getPrices: () => api.get('/api/ws/prices'),
  
  // SSE стримы
  streamPrices: () => new EventSource(`${API_BASE}/api/ws/sse/prices`),
  streamKlines: (symbol, timeframe) => 
    new EventSource(`${API_BASE}/api/ws/sse/klines?symbol=${symbol}&timeframe=${timeframe}`),
};

// ============================================
// Database API - База данных
// ============================================
export const databaseApi = {
  getInfo: () => api.get('/api/db/info'),
  backup: () => api.post('/api/db/backup'),
  restore: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/api/db/restore', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  optimize: () => api.post('/api/db/optimize'),
};

// ============================================
// Health & Info
// ============================================
export const healthApi = {
  check: () => api.get('/health'),
  info: () => api.get('/api/info'),
  version: () => api.get('/api/version'),
};

export default api;
