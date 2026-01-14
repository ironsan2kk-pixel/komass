/**
 * Indicator.jsx
 * =============
 * Main indicator page with support for TRG and Dominant indicators.
 * 
 * Features:
 * - Indicator type selector (TRG / Dominant)
 * - Preset browser for Dominant presets
 * - Auto-fill parameters from selected preset
 * - "Modified" tracking for preset changes
 * - Dynamic parameter forms
 * - Trade levels visualization (TP/SL/Entry lines) - Chat #28
 * 
 * Chat #27: Dominant UI Integration
 * Chat #28: Trade levels visualization for all trades
 */

import React, { useState, useRef, useEffect, useCallback, useMemo } from 'react';
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
import { Button, Input, Badge } from '../components/ui';

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
  commission_percent: 0.1,
  // Dominant (new)
  dominant_sensitivity: 21,
  dominant_filter_type: 0,
  dominant_sl_mode: 0,
  dominant_tp1_percent: 1.0, dominant_tp2_percent: 2.0, 
  dominant_tp3_percent: 3.0, dominant_tp4_percent: 5.0,
  dominant_tp1_amount: 40, dominant_tp2_amount: 30, 
  dominant_tp3_amount: 20, dominant_tp4_amount: 10,
  dominant_sl_percent: 2.0,
  dominant_fixed_stop: false,  // Chat #28: If true, SL from entry; if false, SL from mid_channel
  // Chart options (Chat #28)
  show_trade_levels: true,  // Show TP/SL/Entry lines on chart
};

const Indicator = () => {
  // State
  const [settings, setSettings] = useState(DEFAULT_SETTINGS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('chart');
  
  // Indicator type state (NEW)
  const [indicatorType, setIndicatorType] = useState('trg');
  
  // Dominant presets state (NEW)
  const [dominantPresets, setDominantPresets] = useState([]);
  const [presetsLoading, setPresetsLoading] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState(null);
  const [presetOriginalParams, setPresetOriginalParams] = useState(null);
  
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
  
  // Cache
  const [cachedResult, setCachedResult] = useState(false);
  const [cacheStats, setCacheStats] = useState(null);

  // Chart refs
  const chartContainerRef = useRef(null);
  const equityChartRef = useRef(null);
  const chartRef = useRef(null);
  const equityChartInstanceRef = useRef(null);
  
  // Store line series refs for cleanup
  const tradeLevelSeriesRef = useRef([]);

  // Logging
  const addLog = useCallback((message, type = 'info') => {
    setLogs(prev => [...prev, { timestamp: Date.now(), message, type }].slice(-100));
  }, []);

  const clearLogs = useCallback(() => setLogs([]), []);

  // Cache functions
  const fetchCacheStats = useCallback(async () => {
    try {
      const res = await fetch('/api/indicator/cache-stats');
      const data = await res.json();
      if (data.success) setCacheStats(data);
    } catch (err) {
      console.error('Cache stats error:', err);
    }
  }, []);

  const clearCache = useCallback(async () => {
    try {
      const res = await fetch('/api/indicator/cache-clear', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        addLog('🗑️ Кэш очищен', 'success');
        fetchCacheStats();
      }
    } catch (err) {
      addLog(`❌ Ошибка очистки кэша: ${err.message}`, 'error');
    }
  }, [addLog, fetchCacheStats]);

  // Fetch cache stats periodically
  useEffect(() => {
    fetchCacheStats();
    const interval = setInterval(fetchCacheStats, 30000);
    return () => clearInterval(interval);
  }, [fetchCacheStats]);

  // ============ DOMINANT PRESETS LOADING (NEW) ============
  const fetchDominantPresets = useCallback(async () => {
    setPresetsLoading(true);
    try {
      const res = await fetch('/api/presets/dominant/list');
      const data = await res.json();
      if (data.presets) {
        setDominantPresets(data.presets);
        addLog(`📦 Загружено ${data.presets.length} пресетов Dominant`, 'info');
      } else if (Array.isArray(data)) {
        setDominantPresets(data);
        addLog(`📦 Загружено ${data.length} пресетов Dominant`, 'info');
      }
    } catch (err) {
      addLog(`❌ Ошибка загрузки пресетов: ${err.message}`, 'error');
      console.error('Presets fetch error:', err);
    } finally {
      setPresetsLoading(false);
    }
  }, [addLog]);

  // Load Dominant presets on indicator change
  useEffect(() => {
    if (indicatorType === 'dominant' && dominantPresets.length === 0) {
      fetchDominantPresets();
    }
  }, [indicatorType, dominantPresets.length, fetchDominantPresets]);

  // ============ PRESET SELECTION (NEW) ============
  const handlePresetSelect = useCallback((preset) => {
    if (!preset) {
      setSelectedPreset(null);
      setPresetOriginalParams(null);
      addLog('🔄 Пресет сброшен', 'info');
      return;
    }

    setSelectedPreset(preset);
    
    // Extract params and apply to settings
    const params = preset.params && Object.keys(preset.params).length > 0 ? preset.params : preset;
    const newSettings = {
      dominant_sensitivity: params.sensitivity ?? params.sens ?? 21,
      dominant_filter_type: params.filter_type ?? params.filterType ?? 0,
      dominant_sl_mode: params.sl_mode ?? params.slMode ?? 0,
      dominant_tp1_percent: params.tp1_percent ?? params.tp1 ?? 1.0,
      dominant_tp2_percent: params.tp2_percent ?? params.tp2 ?? 2.0,
      dominant_tp3_percent: params.tp3_percent ?? params.tp3 ?? 3.0,
      dominant_tp4_percent: params.tp4_percent ?? params.tp4 ?? 5.0,
      dominant_tp1_amount: params.tp1_amount ?? 40,
      dominant_tp2_amount: params.tp2_amount ?? 30,
      dominant_tp3_amount: params.tp3_amount ?? 20,
      dominant_tp4_amount: params.tp4_amount ?? 10,
      dominant_sl_percent: params.sl_percent ?? params.sl ?? 2.0,
    };
    
    setPresetOriginalParams(newSettings);
    setSettings(prev => ({ ...prev, ...newSettings }));
    addLog(`✅ Пресет "${preset.name}" применён`, 'success');
  }, [addLog]);

  // Check if current settings differ from selected preset
  const isModified = useMemo(() => {
    if (!selectedPreset || !presetOriginalParams) return false;
    
    const keysToCheck = [
      'dominant_sensitivity', 'dominant_filter_type', 'dominant_sl_mode',
      'dominant_tp1_percent', 'dominant_tp2_percent', 'dominant_tp3_percent', 'dominant_tp4_percent',
      'dominant_sl_percent'
    ];
    
    return keysToCheck.some(key => settings[key] !== presetOriginalParams[key]);
  }, [settings, selectedPreset, presetOriginalParams]);

  // Handle indicator type change
  const handleIndicatorChange = useCallback((newType) => {
    setIndicatorType(newType);
    addLog(`🔄 Индикатор изменён на ${newType.toUpperCase()}`, 'info');
    
    // Reset preset selection when switching to TRG
    if (newType === 'trg') {
      setSelectedPreset(null);
      setPresetOriginalParams(null);
    }
  }, [addLog]);

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

  // ============ RENDER CHART WITH TRADE LEVELS (Chat #28) ============
  const renderChart = useCallback((data) => {
    if (!chartContainerRef.current || !data) return;

    // Clear previous chart
    if (chartRef.current) {
      chartRef.current.remove();
      chartRef.current = null;
    }
    
    // Clear previous level series
    tradeLevelSeriesRef.current = [];

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

    // TRG Lines (indicator lines)
    if (data.indicators?.trg_upper) {
      const upperSeries = chart.addLineSeries({ color: '#22c55e', lineWidth: 1, lineStyle: 2 });
      upperSeries.setData(data.indicators.trg_upper);
    }
    if (data.indicators?.trg_lower) {
      const lowerSeries = chart.addLineSeries({ color: '#ef4444', lineWidth: 1, lineStyle: 2 });
      lowerSeries.setData(data.indicators.trg_lower);
    }

    // ============ TRADE LEVEL LINES (Chat #28) ============
    // Draw TP/SL/Entry lines for each trade
    if (settings.show_trade_levels && data.trades?.length > 0) {
      data.trades.forEach((trade, tradeIdx) => {
        // Get entry and exit timestamps
        const entryTime = trade.entry_time 
          ? Math.floor(new Date(trade.entry_time).getTime() / 1000)
          : null;
        const exitTime = trade.exit_time
          ? Math.floor(new Date(trade.exit_time).getTime() / 1000)
          : null;
        
        if (!entryTime || !exitTime) return;
        
        const entryPrice = trade.entry_price;
        const isLong = trade.type === 'long';
        
        // Get TP levels (works for both TRG and Dominant)
        const tpLevels = trade.tp_levels || [];
        
        // Get SL level
        const slLevel = trade.sl_level || trade.initial_sl || trade.final_sl;
        
        // Get which TPs were hit
        // TRG uses tp_hit: [true, true, false, false]
        // Dominant uses tps_hit: [1, 2] (numbers of hit TPs)
        const tpHit = trade.tp_hit || [];
        const tpsHitNums = trade.tps_hit || [];
        
        // Check if TP was hit
        const isTpHit = (tpIdx) => {
          if (Array.isArray(tpHit) && tpHit[tpIdx] === true) return true;
          if (Array.isArray(tpsHitNums) && tpsHitNums.includes(tpIdx + 1)) return true;
          return false;
        };
        
        // Entry line (blue)
        if (entryPrice) {
          const entrySeries = chart.addLineSeries({
            color: '#3b82f6',
            lineWidth: 1,
            lineStyle: 0,
            lastValueVisible: false,
            priceLineVisible: false,
          });
          entrySeries.setData([
            { time: entryTime, value: entryPrice },
            { time: exitTime, value: entryPrice },
          ]);
          tradeLevelSeriesRef.current.push(entrySeries);
        }
        
        // TP lines (green)
        tpLevels.forEach((tpPrice, tpIdx) => {
          if (!tpPrice) return;
          
          const wasHit = isTpHit(tpIdx);
          
          const tpSeries = chart.addLineSeries({
            color: wasHit ? '#22c55e' : '#4ade80',
            lineWidth: 1,
            lineStyle: wasHit ? 0 : 2, // Solid if hit, dashed if not
            lastValueVisible: false,
            priceLineVisible: false,
          });
          tpSeries.setData([
            { time: entryTime, value: tpPrice },
            { time: exitTime, value: tpPrice },
          ]);
          tradeLevelSeriesRef.current.push(tpSeries);
        });
        
        // SL line (red)
        if (slLevel) {
          const slHit = trade.exit_reason === 'sl' || trade.exit_reason === 'SL';
          
          const slSeries = chart.addLineSeries({
            color: slHit ? '#ef4444' : '#f87171',
            lineWidth: 1,
            lineStyle: slHit ? 0 : 2,
            lastValueVisible: false,
            priceLineVisible: false,
          });
          slSeries.setData([
            { time: entryTime, value: slLevel },
            { time: exitTime, value: slLevel },
          ]);
          tradeLevelSeriesRef.current.push(slSeries);
        }
      });
    }

    // ============ TRADE MARKERS ============
    // Build enhanced markers with TP hit checkmarks
    if (data.trades?.length > 0) {
      const markers = [];
      
      data.trades.forEach((trade, idx) => {
        const entryTime = trade.entry_time 
          ? Math.floor(new Date(trade.entry_time).getTime() / 1000)
          : null;
        const exitTime = trade.exit_time
          ? Math.floor(new Date(trade.exit_time).getTime() / 1000)
          : null;
        
        if (!entryTime) return;
        
        const isLong = trade.type === 'long';
        const isReentry = trade.is_reentry;
        
        // Entry marker
        markers.push({
          time: entryTime,
          position: isLong ? 'belowBar' : 'aboveBar',
          color: isReentry ? '#fbbf24' : (isLong ? '#22c55e' : '#ef4444'),
          shape: isLong ? 'arrowUp' : 'arrowDown',
          text: isReentry ? `RE-${trade.type.toUpperCase()}` : trade.type.toUpperCase(),
        });
        
        // TP hit markers
        const tpLevels = trade.tp_levels || [];
        const tpHit = trade.tp_hit || [];
        const tpsHitNums = trade.tps_hit || [];
        const duration = exitTime && entryTime ? exitTime - entryTime : 0;
        
        // Count hit TPs
        let hitCount = 0;
        tpLevels.forEach((tpPrice, tpIdx) => {
          const wasHit = (Array.isArray(tpHit) && tpHit[tpIdx] === true) ||
                        (Array.isArray(tpsHitNums) && tpsHitNums.includes(tpIdx + 1));
          if (wasHit) {
            hitCount++;
            // Place TP marker between entry and exit
            const tpTime = entryTime + Math.floor(duration * hitCount / (tpLevels.length + 1));
            markers.push({
              time: tpTime,
              position: isLong ? 'aboveBar' : 'belowBar',
              color: '#22c55e',
              shape: 'circle',
              text: `TP${tpIdx + 1}✓`,
            });
          }
        });
        
        // Exit marker
        if (exitTime) {
          const pnl = trade.pnl || 0;
          const exitReason = trade.exit_reason || '';
          const isSL = exitReason.toLowerCase() === 'sl';
          
          markers.push({
            time: exitTime,
            position: isLong ? 'aboveBar' : 'belowBar',
            color: pnl > 0 ? '#22c55e' : '#ef4444',
            shape: isSL ? 'square' : 'circle',
            text: `${pnl >= 0 ? '+' : ''}${pnl.toFixed(1)}%`,
          });
        }
      });
      
      // Sort by time and set markers
      markers.sort((a, b) => a.time - b.time);
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
  }, [settings.show_trade_levels]);

  // Main calculate
  const calculate = async (forceRecalculate = false) => {
    setLoading(true);
    
    // Show period info in log if dates are set
    let periodInfo = '';
    if (settings.start_date || settings.end_date) {
      periodInfo = ` [${settings.start_date || '...'} — ${settings.end_date || '...'}]`;
    }
    const forceLabel = forceRecalculate ? ' (force)' : '';
    const indicatorLabel = indicatorType.toUpperCase();
    addLog(`🚀 Запуск ${indicatorLabel}: ${settings.symbol} ${settings.timeframe}${periodInfo}${forceLabel}...`, 'info');
    
    try {
      // Build request body based on indicator type
      const requestBody = {
        ...settings,
        indicator_type: indicatorType,
        force_recalculate: forceRecalculate
      };
      
      const res = await fetch('/api/indicator/calculate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
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
            body: JSON.stringify(requestBody)
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
      setCachedResult(data.cached || false);
      fetchCacheStats();
      
      // Log cache status
      const cacheStatus = data.cached ? '📦 (из кэша)' : '🔄 (новый расчёт)';
      
      // Save data range from response
      if (data.data_range) {
        setDataRange(data.data_range);
        addLog(`📅 Период: ${data.data_range.used_start} — ${data.data_range.used_end} (${data.data_range.used_candles} свечей)`, 'info');
      }
      
      addLog(`✅ ${data.candles?.length || 0} свечей загружено ${cacheStatus}`, 'success');
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
    a.download = `komas_${indicatorType}_${settings.symbol}_${settings.timeframe}_trades.csv`;
    a.click();
    addLog('📄 CSV экспортирован', 'success');
  };

  const exportJSON = () => {
    if (!result) return;
    const data = { 
      indicator_type: indicatorType,
      settings, 
      stats: result.stats, 
      trades: result.trades 
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `komas_${indicatorType}_${settings.symbol}_${settings.timeframe}.json`;
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

  // Tabs
  const tabs = [
    { id: 'chart', icon: '📈', label: 'График' },
    { id: 'stats', icon: '📊', label: 'Статистика' },
    { id: 'trades', icon: '📋', label: 'Сделки' },
    { id: 'monthly', icon: '📅', label: 'Месяцы' },
    { id: 'optimize', icon: '🔥', label: 'Оптимизация' },
    { id: 'heatmap', icon: '🗺️', label: 'Heatmap' },
  ];

  return (
    <div className="flex h-screen bg-gray-900 text-white overflow-hidden">
      {/* Settings Sidebar */}
      <SettingsSidebar 
        settings={settings} 
        onUpdate={updateSetting}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        dataRange={dataRange}
        cacheStats={cacheStats}
        onClearCache={clearCache}
        indicatorType={indicatorType}
        onIndicatorChange={handleIndicatorChange}
        presets={dominantPresets}
        presetsLoading={presetsLoading}
        selectedPreset={selectedPreset}
        onPresetSelect={handlePresetSelect}
        isModified={isModified}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="bg-gray-800 border-b border-gray-700 px-4 py-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Symbol selector */}
              <div className="relative">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setShowSymbolDropdown(!showSymbolDropdown)}
                >
                  <span className="font-bold">{settings.symbol}</span>
                  <span className="text-gray-400 ml-1">▼</span>
                </Button>

                {showSymbolDropdown && (
                  <div className="absolute top-full left-0 mt-1 w-48 bg-gray-800 border border-gray-700 rounded shadow-lg z-50 max-h-64 overflow-y-auto">
                    <Input
                      type="text"
                      placeholder="Search..."
                      value={symbolSearch}
                      onChange={(e) => setSymbolSearch(e.target.value)}
                      className="border-b border-gray-600 rounded-none text-sm"
                      autoFocus
                    />
                    {filteredSymbols.map(s => (
                      <Button
                        key={s}
                        variant={settings.symbol === s ? 'primary' : 'ghost'}
                        size="sm"
                        onClick={() => selectSymbol(s)}
                        className={`w-full justify-start rounded-none ${
                          settings.symbol === s ? 'bg-purple-600' : ''
                        }`}
                      >
                        {s}
                      </Button>
                    ))}
                  </div>
                )}
              </div>

              {/* Timeframe selector */}
              <div className="flex gap-1">
                {TIMEFRAMES.map(tf => (
                  <Button
                    key={tf}
                    variant={settings.timeframe === tf ? 'primary' : 'secondary'}
                    size="sm"
                    onClick={() => updateSetting('timeframe', tf)}
                    className={`text-xs ${settings.timeframe === tf ? 'bg-purple-600' : ''}`}
                  >
                    {tf}
                  </Button>
                ))}
              </div>

              {/* Indicator badge */}
              <Badge
                variant={indicatorType === 'trg' ? 'secondary' : 'primary'}
                className={`${indicatorType === 'trg' ? 'bg-purple-600' : 'bg-blue-600'}`}
              >
                {indicatorType.toUpperCase()}
              </Badge>

              {/* Paper Trading badge */}
              <Badge variant="warning" className="text-xs">
                📊 Paper Trading
              </Badge>

              {/* Trade levels toggle (Chat #28) */}
              <label className="flex items-center gap-1.5 text-xs text-gray-400 cursor-pointer">
                <input
                  type="checkbox"
                  checked={settings.show_trade_levels}
                  onChange={(e) => updateSetting('show_trade_levels', e.target.checked)}
                  className="rounded"
                />
                <span>Уровни</span>
              </label>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="primary"
                size="sm"
                onClick={() => calculate()}
                disabled={loading}
                loading={loading}
                className="bg-purple-600 hover:bg-purple-500"
              >
                {loading ? 'Расчёт...' : '▶️ Рассчитать'}
              </Button>

              <Button
                variant="secondary"
                size="sm"
                onClick={() => calculate(true)}
                disabled={loading}
                title="Принудительный пересчёт (без кэша)"
              >
                🔄
              </Button>

              <Button
                variant="secondary"
                size="sm"
                onClick={exportCSV}
                disabled={!result?.trades?.length}
              >
                📄 CSV
              </Button>

              <Button
                variant="secondary"
                size="sm"
                onClick={exportJSON}
                disabled={!result}
              >
                📄 JSON
              </Button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mt-2">
            {tabs.map(tab => (
              <Button
                key={tab.id}
                variant={activeTab === tab.id ? 'secondary' : 'ghost'}
                size="sm"
                onClick={() => setActiveTab(tab.id)}
                className={activeTab === tab.id ? 'bg-gray-700' : ''}
              >
                {tab.icon} {tab.label}
              </Button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-hidden">
          {activeTab === 'chart' && (
            <div className="h-full flex flex-col">
              <div ref={chartContainerRef} className="flex-1" />
              <div ref={equityChartRef} className="h-24 border-t border-gray-700" />
            </div>
          )}

          {activeTab === 'stats' && (
            <div className="h-full overflow-y-auto p-4">
              <StatsPanel stats={result?.stats} trades={result?.trades} indicatorType={indicatorType} />
            </div>
          )}

          {activeTab === 'trades' && (
            <div className="h-full overflow-hidden">
              <TradesTable trades={result?.trades || []} />
            </div>
          )}

          {activeTab === 'monthly' && (
            <div className="h-full overflow-y-auto p-4">
              <MonthlyPanel monthly={result?.monthly} />
            </div>
          )}

          {activeTab === 'optimize' && (
            <div className="h-full overflow-y-auto p-4">
              <AutoOptimizePanel 
                settings={settings}
                onApplyParams={applyParams}
                addLog={addLog}
              />
            </div>
          )}

          {activeTab === 'heatmap' && (
            <div className="h-full overflow-y-auto p-4">
              <HeatmapPanel 
                data={heatmapData}
                loading={loadingHeatmap}
                onGenerate={generateHeatmap}
                onSelectCell={(i1, i2) => {
                  updateSetting('trg_atr_length', i1);
                  updateSetting('trg_multiplier', i2);
                  addLog(`Выбрано: i1=${i1}, i2=${i2}`, 'info');
                }}
              />
            </div>
          )}
        </div>

        {/* Logs Panel */}
        <LogsPanel 
          logs={logs}
          collapsed={logsCollapsed}
          onToggle={() => setLogsCollapsed(!logsCollapsed)}
          onClear={clearLogs}
        />
      </div>
    </div>
  );
};

export default Indicator;
