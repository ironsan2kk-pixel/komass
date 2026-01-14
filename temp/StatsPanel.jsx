import React from 'react';

const StatCard = ({ label, value, color = 'text-white', size = 'normal' }) => (
  <div className="bg-gray-700/50 rounded-lg p-2 text-center">
    <div className={`font-bold ${color} ${size === 'large' ? 'text-xl' : 'text-lg'}`}>
      {value}
    </div>
    <div className="text-xs text-gray-400">{label}</div>
  </div>
);

const TP_SYMBOLS = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩'];

const StatsPanel = ({ statistics, tpCount = 4, dataRange, cached }) => {
  if (!statistics) {
    return (
      <div className="p-4 text-center text-gray-500">
        Запустите расчёт чтобы увидеть статистику
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* Cache Status Banner */}
      {cached !== undefined && (
        <div className={`rounded-lg p-2 flex items-center justify-between ${
          cached 
            ? 'bg-blue-900/20 border border-blue-700/50' 
            : 'bg-green-900/20 border border-green-700/50'
        }`}>
          <span className={cached ? 'text-blue-400' : 'text-green-400'}>
            {cached ? '📦 Результат из кэша' : '🔄 Свежий расчёт'}
          </span>
          <span className="text-xs text-gray-400">
            {cached ? 'TTL: 5 мин' : 'Сохранено в кэш'}
          </span>
        </div>
      )}

      {/* Data Period Info */}
      {dataRange && (
        <div className="bg-purple-900/20 border border-purple-700/50 rounded-lg p-3 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <span className="text-purple-400 font-medium">📅 Период бэктеста:</span>
            <span className="text-white font-mono">
              {dataRange.used_start} — {dataRange.used_end}
            </span>
          </div>
          <div className="flex items-center gap-4 text-sm">
            <span className="text-gray-400">
              Использовано: <span className="text-purple-300 font-bold">{dataRange.used_candles?.toLocaleString()}</span> свечей
            </span>
            {dataRange.total_candles !== dataRange.used_candles && (
              <span className="text-gray-500">
                / {dataRange.total_candles?.toLocaleString()} доступно
              </span>
            )}
          </div>
        </div>
      )}

      {/* Main Stats Grid */}
      <div className="grid grid-cols-4 lg:grid-cols-8 gap-2">
        <StatCard label="Сделок" value={statistics.total_trades} />
        <StatCard 
          label="Win Rate" 
          value={`${statistics.win_rate}%`} 
          color={statistics.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}
        />
        <StatCard 
          label="Profit Factor" 
          value={statistics.profit_factor} 
          color={statistics.profit_factor >= 1.5 ? 'text-green-400' : statistics.profit_factor >= 1 ? 'text-yellow-400' : 'text-red-400'}
        />
        <StatCard 
          label="Max DD" 
          value={`${statistics.max_drawdown}%`} 
          color="text-red-400"
        />
        <StatCard 
          label="Avg Win" 
          value={`${statistics.avg_win}%`} 
          color="text-green-400"
        />
        <StatCard 
          label="Avg Loss" 
          value={`${statistics.avg_loss}%`} 
          color="text-red-400"
        />
        <StatCard 
          label="Final Capital" 
          value={`$${statistics.final_capital?.toLocaleString()}`} 
          color="text-purple-400"
          size="large"
        />
        <StatCard 
          label="Profit" 
          value={`${statistics.profit_pct >= 0 ? '+' : ''}${statistics.profit_pct}%`} 
          color={statistics.profit_pct >= 0 ? 'text-green-400' : 'text-red-400'}
          size="large"
        />
      </div>

      {/* Additional Stats */}
      <div className="grid grid-cols-4 gap-2">
        <StatCard 
          label="Sharpe Ratio" 
          value={statistics.sharpe || '-'} 
          color="text-blue-400"
        />
        <StatCard 
          label="Recovery Factor" 
          value={statistics.recovery_factor || '-'} 
          color="text-cyan-400"
        />
        <StatCard 
          label="Initial Capital" 
          value={`$${statistics.initial_capital?.toLocaleString()}`} 
          color="text-gray-400"
        />
        <StatCard 
          label="Total PnL" 
          value={`$${statistics.total_pnl?.toLocaleString()}`} 
          color={statistics.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}
        />
      </div>

      {/* Accuracy Breakdown */}
      <div className="bg-gray-700/30 rounded-lg p-3">
        <h4 className="text-green-400 font-bold text-sm mb-2">🎯 Strategy Accuracy</h4>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-gray-400 border-b border-gray-600">
              <th className="py-1 text-left">Period</th>
              {Array.from({ length: tpCount }, (_, i) => (
                <th key={i} className="py-1 text-center text-base">{TP_SYMBOLS[i]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {['last_5', 'last_10', 'last_20', 'last_50', 'last_100'].map(period => (
              <tr key={period} className="border-b border-gray-700/50">
                <td className="py-1 text-gray-400">Last {period.split('_')[1]}</td>
                {Array.from({ length: tpCount }, (_, i) => (
                  <td key={i} className="py-1 text-center text-white">
                    {statistics.accuracy?.[period]?.[`tp${i+1}`] || 0}%
                  </td>
                ))}
              </tr>
            ))}
            <tr className="bg-green-900/20 font-bold">
              <td className="py-1 text-green-400">Total</td>
              {Array.from({ length: tpCount }, (_, i) => (
                <td key={i} className="py-1 text-center text-white">
                  {statistics.accuracy?.total?.[`tp${i+1}`] || 0}%
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Profit Panel */}
      <div className="bg-gray-700/30 rounded-lg p-3">
        <h4 className="text-yellow-400 font-bold text-sm mb-2">💰 Profit Panel</h4>
        <table className="w-full text-xs">
          <thead>
            <tr className="text-gray-400 border-b border-gray-600">
              <th className="py-1 text-left"></th>
              {Array.from({ length: tpCount }, (_, i) => (
                <th key={i} className="py-1 text-center">TP{i+1}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-gray-700/50">
              <td className="py-1 text-gray-400">Winning</td>
              {Array.from({ length: tpCount }, (_, i) => (
                <td key={i} className="py-1 text-center text-white">
                  {statistics.profit_panel?.[`tp${i+1}`]?.winning || 0}/{statistics.total_trades}
                </td>
              ))}
            </tr>
            <tr className="border-b border-gray-700/50">
              <td className="py-1 text-gray-400">Profit</td>
              {Array.from({ length: tpCount }, (_, i) => (
                <td key={i} className="py-1 text-center text-green-400">
                  +{statistics.profit_panel?.[`tp${i+1}`]?.profit || 0}%
                </td>
              ))}
            </tr>
            <tr className="border-b border-gray-700/50">
              <td className="py-1 text-gray-400">Loss</td>
              {Array.from({ length: tpCount }, (_, i) => (
                <td key={i} className="py-1 text-center text-red-400">
                  {statistics.profit_panel?.[`tp${i+1}`]?.loss || 0}%
                </td>
              ))}
            </tr>
            <tr className="bg-purple-900/20 font-bold">
              <td className="py-1 text-purple-400">Final</td>
              {Array.from({ length: tpCount }, (_, i) => {
                const final = statistics.profit_panel?.[`tp${i+1}`]?.final || 0;
                return (
                  <td key={i} className={`py-1 text-center ${final >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {final >= 0 ? '+' : ''}{final}%
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>

      {/* Long/Short/Reentry Stats */}
      <div className="grid grid-cols-3 gap-2">
        <div className="bg-green-900/20 rounded-lg p-3 text-center">
          <div className="text-green-400 text-xl font-bold">
            {statistics.long_wins}/{statistics.long_trades}
          </div>
          <div className="text-xs text-gray-400">Long ({statistics.long_win_rate}%)</div>
        </div>
        <div className="bg-red-900/20 rounded-lg p-3 text-center">
          <div className="text-red-400 text-xl font-bold">
            {statistics.short_wins}/{statistics.short_trades}
          </div>
          <div className="text-xs text-gray-400">Short ({statistics.short_win_rate}%)</div>
        </div>
        <div className="bg-yellow-900/20 rounded-lg p-3 text-center">
          <div className="text-yellow-400 text-xl font-bold">
            {statistics.reentry_wins || 0}/{statistics.reentry_trades || 0}
          </div>
          <div className="text-xs text-gray-400">Re-entry ({statistics.reentry_win_rate || 0}%)</div>
        </div>
      </div>
    </div>
  );
};

export default StatsPanel;

