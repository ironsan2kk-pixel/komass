/**
 * FilterCategory.jsx
 * ==================
 * Collapsible category component for grouping filters.
 * 
 * Features:
 * - Expandable/collapsible category section
 * - Shows count of enabled filters
 * - Color-coded by category
 * - Contains FilterCard components
 * 
 * Chat #44: Filters UI
 * Author: KOMAS Team
 * Version: 4.0
 */

import { useState } from 'react';
import FilterCard from './FilterCard';

// Color mapping for categories
const COLOR_CLASSES = {
  blue: {
    bg: 'bg-blue-900/20',
    border: 'border-blue-800/50',
    badge: 'bg-blue-600/30 text-blue-400',
    icon: 'text-blue-400',
  },
  yellow: {
    bg: 'bg-yellow-900/20',
    border: 'border-yellow-800/50',
    badge: 'bg-yellow-600/30 text-yellow-400',
    icon: 'text-yellow-400',
  },
  green: {
    bg: 'bg-green-900/20',
    border: 'border-green-800/50',
    badge: 'bg-green-600/30 text-green-400',
    icon: 'text-green-400',
  },
  purple: {
    bg: 'bg-purple-900/20',
    border: 'border-purple-800/50',
    badge: 'bg-purple-600/30 text-purple-400',
    icon: 'text-purple-400',
  },
  red: {
    bg: 'bg-red-900/20',
    border: 'border-red-800/50',
    badge: 'bg-red-600/30 text-red-400',
    icon: 'text-red-400',
  },
  gray: {
    bg: 'bg-gray-900/20',
    border: 'border-gray-800/50',
    badge: 'bg-gray-600/30 text-gray-400',
    icon: 'text-gray-400',
  },
};

export default function FilterCategory({
  category,
  displayName,
  description,
  icon,
  color = 'gray',
  filters = [],
  expanded = false,
  onToggleExpand,
  onToggleFilter,
  onUpdateParams,
  disabled = false,
}) {
  const [expandedFilters, setExpandedFilters] = useState([]);
  
  const colorClasses = COLOR_CLASSES[color] || COLOR_CLASSES.gray;
  
  // Count enabled filters
  const enabledCount = filters.filter(f => f.config?.enabled).length;
  const totalCount = filters.length;
  
  // Toggle individual filter expansion
  const handleToggleFilterExpand = (filterName) => {
    setExpandedFilters(prev =>
      prev.includes(filterName)
        ? prev.filter(f => f !== filterName)
        : [...prev, filterName]
    );
  };
  
  return (
    <div className={`${expanded ? colorClasses.bg : ''}`}>
      {/* Category Header */}
      <button
        onClick={onToggleExpand}
        className="w-full p-4 flex items-center justify-between hover:bg-gray-700/30 
                   transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className={`text-2xl ${colorClasses.icon}`}>
            {icon}
          </span>
          <div className="text-left">
            <h3 className="font-medium text-white">
              {displayName}
            </h3>
            {description && (
              <p className="text-xs text-gray-500 mt-0.5">
                {description}
              </p>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {/* Enabled count badge */}
          <span className={`px-2 py-0.5 rounded text-xs font-medium ${colorClasses.badge}`}>
            {enabledCount}/{totalCount}
          </span>
          
          {/* Expand/collapse arrow */}
          <span className={`text-gray-400 transition-transform duration-200 
                          ${expanded ? 'rotate-180' : ''}`}>
            ▼
          </span>
        </div>
      </button>
      
      {/* Filters List */}
      {expanded && (
        <div className="px-4 pb-4 space-y-2">
          {filters.length === 0 ? (
            <div className="text-center py-4 text-gray-500 text-sm">
              No filters available in this category
            </div>
          ) : (
            filters.map(filter => (
              <FilterCard
                key={filter.name}
                name={filter.name}
                description={filter.description}
                priority={filter.priority}
                configSchema={filter.config_schema || {}}
                enabled={filter.config?.enabled || false}
                params={filter.config?.params || {}}
                expanded={expandedFilters.includes(filter.name)}
                onToggle={(enabled) => onToggleFilter(filter.name, enabled)}
                onUpdateParams={(params) => onUpdateParams(filter.name, params)}
                onToggleExpand={() => handleToggleFilterExpand(filter.name)}
                disabled={disabled}
                color={color}
              />
            ))
          )}
        </div>
      )}
    </div>
  );
}
