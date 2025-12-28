/**
 * KOMAS Trading Server - Results Table Component
 * ===============================================
 * Sortable table for displaying preset optimization scores.
 * 
 * Features:
 * - Sortable columns (click header to sort)
 * - Selectable rows (checkbox)
 * - Grade badges with colors
 * - Responsive design
 * - Loading state
 * 
 * Chat #47: Preset Optimizer Results
 */

import React from 'react';
import { GradeBadge, GRADE_CONFIG } from './ResultsPanel';

/**
 * Column definitions
 */
const COLUMNS = [
  { key: 'rank', label: '#', sortable: true, width: 'w-12', align: 'text-center' },
  { key: 'preset_name', label: 'Preset', sortable: false, width: 'min-w-[180px]', align: 'text-left' },
  { key: 'indicator_type', label: 'Type', sortable: false, width: 'w-20', align: 'text-center' },
  { key: 'overall_score', label: 'Score', sortable: true, width: 'w-24', align: 'text-center' },
  { key: 'avg_pnl', label: 'Avg PnL%', sortable: true, width: 'w-24', align: 'text-right' },
  { key: 'avg_win_rate', label: 'Win Rate', sortable: true, width: 'w-24', align: 'text-right' },
  { key: 'avg_max_dd', label: 'Max DD', sortable: true, width: 'w-24', align: 'text-right' },
  { key: 'avg_sharpe', label: 'Sharpe', sortable: true, width: 'w-20', align: 'text-right' },
  { key: 'positive_ratio', label: 'Consistency', sortable: true, width: 'w-24', align: 'text-center' },
  { key: 'best_pair', label: 'Best Pair', sortable: false, width: 'w-28', align: 'text-center' },
];

/**
 * Sort indicator component
 */
const SortIndicator = ({ active, order }) => {
  if (!active) {
    return <span className="text-gray-600 ml-1">↕</span>;
  }
  return (
    <span className="text-blue-400 ml-1">
      {order === 'desc' ? '↓' : '↑'}
    </span>
  );
};

/**
 * Table header component
 */
const TableHeader = ({ columns, sortBy, sortOrder, onSort, showCheckbox, allSelected, onSelectAll }) => {
  return (
    <thead className="bg-gray-800/50 sticky top-0">
      <tr>
        {/* Checkbox column */}
        {showCheckbox && (
          <th className="w-10 px-2 py-3">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={onSelectAll}
              className="rounded bg-gray-700 border-gray-600 text-blue-500 
                focus:ring-blue-500 focus:ring-offset-gray-900"
            />
          </th>
        )}
        
        {/* Data columns */}
        {columns.map((col) => (
          <th
            key={col.key}
            className={`
              px-3 py-3 text-xs font-medium text-gray-400 uppercase tracking-wider
              ${col.width} ${col.align}
              ${col.sortable ? 'cursor-pointer hover:text-white select-none' : ''}
            `}
            onClick={() => col.sortable && onSort(col.key)}
          >
            <span className="inline-flex items-center">
              {col.label}
              {col.sortable && (
                <SortIndicator active={sortBy === col.key} order={sortOrder} />
              )}
            </span>
          </th>
        ))}
      </tr>
    </thead>
  );
};

/**
 * Format cell value based on column type
 */
const formatCellValue = (key, value, row) => {
  switch (key) {
    case 'rank':
      return value || '—';
    
    case 'preset_name':
      return (
        <div className="truncate max-w-[180px]" title={value}>
          <span className="text-white font-medium">{value || row.preset_id}</span>
        </div>
      );
    
    case 'indicator_type':
      return (
        <span className={`
          px-2 py-0.5 rounded text-xs font-medium uppercase
          ${value === 'trg' ? 'bg-blue-500/20 text-blue-400' : 'bg-purple-500/20 text-purple-400'}
        `}>
          {value || '?'}
        </span>
      );
    
    case 'overall_score':
      const grade = row.grade || calculateGrade(value);
      return <GradeBadge grade={grade} score={value} size="sm" />;
    
    case 'avg_pnl':
      const pnlValue = value || 0;
      return (
        <span className={pnlValue >= 0 ? 'text-green-400' : 'text-red-400'}>
          {pnlValue >= 0 ? '+' : ''}{pnlValue.toFixed(2)}%
        </span>
      );
    
    case 'avg_win_rate':
      const wr = (value || 0) * 100;
      return (
        <span className={wr >= 50 ? 'text-green-400' : 'text-yellow-400'}>
          {wr.toFixed(1)}%
        </span>
      );
    
    case 'avg_max_dd':
      const dd = Math.abs(value || 0);
      return (
        <span className={dd <= 15 ? 'text-green-400' : dd <= 25 ? 'text-yellow-400' : 'text-red-400'}>
          -{dd.toFixed(1)}%
        </span>
      );
    
    case 'avg_sharpe':
      const sr = value || 0;
      return (
        <span className={sr >= 1.5 ? 'text-green-400' : sr >= 1 ? 'text-yellow-400' : 'text-gray-400'}>
          {sr.toFixed(2)}
        </span>
      );
    
    case 'positive_ratio':
      const ratio = (value || 0) * 100;
      return (
        <div className="flex items-center gap-1">
          <div className="w-16 bg-gray-700 rounded-full h-2 overflow-hidden">
            <div 
              className={`h-full rounded-full ${ratio >= 70 ? 'bg-green-500' : ratio >= 50 ? 'bg-yellow-500' : 'bg-red-500'}`}
              style={{ width: `${ratio}%` }}
            />
          </div>
          <span className="text-xs text-gray-400">{ratio.toFixed(0)}%</span>
        </div>
      );
    
    case 'best_pair':
      return (
        <div className="text-xs">
          <div className="text-gray-300">{value || '—'}</div>
          <div className="text-green-400">
            +{(row.best_pnl || 0).toFixed(1)}%
          </div>
        </div>
      );
    
    default:
      return value?.toString() || '—';
  }
};

/**
 * Calculate grade from score
 */
function calculateGrade(score) {
  if (score >= 85) return 'A';
  if (score >= 70) return 'B';
  if (score >= 55) return 'C';
  if (score >= 40) return 'D';
  return 'F';
}

/**
 * Table row component
 */
const TableRow = ({ row, columns, isSelected, onSelect, showCheckbox, rank }) => {
  const grade = row.grade || calculateGrade(row.overall_score || 0);
  const gradeConfig = GRADE_CONFIG[grade] || GRADE_CONFIG.F;
  
  return (
    <tr 
      className={`
        border-b border-gray-800 hover:bg-gray-800/50 transition-colors
        ${isSelected ? 'bg-blue-500/10' : ''}
      `}
    >
      {/* Checkbox */}
      {showCheckbox && (
        <td className="px-2 py-3">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onSelect(row.preset_id)}
            className="rounded bg-gray-700 border-gray-600 text-blue-500 
              focus:ring-blue-500 focus:ring-offset-gray-900"
          />
        </td>
      )}
      
      {/* Data cells */}
      {columns.map((col) => (
        <td 
          key={col.key} 
          className={`px-3 py-3 text-sm ${col.align} ${col.key === 'rank' ? 'text-gray-500' : ''}`}
        >
          {col.key === 'rank' 
            ? formatCellValue(col.key, rank, row)
            : formatCellValue(col.key, row[col.key], row)
          }
        </td>
      ))}
    </tr>
  );
};

/**
 * Empty state component
 */
const EmptyState = ({ message = "No presets found" }) => (
  <tr>
    <td colSpan={COLUMNS.length + 1} className="px-4 py-12 text-center text-gray-500">
      <div className="flex flex-col items-center gap-2">
        <span className="text-4xl">📊</span>
        <span>{message}</span>
      </div>
    </td>
  </tr>
);

/**
 * Loading state component
 */
const LoadingState = () => (
  <tr>
    <td colSpan={COLUMNS.length + 1} className="px-4 py-12 text-center">
      <div className="flex items-center justify-center gap-2 text-gray-400">
        <div className="animate-spin h-5 w-5 border-2 border-blue-500 border-t-transparent rounded-full" />
        <span>Loading results...</span>
      </div>
    </td>
  </tr>
);

/**
 * Main Results Table Component
 */
const ResultsTable = ({
  scores = [],
  loading = false,
  selected = new Set(),
  onSelect,
  onSelectAll,
  sortBy = 'overall_score',
  sortOrder = 'desc',
  onSort,
  showCheckbox = true,
  startRank = 1
}) => {
  const allSelected = scores.length > 0 && scores.every(s => selected.has(s.preset_id));
  
  return (
    <div className="overflow-x-auto rounded-lg border border-gray-800">
      <table className="min-w-full divide-y divide-gray-800">
        <TableHeader
          columns={COLUMNS}
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSort={onSort}
          showCheckbox={showCheckbox}
          allSelected={allSelected}
          onSelectAll={onSelectAll}
        />
        
        <tbody className="bg-gray-900/50 divide-y divide-gray-800">
          {loading ? (
            <LoadingState />
          ) : scores.length === 0 ? (
            <EmptyState />
          ) : (
            scores.map((score, index) => (
              <TableRow
                key={score.preset_id || index}
                row={score}
                columns={COLUMNS}
                isSelected={selected.has(score.preset_id)}
                onSelect={onSelect}
                showCheckbox={showCheckbox}
                rank={startRank + index}
              />
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default ResultsTable;
export { COLUMNS, TableHeader, TableRow, formatCellValue };
