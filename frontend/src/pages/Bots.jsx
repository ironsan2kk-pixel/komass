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
import { Button, Card, Input, Select, Spinner, Badge } from '../components/ui';

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
          <Spinner size="lg" className="mx-auto mb-4" />
          <p className="text-gray-400">Загрузка ботов...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center">
          <p className="text-danger-400 text-xl mb-2">❌ Ошибка</p>
          <p className="text-gray-400">{error}</p>
          <Button
            variant="primary"
            onClick={fetchBots}
            className="mt-4"
          >
            Повторить
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex gap-4 p-4">
      {/* Left Panel - Bot List */}
      <Card className="w-80 flex-shrink-0 flex flex-col">
        <Card.Header className="border-b border-dark-700">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">Боты</h2>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setShowCreateModal(true)}
            >
              + Создать
            </Button>
          </div>
          <p className="text-sm text-gray-400 mt-1">
            {bots.length} ботов • {bots.filter(b => b.status === 'running').length} активных
          </p>
        </Card.Header>

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
      </Card>

      {/* Right Panel - Bot Details */}
      <Card className="flex-1 flex flex-col overflow-hidden">
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
                      <Button
                        variant="warning"
                        size="sm"
                        onClick={() => controlBot(selectedBot.id, 'pause')}
                      >
                        ⏸️ Пауза
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => controlBot(selectedBot.id, 'stop')}
                      >
                        ⏹️ Стоп
                      </Button>
                    </>
                  ) : selectedBot.status === 'paused' ? (
                    <>
                      <Button
                        variant="success"
                        size="sm"
                        onClick={() => controlBot(selectedBot.id, 'resume')}
                      >
                        ▶️ Продолжить
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => controlBot(selectedBot.id, 'stop')}
                      >
                        ⏹️ Стоп
                      </Button>
                    </>
                  ) : (
                    <Button
                      variant="success"
                      size="sm"
                      onClick={() => controlBot(selectedBot.id, 'start')}
                    >
                      ▶️ Запустить
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => deleteBot(selectedBot.id)}
                    className="hover:bg-danger-600 hover:text-white"
                  >
                    🗑️
                  </Button>
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
      </Card>

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
        <Spinner size="md" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-2">
        {['all', 'win', 'loss', 'long', 'short'].map((f) => (
          <Button
            key={f}
            variant={filter === f ? 'primary' : 'secondary'}
            size="sm"
            onClick={() => setFilter(f)}
          >
            {f === 'all' ? 'Все' : f === 'win' ? '✓ Win' : f === 'loss' ? '✗ Loss' : f === 'long' ? '🟢 Long' : '🔴 Short'}
          </Button>
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
      <Input
        label="Название"
        type="text"
        value={settings.name}
        onChange={(e) => setSettings({ ...settings, name: e.target.value })}
      />

      <Input
        label="Капитал ($)"
        type="number"
        value={settings.capital}
        onChange={(e) => setSettings({ ...settings, capital: parseFloat(e.target.value) })}
      />

      <Input
        label="Риск на сделку (%)"
        type="number"
        value={settings.risk_per_trade}
        onChange={(e) => setSettings({ ...settings, risk_per_trade: parseFloat(e.target.value) })}
        min={0.1}
        max={10}
        step={0.1}
      />

      <Input
        label="Макс. позиций"
        type="number"
        value={settings.max_positions}
        onChange={(e) => setSettings({ ...settings, max_positions: parseInt(e.target.value) })}
        min={1}
        max={20}
      />

      <Input
        label="Плечо (x)"
        type="number"
        value={settings.leverage}
        onChange={(e) => setSettings({ ...settings, leverage: parseInt(e.target.value) })}
        min={1}
        max={125}
      />

      <Button
        variant="primary"
        className="w-full"
        onClick={handleSave}
        disabled={saving}
        loading={saving}
      >
        {saving ? 'Сохранение...' : 'Сохранить настройки'}
      </Button>
    </div>
  );
}

// Create Bot Modal
function CreateBotModal({ newBot, setNewBot, presets, onClose, onCreate }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md">
        <Card.Header>
          <h2 className="text-xl font-bold">Создать бота</h2>
        </Card.Header>

        <Card.Body className="space-y-4">
          <Input
            label="Название"
            type="text"
            value={newBot.name}
            onChange={(e) => setNewBot({ ...newBot, name: e.target.value })}
            placeholder="Мой бот"
          />

          <Input
            label="Капитал ($)"
            type="number"
            value={newBot.capital}
            onChange={(e) => setNewBot({ ...newBot, capital: parseFloat(e.target.value) })}
          />

          <Input
            label="Символы"
            type="text"
            value={newBot.symbols.join(', ')}
            onChange={(e) => setNewBot({
              ...newBot,
              symbols: e.target.value.split(',').map(s => s.trim().toUpperCase()).filter(Boolean)
            })}
            placeholder="BTCUSDT, ETHUSDT"
            helper="Через запятую"
          />

          <Select
            label="Пресет настроек"
            value={newBot.preset_id}
            onChange={(e) => setNewBot({ ...newBot, preset_id: e.target.value })}
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
          </Select>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1">Описание</label>
            <textarea
              value={newBot.description}
              onChange={(e) => setNewBot({ ...newBot, description: e.target.value })}
              className="w-full bg-dark-800 border border-dark-600 rounded-lg px-3 py-2
                       text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 h-20 resize-none"
              placeholder="Описание бота..."
            />
          </div>

          <div className="flex gap-3 mt-6">
            <Button
              variant="secondary"
              className="flex-1"
              onClick={onClose}
            >
              Отмена
            </Button>
            <Button
              variant="primary"
              className="flex-1"
              onClick={onCreate}
              disabled={!newBot.name}
            >
              Создать
            </Button>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
}
