import { useState, useEffect } from 'react';

// API base
const API_URL = 'http://localhost:8000';

// Bot status colors
const STATUS_COLORS = {
  running: 'bg-green-500',
  stopped: 'bg-gray-500',
  paused: 'bg-yellow-500',
  error: 'bg-red-500',
};

// Bot status icons
const STATUS_ICONS = {
  running: '▶️',
  stopped: '⏹️',
  paused: '⏸️',
  error: '❌',
};

export default function Bots() {
  // State
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedBot, setSelectedBot] = useState(null);
  const [presets, setPresets] = useState([]);
  
  // New bot form
  const [newBot, setNewBot] = useState({
    name: '',
    symbols: ['BTCUSDT'],
    capital: 10000,
    preset_id: 'default',
    description: '',
  });

  // Fetch bots on mount
  useEffect(() => {
    fetchBots();
    fetchPresets();
    
    // Refresh every 10 seconds
    const interval = setInterval(fetchBots, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchBots = async () => {
    try {
      const response = await fetch(`${API_URL}/api/bots/`);
      if (!response.ok) throw new Error('Failed to fetch bots');
      const data = await response.json();
      setBots(data.bots || []);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching bots:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const fetchPresets = async () => {
    try {
      const response = await fetch(`${API_URL}/api/settings/presets`);
      if (response.ok) {
        const data = await response.json();
        setPresets(data.presets || []);
      }
    } catch (err) {
      console.error('Error fetching presets:', err);
    }
  };

  const createBot = async () => {
    try {
      const response = await fetch(`${API_URL}/api/bots/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newBot),
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create bot');
      }
      
      await fetchBots();
      setShowCreateModal(false);
      setNewBot({
        name: '',
        symbols: ['BTCUSDT'],
        capital: 10000,
        preset_id: 'default',
        description: '',
      });
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const deleteBot = async (botId) => {
    if (!confirm('Удалить бота? Это действие необратимо.')) return;
    
    try {
      const response = await fetch(`${API_URL}/api/bots/${botId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) throw new Error('Failed to delete bot');
      await fetchBots();
      setSelectedBot(null);
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  const controlBot = async (botId, action) => {
    try {
      const response = await fetch(`${API_URL}/api/bots/${botId}/${action}`, {
        method: 'POST',
      });
      
      if (!response.ok) throw new Error(`Failed to ${action} bot`);
      await fetchBots();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  // Format currency
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
    }).format(value);
  };

  // Format percent
  const formatPercent = (value) => {
    const sign = value >= 0 ? '+' : '';
    return `${sign}${value?.toFixed(2) || '0.00'}%`;
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Загрузка ботов...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            🤖 Боты
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Управление торговыми ботами • {bots.length} бот(ов)
          </p>
        </div>
        
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-600 
                     hover:from-green-400 hover:to-emerald-500 text-white 
                     rounded-lg font-medium shadow-lg shadow-green-500/25"
        >
          ➕ Создать бота
        </button>
      </header>

      {error && (
        <div className="bg-red-900/30 border border-red-500 rounded-lg p-4 text-red-400">
          {error}
        </div>
      )}

      {/* Bots Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {bots.length === 0 ? (
          <div className="col-span-full text-center py-12 bg-gray-800/50 rounded-lg">
            <p className="text-gray-400 mb-4">Нет созданных ботов</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="text-blue-400 hover:text-blue-300"
            >
              Создать первого бота →
            </button>
          </div>
        ) : (
          bots.map((bot) => (
            <div
              key={bot.id}
              onClick={() => setSelectedBot(bot)}
              className={`bg-gray-800 rounded-lg p-4 cursor-pointer transition-all
                         hover:bg-gray-750 border ${
                           selectedBot?.id === bot.id
                             ? 'border-blue-500'
                             : 'border-gray-700'
                         }`}
            >
              {/* Bot Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full ${STATUS_COLORS[bot.status]}`} />
                  <div>
                    <h3 className="font-semibold text-white">{bot.name}</h3>
                    <p className="text-xs text-gray-400">
                      {STATUS_ICONS[bot.status]} {bot.status}
                    </p>
                  </div>
                </div>
                
                {/* Controls */}
                <div className="flex gap-1">
                  {bot.status === 'stopped' && (
                    <button
                      onClick={(e) => { e.stopPropagation(); controlBot(bot.id, 'start'); }}
                      className="p-2 hover:bg-green-600/20 rounded text-green-400"
                      title="Запустить"
                    >
                      ▶️
                    </button>
                  )}
                  {bot.status === 'running' && (
                    <>
                      <button
                        onClick={(e) => { e.stopPropagation(); controlBot(bot.id, 'pause'); }}
                        className="p-2 hover:bg-yellow-600/20 rounded text-yellow-400"
                        title="Пауза"
                      >
                        ⏸️
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); controlBot(bot.id, 'stop'); }}
                        className="p-2 hover:bg-red-600/20 rounded text-red-400"
                        title="Остановить"
                      >
                        ⏹️
                      </button>
                    </>
                  )}
                  {bot.status === 'paused' && (
                    <button
                      onClick={(e) => { e.stopPropagation(); controlBot(bot.id, 'start'); }}
                      className="p-2 hover:bg-green-600/20 rounded text-green-400"
                      title="Продолжить"
                    >
                      ▶️
                    </button>
                  )}
                </div>
              </div>

              {/* Bot Stats */}
              <div className="grid grid-cols-2 gap-2 mb-4">
                <div className="bg-gray-900/50 rounded p-2">
                  <p className="text-xs text-gray-400">Капитал</p>
                  <p className="text-sm font-medium text-white">
                    {formatCurrency(bot.capital || 0)}
                  </p>
                </div>
                <div className="bg-gray-900/50 rounded p-2">
                  <p className="text-xs text-gray-400">PnL</p>
                  <p className={`text-sm font-medium ${
                    (bot.stats?.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {formatPercent(bot.stats?.pnl || 0)}
                  </p>
                </div>
                <div className="bg-gray-900/50 rounded p-2">
                  <p className="text-xs text-gray-400">Win Rate</p>
                  <p className="text-sm font-medium text-blue-400">
                    {bot.stats?.win_rate?.toFixed(1) || '0.0'}%
                  </p>
                </div>
                <div className="bg-gray-900/50 rounded p-2">
                  <p className="text-xs text-gray-400">Сделок</p>
                  <p className="text-sm font-medium text-white">
                    {bot.stats?.total_trades || 0}
                  </p>
                </div>
              </div>

              {/* Symbols */}
              <div className="flex flex-wrap gap-1">
                {(bot.symbols || []).map((symbol) => (
                  <span
                    key={symbol}
                    className="px-2 py-0.5 bg-blue-900/30 text-blue-400 text-xs rounded"
                  >
                    {symbol}
                  </span>
                ))}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Selected Bot Details */}
      {selectedBot && (
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-white">
              {selectedBot.name}
            </h2>
            <button
              onClick={() => deleteBot(selectedBot.id)}
              className="px-3 py-1 bg-red-600/20 hover:bg-red-600/40 
                         text-red-400 rounded text-sm"
            >
              🗑️ Удалить
            </button>
          </div>

          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="bg-gray-900/50 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">Капитал</p>
              <p className="text-2xl font-bold text-white">
                {formatCurrency(selectedBot.capital)}
              </p>
            </div>
            <div className="bg-gray-900/50 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">Текущий PnL</p>
              <p className={`text-2xl font-bold ${
                (selectedBot.stats?.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
              }`}>
                {formatPercent(selectedBot.stats?.pnl || 0)}
              </p>
            </div>
            <div className="bg-gray-900/50 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">Max Drawdown</p>
              <p className="text-2xl font-bold text-red-400">
                {selectedBot.stats?.max_drawdown?.toFixed(2) || '0.00'}%
              </p>
            </div>
            <div className="bg-gray-900/50 rounded-lg p-4">
              <p className="text-gray-400 text-sm mb-1">Активных позиций</p>
              <p className="text-2xl font-bold text-blue-400">
                {selectedBot.stats?.open_positions || 0}
              </p>
            </div>
          </div>

          {/* Strategies */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-white mb-3">Стратегии</h3>
            <div className="space-y-2">
              {(selectedBot.strategies || []).length === 0 ? (
                <p className="text-gray-400 text-sm">Нет активных стратегий</p>
              ) : (
                selectedBot.strategies.map((strategy, idx) => (
                  <div
                    key={idx}
                    className="bg-gray-900/50 rounded-lg p-3 flex items-center justify-between"
                  >
                    <div>
                      <p className="font-medium text-white">{strategy.name}</p>
                      <p className="text-xs text-gray-400">
                        {strategy.indicator} • {strategy.timeframe}
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs ${
                      strategy.active ? 'bg-green-600/20 text-green-400' : 'bg-gray-600/20 text-gray-400'
                    }`}>
                      {strategy.active ? 'Активна' : 'Отключена'}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Recent Trades */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-3">Последние сделки</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-gray-400 text-left">
                  <tr>
                    <th className="pb-2">Время</th>
                    <th className="pb-2">Символ</th>
                    <th className="pb-2">Тип</th>
                    <th className="pb-2">Цена</th>
                    <th className="pb-2">PnL</th>
                  </tr>
                </thead>
                <tbody>
                  {(selectedBot.recent_trades || []).length === 0 ? (
                    <tr>
                      <td colSpan={5} className="py-4 text-center text-gray-400">
                        Нет сделок
                      </td>
                    </tr>
                  ) : (
                    selectedBot.recent_trades.slice(0, 10).map((trade, idx) => (
                      <tr key={idx} className="border-t border-gray-700">
                        <td className="py-2 text-gray-300">
                          {new Date(trade.timestamp).toLocaleString('ru-RU')}
                        </td>
                        <td className="py-2 text-white">{trade.symbol}</td>
                        <td className={`py-2 ${
                          trade.side === 'long' ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {trade.side === 'long' ? '🟢 Long' : '🔴 Short'}
                        </td>
                        <td className="py-2 text-gray-300">{trade.price}</td>
                        <td className={`py-2 ${
                          (trade.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                        }`}>
                          {formatPercent(trade.pnl || 0)}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Create Bot Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md border border-gray-700">
            <h2 className="text-xl font-bold text-white mb-4">Создать бота</h2>
            
            <div className="space-y-4">
              {/* Name */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Название</label>
                <input
                  type="text"
                  value={newBot.name}
                  onChange={(e) => setNewBot({ ...newBot, name: e.target.value })}
                  className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 
                           text-white focus:outline-none focus:border-blue-500"
                  placeholder="Мой бот"
                />
              </div>

              {/* Capital */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Капитал ($)</label>
                <input
                  type="number"
                  value={newBot.capital}
                  onChange={(e) => setNewBot({ ...newBot, capital: parseFloat(e.target.value) })}
                  className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 
                           text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              {/* Symbols */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Символы</label>
                <input
                  type="text"
                  value={newBot.symbols.join(', ')}
                  onChange={(e) => setNewBot({ 
                    ...newBot, 
                    symbols: e.target.value.split(',').map(s => s.trim().toUpperCase()).filter(Boolean)
                  })}
                  className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 
                           text-white focus:outline-none focus:border-blue-500"
                  placeholder="BTCUSDT, ETHUSDT"
                />
                <p className="text-xs text-gray-500 mt-1">Через запятую</p>
              </div>

              {/* Preset */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Пресет настроек</label>
                <select
                  value={newBot.preset_id}
                  onChange={(e) => setNewBot({ ...newBot, preset_id: e.target.value })}
                  className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 
                           text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="default">Default (стандартный)</option>
                  <option value="conservative">Conservative (низкий риск)</option>
                  <option value="aggressive">Aggressive (высокий риск)</option>
                  <option value="scalper">Scalper (быстрые сделки)</option>
                  {presets.map((preset) => (
                    <option key={preset.id} value={preset.id}>
                      {preset.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm text-gray-400 mb-1">Описание</label>
                <textarea
                  value={newBot.description}
                  onChange={(e) => setNewBot({ ...newBot, description: e.target.value })}
                  className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 
                           text-white focus:outline-none focus:border-blue-500 h-20 resize-none"
                  placeholder="Описание бота..."
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-3 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 
                         text-white rounded-lg"
              >
                Отмена
              </button>
              <button
                onClick={createBot}
                disabled={!newBot.name}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 
                         text-white rounded-lg disabled:opacity-50"
              >
                Создать
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
