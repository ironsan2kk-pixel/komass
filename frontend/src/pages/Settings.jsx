import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Settings, Save, Plus, Trash2, Copy, Loader2, 
  Bell, Key, Send, CheckCircle, XCircle, Eye, EyeOff,
  MessageSquare, Zap, AlertTriangle, Target
} from 'lucide-react'
import toast from 'react-hot-toast'
import { presetsApi, symbolsApi, notificationsApi } from '../services/api'

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('presets')
  
  const tabs = [
    { id: 'presets', label: 'Пресеты', icon: Settings },
    { id: 'notifications', label: 'Уведомления', icon: Bell },
    { id: 'apikeys', label: 'API ключи', icon: Key },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Настройки</h1>
        <p className="text-gray-500">Управление пресетами, уведомлениями и конфигурацией</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-800">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-primary-500 text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'presets' && <PresetsTab />}
      {activeTab === 'notifications' && <NotificationsTab />}
      {activeTab === 'apikeys' && <ApiKeysTab />}
    </div>
  )
}


// ============ PRESETS TAB ============

function PresetsTab() {
  const queryClient = useQueryClient()
  const [selectedPreset, setSelectedPreset] = useState(null)
  const [isCreating, setIsCreating] = useState(false)

  const { data: presets } = useQuery({
    queryKey: ['presets'],
    queryFn: () => presetsApi.getAll().then(r => r.data),
  })

  const { data: symbols } = useQuery({
    queryKey: ['symbols'],
    queryFn: () => symbolsApi.getAll().then(r => r.data),
  })

  const createMutation = useMutation({
    mutationFn: presetsApi.create,
    onSuccess: () => {
      toast.success('Пресет создан')
      queryClient.invalidateQueries(['presets'])
      setIsCreating(false)
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }) => presetsApi.update(id, data),
    onSuccess: () => {
      toast.success('Пресет обновлён')
      queryClient.invalidateQueries(['presets'])
    },
  })

  const deleteMutation = useMutation({
    mutationFn: presetsApi.delete,
    onSuccess: () => {
      toast.success('Пресет удалён')
      queryClient.invalidateQueries(['presets'])
      setSelectedPreset(null)
    },
  })

  const duplicateMutation = useMutation({
    mutationFn: presetsApi.duplicate,
    onSuccess: () => {
      toast.success('Пресет скопирован')
      queryClient.invalidateQueries(['presets'])
    },
  })

  const [form, setForm] = useState({
    name: '',
    symbol: 'BTCUSDT',
    exchange: 'binance',
    timeframe: '1h',
    trg_length: 11,
    trg_atr_length: 11,
    trg_multiplier: 1.0,
    tp_enabled: true,
    sl_mode: 'trailing',
    sl_percent: 2.0,
    sl_activate_at_tp: 3,
    sl_trailing_offset: 0.5,
    use_supertrend_filter: false,
    supertrend_length: 10,
    supertrend_multiplier: 3.0,
    use_rsi_filter: false,
    rsi_length: 14,
    rsi_overbought: 70,
    rsi_oversold: 30,
    use_adx_filter: false,
    adx_length: 14,
    adx_threshold: 25,
    use_volume_filter: false,
    volume_ma_length: 20,
    volume_multiplier: 1.5,
  })

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : 
              type === 'number' ? parseFloat(value) : value
    }))
  }

  const handleSelectPreset = (preset) => {
    setSelectedPreset(preset)
    setForm({ ...preset })
    setIsCreating(false)
  }

  const handleSave = () => {
    if (isCreating) {
      createMutation.mutate(form)
    } else if (selectedPreset) {
      updateMutation.mutate({ id: selectedPreset.id, data: form })
    }
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
      {/* Presets List */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <span>Пресеты</span>
          <button
            onClick={() => {
              setIsCreating(true)
              setSelectedPreset(null)
              setForm(prev => ({ ...prev, name: 'Новый пресет' }))
            }}
            className="btn-ghost btn-sm"
          >
            <Plus className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-2">
          {presets?.items?.map((preset) => (
            <div
              key={preset.id}
              onClick={() => handleSelectPreset(preset)}
              className={`p-3 rounded-lg cursor-pointer transition-colors ${
                selectedPreset?.id === preset.id
                  ? 'bg-primary-600/20 border border-primary-500/50'
                  : 'bg-gray-800/50 hover:bg-gray-800'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium">{preset.name}</span>
                <div className="flex gap-1">
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      duplicateMutation.mutate(preset.id)
                    }}
                    className="p-1 hover:bg-gray-700 rounded"
                  >
                    <Copy className="h-3 w-3 text-gray-500" />
                  </button>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {preset.symbol} • {preset.timeframe}
              </p>
            </div>
          ))}
          {(!presets?.items || presets.items.length === 0) && (
            <p className="text-gray-500 text-sm text-center py-4">Нет пресетов</p>
          )}
        </div>
      </div>

      {/* Preset Editor */}
      <div className="lg:col-span-3 card">
        {(selectedPreset || isCreating) ? (
          <div className="space-y-6">
            <div className="card-header flex items-center justify-between">
              <span>{isCreating ? 'Новый пресет' : 'Редактирование'}</span>
              <div className="flex gap-2">
                {selectedPreset && (
                  <button
                    onClick={() => deleteMutation.mutate(selectedPreset.id)}
                    className="btn-danger btn-sm"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
                <button onClick={handleSave} className="btn-primary btn-sm">
                  <Save className="h-4 w-4 mr-1" />
                  Сохранить
                </button>
              </div>
            </div>

            {/* Basic Settings */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="label">Название</label>
                <input type="text" name="name" value={form.name} onChange={handleChange} className="input" />
              </div>
              <div>
                <label className="label">Символ</label>
                <select name="symbol" value={form.symbol} onChange={handleChange} className="select">
                  {symbols?.items?.map(s => (
                    <option key={s.symbol} value={s.symbol}>{s.symbol}</option>
                  ))}
                  <option value="BTCUSDT">BTCUSDT</option>
                  <option value="ETHUSDT">ETHUSDT</option>
                </select>
              </div>
              <div>
                <label className="label">Биржа</label>
                <select name="exchange" value={form.exchange} onChange={handleChange} className="select">
                  <option value="binance">Binance</option>
                  <option value="bybit">Bybit</option>
                  <option value="okx">OKX</option>
                </select>
              </div>
              <div>
                <label className="label">Таймфрейм</label>
                <select name="timeframe" value={form.timeframe} onChange={handleChange} className="select">
                  <option value="1m">1m</option>
                  <option value="5m">5m</option>
                  <option value="15m">15m</option>
                  <option value="1h">1h</option>
                  <option value="4h">4h</option>
                  <option value="1d">1d</option>
                </select>
              </div>
            </div>

            {/* TRG Settings */}
            <div className="border-t border-gray-800 pt-4">
              <h4 className="text-sm font-medium text-gray-400 mb-3">TRG Индикатор</h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="label">Length</label>
                  <input type="number" name="trg_length" value={form.trg_length} onChange={handleChange} className="input" />
                </div>
                <div>
                  <label className="label">ATR Length</label>
                  <input type="number" name="trg_atr_length" value={form.trg_atr_length} onChange={handleChange} className="input" />
                </div>
                <div>
                  <label className="label">Multiplier</label>
                  <input type="number" step="0.1" name="trg_multiplier" value={form.trg_multiplier} onChange={handleChange} className="input" />
                </div>
              </div>
            </div>

            {/* SL Settings */}
            <div className="border-t border-gray-800 pt-4">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Stop Loss</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="label">Режим</label>
                  <select name="sl_mode" value={form.sl_mode} onChange={handleChange} className="select">
                    <option value="static">Static</option>
                    <option value="breakeven">Breakeven</option>
                    <option value="trailing">Trailing</option>
                  </select>
                </div>
                <div>
                  <label className="label">SL %</label>
                  <input type="number" step="0.1" name="sl_percent" value={form.sl_percent} onChange={handleChange} className="input" />
                </div>
                <div>
                  <label className="label">Активация на TP</label>
                  <input type="number" name="sl_activate_at_tp" value={form.sl_activate_at_tp} onChange={handleChange} className="input" />
                </div>
                <div>
                  <label className="label">Trailing offset %</label>
                  <input type="number" step="0.1" name="sl_trailing_offset" value={form.sl_trailing_offset} onChange={handleChange} className="input" />
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="py-16 text-center">
            <Settings className="h-12 w-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500">Выберите пресет для редактирования</p>
          </div>
        )}
      </div>
    </div>
  )
}


// ============ NOTIFICATIONS TAB ============

function NotificationsTab() {
  const [settings, setSettings] = useState({
    enabled: false,
    bot_token: '',
    chat_id: '',
    message_format: 'simple',
    notify_new_signal: true,
    notify_tp_hit: true,
    notify_sl_hit: true,
    notify_signal_closed: true,
    notify_errors: false,
    include_chart_link: false,
    include_entry_zone: true,
    include_leverage: true,
    show_all_targets: true,
    custom_template: ''
  })
  
  const [showToken, setShowToken] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [isValidating, setIsValidating] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [botInfo, setBotInfo] = useState(null)
  const [previewFormat, setPreviewFormat] = useState(null)

  // Load settings on mount
  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const response = await notificationsApi.getSettings()
      if (response.data?.settings) {
        setSettings(response.data.settings)
      }
    } catch (error) {
      console.error('Failed to load settings:', error)
    }
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleValidateBot = async () => {
    setIsValidating(true)
    try {
      const response = await notificationsApi.validateBot(settings.bot_token)
      if (response.data?.valid) {
        setBotInfo(response.data.bot_info)
        toast.success(`Бот @${response.data.bot_info.username} подключён!`)
      } else {
        toast.error(response.data?.error || 'Ошибка валидации')
        setBotInfo(null)
      }
    } catch (error) {
      toast.error('Ошибка подключения к Telegram API')
      setBotInfo(null)
    } finally {
      setIsValidating(false)
    }
  }

  const handleTestNotification = async () => {
    setIsTesting(true)
    try {
      const response = await notificationsApi.test({
        bot_token: settings.bot_token,
        chat_id: settings.chat_id
      })
      if (response.data?.success) {
        toast.success('Тестовое сообщение отправлено!')
      } else {
        toast.error(response.data?.message || 'Ошибка отправки')
      }
    } catch (error) {
      toast.error('Не удалось отправить сообщение')
    } finally {
      setIsTesting(false)
    }
  }

  const handleSave = async () => {
    setIsSaving(true)
    try {
      await notificationsApi.updateSettings(settings)
      toast.success('Настройки сохранены')
    } catch (error) {
      toast.error('Ошибка сохранения')
    } finally {
      setIsSaving(false)
    }
  }

  const handlePreviewFormat = async (format) => {
    try {
      const response = await notificationsApi.previewFormat(format)
      setPreviewFormat(response.data)
    } catch (error) {
      console.error('Preview error:', error)
    }
  }

  return (
    <div className="space-y-6">
      {/* Telegram Settings */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-blue-400" />
            <span>Telegram</span>
          </div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              name="enabled"
              checked={settings.enabled}
              onChange={handleChange}
              className="rounded border-gray-700"
            />
            <span className="text-sm">Включено</span>
          </label>
        </div>
        
        <div className="space-y-4">
          {/* Bot Token */}
          <div>
            <label className="label">Bot Token</label>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <input
                  type={showToken ? 'text' : 'password'}
                  name="bot_token"
                  value={settings.bot_token}
                  onChange={handleChange}
                  placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                  className="input pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowToken(!showToken)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <button
                onClick={handleValidateBot}
                disabled={!settings.bot_token || isValidating}
                className="btn-primary btn-sm"
              >
                {isValidating ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  'Проверить'
                )}
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Получите токен у @BotFather в Telegram
            </p>
          </div>

          {/* Bot Info */}
          {botInfo && (
            <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5 text-green-400" />
                <span className="text-green-400 font-medium">Бот подключён</span>
              </div>
              <div className="mt-2 text-sm text-gray-400">
                <p>@{botInfo.username} ({botInfo.first_name})</p>
                <p className="text-xs">ID: {botInfo.id}</p>
              </div>
            </div>
          )}

          {/* Chat ID */}
          <div>
            <label className="label">Chat ID / Channel</label>
            <input
              type="text"
              name="chat_id"
              value={settings.chat_id}
              onChange={handleChange}
              placeholder="@channel или -1001234567890"
              className="input"
            />
            <p className="text-xs text-gray-500 mt-1">
              ID чата, канала (@channel) или группы. Используйте @userinfobot для получения ID.
            </p>
          </div>

          {/* Test Button */}
          <div className="flex gap-2">
            <button
              onClick={handleTestNotification}
              disabled={!settings.bot_token || !settings.chat_id || isTesting}
              className="btn-secondary btn-sm"
            >
              {isTesting ? (
                <Loader2 className="h-4 w-4 animate-spin mr-1" />
              ) : (
                <Send className="h-4 w-4 mr-1" />
              )}
              Тест
            </button>
          </div>
        </div>
      </div>

      {/* Message Format */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Zap className="h-5 w-5 text-yellow-400" />
          <span>Формат сообщений</span>
        </div>
        
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            {[
              { id: 'simple', name: 'Simple', desc: 'Читаемый формат с эмодзи' },
              { id: 'cornix', name: 'Cornix', desc: 'Совместим с Cornix ботом' },
              { id: 'custom', name: 'Custom', desc: 'Свой шаблон' }
            ].map(format => (
              <label
                key={format.id}
                className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                  settings.message_format === format.id
                    ? 'border-primary-500 bg-primary-500/10'
                    : 'border-gray-700 hover:border-gray-600'
                }`}
              >
                <input
                  type="radio"
                  name="message_format"
                  value={format.id}
                  checked={settings.message_format === format.id}
                  onChange={handleChange}
                  className="sr-only"
                />
                <div className="flex items-center justify-between">
                  <span className="font-medium">{format.name}</span>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault()
                      handlePreviewFormat(format.id)
                    }}
                    className="text-xs text-primary-400 hover:underline"
                  >
                    Preview
                  </button>
                </div>
                <p className="text-xs text-gray-500 mt-1">{format.desc}</p>
              </label>
            ))}
          </div>

          {/* Preview Modal */}
          {previewFormat && (
            <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-400">
                  Превью: {previewFormat.format}
                </span>
                <button
                  onClick={() => setPreviewFormat(null)}
                  className="text-gray-500 hover:text-gray-300"
                >
                  ✕
                </button>
              </div>
              <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono bg-gray-900 p-3 rounded">
                {previewFormat.preview}
              </pre>
            </div>
          )}

          {/* Custom Template */}
          {settings.message_format === 'custom' && (
            <div>
              <label className="label">Шаблон</label>
              <textarea
                name="custom_template"
                value={settings.custom_template}
                onChange={handleChange}
                rows={6}
                placeholder={`📈 {direction} {symbol}\n\nEntry: {entry_price}\nTargets: {tp_targets}\nSL: {sl_price}\n\nLeverage: {leverage}x`}
                className="input font-mono text-sm"
              />
              <p className="text-xs text-gray-500 mt-1">
                Доступные переменные: {'{symbol}'}, {'{direction}'}, {'{entry_price}'}, {'{tp_targets}'}, {'{sl_price}'}, {'{leverage}'}, {'{timeframe}'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Trigger Settings */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Target className="h-5 w-5 text-red-400" />
          <span>Триггеры уведомлений</span>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          {[
            { name: 'notify_new_signal', label: 'Новый сигнал', icon: '📈' },
            { name: 'notify_tp_hit', label: 'TP достигнут', icon: '🎯' },
            { name: 'notify_sl_hit', label: 'SL сработал', icon: '🛑' },
            { name: 'notify_signal_closed', label: 'Сигнал закрыт', icon: '✅' },
            { name: 'notify_errors', label: 'Ошибки системы', icon: '⚠️' },
          ].map(trigger => (
            <label
              key={trigger.name}
              className="flex items-center gap-3 p-3 bg-gray-800/50 rounded-lg cursor-pointer hover:bg-gray-800"
            >
              <input
                type="checkbox"
                name={trigger.name}
                checked={settings[trigger.name]}
                onChange={handleChange}
                className="rounded border-gray-700"
              />
              <span>{trigger.icon}</span>
              <span className="text-sm">{trigger.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Display Options */}
      <div className="card">
        <div className="card-header">Опции отображения</div>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { name: 'include_entry_zone', label: 'Зона входа' },
            { name: 'include_leverage', label: 'Плечо' },
            { name: 'show_all_targets', label: 'Все таргеты' },
            { name: 'include_chart_link', label: 'Ссылка на график' },
          ].map(option => (
            <label
              key={option.name}
              className="flex items-center gap-2 text-sm"
            >
              <input
                type="checkbox"
                name={option.name}
                checked={settings[option.name]}
                onChange={handleChange}
                className="rounded border-gray-700"
              />
              <span>{option.label}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="btn-primary"
        >
          {isSaving ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <Save className="h-4 w-4 mr-2" />
          )}
          Сохранить настройки
        </button>
      </div>
    </div>
  )
}


// ============ API KEYS TAB ============

function ApiKeysTab() {
  const [keys, setKeys] = useState({
    binance_key: '',
    binance_secret: '',
    bybit_key: '',
    bybit_secret: '',
    okx_key: '',
    okx_secret: '',
    okx_passphrase: ''
  })
  
  const [showSecrets, setShowSecrets] = useState({})

  const handleChange = (e) => {
    const { name, value } = e.target
    setKeys(prev => ({ ...prev, [name]: value }))
  }

  const toggleSecret = (key) => {
    setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }))
  }

  const exchanges = [
    { id: 'binance', name: 'Binance', color: 'yellow' },
    { id: 'bybit', name: 'Bybit', color: 'orange' },
    { id: 'okx', name: 'OKX', color: 'blue' }
  ]

  return (
    <div className="space-y-6">
      {exchanges.map(exchange => (
        <div key={exchange.id} className="card">
          <div className="card-header flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full bg-${exchange.color}-400`} />
            <span>{exchange.name}</span>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="label">API Key</label>
              <input
                type="text"
                name={`${exchange.id}_key`}
                value={keys[`${exchange.id}_key`]}
                onChange={handleChange}
                placeholder="Enter API Key"
                className="input"
              />
            </div>
            
            <div>
              <label className="label">API Secret</label>
              <div className="relative">
                <input
                  type={showSecrets[`${exchange.id}_secret`] ? 'text' : 'password'}
                  name={`${exchange.id}_secret`}
                  value={keys[`${exchange.id}_secret`]}
                  onChange={handleChange}
                  placeholder="Enter API Secret"
                  className="input pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleSecret(`${exchange.id}_secret`)}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showSecrets[`${exchange.id}_secret`] ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {exchange.id === 'okx' && (
              <div>
                <label className="label">Passphrase</label>
                <div className="relative">
                  <input
                    type={showSecrets.okx_passphrase ? 'text' : 'password'}
                    name="okx_passphrase"
                    value={keys.okx_passphrase}
                    onChange={handleChange}
                    placeholder="Enter Passphrase"
                    className="input pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => toggleSecret('okx_passphrase')}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                  >
                    {showSecrets.okx_passphrase ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      ))}

      <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-yellow-400 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-yellow-400 font-medium">Безопасность</p>
            <p className="text-sm text-gray-400 mt-1">
              API ключи хранятся локально и используются только для торговли. 
              Рекомендуется использовать ключи с ограниченными правами (только торговля, без вывода).
            </p>
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button className="btn-primary">
          <Save className="h-4 w-4 mr-2" />
          Сохранить ключи
        </button>
      </div>
    </div>
  )
}
