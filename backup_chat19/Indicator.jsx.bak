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
  // Data period
  start_date: null,
  end_date: null,
  // TRG
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

const Indicator = () => {
  // State
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('chart');
  
  // Data range from last calculation
  const [dataRange, setDataRange] = useState(null);
  
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
    addLog(`✅ Лучшие параметры применены`, 'success');
  };

  // Filtered symbols
  const filteredSymbols = ALL_SYMBOLS.filter(s => 
    s.toLowerCase().includes(symbolSearch.toLowerCase())
  );

  const selectSymbol = (symbol) => {
    updateSetting('symbol', symbol);
    setShowSymbolDropdown(false);
    setSymbolSearch('');
    // Reset data range when symbol changes
    setDataRange(null);
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
      height: chartContainerRef.current.clientHeight,
      layout: { background: { color: '#1f2937' }, textColor: '#9ca3af' },
      grid: { vertLines: { color: '#374151' }, horzLines: { color: '#374151' } },
      crosshair: { mode: 1 },
      rightPriceScale: { borderColor: '#374151' },
      timeScale: { borderColor: '#374151', timeVisible: true },
    });

    // Candles
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e', downColor: '#ef4444',
      borderUpColor: '#22c55e', borderDownColor: '#ef4444',
      wickUpColor: '#22c55e', wickDownColor: '#ef4444',
    });
    candleSeries.setData(data.candles || []);

    // TRG Lines
    if (data.indicators?.trg_upper) {
      const upperSeries = chart.addLineSeries({ color: '#22c55e', lineWidth: 1, lineStyle: 2 });
      upperSeries.setData(data.indicators.trg_upper);
    }
    if (data.indicators?.trg_lower) {
      const lowerSeries = chart.addLineSeries({ color: '#ef4444', lineWidth: 1, lineStyle: 2 });
      lowerSeries.setData(data.indicators.trg_lower);
    }

    // Trade markers
    if (data.trade_markers?.length) {
      const markers = data.trade_markers.map(m => ({
        time: m.time,
        position: m.type === 'entry_long' || m.type === 'entry_short' ? 'belowBar' : 'aboveBar',
        color: m.type.includes('long') ? '#22c55e' : '#ef4444',
        shape: m.type.includes('entry') ? 'arrowUp' : 'arrowDown',
        text: m.type.includes('entry') ? (m.type.includes('long') ? 'L' : 'S') : '',
      }));
      candleSeries.setMarkers(markers);
    }

    chartRef.current = chart;
    chart.timeScale().fitContent();

    // Equity chart
    if (equityChartRef.current && data.equity_curve?.length) {
      if (equityChartInstanceRef.current) {
        equityChartInstanceRef.current.remove();
      }

      const eqChart = createChart(equityChartRef.current, {
        width: equityChartRef.current.clientWidth,
        height: 100,
        layout: { background: { color: '#1f2937' }, textColor: '#9ca3af' },
        grid: { vertLines: { visible: false }, horzLines: { color: '#374151' } },
        rightPriceScale: { borderColor: '#374151' },
        timeScale: { visible: false },
      });

      const eqSeries = eqChart.addAreaSeries({
        lineColor: '#8b5cf6',
        topColor: 'rgba(139, 92, 246, 0.4)',
        bottomColor: 'rgba(139, 92, 246, 0.0)',
        lineWidth: 2,
      });
      eqSeries.setData(data.equity_curve.map(e => ({ time: e.time, value: e.value })));

      equityChartInstanceRef.current = eqChart;
      eqChart.timeScale().fitContent();
    }
  }, []);

  // Main calculate
  const calculate = async () => {
    setLoading(true);
    
    // Show period info in log if dates are set
    let periodInfo = '';
    if (settings.start_date || settings.end_date) {
      periodInfo = ` [${settings.start_date || '...'} — ${settings.end_date || '...'}]`;
    }
    addLog(`🚀 Запуск ${settings.symbol} ${settings.timeframe}${periodInfo}...`, 'info');
    
    try {
      const res = await fetch('/api/indicator/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      
      let data;
      try {
        data = await res.json();
      } catch (parseError) {
        addLog(`❌ Ошибка парсинга ответа: ${parseError.message}`, 'error');
        return;
      }
      
      if (!res.ok) {
        const errorMsg = String(data?.detail || data?.error || 'Ошибка сервера');
        addLog(`❌ Ошибка: ${errorMsg}`, 'error');
        
        if (errorMsg.includes('не найдены') || errorMsg.includes('not found')) {
          addLog(`⏳ Автозагрузка данных с Binance...`, 'warning');
          await new Promise(r => setTimeout(r, 3000));
          addLog(`🔄 Повторная попытка...`, 'info');
          
          const retry = await fetch('/api/indicator/calculate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
          });
          
          let retryData;
          try {
            retryData = await retry.json();
          } catch (parseError) {
            addLog(`❌ Ошибка парсинга повторного ответа`, 'error');
            return;
          }
          
          if (!retry.ok) {
            const retryError = String(retryData?.detail || retryData?.error || 'Ошибка повторной попытки');
            addLog(`❌ Повторная ошибка: ${retryError}`, 'error');
            return;
          }
          
          if (retryData?.success) {
            setResult(retryData);
            // Save data range
            if (retryData.data_range) {
              setDataRange(retryData.data_range);
            }
            if (activeTab === 'chart') renderChart(retryData);
            addLog(`✅ ${retryData.trades?.length || 0} сделок, ${retryData.stats?.win_rate || 0}% WR`, 'success');
          } else {
            addLog(`❌ Ошибка: ${String(retryData?.error || 'Неизвестная ошибка')}`, 'error');
          }
        }
        return;
      }
      
      if (!data?.success) {
        addLog(`❌ Ошибка: ${String(data?.error || data?.message || 'Расчёт не удался')}`, 'error');
        return;
      }
      
      // Success
      setResult(data);
      
      // Save data range from response
      if (data.data_range) {
        setDataRange(data.data_range);
        addLog(`📅 Период: ${data.data_range.used_start} — ${data.data_range.used_end} (${data.data_range.used_candles} свечей)`, 'info');
      }
      
      addLog(`✅ ${data.candles?.length || 0} свечей загружено`, 'success');
      addLog(`📊 ${data.trades?.length || 0} сделок`, 'success');
      
      const stats = data.stats;
      if (stats) {
        const profitPct = stats.profit_pct ?? stats.final_profit_pct ?? 0;
        addLog(`💰 Profit: ${profitPct >= 0 ? '+' : ''}${profitPct?.toFixed(2)}%, WR: ${stats.win_rate}%`, 'success');
      }
      
      if (activeTab === 'chart') renderChart(data);
      
    } catch (err) {
      addLog(`❌ Ошибка сети: ${err?.message || 'Неизвестная ошибка'}`, 'error');
      console.error('Calculate error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Heatmap
  const generateHeatmap = async (i1Range, i2Range) => {
    setLoadingHeatmap(true);
    addLog(`🔥 Генерация Heatmap...`, 'info');
    
    try {
      const res = await fetch('/api/indicator/heatmap', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...settings,
          i1_min: i1Range.min, i1_max: i1Range.max, i1_step: i1Range.step,
          i2_min: i2Range.min, i2_max: i2Range.max, i2_step: i2Range.step,
        })
      });
      
      let data;
      try {
        data = await res.json();
      } catch (parseError) {
        addLog(`❌ Heatmap ошибка парсинга ответа`, 'error');
        return;
      }
      
      if (!res.ok) {
        addLog(`❌ Heatmap ошибка: ${String(data?.detail || data?.error || 'Ошибка сервера')}`, 'error');
        return;
      }
      
      if (data?.success) {
        setHeatmapData(data);
        addLog(`✅ Heatmap готов`, 'success');
      } else {
        addLog(`❌ Heatmap ошибка: ${String(data?.error || 'Неизвестная ошибка')}`, 'error');
      }
    } catch (err) {
      addLog(`❌ Heatmap ошибка сети: ${err?.message || 'Неизвестная ошибка'}`, 'error');
      console.error('Heatmap error:', err);
    } finally {
      setLoadingHeatmap(false);
    }
  };

  // Export
  const exportCSV = () => {
    if (!result?.trades) return;
    const headers = ['#', 'Type', 'Entry Time', 'Exit Time', 'Entry Price', 'Exit Price', 'PnL %', 'Exit Reason'];
    const rows = result.trades.map((t, i) => [
      i + 1, t.type, t.entry_time, t.exit_time, t.entry_price, t.exit_price, t.pnl, t.exit_reason
    ]);
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `komas_${settings.symbol}_${settings.timeframe}_trades.csv`;
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
  
  // Reset data range when symbol/timeframe changes
  useEffect(() => {
    setDataRange(null);
  }, [settings.symbol, settings.timeframe]);

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
          
          {/* Period indicator */}
          {(settings.start_date || settings.end_date) && (
            <span className="text-xs text-purple-400 bg-purple-900/30 px-2 py-1 rounded">
              📅 {settings.start_date || '...'} — {settings.end_date || '...'}
            </span>
          )}
          
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
          dataRange={dataRange}
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
              <StatsPanel statistics={result?.stats} tpCount={settings.tp_count} dataRange={dataRange} />
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
