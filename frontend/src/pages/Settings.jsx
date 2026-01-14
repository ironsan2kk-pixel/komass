import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Settings, Save, Plus, Trash2, Copy,
  Bell, Key, Send, CheckCircle, XCircle, Eye, EyeOff,
  MessageSquare, Zap, AlertTriangle, Target, List
} from 'lucide-react'
import toast from 'react-hot-toast'
import { presetsApi, symbolsApi, notificationsApi, discordApi } from '../services/api'
import TelegramChannels from '../components/TelegramChannels'
import { Button, Card, Input, Select, Spinner, Alert } from '../components/ui'

export default function SettingsPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState('presets')
  
  const tabs = [
    { id: 'presets', label: 'Пресеты', icon: Settings },
    { id: 'notifications', label: 'Telegram', icon: MessageSquare },
    { id: 'discord', label: 'Discord', icon: Bell },
    { id: 'apikeys', label: 'API ключи', icon: Key },
  ]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Настройки</h1>
        <p className="text-gray-500">Управление пресетами, уведомлениями и конфигурацией</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-dark-700 dark:border-dark-700 light:border-gray-200">
        {tabs.map(tab => (
          <Button
            key={tab.id}
            variant="ghost"
            onClick={() => setActiveTab(tab.id)}
            className={`border-b-2 rounded-none ${
              activeTab === tab.id
                ? 'border-primary-500 text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-300'
            }`}
            icon={<tab.icon className="h-4 w-4" />}
          >
            {tab.label}
          </Button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === 'presets' && <PresetsTab />}
      {activeTab === 'notifications' && <NotificationsTab />}
      {activeTab === 'discord' && <DiscordTab />}
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
      <Card>
        <Card.Header className="flex items-center justify-between">
          <span>Пресеты</span>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => {
              setIsCreating(true)
              setSelectedPreset(null)
              setForm(prev => ({ ...prev, name: 'Новый пресет' }))
            }}
            icon={<Plus className="h-4 w-4" />}
          />
        </Card.Header>
        <Card.Body className="space-y-2">
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
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      duplicateMutation.mutate(preset.id)
                    }}
                    icon={<Copy className="h-3 w-3" />}
                  />
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
        </Card.Body>
      </Card>

      {/* Preset Editor */}
      <Card className="lg:col-span-3">
        {(selectedPreset || isCreating) ? (
          <>
            <Card.Header className="flex items-center justify-between">
              <span>{isCreating ? 'Новый пресет' : 'Редактирование'}</span>
              <div className="flex gap-2">
                {selectedPreset && (
                  <Button
                    variant="danger"
                    size="sm"
                    onClick={() => deleteMutation.mutate(selectedPreset.id)}
                    icon={<Trash2 className="h-4 w-4" />}
                  />
                )}
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleSave}
                  icon={<Save className="h-4 w-4" />}
                >
                  Сохранить
                </Button>
              </div>
            </Card.Header>

            <Card.Body className="space-y-6">

            {/* Basic Settings */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <Input
                label="Название"
                name="name"
                value={form.name}
                onChange={handleChange}
              />
              <Select
                label="Символ"
                name="symbol"
                value={form.symbol}
                onChange={handleChange}
              >
                {symbols?.items?.map(s => (
                  <option key={s.symbol} value={s.symbol}>{s.symbol}</option>
                ))}
                <option value="BTCUSDT">BTCUSDT</option>
                <option value="ETHUSDT">ETHUSDT</option>
              </Select>
              <Select
                label="Биржа"
                name="exchange"
                value={form.exchange}
                onChange={handleChange}
              >
                <option value="binance">Binance</option>
                <option value="bybit">Bybit</option>
                <option value="okx">OKX</option>
              </Select>
              <Select
                label="Таймфрейм"
                name="timeframe"
                value={form.timeframe}
                onChange={handleChange}
              >
                <option value="1m">1m</option>
                <option value="5m">5m</option>
                <option value="15m">15m</option>
                <option value="1h">1h</option>
                <option value="4h">4h</option>
                <option value="1d">1d</option>
              </Select>
            </div>

            {/* TRG Settings */}
            <div className="border-t border-dark-700 dark:border-dark-700 light:border-gray-200 pt-4">
              <h4 className="text-sm font-medium text-gray-400 mb-3">TRG Индикатор</h4>
              <div className="grid grid-cols-3 gap-4">
                <Input
                  label="Length"
                  type="number"
                  name="trg_length"
                  value={form.trg_length}
                  onChange={handleChange}
                />
                <Input
                  label="ATR Length"
                  type="number"
                  name="trg_atr_length"
                  value={form.trg_atr_length}
                  onChange={handleChange}
                />
                <Input
                  label="Multiplier"
                  type="number"
                  step="0.1"
                  name="trg_multiplier"
                  value={form.trg_multiplier}
                  onChange={handleChange}
                />
              </div>
            </div>

            {/* SL Settings */}
            <div className="border-t border-dark-700 dark:border-dark-700 light:border-gray-200 pt-4">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Stop Loss</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Select
                  label="Режим"
                  name="sl_mode"
                  value={form.sl_mode}
                  onChange={handleChange}
                >
                  <option value="static">Static</option>
                  <option value="breakeven">Breakeven</option>
                  <option value="trailing">Trailing</option>
                </Select>
                <Input
                  label="SL %"
                  type="number"
                  step="0.1"
                  name="sl_percent"
                  value={form.sl_percent}
                  onChange={handleChange}
                />
                <Input
                  label="Активация на TP"
                  type="number"
                  name="sl_activate_at_tp"
                  value={form.sl_activate_at_tp}
                  onChange={handleChange}
                />
                <Input
                  label="Trailing offset %"
                  type="number"
                  step="0.1"
                  name="sl_trailing_offset"
                  value={form.sl_trailing_offset}
                  onChange={handleChange}
                />
              </div>
            </div>
            </Card.Body>
          </>
        ) : (
          <Card.Body className="py-16 text-center">
            <Settings className="h-12 w-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500">Выберите пресет для редактирования</p>
          </Card.Body>
        )}
      </Card>
    </div>
  )
}


// ============ NOTIFICATIONS TAB ============

function NotificationsTab() {
  const [telegramSubTab, setTelegramSubTab] = useState('settings')

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
      {/* Sub Tabs */}
      <div className="flex gap-2 border-b border-dark-700 dark:border-dark-700 light:border-gray-200">
        <Button
          variant="ghost"
          onClick={() => setTelegramSubTab('settings')}
          className={`border-b-2 rounded-none ${
            telegramSubTab === 'settings'
              ? 'border-blue-500 text-blue-400'
              : 'border-transparent text-gray-500 hover:text-gray-300'
          }`}
          icon={<Settings className="h-4 w-4" />}
        >
          Настройки
        </Button>
        <Button
          variant="ghost"
          onClick={() => setTelegramSubTab('channels')}
          className={`border-b-2 rounded-none ${
            telegramSubTab === 'channels'
              ? 'border-blue-500 text-blue-400'
              : 'border-transparent text-gray-500 hover:text-gray-300'
          }`}
          icon={<List className="h-4 w-4" />}
        >
          Каналы (Multi-Channel)
        </Button>
      </div>

      {/* Settings Sub Tab */}
      {telegramSubTab === 'settings' && (
        <>
          {/* Telegram Settings */}
          <Card>
            <Card.Header className="flex items-center justify-between">
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
            </Card.Header>

            <Card.Body className="space-y-4">
              {/* Paper Trading Warning */}
              <Alert variant="warning">
                <div className="flex items-start gap-2">
                  <span className="text-lg">📊</span>
                  <div>
                    <p className="font-medium">Telegram сигналы для бумажной торговли</p>
                    <p className="text-sm mt-1 opacity-90">
                      Telegram бот отправляет сигналы ТОЛЬКО для симуляции (paper trading).
                      Все сигналы генерируются на основе бэктестов исторических данных.
                      НЕ используйте эти сигналы для реальной торговли.
                    </p>
                  </div>
                </div>
              </Alert>

          {/* Bot Token */}
          <div>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Input
                  label="Bot Token"
                  type={showToken ? 'text' : 'password'}
                  name="bot_token"
                  value={settings.bot_token}
                  onChange={handleChange}
                  placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                  helper="Получите токен у @BotFather в Telegram"
                />
                <button
                  type="button"
                  onClick={() => setShowToken(!showToken)}
                  className="absolute right-2 top-9 text-gray-500 hover:text-gray-300"
                >
                  {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <div className="pt-6">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleValidateBot}
                  disabled={!settings.bot_token || isValidating}
                  loading={isValidating}
                >
                  Проверить
                </Button>
              </div>
            </div>
          </div>

          {/* Bot Info */}
          {botInfo && (
            <Alert variant="success">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">Бот подключён</span>
              </div>
              <div className="mt-2 text-sm">
                <p>@{botInfo.username} ({botInfo.first_name})</p>
                <p className="text-xs opacity-80">ID: {botInfo.id}</p>
              </div>
            </Alert>
          )}

          {/* Chat ID */}
          <Input
            label="Chat ID / Channel"
            name="chat_id"
            value={settings.chat_id}
            onChange={handleChange}
            placeholder="@channel или -1001234567890"
            helper="ID чата, канала (@channel) или группы. Используйте @userinfobot для получения ID."
          />

          {/* Test Button */}
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleTestNotification}
              disabled={!settings.bot_token || !settings.chat_id || isTesting}
              loading={isTesting}
              icon={<Send className="h-4 w-4" />}
            >
              Тест
            </Button>
          </div>
            </Card.Body>
          </Card>

      {/* Message Format */}
      <Card>
        <Card.Header className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-yellow-400" />
          <span>Формат сообщений</span>
        </Card.Header>

        <Card.Body className="space-y-4">
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
              <label className="block text-sm font-medium text-gray-300 mb-1">Шаблон</label>
              <textarea
                name="custom_template"
                value={settings.custom_template}
                onChange={handleChange}
                rows={6}
                placeholder={`📈 {direction} {symbol}\n\nEntry: {entry_price}\nTargets: {tp_targets}\nSL: {sl_price}\n\nLeverage: {leverage}x`}
                className="w-full px-3 py-2 bg-dark-800 border border-dark-600 rounded-lg text-gray-100 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Доступные переменные: {'{symbol}'}, {'{direction}'}, {'{entry_price}'}, {'{tp_targets}'}, {'{sl_price}'}, {'{leverage}'}, {'{timeframe}'}
              </p>
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Trigger Settings */}
      <Card>
        <Card.Header className="flex items-center gap-2">
          <Target className="h-5 w-5 text-red-400" />
          <span>Триггеры уведомлений</span>
        </Card.Header>

        <Card.Body className="grid grid-cols-2 md:grid-cols-3 gap-4">
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
        </Card.Body>
      </Card>

      {/* Display Options */}
      <Card>
        <Card.Header>Опции отображения</Card.Header>

        <Card.Body className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
        </Card.Body>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={isSaving}
          loading={isSaving}
          icon={<Save className="h-4 w-4" />}
        >
          Сохранить настройки
        </Button>
      </div>
        </>
      )}

      {/* Channels Sub Tab */}
      {telegramSubTab === 'channels' && (
        <TelegramChannels />
      )}
    </div>
  )
}


// ============ DISCORD TAB ============

function DiscordTab() {
  const [settings, setSettings] = useState({
    enabled: false,
    webhook_url: '',
    username: 'KOMAS Trading Bot',
    avatar_url: '',
    notify_new_signal: true,
    notify_tp_hit: true,
    notify_sl_hit: true,
    notify_signal_closed: true,
    notify_errors: false,
    include_chart_link: false,
    include_entry_zone: true,
    include_leverage: true,
    show_all_targets: true,
    use_rich_embeds: true
  })

  const [showWebhook, setShowWebhook] = useState(false)
  const [isTesting, setIsTesting] = useState(false)
  const [isValidating, setIsValidating] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [webhookInfo, setWebhookInfo] = useState(null)

  // Load settings on mount
  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const response = await discordApi.getSettings()
      if (response.data?.settings) {
        setSettings(response.data.settings)
      }
    } catch (error) {
      console.error('Failed to load Discord settings:', error)
    }
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
  }

  const handleValidateWebhook = async () => {
    setIsValidating(true)
    try {
      const response = await discordApi.validateWebhook(settings.webhook_url)
      if (response.data?.valid) {
        setWebhookInfo(response.data.webhook_info)
        toast.success(`Webhook подключён! Канал: ${response.data.webhook_info?.name}`)
      } else {
        toast.error(response.data?.error || 'Ошибка валидации')
        setWebhookInfo(null)
      }
    } catch (error) {
      toast.error('Ошибка подключения к Discord API')
      setWebhookInfo(null)
    } finally {
      setIsValidating(false)
    }
  }

  const handleTestNotification = async () => {
    setIsTesting(true)
    try {
      const response = await discordApi.test()
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
      await discordApi.updateSettings(settings)
      toast.success('Настройки сохранены')
    } catch (error) {
      toast.error('Ошибка сохранения')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Discord Settings */}
      <Card>
        <Card.Header className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Bell className="h-5 w-5 text-indigo-400" />
            <span>Discord Webhook</span>
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
        </Card.Header>

        <Card.Body className="space-y-4">
          {/* Webhook URL */}
          <div>
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Input
                  label="Webhook URL"
                  type={showWebhook ? 'text' : 'password'}
                  name="webhook_url"
                  value={settings.webhook_url}
                  onChange={handleChange}
                  placeholder="https://discord.com/api/webhooks/..."
                  helper="Создайте Webhook в настройках канала Discord: Edit Channel → Integrations → Webhooks"
                />
                <button
                  type="button"
                  onClick={() => setShowWebhook(!showWebhook)}
                  className="absolute right-2 top-9 text-gray-500 hover:text-gray-300"
                >
                  {showWebhook ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
              <div className="pt-6">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleValidateWebhook}
                  disabled={!settings.webhook_url || isValidating}
                  loading={isValidating}
                >
                  Проверить
                </Button>
              </div>
            </div>
          </div>

          {/* Webhook Info */}
          {webhookInfo && (
            <Alert variant="success">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">Webhook подключён</span>
              </div>
              <div className="mt-2 text-sm">
                <p>Имя: {webhookInfo.name}</p>
                <p className="text-xs opacity-80">ID: {webhookInfo.id}</p>
                <p className="text-xs opacity-80">Channel ID: {webhookInfo.channel_id}</p>
              </div>
            </Alert>
          )}

          {/* Bot customization */}
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Имя бота"
              name="username"
              value={settings.username}
              onChange={handleChange}
              placeholder="KOMAS Trading Bot"
            />
            <Input
              label="Avatar URL (опционально)"
              name="avatar_url"
              value={settings.avatar_url}
              onChange={handleChange}
              placeholder="https://..."
            />
          </div>

          {/* Test Button */}
          <div className="flex gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={handleTestNotification}
              disabled={!settings.webhook_url || isTesting}
              loading={isTesting}
              icon={<Send className="h-4 w-4" />}
            >
              Тест
            </Button>
          </div>
        </Card.Body>
      </Card>

      {/* Rich Embeds */}
      <Card>
        <Card.Header className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-purple-400" />
          <span>Формат сообщений</span>
        </Card.Header>

        <Card.Body className="space-y-4">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              name="use_rich_embeds"
              checked={settings.use_rich_embeds}
              onChange={handleChange}
              className="rounded border-gray-700"
            />
            <span className="text-sm">Использовать Rich Embeds (цветные карточки)</span>
          </label>
          <p className="text-xs text-gray-500">
            Rich Embeds создают красивые цветные карточки с иконками. Отключите для простого текстового формата.
          </p>
        </Card.Body>
      </Card>

      {/* Trigger Settings */}
      <Card>
        <Card.Header className="flex items-center gap-2">
          <Target className="h-5 w-5 text-red-400" />
          <span>Триггеры уведомлений</span>
        </Card.Header>

        <Card.Body className="grid grid-cols-2 md:grid-cols-3 gap-4">
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
        </Card.Body>
      </Card>

      {/* Display Options */}
      <Card>
        <Card.Header>Опции отображения</Card.Header>

        <Card.Body className="grid grid-cols-2 md:grid-cols-4 gap-4">
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
        </Card.Body>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={isSaving}
          loading={isSaving}
          icon={<Save className="h-4 w-4" />}
        >
          Сохранить настройки
        </Button>
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
        <Card key={exchange.id}>
          <Card.Header className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full bg-${exchange.color}-400`} />
            <span>{exchange.name}</span>
          </Card.Header>

          <Card.Body className="space-y-4">
            <Input
              label="API Key"
              name={`${exchange.id}_key`}
              value={keys[`${exchange.id}_key`]}
              onChange={handleChange}
              placeholder="Enter API Key"
            />

            <div className="relative">
              <Input
                label="API Secret"
                type={showSecrets[`${exchange.id}_secret`] ? 'text' : 'password'}
                name={`${exchange.id}_secret`}
                value={keys[`${exchange.id}_secret`]}
                onChange={handleChange}
                placeholder="Enter API Secret"
              />
              <button
                type="button"
                onClick={() => toggleSecret(`${exchange.id}_secret`)}
                className="absolute right-2 top-9 text-gray-500 hover:text-gray-300"
              >
                {showSecrets[`${exchange.id}_secret`] ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            </div>

            {exchange.id === 'okx' && (
              <div className="relative">
                <Input
                  label="Passphrase"
                  type={showSecrets.okx_passphrase ? 'text' : 'password'}
                  name="okx_passphrase"
                  value={keys.okx_passphrase}
                  onChange={handleChange}
                  placeholder="Enter Passphrase"
                />
                <button
                  type="button"
                  onClick={() => toggleSecret('okx_passphrase')}
                  className="absolute right-2 top-9 text-gray-500 hover:text-gray-300"
                >
                  {showSecrets.okx_passphrase ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            )}
          </Card.Body>
        </Card>
      ))}

      <Alert variant="warning">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium">⚠️ ВАЖНО: Только бумажная торговля (Paper Trading)</p>
            <p className="text-sm mt-1 opacity-90">
              KOMAS v4.0 работает ТОЛЬКО в режиме бумажной торговли (симуляция).
              API ключи НЕ используются для реальной торговли.
              Все сделки выполняются только на исторических данных в режиме бэктестинга.
            </p>
            <p className="text-xs mt-2 opacity-75">
              🔒 Безопасность: API ключи хранятся локально и не передаются на сервер.
            </p>
          </div>
        </div>
      </Alert>

      <div className="flex justify-end">
        <Button variant="primary" icon={<Save className="h-4 w-4" />}>
          Сохранить ключи
        </Button>
      </div>
    </div>
  )
}
