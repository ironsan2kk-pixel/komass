import React, { useState, useEffect, useRef } from 'react';

const OPT_MODES = {
  indicator: { name: 'Индикатор', desc: 'i1, i2', icon: '📊', count: '144' },
  tp: { name: 'Тейки', desc: 'TP1-4', icon: '🎯', count: '16' },
  sl: { name: 'Стопы', desc: 'SL + trailing', icon: '🛡️', count: '30' },
  filters: { name: 'Фильтры', desc: 'ST, RSI, ADX', icon: '🔍', count: '~60' },
  full: { name: 'Полный', desc: 'Все параметры', icon: '🔥', count: '500+' },
};

const AutoOptimizePanel = ({ settings, onApplyBest, addLog }) => {
  const [mode, setMode] = useState('indicator');
  const [depth, setDepth] = useState('medium');
  const [optimizing, setOptimizing] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0, percent: 0, workers: 0 });
  const [bestResult, setBestResult] = useState(null);
  const [results, setResults] = useState([]);
  const [speed, setSpeed] = useState(0);
  const [startTime, setStartTime] = useState(null);
  const eventSourceRef = useRef(null);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (startTime && progress.current > 0) {
      const elapsed = (Date.now() - startTime) / 1000;
      setSpeed(Math.round(progress.current / elapsed));
    }
  }, [progress.current, startTime]);

  const startOptimization = async () => {
    if (optimizing || !settings) return;
    
    setOptimizing(true);
    setProgress({ current: 0, total: 0, percent: 0, workers: 0 });
    setBestResult(null);
    setResults([]);
    setSpeed(0);
    setStartTime(Date.now());
    
    addLog?.(`🚀 Запуск оптимизации: ${OPT_MODES[mode].name}`, 'optimize');

    try {
      const params = new URLSearchParams({
        symbol: settings.symbol || 'BTCUSDT',
        timeframe: settings.timeframe || '1h',
        mode: mode,
        depth: depth,
        i1: settings.trg_atr_length || 45,
        i2: settings.trg_multiplier || 4,
        tp1: settings.tp1_percent || 1.05,
        tp2: settings.tp2_percent || 1.95,
        tp3: settings.tp3_percent || 3.75,
        tp4: settings.tp4_percent || 6.0,
        sl: settings.sl_percent || 6.0,
        sl_mode: settings.sl_trailing_mode || 'breakeven',
        use_st: settings.use_supertrend || false,
        st_period: settings.supertrend_period || 10,
        st_mult: settings.supertrend_multiplier || 3.0,
        use_rsi: settings.use_rsi_filter || false,
        rsi_period: settings.rsi_period || 14,
        use_adx: settings.use_adx_filter || false,
        adx_threshold: settings.adx_threshold || 25,
        allow_reentry: settings.allow_reentry || false,
        leverage: settings.leverage || 1,
        use_commission: settings.use_commission || false,
        commission: settings.commission_percent || 0.1,
      });

      const url = `/api/indicator/auto-optimize-stream?${params}`;
      
      eventSourceRef.current = new EventSource(url);
      
      eventSourceRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'start') {
            setProgress({ current: 0, total: data.total, percent: 0, workers: data.workers || 1 });
            addLog?.(`📊 Тестируем ${data.total} комбинаций на ${data.workers || 1} ядрах...`, 'info');
          } 
          else if (data.type === 'test') {
            setProgress(prev => ({
              ...prev,
              current: data.n,
              percent: Math.round((data.n / data.total) * 100)
            }));
            
            if (data.is_best) {
              setBestResult({
                params: data.params,
                profit: data.profit,
                win_rate: data.win_rate,
                config: data.best_config || null,
              });
              addLog?.(`🏆 Новый лучший: ${data.params} → ${data.profit?.toFixed(2)}%`, 'success');
            }
            
            setResults(prev => [...prev.slice(-20), data]);
          }
          else if (data.type === 'complete') {
            setOptimizing(false);
            eventSourceRef.current?.close();
            
            const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
            
            if (data.best) {
              setBestResult({
                params: data.best.params || `Лучший результат`,
                profit: data.best.profit,
                win_rate: data.best.win_rate,
                config: data.best,
              });
              addLog?.(`✅ Завершено за ${elapsed}с! Лучший: ${data.best.profit?.toFixed(2)}%, WR: ${data.best.win_rate?.toFixed(1)}%`, 'success');
            } else {
              addLog?.(`✅ Завершено за ${elapsed}с! Протестировано: ${data.tested}`, 'success');
            }
          }
          else if (data.type === 'error') {
            setOptimizing(false);
            eventSourceRef.current?.close();
            addLog?.(`❌ Ошибка: ${data.message}`, 'error');
          }
        } catch (e) {
          console.error('Parse error:', e);
          addLog?.(`❌ Ошибка парсинга: ${e.message}`, 'error');
        }
      };
      
      eventSourceRef.current.onerror = (error) => {
        console.error('SSE error:', error);
        setOptimizing(false);
        eventSourceRef.current?.close();
        addLog?.('❌ Ошибка соединения', 'error');
      };
      
    } catch (error) {
      setOptimizing(false);
      addLog?.(`❌ ${error.message}`, 'error');
    }
  };

  const stopOptimization = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setOptimizing(false);
    addLog?.('⏹️ Оптимизация остановлена', 'warning');
  };

  const applyBestResult = () => {
    if (bestResult?.config) {
      onApplyBest?.(bestResult.config);
      addLog?.('✅ Лучшие параметры применены', 'success');
    }
  };

  const eta = progress.current > 0 && speed > 0 
    ? Math.round((progress.total - progress.current) / speed) 
    : null;

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          🔥 Автоподбор параметров
        </h3>
        {progress.workers > 0 && (
          <span className="px-2 py-1 bg-blue-600/30 text-blue-400 text-xs rounded">
            🖥️ {progress.workers} ядер
          </span>
        )}
      </div>

      <div className="space-y-2">
        {Object.entries(OPT_MODES).map(([key, m]) => (
          <button
            key={key}
            onClick={() => setMode(key)}
            disabled={optimizing}
            className={`w-full flex items-center justify-between p-3 rounded-lg transition-all ${
              mode === key
                ? 'bg-purple-600/50 border border-purple-500'
                : 'bg-gray-700/50 border border-gray-600 hover:bg-gray-700'
            } ${optimizing ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <div className="flex items-center gap-2">
              <span className="text-xl">{m.icon}</span>
              <div className="text-left">
                <div className="font-medium text-white">{m.name}</div>
                <div className="text-xs text-gray-400">{m.desc}</div>
              </div>
            </div>
            <span className="text-xs text-gray-500">{m.count}</span>
          </button>
        ))}
      </div>

      {mode === 'full' && (
        <div>
          <label className="text-sm text-gray-400 block mb-2">Глубина поиска</label>
          <div className="flex gap-1">
            {[
              { value: 'fast', label: '⚡ Быстро', desc: '~100 комбинаций' },
              { value: 'medium', label: '⚖️ Средне', desc: '~500 комбинаций' },
              { value: 'deep', label: '🔬 Глубоко', desc: '~1000+ комбинаций' },
            ].map(d => (
              <button
                key={d.value}
                onClick={() => setDepth(d.value)}
                disabled={optimizing}
                className={`flex-1 py-2 rounded text-xs font-medium transition-all ${
                  depth === d.value ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-400'
                } ${optimizing ? 'opacity-50' : ''}`}
                title={d.desc}
              >
                {d.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {optimizing && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-gray-400">
            <span>{progress.current} / {progress.total}</span>
            <div className="flex gap-3">
              {speed > 0 && <span className="text-blue-400">{speed} тестов/сек</span>}
              {eta !== null && <span className="text-yellow-400">~{eta}с осталось</span>}
              <span>{progress.percent}%</span>
            </div>
          </div>
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-purple-500 to-blue-500 transition-all duration-300"
              style={{ width: `${progress.percent}%` }}
            />
          </div>
          {progress.workers > 1 && (
            <div className="text-xs text-gray-500 text-center">
              🚀 Многоядерный режим: {progress.workers} параллельных процессов
            </div>
          )}
        </div>
      )}

      {bestResult && (
        <div className="p-3 bg-green-900/30 border border-green-500/30 rounded-lg space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-green-400 font-medium">🏆 Лучший результат</span>
            <div className="flex gap-3 text-sm">
              <span className={bestResult.profit >= 0 ? 'text-green-400' : 'text-red-400'}>
                {bestResult.profit >= 0 ? '+' : ''}{bestResult.profit?.toFixed(2)}%
              </span>
              <span className="text-gray-400">WR: {bestResult.win_rate?.toFixed(1)}%</span>
            </div>
          </div>
          
          {bestResult.config && (
            <div className="space-y-1 text-xs font-mono bg-black/30 rounded p-2">
              {bestResult.config.trg && (
                <div className="flex items-center gap-2">
                  <span className="text-purple-400">📊 TRG:</span>
                  <span className="text-white">{bestResult.config.trg}</span>
                </div>
              )}
              {bestResult.config.tp && (
                <div className="flex items-center gap-2">
                  <span className="text-green-400">🎯 TP:</span>
                  <span className="text-white">{bestResult.config.tp}</span>
                </div>
              )}
              {bestResult.config.sl && (
                <div className="flex items-center gap-2">
                  <span className="text-red-400">🛡️ SL:</span>
                  <span className="text-white">{bestResult.config.sl}</span>
                </div>
              )}
              {bestResult.config.filters && (
                <div className="flex items-center gap-2">
                  <span className="text-blue-400">🔍 Фильтры:</span>
                  <span className="text-white">
                    {Array.isArray(bestResult.config.filters) 
                      ? bestResult.config.filters.join(', ') 
                      : bestResult.config.filters}
                  </span>
                </div>
              )}
              {bestResult.config.reentry !== undefined && (
                <div className="flex items-center gap-2">
                  <span className="text-yellow-400">🔄 Перезаход:</span>
                  <span className="text-white">{bestResult.config.reentry ? 'Да' : 'Нет'}</span>
                </div>
              )}
            </div>
          )}

          {!optimizing && (
            <button
              onClick={applyBestResult}
              className="w-full mt-2 py-2 bg-green-600 hover:bg-green-700 text-white rounded text-sm font-medium"
            >
              ✅ Применить лучшие параметры
            </button>
          )}
        </div>
      )}

      {results.length > 0 && (
        <div className="max-h-32 overflow-auto text-xs font-mono bg-gray-800/50 rounded p-2">
          {results.slice(-10).map((r, i) => (
            <div 
              key={i} 
              className={`py-0.5 ${r.is_best ? 'text-green-400' : 'text-gray-500'}`}
            >
              #{r.n} {r.params}: {r.profit?.toFixed(2)}% WR:{r.win_rate?.toFixed(0)}%
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        {!optimizing ? (
          <button
            onClick={startOptimization}
            className="flex-1 py-3 bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white rounded-lg font-bold text-sm flex items-center justify-center gap-2"
          >
            🚀 Запустить оптимизацию
          </button>
        ) : (
          <button
            onClick={stopOptimization}
            className="flex-1 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-bold text-sm"
          >
            ⏹️ Остановить
          </button>
        )}
      </div>
    </div>
  );
};

export default AutoOptimizePanel;
