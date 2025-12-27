/**
 * PresetCard - Display a single preset in the library grid
 * 
 * Features:
 * - Show preset info (name, indicator, category, params)
 * - Performance stats if available
 * - Quick actions (edit, clone, delete, export, favorite)
 * - Selection mode for batch operations
 * 
 * Chat: #31-33 — Presets Full Module
 */
import { useState } from 'react';

// Category badges
const CATEGORY_COLORS = {
  scalp: 'bg-red-600',
  'short-term': 'bg-orange-600',
  'mid-term': 'bg-blue-600',
  swing: 'bg-purple-600',
  'long-term': 'bg-green-600',
  special: 'bg-yellow-600',
};

const CATEGORY_LABELS = {
  scalp: 'Скальп',
  'short-term': 'Краткоср.',
  'mid-term': 'Среднеср.',
  swing: 'Свинг',
  'long-term': 'Долгоср.',
  special: 'Спец.',
};

// Source badges
const SOURCE_ICONS = {
  system: '🔧',
  pine_script: '🌲',
  user: '👤',
  manual: '✏️',
  imported: '📥',
  optimizer: '🔬',
};

export default function PresetCard({
  preset,
  selectMode = false,
  isSelected = false,
  onToggleSelect,
  onEdit,
  onClone,
  onDelete,
  onExport,
  onToggleFavorite,
  onApply,
}) {
  const [showActions, setShowActions] = useState(false);
  
  const indicatorType = preset.indicator_type || 'dominant';
  const category = preset.category || 'mid-term';
  const source = preset.source || 'manual';
  const params = preset.params || {};
  
  // Extract key params for display
  const getParamsPreview = () => {
    if (indicatorType === 'trg') {
      return `i1=${params.i1 || '?'} i2=${params.i2 || '?'}`;
    } else {
      return `sens=${params.sensitivity || '?'} ft=${params.filter_type || 0}`;
    }
  };
  
  // Format percentage
  const formatPercent = (val) => {
    if (val === null || val === undefined) return '—';
    return `${val > 0 ? '+' : ''}${val.toFixed(1)}%`;
  };
  
  const formatWinRate = (val) => {
    if (val === null || val === undefined) return '—';
    return `${val.toFixed(1)}%`;
  };

  return (
    <div
      className={`relative bg-gray-800 rounded-lg border transition-all ${
        isSelected 
          ? 'border-blue-500 ring-2 ring-blue-500/50' 
          : 'border-gray-700 hover:border-gray-600'
      }`}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      {/* Selection checkbox */}
      {selectMode && (
        <div 
          className="absolute top-2 left-2 z-10"
          onClick={(e) => {
            e.stopPropagation();
            onToggleSelect?.();
          }}
        >
          <div className={`w-6 h-6 rounded border-2 flex items-center justify-center cursor-pointer transition-colors ${
            isSelected 
              ? 'bg-blue-600 border-blue-600 text-white' 
              : 'bg-gray-700 border-gray-500 hover:border-gray-400'
          }`}>
            {isSelected && '✓'}
          </div>
        </div>
      )}
      
      {/* Favorite star */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          onToggleFavorite?.();
        }}
        className={`absolute top-2 right-2 text-xl transition-transform hover:scale-110 ${
          preset.is_favorite ? 'text-yellow-400' : 'text-gray-600 hover:text-gray-400'
        }`}
      >
        {preset.is_favorite ? '⭐' : '☆'}
      </button>
      
      {/* Main content */}
      <div className="p-4">
        {/* Header */}
        <div className="mb-3">
          {/* Indicator badge */}
          <div className="flex items-center gap-2 mb-2">
            <span className={`px-2 py-0.5 text-xs rounded font-medium ${
              indicatorType === 'trg' ? 'bg-cyan-600' : 'bg-indigo-600'
            }`}>
              {indicatorType.toUpperCase()}
            </span>
            
            <span className={`px-2 py-0.5 text-xs rounded ${CATEGORY_COLORS[category] || 'bg-gray-600'}`}>
              {CATEGORY_LABELS[category] || category}
            </span>
            
            <span className="text-gray-500 text-sm" title={`Источник: ${source}`}>
              {SOURCE_ICONS[source] || '📁'}
            </span>
          </div>
          
          {/* Name */}
          <h3 className="font-semibold text-white truncate" title={preset.name}>
            {preset.name}
          </h3>
          
          {/* Description */}
          {preset.description && (
            <p className="text-gray-400 text-xs mt-1 truncate" title={preset.description}>
              {preset.description}
            </p>
          )}
        </div>
        
        {/* Params */}
        <div className="bg-gray-900 rounded p-2 mb-3">
          <code className="text-cyan-400 text-sm">{getParamsPreview()}</code>
          
          {/* TP/SL preview */}
          {indicatorType === 'dominant' && (
            <div className="text-gray-500 text-xs mt-1">
              TP: {params.tp1_percent || '?'}% / {params.tp2_percent || '?'}% | 
              SL: {params.sl_percent || '?'}%
            </div>
          )}
          
          {indicatorType === 'trg' && params.tp_percents && (
            <div className="text-gray-500 text-xs mt-1">
              TP: {params.tp_percents.slice(0, 3).map(p => `${p}%`).join('/')} | 
              SL: {params.sl_percent || '?'}%
            </div>
          )}
        </div>
        
        {/* Performance stats (if available) */}
        {(preset.win_rate || preset.total_profit_percent) && (
          <div className="grid grid-cols-2 gap-2 mb-3 text-xs">
            <div className="bg-gray-900 rounded p-2">
              <div className="text-gray-500">Win Rate</div>
              <div className={`font-medium ${
                (preset.win_rate || 0) >= 50 ? 'text-green-400' : 'text-red-400'
              }`}>
                {formatWinRate(preset.win_rate)}
              </div>
            </div>
            <div className="bg-gray-900 rounded p-2">
              <div className="text-gray-500">Profit</div>
              <div className={`font-medium ${
                (preset.total_profit_percent || 0) >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {formatPercent(preset.total_profit_percent)}
              </div>
            </div>
            {preset.profit_factor && (
              <div className="bg-gray-900 rounded p-2">
                <div className="text-gray-500">PF</div>
                <div className="font-medium text-white">
                  {preset.profit_factor?.toFixed(2) || '—'}
                </div>
              </div>
            )}
            {preset.max_drawdown_percent && (
              <div className="bg-gray-900 rounded p-2">
                <div className="text-gray-500">Max DD</div>
                <div className="font-medium text-red-400">
                  {formatPercent(-Math.abs(preset.max_drawdown_percent))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* Tags */}
        {preset.tags && preset.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mb-3">
            {preset.tags.slice(0, 3).map((tag, i) => (
              <span key={i} className="px-2 py-0.5 bg-gray-700 text-gray-300 rounded text-xs">
                #{tag}
              </span>
            ))}
            {preset.tags.length > 3 && (
              <span className="px-2 py-0.5 text-gray-500 text-xs">
                +{preset.tags.length - 3}
              </span>
            )}
          </div>
        )}
        
        {/* Actions */}
        <div className={`flex gap-2 transition-opacity ${showActions ? 'opacity-100' : 'opacity-0'}`}>
          <button
            onClick={onApply}
            className="flex-1 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium"
            title="Применить к индикатору"
          >
            ▶ Применить
          </button>
          
          <div className="flex gap-1">
            <button
              onClick={onEdit}
              className="px-2 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm"
              title="Редактировать"
            >
              ✏️
            </button>
            <button
              onClick={onClone}
              className="px-2 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm"
              title="Клонировать"
            >
              📋
            </button>
            <button
              onClick={onExport}
              className="px-2 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm"
              title="Экспорт JSON"
            >
              📤
            </button>
            {source !== 'system' && source !== 'pine_script' && (
              <button
                onClick={onDelete}
                className="px-2 py-1.5 bg-red-700 hover:bg-red-600 rounded text-sm"
                title="Удалить"
              >
                🗑️
              </button>
            )}
          </div>
        </div>
      </div>
      
      {/* Inactive overlay */}
      {preset.is_active === false && (
        <div className="absolute inset-0 bg-gray-900/60 rounded-lg flex items-center justify-center">
          <span className="text-gray-400 font-medium">Неактивен</span>
        </div>
      )}
    </div>
  );
}
