/**
 * FilterCard.jsx
 * ===============
 * Individual filter card with toggle and parameter configuration.
 * 
 * Features:
 * - Enable/disable toggle switch
 * - Priority indicator
 * - Expandable parameters section
 * - Dynamic parameter inputs based on schema
 * 
 * Chat #44: Filters UI
 * Author: KOMAS Team
 * Version: 4.0
 */

import { useState, useCallback } from 'react';
import FilterParams from './FilterParams';

// Priority badge colors
const PRIORITY_COLORS = {
  HIGH: 'bg-red-600/20 text-red-400 border-red-600/30',
  MEDIUM: 'bg-yellow-600/20 text-yellow-400 border-yellow-600/30',
  LOW: 'bg-green-600/20 text-green-400 border-green-600/30',
};

// Priority labels
const PRIORITY_LABELS = {
  HIGH: 'High Priority',
  MEDIUM: 'Medium',
  LOW: 'Low Priority',
};

export default function FilterCard({
  name,
  description,
  priority = 'MEDIUM',
  configSchema = {},
  enabled = false,
  params = {},
  expanded = false,
  onToggle,
  onUpdateParams,
  onToggleExpand,
  disabled = false,
  color = 'gray',
}) {
  const [localParams, setLocalParams] = useState(params);
  
  // Format filter name for display
  const displayName = name
    .replace(/_/g, ' ')
    .replace(/filter$/i, '')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
    .trim();
  
  // Handle parameter change
  const handleParamChange = useCallback((paramName, value) => {
    const newParams = { ...localParams, [paramName]: value };
    setLocalParams(newParams);
    onUpdateParams(newParams);
  }, [localParams, onUpdateParams]);
  
  // Has configurable parameters?
  const hasParams = Object.keys(configSchema).length > 0;
  
  return (
    <div
      className={`rounded-lg border transition-all duration-200 ${
        enabled
          ? 'bg-gray-700/50 border-gray-600'
          : 'bg-gray-800/50 border-gray-700/50'
      }`}
    >
      {/* Filter Header */}
      <div className="p-3 flex items-center gap-3">
        {/* Toggle Switch */}
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={enabled}
            onChange={(e) => onToggle(e.target.checked)}
            disabled={disabled}
            className="sr-only peer"
          />
          <div className={`w-10 h-5 rounded-full peer transition-colors duration-200
                          ${enabled ? 'bg-blue-600' : 'bg-gray-600'}
                          peer-focus:ring-2 peer-focus:ring-blue-500/50
                          peer-disabled:opacity-50 peer-disabled:cursor-not-allowed
                          after:content-[''] after:absolute after:top-0.5 after:left-0.5
                          after:bg-white after:rounded-full after:h-4 after:w-4
                          after:transition-transform after:duration-200
                          ${enabled ? 'after:translate-x-5' : 'after:translate-x-0'}`}>
          </div>
        </label>
        
        {/* Filter Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className={`font-medium ${enabled ? 'text-white' : 'text-gray-400'}`}>
              {displayName}
            </span>
            
            {/* Priority badge */}
            <span className={`px-1.5 py-0.5 text-[10px] font-medium rounded border
                            ${PRIORITY_COLORS[priority] || PRIORITY_COLORS.MEDIUM}`}>
              {priority}
            </span>
          </div>
          
          {/* Description */}
          {description && (
            <p className="text-xs text-gray-500 mt-0.5 truncate">
              {description}
            </p>
          )}
        </div>
        
        {/* Expand button (if has params) */}
        {hasParams && (
          <button
            onClick={onToggleExpand}
            disabled={disabled}
            className={`p-1.5 rounded hover:bg-gray-600/50 transition-colors
                       ${expanded ? 'bg-gray-600/50' : ''}`}
            title="Configure parameters"
          >
            <svg
              className={`w-4 h-4 text-gray-400 transition-transform duration-200
                         ${expanded ? 'rotate-180' : ''}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
        )}
      </div>
      
      {/* Parameters Panel */}
      {expanded && hasParams && (
        <div className="border-t border-gray-700/50 p-3 bg-gray-900/30">
          <FilterParams
            schema={configSchema}
            values={localParams}
            onChange={handleParamChange}
            disabled={disabled || !enabled}
          />
        </div>
      )}
      
      {/* Status bar when enabled */}
      {enabled && (
        <div className="px-3 pb-2">
          <div className="flex items-center gap-2 text-xs">
            <span className="text-green-400">●</span>
            <span className="text-gray-500">Active</span>
            {hasParams && Object.keys(localParams).length > 0 && (
              <>
                <span className="text-gray-600">|</span>
                <span className="text-gray-500">
                  {Object.keys(localParams).length} params configured
                </span>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
