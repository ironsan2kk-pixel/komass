import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Settings, Save, Plus, Trash2, Copy, Loader2, Key, Bell, 
  Server, Eye, EyeOff, Send, Check, AlertCircle, RefreshCw,
  MessageSquare, Shield, Database, Wifi
} from 'lucide-react'
import toast from 'react-hot-toast'
import { presetsApi, settingsApi, symbolsApi } from '../api'

// === Компонент для API ключей ===
function ApiKeysTab() {
  const queryClient = useQueryClient()
  const [showKeys, setShowKeys] = useState({})
  
  const [apiKeys, setApiKeys] = useState({
    binance: { api_key: '', api_secret: '', testnet: false },
    bybit: { api_key: '', api_secret: '', testnet: false },
    okx: { api_key: '', api_secret: '', passphrase: '', testnet: false },
  })

  // Загрузка сохранённых ключей
  const { data: savedKeys, isLoading } = useQuery({
    queryKey: ['api-keys'],
    queryFn: () => settingsApi.getApiKeys().then(r => r.data),
  })

  useEffect(() => {
    if (savedKeys) {
      setApiKeys(prev => ({
        ...prev,
        ...savedKeys
      }))
    }
  }, [savedKeys])

  // Сохранение ключей
  const saveMutation = useMutation({
    mutationFn: (exchange) => settingsApi.saveApiKey(exchange, apiKeys[exchange]),
    onSuccess: (_, exchange) => {
      toast.success(`Ключи ${exchange.toUpperCase()} сохранены`)
      queryClient.invalidateQueries(['api-keys'])
    },
    onError: (err) => {
      toast.error(`Ошибка: ${err.response?.data?.detail || err.message}`)
    }
  })

  // Тест подключения
  const testMutation = useMutation({
    mutationFn: (exchange) => settingsApi.testConnection(exchange),
    onSuccess: (data, exchange) => {
      if (data.data.success) {
        toast.success(`${exchange.toUpperCase()}: Подключение успешно!`)
      } else {
        toast.error(`${exchange.toUpperCase()}: ${data.data.error}`)
      }
    },
    onError: (err) => {
      toast.error(`Ошибка теста: ${err.message}`)
    }
  })

  const toggleShowKey = (exchange, field) => {
    setShowKeys(prev => ({
      ...prev,
      [`${exchange}_${field}`]: !prev[`${exchange}_${field}`]
    }))
  }

  const handleChange = (exchange, field, value) => {
    setApiKeys(prev => ({
      ...prev,
      [exchange]: {
        ...prev[exchange],
        [field]: value
      }
    }))
  }

  const maskKey = (key) => {
    if (!key) return ''
    if (key.length <= 8) return '****'
    return key.slice(0, 4) + '****' + key.slice(-4)
  }

  const exchanges = [
    { id: 'binance', name: 'Binance', color: 'yellow' },
    { id: 'bybit', name: 'Bybit', color: 'orange' },
    { id: 'okx', name: 'OKX', color: 'blue', hasPassphrase: true },
  ]

  if (isLoading) {
    return (
      <div className="py-12 text-center">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500 mx-auto" />
        <p className="text-gray-500 mt-2">Загрузка...</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start gap-3 p-4 bg-yellow-500/10 border border-yellow-500/30 rounded-lg">
        <Shield className="h-5 w-5 text-yellow-400 mt-0.5" />
        <div>
          <h4 className="font-medium text-yellow-400">Безопасность</h4>
          <p className="text-sm text-gray-400 mt-1">
            API ключи хранятся в зашифрованном виде. Используйте ключи только с разрешениями на чтение и торговлю.
            Никогда не давайте разрешение на вывод средств.
          </p>
        </div>
      </div>

      {exchanges.map((exchange) => (
        <div key={exchange.id} className="card">
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Key className={`h-5 w-5 text-${exchange.color}-400`} />
              <span className="font-medium">{exchange.name}</span>
              {savedKeys?.[exchange.id]?.connected && (
                <span className="badge bg-green-500/20 text-green-400">Подключено</span>
              )}
            </div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={apiKeys[exchange.id]?.testnet || false}
                onChange={(e) => handleChange(exchange.id, 'testnet', e.target.checked)}
                className="rounded border-gray-700"
              />
              <span className="text-gray-400">Testnet</span>
            </label>
          </div>

          <div className="space-y-4">
            {/* API Key */}
            <div>
              <label className="label">API Key</label>
              <div className="relative">
                <input
                  type={showKeys[`${exchange.id}_api_key`] ? 'text' : 'password'}
                  value={apiKeys[exchange.id]?.api_key || ''}
                  onChange={(e) => handleChange(exchange.id, 'api_key', e.target.value)}
                  placeholder="Введите API Key"
                  className="input pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleShowKey(exchange.id, 'api_key')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showKeys[`${exchange.id}_api_key`] ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {/* API Secret */}
            <div>
              <label className="label">API Secret</label>
              <div className="relative">
                <input
                  type={showKeys[`${exchange.id}_api_secret`] ? 'text' : 'password'}
                  value={apiKeys[exchange.id]?.api_secret || ''}
                  onChange={(e) => handleChange(exchange.id, 'api_secret', e.target.value)}
                  placeholder="Введите API Secret"
                  className="input pr-10"
                />
                <button
                  type="button"
                  onClick={() => toggleShowKey(exchange.id, 'api_secret')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                >
                  {showKeys[`${exchange.id}_api_secret`] ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Passphrase для OKX */}
            {exchange.hasPassphrase && (
              <div>
                <label className="label">Passphrase</label>
                <div className="relative">
                  <input
                    type={showKeys[`${exchange.id}_passphrase`] ? 'text' : 'password'}
                    value={apiKeys[exchange.id]?.passphrase || ''}
                    onChange={(e) => handleChange(exchange.id, 'passphrase', e.target.value)}
                    placeholder="Введите Passphrase"
                    className="input pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => toggleShowKey(exchange.id, 'passphrase')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300"
                  >
                    {showKeys[`${exchange.id}_passphrase`] ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* Кнопки */}
            <div className="flex gap-2 pt-2">
              <button
                onClick={() => saveMutation.mutate(exchange.id)}
                disabled={saveMutation.isPending}
                className="btn-primary"
              >
                {saveMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Сохранить
              </button>
              <button
                onClick={() => testMutation.mutate(exchange.id)}
                disabled={testMutation.isPending}
                className="btn-secondary"
              >
                {testMutation.isPending ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Wifi className="h-4 w-4" />
                )}
                Тест
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

// === Компонент для уведомлений ===
function NotificationsTab() {
  const queryClient = useQueryClient()
  
  const [settings, setSettings] = useState({
    telegram: {
      enabled: false,
      bot_token: '',
      chat_id: '',
      notify_signals: true,
      notify_trades: true,
      notify_errors: true,
    },
    discord: {
      enabled: false,
      webhook_url: '',
      notify_signals: true,
      notify_trades: true,
      notify_errors: true,
    },
  })

  const { data: savedSettings, isLoading } = useQuery({
    queryKey: ['notification-settings'],
    queryFn: () => settingsApi.getNotifications().then(r => r.data),
  })

  useEffect(() => {
    if (savedSettings) {
      setSettings(prev => ({
        ...prev,
        ...savedSettings
      }))
    }
  }, [savedSettings])

  const saveMutation = useMutation({
    mutationFn: () => settingsApi.saveNotifications(settings),
    onSuccess: () => {
      toast.success('Настройки уведомлений сохранены')
      queryClient.invalidateQueries(['notification-settings'])
    },
    onError: (err) => {
      toast.error(`Ошибка: ${err.response?.data?.detail || err.message}`)
    }
  })

  const testMutation = useMutation({
    mutationFn: (type) => settingsApi.testNotification(type),
    onSuccess: (_, type) => {
      toast.success(`Тестовое уведомление отправлено в ${type}`)
    },
    onError: (err) => {
      toast.error(`Ошибка: ${err.message}`)
    }
  })

  const handleChange = (service, field, value) => {
    setSettings(prev => ({
      ...prev,
      [service]: {
        ...prev[service],
        [field]: value
      }
    }))
  }

  if (isLoading) {
    return (
      <div className="py-12 text-center">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500 mx-auto" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Telegram */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Send className="h-5 w-5 text-blue-400" />
            <span className="font-medium">Telegram</span>
          </div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.telegram.enabled}
              onChange={(e) => handleChange('telegram', 'enabled', e.target.checked)}
              className="rounded border-gray-700"
            />
            <span className="text-sm text-gray-400">Включено</span>
          </label>
        </div>

        <div className="space-y-4">
          <div>
            <label className="label">Bot Token</label>
            <input
              type="password"
              value={settings.telegram.bot_token}
              onChange={(e) => handleChange('telegram', 'bot_token', e.target.value)}
              placeholder="123456:ABC-DEF..."
              className="input"
              disabled={!settings.telegram.enabled}
            />
            <p className="text-xs text-gray-500 mt-1">
              Получите от @BotFather в Telegram
            </p>
          </div>

          <div>
            <label className="label">Chat ID</label>
            <input
              type="text"
              value={settings.telegram.chat_id}
              onChange={(e) => handleChange('telegram', 'chat_id', e.target.value)}
              placeholder="-1001234567890"
              className="input"
              disabled={!settings.telegram.enabled}
            />
            <p className="text-xs text-gray-500 mt-1">
              ID чата или канала для уведомлений
            </p>
          </div>

          <div className="grid grid-cols-3 gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.telegram.notify_signals}
                onChange={(e) => handleChange('telegram', 'notify_signals', e.target.checked)}
                disabled={!settings.telegram.enabled}
                className="rounded border-gray-700"
              />
              <span className="text-sm text-gray-400">Сигналы</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.telegram.notify_trades}
                onChange={(e) => handleChange('telegram', 'notify_trades', e.target.checked)}
                disabled={!settings.telegram.enabled}
                className="rounded border-gray-700"
              />
              <span className="text-sm text-gray-400">Сделки</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.telegram.notify_errors}
                onChange={(e) => handleChange('telegram', 'notify_errors', e.target.checked)}
                disabled={!settings.telegram.enabled}
                className="rounded border-gray-700"
              />
              <span className="text-sm text-gray-400">Ошибки</span>
            </label>
          </div>

          <button
            onClick={() => testMutation.mutate('telegram')}
            disabled={!settings.telegram.enabled || testMutation.isPending}
            className="btn-secondary"
          >
            <Send className="h-4 w-4" />
            Тест уведомления
          </button>
        </div>
      </div>

      {/* Discord */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-purple-400" />
            <span className="font-medium">Discord</span>
          </div>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.discord.enabled}
              onChange={(e) => handleChange('discord', 'enabled', e.target.checked)}
              className="rounded border-gray-700"
            />
            <span className="text-sm text-gray-400">Включено</span>
          </label>
        </div>

        <div className="space-y-4">
          <div>
            <label className="label">Webhook URL</label>
            <input
              type="password"
              value={settings.discord.webhook_url}
              onChange={(e) => handleChange('discord', 'webhook_url', e.target.value)}
              placeholder="https://discord.com/api/webhooks/..."
              className="input"
              disabled={!settings.discord.enabled}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.discord.notify_signals}
                onChange={(e) => handleChange('discord', 'notify_signals', e.target.checked)}
                disabled={!settings.discord.enabled}
                className="rounded border-gray-700"
              />
              <span className="text-sm text-gray-400">Сигналы</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.discord.notify_trades}
                onChange={(e) => handleChange('discord', 'notify_trades', e.target.checked)}
                disabled={!settings.discord.enabled}
                className="rounded border-gray-700"
              />
              <span className="text-sm text-gray-400">Сделки</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={settings.discord.notify_errors}
                onChange={(e) => handleChange('discord', 'notify_errors', e.target.checked)}
                disabled={!settings.discord.enabled}
                className="rounded border-gray-700"
              />
              <span className="text-sm text-gray-400">Ошибки</span>
            </label>
          </div>

          <button
            onClick={() => testMutation.mutate('discord')}
            disabled={!settings.discord.enabled || testMutation.isPending}
            className="btn-secondary"
          >
            <Send className="h-4 w-4" />
            Тест уведомления
          </button>
        </div>
      </div>

      {/* Сохранить всё */}
      <button
        onClick={() => saveMutation.mutate()}
        disabled={saveMutation.isPending}
        className="btn-primary w-full"
      >
        {saveMutation.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <Save className="h-4 w-4" />
        )}
        Сохранить настройки уведомлений
      </button>
    </div>
  )
}

// === Компонент для системных настроек ===
function SystemTab() {
  const queryClient = useQueryClient()
  
  const [settings, setSettings] = useState({
    auto_start: false,
    log_level: 'INFO',
    max_log_size_mb: 100,
    data_retention_days: 90,
    backup_enabled: false,
    backup_interval_hours: 24,
  })

  const { data: systemInfo } = useQuery({
    queryKey: ['system-info'],
    queryFn: () => settingsApi.getSystemInfo().then(r => r.data),
  })

  const { data: savedSettings, isLoading } = useQuery({
    queryKey: ['system-settings'],
    queryFn: () => settingsApi.getSystem().then(r => r.data),
  })

  useEffect(() => {
    if (savedSettings) {
      setSettings(prev => ({ ...prev, ...savedSettings }))
    }
  }, [savedSettings])

  const saveMutation = useMutation({
    mutationFn: () => settingsApi.saveSystem(settings),
    onSuccess: () => {
      toast.success('Системные настройки сохранены')
      queryClient.invalidateQueries(['system-settings'])
    }
  })

  const clearCacheMutation = useMutation({
    mutationFn: () => settingsApi.clearCache(),
    onSuccess: () => {
      toast.success('Кэш очищен')
    }
  })

  if (isLoading) {
    return (
      <div className="py-12 text-center">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500 mx-auto" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Информация о системе */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Server className="h-5 w-5 text-blue-400" />
          <span>Информация о системе</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-gray-500">Версия</p>
            <p className="font-mono">{systemInfo?.version || '3.0.0'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Python</p>
            <p className="font-mono">{systemInfo?.python_version || '3.11'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Uptime</p>
            <p className="font-mono">{systemInfo?.uptime || '-'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">База данных</p>
            <p className="font-mono">{systemInfo?.db_size || '-'}</p>
          </div>
        </div>
      </div>

      {/* Настройки логирования */}
      <div className="card">
        <div className="card-header">Логирование</div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Уровень логирования</label>
            <select
              value={settings.log_level}
              onChange={(e) => setSettings({ ...settings, log_level: e.target.value })}
              className="select"
            >
              <option value="DEBUG">DEBUG</option>
              <option value="INFO">INFO</option>
              <option value="WARNING">WARNING</option>
              <option value="ERROR">ERROR</option>
            </select>
          </div>
          <div>
            <label className="label">Макс. размер логов (MB)</label>
            <input
              type="number"
              value={settings.max_log_size_mb}
              onChange={(e) => setSettings({ ...settings, max_log_size_mb: parseInt(e.target.value) })}
              className="input"
            />
          </div>
        </div>
      </div>

      {/* Хранение данных */}
      <div className="card">
        <div className="card-header">Хранение данных</div>
        <div className="space-y-4">
          <div>
            <label className="label">Хранить данные (дней)</label>
            <input
              type="number"
              value={settings.data_retention_days}
              onChange={(e) => setSettings({ ...settings, data_retention_days: parseInt(e.target.value) })}
              className="input w-32"
            />
          </div>
          
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={settings.backup_enabled}
              onChange={(e) => setSettings({ ...settings, backup_enabled: e.target.checked })}
              className="rounded border-gray-700"
            />
            <span className="text-gray-300">Автоматическое резервное копирование</span>
          </label>

          {settings.backup_enabled && (
            <div>
              <label className="label">Интервал бэкапа (часов)</label>
              <input
                type="number"
                value={settings.backup_interval_hours}
                onChange={(e) => setSettings({ ...settings, backup_interval_hours: parseInt(e.target.value) })}
                className="input w-32"
              />
            </div>
          )}
        </div>
      </div>

      {/* Действия */}
      <div className="flex gap-4">
        <button
          onClick={() => saveMutation.mutate()}
          disabled={saveMutation.isPending}
          className="btn-primary"
        >
          {saveMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
          Сохранить
        </button>
        <button
          onClick={() => clearCacheMutation.mutate()}
          disabled={clearCacheMutation.isPending}
          className="btn-secondary"
        >
          <Database className="h-4 w-4" />
          Очистить кэш
        </button>
      </div>
    </div>
  )
}

// === Компонент для пресетов (оставляем существующий функционал) ===
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
    trg_atr_length: 45,
    trg_multiplier: 4.0,
    tp_count: 4,
    sl_percent: 2.0,
    sl_mode: 'fixed',
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
    setForm({
      name: preset.name,
      symbol: preset.symbol,
      exchange: preset.exchange || 'binance',
      timeframe: preset.timeframe,
      trg_atr_length: preset.trg_atr_length || 45,
      trg_multiplier: preset.trg_multiplier || 4.0,
      tp_count: preset.tp_count || 4,
      sl_percent: preset.sl_percent || 2.0,
      sl_mode: preset.sl_mode || 'fixed',
    })
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
      {/* Список пресетов */}
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
                  ? 'bg-blue-600/20 border border-blue-500/50'
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
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      if (confirm('Удалить пресет?')) {
                        deleteMutation.mutate(preset.id)
                      }
                    }}
                    className="p-1 hover:bg-gray-700 rounded"
                  >
                    <Trash2 className="h-3 w-3 text-red-500" />
                  </button>
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                {preset.symbol} • {preset.timeframe}
              </p>
            </div>
          ))}
          {(!presets?.items || presets.items.length === 0) && (
            <p className="text-center text-gray-500 py-4">Нет пресетов</p>
          )}
        </div>
      </div>

      {/* Форма редактирования */}
      <div className="lg:col-span-3 card">
        {selectedPreset || isCreating ? (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium">
                {isCreating ? 'Новый пресет' : 'Редактирование'}
              </h3>
              <button
                onClick={handleSave}
                disabled={createMutation.isPending || updateMutation.isPending}
                className="btn-primary"
              >
                {(createMutation.isPending || updateMutation.isPending) ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Save className="h-4 w-4" />
                )}
                Сохранить
              </button>
            </div>

            {/* Основные поля */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <label className="label">Название</label>
                <input
                  type="text"
                  name="name"
                  value={form.name}
                  onChange={handleChange}
                  className="input"
                />
              </div>
              <div>
                <label className="label">Символ</label>
                <select name="symbol" value={form.symbol} onChange={handleChange} className="select">
                  {symbols?.items?.map(s => (
                    <option key={s.symbol || s} value={s.symbol || s}>{s.symbol || s}</option>
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

            {/* TRG настройки */}
            <div className="border-t border-gray-800 pt-4">
              <h4 className="text-sm font-medium text-gray-400 mb-3">TRG Индикатор</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <label className="label">ATR Length (i1)</label>
                  <input 
                    type="number" 
                    name="trg_atr_length" 
                    value={form.trg_atr_length} 
                    onChange={handleChange} 
                    className="input" 
                  />
                </div>
                <div>
                  <label className="label">Multiplier (i2)</label>
                  <input 
                    type="number" 
                    step="0.1" 
                    name="trg_multiplier" 
                    value={form.trg_multiplier} 
                    onChange={handleChange} 
                    className="input" 
                  />
                </div>
                <div>
                  <label className="label">TP Count</label>
                  <input 
                    type="number" 
                    name="tp_count" 
                    value={form.tp_count} 
                    onChange={handleChange} 
                    min="1"
                    max="10"
                    className="input" 
                  />
                </div>
                <div>
                  <label className="label">SL %</label>
                  <input 
                    type="number" 
                    step="0.1" 
                    name="sl_percent" 
                    value={form.sl_percent} 
                    onChange={handleChange} 
                    className="input" 
                  />
                </div>
              </div>
            </div>

            {/* SL Mode */}
            <div className="border-t border-gray-800 pt-4">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Stop Loss Mode</h4>
              <select name="sl_mode" value={form.sl_mode} onChange={handleChange} className="select w-48">
                <option value="fixed">Fixed</option>
                <option value="breakeven">Breakeven</option>
                <option value="cascade">Cascade Trailing</option>
              </select>
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

// === Главный компонент ===
export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('presets')

  const tabs = [
    { id: 'presets', label: 'Пресеты', icon: Settings },
    { id: 'api-keys', label: 'API Ключи', icon: Key },
    { id: 'notifications', label: 'Уведомления', icon: Bell },
    { id: 'system', label: 'Система', icon: Server },
  ]

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Настройки</h1>
        <p className="text-gray-500">Управление пресетами и конфигурацией системы</p>
      </div>

      {/* Вкладки */}
      <div className="flex gap-2 border-b border-gray-800 pb-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-600/20 text-blue-400'
                : 'text-gray-400 hover:text-gray-100 hover:bg-gray-800'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Контент вкладок */}
      {activeTab === 'presets' && <PresetsTab />}
      {activeTab === 'api-keys' && <ApiKeysTab />}
      {activeTab === 'notifications' && <NotificationsTab />}
      {activeTab === 'system' && <SystemTab />}
    </div>
  )
}
