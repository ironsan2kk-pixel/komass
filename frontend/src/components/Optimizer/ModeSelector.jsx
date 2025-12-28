/**
 * KOMAS Trading Server - Optimization Mode Selector
 * ==================================================
 * UI component for selecting optimization mode.
 * 
 * Modes:
 * - Quick: Top 20 presets × 5 most liquid pairs (~100 combinations, < 1 min)
 * - Standard: All presets × 10 pairs (~1000+ combinations, < 5 min)
 * - Smart: Adaptive selection based on correlation and clustering
 * - Full: All presets × all pairs (comprehensive, 10+ min)
 * 
 * Chat #46: Preset Optimizer Modes
 */

import React, { useState, useEffect } from 'react';

// Mode icons
const MODE_ICONS = {
  quick: '⚡',
  standard: '⚖️',
  smart: '🧠',
  full: '🔬'
};

// Mode colors
const MODE_COLORS = {
  quick: 'text-yellow-400 border-yellow-400/30 bg-yellow-500/10',
  standard: 'text-blue-400 border-blue-400/30 bg-blue-500/10',
  smart: 'text-purple-400 border-purple-400/30 bg-purple-500/10',
  full: 'text-green-400 border-green-400/30 bg-green-500/10'
};

const MODE_SELECTED_COLORS = {
  quick: 'border-yellow-400 bg-yellow-500/20 ring-2 ring-yellow-400/30',
  standard: 'border-blue-400 bg-blue-500/20 ring-2 ring-blue-400/30',
  smart: 'border-purple-400 bg-purple-500/20 ring-2 ring-purple-400/30',
  full: 'border-green-400 bg-green-500/20 ring-2 ring-green-400/30'
};

/**
 * Single mode card component
 */
const ModeCard = ({ mode, selected, onClick, estimate }) => {
  const isSelected = selected === mode.mode;
  
  return (
    <div
      onClick={() => onClick(mode.mode)}
      className={`
        p-4 rounded-lg border cursor-pointer transition-all duration-200
        ${isSelected ? MODE_SELECTED_COLORS[mode.mode] : MODE_COLORS[mode.mode]}
        hover:scale-102 hover:shadow-lg
      `}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{MODE_ICONS[mode.mode]}</span>
          <span className={`font-bold text-lg ${isSelected ? 'text-white' : ''}`}>
            {mode.name}
          </span>
        </div>
        {isSelected && (
          <span className="text-xs bg-white/20 px-2 py-1 rounded">
            ✓ Selected
          </span>
        )}
      </div>
      
      {/* Description */}
      <p className="text-sm text-gray-400 mb-3">
        {mode.description}
      </p>
      
      {/* Stats */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-black/20 rounded px-2 py-1">
          <span className="text-gray-500">Max Presets: </span>
          <span className="text-gray-300">{mode.max_presets || 'All'}</span>
        </div>
        <div className="bg-black/20 rounded px-2 py-1">
          <span className="text-gray-500">Max Pairs: </span>
          <span className="text-gray-300">{mode.max_pairs || 'All'}</span>
        </div>
        <div className="bg-black/20 rounded px-2 py-1">
          <span className="text-gray-500">Selection: </span>
          <span className="text-gray-300 capitalize">{mode.preset_selection}</span>
        </div>
        <div className="bg-black/20 rounded px-2 py-1">
          <span className="text-gray-500">Pairs: </span>
          <span className="text-gray-300 capitalize">{mode.pair_selection}</span>
        </div>
      </div>
      
      {/* Time estimate if available */}
      {estimate && isSelected && (
        <div className="mt-3 pt-3 border-t border-gray-700">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">Estimated time:</span>
            <span className="text-white font-medium">{estimate.human_readable}</span>
          </div>
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>Combinations:</span>
            <span>{estimate.total_combinations.toLocaleString()}</span>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Compact mode selector (dropdown style)
 */
export const ModeDropdown = ({ 
  value, 
  onChange, 
  modes = [],
  disabled = false 
}) => {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      className={`
        bg-gray-800 border border-gray-700 rounded-lg px-4 py-2
        text-white focus:outline-none focus:ring-2 focus:ring-blue-500
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      {modes.map((mode) => (
        <option key={mode.mode} value={mode.mode}>
          {MODE_ICONS[mode.mode]} {mode.name}
        </option>
      ))}
    </select>
  );
};

/**
 * Time estimate display component
 */
export const TimeEstimate = ({ estimate, loading }) => {
  if (loading) {
    return (
      <div className="flex items-center gap-2 text-gray-400">
        <div className="animate-spin h-4 w-4 border-2 border-gray-600 border-t-gray-400 rounded-full"></div>
        <span>Calculating...</span>
      </div>
    );
  }
  
  if (!estimate) return null;
  
  return (
    <div className="bg-gray-800/50 rounded-lg p-4 border border-gray-700">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">⏱️</span>
        <span className="text-white font-medium">Time Estimate</span>
      </div>
      
      <div className="grid grid-cols-2 gap-4">
        <div>
          <div className="text-2xl font-bold text-blue-400">
            {estimate.human_readable}
          </div>
          <div className="text-xs text-gray-500">Estimated duration</div>
        </div>
        
        <div>
          <div className="text-2xl font-bold text-gray-300">
            {estimate.total_combinations.toLocaleString()}
          </div>
          <div className="text-xs text-gray-500">Total combinations</div>
        </div>
      </div>
      
      <div className="mt-3 pt-3 border-t border-gray-700 grid grid-cols-3 gap-2 text-xs">
        <div>
          <span className="text-gray-500">Presets: </span>
          <span className="text-gray-300">{estimate.effective_presets}</span>
        </div>
        <div>
          <span className="text-gray-500">Pairs: </span>
          <span className="text-gray-300">{estimate.effective_pairs}</span>
        </div>
        <div>
          <span className="text-gray-500">Workers: </span>
          <span className="text-gray-300">{estimate.num_workers}</span>
        </div>
      </div>
    </div>
  );
};

/**
 * Main ModeSelector component
 */
const ModeSelector = ({
  value,
  onChange,
  modes = [],
  estimate = null,
  estimateLoading = false,
  variant = 'cards', // 'cards' | 'dropdown' | 'compact'
  showEstimate = true,
  disabled = false
}) => {
  // Default modes if not provided
  const defaultModes = [
    {
      mode: 'quick',
      name: 'Quick',
      description: 'Fast optimization with top presets and most liquid pairs.',
      max_presets: 20,
      max_pairs: 5,
      preset_selection: 'top_performers',
      pair_selection: 'liquidity'
    },
    {
      mode: 'standard',
      name: 'Standard',
      description: 'Balanced optimization with diverse pair selection.',
      max_presets: 100,
      max_pairs: 10,
      preset_selection: 'all',
      pair_selection: 'diversity'
    },
    {
      mode: 'smart',
      name: 'Smart',
      description: 'Adaptive optimization using correlation and clustering.',
      max_presets: 50,
      max_pairs: 15,
      preset_selection: 'representative',
      pair_selection: 'representative'
    },
    {
      mode: 'full',
      name: 'Full',
      description: 'Comprehensive optimization with all presets and pairs.',
      max_presets: null,
      max_pairs: null,
      preset_selection: 'all',
      pair_selection: 'all'
    }
  ];

  const displayModes = modes.length > 0 ? modes : defaultModes;

  // Dropdown variant
  if (variant === 'dropdown') {
    return (
      <div className="flex items-center gap-4">
        <ModeDropdown 
          value={value} 
          onChange={onChange} 
          modes={displayModes}
          disabled={disabled}
        />
        {showEstimate && estimate && (
          <span className="text-sm text-gray-400">
            ~{estimate.human_readable}
          </span>
        )}
      </div>
    );
  }

  // Compact variant
  if (variant === 'compact') {
    return (
      <div className="space-y-3">
        <div className="flex gap-2">
          {displayModes.map((mode) => (
            <button
              key={mode.mode}
              onClick={() => !disabled && onChange(mode.mode)}
              disabled={disabled}
              className={`
                flex items-center gap-1 px-3 py-2 rounded-lg border transition-all
                ${value === mode.mode 
                  ? MODE_SELECTED_COLORS[mode.mode]
                  : 'border-gray-700 bg-gray-800 text-gray-400 hover:bg-gray-700'
                }
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <span>{MODE_ICONS[mode.mode]}</span>
              <span className="text-sm font-medium">{mode.name}</span>
            </button>
          ))}
        </div>
        {showEstimate && <TimeEstimate estimate={estimate} loading={estimateLoading} />}
      </div>
    );
  }

  // Cards variant (default)
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {displayModes.map((mode) => (
          <ModeCard
            key={mode.mode}
            mode={mode}
            selected={value}
            onClick={disabled ? () => {} : onChange}
            estimate={value === mode.mode ? estimate : null}
          />
        ))}
      </div>
      
      {showEstimate && value && (
        <TimeEstimate estimate={estimate} loading={estimateLoading} />
      )}
    </div>
  );
};

/**
 * Hook for mode selection with auto-estimate
 */
export const useModeSelector = (initialMode = 'standard', presetCount = 0, pairCount = 0) => {
  const [mode, setMode] = useState(initialMode);
  const [modes, setModes] = useState([]);
  const [estimate, setEstimate] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Fetch modes on mount
  useEffect(() => {
    const fetchModes = async () => {
      try {
        const response = await fetch('/api/optimizer/modes');
        const data = await response.json();
        if (data.modes) {
          setModes(data.modes);
        }
      } catch (error) {
        console.error('Failed to fetch modes:', error);
      }
    };
    
    fetchModes();
  }, []);
  
  // Fetch estimate when mode or counts change
  useEffect(() => {
    if (presetCount > 0 && pairCount > 0) {
      const fetchEstimate = async () => {
        setLoading(true);
        try {
          const response = await fetch('/api/optimizer/estimate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              preset_count: presetCount,
              pair_count: pairCount,
              mode: mode
            })
          });
          const data = await response.json();
          setEstimate(data);
        } catch (error) {
          console.error('Failed to fetch estimate:', error);
          setEstimate(null);
        } finally {
          setLoading(false);
        }
      };
      
      fetchEstimate();
    }
  }, [mode, presetCount, pairCount]);
  
  return {
    mode,
    setMode,
    modes,
    estimate,
    loading
  };
};

export default ModeSelector;
