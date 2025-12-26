/**
 * KOMAS Trading Server - API Client
 * =================================
 * Централизованный API клиент с поддержкой SSE streaming
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
// ============================================
export const dataApi = {
  // Получить список доступных символов
  getSymbols: () => api.get('/data/symbols'),
  
  // Получить список таймфреймов
  getTimeframes: () => api.get('/data/timeframes'),
  
  // Скачать данные с биржи
  download: (params) => api.post('/data/download', params),
  
  // Информация о загруженных данных
  getInfo: (symbol, timeframe) => api.get(`/data/info/${symbol}/${timeframe}`),
  
  // Статус всех данных
  getStatus: () => api.get('/data/status'),
  
  // Удалить данные
  delete: (symbol, timeframe) => api.delete(`/data/${symbol}/${timeframe}`),
  
  // Получить свечи для графика
  getCandles: (symbol, timeframe, limit = 500) => 
    api.get(`/data/candles/${symbol}/${timeframe}`, { params: { limit } }),
};

// ============================================
// INDICATOR API - Расчёты и оптимизация
// ============================================
export const indicatorApi = {
  // Основной расчёт индикатора + бэктест
  calculate: (params) => api.post('/indicator/calculate', params),
  
  // Только расчёт индикатора (без бэктеста)
  calculateIndicator: (params) => api.post('/indicator/calculate-indicator', params),
  
  // Бэктест с готовыми данными индикатора
  backtest: (params) => api.post('/indicator/backtest', params),
  
  // Получить UI-схему для динамической генерации формы
  getUISchema: () => api.get('/indicator/ui-schema'),
  
  // Replay mode - пошаговое воспроизведение
  replay: (params) => api.post('/indicator/replay', params),
  
  // Heatmap - тепловая карта i1/i2
  heatmap: (params) => api.post('/indicator/heatmap', params),
  
  // Автооптимизация (SSE streaming)
  autoOptimizeStream: (params, onMessage, onError, onComplete) => {
    const eventSource = new EventSource(
      `/api/indicator/auto-optimize-stream?${new URLSearchParams({
        mode: params.mode,
        metric: params.metric || 'advanced',
        full_mode_depth: params.full_mode_depth || 'medium',
        symbol: params.settings?.symbol || 'BTCUSDT',
        timeframe: params.settings?.timeframe || '1h',
      })}`
    );
    
    // POST параметры через отдельный запрос (для SSE нужен GET)
    // Альтернатива: использовать fetch с ReadableStream
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
        
        if (data.type === 'done' || data.type === 'error') {
          eventSource.close();
          if (data.type === 'done' && onComplete) onComplete(data);
        }
      } catch (e) {
        console.error('SSE parse error:', e);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      eventSource.close();
      if (onError) onError(error);
    };
    
    return eventSource;
  },
  
  // Автооптимизация через fetch (для POST запросов)
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
// ============================================
export const presetsApi = {
  // Получить все пресеты
  getAll: () => api.get('/indicator/presets'),
  
  // Получить пресет по ID
  get: (id) => api.get(`/indicator/presets/${id}`),
  
  // Сохранить пресет
  save: (params) => api.post('/indicator/presets', params),
  
  // Обновить пресет
  update: (id, params) => api.put(`/indicator/presets/${id}`, params),
  
  // Удалить пресет
  delete: (id) => api.delete(`/indicator/presets/${id}`),
};

// ============================================
// SIGNALS API - Торговые сигналы
// ============================================
export const signalsApi = {
  // Получить сигналы с фильтрами
  getSignals: (params) => api.get('/signals', { params }),
  
  // Последние сигналы
  getLatest: (limit = 10) => api.get('/signals/latest', { params: { limit } }),
  
  // Активные сигналы
  getActive: () => api.get('/signals/active'),
  
  // Статистика сигналов
  getStats: () => api.get('/signals/stats'),
  
  // SSE подписка на новые сигналы
  subscribe: (onSignal, onError) => {
    const eventSource = new EventSource('/api/signals/stream');
    
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
// CALENDAR API - Экономический календарь
// ============================================
export const calendarApi = {
  // Получить события
  getEvents: (params) => api.get('/calendar/events', { params }),
  
  // Обновить календарь
  refresh: () => api.post('/calendar/refresh'),
  
  // Фильтры по важности
  getByImportance: (importance) => api.get('/calendar/events', { 
    params: { importance } 
  }),
};

// ============================================
// SETTINGS API - Настройки приложения
// ============================================
export const settingsApi = {
  // Получить все настройки
  getAll: () => api.get('/settings'),
  
  // Сохранить настройки
  save: (params) => api.post('/settings', params),
  
  // Сбросить к дефолтным
  reset: () => api.post('/settings/reset'),
  
  // Telegram настройки
  getTelegram: () => api.get('/settings/telegram'),
  saveTelegram: (params) => api.post('/settings/telegram', params),
  testTelegram: () => api.post('/settings/telegram/test'),
};

// ============================================
// DATABASE API - Управление БД
// ============================================
export const databaseApi = {
  // Статистика БД
  getStats: () => api.get('/database/stats'),
  
  // Очистка старых данных
  cleanup: (days = 30) => api.post('/database/cleanup', { days }),
  
  // Бэкап
  backup: () => api.post('/database/backup'),
  
  // Восстановление
  restore: (file) => api.post('/database/restore', { file }),
};

// ============================================
// PLUGINS API - Управление плагинами
// ============================================
export const pluginsApi = {
  // Список плагинов
  getAll: () => api.get('/plugins'),
  
  // Информация о плагине
  get: (name) => api.get(`/plugins/${name}`),
  
  // Включить/выключить
  toggle: (name, enabled) => api.post(`/plugins/${name}/toggle`, { enabled }),
  
  // Настройки плагина
  getConfig: (name) => api.get(`/plugins/${name}/config`),
  saveConfig: (name, config) => api.post(`/plugins/${name}/config`, config),
};

// ============================================
// PERFORMANCE API - Производительность
// ============================================
export const performanceApi = {
  // Сводка
  getSummary: () => api.get('/performance/summary'),
  
  // Помесячная статистика
  getMonthly: () => api.get('/performance/monthly'),
  
  // Equity curve
  getEquity: () => api.get('/performance/equity'),
  
  // По символам
  getBySymbol: () => api.get('/performance/by-symbol'),
  
  // По стратегиям
  getByStrategy: () => api.get('/performance/by-strategy'),
};

// ============================================
// WebSocket API - Realtime данные
// ============================================
export const wsApi = {
  // Подключение к WebSocket
  connect: (onMessage, onError, onClose) => {
    const ws = new WebSocket(`ws://${window.location.host}/ws`);
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (e) {
        console.error('WS parse error:', e);
      }
    };
    
    ws.onerror = (error) => {
      console.error('WS error:', error);
      if (onError) onError(error);
    };
    
    ws.onclose = () => {
      console.log('WS closed');
      if (onClose) onClose();
    };
    
    return ws;
  },
  
  // Подписка на символ
  subscribe: (ws, symbol, timeframe) => {
    ws.send(JSON.stringify({ 
      action: 'subscribe', 
      symbol, 
      timeframe 
    }));
  },
  
  // Отписка
  unsubscribe: (ws, symbol, timeframe) => {
    ws.send(JSON.stringify({ 
      action: 'unsubscribe', 
      symbol, 
      timeframe 
    }));
  },
};

export default api;
