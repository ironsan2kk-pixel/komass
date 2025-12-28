/**
 * KOMAS Trading Server - Preset Optimizer Page
 * =============================================
 * Full UI for preset optimization with multi-pair backtesting.
 * 
 * Features:
 * - Mode selection (Quick/Standard/Smart/Full)
 * - Preset and pair selection
 * - SSE streaming optimization progress
 * - Results display with sorting and filtering
 * - Heatmap visualization
 * - History of optimization runs
 * - Export results (CSV/JSON)
 * 
 * Chat #49: Optimizer UI
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { optimizerApi } from '../api';
import { 
  ModeSelector, 
  ResultsPanel, 
  HeatmapPanel, 
  HistoryPanel,
  GradeBadge 
} from '../components/Optimizer';

// API base URL for SSE
const API_BASE = 'http://localhost:8000';

// Tabs configuration
const TABS = [
  { id: 'optimize', label: 'Оптимизация', icon: '🚀' },
  { id: 'results', label: 'Результаты', icon: '📊' },
  { id: 'heatmap', label: 'Heatmap', icon: '🗺️' },
  { id: 'history', label: 'История', icon: '📜' },
];

// Timeframes
const TIMEFRAMES = [
  { value: '5m', label: '5 минут' },
  { value: '15m', label: '15 минут' },
  { value: '30m', label: '30 минут' },
  { value: '1h', label: '1 час' },
  { value: '2h', label: '2 часа' },
  { value: '4h', label: '4 часа' },
  { value: '1d', label: '1 день' },
];

/**
 * Progress bar component
 */
const ProgressBar = ({ progress, total, current, elapsed }) => {
  const percentage = total > 0 ? Math.round((progress / total) * 100) : 0;
  
  const formatTime = (seconds) => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm text-gray-400">
        <span>Прогресс: {progress} / {total}</span>
        <span>{percentage}%</span>
      </div>
      <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="flex justify-between text-xs text-gray-500">
        <span>Текущий: {current || '—'}</span>
        <span>Время: {formatTime(elapsed)}</span>
      </div>
    </div>
  );
};

/**
 * Preset selector with search and filters
 */
const PresetSelector = ({ presets, selected, onChange, loading }) => {
  const [search, setSearch] = useState('');
  const [indicatorFilter, setIndicatorFilter] = useState('');
  const [selectAll, setSelectAll] = useState(false);
  
  // Filter presets
  const filtered = presets.filter(p => {
    if (search && !p.name.toLowerCase().includes(search.toLowerCase())) return false;
    if (indicatorFilter && p.indicator_type !== indicatorFilter) return false;
    return true;
  });
  
  // Handle select all
  const handleSelectAll = (checked) => {
    setSelectAll(checked);
    if (checked) {
      onChange(filtered.map(p => p.id));
    } else {
      onChange([]);
    }
  };
  
  // Toggle single preset
  const togglePreset = (presetId) => {
    if (selected.includes(presetId)) {
      onChange(selected.filter(id => id !== presetId));
    } else {
      onChange([...selected, presetId]);
    }
  };
  
  if (loading) {
    return (
      <div className="animate-pulse bg-gray-800 rounded-lg h-64 flex items-center justify-center">
        <span className="text-gray-500">Загрузка пресетов...</span>
      </div>
    );
  }
  
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-3">Выбор пресетов</h3>
        
        {/* Filters */}
        <div className="flex flex-wrap gap-3">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск..."
            className="flex-1 min-w-[200px] bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={indicatorFilter}
            onChange={(e) => setIndicatorFilter(e.target.value)}
            className="bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Все индикаторы</option>
            <option value="trg">TRG</option>
            <option value="dominant">Dominant</option>
          </select>
        </div>
        
        {/* Select all */}
        <div className="flex items-center justify-between mt-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={selectAll}
              onChange={(e) => handleSelectAll(e.target.checked)}
              className="w-4 h-4 rounded border-gray-600 bg-gray-900 text-blue-500 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-400">Выбрать все ({filtered.length})</span>
          </label>
          <span className="text-sm text-blue-400">{selected.length} выбрано</span>
        </div>
      </div>
      
      {/* List */}
      <div className="max-h-64 overflow-y-auto p-2">
        {filtered.length === 0 ? (
          <div className="text-center py-8 text-gray-500">Пресеты не найдены</div>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
            {filtered.map(preset => (
              <label
                key={preset.id}
                className={`
                  flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors
                  ${selected.includes(preset.id) 
                    ? 'bg-blue-500/20 border border-blue-500/50' 
                    : 'bg-gray-900/50 border border-transparent hover:bg-gray-900'}
                `}
              >
                <input
                  type="checkbox"
                  checked={selected.includes(preset.id)}
                  onChange={() => togglePreset(preset.id)}
                  className="w-4 h-4 rounded border-gray-600 bg-gray-900 text-blue-500 focus:ring-blue-500"
                />
                <div className="min-w-0">
                  <div className="text-sm text-white truncate">{preset.name}</div>
                  <div className="text-xs text-gray-500">{preset.indicator_type}</div>
                </div>
              </label>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Pair selector component
 */
const PairSelector = ({ pairs, selected, onChange, loading }) => {
  const [search, setSearch] = useState('');
  const [selectAll, setSelectAll] = useState(false);
  
  // Filter pairs
  const filtered = pairs.filter(p => 
    p.toLowerCase().includes(search.toLowerCase())
  );
  
  // Handle select all
  const handleSelectAll = (checked) => {
    setSelectAll(checked);
    if (checked) {
      onChange(filtered);
    } else {
      onChange([]);
    }
  };
  
  // Toggle single pair
  const togglePair = (pair) => {
    if (selected.includes(pair)) {
      onChange(selected.filter(p => p !== pair));
    } else {
      onChange([...selected, pair]);
    }
  };
  
  // Quick select buttons
  const quickSelect = (type) => {
    const selections = {
      majors: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT'],
      top10: pairs.slice(0, 10),
      top20: pairs.slice(0, 20),
      all: pairs
    };
    onChange(selections[type] || []);
  };
  
  if (loading) {
    return (
      <div className="animate-pulse bg-gray-800 rounded-lg h-64 flex items-center justify-center">
        <span className="text-gray-500">Загрузка пар...</span>
      </div>
    );
  }
  
  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-3">Выбор торговых пар</h3>
        
        {/* Search */}
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Поиск пары..."
          className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        
        {/* Quick select */}
        <div className="flex flex-wrap gap-2 mt-3">
          <button 
            onClick={() => quickSelect('majors')}
            className="px-3 py-1 bg-gray-900 hover:bg-gray-700 rounded text-sm text-gray-300 transition-colors"
          >
            Majors (5)
          </button>
          <button 
            onClick={() => quickSelect('top10')}
            className="px-3 py-1 bg-gray-900 hover:bg-gray-700 rounded text-sm text-gray-300 transition-colors"
          >
            Top 10
          </button>
          <button 
            onClick={() => quickSelect('top20')}
            className="px-3 py-1 bg-gray-900 hover:bg-gray-700 rounded text-sm text-gray-300 transition-colors"
          >
            Top 20
          </button>
          <button 
            onClick={() => onChange([])}
            className="px-3 py-1 bg-gray-900 hover:bg-red-900/50 rounded text-sm text-gray-300 transition-colors"
          >
            Очистить
          </button>
        </div>
        
        {/* Select all */}
        <div className="flex items-center justify-between mt-3">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={selectAll}
              onChange={(e) => handleSelectAll(e.target.checked)}
              className="w-4 h-4 rounded border-gray-600 bg-gray-900 text-blue-500 focus:ring-blue-500"
            />
            <span className="text-sm text-gray-400">Выбрать все ({filtered.length})</span>
          </label>
          <span className="text-sm text-blue-400">{selected.length} выбрано</span>
        </div>
      </div>
      
      {/* List */}
      <div className="max-h-48 overflow-y-auto p-2">
        <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2">
          {filtered.map(pair => (
            <label
              key={pair}
              className={`
                flex items-center gap-2 p-2 rounded cursor-pointer transition-colors
                ${selected.includes(pair) 
                  ? 'bg-green-500/20 border border-green-500/50' 
                  : 'bg-gray-900/50 border border-transparent hover:bg-gray-900'}
              `}
            >
              <input
                type="checkbox"
                checked={selected.includes(pair)}
                onChange={() => togglePair(pair)}
                className="w-4 h-4 rounded border-gray-600 bg-gray-900 text-green-500 focus:ring-green-500"
              />
              <span className="text-sm text-white">{pair.replace('USDT', '')}</span>
            </label>
          ))}
        </div>
      </div>
    </div>
  );
};

/**
 * Main Optimizer Page
 */
export default function Optimizer() {
  // Tab state
  const [activeTab, setActiveTab] = useState('optimize');
  
  // Data state
  const [presets, setPresets] = useState([]);
  const [pairs, setPairs] = useState([]);
  const [modes, setModes] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  
  // Selection state
  const [selectedPresets, setSelectedPresets] = useState([]);
  const [selectedPairs, setSelectedPairs] = useState([]);
  const [selectedMode, setSelectedMode] = useState('standard');
  const [timeframe, setTimeframe] = useState('1h');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  
  // Optimization state
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, item: '' });
  const [elapsed, setElapsed] = useState(0);
  const [estimate, setEstimate] = useState(null);
  const [error, setError] = useState(null);
  
  // Results state
  const [currentRunId, setCurrentRunId] = useState(null);
  const [results, setResults] = useState(null);
  
  // Refs
  const eventSourceRef = useRef(null);
  const elapsedTimerRef = useRef(null);
  const startTimeRef = useRef(null);
  
  // Load initial data
  useEffect(() => {
    const loadData = async () => {
      try {
        setLoadingData(true);
        
        // Load presets
        const presetsRes = await fetch(`${API_BASE}/api/presets/list?limit=500`);
        const presetsData = await presetsRes.json();
        setPresets(presetsData.presets || []);
        
        // Load pairs (from data endpoint)
        const pairsRes = await fetch(`${API_BASE}/api/data/symbols`);
        const pairsData = await pairsRes.json();
        setPairs(pairsData.symbols || []);
        
        // Load modes
        const modesRes = await optimizerApi.getModes();
        setModes(modesRes.data.modes || []);
        
      } catch (err) {
        console.error('Error loading data:', err);
        setError('Ошибка загрузки данных');
      } finally {
        setLoadingData(false);
      }
    };
    
    loadData();
  }, []);
  
  // Estimate time when selection changes
  useEffect(() => {
    const estimateTime = async () => {
      if (selectedPresets.length === 0 || selectedPairs.length === 0) {
        setEstimate(null);
        return;
      }
      
      try {
        const res = await optimizerApi.estimateTime(
          selectedPresets.length,
          selectedPairs.length,
          selectedMode
        );
        setEstimate(res.data);
      } catch (err) {
        console.error('Error estimating time:', err);
      }
    };
    
    estimateTime();
  }, [selectedPresets.length, selectedPairs.length, selectedMode]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      if (elapsedTimerRef.current) {
        clearInterval(elapsedTimerRef.current);
      }
    };
  }, []);
  
  // Start optimization
  const startOptimization = async () => {
    if (selectedPresets.length === 0 || selectedPairs.length === 0) {
      setError('Выберите пресеты и торговые пары');
      return;
    }
    
    setError(null);
    setIsOptimizing(true);
    setProgress({ current: 0, total: selectedPresets.length * selectedPairs.length, item: '' });
    setElapsed(0);
    startTimeRef.current = Date.now();
    
    // Start elapsed timer
    elapsedTimerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);
    
    try {
      // Use fetch for SSE with POST
      const response = await fetch(`${API_BASE}/api/optimizer/presets/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          preset_ids: selectedPresets,
          pairs: selectedPairs,
          timeframe: timeframe,
          mode: selectedMode,
          start_date: startDate || null,
          end_date: endDate || null
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.event === 'progress') {
                setProgress({
                  current: data.completed,
                  total: data.total,
                  item: `${data.preset} × ${data.pair}`
                });
              } else if (data.event === 'complete') {
                setCurrentRunId(data.run_id);
                setIsOptimizing(false);
                clearInterval(elapsedTimerRef.current);
                
                // Load results
                const resultsRes = await optimizerApi.getResults(data.run_id);
                setResults(resultsRes.data);
                setActiveTab('results');
              } else if (data.event === 'error') {
                setError(data.message);
                setIsOptimizing(false);
                clearInterval(elapsedTimerRef.current);
              }
            } catch (e) {
              console.error('Error parsing SSE:', e);
            }
          }
        }
      }
    } catch (err) {
      console.error('Optimization error:', err);
      setError(`Ошибка оптимизации: ${err.message}`);
      setIsOptimizing(false);
      clearInterval(elapsedTimerRef.current);
    }
  };
  
  // Cancel optimization
  const cancelOptimization = async () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    if (elapsedTimerRef.current) {
      clearInterval(elapsedTimerRef.current);
    }
    
    if (currentRunId) {
      try {
        await optimizerApi.cancelOptimization(currentRunId);
      } catch (err) {
        console.error('Error cancelling:', err);
      }
    }
    
    setIsOptimizing(false);
    setError(null);
  };
  
  // Load results from history
  const loadResults = async (runId) => {
    try {
      const res = await optimizerApi.getResults(runId);
      setResults(res.data);
      setCurrentRunId(runId);
      setActiveTab('results');
    } catch (err) {
      console.error('Error loading results:', err);
      setError('Ошибка загрузки результатов');
    }
  };
  
  // Render tab content
  const renderTabContent = () => {
    switch (activeTab) {
      case 'optimize':
        return (
          <div className="space-y-6">
            {/* Mode selector */}
            <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
              <h3 className="text-lg font-semibold text-white mb-4">Режим оптимизации</h3>
              <ModeSelector
                modes={modes}
                selected={selectedMode}
                onChange={setSelectedMode}
                estimate={estimate}
              />
            </div>
            
            {/* Settings row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Timeframe */}
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Таймфрейм</h3>
                <select
                  value={timeframe}
                  onChange={(e) => setTimeframe(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {TIMEFRAMES.map(tf => (
                    <option key={tf.value} value={tf.value}>{tf.label}</option>
                  ))}
                </select>
              </div>
              
              {/* Start date */}
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Дата начала</h3>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              {/* End date */}
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Дата окончания</h3>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            
            {/* Preset selector */}
            <PresetSelector
              presets={presets}
              selected={selectedPresets}
              onChange={setSelectedPresets}
              loading={loadingData}
            />
            
            {/* Pair selector */}
            <PairSelector
              pairs={pairs}
              selected={selectedPairs}
              onChange={setSelectedPairs}
              loading={loadingData}
            />
            
            {/* Estimate */}
            {estimate && (
              <div className="bg-gray-800/50 rounded-lg border border-gray-700 p-4">
                <div className="flex flex-wrap items-center gap-6">
                  <div>
                    <span className="text-gray-400 text-sm">Комбинаций:</span>
                    <span className="ml-2 text-white font-medium">
                      {estimate.total_combinations?.toLocaleString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400 text-sm">Расчётное время:</span>
                    <span className="ml-2 text-white font-medium">
                      {estimate.human_readable || '—'}
                    </span>
                  </div>
                </div>
              </div>
            )}
            
            {/* Error */}
            {error && (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-400">
                {error}
              </div>
            )}
            
            {/* Progress */}
            {isOptimizing && (
              <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
                <h3 className="text-lg font-semibold text-white mb-4">Выполнение оптимизации...</h3>
                <ProgressBar 
                  progress={progress.current}
                  total={progress.total}
                  current={progress.item}
                  elapsed={elapsed}
                />
              </div>
            )}
            
            {/* Action buttons */}
            <div className="flex gap-4">
              {isOptimizing ? (
                <button
                  onClick={cancelOptimization}
                  className="px-6 py-3 bg-red-600 hover:bg-red-700 rounded-lg text-white font-medium transition-colors"
                >
                  ⏹️ Отменить
                </button>
              ) : (
                <button
                  onClick={startOptimization}
                  disabled={selectedPresets.length === 0 || selectedPairs.length === 0}
                  className={`
                    px-6 py-3 rounded-lg font-medium transition-colors
                    ${selectedPresets.length === 0 || selectedPairs.length === 0
                      ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                      : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white'
                    }
                  `}
                >
                  🚀 Запустить оптимизацию
                </button>
              )}
            </div>
          </div>
        );
        
      case 'results':
        return results ? (
          <ResultsPanel 
            result={results} 
            onClose={() => {
              setResults(null);
              setCurrentRunId(null);
            }}
          />
        ) : (
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h3 className="text-xl font-semibold text-white mb-2">Нет результатов</h3>
            <p className="text-gray-400 mb-4">
              Запустите оптимизацию или выберите результаты из истории
            </p>
            <button
              onClick={() => setActiveTab('optimize')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white transition-colors"
            >
              Запустить оптимизацию
            </button>
          </div>
        );
        
      case 'heatmap':
        return currentRunId ? (
          <HeatmapPanel runId={currentRunId} />
        ) : (
          <div className="bg-gray-800 rounded-lg border border-gray-700 p-8 text-center">
            <div className="text-6xl mb-4">🗺️</div>
            <h3 className="text-xl font-semibold text-white mb-2">Нет данных для Heatmap</h3>
            <p className="text-gray-400 mb-4">
              Сначала запустите оптимизацию или загрузите результаты из истории
            </p>
            <button
              onClick={() => setActiveTab('history')}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-white transition-colors"
            >
              Открыть историю
            </button>
          </div>
        );
        
      case 'history':
        return (
          <HistoryPanel 
            onLoad={loadResults}
            currentRunId={currentRunId}
          />
        );
        
      default:
        return null;
    }
  };
  
  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">
          🔬 Оптимизация пресетов
        </h1>
        <p className="text-gray-400">
          Multi-pair бэктестирование и поиск лучших универсальных пресетов
        </p>
      </div>
      
      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-700 pb-2">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              px-4 py-2 rounded-t-lg font-medium transition-colors
              ${activeTab === tab.id
                ? 'bg-gray-800 text-white border-b-2 border-blue-500'
                : 'text-gray-400 hover:text-white hover:bg-gray-800/50'
              }
            `}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>
      
      {/* Content */}
      {renderTabContent()}
    </div>
  );
}
