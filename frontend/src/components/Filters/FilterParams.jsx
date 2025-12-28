/**
 * FilterParams.jsx
 * =================
 * Dynamic parameter input component based on schema.
 * 
 * Supports various input types:
 * - number (with min/max/step)
 * - string (text input)
 * - boolean (checkbox)
 * - select (dropdown)
 * - array (multi-select for sessions, days, etc.)
 * 
 * Chat #44: Filters UI
 * Author: KOMAS Team
 * Version: 4.0
 */

import { useState, useCallback } from 'react';

// Session options for time filters
const SESSION_OPTIONS = [
  { value: 'asia', label: 'Asia (00:00-08:00 UTC)' },
  { value: 'europe', label: 'Europe (07:00-16:00 UTC)' },
  { value: 'us', label: 'US (13:00-22:00 UTC)' },
  { value: 'all', label: 'All Sessions' },
];

// Day options
const DAY_OPTIONS = [
  { value: 'monday', label: 'Monday' },
  { value: 'tuesday', label: 'Tuesday' },
  { value: 'wednesday', label: 'Wednesday' },
  { value: 'thursday', label: 'Thursday' },
  { value: 'friday', label: 'Friday' },
  { value: 'saturday', label: 'Saturday' },
  { value: 'sunday', label: 'Sunday' },
];

// Known array parameter options
const ARRAY_OPTIONS = {
  sessions: SESSION_OPTIONS,
  allowed_sessions: SESSION_OPTIONS,
  days: DAY_OPTIONS,
  allowed_days: DAY_OPTIONS,
  trading_days: DAY_OPTIONS,
};

export default function FilterParams({
  schema = {},
  values = {},
  onChange,
  disabled = false,
}) {
  // Get parameter entries from schema
  const params = Object.entries(schema).filter(
    ([key]) => !key.startsWith('_') && key !== 'type'
  );
  
  if (params.length === 0) {
    return (
      <div className="text-gray-500 text-sm text-center py-2">
        No configurable parameters
      </div>
    );
  }
  
  return (
    <div className="space-y-3">
      {params.map(([name, config]) => (
        <ParamInput
          key={name}
          name={name}
          config={config}
          value={values[name]}
          onChange={(value) => onChange(name, value)}
          disabled={disabled}
        />
      ))}
    </div>
  );
}

// Individual parameter input
function ParamInput({ name, config, value, onChange, disabled }) {
  const {
    type = 'string',
    default: defaultValue,
    description,
    minimum,
    maximum,
    enum: enumOptions,
    items,
  } = config;
  
  // Format name for display
  const displayName = name
    .replace(/_/g, ' ')
    .split(' ')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
  
  // Get current value or default
  const currentValue = value ?? defaultValue;
  
  // Render based on type
  const renderInput = () => {
    // Enum/select type
    if (enumOptions) {
      return (
        <select
          value={currentValue || ''}
          onChange={(e) => onChange(e.target.value)}
          disabled={disabled}
          className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-1.5
                     text-white text-sm focus:outline-none focus:border-blue-500
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {enumOptions.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      );
    }
    
    // Boolean type
    if (type === 'boolean') {
      return (
        <label className="relative inline-flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={currentValue || false}
            onChange={(e) => onChange(e.target.checked)}
            disabled={disabled}
            className="sr-only peer"
          />
          <div className={`w-9 h-5 rounded-full peer transition-colors duration-200
                          ${currentValue ? 'bg-blue-600' : 'bg-gray-600'}
                          peer-focus:ring-2 peer-focus:ring-blue-500/50
                          peer-disabled:opacity-50 peer-disabled:cursor-not-allowed
                          after:content-[''] after:absolute after:top-0.5 after:left-0.5
                          after:bg-white after:rounded-full after:h-4 after:w-4
                          after:transition-transform after:duration-200
                          ${currentValue ? 'after:translate-x-4' : 'after:translate-x-0'}`}>
          </div>
        </label>
      );
    }
    
    // Array type (multi-select)
    if (type === 'array' || ARRAY_OPTIONS[name]) {
      const options = ARRAY_OPTIONS[name] || [];
      const selectedValues = Array.isArray(currentValue) ? currentValue : [];
      
      return (
        <div className="flex flex-wrap gap-2">
          {options.map((opt) => (
            <button
              key={opt.value}
              type="button"
              onClick={() => {
                const newValues = selectedValues.includes(opt.value)
                  ? selectedValues.filter((v) => v !== opt.value)
                  : [...selectedValues, opt.value];
                onChange(newValues);
              }}
              disabled={disabled}
              className={`px-2 py-1 text-xs rounded border transition-colors
                         ${selectedValues.includes(opt.value)
                           ? 'bg-blue-600/30 border-blue-500 text-blue-300'
                           : 'bg-gray-700/30 border-gray-600 text-gray-400 hover:border-gray-500'
                         } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      );
    }
    
    // Number type
    if (type === 'number' || type === 'integer') {
      return (
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={currentValue ?? ''}
            onChange={(e) => {
              const val = e.target.value === '' ? undefined : Number(e.target.value);
              onChange(val);
            }}
            min={minimum}
            max={maximum}
            step={type === 'integer' ? 1 : 0.1}
            disabled={disabled}
            className="flex-1 bg-gray-800 border border-gray-600 rounded px-3 py-1.5
                       text-white text-sm focus:outline-none focus:border-blue-500
                       disabled:opacity-50 disabled:cursor-not-allowed"
          />
          {(minimum !== undefined || maximum !== undefined) && (
            <span className="text-xs text-gray-500 whitespace-nowrap">
              {minimum !== undefined && maximum !== undefined
                ? `${minimum} - ${maximum}`
                : minimum !== undefined
                ? `≥ ${minimum}`
                : `≤ ${maximum}`
              }
            </span>
          )}
        </div>
      );
    }
    
    // Default: string input
    return (
      <input
        type="text"
        value={currentValue || ''}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className="w-full bg-gray-800 border border-gray-600 rounded px-3 py-1.5
                   text-white text-sm focus:outline-none focus:border-blue-500
                   disabled:opacity-50 disabled:cursor-not-allowed"
      />
    );
  };
  
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between">
        <label className="text-sm text-gray-300">
          {displayName}
        </label>
        {defaultValue !== undefined && value !== defaultValue && (
          <button
            onClick={() => onChange(defaultValue)}
            disabled={disabled}
            className="text-xs text-blue-400 hover:text-blue-300 transition-colors"
          >
            Reset
          </button>
        )}
      </div>
      
      {renderInput()}
      
      {description && (
        <p className="text-xs text-gray-500">
          {description}
        </p>
      )}
    </div>
  );
}
