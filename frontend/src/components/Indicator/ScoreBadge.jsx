/**
 * ScoreBadge.jsx
 * ==============
 * Signal Score badge component with A-F grade display.
 * 
 * Features:
 * - Color-coded badge based on grade
 * - Hover tooltip with score breakdown
 * - Compact and full display modes
 * 
 * Chat #36: Score UI
 */

import React, { useState } from 'react';

// Grade colors matching backend get_grade_color
const GRADE_COLORS = {
  A: { bg: 'bg-green-600', text: 'text-green-100', border: 'border-green-500', hex: '#22c55e' },
  B: { bg: 'bg-lime-600', text: 'text-lime-100', border: 'border-lime-500', hex: '#84cc16' },
  C: { bg: 'bg-yellow-600', text: 'text-yellow-100', border: 'border-yellow-500', hex: '#eab308' },
  D: { bg: 'bg-orange-600', text: 'text-orange-100', border: 'border-orange-500', hex: '#f97316' },
  F: { bg: 'bg-red-600', text: 'text-red-100', border: 'border-red-500', hex: '#ef4444' },
};

// Grade descriptions
const GRADE_DESCRIPTIONS = {
  A: 'Excellent',
  B: 'Good',
  C: 'Average',
  D: 'Below Avg',
  F: 'Poor',
};

// Grade thresholds (matching backend)
const GRADE_RANGES = {
  A: { min: 85, max: 100 },
  B: { min: 70, max: 84 },
  C: { min: 55, max: 69 },
  D: { min: 40, max: 54 },
  F: { min: 0, max: 39 },
};

/**
 * Get grade from numeric score
 */
const getGradeFromScore = (score) => {
  if (score >= 85) return 'A';
  if (score >= 70) return 'B';
  if (score >= 55) return 'C';
  if (score >= 40) return 'D';
  return 'F';
};

/**
 * ScoreBadge Component
 * 
 * @param {Object} props
 * @param {number} props.score - Numeric score (0-100)
 * @param {string} props.grade - Grade letter (A-F), auto-calculated if not provided
 * @param {Object} props.components - Score breakdown by component
 * @param {string} props.size - Badge size: 'xs', 'sm', 'md', 'lg'
 * @param {boolean} props.showScore - Show numeric score alongside grade
 * @param {boolean} props.showTooltip - Enable hover tooltip
 * @param {Function} props.onClick - Click handler
 */
const ScoreBadge = ({
  score,
  grade,
  components,
  size = 'sm',
  showScore = false,
  showTooltip = true,
  onClick,
}) => {
  const [tooltipVisible, setTooltipVisible] = useState(false);
  
  // Calculate grade if not provided
  const finalGrade = grade || (typeof score === 'number' ? getGradeFromScore(score) : null);
  
  // Handle missing data
  if (!finalGrade && (score === null || score === undefined)) {
    return (
      <span className="text-gray-500 text-xs">—</span>
    );
  }
  
  const colors = GRADE_COLORS[finalGrade] || GRADE_COLORS.F;
  
  // Size classes
  const sizeClasses = {
    xs: 'text-[10px] px-1 py-0',
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5',
  };

  return (
    <div className="relative inline-block">
      <span
        className={`
          inline-flex items-center gap-1 rounded font-bold
          ${colors.bg} ${colors.text}
          ${sizeClasses[size]}
          ${onClick ? 'cursor-pointer hover:opacity-80' : ''}
          transition-opacity
        `}
        onClick={onClick}
        onMouseEnter={() => showTooltip && setTooltipVisible(true)}
        onMouseLeave={() => setTooltipVisible(false)}
      >
        {finalGrade}
        {showScore && typeof score === 'number' && (
          <span className="opacity-80 font-normal">({score})</span>
        )}
      </span>
      
      {/* Tooltip */}
      {showTooltip && tooltipVisible && (
        <ScoreTooltip
          score={score}
          grade={finalGrade}
          components={components}
        />
      )}
    </div>
  );
};

/**
 * ScoreTooltip Component - Shown on hover
 */
const ScoreTooltip = ({ score, grade, components }) => {
  const colors = GRADE_COLORS[grade] || GRADE_COLORS.F;
  
  return (
    <div 
      className="absolute z-50 left-full ml-2 top-1/2 -translate-y-1/2
                 bg-gray-800 border border-gray-600 rounded-lg shadow-lg
                 min-w-[200px] p-3"
      style={{ pointerEvents: 'none' }}
    >
      {/* Arrow */}
      <div 
        className="absolute left-0 top-1/2 -translate-x-full -translate-y-1/2
                   border-8 border-transparent border-r-gray-600"
      />
      <div 
        className="absolute left-0 top-1/2 -translate-x-[calc(100%-1px)] -translate-y-1/2
                   border-8 border-transparent border-r-gray-800"
      />
      
      {/* Header */}
      <div className="flex items-center justify-between mb-2 pb-2 border-b border-gray-700">
        <span className="text-gray-400 text-sm">Signal Score</span>
        <span className={`font-bold ${colors.text}`}>
          {typeof score === 'number' ? score : '—'} ({grade})
        </span>
      </div>
      
      {/* Grade description */}
      <div className="text-xs text-gray-500 mb-3">
        {GRADE_DESCRIPTIONS[grade] || 'Unknown'} • {GRADE_RANGES[grade]?.min || 0}-{GRADE_RANGES[grade]?.max || 0} pts
      </div>
      
      {/* Component breakdown */}
      {components && Object.keys(components).length > 0 ? (
        <div className="space-y-1.5">
          <ComponentBar 
            label="Confluence" 
            value={components.confluence} 
            max={25} 
          />
          <ComponentBar 
            label="Multi-TF" 
            value={components.multi_tf} 
            max={25} 
          />
          <ComponentBar 
            label="Market Context" 
            value={components.market_context} 
            max={25} 
          />
          <ComponentBar 
            label="Tech Levels" 
            value={components.technical_levels} 
            max={25} 
          />
        </div>
      ) : (
        <div className="text-xs text-gray-500">
          No breakdown available
        </div>
      )}
    </div>
  );
};

/**
 * ComponentBar - Progress bar for component score
 */
const ComponentBar = ({ label, value, max }) => {
  const percentage = typeof value === 'number' ? (value / max) * 100 : 0;
  const displayValue = typeof value === 'number' ? value : 0;
  
  // Color based on percentage
  let barColor = 'bg-red-500';
  if (percentage >= 80) barColor = 'bg-green-500';
  else if (percentage >= 60) barColor = 'bg-lime-500';
  else if (percentage >= 40) barColor = 'bg-yellow-500';
  else if (percentage >= 20) barColor = 'bg-orange-500';
  
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-400 w-24 truncate">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${barColor} rounded-full transition-all`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="text-xs text-white w-10 text-right">{displayValue}/{max}</span>
    </div>
  );
};

/**
 * ScoreBreakdown Component - Full breakdown display
 * For use outside of tooltip (e.g., in modals or panels)
 */
export const ScoreBreakdown = ({ score, grade, components, details }) => {
  const finalGrade = grade || (typeof score === 'number' ? getGradeFromScore(score) : 'F');
  const colors = GRADE_COLORS[finalGrade] || GRADE_COLORS.F;
  
  return (
    <div className="bg-gray-800 rounded-lg p-4 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="text-gray-400 text-sm">Signal Quality Score</div>
          <div className={`text-3xl font-bold ${colors.text}`}>
            {typeof score === 'number' ? score : '—'}
            <span className="text-lg ml-1">/ 100</span>
          </div>
        </div>
        <div 
          className={`w-16 h-16 rounded-lg ${colors.bg} flex items-center justify-center`}
        >
          <span className="text-3xl font-bold text-white">{finalGrade}</span>
        </div>
      </div>
      
      {/* Grade description */}
      <div className={`text-sm ${colors.text} opacity-80`}>
        {GRADE_DESCRIPTIONS[finalGrade]} ({GRADE_RANGES[finalGrade]?.min}-{GRADE_RANGES[finalGrade]?.max} pts)
      </div>
      
      {/* Component breakdown */}
      {components && (
        <div className="space-y-3 pt-2 border-t border-gray-700">
          <ComponentRow 
            label="🎯 Confluence" 
            value={components.confluence} 
            max={25}
            description="Multiple indicators agree on direction"
          />
          <ComponentRow 
            label="📊 Multi-TF Alignment" 
            value={components.multi_tf} 
            max={25}
            description="Higher timeframes confirm signal"
          />
          <ComponentRow 
            label="🌍 Market Context" 
            value={components.market_context} 
            max={25}
            description="Trend strength + volatility conditions"
          />
          <ComponentRow 
            label="📍 Technical Levels" 
            value={components.technical_levels} 
            max={25}
            description="Distance from support/resistance"
          />
        </div>
      )}
      
      {/* Details (optional) */}
      {details && (
        <div className="pt-2 border-t border-gray-700">
          <div className="text-xs text-gray-400 mb-2">Details</div>
          <div className="text-xs text-gray-500 space-y-1">
            {details.confluence?.supertrend_agrees !== undefined && (
              <div>SuperTrend: {details.confluence.supertrend_agrees ? '✅' : '❌'}</div>
            )}
            {details.confluence?.rsi_agrees !== undefined && (
              <div>RSI: {details.confluence.rsi_agrees ? '✅' : '❌'} ({details.confluence.rsi_value?.toFixed(1)})</div>
            )}
            {details.confluence?.adx_strong !== undefined && (
              <div>ADX: {details.confluence.adx_strong ? '✅' : '❌'} ({details.confluence.adx_value?.toFixed(1)})</div>
            )}
            {details.market_context?.trend_strength && (
              <div>Trend: {details.market_context.trend_strength}</div>
            )}
            {details.technical_levels?.level_status && (
              <div>Levels: {details.technical_levels.level_status}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * ComponentRow - Detailed row with description
 */
const ComponentRow = ({ label, value, max, description }) => {
  const percentage = typeof value === 'number' ? (value / max) * 100 : 0;
  const displayValue = typeof value === 'number' ? value : 0;
  
  let barColor = 'bg-red-500';
  if (percentage >= 80) barColor = 'bg-green-500';
  else if (percentage >= 60) barColor = 'bg-lime-500';
  else if (percentage >= 40) barColor = 'bg-yellow-500';
  else if (percentage >= 20) barColor = 'bg-orange-500';
  
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-sm text-white">{label}</span>
        <span className="text-sm text-white font-bold">{displayValue}/{max}</span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${barColor} rounded-full transition-all`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {description && (
        <div className="text-xs text-gray-500 mt-0.5">{description}</div>
      )}
    </div>
  );
};

/**
 * GradeLegend Component - Display all grades with colors
 */
export const GradeLegend = ({ compact = false }) => {
  const grades = ['A', 'B', 'C', 'D', 'F'];
  
  if (compact) {
    return (
      <div className="flex gap-1">
        {grades.map(g => (
          <span 
            key={g}
            className={`px-1 text-xs rounded ${GRADE_COLORS[g].bg} ${GRADE_COLORS[g].text}`}
          >
            {g}
          </span>
        ))}
      </div>
    );
  }
  
  return (
    <div className="flex flex-wrap gap-2">
      {grades.map(g => (
        <div key={g} className="flex items-center gap-1 text-xs">
          <span className={`px-1.5 py-0.5 rounded font-bold ${GRADE_COLORS[g].bg} ${GRADE_COLORS[g].text}`}>
            {g}
          </span>
          <span className="text-gray-400">
            {GRADE_DESCRIPTIONS[g]} ({GRADE_RANGES[g].min}-{GRADE_RANGES[g].max})
          </span>
        </div>
      ))}
    </div>
  );
};

// Export utilities
export { GRADE_COLORS, GRADE_DESCRIPTIONS, GRADE_RANGES, getGradeFromScore };

export default ScoreBadge;
