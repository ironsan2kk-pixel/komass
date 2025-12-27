import React, { useState, useMemo } from 'react';

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
        value={value}
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
      checked={checked}
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
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="bg-gray-700 text-white text-xs rounded px-2 py-1"
    >
      {options.map(opt => (
        <option key={opt.value} value={opt.value}>{opt.label}</option>
      ))}
    </select>
  </div>
);

const SettingsSidebar = ({ settings, onUpdate, collapsed, onToggle, dataRange }) => {
  const update = (key, value) => onUpdate(key, value);

  // Calculate quick period presets based on available data
  const periodPresets = useMemo(() => {
    const now = new Date();
    const presets = [
      { label: 'Всё', value: 'all' },
      { label: '1 год', value: '1y', months: 12 },
      { label: '6 мес', value: '6m', months: 6 },
      { label: '3 мес', value: '3m', months: 3 },
      { label: '1 мес', value: '1m', months: 1 },
    ];
    
    return presets.map(p => {
      if (p.value === 'all') {
        return { ...p, startDate: null, endDate: null };
      }
      const startDate = new Date(now);
      startDate.setMonth(startDate.getMonth() - p.months);
      return { 
        ...p, 
        startDate: startDate.toISOString().split('T')[0],
        endDate: now.toISOString().split('T')[0]
      };
    });
  }, []);

  const applyPeriodPreset = (preset) => {
    if (preset.value === 'all') {
      update('start_date', null);
      update('end_date', null);
    } else {
      update('start_date', preset.startDate);
      update('end_date', preset.endDate);
    }
  };

  // Determine which preset is currently active
  const activePreset = useMemo(() => {
    if (!settings.start_date && !settings.end_date) return 'all';
    
    // Check if matches any preset
    for (const p of periodPresets) {
      if (p.startDate === settings.start_date && p.endDate === settings.end_date) {
        return p.value;
      }
    }
    return null; // Custom range
  }, [settings.start_date, settings.end_date, periodPresets]);

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
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700">
        <span className="text-sm font-bold text-white">⚙️ Настройки</span>
        <button onClick={onToggle} className="text-gray-500 hover:text-white text-xs">
          ◀
        </button>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto">
        
        {/* Data Period Selection - NEW SECTION */}
        <Section title="Период данных" icon="📅">
          {/* Quick preset buttons */}
          <div className="flex flex-wrap gap-1 mb-2">
            {periodPresets.map(preset => (
              <button
                key={preset.value}
                onClick={() => applyPeriodPreset(preset)}
                className={`px-2 py-1 text-xs rounded transition-colors ${
                  activePreset === preset.value
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
          
          {/* Date inputs */}
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400 w-10">От:</span>
              <input
                type="date"
                value={settings.start_date || ''}
                onChange={(e) => update('start_date', e.target.value || null)}
                min={dataRange?.available_start}
                max={settings.end_date || dataRange?.available_end}
                className="flex-1 bg-gray-700 text-white text-xs rounded px-2 py-1"
              />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-400 w-10">До:</span>
              <input
                type="date"
                value={settings.end_date || ''}
                onChange={(e) => update('end_date', e.target.value || null)}
                min={settings.start_date || dataRange?.available_start}
                max={dataRange?.available_end}
                className="flex-1 bg-gray-700 text-white text-xs rounded px-2 py-1"
              />
            </div>
          </div>
          
          {/* Show available range info */}
          {dataRange && (
            <div className="mt-2 p-2 bg-gray-700/50 rounded text-xs">
              <div className="flex justify-between text-gray-400">
                <span>Доступно:</span>
                <span className="text-gray-300">
                  {dataRange.available_start} — {dataRange.available_end}
                </span>
              </div>
              <div className="flex justify-between text-gray-400 mt-1">
                <span>Свечей:</span>
                <span className="text-gray-300">
                  {dataRange.used_candles?.toLocaleString()} / {dataRange.total_candles?.toLocaleString()}
                </span>
              </div>
            </div>
          )}
          
          {/* Validation warning */}
          {settings.start_date && settings.end_date && settings.start_date >= settings.end_date && (
            <div className="mt-1 p-2 bg-red-900/30 border border-red-700 rounded text-xs text-red-400">
              ⚠️ Дата начала должна быть раньше даты окончания
            </div>
          )}
        </Section>

        {/* TRG Indicator */}
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

        {/* Take Profits */}
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
          
          {Array.from({ length: settings.tp_count }, (_, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <span className={`w-8 text-center py-0.5 rounded ${
                i === 0 ? 'bg-green-600' : i === 1 ? 'bg-blue-600' : i === 2 ? 'bg-purple-600' : 'bg-gray-600'
              } text-white`}>
                TP{i + 1}
              </span>
              <input
                type="number"
                value={settings[`tp${i + 1}_percent`]}
                onChange={(e) => update(`tp${i + 1}_percent`, parseFloat(e.target.value) || 0)}
                step={0.1}
                className="w-14 bg-gray-700 text-white rounded px-1 py-0.5 text-right"
              />
              <span className="text-gray-500">%</span>
              <input
                type="number"
                value={settings[`tp${i + 1}_amount`]}
                onChange={(e) => update(`tp${i + 1}_amount`, parseFloat(e.target.value) || 0)}
                className="w-12 bg-gray-700 text-white rounded px-1 py-0.5 text-right"
              />
              <span className="text-gray-500">amt</span>
            </div>
          ))}
        </Section>

        {/* Stop Loss */}
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

        {/* Leverage & Commission */}
        <Section title="Плечо и комиссия" icon="⚡" defaultOpen={false}>
          <NumberInput 
            label="Leverage" 
            value={settings.leverage || 1} 
            onChange={(v) => update('leverage', v)}
            min={1} max={125} step={1}
            suffix="x"
          />
          <Checkbox 
            label="Учитывать комиссию" 
            checked={settings.use_commission || false} 
            onChange={(v) => update('use_commission', v)} 
          />
          {settings.use_commission && (
            <NumberInput 
              label="Комиссия" 
              value={settings.commission_percent || 0.1} 
              onChange={(v) => update('commission_percent', v)}
              min={0} max={1} step={0.01}
              suffix="%"
            />
          )}
        </Section>

        {/* Filters */}
        <Section title="Фильтры" icon="🔍" defaultOpen={false}>
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

        {/* Re-entry */}
        <Section title="Повторные входы" icon="🔄" defaultOpen={false}>
          <Checkbox 
            label="Разрешить повторный вход" 
            checked={settings.allow_reentry} 
            onChange={(v) => update('allow_reentry', v)} 
          />
          <Checkbox 
            label="После SL" 
            checked={settings.reentry_after_sl} 
            onChange={(v) => update('reentry_after_sl', v)} 
          />
          <Checkbox 
            label="После TP" 
            checked={settings.reentry_after_tp} 
            onChange={(v) => update('reentry_after_tp', v)} 
          />
        </Section>

        {/* Adaptive Optimization */}
        <Section title="Адаптивный режим" icon="⚡" defaultOpen={false}>
          <Select
            label="Режим"
            value={settings.adaptive_mode || ''}
            onChange={(v) => update('adaptive_mode', v || null)}
            options={[
              { value: '', label: 'Выключен' },
              { value: 'indicator', label: 'Индикатор' },
              { value: 'tp', label: 'Take Profits' },
              { value: 'all', label: 'Всё' }
            ]}
          />
          <p className="text-xs text-gray-500 mt-1">
            Параметры пересчитываются каждые 20 сделок
          </p>
        </Section>

        {/* Capital */}
        <Section title="Капитал" icon="💰" defaultOpen={false}>
          <NumberInput 
            label="Начальный капитал" 
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
