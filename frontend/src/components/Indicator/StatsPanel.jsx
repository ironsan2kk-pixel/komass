/**
 * StatsPanel.jsx
 * ==============
 * Enhanced statistics panel with Signal Score grade breakdown.
 * 
 * Features:
 * - Existing stats (Win Rate, PF, DD, etc.)
 * - NEW: Grade distribution chart
 * - NEW: Win rate by grade
 * - NEW: Average PnL by grade
 * 
 * Chat #36: Score UI
 */

import React, { useMemo } from 'react';
import { GRADE_COLORS, GRADE_DESCRIPTIONS, getGradeFromScore } from './ScoreBadge';

const StatCard = ({ label, value, color = 'text-white', size = 'normal' }) => (
  <div className="bg-gray-700/50 rounded-lg p-2 text-center">
    <div className={`font-bold ${color} ${size === 'large' ? 'text-xl' : 'text-lg'}`}>
      {value}
    </div>
    <div className="text-xs text-gray-400">{label}</div>
  </div>
);

const TP_SYMBOLS = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩'];

const StatsPanel = ({ stats: statistics, trades, indicatorType, tpCount = 4, dataRange, cached }) => {
  // Calculate grade statistics from trades
  const gradeStats = useMemo(() => {
    if (!trades || !Array.isArray(trades) || trades.length === 0) {
      return null;
    }

    // Check if trades have score data
    const hasScoreData = trades.some(t => 
      t?.signal_score !== undefined || t?.signal_grade !== undefined
    );

    if (!hasScoreData) {
      return null;
    }

    const stats = {
      A: { count: 0, wins: 0, totalPnl: 0, trades: [] },
      B: { count: 0, wins: 0, totalPnl: 0, trades: [] },
      C: { count: 0, wins: 0, totalPnl: 0, trades: [] },
      D: { count: 0, wins: 0, totalPnl: 0, trades: [] },
      F: { count: 0, wins: 0, totalPnl: 0, trades: [] },
    };

    trades.forEach(trade => {
      const grade = trade?.signal_grade || 
        (trade?.signal_score !== undefined ? getGradeFromScore(trade.signal_score) : null);
      
      if (grade && stats[grade]) {
        stats[grade].count++;
        stats[grade].totalPnl += trade?.pnl || 0;
        stats[grade].trades.push(trade);
        
        if ((trade?.pnl || 0) > 0) {
          stats[grade].wins++;
        }
      }
    });

    // Calculate percentages and averages
    const total = trades.length;
    const result = {};
    
    Object.keys(stats).forEach(grade => {
      const s = stats[grade];
      result[grade] = {
        count: s.count,
        percentage: total > 0 ? ((s.count / total) * 100).toFixed(1) : '0.0',
        winRate: s.count > 0 ? ((s.wins / s.count) * 100).toFixed(1) : '0.0',
        avgPnl: s.count > 0 ? (s.totalPnl / s.count).toFixed(2) : '0.00',
        totalPnl: s.totalPnl.toFixed(2),
      };
    });

    return result;
  }, [trades]);

  // Calculate average score
  const avgScore = useMemo(() => {
    if (!trades || !Array.isArray(trades)) return null;
    
    const scoredTrades = trades.filter(t => t?.signal_score !== undefined);
    if (scoredTrades.length === 0) return null;
    
    const sum = scoredTrades.reduce((acc, t) => acc + t.signal_score, 0);
    return (sum / scoredTrades.length).toFixed(1);
  }, [trades]);

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

      {/* ========== NEW: Signal Score Statistics ========== */}
      {gradeStats && (
        <div className="bg-gray-700/30 rounded-lg p-3">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-cyan-400 font-bold text-sm">📊 Signal Score Statistics</h4>
            {avgScore && (
              <span className="text-sm text-gray-400">
                Avg Score: <span className="text-white font-bold">{avgScore}</span>
              </span>
            )}
          </div>
          
          {/* Grade Distribution Bar */}
          <div className="mb-4">
            <div className="flex h-6 rounded-lg overflow-hidden">
              {['A', 'B', 'C', 'D', 'F'].map(grade => {
                const stat = gradeStats[grade];
                const width = parseFloat(stat.percentage);
                if (width === 0) return null;
                
                return (
                  <div
                    key={grade}
                    className={`${GRADE_COLORS[grade].bg} flex items-center justify-center text-xs font-bold text-white transition-all`}
                    style={{ width: `${width}%` }}
                    title={`${grade}: ${stat.count} trades (${stat.percentage}%)`}
                  >
                    {width >= 10 && `${grade}: ${stat.percentage}%`}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Detailed Grade Table */}
          <table className="w-full text-xs">
            <thead>
              <tr className="text-gray-400 border-b border-gray-600">
                <th className="py-1 text-left">Grade</th>
                <th className="py-1 text-center">Trades</th>
                <th className="py-1 text-center">%</th>
                <th className="py-1 text-center">Win Rate</th>
                <th className="py-1 text-center">Avg PnL</th>
                <th className="py-1 text-center">Total PnL</th>
              </tr>
            </thead>
            <tbody>
              {['A', 'B', 'C', 'D', 'F'].map(grade => {
                const stat = gradeStats[grade];
                const colors = GRADE_COLORS[grade];
                const avgPnl = parseFloat(stat.avgPnl);
                const totalPnl = parseFloat(stat.totalPnl);
                
                return (
                  <tr key={grade} className="border-b border-gray-700/50">
                    <td className="py-1.5">
                      <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-bold ${colors.bg} ${colors.text}`}>
                        {grade}
                        <span className="opacity-70 font-normal text-[10px]">
                          {GRADE_DESCRIPTIONS[grade]}
                        </span>
                      </span>
                    </td>
                    <td className="py-1.5 text-center text-white">{stat.count}</td>
                    <td className="py-1.5 text-center text-gray-400">{stat.percentage}%</td>
                    <td className={`py-1.5 text-center font-bold ${
                      parseFloat(stat.winRate) >= 50 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {stat.winRate}%
                    </td>
                    <td className={`py-1.5 text-center ${
                      avgPnl >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {avgPnl >= 0 ? '+' : ''}{stat.avgPnl}%
                    </td>
                    <td className={`py-1.5 text-center font-bold ${
                      totalPnl >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {totalPnl >= 0 ? '+' : ''}{stat.totalPnl}%
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {/* Score Insight */}
          <div className="mt-3 pt-2 border-t border-gray-700 text-xs text-gray-500">
            <span className="text-gray-400">💡 Insight:</span> Higher grades (A, B) typically have better win rates. 
            Consider filtering signals by score ≥ C (55+) for improved results.
          </div>
        </div>
      )}

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
