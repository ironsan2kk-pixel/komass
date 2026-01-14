import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Plus, Trash2, Edit2, Power, PowerOff, Send, Loader2,
  CheckCircle, XCircle, AlertTriangle, Filter, TrendingUp
} from 'lucide-react'
import toast from 'react-hot-toast'
import { notificationsApi } from '../services/api'

export default function TelegramChannels() {
  const queryClient = useQueryClient()
  const [selectedChannel, setSelectedChannel] = useState(null)
  const [showForm, setShowForm] = useState(false)
  const [showFilters, setShowFilters] = useState(false)

  // Fetch channels
  const { data: channelsData, isLoading } = useQuery({
    queryKey: ['telegram-channels'],
    queryFn: () => notificationsApi.channels.getAll(),
  })

  // Fetch stats
  const { data: statsData } = useQuery({
    queryKey: ['telegram-channels-stats'],
    queryFn: () => notificationsApi.channels.getStats(),
  })

  const channels = channelsData?.channels || []
  const stats = statsData?.stats || {}

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: notificationsApi.channels.delete,
    onSuccess: () => {
      toast.success('Канал удалён')
      queryClient.invalidateQueries(['telegram-channels'])
      queryClient.invalidateQueries(['telegram-channels-stats'])
      setSelectedChannel(null)
    },
    onError: () => toast.error('Ошибка удаления канала'),
  })

  // Enable mutation
  const enableMutation = useMutation({
    mutationFn: notificationsApi.channels.enable,
    onSuccess: () => {
      toast.success('Канал включён')
      queryClient.invalidateQueries(['telegram-channels'])
    },
    onError: () => toast.error('Ошибка включения канала'),
  })

  // Disable mutation
  const disableMutation = useMutation({
    mutationFn: notificationsApi.channels.disable,
    onSuccess: () => {
      toast.success('Канал выключен')
      queryClient.invalidateQueries(['telegram-channels'])
    },
    onError: () => toast.error('Ошибка выключения канала'),
  })

  // Test mutation
  const testMutation = useMutation({
    mutationFn: notificationsApi.channels.test,
    onSuccess: () => toast.success('Тестовое сообщение отправлено!'),
    onError: (error) => toast.error(error.message || 'Ошибка отправки'),
  })

  const handleDelete = (channel) => {
    if (confirm(`Удалить канал "${channel.name}"?`)) {
      deleteMutation.mutate(channel.id)
    }
  }

  const handleToggle = (channel) => {
    if (channel.enabled) {
      disableMutation.mutate(channel.id)
    } else {
      enableMutation.mutate(channel.id)
    }
  }

  const handleTest = (channel) => {
    testMutation.mutate(channel.id)
  }

  const handleEdit = (channel) => {
    setSelectedChannel(channel)
    setShowForm(true)
  }

  const handleCreate = () => {
    setSelectedChannel(null)
    setShowForm(true)
  }

  if (showForm) {
    return (
      <ChannelForm
        channel={selectedChannel}
        onClose={() => {
          setShowForm(false)
          setSelectedChannel(null)
        }}
        onSuccess={() => {
          setShowForm(false)
          setSelectedChannel(null)
          queryClient.invalidateQueries(['telegram-channels'])
          queryClient.invalidateQueries(['telegram-channels-stats'])
        }}
      />
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-100">Telegram Каналы</h2>
          <p className="text-sm text-gray-500">Управление multi-channel уведомлениями</p>
        </div>
        <button
          onClick={handleCreate}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="h-4 w-4" />
          Создать канал
        </button>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <div className="text-sm text-gray-500">Всего каналов</div>
            <div className="text-2xl font-bold text-gray-100">{stats.total_channels || 0}</div>
          </div>
          <div className="card">
            <div className="text-sm text-gray-500">Активных</div>
            <div className="text-2xl font-bold text-green-400">{stats.enabled_channels || 0}</div>
          </div>
          <div className="card">
            <div className="text-sm text-gray-500">Выключено</div>
            <div className="text-2xl font-bold text-gray-400">{stats.disabled_channels || 0}</div>
          </div>
          <div className="card">
            <div className="text-sm text-gray-500">Сообщений отправлено</div>
            <div className="text-2xl font-bold text-blue-400">{stats.total_messages_sent || 0}</div>
          </div>
        </div>
      )}

      {/* Channels List */}
      <div className="card">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary-500" />
          </div>
        ) : channels.length === 0 ? (
          <div className="text-center py-12">
            <AlertTriangle className="h-12 w-12 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-500">Нет каналов</p>
            <button
              onClick={handleCreate}
              className="btn-secondary mt-4"
            >
              Создать первый канал
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Статус</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Название</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Chat ID</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Формат</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Фильтры</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">Отправлено</th>
                  <th className="text-right py-3 px-4 text-sm font-medium text-gray-400">Действия</th>
                </tr>
              </thead>
              <tbody>
                {channels.map((channel) => (
                  <tr key={channel.id} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                    <td className="py-3 px-4">
                      {channel.enabled ? (
                        <CheckCircle className="h-5 w-5 text-green-400" />
                      ) : (
                        <XCircle className="h-5 w-5 text-gray-600" />
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-medium text-gray-100">{channel.name}</div>
                    </td>
                    <td className="py-3 px-4">
                      <code className="text-sm text-gray-400">{channel.chat_id}</code>
                    </td>
                    <td className="py-3 px-4">
                      <span className="px-2 py-1 text-xs rounded bg-gray-800 text-gray-300">
                        {channel.message_format}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex flex-wrap gap-1">
                        {channel.routing_rules?.indicators?.length > 0 && (
                          <span className="px-2 py-0.5 text-xs rounded bg-blue-900/30 text-blue-300">
                            {channel.routing_rules.indicators.join(', ')}
                          </span>
                        )}
                        {channel.routing_rules?.symbols?.length > 0 && (
                          <span className="px-2 py-0.5 text-xs rounded bg-purple-900/30 text-purple-300">
                            {channel.routing_rules.symbols.length} символов
                          </span>
                        )}
                        {channel.routing_rules?.score_grades?.length > 0 && (
                          <span className="px-2 py-0.5 text-xs rounded bg-yellow-900/30 text-yellow-300">
                            Grade: {channel.routing_rules.score_grades.join(', ')}
                          </span>
                        )}
                        {channel.routing_rules?.min_score && (
                          <span className="px-2 py-0.5 text-xs rounded bg-green-900/30 text-green-300">
                            Score ≥{channel.routing_rules.min_score}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="text-sm text-gray-400">{channel.messages_sent || 0}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleTest(channel)}
                          disabled={!channel.enabled || testMutation.isPending}
                          className="p-1.5 hover:bg-gray-700 rounded transition-colors disabled:opacity-50"
                          title="Тест отправки"
                        >
                          <Send className="h-4 w-4 text-gray-400" />
                        </button>
                        <button
                          onClick={() => handleEdit(channel)}
                          className="p-1.5 hover:bg-gray-700 rounded transition-colors"
                          title="Редактировать"
                        >
                          <Edit2 className="h-4 w-4 text-gray-400" />
                        </button>
                        <button
                          onClick={() => handleToggle(channel)}
                          disabled={enableMutation.isPending || disableMutation.isPending}
                          className="p-1.5 hover:bg-gray-700 rounded transition-colors"
                          title={channel.enabled ? 'Выключить' : 'Включить'}
                        >
                          {channel.enabled ? (
                            <PowerOff className="h-4 w-4 text-orange-400" />
                          ) : (
                            <Power className="h-4 w-4 text-green-400" />
                          )}
                        </button>
                        <button
                          onClick={() => handleDelete(channel)}
                          disabled={deleteMutation.isPending}
                          className="p-1.5 hover:bg-gray-700 rounded transition-colors"
                          title="Удалить"
                        >
                          <Trash2 className="h-4 w-4 text-red-400" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

// ============ CHANNEL FORM ============

function ChannelForm({ channel, onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    name: channel?.name || '',
    chat_id: channel?.chat_id || '',
    enabled: channel?.enabled ?? true,
    message_format: channel?.message_format || 'simple',
    routing_rules: {
      indicators: channel?.routing_rules?.indicators || [],
      symbols: channel?.routing_rules?.symbols || [],
      directions: channel?.routing_rules?.directions || [],
      min_score: channel?.routing_rules?.min_score || null,
      score_grades: channel?.routing_rules?.score_grades || [],
      notify_new_signal: channel?.routing_rules?.notify_new_signal ?? true,
      notify_tp_hit: channel?.routing_rules?.notify_tp_hit ?? true,
      notify_sl_hit: channel?.routing_rules?.notify_sl_hit ?? true,
      notify_signal_closed: channel?.routing_rules?.notify_signal_closed ?? true,
      notify_errors: channel?.routing_rules?.notify_errors ?? false,
    },
  })

  const [indicatorInput, setIndicatorInput] = useState('')
  const [symbolInput, setSymbolInput] = useState('')

  // Create/Update mutation
  const saveMutation = useMutation({
    mutationFn: (data) => {
      if (channel) {
        return notificationsApi.channels.update(channel.id, data)
      } else {
        return notificationsApi.channels.create(data)
      }
    },
    onSuccess: () => {
      toast.success(channel ? 'Канал обновлён' : 'Канал создан')
      onSuccess()
    },
    onError: (error) => {
      toast.error(error.message || 'Ошибка сохранения')
    },
  })

  const handleSubmit = (e) => {
    e.preventDefault()

    // Validation
    if (!formData.name.trim()) {
      toast.error('Введите название канала')
      return
    }
    if (!formData.chat_id.trim()) {
      toast.error('Введите Chat ID')
      return
    }

    saveMutation.mutate(formData)
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleRulesChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      routing_rules: {
        ...prev.routing_rules,
        [name]: type === 'checkbox' ? checked : (type === 'number' ? (value ? parseInt(value) : null) : value),
      },
    }))
  }

  const addIndicator = () => {
    if (indicatorInput && !formData.routing_rules.indicators.includes(indicatorInput)) {
      setFormData(prev => ({
        ...prev,
        routing_rules: {
          ...prev.routing_rules,
          indicators: [...prev.routing_rules.indicators, indicatorInput],
        },
      }))
      setIndicatorInput('')
    }
  }

  const removeIndicator = (indicator) => {
    setFormData(prev => ({
      ...prev,
      routing_rules: {
        ...prev.routing_rules,
        indicators: prev.routing_rules.indicators.filter(i => i !== indicator),
      },
    }))
  }

  const addSymbol = () => {
    const symbol = symbolInput.toUpperCase()
    if (symbol && !formData.routing_rules.symbols.includes(symbol)) {
      setFormData(prev => ({
        ...prev,
        routing_rules: {
          ...prev.routing_rules,
          symbols: [...prev.routing_rules.symbols, symbol],
        },
      }))
      setSymbolInput('')
    }
  }

  const removeSymbol = (symbol) => {
    setFormData(prev => ({
      ...prev,
      routing_rules: {
        ...prev.routing_rules,
        symbols: prev.routing_rules.symbols.filter(s => s !== symbol),
      },
    }))
  }

  const toggleDirection = (direction) => {
    setFormData(prev => {
      const current = prev.routing_rules.directions
      const updated = current.includes(direction)
        ? current.filter(d => d !== direction)
        : [...current, direction]
      return {
        ...prev,
        routing_rules: {
          ...prev.routing_rules,
          directions: updated,
        },
      }
    })
  }

  const toggleGrade = (grade) => {
    setFormData(prev => {
      const current = prev.routing_rules.score_grades
      const updated = current.includes(grade)
        ? current.filter(g => g !== grade)
        : [...current, grade]
      return {
        ...prev,
        routing_rules: {
          ...prev.routing_rules,
          score_grades: updated,
        },
      }
    })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-100">
            {channel ? 'Редактировать канал' : 'Создать канал'}
          </h2>
          <p className="text-sm text-gray-500">Настройка Telegram канала и routing правил</p>
        </div>
        <button onClick={onClose} className="btn-secondary">
          Отмена
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Settings */}
        <div className="card">
          <div className="card-header">Основные настройки</div>
          <div className="space-y-4">
            <div>
              <label className="label">Название канала</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="Premium Signals"
                className="input"
                required
              />
            </div>

            <div>
              <label className="label">Chat ID</label>
              <input
                type="text"
                name="chat_id"
                value={formData.chat_id}
                onChange={handleChange}
                placeholder="@channel_name или -1001234567890"
                className="input"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                ID чата или @username канала
              </p>
            </div>

            <div>
              <label className="label">Формат сообщений</label>
              <select
                name="message_format"
                value={formData.message_format}
                onChange={handleChange}
                className="input"
              >
                <option value="simple">Simple</option>
                <option value="cornix">Cornix</option>
                <option value="custom">Custom</option>
              </select>
            </div>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="enabled"
                checked={formData.enabled}
                onChange={handleChange}
                className="rounded border-gray-700"
              />
              <span className="text-sm text-gray-300">Канал включён</span>
            </label>
          </div>
        </div>

        {/* Routing Rules */}
        <div className="card">
          <div className="card-header flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Routing Rules (фильтры сигналов)
          </div>

          <div className="space-y-6">
            {/* Indicators */}
            <div>
              <label className="label">Индикаторы</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={indicatorInput}
                  onChange={(e) => setIndicatorInput(e.target.value)}
                  placeholder="TRG, Dominant..."
                  className="input flex-1"
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addIndicator())}
                />
                <button
                  type="button"
                  onClick={addIndicator}
                  className="btn-secondary"
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>
              {formData.routing_rules.indicators.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {formData.routing_rules.indicators.map(ind => (
                    <span
                      key={ind}
                      className="px-3 py-1 rounded bg-blue-900/30 text-blue-300 text-sm flex items-center gap-2"
                    >
                      {ind}
                      <button
                        type="button"
                        onClick={() => removeIndicator(ind)}
                        className="hover:text-red-400"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
              <p className="text-xs text-gray-500 mt-1">
                Пусто = все индикаторы
              </p>
            </div>

            {/* Symbols */}
            <div>
              <label className="label">Символы</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={symbolInput}
                  onChange={(e) => setSymbolInput(e.target.value)}
                  placeholder="BTCUSDT, ETHUSDT..."
                  className="input flex-1"
                  onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addSymbol())}
                />
                <button
                  type="button"
                  onClick={addSymbol}
                  className="btn-secondary"
                >
                  <Plus className="h-4 w-4" />
                </button>
              </div>
              {formData.routing_rules.symbols.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {formData.routing_rules.symbols.map(sym => (
                    <span
                      key={sym}
                      className="px-3 py-1 rounded bg-purple-900/30 text-purple-300 text-sm flex items-center gap-2"
                    >
                      {sym}
                      <button
                        type="button"
                        onClick={() => removeSymbol(sym)}
                        className="hover:text-red-400"
                      >
                        ×
                      </button>
                    </span>
                  ))}
                </div>
              )}
              <p className="text-xs text-gray-500 mt-1">
                Пусто = все символы
              </p>
            </div>

            {/* Directions */}
            <div>
              <label className="label">Направление</label>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => toggleDirection('LONG')}
                  className={`px-4 py-2 rounded transition-colors ${
                    formData.routing_rules.directions.includes('LONG')
                      ? 'bg-green-900/30 text-green-300 border border-green-700'
                      : 'bg-gray-800 text-gray-400 border border-gray-700'
                  }`}
                >
                  LONG
                </button>
                <button
                  type="button"
                  onClick={() => toggleDirection('SHORT')}
                  className={`px-4 py-2 rounded transition-colors ${
                    formData.routing_rules.directions.includes('SHORT')
                      ? 'bg-red-900/30 text-red-300 border border-red-700'
                      : 'bg-gray-800 text-gray-400 border border-gray-700'
                  }`}
                >
                  SHORT
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Пусто = оба направления
              </p>
            </div>

            {/* Score */}
            <div>
              <label className="label">Минимальный Score</label>
              <input
                type="number"
                name="min_score"
                min="0"
                max="100"
                value={formData.routing_rules.min_score || ''}
                onChange={handleRulesChange}
                placeholder="0-100"
                className="input"
              />
              <p className="text-xs text-gray-500 mt-1">
                Пусто = любой score
              </p>
            </div>

            {/* Grades */}
            <div>
              <label className="label">Grade (оценка)</label>
              <div className="flex gap-2">
                {['A', 'B', 'C', 'D', 'F'].map(grade => (
                  <button
                    key={grade}
                    type="button"
                    onClick={() => toggleGrade(grade)}
                    className={`px-4 py-2 rounded font-bold transition-colors ${
                      formData.routing_rules.score_grades.includes(grade)
                        ? 'bg-yellow-900/30 text-yellow-300 border border-yellow-700'
                        : 'bg-gray-800 text-gray-400 border border-gray-700'
                    }`}
                  >
                    {grade}
                  </button>
                ))}
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Пусто = любой grade
              </p>
            </div>
          </div>
        </div>

        {/* Notification Types */}
        <div className="card">
          <div className="card-header">Типы уведомлений</div>
          <div className="space-y-3">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="notify_new_signal"
                checked={formData.routing_rules.notify_new_signal}
                onChange={handleRulesChange}
                className="rounded border-gray-700"
              />
              <span className="text-sm text-gray-300">Новые сигналы</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="notify_tp_hit"
                checked={formData.routing_rules.notify_tp_hit}
                onChange={handleRulesChange}
                className="rounded border-gray-700"
              />
              <span className="text-sm text-gray-300">Take Profit</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="notify_sl_hit"
                checked={formData.routing_rules.notify_sl_hit}
                onChange={handleRulesChange}
                className="rounded border-gray-700"
              />
              <span className="text-sm text-gray-300">Stop Loss</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="notify_signal_closed"
                checked={formData.routing_rules.notify_signal_closed}
                onChange={handleRulesChange}
                className="rounded border-gray-700"
              />
              <span className="text-sm text-gray-300">Закрытие сигналов</span>
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                name="notify_errors"
                checked={formData.routing_rules.notify_errors}
                onChange={handleRulesChange}
                className="rounded border-gray-700"
              />
              <span className="text-sm text-gray-300">Ошибки</span>
            </label>
          </div>
        </div>

        {/* Submit */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={saveMutation.isPending}
            className="btn-primary flex-1 flex items-center justify-center gap-2"
          >
            {saveMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            {channel ? 'Сохранить' : 'Создать канал'}
          </button>
          <button
            type="button"
            onClick={onClose}
            className="btn-secondary"
          >
            Отмена
          </button>
        </div>
      </form>
    </div>
  )
}
