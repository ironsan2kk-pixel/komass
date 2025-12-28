/**
 * Preset Optimizer Modal
 * Run optimization across all presets for selected pairs
 * 
 * Chat #48 - Fixed with polling fallback for long-running optimizations
 */
import { useState, useRef, useEffect, useCallback } from 'react';

const API_URL = 'http://localhost:8000';

// Available pairs for optimization
const AVAILABLE_PAIRS = [
  'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
  'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT', 'LINKUSDT', 'DOTUSDT',
  'MATICUSDT', 'LTCUSDT', 'SHIBUSDT', 'TRXUSDT', 'ATOMUSDT',
  'UNIUSDT', 'APTUSDT', 'NEARUSDT', 'ARBUSDT', 'OPUSDT'
];

const TIMEFRAMES = ['15m', '30m', '1h', '2h', '4h', '1d'];

export default function PresetOptimizerModal({ isOpen, onClose, indicatorType = 'all' }) {
  const [selectedPairs, setSelectedPairs] = useState(['BTCUSDT', 'ETHUSDT', 'SOLUSDT']);
  const [timeframe, setTimeframe] = useState('1h');
  const [mode, setMode] = useState('quick'); // quick, standard, full
  
  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, percent: 0 });
  const [results, setResults] = useState([]);
  const [logs, setLogs] = useState([]);
  const [runId, setRunId] = useState(null);
  const [startTime, setStartTime] = useState(null);
  
  const eventSourceRef = useRef(null);
  const pollingRef = useRef(null);
  const logsEndRef = useRef(null);
  
  const addLog = useCallback((message, type = 'info') => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [...prev.slice(-100), { time, message, type }]);
  }, []);
  
  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);
  
  const togglePair = (pair) => {
    setSelectedPairs(prev => 
      prev.includes(pair) 
        ? prev.filter(p => p !== pair)
        : [...prev, pair]
    );
  };
  
  const selectAllPairs = () => setSelectedPairs([...AVAILABLE_PAIRS]);
  const clearPairs = () => setSelectedPairs([]);
  
  // Load results from API
  const loadResults = useCallback(async (rid) => {
    try {
      addLog(`📥 Загрузка результатов...`, 'info');
      const response = await fetch(`${API_URL}/api/optimizer/results/${rid}/scores?limit=50`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.scores && data.scores.length > 0) {
        // Map API response to our format
        const mappedResults = data.scores.map(s => ({
          preset_id: s.preset_id,
          preset_name: s.preset_name,
          indicator_type: s.indicator_type,
          avg_pnl: s.avg_pnl,
          avg_win_rate: s.avg_win_rate,
          avg_sharpe: s.avg_sharpe,
          avg_max_dd: s.avg_max_dd,
          positive_pairs: s.positive_pairs,
          total_pairs: s.total_pairs,
          grade: s.grade,
          overall_score: s.overall_score
        }));
        
        setResults(mappedResults);
        addLog(`✅ Загружено ${mappedResults.length} результатов`, 'success');
        
        if (mappedResults.length > 0) {
          const best = mappedResults[0];
          addLog(`🏆 Лучший: ${best.preset_name} (PnL: ${best.avg_pnl?.toFixed(2)}%)`, 'success');
        }
      } else {
        addLog(`⚠️ Результаты пусты`, 'warning');
      }
    } catch (error) {
      addLog(`❌ Ошибка загрузки результатов: ${error.message}`, 'error');
    }
  }, [addLog]);
  
  // Check optimization history for our run
  const checkHistory = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/api/optimizer/history?limit=5`);
      if (!response.ok) return null;
      
      const data = await response.json();
      
      // Find most recent completed run
      const completed = data.runs?.find(r => r.status === 'completed');
      return completed;
    } catch (error) {
      return null;
    }
  }, []);
  
  // Polling function to check for completion
  const pollForCompletion = useCallback(async () => {
    const elapsed = Math.round((Date.now() - startTime) / 1000);
    
    // Update progress display with elapsed time
    setProgress(prev => ({
      ...prev,
      elapsed
    }));
    
    // Check if optimization completed
    const completed = await checkHistory();
    
    if (completed && completed.run_id && !results.length) {
      // Found a completed run, load results
      addLog(`🏁 Оптимизация завершена за ${elapsed} сек`, 'success');
      setRunning(false);
      setRunId(completed.run_id);
      
      // Stop polling
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
        pollingRef.current = null;
      }
      
      // Load results
      await loadResults(completed.run_id);
    }
  }, [startTime, results.length, checkHistory, loadResults, addLog]);
  
  // Start polling when running
  useEffect(() => {
    if (running && startTime) {
      // Poll every 5 seconds
      pollingRef.current = setInterval(pollForCompletion, 5000);
      
      return () => {
        if (pollingRef.current) {
          clearInterval(pollingRef.current);
          pollingRef.current = null;
        }
      };
    }
  }, [running, startTime, pollForCompletion]);
  
  const startOptimization = async () => {
    if (selectedPairs.length === 0) {
      addLog('❌ Выберите хотя бы одну пару', 'error');
      return;
    }
    
    setRunning(true);
    setResults([]);
    setRunId(null);
    setStartTime(Date.now());
    setProgress({ current: 0, total: 0, percent: 0, elapsed: 0 });
    addLog(`🚀 Запуск оптимизации: ${selectedPairs.length} пар, режим ${mode}`, 'info');
    
    try {
      const params = new URLSearchParams({
        pairs: selectedPairs.join(','),
        timeframe,
        mode,
        indicator_type: indicatorType === 'all' ? '' : indicatorType,
      });
      
      const url = `${API_URL}/api/optimizer/presets/stream?${params}`;
      addLog(`📡 Подключение к серверу...`, 'info');
      
      eventSourceRef.current = new EventSource(url);
      
      let receivedEvents = false;
      
      eventSourceRef.current.onopen = () => {
        addLog('✅ Соединение установлено', 'success');
        addLog('⏳ Ожидание результатов (может занять несколько минут)...', 'info');
      };
      
      eventSourceRef.current.onmessage = (event) => {
        try {
          receivedEvents = true;
          const data = JSON.parse(event.data);
          
          if (data.type === 'heartbeat') {
            // Just a keepalive, ignore
            return;
          }
          
          if (data.type === 'start') {
            const totalCombinations = data.total || (data.presets * data.pairs);
            setProgress(prev => ({ ...prev, current: 0, total: totalCombinations, percent: 0 }));
            addLog(`📊 Тестируем ${totalCombinations} комбинаций (${data.presets} пресетов × ${data.pairs} пар)`, 'info');
            addLog(`⚡ Используем ${data.workers || 'N/A'} ядер`, 'info');
          }
          else if (data.type === 'progress') {
            const pct = Math.round((data.current / data.total) * 100);
            setProgress(prev => ({
              ...prev,
              current: data.current,
              total: data.total,
              percent: pct
            }));
            if (data.current % 10 === 0 || data.current === data.total) {
              addLog(`📈 Прогресс: ${data.current}/${data.total} (${pct}%)`, 'info');
            }
          }
          else if (data.type === 'preset_done') {
            const pnlColor = data.avg_pnl >= 0 ? '🟢' : '🔴';
            addLog(`${pnlColor} ${data.preset_name}: PnL ${data.avg_pnl?.toFixed(2)}%, WR ${data.avg_win_rate?.toFixed(1)}%`, 
                   data.avg_pnl >= 0 ? 'success' : 'warning');
          }
          else if (data.type === 'complete') {
            setRunning(false);
            
            // Stop polling
            if (pollingRef.current) {
              clearInterval(pollingRef.current);
              pollingRef.current = null;
            }
            
            if (data.results && data.results.length > 0) {
              setResults(data.results);
              addLog(`🏁 Оптимизация завершена!`, 'success');
              if (data.best) {
                addLog(`🏆 Лучший пресет: ${data.best.preset_name} (PnL: ${data.best.avg_pnl?.toFixed(2)}%)`, 'success');
              }
            } else if (data.run_id) {
              // Results not in SSE, load from API
              setRunId(data.run_id);
              loadResults(data.run_id);
            }
            
            addLog(`⏱️ Время: ${data.duration?.toFixed(1) || 'N/A'} сек`, 'info');
            eventSourceRef.current?.close();
          }
          else if (data.type === 'error') {
            setRunning(false);
            addLog(`❌ Ошибка: ${data.message}`, 'error');
            eventSourceRef.current?.close();
          }
        } catch (e) {
          console.error('Parse error:', e);
        }
      };
      
      eventSourceRef.current.onerror = async (e) => {
        eventSourceRef.current?.close();
        
        // If we didn't receive any events, it's a connection error
        if (!receivedEvents) {
          setRunning(false);
          addLog('❌ Ошибка соединения с сервером', 'error');
          return;
        }
        
        // Otherwise, connection closed after work started - check for results
        addLog('📡 Соединение закрыто, проверяем результаты...', 'info');
        
        // Wait a bit and check history
        setTimeout(async () => {
          const completed = await checkHistory();
          if (completed) {
            setRunning(false);
            setRunId(completed.run_id);
            await loadResults(completed.run_id);
          } else {
            // Still running, continue polling
            addLog('⏳ Оптимизация продолжается в фоне...', 'info');
          }
        }, 2000);
      };
      
    } catch (error) {
      setRunning(false);
      addLog(`❌ Ошибка запуска: ${error.message}`, 'error');
    }
  };
  
  const stopOptimization = () => {
    eventSourceRef.current?.close();
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    setRunning(false);
    addLog('⏹️ Остановлено пользователем', 'warning');
  };
  
  // Load results manually
  const loadLatestResults = async () => {
    addLog('🔍 Поиск последних результатов...', 'info');
    const completed = await checkHistory();
    if (completed) {
      setRunId(completed.run_id);
      await loadResults(completed.run_id);
    } else {
      addLog('⚠️ Нет завершённых оптимизаций', 'warning');
    }
  };
  
  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col border border-gray-700">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700 bg-gray-800">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            🔥 Оптимизация пресетов
          </h2>
          <button 
            onClick={onClose} 
            className="text-gray-400 hover:text-white text-2xl leading-none"
          >
            ×
          </button>
        </div>
        
        {/* Content */}
        <div className="flex-1 overflow-auto p-4 space-y-4">
          {/* Settings Row */}
          <div className="grid grid-cols-3 gap-4">
            {/* Mode */}
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Режим</label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
                disabled={running}
              >
                <option value="quick">Quick (топ-20 пресетов)</option>
                <option value="standard">Standard (топ-50)</option>
                <option value="full">Full (все пресеты)</option>
              </select>
            </div>
            
            {/* Timeframe */}
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Таймфрейм</label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white focus:border-blue-500 focus:outline-none"
                disabled={running}
              >
                {TIMEFRAMES.map(tf => (
                  <option key={tf} value={tf}>{tf}</option>
                ))}
              </select>
            </div>
            
            {/* Indicator filter */}
            <div>
              <label className="text-sm text-gray-400 mb-1 block">Индикатор</label>
              <div className="bg-gray-800 border border-gray-600 rounded-lg px-3 py-2 text-white">
                {indicatorType === 'all' ? 'Все (TRG + Dominant)' : indicatorType.toUpperCase()}
              </div>
            </div>
          </div>
          
          {/* Pairs Selection */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm text-gray-400">
                Торговые пары ({selectedPairs.length} выбрано)
              </label>
              <div className="space-x-2">
                <button
                  onClick={selectAllPairs}
                  className="text-xs text-blue-400 hover:text-blue-300"
                  disabled={running}
                >
                  Выбрать все
                </button>
                <button
                  onClick={clearPairs}
                  className="text-xs text-gray-400 hover:text-gray-300"
                  disabled={running}
                >
                  Очистить
                </button>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              {AVAILABLE_PAIRS.map(pair => (
                <button
                  key={pair}
                  onClick={() => togglePair(pair)}
                  disabled={running}
                  className={`px-3 py-1 rounded-lg text-sm transition-colors ${
                    selectedPairs.includes(pair)
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'
                  } ${running ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {pair.replace('USDT', '')}
                </button>
              ))}
            </div>
          </div>
          
          {/* Progress */}
          {(running || progress.total > 0) && (
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-400">Прогресс</span>
                <span className="text-white font-mono">
                  {progress.current} / {progress.total} ({progress.percent}%)
                  {progress.elapsed > 0 && (
                    <span className="text-gray-500 ml-2">
                      {Math.floor(progress.elapsed / 60)}:{String(progress.elapsed % 60).padStart(2, '0')}
                    </span>
                  )}
                </span>
              </div>
              <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-300 ${
                    running ? 'bg-gradient-to-r from-blue-600 to-purple-600 animate-pulse' : 'bg-green-600'
                  }`}
                  style={{ width: `${Math.max(progress.percent, running ? 5 : 0)}%` }}
                />
              </div>
            </div>
          )}
          
          {/* Results */}
          {results.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-white font-medium flex items-center gap-2">
                  🏆 Топ-10 результатов
                </h3>
                {runId && (
                  <span className="text-xs text-gray-500 font-mono">
                    {runId}
                  </span>
                )}
              </div>
              <div className="space-y-2 max-h-48 overflow-auto">
                {results.slice(0, 10).map((r, i) => (
                  <div 
                    key={r.preset_id || i} 
                    className={`flex items-center justify-between text-sm p-2 rounded ${
                      i === 0 ? 'bg-yellow-900/30 border border-yellow-600/50' : 'bg-gray-700/50'
                    }`}
                  >
                    <span className="text-gray-300 flex items-center gap-2">
                      <span className={`w-6 text-center ${i === 0 ? 'text-yellow-400' : 'text-gray-500'}`}>
                        #{i + 1}
                      </span>
                      <span>{r.preset_name}</span>
                      <span className="text-gray-500 text-xs">
                        ({r.indicator_type?.toUpperCase()})
                      </span>
                      {r.grade && (
                        <span className={`px-1.5 py-0.5 rounded text-xs font-bold ${
                          r.grade === 'A' ? 'bg-green-600' :
                          r.grade === 'B' ? 'bg-blue-600' :
                          r.grade === 'C' ? 'bg-yellow-600' :
                          'bg-red-600'
                        }`}>
                          {r.grade}
                        </span>
                      )}
                    </span>
                    <span className="flex items-center gap-4 text-right">
                      <span className={r.avg_pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                        {r.avg_pnl >= 0 ? '+' : ''}{r.avg_pnl?.toFixed(2)}%
                      </span>
                      <span className="text-gray-400 w-16">
                        WR: {r.avg_win_rate?.toFixed(0)}%
                      </span>
                      <span className="text-gray-500 w-20 text-xs">
                        {r.positive_pairs}/{r.total_pairs} пар
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Logs */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-sm text-gray-400">Логи</label>
              {!running && (
                <button
                  onClick={loadLatestResults}
                  className="text-xs text-blue-400 hover:text-blue-300"
                >
                  📥 Загрузить последние результаты
                </button>
              )}
            </div>
            <div className="bg-black rounded-lg p-3 h-40 overflow-auto font-mono text-xs border border-gray-700">
              {logs.map((log, i) => (
                <div key={i} className={`${
                  log.type === 'error' ? 'text-red-400' :
                  log.type === 'success' ? 'text-green-400' :
                  log.type === 'warning' ? 'text-yellow-400' :
                  'text-gray-400'
                }`}>
                  <span className="text-gray-600">[{log.time}]</span> {log.message}
                </div>
              ))}
              {logs.length === 0 && (
                <div className="text-gray-600">Готово к запуску оптимизации...</div>
              )}
              <div ref={logsEndRef} />
            </div>
          </div>
        </div>
        
        {/* Footer */}
        <div className="flex justify-between items-center gap-3 p-4 border-t border-gray-700 bg-gray-800">
          <div className="text-sm text-gray-400">
            {running && '⏳ Выполняется оптимизация...'}
            {!running && results.length > 0 && `✅ Найдено ${results.length} результатов`}
          </div>
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition-colors"
            >
              Закрыть
            </button>
            
            {running ? (
              <button
                onClick={stopOptimization}
                className="px-6 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg transition-colors flex items-center gap-2"
              >
                ⏹️ Остановить
              </button>
            ) : (
              <button
                onClick={startOptimization}
                className="px-6 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-lg transition-colors flex items-center gap-2"
              >
                🚀 Запустить
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
