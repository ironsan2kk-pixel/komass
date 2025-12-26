/**
 * Trades Table Component
 * ======================
 * Таблица сделок с фильтрами
 */
import { useState, useMemo } from 'react';

const FILTERS = [
  { id: 'all', name: 'Все' },
  { id: 'long', name: 'Long' },
  { id: 'short', name: 'Short' },
  { id: 'win', name: 'Win' },
  { id: 'loss', name: 'Loss' },
  { id: 'reentry', name: 'Re-entry' },
];

export default function TradesTable({ trades }) {
  const [filter, setFilter] = useState('all');
  const [sortBy, setSortBy] = useState('time');
  const [sortDir, setSortDir] = useState('desc');

  const filteredTrades = useMemo(() => {
    if (!trades) return [];

    let result = [...trades];

    // Apply filter
    switch (filter) {
      case 'long':
        result = result.filter(t => t.type === 'long');
        break;
      case 'short':
        result = result.filter(t => t.type === 'short');
        break;
      case 'win':
        result = result.filter(t => t.pnl >= 0);
        break;
      case 'loss':
        result = result.filter(t => t.pnl < 0);
        break;
      case 'reentry':
        result = result.filter(t => t.is_reentry);
        break;
    }

    // Apply sort
    result.sort((a, b) => {
      let aVal, bVal;
      
      switch (sortBy) {
        case 'time':
          aVal = new Date(a.entry_time).getTime();
          bVal = new Date(b.entry_time).getTime();
          break;
        case 'type':
          aVal = a.type;
          bVal = b.type;
          break;
        case 'pnl':
          aVal = a.pnl;
          bVal = b.pnl;
          break;
        default:
          aVal = a[sortBy];
          bVal = b[sortBy];
      }

      if (sortDir === 'asc') {
        return aVal > bVal ? 1 : -1;
      }
      return aVal < bVal ? 1 : -1;
    });

    return result;
  }, [trades, filter, sortBy, sortDir]);

  const toggleSort = (column) => {
    if (sortBy === column) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortDir('desc');
    }
  };

  if (!trades || trades.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-96 text-gray-500">
        <span className="text-6xl mb-4">📋</span>
        <p>Нет сделок для отображения</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center justify-between">
        <div className="flex gap-2">
          {FILTERS.map(f => (
            <button
              key={f.id}
              onClick={() => setFilter(f.id)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                filter === f.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-400 hover:text-white'
              }`}
            >
              {f.name}
            </button>
          ))}
        </div>
        
        <div className="text-sm text-gray-400">
          Показано: {filteredTrades.length} / {trades.length}
        </div>
      </div>

      {/* Table */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl overflow-hidden">
        <div className="overflow-x-auto max-h-[600px]">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-gray-800 z-10">
              <tr className="text-gray-400 border-b border-gray-700">
                <th className="text-left p-3">#</th>
                <th 
                  className="text-left p-3 cursor-pointer hover:text-white"
                  onClick={() => toggleSort('type')}
                >
                  Тип {sortBy === 'type' && (sortDir === 'asc' ? '↑' : '↓')}
                </th>
                <th 
                  className="text-left p-3 cursor-pointer hover:text-white"
                  onClick={() => toggleSort('time')}
                >
                  Вход {sortBy === 'time' && (sortDir === 'asc' ? '↑' : '↓')}
                </th>
                <th className="text-left p-3">Выход</th>
                <th className="text-right p-3">Цена входа</th>
                <th className="text-right p-3">Цена выхода</th>
                <th className="text-center p-3">TP</th>
                <th className="text-left p-3">Причина</th>
                <th 
                  className="text-right p-3 cursor-pointer hover:text-white"
                  onClick={() => toggleSort('pnl')}
                >
                  PnL {sortBy === 'pnl' && (sortDir === 'asc' ? '↑' : '↓')}
                </th>
              </tr>
            </thead>
            <tbody>
              {filteredTrades.map((trade, i) => (
                <tr 
                  key={i} 
                  className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors"
                >
                  <td className="p-3 text-gray-500">{i + 1}</td>
                  <td className="p-3">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium ${
                      trade.type === 'long' 
                        ? 'bg-green-500/20 text-green-400' 
                        : 'bg-red-500/20 text-red-400'
                    }`}>
                      {trade.type === 'long' ? '📈' : '📉'} {trade.type?.toUpperCase()}
                    </span>
                    {trade.is_reentry && (
                      <span className="ml-1 px-1.5 py-0.5 bg-yellow-500/20 text-yellow-400 rounded text-xs">
                        RE
                      </span>
                    )}
                  </td>
                  <td className="p-3 text-xs font-mono">
                    {formatDateTime(trade.entry_time)}
                  </td>
                  <td className="p-3 text-xs font-mono text-gray-400">
                    {formatDateTime(trade.exit_time)}
                  </td>
                  <td className="p-3 text-right font-mono">
                    {trade.entry_price?.toFixed(2)}
                  </td>
                  <td className="p-3 text-right font-mono text-gray-400">
                    {trade.exit_price?.toFixed(2)}
                  </td>
                  <td className="p-3 text-center">
                    {trade.tp_hit?.length > 0 ? (
                      <span className="text-green-400 text-xs">
                        {trade.tp_hit.join(', ')}
                      </span>
                    ) : '-'}
                  </td>
                  <td className="p-3">
                    <span className={`text-xs ${
                      trade.exit_reason === 'sl' 
                        ? 'text-red-400' 
                        : trade.exit_reason?.includes('tp')
                        ? 'text-green-400'
                        : 'text-gray-400'
                    }`}>
                      {formatExitReason(trade.exit_reason)}
                    </span>
                  </td>
                  <td className={`p-3 text-right font-bold ${
                    trade.pnl >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {trade.pnl >= 0 ? '+' : ''}{trade.pnl?.toFixed(2)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-4">
        <SummaryCard 
          label="Long Win Rate" 
          value={calculateWinRate(filteredTrades.filter(t => t.type === 'long'))}
          color="green"
        />
        <SummaryCard 
          label="Short Win Rate" 
          value={calculateWinRate(filteredTrades.filter(t => t.type === 'short'))}
          color="red"
        />
        <SummaryCard 
          label="Avg Win" 
          value={calculateAvgWin(filteredTrades)}
          color="green"
        />
        <SummaryCard 
          label="Avg Loss" 
          value={calculateAvgLoss(filteredTrades)}
          color="red"
        />
      </div>
    </div>
  );
}

// Helpers
function formatDateTime(dt) {
  if (!dt) return '-';
  const d = new Date(dt);
  return d.toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function formatExitReason(reason) {
  if (!reason) return '-';
  
  const map = {
    'sl': '🛑 Stop Loss',
    'tp1': '🎯 TP1',
    'tp2': '🎯 TP2',
    'tp3': '🎯 TP3',
    'tp4': '🎯 TP4',
    'signal': '📊 Signal',
    'trailing': '📈 Trailing',
  };
  
  return map[reason] || reason;
}

function calculateWinRate(trades) {
  if (!trades.length) return '-';
  const wins = trades.filter(t => t.pnl >= 0).length;
  return `${((wins / trades.length) * 100).toFixed(1)}%`;
}

function calculateAvgWin(trades) {
  const wins = trades.filter(t => t.pnl > 0);
  if (!wins.length) return '-';
  const avg = wins.reduce((sum, t) => sum + t.pnl, 0) / wins.length;
  return `+${avg.toFixed(2)}%`;
}

function calculateAvgLoss(trades) {
  const losses = trades.filter(t => t.pnl < 0);
  if (!losses.length) return '-';
  const avg = losses.reduce((sum, t) => sum + t.pnl, 0) / losses.length;
  return `${avg.toFixed(2)}%`;
}

function SummaryCard({ label, value, color }) {
  const colors = {
    green: 'text-green-400',
    red: 'text-red-400',
  };
  
  return (
    <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-3">
      <div className="text-xs text-gray-400">{label}</div>
      <div className={`text-lg font-bold ${colors[color]}`}>{value}</div>
    </div>
  );
}
