import React from 'react';

const MonthlyPanel = ({ monthly }) => {
  if (!monthly || typeof monthly !== 'object' || Object.keys(monthly).length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <div className="text-4xl mb-2">📅</div>
        <div>Нет данных по месяцам</div>
        <div className="text-xs mt-1">Запустите расчёт для отображения помесячной статистики</div>
      </div>
    );
  }

  const months = Object.entries(monthly).sort((a, b) => a[0].localeCompare(b[0]));

  if (months.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        Нет данных по месяцам
      </div>
    );
  }

  const profitableMonths = months.filter(([_, d]) => (d?.pnl ?? 0) >= 0).length;
  const losingMonths = months.filter(([_, d]) => (d?.pnl ?? 0) < 0).length;
  const winRateMonthly = months.length > 0 
    ? ((profitableMonths / months.length) * 100).toFixed(0) 
    : 0;

  return (
    <div className="p-4">
      <div className="grid grid-cols-4 lg:grid-cols-6 gap-2">
        {months.map(([month, data]) => {
          const safeData = {
            trades: data?.trades ?? 0,
            wins: data?.wins ?? 0,
            losses: data?.losses ?? 0,
            pnl: data?.pnl ?? 0,
            tp1_hits: data?.tp1_hits ?? 0,
            tp2_hits: data?.tp2_hits ?? 0,
            tp3_hits: data?.tp3_hits ?? 0,
            tp4_hits: data?.tp4_hits ?? 0,
          };

          const winRate = safeData.trades > 0 
            ? ((safeData.wins / safeData.trades) * 100).toFixed(0) 
            : 0;
          const isProfit = safeData.pnl >= 0;
          
          return (
            <div 
              key={month}
              className={`p-3 rounded-lg ${
                isProfit 
                  ? 'bg-green-900/30 border border-green-500/30' 
                  : 'bg-red-900/30 border border-red-500/30'
              }`}
            >
              <div className="text-xs text-gray-400 mb-1">{month}</div>
              <div className={`text-lg font-bold ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
                {isProfit ? '+' : ''}{safeData.pnl.toFixed(2)}%
              </div>
              <div className="flex justify-between text-xs mt-1">
                <span className="text-gray-400">{safeData.trades} trades</span>
                <span className={Number(winRate) >= 50 ? 'text-green-400' : 'text-red-400'}>
                  {winRate}%
                </span>
              </div>
              <div className="flex gap-1 mt-1 text-xs">
                <span className="text-green-400">{safeData.wins}W</span>
                <span className="text-red-400">{safeData.losses}L</span>
              </div>
              <div className="flex gap-1 mt-2">
                {[1, 2, 3, 4].map(tp => (
                  <div 
                    key={tp}
                    className="flex-1 text-center text-xs bg-gray-700/50 rounded py-0.5"
                    title={`TP${tp} hits`}
                  >
                    {safeData[`tp${tp}_hits`] || 0}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 p-3 bg-gray-700/30 rounded-lg">
        <div className="grid grid-cols-4 gap-4 text-center">
          <div>
            <div className="text-xl font-bold text-white">{months.length}</div>
            <div className="text-xs text-gray-400">Месяцев</div>
          </div>
          <div>
            <div className="text-xl font-bold text-green-400">{profitableMonths}</div>
            <div className="text-xs text-gray-400">Прибыльных</div>
          </div>
          <div>
            <div className="text-xl font-bold text-red-400">{losingMonths}</div>
            <div className="text-xs text-gray-400">Убыточных</div>
          </div>
          <div>
            <div className="text-xl font-bold text-purple-400">{winRateMonthly}%</div>
            <div className="text-xs text-gray-400">Win Rate</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MonthlyPanel;
