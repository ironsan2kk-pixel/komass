import React, { useState } from 'react';

const TradesTable = ({ trades }) => {
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('time');
  const [sortDesc, setSortDesc] = useState(true);

  if (!trades || !Array.isArray(trades) || trades.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <div className="text-4xl mb-2">📋</div>
        <div>Нет сделок для отображения</div>
        <div className="text-xs mt-1">Запустите расчёт для получения списка сделок</div>
      </div>
    );
  }

  let filteredTrades = [...trades];
  if (filter === 'long') filteredTrades = filteredTrades.filter(t => t?.type === 'long');
  if (filter === 'short') filteredTrades = filteredTrades.filter(t => t?.type === 'short');
  if (filter === 'win') filteredTrades = filteredTrades.filter(t => (t?.pnl ?? 0) > 0);
  if (filter === 'loss') filteredTrades = filteredTrades.filter(t => (t?.pnl ?? 0) < 0);
  if (filter === 'reentry') filteredTrades = filteredTrades.filter(t => t?.is_reentry);

  filteredTrades.sort((a, b) => {
    let aVal, bVal;
    if (sortBy === 'time') {
      aVal = new Date(a?.entry_time || 0).getTime();
      bVal = new Date(b?.entry_time || 0).getTime();
    } else if (sortBy === 'pnl') {
      aVal = a?.pnl ?? 0;
      bVal = b?.pnl ?? 0;
    } else if (sortBy === 'type') {
      aVal = a?.type || '';
      bVal = b?.type || '';
      return sortDesc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal);
    }
    return sortDesc ? bVal - aVal : aVal - bVal;
  });

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return '-';
      return d.toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit' }) + 
             ' ' + d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '-';
    }
  };

  const formatPrice = (price) => {
    if (price === null || price === undefined) return '-';
    return Number(price).toFixed(2);
  };

  const formatPnl = (pnl) => {
    if (pnl === null || pnl === undefined) return '-';
    const value = Number(pnl);
    return `${value >= 0 ? '+' : ''}${value.toFixed(2)}%`;
  };

  return (
    <div className="p-4">
      <div className="flex gap-2 mb-4 flex-wrap">
        {[
          { value: 'all', label: 'Все' },
          { value: 'long', label: '🟢 Long' },
          { value: 'short', label: '🔴 Short' },
          { value: 'win', label: '✅ Win' },
          { value: 'loss', label: '❌ Loss' },
          { value: 'reentry', label: '🔄 Re-entry' },
        ].map(f => (
          <button
            key={f.value}
            onClick={() => setFilter(f.value)}
            className={`px-3 py-1 text-xs rounded ${
              filter === f.value ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-400'
            }`}
          >
            {f.label}
          </button>
        ))}
        <span className="text-gray-500 text-xs self-center ml-2">
          {filteredTrades.length} / {trades.length}
        </span>
      </div>

      <div className="overflow-auto max-h-[500px] rounded-lg border border-gray-700">
        <table className="w-full text-xs">
          <thead className="sticky top-0 bg-gray-800">
            <tr className="text-gray-400 border-b border-gray-700">
              <th className="py-2 px-2 text-left">#</th>
              <th 
                className="py-2 px-2 text-left cursor-pointer hover:text-white"
                onClick={() => { setSortBy('type'); setSortDesc(!sortDesc); }}
              >
                Тип {sortBy === 'type' && (sortDesc ? '↓' : '↑')}
              </th>
              <th 
                className="py-2 px-2 text-left cursor-pointer hover:text-white"
                onClick={() => { setSortBy('time'); setSortDesc(!sortDesc); }}
              >
                Вход {sortBy === 'time' && (sortDesc ? '↓' : '↑')}
              </th>
              <th className="py-2 px-2 text-left">Выход</th>
              <th className="py-2 px-2 text-right">Цена входа</th>
              <th className="py-2 px-2 text-right">Цена выхода</th>
              <th className="py-2 px-2 text-center">TP</th>
              <th className="py-2 px-2 text-center">Причина</th>
              <th 
                className="py-2 px-2 text-right cursor-pointer hover:text-white"
                onClick={() => { setSortBy('pnl'); setSortDesc(!sortDesc); }}
              >
                PnL {sortBy === 'pnl' && (sortDesc ? '↓' : '↑')}
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredTrades.map((trade, idx) => {
              const originalIndex = trades.indexOf(trade);
              const pnl = trade?.pnl ?? 0;
              
              return (
                <tr 
                  key={idx}
                  className="border-b border-gray-700/50 hover:bg-gray-700/30"
                >
                  <td className="py-2 px-2 text-gray-500">{originalIndex + 1}</td>
                  <td className="py-2 px-2">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      trade?.type === 'long' ? 'bg-green-600' : 'bg-red-600'
                    }`}>
                      {trade?.type === 'long' ? '🟢 LONG' : '🔴 SHORT'}
                    </span>
                    {trade?.is_reentry && (
                      <span className="ml-1 text-yellow-400">🔄</span>
                    )}
                  </td>
                  <td className="py-2 px-2 text-gray-300">{formatDate(trade?.entry_time)}</td>
                  <td className="py-2 px-2 text-gray-300">{formatDate(trade?.exit_time)}</td>
                  <td className="py-2 px-2 text-right text-white">{formatPrice(trade?.entry_price)}</td>
                  <td className="py-2 px-2 text-right text-white">{formatPrice(trade?.exit_price)}</td>
                  <td className="py-2 px-2 text-center">
                    {trade?.tp_hit?.length > 0 ? (
                      <div className="flex gap-0.5 justify-center">
                        {trade.tp_hit.map(tp => (
                          <span 
                            key={tp}
                            className={`w-5 h-5 flex items-center justify-center rounded text-xs ${
                              tp === 1 ? 'bg-green-600' : 
                              tp === 2 ? 'bg-blue-600' : 
                              tp === 3 ? 'bg-purple-600' : 'bg-yellow-600'
                            }`}
                          >
                            {tp}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span className="text-gray-500">-</span>
                    )}
                  </td>
                  <td className="py-2 px-2 text-center">
                    <span className={`px-2 py-0.5 rounded text-xs ${
                      trade?.exit_reason === 'SL' ? 'bg-red-900 text-red-300' :
                      trade?.exit_reason?.startsWith('TP') ? 'bg-green-900 text-green-300' :
                      'bg-gray-700 text-gray-300'
                    }`}>
                      {trade?.exit_reason || '-'}
                    </span>
                  </td>
                  <td className={`py-2 px-2 text-right font-bold ${
                    pnl >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {formatPnl(pnl)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TradesTable;
