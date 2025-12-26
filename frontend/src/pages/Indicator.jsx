/**
 * KOMAS Trading Server - Indicator Page
 * ======================================
 * Главная страница с 6 вкладками:
 * 1. График - свечной график + equity
 * 2. Статистика - метрики и accuracy
 * 3. Сделки - таблица с фильтрами
 * 4. Месяцы - помесячная разбивка
 * 5. Оптимизация - автооптимизация с SSE
 * 6. Heatmap - тепловая карта i1/i2
 */
import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { createChart } from 'lightweight-charts';
import { indicatorApi, dataApi, presetsApi } from '../api';
import {
  SettingsSidebar,
  StatsPanel,
  TradesTable,
  MonthlyPanel,
  HeatmapPanel,
  AutoOptimizePanel,
  LogsPanel,
} from '../components/Indicator';

// ============================================
// CONSTANTS
// ============================================
const TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d'];

const SYMBOLS = [
  "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
  "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
  "LTCUSDT", "ATOMUSDT", "UNIUSDT", "NEARUSDT", "APTUSDT",
  "ARBUSDT", "OPUSDT", "SUIUSDT", "SEIUSDT", "PEPEUSDT",
  "MATICUSDT", "FTMUSDT", "SANDUSDT", "MANAUSDT", "AXSUSDT",
  "AAVEUSDT", "MKRUSDT", "COMPUSDT", "SNXUSDT", "CRVUSDT",
  "LDOUSDT", "RNDRUSDT", "FETUSDT", "OCEANUSDT", "AGIXUSDT",
  "INJUSDT", "TIAUSDT", "JUPUSDT", "WIFUSDT", "BONKUSDT",
];

const TABS = [
  { id: 'chart', name: '📈 График', icon: '📈' },
  { id: 'stats', name: '📊 Статистика', icon: '📊' },
  { id: 'trades', name: '📋 Сделки', icon: '📋' },
  { id: 'monthly', name: '📅 Месяцы', icon: '📅' },
  { id: 'optimize', name: '🔥 Оптимизация', icon: '🔥' },
  { id: 'heatmap', name: '🗺️ Heatmap', icon: '🗺️' },
];

// Helper: Convert time to Unix timestamp (seconds)
// lightweight-charts requires time as Unix timestamp in seconds
const toTimestamp = (time) => {
  if (!time) return 0;
  // Already a number (timestamp)
  if (typeof time === 'number') {
    // If milliseconds, convert to seconds
    return time > 9999999999 ? Math.floor(time / 1000) : time;
  }
  // ISO string or other string format
  if (typeof time === 'string') {
    const date = new Date(time);
    return Math.floor(date.getTime() / 1000);
  }
  return 0;
};

const DEFAULT_SETTINGS = {
  symbol: 'BTCUSDT',
  timeframe: '1h',
  // TRG Indicator
  trg_atr_length: 45,
  trg_multiplier: 4,
  // Take Profits (1-10)
  tp_count: 4,
  tp1_percent: 1.05, tp1_amount: 50,
  tp2_percent: 1.95, tp2_amount: 30,
  tp3_percent: 3.75, tp3_amount: 15,
  tp4_percent: 6.0, tp4_amount: 5,
  tp5_percent: 8.0, tp5_amount: 0,
  tp6_percent: 10.0, tp6_amount: 0,
  tp7_percent: 12.0, tp7_amount: 0,
  tp8_percent: 15.0, tp8_amount: 0,
  tp9_percent: 18.0, tp9_amount: 0,
  tp10_percent: 20.0, tp10_amount: 0,
  // Stop Loss
  sl_percent: 6.0,
  sl_trailing_mode: 'breakeven', // 'fixed', 'breakeven', 'cascade'
  // Filters
  use_supertrend: false,
  supertrend_period: 10,
  supertrend_multiplier: 3.0,
  use_rsi_filter: false,
  rsi_period: 14,
  rsi_overbought: 70,
  rsi_oversold: 30,
  use_adx_filter: false,
  adx_period: 14,
  adx_threshold: 25,
  use_volume_filter: false,
  // Re-entry
  allow_reentry: true,
  reentry_after_sl: true,
  reentry_after_tp: false,
  // Capital & Risk
  initial_capital: 10000,
  leverage: 1,
  use_commission: false,
  commission_percent: 0.1,
  // Adaptive
  adaptive_mode: null, // null, 'indicator', 'tp', 'all'
};

// ============================================
// MAIN COMPONENT
// ============================================
export default function Indicator() {
  // Settings state
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  
  // UI state
  const [activeTab, setActiveTab] = useState('chart');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [symbolSearch, setSymbolSearch] = useState('');
  const [showSymbolDropdown, setShowSymbolDropdown] = useState(false);
  
  // Results state
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // Logs state
  const [logs, setLogs] = useState([]);
  const [logsExpanded, setLogsExpanded] = useState(false);
  
  // Presets state
  const [presets, setPresets] = useState([]);
  const [selectedPreset, setSelectedPreset] = useState(null);
  
  // Chart refs
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const equitySeriesRef = useRef(null);

  // ============================================
  // LOGGING
  // ============================================
  const addLog = useCallback((message, type = 'info') => {
    const log = {
      id: Date.now(),
      time: new Date().toLocaleTimeString('ru-RU'),
      message,
      type, // info, success, error, warning, optimize
    };
    setLogs(prev => [...prev.slice(-100), log]);
    
    // Auto-expand on error
    if (type === 'error') {
      setLogsExpanded(true);
    }
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  // ============================================
  // SETTINGS HANDLERS
  // ============================================
  const updateSetting = useCallback((key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  }, []);

  const updateSettings = useCallback((updates) => {
    setSettings(prev => ({ ...prev, ...updates }));
  }, []);

  const resetSettings = useCallback(() => {
    setSettings(DEFAULT_SETTINGS);
    addLog('Настройки сброшены к значениям по умолчанию', 'info');
  }, [addLog]);

  // ============================================
  // PRESETS
  // ============================================
  const loadPresets = useCallback(async () => {
    try {
      const res = await presetsApi.getAll();
      // API returns array directly, not {presets: [...]}
      setPresets(Array.isArray(res.data) ? res.data : res.data?.presets || []);
    } catch (err) {
      // Silently fail - presets endpoint may not exist yet
      // console.error('Failed to load presets:', err);
    }
  }, []);

  const savePreset = useCallback(async (name) => {
    try {
      await presetsApi.save({ name, settings });
      addLog(`Пресет "${name}" сохранён`, 'success');
      loadPresets();
    } catch (err) {
      addLog(`Ошибка сохранения пресета: ${err.message}`, 'error');
    }
  }, [settings, addLog, loadPresets]);

  const loadPreset = useCallback((preset) => {
    setSettings(prev => ({ ...prev, ...preset.settings }));
    setSelectedPreset(preset.id);
    addLog(`Загружен пресет: ${preset.name}`, 'info');
  }, [addLog]);

  useEffect(() => {
    loadPresets();
  }, [loadPresets]);

  // ============================================
  // CHART
  // ============================================
  useEffect(() => {
    if (!chartContainerRef.current) return;

    // Create chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: 'solid', color: 'transparent' },
        textColor: '#9ca3af',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
      },
      timeScale: {
        borderColor: 'rgba(255, 255, 255, 0.1)',
        timeVisible: true,
      },
    });

    // Candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: '#22c55e',
      wickDownColor: '#ef4444',
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    // Resize handler
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: chartContainerRef.current.clientHeight,
        });
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // Update chart data
  useEffect(() => {
    if (!candleSeriesRef.current || !result?.candles) return;

    const chartData = result.candles.map(c => ({
      time: toTimestamp(c.time),
      open: c.open,
      high: c.high,
      low: c.low,
      close: c.close,
    }));

    candleSeriesRef.current.setData(chartData);
    
    // Add markers for trades
    if (result.trades) {
      const markers = result.trades.flatMap(trade => {
        const marks = [];
        
        // Entry marker
        marks.push({
          time: toTimestamp(trade.entry_time),
          position: trade.type === 'long' ? 'belowBar' : 'aboveBar',
          color: trade.type === 'long' ? '#22c55e' : '#ef4444',
          shape: trade.type === 'long' ? 'arrowUp' : 'arrowDown',
          text: trade.type === 'long' ? 'L' : 'S',
        });
        
        // Exit marker
        if (trade.exit_time) {
          marks.push({
            time: toTimestamp(trade.exit_time),
            position: trade.type === 'long' ? 'aboveBar' : 'belowBar',
            color: trade.pnl >= 0 ? '#22c55e' : '#ef4444',
            shape: 'circle',
            text: `${trade.pnl >= 0 ? '+' : ''}${trade.pnl?.toFixed(1)}%`,
          });
        }
        
        return marks;
      });
      
      candleSeriesRef.current.setMarkers(markers);
    }

    // Fit content
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [result]);

  // ============================================
  // CALCULATE / BACKTEST
  // ============================================
  const runCalculation = useCallback(async () => {
    setLoading(true);
    setError(null);
    addLog(`Запуск расчёта ${settings.symbol} ${settings.timeframe}...`);

    try {
      const res = await indicatorApi.calculate(settings);
      
      if (res.data?.success) {
        setResult(res.data);
        const trades = res.data.stats?.total_trades || 0;
        const profit = res.data.stats?.profit_pct?.toFixed(2) || 0;
        addLog(`✅ Завершено: ${trades} сделок, ${profit}%`, 'success');
      } else {
        throw new Error(res.data?.detail || 'Неизвестная ошибка');
      }
    } catch (err) {
      const errorMsg = err.response?.data?.detail || err.message;
      
      // Handle missing data
      if (errorMsg.includes('не найдены') || errorMsg.includes('not found')) {
        addLog(`⏳ Данные не найдены. Скачиваю с Binance...`, 'warning');
        
        try {
          // Download data
          await dataApi.download({
            symbol: settings.symbol,
            timeframe: settings.timeframe,
            limit: 5000,
          });
          
          addLog(`🔄 Данные загружены, повторный расчёт...`, 'info');
          
          // Retry calculation
          const retryRes = await indicatorApi.calculate(settings);
          
          if (retryRes.data?.success) {
            setResult(retryRes.data);
            const trades = retryRes.data.stats?.total_trades || 0;
            const profit = retryRes.data.stats?.profit_pct?.toFixed(2) || 0;
            addLog(`✅ Завершено: ${trades} сделок, ${profit}%`, 'success');
          } else {
            throw new Error(retryRes.data?.detail || 'Ошибка после загрузки данных');
          }
        } catch (downloadErr) {
          addLog(`❌ Ошибка загрузки: ${downloadErr.message}`, 'error');
          setError(downloadErr.message);
        }
      } else {
        addLog(`❌ Ошибка: ${errorMsg}`, 'error');
        setError(errorMsg);
      }
    } finally {
      setLoading(false);
    }
  }, [settings, addLog]);

  // ============================================
  // KEYBOARD SHORTCUTS
  // ============================================
  useEffect(() => {
    const handleKeyDown = (e) => {
      // Enter to calculate
      if (e.key === 'Enter' && !e.shiftKey && !loading) {
        runCalculation();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [runCalculation, loading]);

  // ============================================
  // FILTERED SYMBOLS
  // ============================================
  const filteredSymbols = useMemo(() => {
    if (!symbolSearch) return SYMBOLS;
    const search = symbolSearch.toUpperCase();
    return SYMBOLS.filter(s => s.includes(search));
  }, [symbolSearch]);

  // ============================================
  // EXPORT
  // ============================================
  const exportResults = useCallback((format = 'json') => {
    if (!result) return;

    let content, filename, type;

    if (format === 'json') {
      content = JSON.stringify(result, null, 2);
      filename = `komas_${settings.symbol}_${settings.timeframe}_${Date.now()}.json`;
      type = 'application/json';
    } else {
      // CSV
      const headers = ['#', 'Type', 'Entry Time', 'Exit Time', 'Entry Price', 'Exit Price', 'PnL %', 'Exit Reason'];
      const rows = result.trades?.map((t, i) => [
        i + 1,
        t.type,
        t.entry_time,
        t.exit_time,
        t.entry_price,
        t.exit_price,
        t.pnl?.toFixed(2),
        t.exit_reason,
      ]) || [];
      
      content = [headers, ...rows].map(r => r.join(',')).join('\n');
      filename = `komas_trades_${settings.symbol}_${settings.timeframe}_${Date.now()}.csv`;
      type = 'text/csv';
    }

    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
    
    addLog(`Экспортировано в ${format.toUpperCase()}`, 'success');
  }, [result, settings, addLog]);

  // ============================================
  // APPLY HEATMAP PARAMS
  // ============================================
  const applyHeatmapParams = useCallback((params) => {
    setSettings(prev => ({
      ...prev,
      trg_atr_length: params.i1,
      trg_multiplier: params.i2,
    }));
    addLog(`Применены параметры: i1=${params.i1}, i2=${params.i2}`, 'info');
  }, [addLog]);

  // ============================================
  // RENDER
  // ============================================
  return (
    <div className="h-screen flex flex-col bg-gray-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Symbol Selector */}
            <div className="relative">
              <button
                onClick={() => setShowSymbolDropdown(!showSymbolDropdown)}
                className="flex items-center gap-2 bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg transition-colors"
              >
                <span className="font-bold text-lg">{settings.symbol}</span>
                <span className="text-gray-400">▼</span>
              </button>
              
              {showSymbolDropdown && (
                <div className="absolute top-full left-0 mt-1 bg-gray-800 border border-gray-700 rounded-lg shadow-xl z-50 w-64">
                  <input
                    type="text"
                    placeholder="Поиск..."
                    value={symbolSearch}
                    onChange={(e) => setSymbolSearch(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border-b border-gray-600 rounded-t-lg text-sm focus:outline-none"
                    autoFocus
                  />
                  <div className="max-h-64 overflow-y-auto">
                    {filteredSymbols.map(symbol => (
                      <button
                        key={symbol}
                        onClick={() => {
                          updateSetting('symbol', symbol);
                          setShowSymbolDropdown(false);
                          setSymbolSearch('');
                        }}
                        className={`w-full px-3 py-2 text-left hover:bg-gray-700 transition-colors ${
                          settings.symbol === symbol ? 'bg-blue-600' : ''
                        }`}
                      >
                        {symbol}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Timeframe Selector */}
            <div className="flex bg-gray-700 rounded-lg p-1">
              {TIMEFRAMES.map(tf => (
                <button
                  key={tf}
                  onClick={() => updateSetting('timeframe', tf)}
                  className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                    settings.timeframe === tf
                      ? 'bg-blue-600 text-white'
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {tf}
                </button>
              ))}
            </div>

            {/* Presets */}
            <select
              value={selectedPreset || ''}
              onChange={(e) => {
                const preset = presets.find(p => p.id === e.target.value);
                if (preset) loadPreset(preset);
              }}
              className="bg-gray-700 px-3 py-2 rounded-lg text-sm"
            >
              <option value="">Пресеты...</option>
              {presets.map(p => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-3">
            {/* Export */}
            <div className="flex gap-1">
              <button
                onClick={() => exportResults('csv')}
                disabled={!result}
                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm disabled:opacity-50 transition-colors"
              >
                CSV
              </button>
              <button
                onClick={() => exportResults('json')}
                disabled={!result}
                className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm disabled:opacity-50 transition-colors"
              >
                JSON
              </button>
            </div>

            {/* Calculate Button */}
            <button
              onClick={runCalculation}
              disabled={loading}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 px-6 py-2 rounded-lg font-medium transition-colors"
            >
              {loading ? (
                <>
                  <span className="animate-spin">⏳</span>
                  Расчёт...
                </>
              ) : (
                <>
                  <span>▶</span>
                  Рассчитать
                </>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Settings Sidebar */}
        <SettingsSidebar
          settings={settings}
          updateSetting={updateSetting}
          updateSettings={updateSettings}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          onReset={resetSettings}
          onSavePreset={savePreset}
        />

        {/* Content Area */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Quick Stats */}
          {result?.stats && (
            <div className="bg-gray-800 border-b border-gray-700 px-4 py-3">
              <div className="flex gap-4">
                <StatBadge 
                  label="Прибыль" 
                  value={`${result.stats.profit_pct?.toFixed(2)}%`}
                  color={result.stats.profit_pct >= 0 ? 'green' : 'red'}
                />
                <StatBadge 
                  label="Win Rate" 
                  value={`${result.stats.win_rate?.toFixed(1)}%`}
                  color="blue"
                />
                <StatBadge 
                  label="Сделок" 
                  value={result.stats.total_trades}
                  color="purple"
                />
                <StatBadge 
                  label="Просадка" 
                  value={`${result.stats.max_drawdown?.toFixed(1)}%`}
                  color="orange"
                />
                <StatBadge 
                  label="PF" 
                  value={result.stats.profit_factor?.toFixed(2)}
                  color="cyan"
                />
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="bg-gray-800 border-b border-gray-700 px-4">
            <div className="flex gap-1">
              {TABS.map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-white'
                      : 'border-transparent text-gray-400 hover:text-white'
                  }`}
                >
                  {tab.name}
                </button>
              ))}
            </div>
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-auto p-4">
            {activeTab === 'chart' && (
              <div className="h-full bg-gray-800/50 rounded-xl border border-gray-700">
                <div ref={chartContainerRef} className="w-full h-full" />
              </div>
            )}

            {activeTab === 'stats' && (
              <StatsPanel stats={result?.stats} accuracy={result?.accuracy} />
            )}

            {activeTab === 'trades' && (
              <TradesTable trades={result?.trades} />
            )}

            {activeTab === 'monthly' && (
              <MonthlyPanel monthly={result?.monthly} />
            )}

            {activeTab === 'optimize' && (
              <AutoOptimizePanel
                settings={settings}
                onApplyParams={updateSettings}
                addLog={addLog}
              />
            )}

            {activeTab === 'heatmap' && (
              <HeatmapPanel
                settings={settings}
                onApplyParams={applyHeatmapParams}
                addLog={addLog}
              />
            )}
          </div>
        </main>
      </div>

      {/* Logs Panel */}
      <LogsPanel
        logs={logs}
        expanded={logsExpanded}
        onToggle={() => setLogsExpanded(!logsExpanded)}
        onClear={clearLogs}
      />

      {/* Click outside to close symbol dropdown */}
      {showSymbolDropdown && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowSymbolDropdown(false)}
        />
      )}
    </div>
  );
}

// ============================================
// STAT BADGE COMPONENT
// ============================================
function StatBadge({ label, value, color }) {
  const colors = {
    green: 'text-green-400',
    red: 'text-red-400',
    blue: 'text-blue-400',
    purple: 'text-purple-400',
    orange: 'text-orange-400',
    cyan: 'text-cyan-400',
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-gray-500 text-sm">{label}:</span>
      <span className={`font-bold ${colors[color]}`}>{value}</span>
    </div>
  );
}
