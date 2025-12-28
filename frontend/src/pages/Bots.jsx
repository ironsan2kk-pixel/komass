/**
 * Bots.jsx
 * =========
 * Bot management page with filter configuration.
 * 
 * Features:
 * - Bot list with status
 * - Create/edit/delete bots
 * - Bot details panel
 * - Filter configuration tab
 * - Statistics and trades
 * 
 * Chat #44: Added FilterSettings integration
 * Author: KOMAS Team
 * Version: 4.0
 */

import { useState, useEffect } from 'react';
import { FilterSettings } from '../components/Filters';

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

// Detail tabs
const DETAIL_TABS = [
  { id: 'overview', label: 'Overview', icon: '📊' },
  { id: 'filters', label: 'Filters', icon: '🔍' },
  { id: 'trades', label: 'Trades', icon: '📋' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
];

export default function Bots() {
  // State
  const [bots, setBots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedBot, setSelectedBot] = useState(null);
  const [selectedTab, setSelectedTab] = useState('overview');
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

  // Handle filter config change
  const handleFilterConfigChange = (newConfig) => {
    console.log('Filter config updated:', newConfig);
    // Optionally refresh bot data
    fetchBots();
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

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-400 text-xl mb-2">❌ Ошибка</p>
          <p className="text-gray-400">{error}</p>
          <button
            onClick={fetchBots}
            className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
          >
            Повторить
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex gap-4 p-4">
      {/* Left Panel - Bot List */}
      <div className="w-80 flex-shrink-0 bg-gray-800 rounded-lg border border-gray-700 flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-white">Боты</h2>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded text-sm"
            >
              + Создать
            </button>
          </div>
          <p className="text-sm text-gray-400 mt-1">
            {bots.length} ботов • {bots.filter(b => b.status === 'running').length} активных
          </p>
        </div>

        {/* Bot List */}
        <div className="flex-1 overflow-y-auto">
          {bots.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p className="text-4xl mb-2">🤖</p>
              <p>Нет ботов</p>
              <p className="text-sm">Создайте первого бота</p>
            </div>
          ) : (
            <div className="p-2 space-y-2">
              {bots.map((bot) => (
                <button
                  key={bot.id}
                  onClick={() => {
                    setSelectedBot(bot);
                    setSelectedTab('overview');
                  }}
                  className={`w-full p-3 rounded-lg text-left transition-colors ${
                    selectedBot?.id === bot.id
                      ? 'bg-blue-600/20 border border-blue-500'
                      : 'bg-gray-700/50 border border-transparent hover:bg-gray-700'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-white">{bot.name}</span>
                    <span className={`w-2 h-2 rounded-full ${STATUS_COLORS[bot.status] || STATUS_COLORS.stopped}`}></span>
                  </div>
                  <div className="flex items-center justify-between mt-1 text-sm">
                    <span className="text-gray-400">
                      {bot.symbols?.length || 0} пар
                    </span>
                    <span className={`${(bot.stats?.pnl_percent || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                      {formatPercent(bot.stats?.pnl_percent)}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Right Panel - Bot Details */}
      <div className="flex-1 bg-gray-800 rounded-lg border border-gray-700 flex flex-col overflow-hidden">
        {selectedBot ? (
          <>
            {/* Bot Header */}
            <div className="p-4 border-b border-gray-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{STATUS_ICONS[selectedBot.status] || '🤖'}</span>
                  <div>
                    <h2 className="text-xl font-bold text-white">{selectedBot.name}</h2>
                    <p className="text-sm text-gray-400">
                      {selectedBot.symbols?.join(', ') || 'No symbols'}
                    </p>
                  </div>
                </div>
                
                {/* Control Buttons */}
                <div className="flex items-center gap-2">
                  {selectedBot.status === 'running' ? (
                    <>
                      <button
                        onClick={() => controlBot(selectedBot.id, 'pause')}
                        className="px-3 py-1.5 bg-yellow-600 hover:bg-yellow-500 text-white rounded text-sm"
                      >
                        ⏸️ Пауза
                      </button>
                      <button
                        onClick={() => controlBot(selectedBot.id, 'stop')}
                        className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded text-sm"
                      >
                        ⏹️ Стоп
                      </button>
                    </>
                  ) : selectedBot.status === 'paused' ? (
                    <>
                      <button
                        onClick={() => controlBot(selectedBot.id, 'resume')}
                        className="px-3 py-1.5 bg-green-600 hover:bg-green-500 text-white rounded text-sm"
                      >
                        ▶️ Продолжить
                      </button>
                      <button
                        onClick={() => controlBot(selectedBot.id, 'stop')}
                        className="px-3 py-1.5 bg-red-600 hover:bg-red-500 text-white rounded text-sm"
                      >
                        ⏹️ Стоп
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => controlBot(selectedBot.id, 'start')}
                      className="px-3 py-1.5 bg-green-600 hover:bg-green-500 text-white rounded text-sm"
                    >
                      ▶️ Запустить
                    </button>
                  )}
                  <button
                    onClick={() => deleteBot(selectedBot.id)}
                    className="px-3 py-1.5 bg-gray-700 hover:bg-red-600 text-gray-300 hover:text-white rounded text-sm"
                  >
                    🗑️
                  </button>
                </div>
              </div>

              {/* Tabs */}
              <div className="flex gap-1 mt-4">
                {DETAIL_TABS.map((tab) => (
                  <button
                    key={tab.id}
                    onClick={() => setSelectedTab(tab.id)}
                    className={`px-4 py-2 rounded-t-lg text-sm font-medium transition-colors ${
                      selectedTab === tab.id
                        ? 'bg-gray-700 text-white'
                        : 'text-gray-400 hover:text-white hover:bg-gray-700/50'
                    }`}
                  >
                    <span className="mr-1.5">{tab.icon}</span>
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Tab Content */}
            <div className="flex-1 overflow-y-auto p-4">
              {selectedTab === 'overview' && (
                <BotOverview bot={selectedBot} formatCurrency={formatCurrency} formatPercent={formatPercent} />
              )}
              
              {selectedTab === 'filters' && (
                <FilterSettings 
                  botId={selectedBot.id} 
                  onConfigChange={handleFilterConfigChange}
                />
              )}
              
              {selectedTab === 'trades' && (
                <BotTrades bot={selectedBot} formatPercent={formatPercent} />
              )}
              
              {selectedTab === 'settings' && (
                <BotSettings bot={selectedBot} onUpdate={fetchBots} />
              )}
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center text-gray-500">
              <p className="text-6xl mb-4">🤖</p>
              <p className="text-xl">Выберите бота</p>
              <p className="text-sm mt-2">или создайте нового</p>
            </div>
          </div>
        )}
      </div>

      {/* Create Bot Modal */}
      {showCreateModal && (
        <CreateBotModal
          newBot={newBot}
          setNewBot={setNewBot}
          presets={presets}
          onClose={() => setShowCreateModal(false)}
          onCreate={createBot}
        />
      )}
    </div>
  );
}

// Bot Overview Component
function BotOverview({ bot, formatCurrency, formatPercent }) {
  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-gray-900/50 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-1">Капитал</p>
          <p className="text-2xl font-bold text-white">
            {formatCurrency(bot.capital || 0)}
          </p>
        </div>
        <div className="bg-gray-900/50 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-1">PnL</p>
          <p className={`text-2xl font-bold ${(bot.stats?.pnl_percent || 0) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
            {formatPercent(bot.stats?.pnl_percent)}
          </p>
        </div>
        <div className="bg-gray-900/50 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-1">Max Drawdown</p>
          <p className="text-2xl font-bold text-red-400">
            {bot.stats?.max_drawdown?.toFixed(2) || '0.00'}%
          </p>
        </div>
        <div className="bg-gray-900/50 rounded-lg p-4">
          <p className="text-gray-400 text-sm mb-1">Активных позиций</p>
          <p className="text-2xl font-bold text-blue-400">
            {bot.stats?.open_positions || 0}
          </p>
        </div>
      </div>

      {/* Strategies */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-3">Стратегии</h3>
        <div className="space-y-2">
          {(bot.strategies || []).length === 0 ? (
            <p className="text-gray-400 text-sm">Нет активных стратегий</p>
          ) : (
            bot.strategies.map((strategy, idx) => (
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

      {/* Recent Trades Preview */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-3">Последние сделки</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="text-gray-400 text-left">
              <tr>
                <th className="pb-2">Время</th>
                <th className="pb-2">Символ</th>
                <th className="pb-2">Тип</th>
                <th className="pb-2">PnL</th>
              </tr>
            </thead>
            <tbody>
              {(bot.recent_trades || []).length === 0 ? (
                <tr>
                  <td colSpan={4} className="py-4 text-center text-gray-400">
                    Нет сделок
                  </td>
                </tr>
              ) : (
                bot.recent_trades.slice(0, 5).map((trade, idx) => (
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
                    <td className={`py-2 ${
                      (trade.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                    }`}>
                      {((trade.pnl || 0) >= 0 ? '+' : '') + (trade.pnl?.toFixed(2) || '0.00')}%
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Bot Trades Component
function BotTrades({ bot, formatPercent }) {
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchTrades();
  }, [bot.id]);

  const fetchTrades = async () => {
    try {
      const response = await fetch(`${API_URL}/api/bots/${bot.id}/positions/closed?limit=100`);
      if (response.ok) {
        const data = await response.json();
        setTrades(data.positions || []);
      }
    } catch (err) {
      console.error('Error fetching trades:', err);
    } finally {
      setLoading(false);
    }
  };

  const filteredTrades = trades.filter(t => {
    if (filter === 'all') return true;
    if (filter === 'win') return (t.pnl || 0) > 0;
    if (filter === 'loss') return (t.pnl || 0) < 0;
    if (filter === 'long') return t.side === 'long';
    if (filter === 'short') return t.side === 'short';
    return true;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'win', 'loss', 'long', 'short'].map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded text-sm ${
              filter === f
                ? 'bg-blue-600 text-white'
                : 'bg-gray-700 text-gray-400 hover:text-white'
            }`}
          >
            {f === 'all' ? 'Все' : f === 'win' ? '✓ Win' : f === 'loss' ? '✗ Loss' : f === 'long' ? '🟢 Long' : '🔴 Short'}
          </button>
        ))}
      </div>

      {/* Trades Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="text-gray-400 text-left">
            <tr>
              <th className="pb-2">Время</th>
              <th className="pb-2">Символ</th>
              <th className="pb-2">Тип</th>
              <th className="pb-2">Entry</th>
              <th className="pb-2">Exit</th>
              <th className="pb-2">PnL</th>
            </tr>
          </thead>
          <tbody>
            {filteredTrades.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-8 text-center text-gray-400">
                  Нет сделок
                </td>
              </tr>
            ) : (
              filteredTrades.map((trade, idx) => (
                <tr key={idx} className="border-t border-gray-700">
                  <td className="py-2 text-gray-300">
                    {new Date(trade.closed_at || trade.timestamp).toLocaleString('ru-RU')}
                  </td>
                  <td className="py-2 text-white">{trade.symbol}</td>
                  <td className={`py-2 ${
                    trade.side === 'long' ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {trade.side === 'long' ? '🟢' : '🔴'}
                  </td>
                  <td className="py-2 text-gray-300">{trade.entry_price?.toFixed(2)}</td>
                  <td className="py-2 text-gray-300">{trade.exit_price?.toFixed(2)}</td>
                  <td className={`py-2 ${
                    (trade.pnl || 0) >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {formatPercent(trade.pnl)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Bot Settings Component
function BotSettings({ bot, onUpdate }) {
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({
    name: bot.name,
    capital: bot.capital || 10000,
    risk_per_trade: bot.risk_per_trade || 1,
    max_positions: bot.max_positions || 3,
    leverage: bot.leverage || 10,
  });

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await fetch(`${API_URL}/api/bots/${bot.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      
      if (!response.ok) throw new Error('Failed to update bot');
      
      onUpdate();
    } catch (err) {
      alert(`Error: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6 max-w-md">
      <div>
        <label className="block text-sm text-gray-400 mb-1">Название</label>
        <input
          type="text"
          value={settings.name}
          onChange={(e) => setSettings({ ...settings, name: e.target.value })}
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 
                   text-white focus:outline-none focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm text-gray-400 mb-1">Капитал ($)</label>
        <input
          type="number"
          value={settings.capital}
          onChange={(e) => setSettings({ ...settings, capital: parseFloat(e.target.value) })}
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 
                   text-white focus:outline-none focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm text-gray-400 mb-1">Риск на сделку (%)</label>
        <input
          type="number"
          value={settings.risk_per_trade}
          onChange={(e) => setSettings({ ...settings, risk_per_trade: parseFloat(e.target.value) })}
          min={0.1}
          max={10}
          step={0.1}
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 
                   text-white focus:outline-none focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm text-gray-400 mb-1">Макс. позиций</label>
        <input
          type="number"
          value={settings.max_positions}
          onChange={(e) => setSettings({ ...settings, max_positions: parseInt(e.target.value) })}
          min={1}
          max={20}
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 
                   text-white focus:outline-none focus:border-blue-500"
        />
      </div>

      <div>
        <label className="block text-sm text-gray-400 mb-1">Плечо (x)</label>
        <input
          type="number"
          value={settings.leverage}
          onChange={(e) => setSettings({ ...settings, leverage: parseInt(e.target.value) })}
          min={1}
          max={125}
          className="w-full bg-gray-900 border border-gray-600 rounded-lg px-3 py-2 
                   text-white focus:outline-none focus:border-blue-500"
        />
      </div>

      <button
        onClick={handleSave}
        disabled={saving}
        className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg disabled:opacity-50"
      >
        {saving ? 'Сохранение...' : 'Сохранить настройки'}
      </button>
    </div>
  );
}

// Create Bot Modal
function CreateBotModal({ newBot, setNewBot, presets, onClose, onCreate }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-md border border-gray-700">
        <h2 className="text-xl font-bold text-white mb-4">Создать бота</h2>
        
        <div className="space-y-4">
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

        <div className="flex gap-3 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 
                     text-white rounded-lg"
          >
            Отмена
          </button>
          <button
            onClick={onCreate}
            disabled={!newBot.name}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 
                     text-white rounded-lg disabled:opacity-50"
          >
            Создать
          </button>
        </div>
      </div>
    </div>
  );
}
