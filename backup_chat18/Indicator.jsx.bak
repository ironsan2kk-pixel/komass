import React, { useState, useRef, useEffect, useCallback } from 'react';
import { createChart } from 'lightweight-charts';
import {
  LogsPanel,
  SettingsSidebar,
  StatsPanel,
  MonthlyPanel,
  TradesTable,
  HeatmapPanel,
  AutoOptimizePanel
} from '../components/Indicator';

const TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d'];

const ALL_SYMBOLS = [
  "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
  "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
  "MATICUSDT", "LTCUSDT", "ATOMUSDT", "UNIUSDT", "NEARUSDT",
  "APTUSDT", "ARBUSDT", "OPUSDT", "SUIUSDT", "SEIUSDT",
  "TRXUSDT", "TONUSDT", "SHIBUSDT", "BCHUSDT", "XLMUSDT",
  "HBARUSDT", "FILUSDT", "ETCUSDT", "INJUSDT", "IMXUSDT",
  "RNDRUSDT", "GRTUSDT", "FTMUSDT", "AAVEUSDT", "MKRUSDT",
  "ALGOUSDT", "FLOWUSDT", "XTZUSDT", "SANDUSDT", "MANAUSDT",
  "AXSUSDT", "GALAUSDT", "THETAUSDT", "EOSUSDT", "IOTAUSDT",
  "NEOUSDT", "KLAYUSDT", "QNTUSDT", "CHZUSDT", "APEUSDT",
  "ZILUSDT", "CRVUSDT", "LRCUSDT", "ENJUSDT", "BATUSDT",
  "COMPUSDT", "SNXUSDT", "1INCHUSDT", "YFIUSDT", "SUSHIUSDT",
  "ZECUSDT", "DASHUSDT", "WAVESUSDT", "KAVAUSDT", "ANKRUSDT",
  "ICPUSDT", "RUNEUSDT", "STXUSDT", "MINAUSDT", "GMXUSDT",
  "LDOUSDT", "CFXUSDT", "FETUSDT", "OCEANUSDT", "VETUSDT",
  "DYDXUSDT", "WOOUSDT", "ARUSDT", "JASMYUSDT", "GMTUSDT",
  "PEPEUSDT", "FLOKIUSDT", "WIFUSDT", "ORDIUSDT", "JUPUSDT"
];

const DEFAULT_SETTINGS = {
  symbol: 'BTCUSDT',
  timeframe: '1h',
  trg_atr_length: 45,
  trg_multiplier: 4,
  tp_count: 4,
  tp1_percent: 1.05, tp2_percent: 1.95, tp3_percent: 3.75, tp4_percent: 6.0,
  tp5_percent: 8.0, tp6_percent: 10.0, tp7_percent: 12.0, tp8_percent: 15.0,
  tp9_percent: 18.0, tp10_percent: 20.0,
  tp1_amount: 50, tp2_amount: 30, tp3_amount: 15, tp4_amount: 5,
  tp5_amount: 0, tp6_amount: 0, tp7_amount: 0, tp8_amount: 0,
  tp9_amount: 0, tp10_amount: 0,
  sl_percent: 6.0,
  sl_trailing_mode: 'breakeven',
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
  allow_reentry: true,
  reentry_after_sl: true,
  reentry_after_tp: false,
  adaptive_mode: null,
  initial_capital: 10000,
  leverage: 1,
  use_commission: false,
  commission_percent: 0.1
};

// Helper: Convert time value to Unix timestamp in seconds
// Handles both numeric timestamps and ISO strings
const toUnixTime = (timeValue) => {
  if (typeof timeValue === 'number') {
    // Already Unix timestamp - check if seconds or milliseconds
    // If value is greater than year 3000 in seconds, assume it's milliseconds
    return timeValue > 32503680000 ? Math.floor(timeValue / 1000) : timeValue;
  }
  if (typeof timeValue === 'string') {
    return Math.floor(new Date(timeValue).getTime() / 1000);
  }
  return 0;
};

// Helper: Deduplicate and sort time series data
const deduplicateTimeSeries = (data, timeKey = 'time') => {
  const seen = new Set();
  const result = [];
  
  // Sort first
  const sorted = [...data].sort((a, b) => {
    const timeA = toUnixTime(a[timeKey]);
    const timeB = toUnixTime(b[timeKey]);
    return timeA - timeB;
  });
  
  for (const item of sorted) {
    const time = toUnixTime(item[timeKey]);
    if (!seen.has(time)) {
      seen.add(time);
      result.push({ ...item, [timeKey]: time });
    }
  }
  
  return result;
};

const Indicator = () => {
  // State
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('chart');
  
  // Sidebar & Logs
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [logsCollapsed, setLogsCollapsed] = useState(true);
  const [logs, setLogs] = useState([]);
  
  // Symbol search
  const [symbolSearch, setSymbolSearch] = useState('');
  const [showSymbolDropdown, setShowSymbolDropdown] = useState(false);
  
  // Heatmap
  const [heatmapData, setHeatmapData] = useState(null);
  const [loadingHeatmap, setLoadingHeatmap] = useState(false);

  // Chart refs
  const chartContainerRef = useRef(null);
  const equityChartRef = useRef(null);
  const chartRef = useRef(null);
  const equityChartInstanceRef = useRef(null);

  // Logging
  const addLog = useCallback((message, type = 'info') => {
    setLogs(prev => [...prev, { timestamp: Date.now(), message, type }].slice(-100));
  }, []);

  const clearLogs = useCallback(() => setLogs([]), []);

  // Update settings
  const updateSetting = (key, value) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  // Apply params from optimization
  const applyParams = (params) => {
    const mapped = {};
    if (params.i1 !== undefined) mapped.trg_atr_length = params.i1;
    if (params.i2 !== undefined) mapped.trg_multiplier = params.i2;
    if (params.tp1 !== undefined) mapped.tp1_percent = params.tp1;
    if (params.tp2 !== undefined) mapped.tp2_percent = params.tp2;
    if (params.tp3 !== undefined) mapped.tp3_percent = params.tp3;
    if (params.tp4 !== undefined) mapped.tp4_percent = params.tp4;
    if (params.sl !== undefined) mapped.sl_percent = params.sl;
    if (params.sl_mode !== undefined) mapped.sl_trailing_mode = params.sl_mode;
    if (params.use_st !== undefined) mapped.use_supertrend = params.use_st;
    if (params.st_period !== undefined) mapped.supertrend_period = params.st_period;
    if (params.st_mult !== undefined) mapped.supertrend_multiplier = params.st_mult;
    if (params.use_rsi !== undefined) mapped.use_rsi_filter = params.use_rsi;
    if (params.use_adx !== undefined) mapped.use_adx_filter = params.use_adx;
    if (params.allow_reentry !== undefined) mapped.allow_reentry = params.allow_reentry;
    
    setSettings(prev => ({ ...prev, ...mapped }));
    addLog('✅ Лучшие параметры применены', 'success');
  };

  // Filtered symbols
  const filteredSymbols = ALL_SYMBOLS.filter(s => 
    s.toLowerCase().includes(symbolSearch.toLowerCase())
  );

  const selectSymbol = (symbol) => {
    updateSetting('symbol', symbol);
    setShowSymbolDropdown(false);
    setSymbolSearch('');
    addLog(`Выбрана пара: ${symbol}`, 'info');
  };

  // Render charts
  const renderChart = useCallback((data) => {
    if (!chartContainerRef.current || !data) return;

    // Clear previous
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: chartContainerRef.current.clientHeight || 400,
      layout: {
        background: { type: 'solid', color: '#1a1a2e' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
      },
      crosshair: { mode: 0 },
      rightPriceScale: { borderColor: '#2B2B43' },
      timeScale: { borderColor: '#2B2B43', timeVisible: true },
    });

    chartRef.current = chart;

    // Candlesticks
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderDownColor: '#ef5350',
      borderUpColor: '#26a69a',
      wickDownColor: '#ef5350',
      wickUpColor: '#26a69a',
    });

    if (data.candles?.length > 0) {
      // Process candles with proper time handling and deduplication
      const candles = deduplicateTimeSeries(
        data.candles.map(c => ({
          time: toUnixTime(c.timestamp || c.time),
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }))
      );
      candleSeries.setData(candles);
    }

    // TRG line
    if (data.indicators?.trg_line) {
      const trgSeries = chart.addLineSeries({
        color: '#9c27b0',
        lineWidth: 2,
        title: 'TRG',
      });
      const trgData = deduplicateTimeSeries(
        data.indicators.trg_line
          .filter(d => d.value !== null && d.value !== undefined)
          .map(d => ({
            time: toUnixTime(d.timestamp || d.time),
            value: d.value,
          }))
      );
      if (trgData.length > 0) trgSeries.setData(trgData);
    }

    // Trade markers
    if (data.trade_markers?.length > 0) {
      const markers = data.trade_markers.map(m => ({
        time: toUnixTime(m.time),
        position: m.position === 'below' ? 'belowBar' : m.position,
        color: m.color || (m.type === 'entry' ? '#2196F3' : m.type === 'tp' ? '#4CAF50' : '#f44336'),
        shape: m.shape || (m.type === 'entry' ? 'arrowUp' : m.type === 'tp' ? 'circle' : 'arrowDown'),
        text: m.text || m.type,
      }));
      
      // Sort markers by time
      markers.sort((a, b) => a.time - b.time);
      candleSeries.setMarkers(markers);
    }

    chart.timeScale().fitContent();

    // Equity curve
    if (equityChartRef.current && data.equity_curve?.length > 0) {
      if (equityChartInstanceRef.current) {
        equityChartInstanceRef.current.remove();
      }

      const eqChart = createChart(equityChartRef.current, {
        width: equityChartRef.current.clientWidth,
        height: 100,
        layout: {
          background: { type: 'solid', color: '#1a1a2e' },
          textColor: '#d1d4dc',
        },
        grid: {
          vertLines: { color: '#2B2B43' },
          horzLines: { color: '#2B2B43' },
        },
        rightPriceScale: { borderColor: '#2B2B43' },
        timeScale: { visible: false },
      });

      equityChartInstanceRef.current = eqChart;

      const eqSeries = eqChart.addAreaSeries({
        lineColor: '#2196F3',
        topColor: 'rgba(33, 150, 243, 0.4)',
        bottomColor: 'rgba(33, 150, 243, 0.0)',
        lineWidth: 2,
      });

      const eqData = deduplicateTimeSeries(
        data.equity_curve.map(e => ({
          time: toUnixTime(e.time || e.timestamp),
          value: e.value || e.equity,
        }))
      );
      eqSeries.setData(eqData);
      eqChart.timeScale().fitContent();
    }
  }, []);

  // Main calculate
  const calculate = async () => {
    setLoading(true);
    addLog(`🚀 Запуск ${settings.symbol} ${settings.timeframe}...`, 'info');
    
    try {
      const res = await fetch('/api/indicator/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || `HTTP ${res.status}`);
      }
      
      const data = await res.json();
      
      if (data.success) {
        setResult(data);
        addLog(`✅ Готово! Сделок: ${data.trades?.length || 0}`, 'success');
        renderChart(data);
      } else {
        throw new Error(data.error || 'Unknown error');
      }
    } catch (err) {
      addLog(`❌ Ошибка: ${err.message}`, 'error');
      setLogsCollapsed(false);
    } finally {
      setLoading(false);
    }
  };

  // Generate heatmap
  const generateHeatmap = async () => {
    setLoadingHeatmap(true);
    addLog('🔥 Генерация heatmap...', 'info');
    
    try {
      const res = await fetch('/api/indicator/heatmap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      
      if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || `HTTP ${res.status}`);
      }
      
      const data = await res.json();
      setHeatmapData(data);
      addLog(`✅ Heatmap готов: ${data.results?.length || 0} комбинаций`, 'success');
    } catch (err) {
      addLog(`❌ Ошибка heatmap: ${err.message}`, 'error');
      setLogsCollapsed(false);
    } finally {
      setLoadingHeatmap(false);
    }
  };

  // Export functions
  const exportCSV = () => {
    if (!result?.trades) return;
    const headers = ['entry_time', 'exit_time', 'type', 'entry_price', 'exit_price', 'pnl', 'exit_reason'];
    const rows = result.trades.map(t => headers.map(h => t[h] ?? '').join(','));
    const csv = [headers.join(','), ...rows].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `komas_${settings.symbol}_${settings.timeframe}.csv`;
    a.click();
    addLog('📄 CSV экспортирован', 'success');
  };

  const exportJSON = () => {
    if (!result) return;
    const data = { settings, stats: result.stats, trades: result.trades };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `komas_${settings.symbol}_${settings.timeframe}.json`;
    a.click();
    addLog('📄 JSON экспортирован', 'success');
  };

  // Resize
  useEffect(() => {
    const handleResize = () => {
      if (chartRef.current && chartContainerRef.current) {
        chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
      if (equityChartInstanceRef.current && equityChartRef.current) {
        equityChartInstanceRef.current.applyOptions({ width: equityChartRef.current.clientWidth });
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Re-render chart on tab change
  useEffect(() => {
    if (activeTab === 'chart' && result) {
      setTimeout(() => renderChart(result), 100);
    }
  }, [activeTab, result, renderChart]);

  // Keyboard
  useEffect(() => {
    const handleKey = (e) => {
      if (e.key === 'Enter' && !loading) calculate();
    };
    window.addEventListener('keydown', handleKey);
    return () => window.removeEventListener('keydown', handleKey);
  }, [loading, settings]);

  const stats = result?.stats;
  const profitPct = stats?.profit_pct ?? stats?.final_profit_pct ?? 0;

  const TABS = [
    { key: 'chart', label: '📈 График' },
    { key: 'stats', label: '📊 Статистика' },
    { key: 'trades', label: '📋 Сделки' },
    { key: 'monthly', label: '📅 Месяцы' },
    { key: 'optimize', label: '🔥 Оптимизация' },
    { key: 'heatmap', label: '🗺️ Heatmap' },
  ];

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-3">
          <h1 className="text-lg font-bold text-white">🎯 Komas Indicator</h1>
          
          {/* Symbol */}
          <div className="relative">
            <button
              onClick={() => setShowSymbolDropdown(!showSymbolDropdown)}
              className="bg-gray-700 text-white rounded px-3 py-1.5 text-sm flex items-center gap-2 hover:bg-gray-600"
            >
              <span className="font-mono">{settings.symbol}</span>
              <span className="text-gray-400">▼</span>
            </button>
            
            {showSymbolDropdown && (
              <div className="absolute z-50 mt-1 w-56 bg-gray-800 border border-gray-700 rounded-lg shadow-xl">
                <input
                  type="text"
                  value={symbolSearch}
                  onChange={(e) => setSymbolSearch(e.target.value)}
                  placeholder="Поиск..."
                  className="w-full bg-gray-700 text-white px-3 py-2 text-sm rounded-t-lg border-b border-gray-600"
                  autoFocus
                />
                <div className="max-h-48 overflow-y-auto">
                  {filteredSymbols.map(symbol => (
                    <button
                      key={symbol}
                      onClick={() => selectSymbol(symbol)}
                      className={`w-full text-left px-3 py-1.5 text-sm hover:bg-gray-700 ${
                        settings.symbol === symbol ? 'bg-purple-600 text-white' : 'text-gray-300'
                      }`}
                    >
                      {symbol}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
          
          {/* Timeframe */}
          <select
            value={settings.timeframe}
            onChange={(e) => updateSetting('timeframe', e.target.value)}
            className="bg-gray-700 text-white rounded px-2 py-1.5 text-sm"
          >
            {TIMEFRAMES.map(tf => <option key={tf} value={tf}>{tf}</option>)}
          </select>
          
          {/* Run */}
          <button
            onClick={calculate}
            disabled={loading}
            className={`px-4 py-1.5 rounded text-sm font-bold ${
              loading ? 'bg-gray-600 text-gray-400' : 'bg-purple-600 hover:bg-purple-500 text-white'
            }`}
          >
            {loading ? '⏳...' : '▶️ Запустить'}
          </button>
        </div>
        
        {/* Stats & Export */}
        <div className="flex items-center gap-2">
          {stats && (
            <div className="flex items-center gap-3 mr-4 text-sm">
              <span className={profitPct >= 0 ? 'text-green-400' : 'text-red-400'}>
                {profitPct >= 0 ? '+' : ''}{profitPct?.toFixed(2)}%
              </span>
              <span className="text-gray-500">|</span>
              <span className="text-blue-400">{stats.win_rate}% WR</span>
              <span className="text-gray-500">|</span>
              <span className="text-gray-300">{stats.total_trades} trades</span>
            </div>
          )}
          <button onClick={exportCSV} className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded hover:bg-gray-600">CSV</button>
          <button onClick={exportJSON} className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded hover:bg-gray-600">JSON</button>
        </div>
      </div>

      {/* Main */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar */}
        <SettingsSidebar
          settings={settings}
          onUpdate={updateSetting}
          collapsed={sidebarCollapsed}
          onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* Content */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tabs */}
          <div className="flex items-center gap-1 px-4 py-2 bg-gray-800 border-b border-gray-700">
            {TABS.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-3 py-1.5 text-xs rounded font-medium transition-colors ${
                  activeTab === tab.key
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="flex-1 overflow-auto">
            {activeTab === 'chart' && (
              <div className="p-4 space-y-2 h-full flex flex-col">
                <div ref={chartContainerRef} className="flex-1 bg-gray-800 rounded-lg min-h-[400px]" />
                <div ref={equityChartRef} className="h-[100px] bg-gray-800 rounded-lg" />
              </div>
            )}

            {activeTab === 'stats' && (
              <StatsPanel statistics={result?.stats} tpCount={settings.tp_count} />
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
                onApplyBest={applyParams}
                addLog={addLog}
              />
            )}

            {activeTab === 'heatmap' && (
              <HeatmapPanel
                data={heatmapData}
                loading={loadingHeatmap}
                onGenerate={generateHeatmap}
              />
            )}
          </div>
        </div>
      </div>

      {/* Logs */}
      <LogsPanel
        logs={logs}
        onClear={clearLogs}
        collapsed={logsCollapsed}
        onToggle={() => setLogsCollapsed(!logsCollapsed)}
      />
    </div>
  );
};

export default Indicator;
