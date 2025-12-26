/**
 * KOMAS Trading Server - API Client v3.5.1
 * =========================================
 * Централизованный API клиент с поддержкой SSE streaming
 * 
 * FIXED: Исправлены пути к API endpoints
 */
import axios from 'axios';

const API_BASE = '/api';

// Create axios instance with default config
export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 60000, // 60 секунд для длительных операций
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ============================================
// DATA API - Управление рыночными данными
// Prefix: /api/data
// ============================================
export const dataApi = {
  // Получить список доступных символов
  getSymbols: () => api.get('/data/symbols'),
  
  // Получить список загруженных файлов
  getAvailable: () => api.get('/data/available'),
  
  // Скачать данные с биржи
  download: (params) => api.post('/data/download', params),
  
  // Прогресс загрузки
  getDownloadProgress: () => api.get('/data/download/progress'),
  
  // Отменить загрузку
  cancelDownload: (taskId) => api.post(`/data/download/cancel/${taskId}`),
  
  // Синхронизация данных
  sync: (params) => api.post('/data/sync', params),
  
  // Удалить файл данных
  deleteFile: (filename) => api.delete(`/data/file/${filename}`),
  
  // Продолжить загрузку
  continue: (symbol, timeframe) => api.post(`/data/continue/${symbol}/${timeframe}`),
  
  // Debug информация
  debug: () => api.get('/data/debug'),
};

// ============================================
// INDICATOR API - Расчёты и оптимизация
// Prefix: /api/indicator
// ============================================
export const indicatorApi = {
  // Основной расчёт индикатора + бэктест
  calculate: (params) => api.post('/indicator/calculate', params),
  
  // Получить свечи для графика
  getCandles: (symbol, timeframe, limit = 500) => 
    api.get(`/indicator/candles/${symbol}/${timeframe}`, { params: { limit } }),
  
  // Replay mode - пошаговое воспроизведение
  replay: (params) => api.post('/indicator/replay', params),
  
  // Heatmap - тепловая карта i1/i2
  heatmap: (params) => api.post('/indicator/heatmap', params),
  
  // Автооптимизация
  autoOptimize: (params) => api.post('/indicator/auto-optimize', params),
  
  // Автооптимизация (SSE streaming) - использует fetch для POST
  autoOptimizeFetch: async (params, onMessage, onError, onComplete) => {
    try {
      const response = await fetch('/api/indicator/auto-optimize-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params),
      });
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              onMessage(data);
              
              if (data.type === 'done' && onComplete) {
                onComplete(data);
              }
            } catch (e) {
              console.error('Parse error:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Fetch error:', error);
      if (onError) onError(error);
    }
  },
};

// ============================================
// PRESETS API - Сохранённые настройки
// Prefix: /api/db (НЕ /api/indicator!)
// ============================================
export const presetsApi = {
  // Получить все пресеты
  getAll: () => api.get('/db/presets'),
  
  // Получить пресет по ID
  get: (id) => api.get(`/db/presets/${id}`),
  
  // Сохранить пресет
  save: (params) => api.post('/db/presets', params),
  
  // Обновить пресет
  update: (id, params) => api.put(`/db/presets/${id}`, params),
  
  // Удалить пресет
  delete: (id) => api.delete(`/db/presets/${id}`),
  
  // Добавить в избранное
  favorite: (id) => api.post(`/db/presets/${id}/favorite`),
  
  // Обновить статистику производительности
  updatePerformance: (id, stats) => api.put(`/db/presets/${id}/performance`, stats),
};

// ============================================
// SIGNALS API - Торговые сигналы
// Prefix: /api/signals
// ============================================
export const signalsApi = {
  // Получить сигналы с фильтрами
  getSignals: (params) => api.get('/signals', { params }),
  
  // Получить сигнал по ID
  getSignal: (id) => api.get(`/signals/${id}`),
  
  // Создать сигнал
  create: (params) => api.post('/signals', params),
  
  // Обновить сигнал
  update: (id, params) => api.put(`/signals/${id}`, params),
  
  // Удалить сигнал
  delete: (id) => api.delete(`/signals/${id}`),
  
  // Активные сигналы
  getActive: () => api.get('/signals/active'),
  
  // История сигналов
  getHistory: (params) => api.get('/signals/history', { params }),
  
  // Статистика сигналов
  getStats: () => api.get('/signals/stats'),
  
  // Экспорт сигналов
  export: (params) => api.post('/signals/export', params),
  
  // Batch операции
  batch: (params) => api.post('/signals/batch', params),
  
  // SSE подписка на новые сигналы
  subscribe: (onSignal, onError) => {
    const eventSource = new EventSource('/api/signals/sse/stream');
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onSignal(data);
      } catch (e) {
        console.error('Signal parse error:', e);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('Signal stream error:', error);
      if (onError) onError(error);
    };
    
    return eventSource;
  },
};

// ============================================
// SETTINGS API - Настройки приложения
// Prefix: /api/db (settings хранятся в БД)
// ============================================
export const settingsApi = {
  // Получить все настройки
  getAll: () => api.get('/db/settings'),
  
  // Получить настройку по ключу
  get: (key) => api.get(`/db/settings/${key}`),
  
  // Сохранить настройки
  save: (params) => api.post('/db/settings', params),
  
  // Удалить настройку
  delete: (key) => api.delete(`/db/settings/${key}`),
};

// ============================================
// DATABASE API - Управление БД и кэшем
// Prefix: /api/db
// ============================================
export const databaseApi = {
  // Информация о БД
  getInfo: () => api.get('/db/info'),
  
  // Кэш данных
  getCache: () => api.get('/db/cache'),
  
  // Информация о кэше символа
  getCacheInfo: (symbol, timeframe) => api.get(`/db/cache/${symbol}/${timeframe}`),
  
  // Очистить кэш символа
  clearCache: (symbol, timeframe) => api.delete(`/db/cache/${symbol}/${timeframe}`),
};

// ============================================
// PLUGINS API - Управление плагинами
// Prefix: /api/plugins
// ============================================
export const pluginsApi = {
  // Список плагинов
  getAll: () => api.get('/plugins'),
  
  // Информация о плагине
  get: (name) => api.get(`/plugins/${name}`),
  
  // UI Schema плагина
  getUISchema: (name) => api.get(`/plugins/${name}/ui-schema`),
  
  // Значения по умолчанию
  getDefaults: (name) => api.get(`/plugins/${name}/defaults`),
  
  // Валидация параметров
  validate: (name, params) => api.post(`/plugins/${name}/validate`, params),
};

// ============================================
// WEBSOCKET API - Realtime данные
// Prefix: /api/ws
// ============================================
export const wsApi = {
  // Статус подключения
  getStatus: () => api.get('/ws/status'),
  
  // Подключиться к WebSocket
  connect: () => api.post('/ws/connect'),
  
  // Отключиться
  disconnect: () => api.post('/ws/disconnect'),
  
  // Подписаться на стрим
  subscribe: (params) => api.post('/ws/subscribe', params),
  
  // Отписаться
  unsubscribe: (params) => api.post('/ws/unsubscribe', params),
  
  // Отписаться от всего
  unsubscribeAll: () => api.post('/ws/unsubscribe-all'),
  
  // Активные стримы
  getStreams: () => api.get('/ws/streams'),
  
  // Кэшированные цены
  getPrices: () => api.get('/ws/prices'),
  
  // SSE стрим цен
  subscribePrices: (onPrice, onError) => {
    const eventSource = new EventSource('/api/ws/sse/prices');
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onPrice(data);
      } catch (e) {
        console.error('Price parse error:', e);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('Price stream error:', error);
      if (onError) onError(error);
    };
    
    return eventSource;
  },
  
  // SSE стрим свечей
  subscribeKlines: (onKline, onError) => {
    const eventSource = new EventSource('/api/ws/sse/klines');
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onKline(data);
      } catch (e) {
        console.error('Kline parse error:', e);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('Kline stream error:', error);
      if (onError) onError(error);
    };
    
    return eventSource;
  },
};

// ============================================
// LOGS API - Логи сервера
// Endpoints в main.py
// ============================================
export const logsApi = {
  // Список лог-файлов
  list: () => api.get('/logs/list'),
  
  // Сегодняшний лог
  today: (lines = 100) => api.get('/logs/today', { params: { lines } }),
  
  // Логи ошибок
  errors: (lines = 50) => api.get('/logs/errors', { params: { lines } }),
  
  // Скачать лог-файл
  download: (filename) => api.get(`/logs/download/${filename}`, { responseType: 'blob' }),
  
  // Очистить старые логи
  clear: (days = 7) => api.get('/logs/clear', { params: { days } }),
};

// ============================================
// HEALTH API
// ============================================
export const healthApi = {
  check: () => api.get('/health'),
  info: () => api.get('/info'),
};

export default api;
