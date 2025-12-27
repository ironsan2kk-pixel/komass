/**
 * TradesTable.jsx
 * ===============
 * Enhanced trades table with Signal Score integration.
 * 
 * Features:
 * - Score column with grade badges
 * - Filter by grade (All/A/B/C/D/F)
 * - Sort by score
 * - Score breakdown tooltip on hover
 * 
 * Chat #36: Score UI
 */

import React, { useState, useMemo } from 'react';
import ScoreBadge, { GRADE_COLORS, getGradeFromScore } from './ScoreBadge';

const TradesTable = ({ trades }) => {
  const [filter, setFilter] = useState('all');
  const [gradeFilter, setGradeFilter] = useState('all');
  const [sortBy, setSortBy] = useState('time');
  const [sortDesc, setSortDesc] = useState(true);

  // Check if trades have score data
  const hasScoreData = useMemo(() => {
    if (!trades || !Array.isArray(trades) || trades.length === 0) return false;
    return trades.some(t => t?.signal_score !== undefined || t?.signal_grade !== undefined);
  }, [trades]);

  // Calculate grade statistics
  const gradeStats = useMemo(() => {
    if (!trades || !Array.isArray(trades)) return {};
    
    const stats = { A: 0, B: 0, C: 0, D: 0, F: 0 };
    
    trades.forEach(trade => {
      const grade = trade?.signal_grade || 
        (trade?.signal_score !== undefined ? getGradeFromScore(trade.signal_score) : null);
      if (grade && stats[grade] !== undefined) {
        stats[grade]++;
      }
    });
    
    return stats;
  }, [trades]);

  if (!trades || !Array.isArray(trades) || trades.length === 0) {
    return (
      <div className="p-4 text-center text-gray-500">
        <div className="text-4xl mb-2">📋</div>
        <div>Нет сделок для отображения</div>
        <div className="text-xs mt-1">Запустите расчёт для получения списка сделок</div>
      </div>
    );
  }

  // Apply type/result filter
  let filteredTrades = [...trades];
  if (filter === 'long') filteredTrades = filteredTrades.filter(t => t?.type === 'long');
  if (filter === 'short') filteredTrades = filteredTrades.filter(t => t?.type === 'short');
  if (filter === 'win') filteredTrades = filteredTrades.filter(t => (t?.pnl ?? 0) > 0);
  if (filter === 'loss') filteredTrades = filteredTrades.filter(t => (t?.pnl ?? 0) < 0);
  if (filter === 'reentry') filteredTrades = filteredTrades.filter(t => t?.is_reentry);

  // Apply grade filter
  if (gradeFilter !== 'all' && hasScoreData) {
    filteredTrades = filteredTrades.filter(trade => {
      const grade = trade?.signal_grade || 
        (trade?.signal_score !== undefined ? getGradeFromScore(trade.signal_score) : null);
      return grade === gradeFilter;
    });
  }

  // Apply sorting
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
    } else if (sortBy === 'score') {
      aVal = a?.signal_score ?? -1;
      bVal = b?.signal_score ?? -1;
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
      {/* Type/Result Filters */}
      <div className="flex gap-2 mb-3 flex-wrap">
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
            className={`px-3 py-1 text-xs rounded transition-colors ${
              filter === f.value ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
            }`}
          >
            {f.label}
          </button>
        ))}
        <span className="text-gray-500 text-xs self-center ml-2">
          {filteredTrades.length} / {trades.length}
        </span>
      </div>

      {/* Grade Filters (only if score data exists) */}
      {hasScoreData && (
        <div className="flex gap-2 mb-4 flex-wrap items-center">
          <span className="text-gray-400 text-xs mr-1">📊 Score:</span>
          {[
            { value: 'all', label: 'Все', color: 'bg-gray-700' },
            { value: 'A', label: `A (${gradeStats.A || 0})`, color: GRADE_COLORS.A.bg },
            { value: 'B', label: `B (${gradeStats.B || 0})`, color: GRADE_COLORS.B.bg },
            { value: 'C', label: `C (${gradeStats.C || 0})`, color: GRADE_COLORS.C.bg },
            { value: 'D', label: `D (${gradeStats.D || 0})`, color: GRADE_COLORS.D.bg },
            { value: 'F', label: `F (${gradeStats.F || 0})`, color: GRADE_COLORS.F.bg },
          ].map(g => (
            <button
              key={g.value}
              onClick={() => setGradeFilter(g.value)}
              className={`px-2 py-0.5 text-xs rounded transition-all ${
                gradeFilter === g.value 
                  ? `${g.color} text-white ring-2 ring-white/30` 
                  : 'bg-gray-700/50 text-gray-400 hover:bg-gray-600'
              }`}
            >
              {g.label}
            </button>
          ))}
        </div>
      )}

      {/* Table */}
      <div className="overflow-auto max-h-[500px] rounded-lg border border-gray-700">
        <table className="w-full text-xs">
          <thead className="sticky top-0 bg-gray-800 z-10">
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
              {/* Score column - only show if data exists */}
              {hasScoreData && (
                <th 
                  className="py-2 px-2 text-center cursor-pointer hover:text-white"
                  onClick={() => { setSortBy('score'); setSortDesc(!sortDesc); }}
                  title="Signal Quality Score"
                >
                  Score {sortBy === 'score' && (sortDesc ? '↓' : '↑')}
                </th>
              )}
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
              
              // Get score and grade
              const score = trade?.signal_score;
              const grade = trade?.signal_grade || 
                (score !== undefined ? getGradeFromScore(score) : null);
              const components = trade?.score_components;
              
              return (
                <tr 
                  key={idx}
                  className="border-b border-gray-700/50 hover:bg-gray-700/30 transition-colors"
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
                  {/* Score cell */}
                  {hasScoreData && (
                    <td className="py-2 px-2 text-center">
                      <ScoreBadge 
                        score={score}
                        grade={grade}
                        components={components}
                        size="sm"
                        showScore={true}
                        showTooltip={!!components}
                      />
                    </td>
                  )}
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

      {/* Grade Legend (only if score data exists) */}
      {hasScoreData && (
        <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center gap-2">
            <span>Grade Scale:</span>
            <span className="text-green-400">A (85-100)</span>
            <span className="text-lime-400">B (70-84)</span>
            <span className="text-yellow-400">C (55-69)</span>
            <span className="text-orange-400">D (40-54)</span>
            <span className="text-red-400">F (0-39)</span>
          </div>
          <div>
            Hover over score for details
          </div>
        </div>
      )}
    </div>
  );
};

export default TradesTable;
