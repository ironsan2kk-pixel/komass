/**
 * Stats Panel Component
 * =====================
 * Панель статистики с метриками и accuracy
 */
export default function StatsPanel({ stats, accuracy }) {
  if (!stats) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-gray-500">
        <span className="text-6xl mb-4">📊</span>
        <p>Запустите расчёт чтобы увидеть статистику</p>
      </div>
    );
  }

  const mainStats = [
    { label: 'Всего сделок', value: stats.total_trades, color: 'text-white' },
    { label: 'Выигрышных', value: stats.winning_trades, color: 'text-green-400' },
    { label: 'Проигрышных', value: stats.losing_trades, color: 'text-red-400' },
    { label: 'Win Rate', value: `${stats.win_rate?.toFixed(2)}%`, color: 'text-blue-400' },
    { label: 'Profit Factor', value: stats.profit_factor?.toFixed(2), color: 'text-cyan-400' },
    { label: 'Макс. просадка', value: `${stats.max_drawdown?.toFixed(2)}%`, color: 'text-orange-400' },
    { label: 'Средняя прибыль', value: `${stats.avg_win?.toFixed(2)}%`, color: 'text-green-400' },
    { label: 'Средний убыток', value: `${stats.avg_loss?.toFixed(2)}%`, color: 'text-red-400' },
    { label: 'Начальный капитал', value: `$${stats.initial_capital?.toLocaleString()}`, color: 'text-gray-400' },
    { label: 'Конечный капитал', value: `$${stats.final_capital?.toLocaleString()}`, color: 'text-white' },
    { label: 'Прибыль', value: `${stats.profit_pct?.toFixed(2)}%`, color: stats.profit_pct >= 0 ? 'text-green-400' : 'text-red-400' },
    { label: 'Sharpe Ratio', value: stats.sharpe?.toFixed(2) || '-', color: 'text-purple-400' },
    { label: 'Recovery Factor', value: stats.recovery_factor?.toFixed(2) || '-', color: 'text-indigo-400' },
  ];

  return (
    <div className="space-y-6">
      {/* Main Stats Grid */}
      <div className="grid grid-cols-4 gap-4">
        {mainStats.map((stat, i) => (
          <div
            key={i}
            className="bg-gray-800/50 border border-gray-700 rounded-xl p-4"
          >
            <div className="text-xs text-gray-400 mb-1">{stat.label}</div>
            <div className={`text-xl font-bold ${stat.color}`}>
              {stat.value ?? '-'}
            </div>
          </div>
        ))}
      </div>

      {/* Accuracy Table */}
      {accuracy && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
          <h3 className="font-bold mb-4">🎯 Accuracy по периодам</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-gray-700">
                  <th className="text-left py-2">Период</th>
                  <th className="text-right py-2">Сделок</th>
                  <th className="text-right py-2">Win Rate</th>
                  <th className="text-right py-2">Avg Win</th>
                  <th className="text-right py-2">Avg Loss</th>
                  <th className="text-right py-2">PF</th>
                </tr>
              </thead>
              <tbody>
                {['last_5', 'last_10', 'last_20', 'last_50', 'last_100', 'total'].map(period => {
                  const data = accuracy[period];
                  if (!data) return null;
                  
                  const label = period === 'total' ? 'Всего' : `Последние ${period.split('_')[1]}`;
                  
                  return (
                    <tr key={period} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                      <td className="py-2">{label}</td>
                      <td className="text-right">{data.trades}</td>
                      <td className={`text-right font-medium ${data.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}`}>
                        {data.win_rate?.toFixed(1)}%
                      </td>
                      <td className="text-right text-green-400">{data.avg_win?.toFixed(2)}%</td>
                      <td className="text-right text-red-400">{data.avg_loss?.toFixed(2)}%</td>
                      <td className={`text-right font-medium ${data.profit_factor >= 1 ? 'text-green-400' : 'text-red-400'}`}>
                        {data.profit_factor?.toFixed(2)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TP Stats */}
      {stats.tp_stats && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
          <h3 className="font-bold mb-4">📈 Статистика по TP</h3>
          <div className="grid grid-cols-5 gap-3">
            {Object.entries(stats.tp_stats).map(([tp, data]) => (
              <div key={tp} className="bg-gray-700/50 rounded-lg p-3 text-center">
                <div className="text-sm text-gray-400 mb-1">{tp.toUpperCase()}</div>
                <div className="text-lg font-bold text-green-400">{data.hits || 0}</div>
                <div className="text-xs text-gray-500">{data.percent?.toFixed(1)}%</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Long/Short Stats */}
      <div className="grid grid-cols-2 gap-4">
        {/* Long Stats */}
        <div className="bg-gradient-to-br from-green-500/10 to-emerald-500/10 border border-green-500/30 rounded-xl p-4">
          <h3 className="font-bold text-green-400 mb-3">📈 Long Trades</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Всего</span>
              <span>{stats.long_trades || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Win Rate</span>
              <span className="text-green-400">{stats.long_win_rate?.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Прибыль</span>
              <span className={stats.long_profit >= 0 ? 'text-green-400' : 'text-red-400'}>
                {stats.long_profit?.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>

        {/* Short Stats */}
        <div className="bg-gradient-to-br from-red-500/10 to-rose-500/10 border border-red-500/30 rounded-xl p-4">
          <h3 className="font-bold text-red-400 mb-3">📉 Short Trades</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-400">Всего</span>
              <span>{stats.short_trades || 0}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Win Rate</span>
              <span className="text-green-400">{stats.short_win_rate?.toFixed(1)}%</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-400">Прибыль</span>
              <span className={stats.short_profit >= 0 ? 'text-green-400' : 'text-red-400'}>
                {stats.short_profit?.toFixed(2)}%
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
