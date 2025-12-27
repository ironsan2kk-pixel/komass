/**
 * PresetSelector.jsx
 * ==================
 * Component for browsing and selecting Dominant indicator presets.
 * 
 * Features:
 * - Category tabs (All, Scalp, Short-Term, Mid-Term, Long-Term)
 * - Search/filter functionality
 * - Preset details display
 * - Auto-fill parameters on selection
 * 
 * Chat #27: Dominant UI Integration
 */

import React, { useState, useEffect, useMemo } from 'react';

const CATEGORIES = [
  { key: 'all', label: 'Все', icon: '📋' },
  { key: 'scalp', label: 'Scalp', icon: '⚡' },
  { key: 'short-term', label: 'Short', icon: '🏃' },
  { key: 'mid-term', label: 'Mid', icon: '🎯' },
  { key: 'long-term', label: 'Long', icon: '🐢' },
];

const FILTER_TYPE_NAMES = {
  0: 'None',
  1: 'ATR',
  2: 'RSI',
  3: 'ATR+RSI',
  4: 'Volatility',
};

const SL_MODE_NAMES = {
  0: 'No BE',
  1: 'After TP1',
  2: 'After TP2',
  3: 'After TP3',
  4: 'Cascade',
};

const PresetSelector = ({ 
  presets = [], 
  selectedPreset, 
  onSelect, 
  loading = false,
  indicatorType = 'dominant'
}) => {
  const [category, setCategory] = useState('all');
  const [search, setSearch] = useState('');

  // Filter presets by category and search
  const filteredPresets = useMemo(() => {
    if (!presets || presets.length === 0) return [];
    
    return presets.filter(p => {
      // Category filter
      if (category !== 'all') {
        const presetCategory = p.category?.toLowerCase() || 'mid-term';
        if (presetCategory !== category) return false;
      }
      
      // Search filter
      if (search) {
        const searchLower = search.toLowerCase();
        const name = (p.name || '').toLowerCase();
        const symbol = (p.symbol || '').toLowerCase();
        const timeframe = (p.timeframe || '').toLowerCase();
        return name.includes(searchLower) || 
               symbol.includes(searchLower) || 
               timeframe.includes(searchLower);
      }
      
      return true;
    });
  }, [presets, category, search]);

  // Count by category
  const categoryCounts = useMemo(() => {
    const counts = { all: presets?.length || 0 };
    CATEGORIES.slice(1).forEach(cat => {
      counts[cat.key] = presets?.filter(p => 
        (p.category?.toLowerCase() || 'mid-term') === cat.key
      ).length || 0;
    });
    return counts;
  }, [presets]);

  // Get preset display info
  const getPresetInfo = (preset) => {
    if (!preset?.params) return {};
    const params = preset.params;
    return {
      sensitivity: params.sensitivity ?? params.sens ?? 21,
      filterType: params.filter_type ?? params.filterType ?? 0,
      slMode: params.sl_mode ?? params.slMode ?? 0,
      tp1: params.tp1_percent ?? params.tp1 ?? 1.0,
      tp4: params.tp4_percent ?? params.tp4 ?? 5.0,
      sl: params.sl_percent ?? params.sl ?? 2.0,
    };
  };

  if (indicatorType !== 'dominant') {
    return (
      <div className="p-3 text-center text-gray-500 text-xs">
        TRG пресеты будут доступны в следующих версиях
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {/* Search */}
      <div className="relative">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="🔍 Поиск пресетов..."
          className="w-full bg-gray-700 text-white text-xs rounded px-3 py-2 pl-3 pr-8"
        />
        {search && (
          <button
            onClick={() => setSearch('')}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
          >
            ✕
          </button>
        )}
      </div>

      {/* Category tabs */}
      <div className="flex flex-wrap gap-1">
        {CATEGORIES.map(cat => (
          <button
            key={cat.key}
            onClick={() => setCategory(cat.key)}
            className={`px-2 py-1 text-xs rounded transition-colors flex items-center gap-1 ${
              category === cat.key
                ? 'bg-purple-600 text-white'
                : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
            }`}
          >
            <span>{cat.icon}</span>
            <span className="hidden sm:inline">{cat.label}</span>
            <span className="text-[10px] opacity-70">({categoryCounts[cat.key]})</span>
          </button>
        ))}
      </div>

      {/* Presets list */}
      <div className="max-h-64 overflow-y-auto space-y-1 border border-gray-700 rounded bg-gray-800/50">
        {loading ? (
          <div className="p-4 text-center text-gray-500 text-xs">
            ⏳ Загрузка пресетов...
          </div>
        ) : filteredPresets.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-xs">
            {presets?.length === 0 
              ? '📭 Нет пресетов' 
              : '🔍 Ничего не найдено'}
          </div>
        ) : (
          filteredPresets.map(preset => {
            const info = getPresetInfo(preset);
            const isSelected = selectedPreset?.id === preset.id;
            
            return (
              <button
                key={preset.id}
                onClick={() => onSelect(preset)}
                className={`w-full text-left p-2 transition-colors ${
                  isSelected
                    ? 'bg-purple-600/30 border-l-2 border-purple-500'
                    : 'hover:bg-gray-700/50'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      {isSelected && <span className="text-green-400">✓</span>}
                      <span className={`text-xs font-medium ${
                        isSelected ? 'text-white' : 'text-gray-300'
                      }`}>
                        {preset.name}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-1 text-[10px] text-gray-500">
                      <span>sens: {info.sensitivity}</span>
                      <span>•</span>
                      <span>filter: {FILTER_TYPE_NAMES[info.filterType] || info.filterType}</span>
                      <span>•</span>
                      <span>SL: {SL_MODE_NAMES[info.slMode] || info.slMode}</span>
                    </div>
                  </div>
                  {preset.symbol && preset.timeframe && (
                    <span className="text-[10px] text-gray-500 bg-gray-700 px-1.5 py-0.5 rounded">
                      {preset.symbol}/{preset.timeframe}
                    </span>
                  )}
                </div>
              </button>
            );
          })
        )}
      </div>

      {/* Selected preset details */}
      {selectedPreset && (
        <div className="p-2 bg-purple-900/20 border border-purple-700/30 rounded text-xs">
          <div className="flex items-center justify-between mb-2">
            <span className="font-medium text-purple-300">
              ✓ {selectedPreset.name}
            </span>
            <button
              onClick={() => onSelect(null)}
              className="text-gray-500 hover:text-white text-[10px]"
            >
              ✕ Сбросить
            </button>
          </div>
          <div className="grid grid-cols-3 gap-2 text-gray-400">
            <div>
              <div className="text-gray-500">Sensitivity</div>
              <div className="text-white">{getPresetInfo(selectedPreset).sensitivity}</div>
            </div>
            <div>
              <div className="text-gray-500">Filter</div>
              <div className="text-white">{FILTER_TYPE_NAMES[getPresetInfo(selectedPreset).filterType]}</div>
            </div>
            <div>
              <div className="text-gray-500">SL Mode</div>
              <div className="text-white">{SL_MODE_NAMES[getPresetInfo(selectedPreset).slMode]}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PresetSelector;
