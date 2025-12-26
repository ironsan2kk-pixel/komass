/**
 * Heatmap Panel Component
 * =======================
 * Тепловая карта i1/i2 с кликабельными ячейками
 */
import { useState, useCallback } from 'react';
import { indicatorApi } from '../../api';

export default function HeatmapPanel({ settings, onApplyParams, addLog }) {
  // Heatmap config
  const [config, setConfig] = useState({
    i1_min: 20,
    i1_max: 80,
    i1_step: 5,
    i2_min: 2,
    i2_max: 8,
    i2_step: 1,
  });

  // State
  const [loading, setLoading] = useState(false);
  const [heatmapData, setHeatmapData] = useState(null);
  const [hoveredCell, setHoveredCell] = useState(null);

  // Generate heatmap
  const generateHeatmap = useCallback(async () => {
    setLoading(true);
    addLog('🗺️ Генерация heatmap...', 'info');

    try {
      const res = await indicatorApi.heatmap({
        ...settings,
        ...config,
      });

      if (res.data?.success) {
        setHeatmapData(res.data);
        addLog(`✅ Heatmap готов: ${res.data.results?.length || 0} комбинаций`, 'success');
      } else {
        throw new Error(res.data?.detail || 'Ошибка генерации');
      }
    } catch (err) {
      addLog(`❌ Ошибка: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  }, [settings, config, addLog]);

  // Get color for cell
  const getCellColor = (value, min, max) => {
    if (value === null || value === undefined) return 'bg-gray-800';
    
    const range = max - min || 1;
    const normalized = (value - min) / range;
    
    if (value < 0) {
      // Red gradient for losses
      const intensity = Math.min(1, Math.abs(normalized));
      return `rgba(239, 68, 68, ${0.2 + intensity * 0.8})`;
    } else {
      // Green gradient for profits
      const intensity = Math.min(1, normalized);
      return `rgba(34, 197, 94, ${0.2 + intensity * 0.8})`;
    }
  };

  // Build matrix from results
  const buildMatrix = () => {
    if (!heatmapData?.results) return { matrix: [], i1Values: [], i2Values: [] };

    const i1Values = [];
    const i2Values = [];
    const resultMap = {};

    // Collect unique values and build map
    heatmapData.results.forEach(r => {
      if (!i1Values.includes(r.i1)) i1Values.push(r.i1);
      if (!i2Values.includes(r.i2)) i2Values.push(r.i2);
      resultMap[`${r.i1}-${r.i2}`] = r;
    });

    i1Values.sort((a, b) => a - b);
    i2Values.sort((a, b) => a - b);

    // Build matrix
    const matrix = i2Values.map(i2 => 
      i1Values.map(i1 => resultMap[`${i1}-${i2}`] || null)
    );

    return { matrix, i1Values, i2Values };
  };

  const { matrix, i1Values, i2Values } = buildMatrix();

  // Find min/max for color scaling
  const allValues = heatmapData?.results?.map(r => r.profit_pct) || [];
  const minValue = Math.min(...allValues, 0);
  const maxValue = Math.max(...allValues, 0);

  // Find best result
  const bestResult = heatmapData?.results?.reduce((best, r) => 
    !best || r.profit_pct > best.profit_pct ? r : best
  , null);

  return (
    <div className="space-y-4">
      {/* Config */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-bold">🗺️ Heatmap Configuration</h3>
          <button
            onClick={generateHeatmap}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 rounded-lg font-medium transition-colors"
          >
            {loading ? (
              <>
                <span className="animate-spin">⏳</span>
                Генерация...
              </>
            ) : (
              <>
                <span>🔥</span>
                Сгенерировать
              </>
            )}
          </button>
        </div>

        <div className="grid grid-cols-6 gap-4">
          <ConfigInput
            label="i1 Min"
            value={config.i1_min}
            onChange={(v) => setConfig(prev => ({ ...prev, i1_min: v }))}
            min={10}
            max={200}
          />
          <ConfigInput
            label="i1 Max"
            value={config.i1_max}
            onChange={(v) => setConfig(prev => ({ ...prev, i1_max: v }))}
            min={10}
            max={200}
          />
          <ConfigInput
            label="i1 Step"
            value={config.i1_step}
            onChange={(v) => setConfig(prev => ({ ...prev, i1_step: v }))}
            min={1}
            max={20}
          />
          <ConfigInput
            label="i2 Min"
            value={config.i2_min}
            onChange={(v) => setConfig(prev => ({ ...prev, i2_min: v }))}
            min={1}
            max={10}
          />
          <ConfigInput
            label="i2 Max"
            value={config.i2_max}
            onChange={(v) => setConfig(prev => ({ ...prev, i2_max: v }))}
            min={1}
            max={10}
          />
          <ConfigInput
            label="i2 Step"
            value={config.i2_step}
            onChange={(v) => setConfig(prev => ({ ...prev, i2_step: v }))}
            min={0.5}
            max={2}
            step={0.5}
          />
        </div>

        <div className="mt-3 text-xs text-gray-500">
          Комбинаций: ~{Math.ceil((config.i1_max - config.i1_min) / config.i1_step + 1) * 
            Math.ceil((config.i2_max - config.i2_min) / config.i2_step + 1)}
        </div>
      </div>

      {/* Heatmap */}
      {heatmapData && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
          <div className="flex items-start gap-6">
            {/* Matrix */}
            <div className="flex-1">
              <div className="flex">
                {/* Y-axis label */}
                <div className="w-12 flex flex-col items-center justify-center">
                  <span className="text-xs text-gray-400 transform -rotate-90 whitespace-nowrap">
                    i2 (Multiplier)
                  </span>
                </div>

                {/* Matrix container */}
                <div>
                  {/* X-axis labels */}
                  <div className="flex ml-8 mb-1">
                    {i1Values.map(i1 => (
                      <div key={i1} className="w-10 text-center text-xs text-gray-400">
                        {i1}
                      </div>
                    ))}
                  </div>

                  {/* Matrix rows */}
                  {matrix.map((row, rowIdx) => (
                    <div key={rowIdx} className="flex items-center">
                      {/* Y-axis label */}
                      <div className="w-8 text-right text-xs text-gray-400 pr-2">
                        {i2Values[rowIdx]}
                      </div>

                      {/* Cells */}
                      {row.map((cell, colIdx) => {
                        const isBest = bestResult && cell?.i1 === bestResult.i1 && cell?.i2 === bestResult.i2;
                        const isHovered = hoveredCell?.i1 === cell?.i1 && hoveredCell?.i2 === cell?.i2;
                        
                        return (
                          <div
                            key={colIdx}
                            className={`w-10 h-10 rounded cursor-pointer transition-all ${
                              isBest ? 'ring-2 ring-yellow-400' : ''
                            } ${isHovered ? 'ring-2 ring-white scale-110 z-10' : ''}`}
                            style={{
                              backgroundColor: cell ? getCellColor(cell.profit_pct, minValue, maxValue) : '#374151',
                            }}
                            onMouseEnter={() => setHoveredCell(cell)}
                            onMouseLeave={() => setHoveredCell(null)}
                            onClick={() => cell && onApplyParams({ i1: cell.i1, i2: cell.i2 })}
                            title={cell ? `i1=${cell.i1}, i2=${cell.i2}\nProfit: ${cell.profit_pct?.toFixed(2)}%\nTrades: ${cell.total_trades}` : 'No data'}
                          />
                        );
                      })}
                    </div>
                  ))}

                  {/* X-axis title */}
                  <div className="text-center text-xs text-gray-400 mt-2 ml-8">
                    i1 (ATR Length)
                  </div>
                </div>
              </div>
            </div>

            {/* Legend & Info */}
            <div className="w-64 space-y-4">
              {/* Hovered Cell Info */}
              {hoveredCell && (
                <div className="bg-gray-700/50 rounded-lg p-3">
                  <div className="text-sm font-medium mb-2">📍 Ячейка</div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">i1</span>
                      <span>{hoveredCell.i1}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">i2</span>
                      <span>{hoveredCell.i2}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Profit</span>
                      <span className={hoveredCell.profit_pct >= 0 ? 'text-green-400' : 'text-red-400'}>
                        {hoveredCell.profit_pct?.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Trades</span>
                      <span>{hoveredCell.total_trades}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Win Rate</span>
                      <span>{hoveredCell.win_rate?.toFixed(1)}%</span>
                    </div>
                  </div>
                  <button
                    onClick={() => onApplyParams({ i1: hoveredCell.i1, i2: hoveredCell.i2 })}
                    className="w-full mt-3 py-2 bg-blue-600 hover:bg-blue-500 rounded text-sm font-medium"
                  >
                    Применить
                  </button>
                </div>
              )}

              {/* Best Result */}
              {bestResult && (
                <div className="bg-gradient-to-br from-yellow-500/10 to-amber-500/10 border border-yellow-500/30 rounded-lg p-3">
                  <div className="text-sm font-medium text-yellow-400 mb-2">🏆 Лучший результат</div>
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-400">Параметры</span>
                      <span>i1={bestResult.i1}, i2={bestResult.i2}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Profit</span>
                      <span className="text-green-400 font-bold">
                        +{bestResult.profit_pct?.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-400">Win Rate</span>
                      <span>{bestResult.win_rate?.toFixed(1)}%</span>
                    </div>
                  </div>
                  <button
                    onClick={() => onApplyParams({ i1: bestResult.i1, i2: bestResult.i2 })}
                    className="w-full mt-3 py-2 bg-yellow-600 hover:bg-yellow-500 rounded text-sm font-medium"
                  >
                    Применить лучшие
                  </button>
                </div>
              )}

              {/* Legend */}
              <div className="bg-gray-700/50 rounded-lg p-3">
                <div className="text-sm font-medium mb-2">📊 Легенда</div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-3 rounded bg-gradient-to-r from-red-500 via-gray-600 to-green-500" />
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-1">
                  <span>{minValue.toFixed(1)}%</span>
                  <span>0%</span>
                  <span>{maxValue.toFixed(1)}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* No data placeholder */}
      {!heatmapData && !loading && (
        <div className="flex flex-col items-center justify-center h-64 text-gray-500">
          <span className="text-6xl mb-4">🗺️</span>
          <p>Настройте параметры и нажмите "Сгенерировать"</p>
        </div>
      )}
    </div>
  );
}

// Config Input Component
function ConfigInput({ label, value, onChange, min, max, step = 1 }) {
  return (
    <div>
      <label className="text-xs text-gray-400 block mb-1">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        min={min}
        max={max}
        step={step}
        className="w-full bg-gray-700 px-3 py-1.5 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
    </div>
  );
}
