/**
 * FilterSettings.jsx
 * ==================
 * Main filter configuration component for bot settings.
 * 
 * Features:
 * - Load all available filters from API
 * - Group filters by category
 * - Profile selector (Minimal/Conservative/Balanced/Aggressive)
 * - Enable/disable individual filters
 * - Edit filter parameters
 * - View filter statistics
 * 
 * Chat #44: Filters UI
 * Author: KOMAS Team
 * Version: 4.0
 */

import { useState, useEffect, useCallback } from 'react';
import FilterCategory from './FilterCategory';
import FilterProfileSelector from './FilterProfileSelector';
import FilterStats from './FilterStats';
import { filtersApi } from '../../api';

// Category display order and icons
const CATEGORY_CONFIG = {
  time: {
    icon: '⏰',
    displayName: 'Time Filters',
    description: 'Control when trades can be opened',
    color: 'blue',
  },
  volatility: {
    icon: '📊',
    displayName: 'Volatility Filters',
    description: 'Filter by market volatility conditions',
    color: 'yellow',
  },
  trend: {
    icon: '📈',
    displayName: 'Trend Filters',
    description: 'Follow market trends and regime',
    color: 'green',
  },
  portfolio: {
    icon: '💼',
    displayName: 'Portfolio Filters',
    description: 'Manage portfolio diversification',
    color: 'purple',
  },
  protection: {
    icon: '🛡️',
    displayName: 'Protection Filters',
    description: 'Equity and drawdown protection',
    color: 'red',
  },
};

// Category order for display
const CATEGORY_ORDER = ['time', 'volatility', 'trend', 'portfolio', 'protection'];

export default function FilterSettings({ botId, onConfigChange }) {
  // State
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [availableFilters, setAvailableFilters] = useState({});
  const [botFilters, setBotFilters] = useState({});
  const [filterStats, setFilterStats] = useState(null);
  const [profiles, setProfiles] = useState([]);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [expandedCategories, setExpandedCategories] = useState(['time']);
  const [hasChanges, setHasChanges] = useState(false);

  // Load data on mount
  useEffect(() => {
    if (botId) {
      loadData();
    }
  }, [botId]);

  // Load all filter data
  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Load available filters
      const availableRes = await filtersApi.getAvailable();
      setAvailableFilters(availableRes.data || {});
      
      // Load filter profiles
      const profilesRes = await filtersApi.getProfiles();
      setProfiles(profilesRes.data?.profiles || []);
      
      // Load bot's current filter config
      if (botId) {
        const configRes = await filtersApi.getBotConfig(botId);
        setBotFilters(configRes.data?.filters || {});
        
        // Load filter stats
        const statsRes = await filtersApi.getStats(botId);
        setFilterStats(statsRes.data || null);
      }
    } catch (err) {
      console.error('Error loading filter data:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  // Group filters by category
  const getFiltersByCategory = useCallback(() => {
    const grouped = {};
    
    // Initialize all categories
    CATEGORY_ORDER.forEach(cat => {
      grouped[cat] = [];
    });
    
    // Group available filters
    Object.entries(availableFilters).forEach(([name, info]) => {
      const category = info.category || 'unknown';
      if (!grouped[category]) {
        grouped[category] = [];
      }
      grouped[category].push({
        name,
        ...info,
        config: botFilters[name] || { enabled: false, params: {} },
      });
    });
    
    // Sort filters within each category by priority
    const priorityOrder = { HIGH: 0, MEDIUM: 1, LOW: 2 };
    Object.keys(grouped).forEach(cat => {
      grouped[cat].sort((a, b) => {
        const pa = priorityOrder[a.priority] ?? 1;
        const pb = priorityOrder[b.priority] ?? 1;
        return pa - pb;
      });
    });
    
    return grouped;
  }, [availableFilters, botFilters]);

  // Toggle filter enabled/disabled
  const handleToggleFilter = async (filterName, enabled) => {
    // Optimistic update
    const newFilters = {
      ...botFilters,
      [filterName]: {
        ...botFilters[filterName],
        enabled,
        params: botFilters[filterName]?.params || {},
      },
    };
    setBotFilters(newFilters);
    setHasChanges(true);
    
    try {
      if (enabled) {
        await filtersApi.enableFilter(botId, filterName);
      } else {
        await filtersApi.disableFilter(botId, filterName);
      }
      
      // Notify parent
      if (onConfigChange) {
        onConfigChange(newFilters);
      }
    } catch (err) {
      console.error('Error toggling filter:', err);
      // Revert on error
      setBotFilters(botFilters);
      setError(err.response?.data?.detail || err.message);
    }
  };

  // Update filter parameters
  const handleUpdateParams = async (filterName, params) => {
    const newFilters = {
      ...botFilters,
      [filterName]: {
        ...botFilters[filterName],
        params,
      },
    };
    setBotFilters(newFilters);
    setHasChanges(true);
    
    // Don't auto-save params - wait for explicit save
  };

  // Save all filter configurations
  const handleSave = async () => {
    setSaving(true);
    setError(null);
    
    try {
      await filtersApi.saveBotConfig(botId, { filters: botFilters });
      setHasChanges(false);
      
      // Reload stats after save
      const statsRes = await filtersApi.getStats(botId);
      setFilterStats(statsRes.data || null);
      
      // Notify parent
      if (onConfigChange) {
        onConfigChange(botFilters);
      }
    } catch (err) {
      console.error('Error saving filters:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setSaving(false);
    }
  };

  // Apply filter profile
  const handleApplyProfile = async (profileName) => {
    setSaving(true);
    setError(null);
    
    try {
      await filtersApi.applyProfile(botId, profileName);
      setSelectedProfile(profileName);
      
      // Reload config after applying profile
      const configRes = await filtersApi.getBotConfig(botId);
      setBotFilters(configRes.data?.filters || {});
      setHasChanges(false);
      
      // Notify parent
      if (onConfigChange) {
        onConfigChange(configRes.data?.filters || {});
      }
    } catch (err) {
      console.error('Error applying profile:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setSaving(false);
    }
  };

  // Toggle category expanded/collapsed
  const handleToggleCategory = (category) => {
    setExpandedCategories(prev => 
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  // Reset filters
  const handleReset = async () => {
    if (!confirm('Reset all filters to default? This will disable all filters.')) {
      return;
    }
    
    setSaving(true);
    try {
      await filtersApi.resetStats(botId);
      setBotFilters({});
      setHasChanges(false);
      
      // Reload
      await loadData();
    } catch (err) {
      console.error('Error resetting filters:', err);
      setError(err.response?.data?.detail || err.message);
    } finally {
      setSaving(false);
    }
  };

  // Get enabled filter count
  const getEnabledCount = () => {
    return Object.values(botFilters).filter(f => f.enabled).length;
  };

  // Loading state
  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-3 text-gray-400">Loading filters...</span>
        </div>
      </div>
    );
  }

  const filtersByCategory = getFiltersByCategory();

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <span className="text-2xl">🔍</span>
              Signal Filters
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              {getEnabledCount()} of {Object.keys(availableFilters).length} filters active
            </p>
          </div>
          
          <div className="flex items-center gap-2">
            {hasChanges && (
              <span className="text-yellow-400 text-sm mr-2">
                Unsaved changes
              </span>
            )}
            <button
              onClick={handleReset}
              disabled={saving}
              className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-gray-300 
                       rounded text-sm transition-colors"
            >
              Reset
            </button>
            <button
              onClick={handleSave}
              disabled={saving || !hasChanges}
              className="px-4 py-1.5 bg-blue-600 hover:bg-blue-500 text-white 
                       rounded text-sm transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="mx-4 mt-4 p-3 bg-red-900/30 border border-red-700 rounded-lg">
          <div className="flex items-center text-red-400">
            <span className="mr-2">❌</span>
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-400 hover:text-red-300"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* Profile Selector */}
      <div className="p-4 border-b border-gray-700">
        <FilterProfileSelector
          profiles={profiles}
          selected={selectedProfile}
          onSelect={handleApplyProfile}
          disabled={saving}
        />
      </div>

      {/* Filter Statistics */}
      {filterStats && (
        <div className="p-4 border-b border-gray-700">
          <FilterStats stats={filterStats} botId={botId} />
        </div>
      )}

      {/* Filter Categories */}
      <div className="divide-y divide-gray-700">
        {CATEGORY_ORDER.map(category => {
          const filters = filtersByCategory[category] || [];
          if (filters.length === 0) return null;
          
          const config = CATEGORY_CONFIG[category] || {
            icon: '📋',
            displayName: category,
            description: '',
            color: 'gray',
          };
          
          return (
            <FilterCategory
              key={category}
              category={category}
              displayName={config.displayName}
              description={config.description}
              icon={config.icon}
              color={config.color}
              filters={filters}
              expanded={expandedCategories.includes(category)}
              onToggleExpand={() => handleToggleCategory(category)}
              onToggleFilter={handleToggleFilter}
              onUpdateParams={handleUpdateParams}
              disabled={saving}
            />
          );
        })}
      </div>

      {/* Footer */}
      <div className="p-4 bg-gray-900/50 border-t border-gray-700 rounded-b-lg">
        <div className="flex items-center justify-between text-sm text-gray-400">
          <span>
            💡 Filters are applied in priority order. Enable only what you need.
          </span>
          <button
            onClick={loadData}
            className="text-blue-400 hover:text-blue-300 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>
    </div>
  );
}
