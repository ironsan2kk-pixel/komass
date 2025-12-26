/**
 * Auto Optimize Panel Component
 * =============================
 * Панель автооптимизации с SSE streaming
 */
import { useState, useRef, useCallback } from 'react';

const OPT_MODES = [
  { id: 'indicator', name: 'Индикатор', icon: '📊', desc: 'i1, i2 параметры', count: '~144' },
  { id: 'tp', name: 'Take Profits', icon: '🎯', desc: 'TP1-4 уровни', count: '~16' },
  { id: 'sl', name: 'Stop Loss', icon: '🛡️', desc: 'SL + trailing', count: '~30' },
  { id: 'filters', name: 'Фильтры', icon: '🔍', desc: 'ST, RSI, ADX', count: '~60' },
  { id: 'full', name: 'Полный', icon: '🔥', desc: 'Все параметры', count: '500+' },
];

const DEPTHS = [
  { id: 'fast', name: 'Быстрый', desc: '~100 тестов' },
  { id: 'medium', name: 'Средний', desc: '~500 тестов' },
  { id: 'deep', name: 'Глубокий', desc: '~1000+ тестов' },
];

export default function AutoOptimizePanel({ settings, onApplyParams, addLog }) {
  // State
  const [mode, setMode] = useState('indicator');
  const [depth, setDepth] = useState('medium');
  const [metric, setMetric] = useState('advanced');
  const [optimizing, setOptimizing] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, percent: 0 });
  const [results, setResults] = useState([]);
  const [bestResult, setBestResult] = useState(null);
  const [workers, setWorkers] = useState(0);
  const [speed, setSpeed] = useState(0);
  const [eta, setEta] = useState(null);
  
  // Refs
  const abortControllerRef = useRef(null);
  const startTimeRef = useRef(null);

  // Start optimization
  const startOptimization = useCallback(async () => {
    setOptimizing(true);
    setProgress({ current: 0, total: 0, percent: 0 });
    setResults([]);
    setBestResult(null);
    setSpeed(0);
    setEta(null);
    startTimeRef.current = Date.now();

    addLog(`🚀 Запуск оптимизации: ${OPT_MODES.find(m => m.id === mode)?.name}`, 'optimize');

    try {
      abortControllerRef.current = new AbortController();

      const response = await fetch('/api/indicator/auto-optimize-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          mode,
          metric,
          full_mode_depth: depth,
          settings,
        }),
        signal: abortControllerRef.current.signal,
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
              handleSSEMessage(data);
            } catch (e) {
              console.error('Parse error:', e);
            }
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        addLog(`❌ Ошибка: ${err.message}`, 'error');
      }
    } finally {
      setOptimizing(false);
      abortControllerRef.current = null;
    }
  }, [mode, depth, metric, settings, addLog]);

  // Handle SSE messages
  const handleSSEMessage = useCallback((data) => {
    switch (data.type) {
      case 'start':
        setProgress(prev => ({ ...prev, total: data.total }));
        setWorkers(data.workers || 1);
        addLog(`📋 Всего тестов: ${data.total}, ядер: ${data.workers || 1}`, 'info');
        break;

      case 'test':
        const elapsed = (Date.now() - startTimeRef.current) / 1000;
        const testsPerSec = data.n / elapsed;
        const remaining = data.total - data.n;
        const etaSeconds = remaining / testsPerSec;

        setProgress({
          current: data.n,
          total: data.total,
          percent: Math.round((data.n / data.total) * 100),
        });
        setSpeed(testsPerSec);
        setEta(etaSeconds);

        // Add to results
        setResults(prev => [...prev.slice(-10), {
          n: data.n,
          params: data.params,
          profit: data.profit,
          win_rate: data.win_rate,
          is_best: data.is_best,
        }]);

        // Update best
        if (data.is_best) {
          setBestResult({
            params: data.params,
            config: data.best_config,
            profit: data.profit,
            win_rate: data.win_rate,
            trades: data.trades,
            profit_factor: data.profit_factor,
          });
        }
        break;

      case 'done':
        addLog(`✅ Оптимизация завершена! Лучший результат: ${data.best_result?.profit_pct?.toFixed(2)}%`, 'success');
        
        if (data.best_params) {
          setBestResult(prev => ({
            ...prev,
            params: data.best_params,
            config: data.best_result,
          }));
        }
        break;

      case 'error':
        addLog(`❌ ${data.message}`, 'error');
        break;
    }
  }, [addLog]);

  // Stop optimization
  const stopOptimization = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      addLog('⏹️ Оптимизация остановлена', 'warning');
    }
  }, [addLog]);

  // Apply best params
  const applyBestParams = useCallback(() => {
    if (bestResult?.params) {
      onApplyParams(bestResult.params);
      addLog('✅ Лучшие параметры применены', 'success');
    }
  }, [bestResult, onApplyParams, addLog]);

  // Format ETA
  const formatEta = (seconds) => {
    if (!seconds || !isFinite(seconds)) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="space-y-4">
      {/* Mode Selection */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <h3 className="font-bold mb-4">🎛️ Режим оптимизации</h3>
        <div className="grid grid-cols-5 gap-3">
          {OPT_MODES.map(m => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              disabled={optimizing}
              className={`p-4 rounded-xl border transition-all ${
                mode === m.id
                  ? 'bg-blue-600/20 border-blue-500 text-white'
                  : 'bg-gray-700/50 border-gray-600 text-gray-400 hover:border-gray-500'
              } disabled:opacity-50`}
            >
              <div className="text-2xl mb-2">{m.icon}</div>
              <div className="font-medium text-sm">{m.name}</div>
              <div className="text-xs text-gray-500 mt-1">{m.desc}</div>
              <div className="text-xs text-gray-600 mt-1">~{m.count}</div>
            </button>
          ))}
        </div>

        {/* Depth (for full mode) */}
        {mode === 'full' && (
          <div className="mt-4 pt-4 border-t border-gray-700">
            <div className="text-sm text-gray-400 mb-2">Глубина поиска</div>
            <div className="flex gap-2">
              {DEPTHS.map(d => (
                <button
                  key={d.id}
                  onClick={() => setDepth(d.id)}
                  disabled={optimizing}
                  className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-colors ${
                    depth === d.id
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-400 hover:text-white'
                  } disabled:opacity-50`}
                >
                  {d.name}
                  <div className="text-xs opacity-60">{d.desc}</div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Metric selector */}
          <select
            value={metric}
            onChange={(e) => setMetric(e.target.value)}
            disabled={optimizing}
            className="bg-gray-700 px-3 py-2 rounded-lg text-sm"
          >
            <option value="profit">По прибыли</option>
            <option value="win_rate">По Win Rate</option>
            <option value="advanced">Комплексный</option>
            <option value="sharpe">По Sharpe</option>
          </select>

          {/* Workers info */}
          {workers > 0 && (
            <div className="text-sm text-gray-400">
              🖥️ {workers} ядер
            </div>
          )}
        </div>

        {/* Start/Stop button */}
        {optimizing ? (
          <button
            onClick={stopOptimization}
            className="flex items-center gap-2 px-6 py-2 bg-red-600 hover:bg-red-500 rounded-lg font-medium"
          >
            <span>⏹️</span>
            Остановить
          </button>
        ) : (
          <button
            onClick={startOptimization}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium"
          >
            <span>🚀</span>
            Запустить
          </button>
        )}
      </div>

      {/* Progress */}
      {optimizing && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Прогресс</span>
            <span className="text-sm font-medium">
              {progress.current} / {progress.total} ({progress.percent}%)
            </span>
          </div>
          
          {/* Progress bar */}
          <div className="h-3 bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-600 to-cyan-500 transition-all duration-300"
              style={{ width: `${progress.percent}%` }}
            />
          </div>

          {/* Stats */}
          <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
            <span>⚡ {speed.toFixed(1)} тестов/сек</span>
            <span>⏱️ ETA: {formatEta(eta)}</span>
          </div>
        </div>
      )}

      {/* Best Result */}
      {bestResult && (
        <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-xl p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-green-400">🏆 Лучший результат</h3>
            <button
              onClick={applyBestParams}
              className="px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg text-sm font-medium"
            >
              Применить
            </button>
          </div>

          <div className="grid grid-cols-4 gap-4">
            <div>
              <div className="text-xs text-gray-400">Прибыль</div>
              <div className="text-xl font-bold text-green-400">
                +{bestResult.profit?.toFixed(2) || bestResult.config?.profit_pct?.toFixed(2)}%
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-400">Win Rate</div>
              <div className="text-xl font-bold text-blue-400">
                {bestResult.win_rate?.toFixed(1) || bestResult.config?.win_rate?.toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-400">Сделок</div>
              <div className="text-xl font-bold text-purple-400">
                {bestResult.trades || bestResult.config?.total_trades}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-400">PF</div>
              <div className="text-xl font-bold text-cyan-400">
                {(bestResult.profit_factor || bestResult.config?.profit_factor)?.toFixed(2)}
              </div>
            </div>
          </div>

          {/* Parameters */}
          {bestResult.params && (
            <div className="mt-4 pt-4 border-t border-green-500/20">
              <div className="text-xs text-gray-400 mb-2">Параметры</div>
              <div className="flex flex-wrap gap-2">
                {Object.entries(bestResult.params).map(([key, value]) => (
                  <span
                    key={key}
                    className="px-2 py-1 bg-gray-700/50 rounded text-xs"
                  >
                    {key}: {typeof value === 'number' ? value.toFixed(2) : String(value)}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Recent Results Log */}
      {results.length > 0 && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
          <h3 className="font-bold mb-3">📜 Последние результаты</h3>
          <div className="space-y-1 max-h-48 overflow-y-auto">
            {results.map((r, i) => (
              <div
                key={i}
                className={`flex items-center justify-between text-xs py-1 px-2 rounded ${
                  r.is_best ? 'bg-green-500/20 text-green-400' : 'text-gray-400'
                }`}
              >
                <span>#{r.n}</span>
                <span className="font-mono">
                  {Object.entries(r.params || {}).slice(0, 3).map(([k, v]) => 
                    `${k}=${typeof v === 'number' ? v.toFixed(1) : v}`
                  ).join(', ')}
                </span>
                <span className={r.profit >= 0 ? 'text-green-400' : 'text-red-400'}>
                  {r.profit >= 0 ? '+' : ''}{r.profit?.toFixed(2)}%
                </span>
                <span>{r.win_rate?.toFixed(1)}%</span>
                {r.is_best && <span>🏆</span>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {!optimizing && !bestResult && results.length === 0 && (
        <div className="flex flex-col items-center justify-center h-48 text-gray-500">
          <span className="text-6xl mb-4">🔥</span>
          <p>Выберите режим и запустите оптимизацию</p>
        </div>
      )}
    </div>
  );
}
