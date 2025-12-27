import React, { useState } from 'react';

const HeatmapPanel = ({ data, loading, onGenerate }) => {
  const [i1Range, setI1Range] = useState({ min: 20, max: 80, step: 5 });
  const [i2Range, setI2Range] = useState({ min: 2, max: 8, step: 0.5 });

  if (!data && !loading) {
    return (
      <div className="p-4">
        <div className="mb-4 grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-300">i1 (ATR Length)</h4>
            <div className="flex gap-2">
              <input
                type="number"
                value={i1Range.min}
                onChange={(e) => setI1Range({...i1Range, min: parseInt(e.target.value) || 0})}
                className="w-16 bg-gray-700 text-white text-xs rounded px-2 py-1"
                placeholder="Min"
              />
              <input
                type="number"
                value={i1Range.max}
                onChange={(e) => setI1Range({...i1Range, max: parseInt(e.target.value) || 0})}
                className="w-16 bg-gray-700 text-white text-xs rounded px-2 py-1"
                placeholder="Max"
              />
              <input
                type="number"
                value={i1Range.step}
                onChange={(e) => setI1Range({...i1Range, step: parseInt(e.target.value) || 1})}
                className="w-16 bg-gray-700 text-white text-xs rounded px-2 py-1"
                placeholder="Step"
              />
            </div>
          </div>
          <div className="space-y-2">
            <h4 className="text-sm font-medium text-gray-300">i2 (Multiplier)</h4>
            <div className="flex gap-2">
              <input
                type="number"
                value={i2Range.min}
                onChange={(e) => setI2Range({...i2Range, min: parseFloat(e.target.value) || 0})}
                className="w-16 bg-gray-700 text-white text-xs rounded px-2 py-1"
                placeholder="Min"
                step="0.5"
              />
              <input
                type="number"
                value={i2Range.max}
                onChange={(e) => setI2Range({...i2Range, max: parseFloat(e.target.value) || 0})}
                className="w-16 bg-gray-700 text-white text-xs rounded px-2 py-1"
                placeholder="Max"
                step="0.5"
              />
              <input
                type="number"
                value={i2Range.step}
                onChange={(e) => setI2Range({...i2Range, step: parseFloat(e.target.value) || 0.5})}
                className="w-16 bg-gray-700 text-white text-xs rounded px-2 py-1"
                placeholder="Step"
                step="0.5"
              />
            </div>
          </div>
        </div>
        <button
          onClick={() => onGenerate?.(i1Range, i2Range)}
          className="w-full bg-purple-600 hover:bg-purple-700 text-white py-2 rounded font-medium"
        >
          🔥 Сгенерировать Heatmap
        </button>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="p-4 text-center">
        <div className="animate-spin w-8 h-8 border-4 border-purple-500 border-t-transparent rounded-full mx-auto mb-2"></div>
        <div className="text-gray-400">Генерация heatmap...</div>
      </div>
    );
  }

  if (!data || !data.matrix || !Array.isArray(data.matrix)) {
    return (
      <div className="p-4 text-center text-gray-500">
        <div className="text-4xl mb-2">🗺️</div>
        <div>Нет данных для heatmap</div>
      </div>
    );
  }

  const allValues = data.matrix.flat().filter(v => v !== null && v !== undefined && !isNaN(v));
  
  if (allValues.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        Нет данных для отображения heatmap
      </div>
    );
  }

  const minVal = Math.min(...allValues);
  const maxVal = Math.max(...allValues);

  const getColor = (value) => {
    if (value === null || value === undefined) return 'bg-gray-800';
    if (value < 0) {
      const intensity = Math.abs(value / (minVal || 1));
      return `rgba(239, 68, 68, ${0.3 + Math.min(intensity, 1) * 0.7})`;
    } else {
      const intensity = value / (maxVal || 1);
      return `rgba(34, 197, 94, ${0.3 + Math.min(intensity, 1) * 0.7})`;
    }
  };

  const formatValue = (value) => {
    if (value === null || value === undefined) return '-';
    return `${value >= 0 ? '+' : ''}${Number(value).toFixed(0)}`;
  };

  return (
    <div className="p-4">
      <div className="overflow-auto">
        <table className="w-full text-xs">
          <thead>
            <tr>
              <th className="p-1 text-gray-500">i1 \ i2</th>
              {data.i2_values?.map(i2 => (
                <th key={i2} className="p-1 text-gray-400">{i2}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.matrix?.map((row, i1Idx) => (
              <tr key={i1Idx}>
                <td className="p-1 text-gray-400 font-medium">{data.i1_values?.[i1Idx]}</td>
                {row.map((value, i2Idx) => (
                  <td 
                    key={i2Idx}
                    className="p-1 text-center text-white font-bold"
                    style={{ backgroundColor: getColor(value) }}
                    title={`i1=${data.i1_values?.[i1Idx]}, i2=${data.i2_values?.[i2Idx]}: ${value !== null ? value.toFixed(2) : '-'}%`}
                  >
                    {formatValue(value)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {data.best && (
        <div className="mt-4 p-3 bg-green-900/30 border border-green-500/30 rounded-lg">
          <h4 className="text-green-400 font-bold text-sm mb-2">🏆 Лучший результат</h4>
          <div className="grid grid-cols-4 gap-2 text-sm">
            <div>
              <span className="text-gray-400">i1:</span>
              <span className="text-white ml-1">{data.best.i1}</span>
            </div>
            <div>
              <span className="text-gray-400">i2:</span>
              <span className="text-white ml-1">{data.best.i2}</span>
            </div>
            <div>
              <span className="text-gray-400">Profit:</span>
              <span className="text-green-400 ml-1">+{data.best.profit?.toFixed(2) ?? '0.00'}%</span>
            </div>
            <div>
              <span className="text-gray-400">WinRate:</span>
              <span className="text-white ml-1">{data.best.win_rate?.toFixed(1) ?? '0.0'}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default HeatmapPanel;
