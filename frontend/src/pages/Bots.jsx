/**
 * Komas Trading Server - Bots Management Page
 * ============================================
 * Full-featured UI for managing trading bots
 */
import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../api';

// ============ ICONS ============

const PlayIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const StopIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
  </svg>
);

const PauseIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 9v6m4-6v6m7-3a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const RefreshIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
  </svg>
);

const PlusIcon = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
  </svg>
);

const TrashIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
  </svg>
);

const EditIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
  </svg>
);

const ChartIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
  </svg>
);

// ============ STATUS BADGE ============

const StatusBadge = ({ status }) => {
  const colors = {
    running: 'bg-green-500/20 text-green-400 border-green-500/30',
    stopped: 'bg-gray-500/20 text-gray-400 border-gray-500/30',
    paused: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
    error: 'bg-red-500/20 text-red-400 border-red-500/30',
  };

  const labels = {
    running: '🟢 Running',
    stopped: '⚫ Stopped',
    paused: '🟡 Paused',
    error: '🔴 Error',
  };

  return (
    <span className={`px-2 py-1 text-xs rounded border ${colors[status] || colors.stopped}`}>
      {labels[status] || status}
    </span>
  );
};

// ============ PNL DISPLAY ============

const PnlDisplay = ({ value, percent }) => {
  const isPositive = value >= 0;
  const color = isPositive ? 'text-green-400' : 'text-red-400';
  const sign = isPositive ? '+' : '';

  return (
    <div className={color}>
      <div className="font-medium">{sign}${value.toFixed(2)}</div>
      <div className="text-xs opacity-75">{sign}{percent.toFixed(2)}%</div>
    </div>
  );
};

// ============ SUMMARY CARDS ============

const SummaryCards = ({ summary, runnerStatus }) => {
  if (!summary) return null;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 mb-6">
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="text-gray-400 text-sm mb-1">Total Bots</div>
        <div className="text-2xl font-bold text-white">{summary.total_bots}</div>
      </div>
      
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="text-gray-400 text-sm mb-1">Running</div>
        <div className="text-2xl font-bold text-green-400">{summary.running_bots}</div>
      </div>
      
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="text-gray-400 text-sm mb-1">Total Capital</div>
        <div className="text-2xl font-bold text-white">${summary.total_capital.toLocaleString()}</div>
      </div>
      
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="text-gray-400 text-sm mb-1">Total PnL</div>
        <div className={`text-2xl font-bold ${summary.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {summary.total_pnl >= 0 ? '+' : ''}${summary.total_pnl.toFixed(2)}
        </div>
      </div>
      
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="text-gray-400 text-sm mb-1">Open Positions</div>
        <div className="text-2xl font-bold text-blue-400">{summary.total_open_positions}</div>
      </div>
      
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="text-gray-400 text-sm mb-1">Runner Status</div>
        <div className={`text-2xl font-bold ${runnerStatus?.running ? 'text-green-400' : 'text-gray-400'}`}>
          {runnerStatus?.running ? '🟢 Active' : '⚫ Stopped'}
        </div>
      </div>
    </div>
  );
};

// ============ CREATE BOT MODAL ============

const CreateBotModal = ({ isOpen, onClose, onCreate, presets }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [capital, setCapital] = useState(10000);
  const [leverage, setLeverage] = useState(1);
  const [symbol, setSymbol] = useState('BTCUSDT');
  const [timeframe, setTimeframe] = useState('1h');
  const [preset, setPreset] = useState('Balanced');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const selectedPreset = presets?.find(p => p.name === preset);
      
      const config = {
        name,
        description,
        initial_capital: parseFloat(capital),
        leverage: parseInt(leverage),
        commission_percent: 0.075,
        symbols: [{ symbol, timeframe, enabled: true, allocation_percent: 100 }],
        strategy: selectedPreset?.strategy || {
          indicator: 'trg',
          atr_length: 45,
          multiplier: 4.0,
          tp_count: 4,
          sl_percent: 2.0,
          sl_mode: 'fixed'
        },
        notify_signals: true,
        notify_tp_hit: true,
        notify_sl_hit: true
      };

      await onCreate(config);
      setName('');
      setDescription('');
      onClose();
    } catch (err) {
      console.error('Failed to create bot:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg p-6 w-full max-w-lg mx-4">
        <h2 className="text-xl font-bold text-white mb-4">Create New Bot</h2>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Bot Name *</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 rounded text-white"
              placeholder="My Trading Bot"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Description</label>
            <input
              type="text"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 rounded text-white"
              placeholder="BTC scalping strategy"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Initial Capital ($)</label>
              <input
                type="number"
                value={capital}
                onChange={(e) => setCapital(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 rounded text-white"
                min="100"
                step="100"
              />
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Leverage</label>
              <select
                value={leverage}
                onChange={(e) => setLeverage(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 rounded text-white"
              >
                {[1, 2, 3, 5, 10, 20, 50, 100, 125].map(l => (
                  <option key={l} value={l}>{l}x</option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-400 mb-1">Symbol</label>
              <select
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 rounded text-white"
              >
                <option value="BTCUSDT">BTCUSDT</option>
                <option value="ETHUSDT">ETHUSDT</option>
                <option value="BNBUSDT">BNBUSDT</option>
                <option value="SOLUSDT">SOLUSDT</option>
                <option value="XRPUSDT">XRPUSDT</option>
              </select>
            </div>
            <div>
              <label className="block text-sm text-gray-400 mb-1">Timeframe</label>
              <select
                value={timeframe}
                onChange={(e) => setTimeframe(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 rounded text-white"
              >
                <option value="15m">15 min</option>
                <option value="30m">30 min</option>
                <option value="1h">1 hour</option>
                <option value="4h">4 hours</option>
                <option value="1d">1 day</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-sm text-gray-400 mb-1">Strategy Preset</label>
            <select
              value={preset}
              onChange={(e) => setPreset(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 rounded text-white"
            >
              {presets?.map(p => (
                <option key={p.name} value={p.name}>{p.name} - {p.description}</option>
              ))}
            </select>
          </div>

          <div className="flex gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-white"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading || !name}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-white disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Bot'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ============ BOT DETAIL MODAL ============

const BotDetailModal = ({ bot, onClose, onAction }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [positions, setPositions] = useState([]);
  const [logs, setLogs] = useState([]);
  const [equity, setEquity] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (bot) {
      loadDetails();
    }
  }, [bot, activeTab]);

  const loadDetails = async () => {
    setLoading(true);
    try {
      if (activeTab === 'positions') {
        const [openRes, closedRes] = await Promise.all([
          api.get(`/api/bots/${bot.id}/positions/open`),
          api.get(`/api/bots/${bot.id}/positions/closed?limit=20`)
        ]);
        setPositions([...openRes.data.positions, ...closedRes.data.positions]);
      } else if (activeTab === 'logs') {
        const res = await api.get(`/api/bots/${bot.id}/logs?limit=50`);
        setLogs(res.data.logs);
      } else if (activeTab === 'equity') {
        const res = await api.get(`/api/bots/${bot.id}/equity?limit=100`);
        setEquity(res.data.points);
      }
    } catch (err) {
      console.error('Failed to load details:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!bot) return null;

  const tabs = [
    { id: 'overview', label: '📊 Overview' },
    { id: 'positions', label: '📋 Positions' },
    { id: 'equity', label: '📈 Equity' },
    { id: 'logs', label: '📝 Logs' },
  ];

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-800 rounded-lg w-full max-w-4xl mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white">{bot.name}</h2>
            <StatusBadge status={bot.status} />
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-2xl">&times;</button>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-700 flex">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm ${
                activeTab === tab.id
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-4">
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Stats Grid */}
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-700/50 rounded p-4">
                  <div className="text-gray-400 text-sm mb-1">Current Capital</div>
                  <div className="text-xl font-bold text-white">${bot.current_capital?.toLocaleString() || '0'}</div>
                </div>
                <div className="bg-gray-700/50 rounded p-4">
                  <div className="text-gray-400 text-sm mb-1">Total PnL</div>
                  <div className={`text-xl font-bold ${bot.total_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {bot.total_pnl >= 0 ? '+' : ''}${bot.total_pnl?.toFixed(2) || '0.00'}
                  </div>
                </div>
                <div className="bg-gray-700/50 rounded p-4">
                  <div className="text-gray-400 text-sm mb-1">Win Rate</div>
                  <div className="text-xl font-bold text-white">{bot.win_rate?.toFixed(1) || '0'}%</div>
                </div>
              </div>

              {/* Info */}
              <div className="bg-gray-700/50 rounded p-4 space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-400">Symbols:</span>
                  <span className="text-white">{bot.symbols?.join(', ')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Initial Capital:</span>
                  <span className="text-white">${bot.initial_capital?.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Total Trades:</span>
                  <span className="text-white">{bot.total_trades || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Open Positions:</span>
                  <span className="text-white">{bot.open_positions_count || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Created:</span>
                  <span className="text-white">{new Date(bot.created_at).toLocaleDateString()}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3">
                {bot.status === 'stopped' && (
                  <button
                    onClick={() => onAction(bot.id, 'start')}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 rounded text-white"
                  >
                    <PlayIcon /> Start
                  </button>
                )}
                {bot.status === 'running' && (
                  <>
                    <button
                      onClick={() => onAction(bot.id, 'pause')}
                      className="flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-500 rounded text-white"
                    >
                      <PauseIcon /> Pause
                    </button>
                    <button
                      onClick={() => onAction(bot.id, 'stop')}
                      className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 rounded text-white"
                    >
                      <StopIcon /> Stop
                    </button>
                  </>
                )}
                {bot.status === 'paused' && (
                  <button
                    onClick={() => onAction(bot.id, 'resume')}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 rounded text-white"
                  >
                    <PlayIcon /> Resume
                  </button>
                )}
                <button
                  onClick={() => onAction(bot.id, 'force-check')}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-white"
                  disabled={bot.status !== 'running'}
                >
                  <RefreshIcon /> Force Check
                </button>
              </div>
            </div>
          )}

          {activeTab === 'positions' && (
            <div className="space-y-2">
              {loading ? (
                <div className="text-center text-gray-400 py-8">Loading...</div>
              ) : positions.length === 0 ? (
                <div className="text-center text-gray-400 py-8">No positions</div>
              ) : (
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-gray-400 text-sm">
                      <th className="pb-2">Symbol</th>
                      <th className="pb-2">Direction</th>
                      <th className="pb-2">Entry</th>
                      <th className="pb-2">Exit</th>
                      <th className="pb-2">PnL</th>
                      <th className="pb-2">Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {positions.map((pos, idx) => (
                      <tr key={idx} className="border-t border-gray-700">
                        <td className="py-2 text-white">{pos.symbol}</td>
                        <td className={`py-2 ${pos.direction === 'long' ? 'text-green-400' : 'text-red-400'}`}>
                          {pos.direction?.toUpperCase()}
                        </td>
                        <td className="py-2 text-white">${pos.entry_price?.toFixed(2)}</td>
                        <td className="py-2 text-white">
                          {pos.exit_price ? `$${pos.exit_price.toFixed(2)}` : '-'}
                        </td>
                        <td className={`py-2 ${pos.realized_pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                          {pos.realized_pnl >= 0 ? '+' : ''}${pos.realized_pnl?.toFixed(2) || '0.00'}
                        </td>
                        <td className="py-2">
                          <span className={`px-2 py-1 text-xs rounded ${
                            pos.status === 'open' ? 'bg-blue-500/20 text-blue-400' : 'bg-gray-500/20 text-gray-400'
                          }`}>
                            {pos.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          )}

          {activeTab === 'equity' && (
            <div>
              {loading ? (
                <div className="text-center text-gray-400 py-8">Loading...</div>
              ) : equity.length === 0 ? (
                <div className="text-center text-gray-400 py-8">No equity data</div>
              ) : (
                <div className="space-y-4">
                  {/* Simple equity chart using bars */}
                  <div className="h-64 flex items-end gap-1">
                    {equity.slice(-50).map((point, idx) => {
                      const max = Math.max(...equity.map(e => e.equity));
                      const min = Math.min(...equity.map(e => e.equity));
                      const range = max - min || 1;
                      const height = ((point.equity - min) / range) * 100;
                      
                      return (
                        <div
                          key={idx}
                          className="flex-1 bg-blue-500 rounded-t"
                          style={{ height: `${Math.max(height, 5)}%` }}
                          title={`$${point.equity.toFixed(2)}`}
                        />
                      );
                    })}
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-gray-400 text-sm">Start</div>
                      <div className="text-white">${equity[0]?.equity?.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-gray-400 text-sm">Current</div>
                      <div className="text-white">${equity[equity.length - 1]?.equity?.toFixed(2)}</div>
                    </div>
                    <div>
                      <div className="text-gray-400 text-sm">Max Drawdown</div>
                      <div className="text-red-400">
                        {Math.max(...equity.map(e => e.drawdown || 0)).toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'logs' && (
            <div className="space-y-2 font-mono text-sm">
              {loading ? (
                <div className="text-center text-gray-400 py-8">Loading...</div>
              ) : logs.length === 0 ? (
                <div className="text-center text-gray-400 py-8">No logs</div>
              ) : (
                logs.map((log, idx) => {
                  const levelColors = {
                    info: 'text-blue-400',
                    warning: 'text-yellow-400',
                    error: 'text-red-400',
                    trade: 'text-green-400',
                  };
                  
                  return (
                    <div key={idx} className="bg-gray-700/50 rounded p-2">
                      <div className="flex items-center gap-2">
                        <span className="text-gray-500 text-xs">
                          {new Date(log.timestamp).toLocaleTimeString()}
                        </span>
                        <span className={`text-xs uppercase ${levelColors[log.level] || 'text-gray-400'}`}>
                          [{log.level}]
                        </span>
                        <span className="text-white">{log.message}</span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ============ BOTS TABLE ============

const BotsTable = ({ bots, onSelect, onAction, onDelete }) => {
  if (!bots || bots.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-8 text-center">
        <div className="text-gray-400 mb-4">No bots created yet</div>
        <div className="text-gray-500 text-sm">Create your first bot to start trading</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <table className="w-full">
        <thead>
          <tr className="text-left text-gray-400 text-sm border-b border-gray-700">
            <th className="px-4 py-3">Bot</th>
            <th className="px-4 py-3">Status</th>
            <th className="px-4 py-3">Symbols</th>
            <th className="px-4 py-3">Capital</th>
            <th className="px-4 py-3">PnL</th>
            <th className="px-4 py-3">Win Rate</th>
            <th className="px-4 py-3">Trades</th>
            <th className="px-4 py-3">Actions</th>
          </tr>
        </thead>
        <tbody>
          {bots.map((bot) => (
            <tr
              key={bot.id}
              className="border-b border-gray-700 hover:bg-gray-700/50 cursor-pointer"
              onClick={() => onSelect(bot)}
            >
              <td className="px-4 py-3">
                <div>
                  <div className="text-white font-medium">{bot.name}</div>
                  <div className="text-gray-500 text-xs">{bot.description || bot.id.slice(0, 8)}</div>
                </div>
              </td>
              <td className="px-4 py-3">
                <StatusBadge status={bot.status} />
              </td>
              <td className="px-4 py-3">
                <div className="flex flex-wrap gap-1">
                  {bot.symbols?.slice(0, 3).map(s => (
                    <span key={s} className="px-2 py-0.5 bg-gray-700 rounded text-xs text-gray-300">
                      {s}
                    </span>
                  ))}
                  {bot.symbols?.length > 3 && (
                    <span className="text-gray-500 text-xs">+{bot.symbols.length - 3}</span>
                  )}
                </div>
              </td>
              <td className="px-4 py-3 text-white">
                ${bot.current_capital?.toLocaleString() || '0'}
              </td>
              <td className="px-4 py-3">
                <PnlDisplay value={bot.total_pnl || 0} percent={bot.total_pnl_percent || 0} />
              </td>
              <td className="px-4 py-3 text-white">
                {bot.win_rate?.toFixed(1) || '0'}%
              </td>
              <td className="px-4 py-3 text-white">
                {bot.total_trades || 0}
              </td>
              <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                <div className="flex items-center gap-2">
                  {bot.status === 'stopped' && (
                    <button
                      onClick={() => onAction(bot.id, 'start')}
                      className="p-1.5 hover:bg-green-500/20 rounded text-green-400"
                      title="Start"
                    >
                      <PlayIcon />
                    </button>
                  )}
                  {bot.status === 'running' && (
                    <button
                      onClick={() => onAction(bot.id, 'stop')}
                      className="p-1.5 hover:bg-red-500/20 rounded text-red-400"
                      title="Stop"
                    >
                      <StopIcon />
                    </button>
                  )}
                  {bot.status === 'paused' && (
                    <button
                      onClick={() => onAction(bot.id, 'resume')}
                      className="p-1.5 hover:bg-green-500/20 rounded text-green-400"
                      title="Resume"
                    >
                      <PlayIcon />
                    </button>
                  )}
                  <button
                    onClick={() => onSelect(bot)}
                    className="p-1.5 hover:bg-blue-500/20 rounded text-blue-400"
                    title="Details"
                  >
                    <ChartIcon />
                  </button>
                  <button
                    onClick={() => onDelete(bot.id)}
                    className="p-1.5 hover:bg-red-500/20 rounded text-red-400"
                    title="Delete"
                    disabled={bot.status === 'running'}
                  >
                    <TrashIcon />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

// ============ MAIN PAGE ============

export default function Bots() {
  const [bots, setBots] = useState([]);
  const [summary, setSummary] = useState(null);
  const [runnerStatus, setRunnerStatus] = useState(null);
  const [presets, setPresets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedBot, setSelectedBot] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [botsRes, summaryRes, runnerRes, presetsRes] = await Promise.all([
        api.get('/api/bots/'),
        api.get('/api/bots/summary'),
        api.get('/api/bots/runner/status'),
        api.get('/api/bots/presets/strategies'),
      ]);

      setBots(botsRes.data.bots);
      setSummary(summaryRes.data);
      setRunnerStatus(runnerRes.data);
      setPresets(presetsRes.data.presets);
      setError(null);
    } catch (err) {
      console.error('Failed to load bots:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    
    // Auto-refresh every 10 seconds
    const interval = setInterval(loadData, 10000);
    return () => clearInterval(interval);
  }, [loadData]);

  const handleCreateBot = async (config) => {
    try {
      await api.post('/api/bots/', { config });
      await loadData();
    } catch (err) {
      console.error('Failed to create bot:', err);
      throw err;
    }
  };

  const handleAction = async (botId, action) => {
    try {
      await api.post(`/api/bots/${botId}/${action}`);
      await loadData();
      
      // Refresh selected bot if it's the one we acted on
      if (selectedBot?.id === botId) {
        const res = await api.get(`/api/bots/${botId}`);
        setSelectedBot(res.data.bot);
      }
    } catch (err) {
      console.error(`Failed to ${action} bot:`, err);
    }
  };

  const handleDelete = async (botId) => {
    if (!confirm('Are you sure you want to delete this bot?')) return;
    
    try {
      await api.delete(`/api/bots/${botId}`);
      await loadData();
      if (selectedBot?.id === botId) {
        setSelectedBot(null);
      }
    } catch (err) {
      console.error('Failed to delete bot:', err);
      alert(err.response?.data?.detail || 'Failed to delete bot');
    }
  };

  const handleToggleRunner = async () => {
    try {
      if (runnerStatus?.running) {
        await api.post('/api/bots/runner/stop');
      } else {
        await api.post('/api/bots/runner/start');
      }
      await loadData();
    } catch (err) {
      console.error('Failed to toggle runner:', err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">🤖 Trading Bots</h1>
          <p className="text-gray-400">Manage automated trading strategies</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleToggleRunner}
            className={`flex items-center gap-2 px-4 py-2 rounded ${
              runnerStatus?.running
                ? 'bg-red-600 hover:bg-red-500'
                : 'bg-green-600 hover:bg-green-500'
            } text-white`}
          >
            {runnerStatus?.running ? (
              <><StopIcon /> Stop Runner</>
            ) : (
              <><PlayIcon /> Start Runner</>
            )}
          </button>
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-white"
          >
            <RefreshIcon /> Refresh
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded text-white"
          >
            <PlusIcon /> New Bot
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 bg-red-500/20 border border-red-500/30 rounded-lg p-4 text-red-400">
          Error: {error}
        </div>
      )}

      {/* Summary */}
      <SummaryCards summary={summary} runnerStatus={runnerStatus} />

      {/* Bots Table */}
      {loading && bots.length === 0 ? (
        <div className="text-center text-gray-400 py-12">Loading bots...</div>
      ) : (
        <BotsTable
          bots={bots}
          onSelect={setSelectedBot}
          onAction={handleAction}
          onDelete={handleDelete}
        />
      )}

      {/* Create Modal */}
      <CreateBotModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onCreate={handleCreateBot}
        presets={presets}
      />

      {/* Detail Modal */}
      <BotDetailModal
        bot={selectedBot}
        onClose={() => setSelectedBot(null)}
        onAction={handleAction}
      />
    </div>
  );
}
