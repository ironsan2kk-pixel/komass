import { useState, useEffect, useRef, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Zap, Filter, Download, RefreshCw, X, TrendingUp, TrendingDown,
  ChevronLeft, ChevronRight, Search, AlertCircle, CheckCircle2,
  Clock, DollarSign, Percent, Target, Activity
} from 'lucide-react'
import toast from 'react-hot-toast'
import { signalsApi } from '../api'

// === Статистика сигналов ===
function SignalsStats({ stats }) {
  if (!stats) return null
  
  const items = [
    { 
      label: 'Всего сигналов', 
      value: stats.total || 0, 
      icon: Activity,
      color: 'text-blue-400'
    },
    { 
      label: 'Активных', 
      value: stats.active || 0, 
      icon: Zap,
      color: 'text-yellow-400'
    },
    { 
      label: 'Win Rate', 
      value: `${(stats.win_rate || 0).toFixed(1)}%`, 
      icon: Target,
      color: stats.win_rate >= 50 ? 'text-green-400' : 'text-red-400'
    },
    { 
      label: 'Общий PnL', 
      value: `${(stats.total_pnl || 0).toFixed(2)}%`, 
      icon: DollarSign,
      color: stats.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'
    },
    { 
      label: 'Wins / Losses', 
      value: `${stats.wins || 0} / ${stats.losses || 0}`, 
      icon: Percent,
      color: 'text-gray-400'
    },
  ]

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
      {items.map((item, i) => (
        <div key={i} className="card p-4">
          <div className="flex items-center gap-2 mb-2">
            <item.icon className={`h-4 w-4 ${item.color}`} />
            <span className="text-xs text-gray-500">{item.label}</span>
          </div>
          <p className={`text-xl font-bold ${item.color}`}>{item.value}</p>
        </div>
      ))}
    </div>
  )
}

// === Фильтры ===
function SignalsFilters({ filters, onChange, symbols }) {
  return (
    <div className="card p-4">
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-gray-500" />
          <span className="text-sm text-gray-400">Фильтры:</span>
        </div>

        {/* Поиск */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="text"
            placeholder="Поиск..."
            value={filters.search || ''}
            onChange={(e) => onChange({ ...filters, search: e.target.value })}
            className="input pl-9 w-48"
          />
        </div>

        {/* Символ */}
        <select
          value={filters.symbol || ''}
          onChange={(e) => onChange({ ...filters, symbol: e.target.value })}
          className="select w-36"
        >
          <option value="">Все пары</option>
          {symbols?.map(s => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        {/* Направление */}
        <select
          value={filters.direction || ''}
          onChange={(e) => onChange({ ...filters, direction: e.target.value })}
          className="select w-32"
        >
          <option value="">Все</option>
          <option value="long">Long</option>
          <option value="short">Short</option>
        </select>

        {/* Статус */}
        <select
          value={filters.status || ''}
          onChange={(e) => onChange({ ...filters, status: e.target.value })}
          className="select w-36"
        >
          <option value="">Все статусы</option>
          <option value="active">Активные</option>
          <option value="closed">Закрытые</option>
          <option value="cancelled">Отменённые</option>
        </select>

        {/* Сброс */}
        <button
          onClick={() => onChange({ status: '', symbol: '', direction: '', search: '' })}
          className="btn-ghost text-sm"
        >
          <X className="h-4 w-4" />
          Сбросить
        </button>
      </div>
    </div>
  )
}

// === Таблица сигналов ===
function SignalsTable({ signals, onClose, isClosing }) {
  const getDirectionIcon = (direction) => {
    return direction === 'long' 
      ? <TrendingUp className="h-4 w-4 text-green-400" />
      : <TrendingDown className="h-4 w-4 text-red-400" />
  }

  const getStatusBadge = (status) => {
    const styles = {
      active: 'bg-yellow-500/20 text-yellow-400',
      closed: 'bg-gray-500/20 text-gray-400',
      tp_hit: 'bg-green-500/20 text-green-400',
      sl_hit: 'bg-red-500/20 text-red-400',
      cancelled: 'bg-gray-500/20 text-gray-500',
    }
    const labels = {
      active: 'Активен',
      closed: 'Закрыт',
      tp_hit: 'TP Hit',
      sl_hit: 'SL Hit',
      cancelled: 'Отменён',
    }
    return (
      <span className={`badge ${styles[status] || styles.closed}`}>
        {labels[status] || status}
      </span>
    )
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const formatPrice = (price) => {
    if (!price) return '-'
    return parseFloat(price).toFixed(2)
  }

  const formatPnL = (pnl) => {
    if (pnl === null || pnl === undefined) return '-'
    const value = parseFloat(pnl)
    const color = value >= 0 ? 'text-green-400' : 'text-red-400'
    const sign = value >= 0 ? '+' : ''
    return <span className={color}>{sign}{value.toFixed(2)}%</span>
  }

  if (!signals?.length) {
    return (
      <div className="card py-16 text-center">
        <Zap className="h-12 w-12 text-gray-600 mx-auto mb-4" />
        <p className="text-gray-500">Нет сигналов по выбранным фильтрам</p>
      </div>
    )
  }

  return (
    <div className="card overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-800/50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Время</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Пара</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Направление</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Вход</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">TP / SL</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Статус</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">PnL</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase">Действия</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800">
            {signals.map((signal) => (
              <tr key={signal.id} className="hover:bg-gray-800/30 transition-colors">
                <td className="px-4 py-3 text-sm font-mono text-gray-400">
                  #{signal.id}
                </td>
                <td className="px-4 py-3 text-sm text-gray-300 whitespace-nowrap">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3 text-gray-500" />
                    {formatDate(signal.created_at)}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm font-medium text-white">
                  {signal.symbol}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {getDirectionIcon(signal.direction)}
                    <span className={signal.direction === 'long' ? 'text-green-400' : 'text-red-400'}>
                      {signal.direction?.toUpperCase()}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm font-mono text-gray-300">
                  ${formatPrice(signal.entry_price)}
                </td>
                <td className="px-4 py-3 text-sm font-mono">
                  <div className="flex flex-col gap-0.5">
                    <span className="text-green-400">${formatPrice(signal.take_profit)}</span>
                    <span className="text-red-400">${formatPrice(signal.stop_loss)}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  {getStatusBadge(signal.status)}
                </td>
                <td className="px-4 py-3 text-sm font-medium">
                  {formatPnL(signal.pnl)}
                </td>
                <td className="px-4 py-3">
                  {signal.status === 'active' && (
                    <button
                      onClick={() => onClose(signal.id)}
                      disabled={isClosing}
                      className="btn-ghost btn-sm text-red-400 hover:text-red-300"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// === Пагинация ===
function Pagination({ page, totalPages, onPageChange }) {
  if (totalPages <= 1) return null

  return (
    <div className="flex items-center justify-center gap-2">
      <button
        onClick={() => onPageChange(page - 1)}
        disabled={page <= 1}
        className="btn-ghost btn-sm disabled:opacity-50"
      >
        <ChevronLeft className="h-4 w-4" />
      </button>
      
      <span className="text-sm text-gray-400">
        Страница {page} из {totalPages}
      </span>
      
      <button
        onClick={() => onPageChange(page + 1)}
        disabled={page >= totalPages}
        className="btn-ghost btn-sm disabled:opacity-50"
      >
        <ChevronRight className="h-4 w-4" />
      </button>
    </div>
  )
}

// === Основной компонент ===
export default function Signals() {
  const queryClient = useQueryClient()
  const eventSourceRef = useRef(null)
  
  const [filters, setFilters] = useState({
    status: '',
    symbol: '',
    direction: '',
    search: ''
  })
  const [page, setPage] = useState(1)
  const [isSSEConnected, setIsSSEConnected] = useState(false)
  const limit = 20

  // Загрузка сигналов
  const { data: signalsData, isLoading, refetch } = useQuery({
    queryKey: ['signals', filters, page],
    queryFn: () => signalsApi.getAll({
      ...filters,
      page,
      limit
    }).then(r => r.data),
    refetchInterval: isSSEConnected ? false : 10000, // Отключаем polling если SSE работает
  })

  // Загрузка статистики
  const { data: stats } = useQuery({
    queryKey: ['signals-stats'],
    queryFn: () => signalsApi.getStats().then(r => r.data),
    refetchInterval: 30000,
  })

  // Загрузка списка символов
  const { data: symbols } = useQuery({
    queryKey: ['signals-symbols'],
    queryFn: () => signalsApi.getSymbols().then(r => r.data),
  })

  // Закрытие сигнала
  const closeMutation = useMutation({
    mutationFn: (id) => signalsApi.close(id),
    onSuccess: () => {
      toast.success('Сигнал закрыт')
      queryClient.invalidateQueries(['signals'])
      queryClient.invalidateQueries(['signals-stats'])
    },
    onError: (err) => {
      toast.error(`Ошибка: ${err.response?.data?.detail || err.message}`)
    }
  })

  // Экспорт
  const handleExport = async (format) => {
    try {
      const response = await signalsApi.export({ format, ...filters })
      const blob = new Blob([response.data], {
        type: format === 'csv' ? 'text/csv' : 'application/json'
      })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `signals_export.${format}`
      a.click()
      URL.revokeObjectURL(url)
      toast.success(`Экспорт в ${format.toUpperCase()} завершён`)
    } catch (err) {
      toast.error(`Ошибка экспорта: ${err.message}`)
    }
  }

  // SSE подключение для real-time обновлений
  useEffect(() => {
    const connectSSE = () => {
      try {
        const eventSource = new EventSource('/api/signals/sse/stream')
        eventSourceRef.current = eventSource

        eventSource.onopen = () => {
          setIsSSEConnected(true)
          console.log('SSE: Connected to signals stream')
        }

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            if (data.type === 'signal_update' || data.type === 'new_signal') {
              queryClient.invalidateQueries(['signals'])
              queryClient.invalidateQueries(['signals-stats'])
              
              if (data.type === 'new_signal') {
                toast.success(`Новый сигнал: ${data.symbol} ${data.direction.toUpperCase()}`, {
                  icon: <Zap className="h-5 w-5 text-yellow-400" />
                })
              }
            }
          } catch (e) {
            console.error('SSE parse error:', e)
          }
        }

        eventSource.onerror = () => {
          setIsSSEConnected(false)
          eventSource.close()
          // Переподключение через 5 секунд
          setTimeout(connectSSE, 5000)
        }
      } catch (err) {
        console.error('SSE connection error:', err)
        setIsSSEConnected(false)
      }
    }

    connectSSE()

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
    }
  }, [queryClient])

  // Сброс страницы при изменении фильтров
  useEffect(() => {
    setPage(1)
  }, [filters])

  const signals = signalsData?.items || []
  const totalPages = Math.ceil((signalsData?.total || 0) / limit)

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-100">Сигналы</h1>
          <p className="text-gray-500">Торговые сигналы стратегии Komas</p>
        </div>
        <div className="flex items-center gap-3">
          {/* SSE статус */}
          <div className="flex items-center gap-2 text-sm">
            {isSSEConnected ? (
              <>
                <CheckCircle2 className="h-4 w-4 text-green-400" />
                <span className="text-green-400">Live</span>
              </>
            ) : (
              <>
                <AlertCircle className="h-4 w-4 text-yellow-400" />
                <span className="text-yellow-400">Reconnecting...</span>
              </>
            )}
          </div>

          {/* Экспорт */}
          <div className="relative group">
            <button className="btn-secondary">
              <Download className="h-4 w-4" />
              Экспорт
            </button>
            <div className="absolute right-0 top-full mt-1 bg-gray-800 rounded-lg shadow-lg border border-gray-700 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <button
                onClick={() => handleExport('csv')}
                className="block w-full px-4 py-2 text-left text-sm hover:bg-gray-700 rounded-t-lg"
              >
                CSV
              </button>
              <button
                onClick={() => handleExport('json')}
                className="block w-full px-4 py-2 text-left text-sm hover:bg-gray-700 rounded-b-lg"
              >
                JSON
              </button>
            </div>
          </div>

          {/* Обновить */}
          <button onClick={() => refetch()} className="btn-secondary">
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Обновить
          </button>
        </div>
      </div>

      {/* Статистика */}
      <SignalsStats stats={stats} />

      {/* Фильтры */}
      <SignalsFilters 
        filters={filters} 
        onChange={setFilters} 
        symbols={symbols}
      />

      {/* Таблица */}
      {isLoading ? (
        <div className="card py-12 text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-500 mx-auto" />
          <p className="text-gray-500 mt-2">Загрузка сигналов...</p>
        </div>
      ) : (
        <SignalsTable 
          signals={signals} 
          onClose={(id) => closeMutation.mutate(id)}
          isClosing={closeMutation.isPending}
        />
      )}

      {/* Пагинация */}
      <Pagination 
        page={page} 
        totalPages={totalPages} 
        onPageChange={setPage} 
      />
    </div>
  )
}
