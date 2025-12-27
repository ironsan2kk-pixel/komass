import React from 'react';

const StatCard = ({ label, value, color = 'text-white', size = 'normal' }) => (
  <div className="bg-gray-700/50 rounded-lg p-2 text-center">
    <div className={`font-bold ${color} ${size === 'large' ? 'text-xl' : 'text-lg'}`}>
      {value ?? '-'}
    </div>
    <div className="text-xs text-gray-400">{label}</div>
  </div>
);

const TP_SYMBOLS = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩'];

const StatsPanel = ({ statistics, tpCount = 4 }) => {
  if (!statistics) {
    return (
      <div className="p-4 text-center text-gray-500">
        <div className="text-4xl mb-2">📊</div>
        <div>Запустите расчёт чтобы увидеть статистику</div>
      </div>
    );
  }

  const safeStats = {
    total_trades: statistics.total_trades ?? 0,
    win_rate: statistics.win_rate ?? 0,
    profit_factor: statistics.profit_factor ?? 0,
    max_drawdown: statistics.max_drawdown ?? 0,
    avg_win: statistics.avg_win ?? 0,
    avg_loss: statistics.avg_loss ?? 0,
    final_capital: statistics.final_capital ?? 0,
    profit_pct: statistics.profit_pct ?? statistics.final_profit_pct ?? 0,
    sharpe: statistics.sharpe ?? null,
    recovery_factor: statistics.recovery_factor ?? null,
    initial_capital: statistics.initial_capital ?? 10000,
    total_pnl: statistics.total_pnl ?? 0,
    long_wins: statistics.long_wins ?? 0,
    long_trades: statistics.long_trades ?? 0,
    long_win_rate: statistics.long_win_rate ?? 0,
    short_wins: statistics.short_wins ?? 0,
    short_trades: statistics.short_trades ?? 0,
    short_win_rate: statistics.short_win_rate ?? 0,
    reentry_wins: statistics.reentry_wins ?? 0,
    reentry_trades: statistics.reentry_trades ?? 0,
    reentry_win_rate: statistics.reentry_win_rate ?? 0,
    accuracy: statistics.accuracy ?? {},
    profit_panel: statistics.profit_panel ?? {},
  };

  const formatNumber = (num, decimals = 2) => {
    if (num === null || num === undefined || isNaN(num)) return '-';
    return Number(num).toFixed(decimals);
  };

  const formatCurrency = (num) => {
    if (num === null || num === undefined || isNaN(num)) return '-';
    return '$' + Number(num).toLocaleString('en-US', { maximumFractionDigits: 0 });
  };

  return (
    <div className="p-4 space-y-4">
      <div className="grid grid-cols-4 lg:grid-cols-8 gap-2">
        <StatCard label="Сделок" value={safeStats.total_trades} />
        <StatCard 
          label="Win Rate" 
          value={`${formatNumber(safeStats.win_rate, 1)}%`} 
          color={safeStats.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}
        />
        <StatCard 
          label="Profit Factor" 
          value={formatNumber(safeStats.profit_factor)} 
          color={safeStats.profit_factor >= 1.5 ? 'text-green-400' : safeStats.profit_factor >= 1 ? 'text-yellow-400' : 'text-red-400'}
        />
        <StatCard 
          label="Max DD" 
          value={`${formatNumber(safeStats.max_drawdown)}%`} 
          color="text-red-400"
        />
        <StatCard 
          label="Avg Win" 
          value={`${formatNumber(safeStats.avg_win)}%`} 
          color="text-green-400"
        />
        <StatCard 
          label="Avg Loss" 
          value={`${formatNumber(safeStats.avg_loss)}%`} 
          color="text-red-400"
        />
        <StatCard 
          label="Final Capital" 
          value={formatCurrency(safeStats.final_capital)} 
          color="text-purple-400"
          size="large"
        />
        <StatCard 
          label="Profit" 
          value={`${safeStats.profit_pct >= 0 ? '+' : ''}${formatNumber(safeStats.profit_pct)}%`} 
          color={safeStats.profit_pct >= 0 ? 'text-green-400' : 'text-red-400'}
          size="large"
        />
      </div>

      <div className="grid grid-cols-4 gap-2">
        <StatCard 
          label="Sharpe Ratio" 
          value={safeStats.sharpe !== null ? formatNumber(safeStats.sharpe) : '-'} 
          color="text-blue-400"
        />
        <StatCard 
          label="Recovery Factor" 
          value={safeStats.recovery_factor !== null ? formatNumber(safeStats.recovery_factor) : '-'} 
          color="text-cyan-400"
        />
        <StatCard 
          label="Initial Capital" 
          value={formatCurrency(safeStats.initial_capital)} 
          color="text-gray-400"
        />
        <StatCard 
          label="Total PnL" 
          value={formatCurrency(safeStats.total_pnl)} 
          color={safeStats.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}
        />
      </div>

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
                    {safeStats.accuracy?.[period]?.[`tp${i+1}`] ?? 0}%
                  </td>
                ))}
              </tr>
            ))}
            <tr className="bg-green-900/20 font-bold">
              <td className="py-1 text-green-400">Total</td>
              {Array.from({ length: tpCount }, (_, i) => (
                <td key={i} className="py-1 text-center text-white">
                  {safeStats.accuracy?.total?.[`tp${i+1}`] ?? 0}%
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>

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
                  {safeStats.profit_panel?.[`tp${i+1}`]?.winning ?? 0}/{safeStats.total_trades}
                </td>
              ))}
            </tr>
            <tr className="border-b border-gray-700/50">
              <td className="py-1 text-gray-400">Profit</td>
              {Array.from({ length: tpCount }, (_, i) => (
                <td key={i} className="py-1 text-center text-green-400">
                  +{safeStats.profit_panel?.[`tp${i+1}`]?.profit ?? 0}%
                </td>
              ))}
            </tr>
            <tr className="border-b border-gray-700/50">
              <td className="py-1 text-gray-400">Loss</td>
              {Array.from({ length: tpCount }, (_, i) => (
                <td key={i} className="py-1 text-center text-red-400">
                  {safeStats.profit_panel?.[`tp${i+1}`]?.loss ?? 0}%
                </td>
              ))}
            </tr>
            <tr className="bg-purple-900/20 font-bold">
              <td className="py-1 text-purple-400">Final</td>
              {Array.from({ length: tpCount }, (_, i) => {
                const final = safeStats.profit_panel?.[`tp${i+1}`]?.final ?? 0;
                return (
                  <td key={i} className={`py-1 text-center ${final >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {final >= 0 ? '+' : ''}{formatNumber(final)}%
                  </td>
                );
              })}
            </tr>
          </tbody>
        </table>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <div className="bg-green-900/20 rounded-lg p-3 text-center">
          <div className="text-green-400 text-xl font-bold">
            {safeStats.long_wins}/{safeStats.long_trades}
          </div>
          <div className="text-xs text-gray-400">Long ({formatNumber(safeStats.long_win_rate, 1)}%)</div>
        </div>
        <div className="bg-red-900/20 rounded-lg p-3 text-center">
          <div className="text-red-400 text-xl font-bold">
            {safeStats.short_wins}/{safeStats.short_trades}
          </div>
          <div className="text-xs text-gray-400">Short ({formatNumber(safeStats.short_win_rate, 1)}%)</div>
        </div>
        <div className="bg-yellow-900/20 rounded-lg p-3 text-center">
          <div className="text-yellow-400 text-xl font-bold">
            {safeStats.reentry_wins}/{safeStats.reentry_trades}
          </div>
          <div className="text-xs text-gray-400">Re-entry ({formatNumber(safeStats.reentry_win_rate, 1)}%)</div>
        </div>
      </div>
    </div>
  );
};

export default StatsPanel;
