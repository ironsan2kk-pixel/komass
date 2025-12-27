/**
 * Indicator Components Index
 * ==========================
 * Export all indicator-related components.
 * 
 * Chat #27: Added PresetSelector
 * Chat #36: Added ScoreBadge, ScoreBreakdown, GradeLegend
 */

export { default as LogsPanel } from './LogsPanel';
export { default as SettingsSidebar } from './SettingsSidebar';
export { default as StatsPanel } from './StatsPanel';
export { default as MonthlyPanel } from './MonthlyPanel';
export { default as TradesTable } from './TradesTable';
export { default as HeatmapPanel } from './HeatmapPanel';
export { default as AutoOptimizePanel } from './AutoOptimizePanel';
export { default as PresetSelector } from './PresetSelector';

// Signal Score components (Chat #36)
export { default as ScoreBadge } from './ScoreBadge';
export { 
  ScoreBreakdown,
  GradeLegend,
  GRADE_COLORS,
  GRADE_DESCRIPTIONS,
  GRADE_RANGES,
  getGradeFromScore,
} from './ScoreBadge';
