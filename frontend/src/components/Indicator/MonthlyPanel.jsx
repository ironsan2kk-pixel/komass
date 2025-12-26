/**
 * Monthly Panel Component
 * =======================
 * Помесячная разбивка результатов
 */
export default function MonthlyPanel({ monthly }) {
  if (!monthly || monthly.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-gray-500">
        <span className="text-6xl mb-4">📅</span>
        <p>Нет данных по месяцам</p>
      </div>
    );
  }

  // Calculate summary
  const summary = {
    total: monthly.length,
    profitable: monthly.filter(m => m.pnl >= 0).length,
    unprofitable: monthly.filter(m => m.pnl < 0).length,
    totalPnl: monthly.reduce((sum, m) => sum + (m.pnl || 0), 0),
    avgPnl: monthly.reduce((sum, m) => sum + (m.pnl || 0), 0) / monthly.length,
    totalTrades: monthly.reduce((sum, m) => sum + (m.trades || 0), 0),
    avgWinRate: monthly.reduce((sum, m) => sum + (m.win_rate || 0), 0) / monthly.length,
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-6 gap-4">
        <SummaryCard label="Всего месяцев" value={summary.total} />
        <SummaryCard label="Прибыльных" value={summary.profitable} color="green" />
        <SummaryCard label="Убыточных" value={summary.unprofitable} color="red" />
        <SummaryCard 
          label="Общая прибыль" 
          value={`${summary.totalPnl >= 0 ? '+' : ''}${summary.totalPnl.toFixed(2)}%`}
          color={summary.totalPnl >= 0 ? 'green' : 'red'}
        />
        <SummaryCard 
          label="Средняя прибыль" 
          value={`${summary.avgPnl >= 0 ? '+' : ''}${summary.avgPnl.toFixed(2)}%`}
          color={summary.avgPnl >= 0 ? 'green' : 'red'}
        />
        <SummaryCard 
          label="Общий Win Rate" 
          value={`${summary.avgWinRate.toFixed(1)}%`}
          color={summary.avgWinRate >= 50 ? 'green' : 'orange'}
        />
      </div>

      {/* Monthly Grid */}
      <div className="grid grid-cols-4 gap-4">
        {monthly.map((m, i) => (
          <MonthCard key={i} data={m} />
        ))}
      </div>

      {/* TP Distribution */}
      {monthly.some(m => m.tp_hits) && (
        <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
          <h3 className="font-bold mb-4">📊 TP Distribution по месяцам</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-gray-700">
                  <th className="text-left py-2">Месяц</th>
                  <th className="text-right py-2">TP1</th>
                  <th className="text-right py-2">TP2</th>
                  <th className="text-right py-2">TP3</th>
                  <th className="text-right py-2">TP4</th>
                  <th className="text-right py-2">SL</th>
                </tr>
              </thead>
              <tbody>
                {monthly.map((m, i) => (
                  <tr key={i} className="border-b border-gray-700/50">
                    <td className="py-2">{m.month}</td>
                    <td className="text-right text-green-400">{m.tp_hits?.tp1 || 0}</td>
                    <td className="text-right text-green-400">{m.tp_hits?.tp2 || 0}</td>
                    <td className="text-right text-green-400">{m.tp_hits?.tp3 || 0}</td>
                    <td className="text-right text-green-400">{m.tp_hits?.tp4 || 0}</td>
                    <td className="text-right text-red-400">{m.sl_hits || 0}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// Month Card Component
function MonthCard({ data }) {
  const isProfit = data.pnl >= 0;
  
  return (
    <div 
      className={`rounded-xl border p-4 transition-all hover:scale-[1.02] ${
        isProfit 
          ? 'bg-gradient-to-br from-green-500/10 to-emerald-500/10 border-green-500/30' 
          : 'bg-gradient-to-br from-red-500/10 to-rose-500/10 border-red-500/30'
      }`}
    >
      {/* Month Header */}
      <div className="flex items-center justify-between mb-3">
        <span className="font-medium text-gray-300">{data.month}</span>
        <span className={`text-xs px-2 py-0.5 rounded ${
          isProfit ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
        }`}>
          {data.trades} сделок
        </span>
      </div>

      {/* PnL */}
      <div className={`text-2xl font-bold mb-2 ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
        {isProfit ? '+' : ''}{data.pnl?.toFixed(2)}%
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-gray-500">Win Rate</span>
          <div className={`font-medium ${data.win_rate >= 50 ? 'text-green-400' : 'text-red-400'}`}>
            {data.win_rate?.toFixed(1)}%
          </div>
        </div>
        <div>
          <span className="text-gray-500">PF</span>
          <div className={`font-medium ${data.profit_factor >= 1 ? 'text-green-400' : 'text-red-400'}`}>
            {data.profit_factor?.toFixed(2)}
          </div>
        </div>
      </div>

      {/* TP Hits Bar */}
      {data.tp_hits && (
        <div className="mt-3 flex gap-1">
          {['tp1', 'tp2', 'tp3', 'tp4'].map(tp => {
            const hits = data.tp_hits[tp] || 0;
            return (
              <div
                key={tp}
                className="flex-1 text-center"
                title={`${tp.toUpperCase()}: ${hits}`}
              >
                <div className="h-1 bg-gray-700 rounded-full overflow-hidden mb-1">
                  <div
                    className="h-full bg-green-500"
                    style={{ width: `${Math.min(100, (hits / data.trades) * 100)}%` }}
                  />
                </div>
                <span className="text-[10px] text-gray-500">{tp.toUpperCase()}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Summary Card Component
function SummaryCard({ label, value, color }) {
  const colors = {
    green: 'text-green-400',
    red: 'text-red-400',
    orange: 'text-orange-400',
    undefined: 'text-white',
  };
  
  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4">
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className={`text-xl font-bold ${colors[color] || 'text-white'}`}>
        {value}
      </div>
    </div>
  );
}
