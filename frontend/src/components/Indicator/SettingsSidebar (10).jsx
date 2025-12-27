import React, { useState } from 'react';

const Section = ({ title, icon, children, defaultOpen = true }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border-b border-gray-700">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-3 py-2 flex items-center justify-between hover:bg-gray-700/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span>{icon}</span>
          <span className="text-sm font-medium text-gray-200">{title}</span>
        </div>
        <span className="text-gray-500 text-xs">{isOpen ? '▼' : '▶'}</span>
      </button>
      {isOpen && (
        <div className="px-3 pb-3 space-y-2">
          {children}
        </div>
      )}
    </div>
  );
};

const NumberInput = ({ label, value, onChange, min, max, step = 1, suffix = '' }) => (
  <div className="flex items-center justify-between">
    <span className="text-xs text-gray-400">{label}</span>
    <div className="flex items-center gap-1">
      <input
        type="number"
        value={value ?? ''}
        onChange={(e) => onChange(parseFloat(e.target.value) || 0)}
        min={min}
        max={max}
        step={step}
        className="w-16 bg-gray-700 text-white text-xs rounded px-2 py-1 text-right"
      />
      {suffix && <span className="text-xs text-gray-500">{suffix}</span>}
    </div>
  </div>
);

const Checkbox = ({ label, checked, onChange }) => (
  <label className="flex items-center gap-2 cursor-pointer">
    <input
      type="checkbox"
      checked={checked ?? false}
      onChange={(e) => onChange(e.target.checked)}
      className="rounded"
    />
    <span className="text-xs text-gray-300">{label}</span>
  </label>
);

const Select = ({ label, value, onChange, options }) => (
  <div className="flex items-center justify-between">
    <span className="text-xs text-gray-400">{label}</span>
    <select
      value={value ?? ''}
      onChange={(e) => onChange(e.target.value)}
      className="bg-gray-700 text-white text-xs rounded px-2 py-1"
    >
      {options.map(opt => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  </div>
);

const SettingsSidebar = ({ settings = {}, onUpdate, collapsed, onToggle }) => {
  const update = (key, value) => onUpdate?.(key, value);

  if (collapsed) {
    return (
      <div 
        className="w-10 bg-gray-800 border-r border-gray-700 flex flex-col items-center py-2 cursor-pointer"
        onClick={onToggle}
      >
        <span className="text-gray-400 hover:text-white">⚙️</span>
        <span className="text-gray-500 text-xs mt-1 writing-vertical">Settings</span>
      </div>
    );
  }

  return (
    <div className="w-64 bg-gray-800 border-r border-gray-700 flex flex-col overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700">
        <span className="text-sm font-bold text-white">⚙️ Настройки</span>
        <button onClick={onToggle} className="text-gray-500 hover:text-white text-xs">
          ◀
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        
        <Section title="TRG Indicator" icon="📊">
          <NumberInput 
            label="i1 (ATR Length)" 
            value={settings.trg_atr_length} 
            onChange={(v) => update('trg_atr_length', v)}
            min={10} max={200}
          />
          <NumberInput 
            label="i2 (Multiplier)" 
            value={settings.trg_multiplier} 
            onChange={(v) => update('trg_multiplier', v)}
            min={1} max={10} step={0.5}
          />
        </Section>

        <Section title="Take Profits" icon="🎯">
          <div className="flex items-center gap-1 mb-2">
            <span className="text-xs text-gray-400">Count:</span>
            {[1,2,3,4,5,6,7,8,9,10].map(n => (
              <button
                key={n}
                onClick={() => update('tp_count', n)}
                className={`w-5 h-5 text-xs rounded ${
                  settings.tp_count === n ? 'bg-purple-600 text-white' : 'bg-gray-700 text-gray-400'
                }`}
              >
                {n}
              </button>
            ))}
          </div>
          
          {Array.from({ length: settings.tp_count || 4 }, (_, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <span className={`w-8 text-center py-0.5 rounded ${
                i === 0 ? 'bg-green-600' : i === 1 ? 'bg-blue-600' : i === 2 ? 'bg-purple-600' : 'bg-gray-600'
              } text-white`}>
                TP{i + 1}
              </span>
              <input
                type="number"
                value={settings[`tp${i + 1}_percent`] ?? 0}
                onChange={(e) => update(`tp${i + 1}_percent`, parseFloat(e.target.value) || 0)}
                step={0.1}
                className="w-14 bg-gray-700 text-white rounded px-1 py-0.5 text-right"
              />
              <span className="text-gray-500">%</span>
              <input
                type="number"
                value={settings[`tp${i + 1}_amount`] ?? 0}
                onChange={(e) => update(`tp${i + 1}_amount`, parseFloat(e.target.value) || 0)}
                className="w-12 bg-gray-700 text-white rounded px-1 py-0.5 text-right"
              />
              <span className="text-gray-500">amt</span>
            </div>
          ))}
        </Section>

        <Section title="Stop Loss" icon="🛑">
          <NumberInput 
            label="SL %" 
            value={settings.sl_percent} 
            onChange={(v) => update('sl_percent', v)}
            min={1} max={50} step={0.5}
            suffix="%"
          />
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400">Trailing:</span>
            <div className="flex gap-1">
              {[
                { value: 'no', label: 'Фикс' },
                { value: 'breakeven', label: 'БУ' },
                { value: 'moving', label: 'Каскад' }
              ].map(mode => (
                <button
                  key={mode.value}
                  onClick={() => update('sl_trailing_mode', mode.value)}
                  className={`px-2 py-0.5 text-xs rounded ${
                    settings.sl_trailing_mode === mode.value 
                      ? 'bg-purple-600 text-white' 
                      : 'bg-gray-700 text-gray-400'
                  }`}
                >
                  {mode.label}
                </button>
              ))}
            </div>
          </div>
        </Section>

        <Section title="Leverage & Commission" icon="⚡" defaultOpen={false}>
          <NumberInput 
            label="Leverage" 
            value={settings.leverage || 1} 
            onChange={(v) => update('leverage', v)}
            min={1} max={125} step={1}
            suffix="x"
          />
          <Checkbox 
            label="Include commission" 
            checked={settings.use_commission || false} 
            onChange={(v) => update('use_commission', v)} 
          />
          {settings.use_commission && (
            <NumberInput 
              label="Commission" 
              value={settings.commission_percent || 0.1} 
              onChange={(v) => update('commission_percent', v)}
              min={0} max={1} step={0.01}
              suffix="%"
            />
          )}
        </Section>

        <Section title="Filters" icon="🔍" defaultOpen={false}>
          <Checkbox 
            label="SuperTrend" 
            checked={settings.use_supertrend} 
            onChange={(v) => update('use_supertrend', v)} 
          />
          {settings.use_supertrend && (
            <div className="ml-4 space-y-1">
              <NumberInput label="Period" value={settings.supertrend_period} onChange={(v) => update('supertrend_period', v)} min={5} max={50} />
              <NumberInput label="Multiplier" value={settings.supertrend_multiplier} onChange={(v) => update('supertrend_multiplier', v)} min={1} max={10} step={0.5} />
            </div>
          )}

          <Checkbox 
            label="RSI Filter" 
            checked={settings.use_rsi_filter} 
            onChange={(v) => update('use_rsi_filter', v)} 
          />
          {settings.use_rsi_filter && (
            <div className="ml-4 space-y-1">
              <NumberInput label="Period" value={settings.rsi_period} onChange={(v) => update('rsi_period', v)} min={5} max={50} />
              <NumberInput label="Overbought" value={settings.rsi_overbought} onChange={(v) => update('rsi_overbought', v)} min={50} max={100} />
              <NumberInput label="Oversold" value={settings.rsi_oversold} onChange={(v) => update('rsi_oversold', v)} min={0} max={50} />
            </div>
          )}

          <Checkbox 
            label="ADX Filter" 
            checked={settings.use_adx_filter} 
            onChange={(v) => update('use_adx_filter', v)} 
          />
          {settings.use_adx_filter && (
            <div className="ml-4 space-y-1">
              <NumberInput label="Period" value={settings.adx_period} onChange={(v) => update('adx_period', v)} min={5} max={50} />
              <NumberInput label="Threshold" value={settings.adx_threshold} onChange={(v) => update('adx_threshold', v)} min={10} max={50} />
            </div>
          )}

          <Checkbox 
            label="Volume Filter" 
            checked={settings.use_volume_filter} 
            onChange={(v) => update('use_volume_filter', v)} 
          />
        </Section>

        <Section title="Re-entry" icon="🔄" defaultOpen={false}>
          <Checkbox 
            label="Allow re-entry" 
            checked={settings.allow_reentry} 
            onChange={(v) => update('allow_reentry', v)} 
          />
          <Checkbox 
            label="After SL" 
            checked={settings.reentry_after_sl} 
            onChange={(v) => update('reentry_after_sl', v)} 
          />
          <Checkbox 
            label="After TP" 
            checked={settings.reentry_after_tp} 
            onChange={(v) => update('reentry_after_tp', v)} 
          />
        </Section>

        <Section title="Adaptive Mode" icon="⚡" defaultOpen={false}>
          <Select
            label="Mode"
            value={settings.adaptive_mode || ''}
            onChange={(v) => update('adaptive_mode', v || null)}
            options={[
              { value: '', label: 'Disabled' },
              { value: 'indicator', label: 'Indicator' },
              { value: 'tp', label: 'Take Profits' },
              { value: 'all', label: 'All' }
            ]}
          />
          <p className="text-xs text-gray-500 mt-1">
            Parameters recalculated every 20 trades
          </p>
        </Section>

        <Section title="Capital" icon="💰" defaultOpen={false}>
          <NumberInput 
            label="Initial Capital" 
            value={settings.initial_capital} 
            onChange={(v) => update('initial_capital', v)}
            min={100} max={1000000}
            suffix="$"
          />
        </Section>

      </div>
    </div>
  );
};

export default SettingsSidebar;
