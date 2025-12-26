/**
 * Settings Sidebar Component
 * ==========================
 * Боковая панель с настройками индикатора
 */
import { useState } from 'react';

const SECTIONS = [
  { id: 'trg', name: '📊 TRG Индикатор', defaultOpen: true },
  { id: 'tp', name: '🎯 Take Profits', defaultOpen: true },
  { id: 'sl', name: '🛡️ Stop Loss', defaultOpen: true },
  { id: 'filters', name: '🔍 Фильтры', defaultOpen: false },
  { id: 'reentry', name: '🔄 Re-entry', defaultOpen: false },
  { id: 'capital', name: '💰 Капитал', defaultOpen: false },
  { id: 'adaptive', name: '🧠 Adaptive', defaultOpen: false },
];

export default function SettingsSidebar({
  settings,
  updateSetting,
  updateSettings,
  collapsed,
  onToggle,
  onReset,
  onSavePreset,
}) {
  const [expandedSections, setExpandedSections] = useState(
    SECTIONS.reduce((acc, s) => ({ ...acc, [s.id]: s.defaultOpen }), {})
  );
  const [presetName, setPresetName] = useState('');
  const [showPresetInput, setShowPresetInput] = useState(false);

  const toggleSection = (id) => {
    setExpandedSections(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleSavePreset = () => {
    if (presetName.trim()) {
      onSavePreset(presetName.trim());
      setPresetName('');
      setShowPresetInput(false);
    }
  };

  if (collapsed) {
    return (
      <div className="w-12 bg-gray-800 border-r border-gray-700 flex flex-col items-center py-4">
        <button
          onClick={onToggle}
          className="text-gray-400 hover:text-white p-2 hover:bg-gray-700 rounded"
        >
          ▶
        </button>
      </div>
    );
  }

  return (
    <aside className="w-80 bg-gray-800 border-r border-gray-700 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-700 flex items-center justify-between">
        <h2 className="font-bold text-lg">⚙️ Настройки</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setShowPresetInput(!showPresetInput)}
            className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
            title="Сохранить пресет"
          >
            💾
          </button>
          <button
            onClick={onReset}
            className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
            title="Сбросить"
          >
            🔄
          </button>
          <button
            onClick={onToggle}
            className="text-gray-400 hover:text-white"
          >
            ◀
          </button>
        </div>
      </div>

      {/* Save Preset Input */}
      {showPresetInput && (
        <div className="p-3 border-b border-gray-700 flex gap-2">
          <input
            type="text"
            value={presetName}
            onChange={(e) => setPresetName(e.target.value)}
            placeholder="Название пресета..."
            className="flex-1 bg-gray-700 px-3 py-1.5 rounded text-sm"
            onKeyDown={(e) => e.key === 'Enter' && handleSavePreset()}
          />
          <button
            onClick={handleSavePreset}
            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-sm"
          >
            Сохранить
          </button>
        </div>
      )}

      {/* Sections */}
      <div className="flex-1 overflow-y-auto">
        {/* TRG Indicator */}
        <Section
          title={SECTIONS[0].name}
          expanded={expandedSections.trg}
          onToggle={() => toggleSection('trg')}
        >
          <div className="space-y-3">
            <NumberInput
              label="i1 (ATR Length)"
              value={settings.trg_atr_length}
              onChange={(v) => updateSetting('trg_atr_length', v)}
              min={10}
              max={200}
            />
            <NumberInput
              label="i2 (Multiplier)"
              value={settings.trg_multiplier}
              onChange={(v) => updateSetting('trg_multiplier', v)}
              min={1}
              max={10}
              step={0.5}
            />
          </div>
        </Section>

        {/* Take Profits */}
        <Section
          title={SECTIONS[1].name}
          expanded={expandedSections.tp}
          onToggle={() => toggleSection('tp')}
        >
          <div className="space-y-3">
            <NumberInput
              label="Активных TP"
              value={settings.tp_count}
              onChange={(v) => updateSetting('tp_count', v)}
              min={1}
              max={10}
            />
            
            {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].slice(0, settings.tp_count).map(n => (
              <div key={n} className="grid grid-cols-2 gap-2">
                <NumberInput
                  label={`TP${n} %`}
                  value={settings[`tp${n}_percent`]}
                  onChange={(v) => updateSetting(`tp${n}_percent`, v)}
                  min={0.1}
                  max={50}
                  step={0.05}
                />
                <NumberInput
                  label={`TP${n} объём`}
                  value={settings[`tp${n}_amount`]}
                  onChange={(v) => updateSetting(`tp${n}_amount`, v)}
                  min={0}
                  max={100}
                />
              </div>
            ))}
          </div>
        </Section>

        {/* Stop Loss */}
        <Section
          title={SECTIONS[2].name}
          expanded={expandedSections.sl}
          onToggle={() => toggleSection('sl')}
        >
          <div className="space-y-3">
            <NumberInput
              label="SL %"
              value={settings.sl_percent}
              onChange={(v) => updateSetting('sl_percent', v)}
              min={0.5}
              max={50}
              step={0.5}
            />
            
            <div>
              <label className="text-xs text-gray-400 block mb-1">Trailing Mode</label>
              <div className="flex gap-1">
                {['fixed', 'breakeven', 'cascade'].map(mode => (
                  <button
                    key={mode}
                    onClick={() => updateSetting('sl_trailing_mode', mode)}
                    className={`flex-1 py-1.5 px-2 rounded text-xs font-medium transition-colors ${
                      settings.sl_trailing_mode === mode
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-700 text-gray-400 hover:text-white'
                    }`}
                  >
                    {mode === 'fixed' ? 'Fixed' : mode === 'breakeven' ? 'BE' : 'Cascade'}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </Section>

        {/* Filters */}
        <Section
          title={SECTIONS[3].name}
          expanded={expandedSections.filters}
          onToggle={() => toggleSection('filters')}
        >
          <div className="space-y-4">
            {/* SuperTrend */}
            <div className="space-y-2">
              <Toggle
                label="SuperTrend"
                checked={settings.use_supertrend}
                onChange={(v) => updateSetting('use_supertrend', v)}
              />
              {settings.use_supertrend && (
                <div className="grid grid-cols-2 gap-2 pl-4">
                  <NumberInput
                    label="Period"
                    value={settings.supertrend_period}
                    onChange={(v) => updateSetting('supertrend_period', v)}
                    min={5}
                    max={50}
                  />
                  <NumberInput
                    label="Mult"
                    value={settings.supertrend_multiplier}
                    onChange={(v) => updateSetting('supertrend_multiplier', v)}
                    min={1}
                    max={10}
                    step={0.5}
                  />
                </div>
              )}
            </div>

            {/* RSI */}
            <div className="space-y-2">
              <Toggle
                label="RSI Filter"
                checked={settings.use_rsi_filter}
                onChange={(v) => updateSetting('use_rsi_filter', v)}
              />
              {settings.use_rsi_filter && (
                <div className="grid grid-cols-3 gap-2 pl-4">
                  <NumberInput
                    label="Period"
                    value={settings.rsi_period}
                    onChange={(v) => updateSetting('rsi_period', v)}
                    min={5}
                    max={50}
                  />
                  <NumberInput
                    label="OB"
                    value={settings.rsi_overbought}
                    onChange={(v) => updateSetting('rsi_overbought', v)}
                    min={50}
                    max={95}
                  />
                  <NumberInput
                    label="OS"
                    value={settings.rsi_oversold}
                    onChange={(v) => updateSetting('rsi_oversold', v)}
                    min={5}
                    max={50}
                  />
                </div>
              )}
            </div>

            {/* ADX */}
            <div className="space-y-2">
              <Toggle
                label="ADX Filter"
                checked={settings.use_adx_filter}
                onChange={(v) => updateSetting('use_adx_filter', v)}
              />
              {settings.use_adx_filter && (
                <div className="grid grid-cols-2 gap-2 pl-4">
                  <NumberInput
                    label="Period"
                    value={settings.adx_period}
                    onChange={(v) => updateSetting('adx_period', v)}
                    min={5}
                    max={50}
                  />
                  <NumberInput
                    label="Threshold"
                    value={settings.adx_threshold}
                    onChange={(v) => updateSetting('adx_threshold', v)}
                    min={10}
                    max={50}
                  />
                </div>
              )}
            </div>

            {/* Volume */}
            <Toggle
              label="Volume Filter"
              checked={settings.use_volume_filter}
              onChange={(v) => updateSetting('use_volume_filter', v)}
            />
          </div>
        </Section>

        {/* Re-entry */}
        <Section
          title={SECTIONS[4].name}
          expanded={expandedSections.reentry}
          onToggle={() => toggleSection('reentry')}
        >
          <div className="space-y-3">
            <Toggle
              label="Разрешить Re-entry"
              checked={settings.allow_reentry}
              onChange={(v) => updateSetting('allow_reentry', v)}
            />
            {settings.allow_reentry && (
              <>
                <Toggle
                  label="После SL"
                  checked={settings.reentry_after_sl}
                  onChange={(v) => updateSetting('reentry_after_sl', v)}
                />
                <Toggle
                  label="После TP"
                  checked={settings.reentry_after_tp}
                  onChange={(v) => updateSetting('reentry_after_tp', v)}
                />
              </>
            )}
          </div>
        </Section>

        {/* Capital */}
        <Section
          title={SECTIONS[5].name}
          expanded={expandedSections.capital}
          onToggle={() => toggleSection('capital')}
        >
          <div className="space-y-3">
            <NumberInput
              label="Начальный капитал"
              value={settings.initial_capital}
              onChange={(v) => updateSetting('initial_capital', v)}
              min={100}
              max={1000000}
              step={100}
            />
            <NumberInput
              label="Плечо"
              value={settings.leverage}
              onChange={(v) => updateSetting('leverage', v)}
              min={1}
              max={125}
            />
            <Toggle
              label="Комиссия"
              checked={settings.use_commission}
              onChange={(v) => updateSetting('use_commission', v)}
            />
            {settings.use_commission && (
              <NumberInput
                label="Комиссия %"
                value={settings.commission_percent}
                onChange={(v) => updateSetting('commission_percent', v)}
                min={0}
                max={1}
                step={0.01}
              />
            )}
          </div>
        </Section>

        {/* Adaptive */}
        <Section
          title={SECTIONS[6].name}
          expanded={expandedSections.adaptive}
          onToggle={() => toggleSection('adaptive')}
        >
          <div>
            <label className="text-xs text-gray-400 block mb-2">Режим адаптации</label>
            <div className="grid grid-cols-2 gap-2">
              {[
                { value: null, label: 'Выкл' },
                { value: 'indicator', label: 'Индикатор' },
                { value: 'tp', label: 'TP' },
                { value: 'all', label: 'Всё' },
              ].map(opt => (
                <button
                  key={opt.label}
                  onClick={() => updateSetting('adaptive_mode', opt.value)}
                  className={`py-2 px-3 rounded text-sm font-medium transition-colors ${
                    settings.adaptive_mode === opt.value
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-400 hover:text-white'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </Section>
      </div>
    </aside>
  );
}

// ============================================
// SUB-COMPONENTS
// ============================================
function Section({ title, expanded, onToggle, children }) {
  return (
    <div className="border-b border-gray-700">
      <button
        onClick={onToggle}
        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-700/50 transition-colors"
      >
        <span className="font-medium text-sm">{title}</span>
        <span className="text-gray-400">{expanded ? '▼' : '▶'}</span>
      </button>
      {expanded && (
        <div className="px-4 pb-4">
          {children}
        </div>
      )}
    </div>
  );
}

function NumberInput({ label, value, onChange, min, max, step = 1 }) {
  return (
    <div>
      <label className="text-xs text-gray-400 block mb-1">{label}</label>
      <input
        type="number"
        value={value}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        min={min}
        max={max}
        step={step}
        className="w-full bg-gray-700 px-3 py-1.5 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
    </div>
  );
}

function Toggle({ label, checked, onChange }) {
  return (
    <label className="flex items-center justify-between cursor-pointer">
      <span className="text-sm text-gray-300">{label}</span>
      <button
        onClick={() => onChange(!checked)}
        className={`w-10 h-5 rounded-full transition-colors relative ${
          checked ? 'bg-blue-600' : 'bg-gray-600'
        }`}
      >
        <span
          className={`absolute top-0.5 w-4 h-4 bg-white rounded-full transition-transform ${
            checked ? 'translate-x-5' : 'translate-x-0.5'
          }`}
        />
      </button>
    </label>
  );
}
