/**
 * FilterStats.jsx
 * ================
 * Display filter performance statistics.
 * 
 * Shows:
 * - Total signals processed
 * - Signals blocked/passed
 * - Block rate percentage
 * - Per-filter breakdown
 * - Top blocking filters
 * 
 * Chat #44: Filters UI
 * Author: KOMAS Team
 * Version: 4.0
 */

import { useState } from 'react';

export default function FilterStats({ stats, botId }) {
  const [showDetails, setShowDetails] = useState(false);
  
  if (!stats) {
    return null;
  }
  
  const {
    filter_count = 0,
    enabled_count = 0,
    statistics = {},
    log_entries = 0,
  } = stats;
  
  // Calculate totals from statistics
  const totalChecked = Object.values(statistics).reduce(
    (sum, s) => sum + (s.total_checks || 0), 0
  );
  const totalBlocked = Object.values(statistics).reduce(
    (sum, s) => sum + (s.blocked || 0), 0
  );
  const totalPassed = totalChecked - totalBlocked;
  const blockRate = totalChecked > 0 
    ? ((totalBlocked / totalChecked) * 100).toFixed(1) 
    : 0;
  
  // Get top blocking filters
  const topBlockers = Object.entries(statistics)
    .filter(([_, s]) => s.blocked > 0)
    .sort((a, b) => b[1].blocked - a[1].blocked)
    .slice(0, 5);
  
  // Format filter name
  const formatName = (name) => {
    return name
      .replace(/_/g, ' ')
      .replace(/filter$/i, '')
      .split(' ')
      .map(w => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ')
      .trim();
  };
  
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-300">
          Filter Statistics
        </h3>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
        >
          {showDetails ? 'Hide Details' : 'Show Details'}
        </button>
      </div>
      
      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard
          label="Active Filters"
          value={enabled_count}
          total={filter_count}
          color="blue"
        />
        <StatCard
          label="Signals Checked"
          value={totalChecked}
          color="gray"
        />
        <StatCard
          label="Signals Passed"
          value={totalPassed}
          color="green"
        />
        <StatCard
          label="Block Rate"
          value={`${blockRate}%`}
          color={blockRate > 50 ? 'yellow' : blockRate > 80 ? 'red' : 'green'}
        />
      </div>
      
      {/* Detailed Breakdown */}
      {showDetails && (
        <div className="mt-4 space-y-4">
          {/* Top Blockers */}
          {topBlockers.length > 0 && (
            <div className="bg-gray-900/50 rounded-lg p-3">
              <h4 className="text-xs font-medium text-gray-400 mb-2">
                Top Blocking Filters
              </h4>
              <div className="space-y-2">
                {topBlockers.map(([name, filterStats]) => {
                  const blockPct = filterStats.total_checks > 0
                    ? ((filterStats.blocked / filterStats.total_checks) * 100).toFixed(1)
                    : 0;
                  
                  return (
                    <div key={name} className="flex items-center gap-2">
                      <div className="flex-1">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-300">
                            {formatName(name)}
                          </span>
                          <span className="text-red-400">
                            {filterStats.blocked} blocked
                          </span>
                        </div>
                        <div className="mt-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-red-500 rounded-full transition-all duration-500"
                            style={{ width: `${Math.min(blockPct, 100)}%` }}
                          />
                        </div>
                      </div>
                      <span className="text-xs text-gray-500 w-12 text-right">
                        {blockPct}%
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
          
          {/* All Filters Stats */}
          <div className="bg-gray-900/50 rounded-lg p-3">
            <h4 className="text-xs font-medium text-gray-400 mb-2">
              All Filter Statistics
            </h4>
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="text-gray-500">
                  <tr>
                    <th className="text-left pb-2">Filter</th>
                    <th className="text-right pb-2">Checks</th>
                    <th className="text-right pb-2">Passed</th>
                    <th className="text-right pb-2">Blocked</th>
                    <th className="text-right pb-2">Pass Rate</th>
                  </tr>
                </thead>
                <tbody className="text-gray-300">
                  {Object.entries(statistics).length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-4 text-center text-gray-500">
                        No filter statistics yet
                      </td>
                    </tr>
                  ) : (
                    Object.entries(statistics).map(([name, s]) => {
                      const passRate = s.total_checks > 0
                        ? (((s.total_checks - s.blocked) / s.total_checks) * 100).toFixed(1)
                        : 100;
                      
                      return (
                        <tr key={name} className="border-t border-gray-700/50">
                          <td className="py-2 text-gray-300">
                            {formatName(name)}
                          </td>
                          <td className="py-2 text-right text-gray-400">
                            {s.total_checks || 0}
                          </td>
                          <td className="py-2 text-right text-green-400">
                            {(s.total_checks || 0) - (s.blocked || 0)}
                          </td>
                          <td className="py-2 text-right text-red-400">
                            {s.blocked || 0}
                          </td>
                          <td className={`py-2 text-right ${
                            passRate >= 80 ? 'text-green-400' :
                            passRate >= 50 ? 'text-yellow-400' :
                            'text-red-400'
                          }`}>
                            {passRate}%
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
          </div>
          
          {/* Log Entries Count */}
          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Decision log entries: {log_entries}</span>
            <span>Last updated: just now</span>
          </div>
        </div>
      )}
    </div>
  );
}

// Stat card component
function StatCard({ label, value, total, color = 'gray' }) {
  const colorClasses = {
    blue: 'text-blue-400',
    green: 'text-green-400',
    yellow: 'text-yellow-400',
    red: 'text-red-400',
    gray: 'text-gray-300',
  };
  
  return (
    <div className="bg-gray-900/50 rounded-lg p-3">
      <div className="text-xs text-gray-500 mb-1">{label}</div>
      <div className={`text-lg font-semibold ${colorClasses[color] || colorClasses.gray}`}>
        {value}
        {total !== undefined && (
          <span className="text-gray-500 text-sm font-normal">
            /{total}
          </span>
        )}
      </div>
    </div>
  );
}
