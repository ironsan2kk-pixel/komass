/**
 * PresetModal - Modal for creating, editing, or cloning presets
 * 
 * Features:
 * - Dynamic form based on indicator type (TRG/Dominant)
 * - Validation
 * - Preview of params
 * 
 * Chat: #31-33 — Presets Full Module
 */
import { useState, useEffect } from 'react';

// Category options
const CATEGORIES = [
  { value: 'scalp', label: 'Скальп' },
  { value: 'short-term', label: 'Краткосрочные' },
  { value: 'mid-term', label: 'Среднесрочные' },
  { value: 'swing', label: 'Свинг' },
  { value: 'long-term', label: 'Долгосрочные' },
  { value: 'special', label: 'Специальные' },
];

// Filter type names for Dominant
const DOMINANT_FILTER_TYPES = [
  { value: 0, label: 'None (без фильтра)' },
  { value: 1, label: 'ATR Condition' },
  { value: 2, label: 'RSI' },
  { value: 3, label: 'ATR + RSI' },
  { value: 4, label: 'Volatility' },
];

// SL modes for Dominant
const DOMINANT_SL_MODES = [
  { value: 0, label: 'No SL movement' },
  { value: 1, label: 'After TP1' },
  { value: 2, label: 'After TP2' },
  { value: 3, label: 'After TP3' },
  { value: 4, label: 'Cascade' },
];

// TRG SL modes
const TRG_SL_MODES = [
  { value: 'fixed', label: 'Fixed' },
  { value: 'breakeven', label: 'Breakeven' },
  { value: 'cascade', label: 'Cascade' },
];

export default function PresetModal({ mode, preset, onClose, onSave }) {
  const isCreate = mode === 'create';
  const isClone = mode === 'clone';
  const isEdit = mode === 'edit';
  
  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [indicatorType, setIndicatorType] = useState('dominant');
  const [category, setCategory] = useState('mid-term');
  const [tags, setTags] = useState('');
  
  // Dominant params
  const [sensitivity, setSensitivity] = useState(21);
  const [tp1Percent, setTp1Percent] = useState(2.5);
  const [tp2Percent, setTp2Percent] = useState(5.0);
  const [tp3Percent, setTp3Percent] = useState(7.5);
  const [tp4Percent, setTp4Percent] = useState(10.0);
  const [slPercent, setSlPercent] = useState(3.0);
  const [filterType, setFilterType] = useState(0);
  const [slMode, setSlMode] = useState(0);
  const [fixedStop, setFixedStop] = useState(true);
  
  // TRG params
  const [i1, setI1] = useState(45);
  const [i2, setI2] = useState(4.0);
  const [trgTpPercents, setTrgTpPercents] = useState([1.05, 1.95, 3.75, 6.0]);
  const [trgTpAmounts, setTrgTpAmounts] = useState([50, 30, 15, 5]);
  const [trgSlPercent, setTrgSlPercent] = useState(2.0);
  const [trgSlMode, setTrgSlMode] = useState('fixed');
  
  // Errors
  const [errors, setErrors] = useState({});
  
  // Initialize from preset
  useEffect(() => {
    if (preset) {
      setName(isClone ? `${preset.name} (Copy)` : preset.name);
      setDescription(preset.description || '');
      setIndicatorType(preset.indicator_type || 'dominant');
      setCategory(preset.category || 'mid-term');
      setTags(preset.tags?.join(', ') || '');
      
      const params = preset.params || {};
      
      if (preset.indicator_type === 'trg') {
        setI1(params.i1 || 45);
        setI2(params.i2 || 4.0);
        setTrgTpPercents(params.tp_percents || [1.05, 1.95, 3.75, 6.0]);
        setTrgTpAmounts(params.tp_amounts || [50, 30, 15, 5]);
        setTrgSlPercent(params.sl_percent || 2.0);
        setTrgSlMode(params.sl_mode || 'fixed');
      } else {
        setSensitivity(params.sensitivity || 21);
        setTp1Percent(params.tp1_percent || 2.5);
        setTp2Percent(params.tp2_percent || 5.0);
        setTp3Percent(params.tp3_percent || 7.5);
        setTp4Percent(params.tp4_percent || 10.0);
        setSlPercent(params.sl_percent || 3.0);
        setFilterType(params.filter_type || 0);
        setSlMode(params.sl_mode || 0);
        setFixedStop(params.fixed_stop !== false);
      }
    }
  }, [preset, isClone]);
  
  // Validation
  const validate = () => {
    const newErrors = {};
    
    if (!name.trim()) {
      newErrors.name = 'Название обязательно';
    }
    
    if (indicatorType === 'dominant') {
      if (sensitivity < 10 || sensitivity > 100) {
        newErrors.sensitivity = 'Sensitivity должен быть от 10 до 100';
      }
      if (tp1Percent <= 0 || tp1Percent > 50) {
        newErrors.tp1 = 'TP1 должен быть от 0.1 до 50%';
      }
      if (slPercent <= 0 || slPercent > 50) {
        newErrors.sl = 'SL должен быть от 0.1 до 50%';
      }
    } else {
      if (i1 < 10 || i1 > 200) {
        newErrors.i1 = 'i1 должен быть от 10 до 200';
      }
      if (i2 < 1 || i2 > 10) {
        newErrors.i2 = 'i2 должен быть от 1 до 10';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  // Submit
  const handleSubmit = () => {
    if (!validate()) return;
    
    // Build params
    let params = {};
    
    if (indicatorType === 'dominant') {
      params = {
        sensitivity: Number(sensitivity),
        tp1_percent: Number(tp1Percent),
        tp2_percent: Number(tp2Percent),
        tp3_percent: Number(tp3Percent),
        tp4_percent: Number(tp4Percent),
        sl_percent: Number(slPercent),
        filter_type: Number(filterType),
        sl_mode: Number(slMode),
        fixed_stop: fixedStop,
      };
    } else {
      params = {
        i1: Number(i1),
        i2: Number(i2),
        tp_count: trgTpPercents.length,
        tp_percents: trgTpPercents.map(Number),
        tp_amounts: trgTpAmounts.map(Number),
        sl_percent: Number(trgSlPercent),
        sl_mode: trgSlMode,
      };
    }
    
    const presetData = {
      name: name.trim(),
      description: description.trim() || null,
      indicator_type: indicatorType,
      category,
      params,
      tags: tags.split(',').map(t => t.trim()).filter(Boolean),
      source: 'manual',
    };
    
    onSave(presetData);
  };
  
  // Update TRG TP
  const updateTrgTp = (index, field, value) => {
    if (field === 'percent') {
      const newPercents = [...trgTpPercents];
      newPercents[index] = Number(value);
      setTrgTpPercents(newPercents);
    } else {
      const newAmounts = [...trgTpAmounts];
      newAmounts[index] = Number(value);
      setTrgTpAmounts(newAmounts);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <h2 className="text-xl font-bold">
            {isCreate && '➕ Новый пресет'}
            {isEdit && '✏️ Редактировать пресет'}
            {isClone && '📋 Клонировать пресет'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-2xl"
          >
            ×
          </button>
        </div>
        
        {/* Body */}
        <div className="p-4 overflow-y-auto max-h-[calc(90vh-120px)]">
          {/* Basic info */}
          <div className="space-y-4 mb-6">
            <div>
              <label className="block text-gray-400 text-sm mb-1">Название *</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className={`w-full px-3 py-2 bg-gray-700 border rounded focus:outline-none ${
                  errors.name ? 'border-red-500' : 'border-gray-600 focus:border-blue-500'
                }`}
                placeholder="My Preset"
              />
              {errors.name && <span className="text-red-400 text-xs">{errors.name}</span>}
            </div>
            
            <div>
              <label className="block text-gray-400 text-sm mb-1">Описание</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                placeholder="Описание пресета..."
                rows={2}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-gray-400 text-sm mb-1">Индикатор</label>
                <select
                  value={indicatorType}
                  onChange={(e) => setIndicatorType(e.target.value)}
                  disabled={isEdit}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none disabled:opacity-50"
                >
                  <option value="dominant">Dominant</option>
                  <option value="trg">TRG</option>
                </select>
              </div>
              
              <div>
                <label className="block text-gray-400 text-sm mb-1">Категория</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                >
                  {CATEGORIES.map(cat => (
                    <option key={cat.value} value={cat.value}>{cat.label}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div>
              <label className="block text-gray-400 text-sm mb-1">Теги (через запятую)</label>
              <input
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                placeholder="btc, trending, aggressive"
              />
            </div>
          </div>
          
          {/* Divider */}
          <div className="border-t border-gray-700 my-4" />
          
          {/* Indicator-specific params */}
          {indicatorType === 'dominant' ? (
            <div className="space-y-4">
              <h3 className="font-semibold text-lg">🎯 Параметры Dominant</h3>
              
              {/* Sensitivity */}
              <div>
                <label className="block text-gray-400 text-sm mb-1">
                  Sensitivity (10-100)
                </label>
                <input
                  type="number"
                  value={sensitivity}
                  onChange={(e) => setSensitivity(e.target.value)}
                  min={10}
                  max={100}
                  step={1}
                  className={`w-full px-3 py-2 bg-gray-700 border rounded focus:outline-none ${
                    errors.sensitivity ? 'border-red-500' : 'border-gray-600 focus:border-blue-500'
                  }`}
                />
                {errors.sensitivity && <span className="text-red-400 text-xs">{errors.sensitivity}</span>}
              </div>
              
              {/* Take Profits */}
              <div className="grid grid-cols-4 gap-2">
                {[
                  { label: 'TP1 %', value: tp1Percent, setter: setTp1Percent },
                  { label: 'TP2 %', value: tp2Percent, setter: setTp2Percent },
                  { label: 'TP3 %', value: tp3Percent, setter: setTp3Percent },
                  { label: 'TP4 %', value: tp4Percent, setter: setTp4Percent },
                ].map(({ label, value, setter }) => (
                  <div key={label}>
                    <label className="block text-gray-400 text-xs mb-1">{label}</label>
                    <input
                      type="number"
                      value={value}
                      onChange={(e) => setter(e.target.value)}
                      min={0.1}
                      max={50}
                      step={0.1}
                      className="w-full px-2 py-1.5 bg-gray-700 border border-gray-600 rounded text-sm focus:border-blue-500 focus:outline-none"
                    />
                  </div>
                ))}
              </div>
              
              {/* Stop Loss */}
              <div>
                <label className="block text-gray-400 text-sm mb-1">Stop Loss %</label>
                <input
                  type="number"
                  value={slPercent}
                  onChange={(e) => setSlPercent(e.target.value)}
                  min={0.1}
                  max={50}
                  step={0.1}
                  className={`w-full px-3 py-2 bg-gray-700 border rounded focus:outline-none ${
                    errors.sl ? 'border-red-500' : 'border-gray-600 focus:border-blue-500'
                  }`}
                />
                {errors.sl && <span className="text-red-400 text-xs">{errors.sl}</span>}
              </div>
              
              {/* Filter Type & SL Mode */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-400 text-sm mb-1">Filter Type</label>
                  <select
                    value={filterType}
                    onChange={(e) => setFilterType(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                  >
                    {DOMINANT_FILTER_TYPES.map(ft => (
                      <option key={ft.value} value={ft.value}>{ft.label}</option>
                    ))}
                  </select>
                </div>
                
                <div>
                  <label className="block text-gray-400 text-sm mb-1">SL Mode</label>
                  <select
                    value={slMode}
                    onChange={(e) => setSlMode(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                  >
                    {DOMINANT_SL_MODES.map(m => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              {/* Fixed Stop */}
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={fixedStop}
                  onChange={(e) => setFixedStop(e.target.checked)}
                  className="w-4 h-4 rounded"
                />
                <span className="text-gray-300">Fixed Stop (SL от цены входа)</span>
              </label>
            </div>
          ) : (
            <div className="space-y-4">
              <h3 className="font-semibold text-lg">📈 Параметры TRG</h3>
              
              {/* i1 & i2 */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-400 text-sm mb-1">
                    i1 (ATR Length: 10-200)
                  </label>
                  <input
                    type="number"
                    value={i1}
                    onChange={(e) => setI1(e.target.value)}
                    min={10}
                    max={200}
                    className={`w-full px-3 py-2 bg-gray-700 border rounded focus:outline-none ${
                      errors.i1 ? 'border-red-500' : 'border-gray-600 focus:border-blue-500'
                    }`}
                  />
                  {errors.i1 && <span className="text-red-400 text-xs">{errors.i1}</span>}
                </div>
                
                <div>
                  <label className="block text-gray-400 text-sm mb-1">
                    i2 (Multiplier: 1-10)
                  </label>
                  <input
                    type="number"
                    value={i2}
                    onChange={(e) => setI2(e.target.value)}
                    min={1}
                    max={10}
                    step={0.1}
                    className={`w-full px-3 py-2 bg-gray-700 border rounded focus:outline-none ${
                      errors.i2 ? 'border-red-500' : 'border-gray-600 focus:border-blue-500'
                    }`}
                  />
                  {errors.i2 && <span className="text-red-400 text-xs">{errors.i2}</span>}
                </div>
              </div>
              
              {/* Take Profits */}
              <div>
                <label className="block text-gray-400 text-sm mb-2">Take Profits</label>
                <div className="space-y-2">
                  {trgTpPercents.map((percent, index) => (
                    <div key={index} className="flex items-center gap-2">
                      <span className="text-gray-500 w-10">TP{index + 1}</span>
                      <input
                        type="number"
                        value={percent}
                        onChange={(e) => updateTrgTp(index, 'percent', e.target.value)}
                        min={0.1}
                        max={50}
                        step={0.01}
                        className="w-24 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-sm"
                        placeholder="%"
                      />
                      <span className="text-gray-500">%</span>
                      <input
                        type="number"
                        value={trgTpAmounts[index]}
                        onChange={(e) => updateTrgTp(index, 'amount', e.target.value)}
                        min={1}
                        max={100}
                        className="w-20 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-sm"
                        placeholder="Amount"
                      />
                      <span className="text-gray-500">% позиции</span>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Stop Loss */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-gray-400 text-sm mb-1">SL %</label>
                  <input
                    type="number"
                    value={trgSlPercent}
                    onChange={(e) => setTrgSlPercent(e.target.value)}
                    min={0.1}
                    max={50}
                    step={0.1}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                  />
                </div>
                
                <div>
                  <label className="block text-gray-400 text-sm mb-1">SL Mode</label>
                  <select
                    value={trgSlMode}
                    onChange={(e) => setTrgSlMode(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded focus:border-blue-500 focus:outline-none"
                  >
                    {TRG_SL_MODES.map(m => (
                      <option key={m.value} value={m.value}>{m.label}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t border-gray-700 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded"
          >
            Отмена
          </button>
          <button
            onClick={handleSubmit}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded font-medium"
          >
            {isCreate && '➕ Создать'}
            {isEdit && '💾 Сохранить'}
            {isClone && '📋 Клонировать'}
          </button>
        </div>
      </div>
    </div>
  );
}
