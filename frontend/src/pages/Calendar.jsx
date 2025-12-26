import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Calendar, AlertTriangle, Clock, RefreshCw, Filter, 
  Bell, BellOff, Settings, Shield, ShieldOff
} from 'lucide-react'
import toast from 'react-hot-toast'
import { calendarApi, settingsApi } from '../api'

// === Настройки блокировки торговли ===
function TradingBlockSettings({ settings, onChange }) {
  return (
    <div className="card bg-gray-800/50">
      <div className="card-header flex items-center gap-2">
        <Shield className="h-5 w-5 text-blue-400" />
        <span>Блокировка торговли во время новостей</span>
      </div>
      
      <div className="space-y-4">
        <label className="flex items-center gap-3">
          <input
            type="checkbox"
            checked={settings.block_trading}
            onChange={(e) => onChange({ ...settings, block_trading: e.target.checked })}
            className="w-5 h-5 rounded border-gray-600"
          />
          <div>
            <span className="text-gray-200 font-medium">Блокировать торговлю</span>
            <p className="text-xs text-gray-500">Приостановить сигналы во время важных событий</p>
          </div>
        </label>

        {settings.block_trading && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pl-8">
            <div>
              <label className="label">Минут до события</label>
              <input
                type="number"
                value={settings.minutes_before}
                onChange={(e) => onChange({ ...settings, minutes_before: parseInt(e.target.value) })}
                min="0"
                max="120"
                className="input"
              />
            </div>
            <div>
              <label className="label">Минут после события</label>
              <input
                type="number"
                value={settings.minutes_after}
                onChange={(e) => onChange({ ...settings, minutes_after: parseInt(e.target.value) })}
                min="0"
                max="120"
                className="input"
              />
            </div>
            <div>
              <label className="label">Минимальная важность</label>
              <select
                value={settings.min_impact}
                onChange={(e) => onChange({ ...settings, min_impact: e.target.value })}
                className="select"
              >
                <option value="high">Только высокая</option>
                <option value="medium">Средняя и выше</option>
                <option value="low">Все события</option>
              </select>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// === Текущий статус блокировки ===
function BlockStatus({ isBlocked, event }) {
  if (!isBlocked) return null

  return (
    <div className="card bg-red-500/10 border-red-500/50">
      <div className="flex items-start gap-3">
        <ShieldOff className="h-5 w-5 text-red-400 mt-0.5 animate-pulse" />
        <div>
          <h3 className="font-semibold text-red-400">Торговля приостановлена</h3>
          <p className="text-sm text-gray-400 mt-1">
            Новые сигналы временно заблокированы из-за экономического события
          </p>
          {event && (
            <div className="mt-2 p-2 bg-gray-800/50 rounded">
              <p className="text-sm text-gray-300">
                <span className="font-medium">{event.currency}</span>: {event.event}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(event.timestamp).toLocaleString('ru-RU')}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// === Основной компонент ===
export default function CalendarPage() {
  const queryClient = useQueryClient()
  const [hoursAhead, setHoursAhead] = useState(24)
  const [impactFilter, setImpactFilter] = useState('')
  const [currencyFilter, setCurrencyFilter] = useState('')
  
  const [blockSettings, setBlockSettings] = useState({
    block_trading: false,
    minutes_before: 15,
    minutes_after: 15,
    min_impact: 'high',
  })

  // Загрузка событий
  const { data: events, isLoading, refetch } = useQuery({
    queryKey: ['calendar-events', hoursAhead, impactFilter, currencyFilter],
    queryFn: () => {
      const params = new URLSearchParams()
      params.append('hours_ahead', hoursAhead.toString())
      if (impactFilter) params.append('impact', impactFilter)
      if (currencyFilter) params.append('currency', currencyFilter)
      return calendarApi.getEvents(params).then(r => r.data)
    },
    refetchInterval: 60000,
  })

  // Важные события сегодня
  const { data: highImpactToday } = useQuery({
    queryKey: ['high-impact-today'],
    queryFn: () => calendarApi.getHighImpactToday().then(r => r.data),
    refetchInterval: 60000,
  })

  // Статус блокировки
  const { data: blockStatus } = useQuery({
    queryKey: ['trading-block-status'],
    queryFn: () => calendarApi.getBlockStatus().then(r => r.data),
    refetchInterval: 30000,
    enabled: blockSettings.block_trading,
  })

  // Загрузка настроек блокировки
  const { data: savedBlockSettings } = useQuery({
    queryKey: ['calendar-block-settings'],
    queryFn: () => settingsApi.getCalendarSettings().then(r => r.data),
  })

  useEffect(() => {
    if (savedBlockSettings) {
      setBlockSettings(prev => ({ ...prev, ...savedBlockSettings }))
    }
  }, [savedBlockSettings])

  // Сохранение настроек блокировки
  const saveBlockSettingsMutation = useMutation({
    mutationFn: () => settingsApi.saveCalendarSettings(blockSettings),
    onSuccess: () => {
      toast.success('Настройки сохранены')
      queryClient.invalidateQueries(['calendar-block-settings'])
    },
    onError: (err) => {
      toast.error(`Ошибка: ${err.message}`)
    }
  })

  // Обновление календаря
  const handleRefresh = async () => {
    try {
      await calendarApi.refresh()
      refetch()
      toast.success('Календарь обновлён')
    } catch (err) {
      toast.error(`Ошибка обновления: ${err.message}`)
    }
  }

  const getImpactColor = (impact) => {
    switch (impact) {
      case 'high': return 'text-red-400 bg-red-500/20'
      case 'medium': return 'text-yellow-400 bg-yellow-500/20'
      default: return 'text-gray-400 bg-gray-500/20'
    }
  }

  const getImpactLabel = (impact) => {
    switch (impact) {
      case 'high': return 'Высокая'
      case 'medium': return 'Средняя'
      default: return 'Низкая'
    }
  }

  const currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY']

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Экономический календарь</h1>
          <p className="text-gray-500">Предстоящие экономические события</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={() => saveBlockSettingsMutation.mutate()}
            className="btn-secondary"
          >
            <Settings className="h-4 w-4" />
            Сохранить настройки
          </button>
          <button onClick={handleRefresh} className="btn-primary">
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Обновить
          </button>
        </div>
      </div>

      {/* Статус блокировки */}
      <BlockStatus isBlocked={blockStatus?.is_blocked} event={blockStatus?.blocking_event} />

      {/* Настройки блокировки */}
      <TradingBlockSettings settings={blockSettings} onChange={setBlockSettings} />

      {/* Важные события сегодня */}
      {highImpactToday?.length > 0 && (
        <div className="card bg-red-500/10 border-red-500/50">
          <div className="flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-red-400 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-400">Важные события сегодня</h3>
              <p className="text-sm text-gray-400 mt-1">
                {highImpactToday.length} событий высокой важности могут повлиять на торговлю
              </p>
              <div className="flex flex-wrap gap-2 mt-3">
                {highImpactToday.map((event, i) => (
                  <span key={i} className="badge bg-red-500/20 text-red-400">
                    {event.currency}: {event.event}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Фильтры */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-500" />
            <span className="text-sm text-gray-400">Фильтры:</span>
          </div>
          
          <div>
            <select
              value={hoursAhead}
              onChange={(e) => setHoursAhead(Number(e.target.value))}
              className="select w-32 text-sm"
            >
              <option value={4}>4 часа</option>
              <option value={12}>12 часов</option>
              <option value={24}>24 часа</option>
              <option value={48}>48 часов</option>
              <option value={168}>Неделя</option>
            </select>
          </div>

          <div>
            <select
              value={impactFilter}
              onChange={(e) => setImpactFilter(e.target.value)}
              className="select w-32 text-sm"
            >
              <option value="">Все важности</option>
              <option value="high">Высокая</option>
              <option value="medium">Средняя</option>
              <option value="low">Низкая</option>
            </select>
          </div>

          <div>
            <select
              value={currencyFilter}
              onChange={(e) => setCurrencyFilter(e.target.value)}
              className="select w-28 text-sm"
            >
              <option value="">Все валюты</option>
              {currencies.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Таблица событий */}
      <div className="card">
        <div className="card-header flex items-center gap-2">
          <Calendar className="h-5 w-5 text-blue-400" />
          <span>Предстоящие события</span>
          <span className="ml-auto text-sm text-gray-500">
            {events?.length ?? 0} событий
          </span>
        </div>

        {isLoading ? (
          <div className="py-12 text-center">
            <RefreshCw className="h-8 w-8 animate-spin text-blue-500 mx-auto" />
            <p className="text-gray-500 mt-2">Загрузка...</p>
          </div>
        ) : events?.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-800/50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Время</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Валюта</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Важность</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Событие</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Прогноз</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Предыдущее</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {events.map((event, index) => (
                  <tr key={index} className="hover:bg-gray-800/30 transition-colors">
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-2">
                        <Clock className="h-4 w-4 text-gray-500" />
                        <div>
                          <div className="font-medium text-gray-200">
                            {new Date(event.timestamp).toLocaleTimeString('ru-RU', {
                              hour: '2-digit',
                              minute: '2-digit'
                            })}
                          </div>
                          <div className="text-xs text-gray-500">
                            {new Date(event.timestamp).toLocaleDateString('ru-RU')}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="font-mono font-medium text-white">{event.currency}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`badge ${getImpactColor(event.impact)}`}>
                        {getImpactLabel(event.impact)}
                      </span>
                    </td>
                    <td className="px-4 py-3 max-w-xs">
                      <span className="text-gray-200">{event.event}</span>
                    </td>
                    <td className="px-4 py-3 font-mono text-gray-400">
                      {event.forecast ?? '-'}
                    </td>
                    <td className="px-4 py-3 font-mono text-gray-400">
                      {event.previous ?? '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-12 text-center">
            <Calendar className="h-12 w-12 text-gray-600 mx-auto" />
            <p className="text-gray-500 mt-3">Нет событий в выбранном периоде</p>
          </div>
        )}
      </div>

      {/* Легенда */}
      <div className="card">
        <div className="card-header">Важность событий</div>
        <div className="flex flex-wrap gap-6">
          <div className="flex items-center gap-2">
            <span className="badge bg-red-500/20 text-red-400">Высокая</span>
            <span className="text-sm text-gray-400">
              Сильное влияние на рынок, торговля приостанавливается
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="badge bg-yellow-500/20 text-yellow-400">Средняя</span>
            <span className="text-sm text-gray-400">
              Умеренное влияние
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="badge bg-gray-500/20 text-gray-400">Низкая</span>
            <span className="text-sm text-gray-400">
              Минимальное влияние
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
