/**
 * FilterProfileSelector.jsx
 * ==========================
 * Profile selection dropdown for quick filter configuration.
 * 
 * Profiles:
 * - Minimal: Minimum filtering, maximum signals
 * - Conservative: Strict filtering for quality signals
 * - Balanced: Moderate filtering (recommended)
 * - Aggressive: Heavy filtering, only best setups
 * 
 * Chat #44: Filters UI
 * Author: KOMAS Team
 * Version: 4.0
 */

import { useState } from 'react';

// Profile configurations
const PROFILE_CONFIG = {
  minimal: {
    icon: '🟢',
    name: 'Minimal',
    description: 'Minimal filtering - maximum signals, higher risk',
    color: 'green',
    filterCount: '1-2',
  },
  conservative: {
    icon: '🔵',
    name: 'Conservative',
    description: 'Moderate filtering - balanced signals quality',
    color: 'blue',
    filterCount: '3-5',
  },
  balanced: {
    icon: '🟡',
    name: 'Balanced',
    description: 'Recommended - good quality/quantity balance',
    color: 'yellow',
    filterCount: '5-8',
  },
  aggressive: {
    icon: '🔴',
    name: 'Aggressive',
    description: 'Heavy filtering - only highest quality signals',
    color: 'red',
    filterCount: '8+',
  },
};

export default function FilterProfileSelector({
  profiles = [],
  selected,
  onSelect,
  disabled = false,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [hoveredProfile, setHoveredProfile] = useState(null);
  
  // Get profile info (from API or fallback to config)
  const getProfileInfo = (profileName) => {
    const apiProfile = profiles.find(p => p.name === profileName);
    const config = PROFILE_CONFIG[profileName] || {};
    
    return {
      name: profileName,
      displayName: config.name || profileName,
      description: apiProfile?.description || config.description || '',
      icon: config.icon || '📋',
      color: config.color || 'gray',
      filterCount: apiProfile?.filter_count || config.filterCount || '?',
    };
  };
  
  // Get current selection info
  const currentProfile = selected ? getProfileInfo(selected) : null;
  
  // Available profiles (from API or default)
  const availableProfiles = profiles.length > 0 
    ? profiles.map(p => p.name)
    : Object.keys(PROFILE_CONFIG);
  
  return (
    <div className="relative">
      <div className="flex items-center justify-between mb-2">
        <label className="text-sm font-medium text-gray-300">
          Quick Profile
        </label>
        <span className="text-xs text-gray-500">
          Apply preset filter configuration
        </span>
      </div>
      
      {/* Dropdown Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={`w-full flex items-center justify-between p-3 rounded-lg border
                   transition-colors duration-200
                   ${isOpen ? 'border-blue-500 bg-gray-700/50' : 'border-gray-600 bg-gray-800'}
                   hover:border-gray-500 disabled:opacity-50 disabled:cursor-not-allowed`}
      >
        {currentProfile ? (
          <div className="flex items-center gap-3">
            <span className="text-xl">{currentProfile.icon}</span>
            <div className="text-left">
              <span className="text-white font-medium">
                {currentProfile.displayName}
              </span>
              <span className="text-gray-500 text-xs ml-2">
                ({currentProfile.filterCount} filters)
              </span>
            </div>
          </div>
        ) : (
          <span className="text-gray-400">Select a profile...</span>
        )}
        
        <svg
          className={`w-5 h-5 text-gray-400 transition-transform duration-200
                     ${isOpen ? 'rotate-180' : ''}`}
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
      
      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 py-1 bg-gray-800 border border-gray-600 
                       rounded-lg shadow-xl">
          {availableProfiles.map((profileName) => {
            const profile = getProfileInfo(profileName);
            const isSelected = selected === profileName;
            const isHovered = hoveredProfile === profileName;
            
            return (
              <button
                key={profileName}
                onClick={() => {
                  onSelect(profileName);
                  setIsOpen(false);
                }}
                onMouseEnter={() => setHoveredProfile(profileName)}
                onMouseLeave={() => setHoveredProfile(null)}
                className={`w-full flex items-start gap-3 p-3 text-left transition-colors
                           ${isSelected ? 'bg-blue-600/20' : ''}
                           ${isHovered ? 'bg-gray-700/50' : ''}`}
              >
                <span className="text-xl mt-0.5">{profile.icon}</span>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`font-medium ${isSelected ? 'text-blue-400' : 'text-white'}`}>
                      {profile.displayName}
                    </span>
                    <span className="text-xs text-gray-500">
                      {profile.filterCount} filters
                    </span>
                    {isSelected && (
                      <span className="text-blue-400 text-xs">✓ Active</span>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5">
                    {profile.description}
                  </p>
                </div>
              </button>
            );
          })}
          
          {/* Custom option */}
          <div className="border-t border-gray-700 mt-1 pt-1">
            <button
              onClick={() => {
                onSelect(null);
                setIsOpen(false);
              }}
              className="w-full flex items-center gap-3 p-3 text-left hover:bg-gray-700/50 
                        transition-colors"
            >
              <span className="text-xl">⚙️</span>
              <div>
                <span className="text-gray-300 font-medium">Custom</span>
                <p className="text-xs text-gray-500">
                  Configure filters manually
                </p>
              </div>
            </button>
          </div>
        </div>
      )}
      
      {/* Profile Comparison (when open) */}
      {isOpen && (
        <div className="absolute z-40 right-0 top-0 transform translate-x-full pl-4 w-64">
          <div className="bg-gray-800 border border-gray-600 rounded-lg p-4 shadow-xl">
            <h4 className="text-sm font-medium text-white mb-3">
              Profile Comparison
            </h4>
            <div className="space-y-2 text-xs">
              {availableProfiles.map(name => {
                const profile = getProfileInfo(name);
                return (
                  <div key={name} className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <span>{profile.icon}</span>
                      <span className="text-gray-400">{profile.displayName}</span>
                    </span>
                    <span className="text-gray-500">{profile.filterCount}</span>
                  </div>
                );
              })}
            </div>
            <div className="mt-3 pt-3 border-t border-gray-700">
              <p className="text-xs text-gray-500">
                💡 More filters = fewer but higher quality signals
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
