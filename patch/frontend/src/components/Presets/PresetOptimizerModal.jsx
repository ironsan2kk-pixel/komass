/**
 * Preset Optimizer Modal
 * Run optimization across all presets for selected pairs
 * 
 * Chat #48 - SSE Fix + Preset Optimization
 */
import { useState, useRef, useEffect } from 'react';

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
  
  const eventSourceRef = useRef(null);
  const logsEndRef = useRef(null);
  
  const addLog = (message, type = 'info') => {
    const time = new Date().toLocaleTimeString();
    setLogs(prev => [...prev.slice(-100), { time, message, type }]);
  };
  
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
  
  const startOptimization = async () => {
    if (selectedPairs.length === 0) {
      addLog('❌ Выберите хотя бы одну пару', 'error');
      return;
    }
    
    setRunning(true);
    setResults([]);
    setProgress({ current: 0, total: 0, percent: 0 });
    addLog(`🚀 Запуск оптимизации: ${selectedPairs.length} пар, режим ${mode}`, 'info');
    
    try {
      const params = new URLSearchParams({
        pairs: selectedPairs.join(','),
        timeframe,
        mode,
        indicator_type: indicatorType === 'all' ? '' : indicatorType,
      });
      
      const url = `${API_URL}/api/optimizer/presets/stream?${params}`;
      addLog(`📡 Подключение к ${url.split('?')[0]}...`, 'info');
      
      eventSourceRef.current = new EventSource(url);
      
      eventSourceRef.current.onopen = () => {
        addLog('✅ Соединение установлено', 'success');
      };
      
      eventSourceRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'start') {
            setProgress({ current: 0, total: data.total, percent: 0 });
            addLog(`📊 Тестируем ${data.total} комбинаций (${data.presets} пресетов × ${data.pairs} пар)`, 'info');
            addLog(`⚡ Используем ${data.workers || 'N/A'} ядер`, 'info');
          }
          else if (data.type === 'progress') {
            const pct = Math.round((data.current / data.total) * 100);
            setProgress({
              current: data.current,
              total: data.total,
              percent: pct
            });
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
            setResults(data.results || []);
            addLog(`🏁 Оптимизация завершена!`, 'success');
            if (data.best) {
              addLog(`🏆 Лучший пресет: ${data.best.preset_name} (PnL: ${data.best.avg_pnl?.toFixed(2)}%)`, 'success');
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
          addLog(`⚠️ Ошибка парсинга: ${e.message}`, 'warning');
        }
      };
      
      eventSourceRef.current.onerror = (e) => {
        setRunning(false);
        addLog('❌ Ошибка соединения с сервером', 'error');
        addLog('💡 Проверьте, что бэкенд запущен и endpoint /api/optimizer/presets/stream доступен', 'warning');
        eventSourceRef.current?.close();
      };
      
    } catch (error) {
      setRunning(false);
      addLog(`❌ Ошибка запуска: ${error.message}`, 'error');
    }
  };
  
  const stopOptimization = () => {
    eventSourceRef.current?.close();
    setRunning(false);
    addLog('⏹️ Остановлено пользователем', 'warning');
  };
  
  useEffect(() => {
    return () => {
      eventSourceRef.current?.close();
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
                </span>
              </div>
              <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-blue-600 to-purple-600 transition-all duration-300"
                  style={{ width: `${progress.percent}%` }}
                />
              </div>
            </div>
          )}
          
          {/* Results */}
          {results.length > 0 && (
            <div className="bg-gray-800 rounded-lg p-4">
              <h3 className="text-white font-medium mb-3 flex items-center gap-2">
                🏆 Топ-10 результатов
              </h3>
              <div className="space-y-2 max-h-48 overflow-auto">
                {results.slice(0, 10).map((r, i) => (
                  <div 
                    key={i} 
                    className={`flex items-center justify-between text-sm p-2 rounded ${
                      i === 0 ? 'bg-yellow-900/30 border border-yellow-600/50' : 'bg-gray-700/50'
                    }`}
                  >
                    <span className="text-gray-300">
                      <span className={`mr-2 ${i === 0 ? 'text-yellow-400' : 'text-gray-500'}`}>
                        #{i + 1}
                      </span>
                      {r.preset_name}
                      <span className="text-gray-500 ml-2 text-xs">
                        ({r.indicator_type?.toUpperCase()})
                      </span>
                    </span>
                    <span className="flex items-center gap-4">
                      <span className={r.avg_pnl >= 0 ? 'text-green-400' : 'text-red-400'}>
                        {r.avg_pnl >= 0 ? '+' : ''}{r.avg_pnl?.toFixed(2)}%
                      </span>
                      <span className="text-gray-400">
                        WR: {r.avg_win_rate?.toFixed(1)}%
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Logs */}
          <div>
            <label className="text-sm text-gray-400 mb-1 block">Логи</label>
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
