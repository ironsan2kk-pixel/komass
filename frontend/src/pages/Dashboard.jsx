/**
 * Dashboard.jsx - Live Overview
 *
 * Features:
 * - Live prices via SSE
 * - Recent signals
 * - Active bots status
 */
import { useState, useEffect, useRef } from 'react';

const API_BASE = 'http://localhost:8000';

// Price card component
function PriceCard({ symbol, price, change, loading }) {
  const isPositive = change >= 0;

  return (
    <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border)]">
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-lg font-bold text-[var(--text-primary)]">{symbol}</h3>
          <p className="text-2xl font-mono text-[var(--text-primary)]">
            {loading ? '...' : `$${price?.toLocaleString()}`}
          </p>
        </div>
        <span className={`text-sm px-2 py-1 rounded ${isPositive ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>
          {isPositive ? '+' : ''}{change?.toFixed(2)}%
        </span>
      </div>
    </div>
  );
}

// Bot status card
function BotCard({ bot }) {
  const statusColors = {
    running: 'bg-green-500',
    stopped: 'bg-gray-500',
    error: 'bg-red-500'
  };

  return (
    <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border)]">
      <div className="flex justify-between items-center">
        <div>
          <h4 className="font-medium text-[var(--text-primary)]">{bot.name}</h4>
          <p className="text-sm text-[var(--text-secondary)]">
            {bot.symbols?.length || 0} pairs
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${statusColors[bot.status] || statusColors.stopped}`} />
          <span className="text-sm text-[var(--text-secondary)] capitalize">{bot.status}</span>
        </div>
      </div>
      {bot.pnl !== undefined && (
        <p className={`text-sm mt-2 ${bot.pnl >= 0 ? 'text-green-400' : 'text-red-400'}`}>
          PnL: {bot.pnl >= 0 ? '+' : ''}{bot.pnl.toFixed(2)}%
        </p>
      )}
    </div>
  );
}

// Signal row
function SignalRow({ signal }) {
  const typeColors = {
    LONG: 'text-green-400',
    SHORT: 'text-red-400',
    CLOSE: 'text-yellow-400'
  };

  return (
    <div className="flex justify-between items-center py-2 border-b border-[var(--border)] last:border-0">
      <div className="flex items-center gap-3">
        <span className={`font-medium ${typeColors[signal.type] || 'text-[var(--text-primary)]'}`}>
          {signal.type}
        </span>
        <span className="text-[var(--text-primary)]">{signal.symbol}</span>
      </div>
      <div className="text-right">
        <p className="text-sm text-[var(--text-primary)]">${signal.price}</p>
        <p className="text-xs text-[var(--text-secondary)]">{signal.time}</p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [prices, setPrices] = useState({});
  const [bots, setBots] = useState([]);
  const [signals, setSignals] = useState([]);
  const [wsStatus, setWsStatus] = useState('disconnected');
  const [loading, setLoading] = useState(true);
  const eventSourceRef = useRef(null);

  const defaultSymbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT'];

  // Fetch bots
  useEffect(() => {
    async function fetchBots() {
      try {
        const res = await fetch(`${API_BASE}/api/bots`);
        if (res.ok) {
          const data = await res.json();
          setBots(data.bots || []);
        }
      } catch (err) {
        console.error('Failed to fetch bots:', err);
      }
    }

    fetchBots();
    const interval = setInterval(fetchBots, 30000);
    return () => clearInterval(interval);
  }, []);

  // Fetch signals
  useEffect(() => {
    async function fetchSignals() {
      try {
        const res = await fetch(`${API_BASE}/api/signals?limit=5`);
        if (res.ok) {
          const data = await res.json();
          setSignals(data.signals || []);
        }
      } catch (err) {
        console.error('Failed to fetch signals:', err);
      }
    }

    fetchSignals();
    const interval = setInterval(fetchSignals, 10000);
    return () => clearInterval(interval);
  }, []);

  // SSE for live prices
  useEffect(() => {
    async function startPriceStream() {
      try {
        // Start quick prices
        await fetch(`${API_BASE}/api/ws/quick/start-prices?symbols=${defaultSymbols.join(',')}`, {
          method: 'POST'
        });

        setWsStatus('connecting');

        // Connect to SSE
        const es = new EventSource(`${API_BASE}/api/ws/sse/prices?symbols=${defaultSymbols.join(',')}`);
        eventSourceRef.current = es;

        es.onopen = () => {
          setWsStatus('connected');
          setLoading(false);
        };

        es.onmessage = (event) => {
          try {
            const msg = JSON.parse(event.data);
            if (msg.data && msg.data.symbol) {
              setPrices(prev => ({
                ...prev,
                [msg.data.symbol]: {
                  price: parseFloat(msg.data.price || msg.data.close || 0),
                  change: parseFloat(msg.data.price_change_percent || 0)
                }
              }));
            }
          } catch (e) {
            // Ignore parse errors
          }
        };

        es.onerror = () => {
          setWsStatus('error');
        };

      } catch (err) {
        console.error('Failed to start price stream:', err);
        setWsStatus('error');
        setLoading(false);
      }
    }

    startPriceStream();

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const statusColors = {
    connected: 'bg-green-500',
    connecting: 'bg-yellow-500',
    disconnected: 'bg-gray-500',
    error: 'bg-red-500'
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Dashboard</h1>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${statusColors[wsStatus]}`} />
          <span className="text-sm text-[var(--text-secondary)] capitalize">{wsStatus}</span>
        </div>
      </div>

      {/* Live Prices */}
      <section>
        <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-3">Live Prices</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {defaultSymbols.map(symbol => (
            <PriceCard
              key={symbol}
              symbol={symbol}
              price={prices[symbol]?.price}
              change={prices[symbol]?.change || 0}
              loading={loading}
            />
          ))}
        </div>
      </section>

      {/* Bots & Signals */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Active Bots */}
        <section>
          <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-3">
            Active Bots ({bots.filter(b => b.status === 'running').length})
          </h2>
          <div className="space-y-3">
            {bots.length === 0 ? (
              <p className="text-[var(--text-secondary)] text-sm">No bots configured</p>
            ) : (
              bots.slice(0, 5).map(bot => (
                <BotCard key={bot.id} bot={bot} />
              ))
            )}
          </div>
        </section>

        {/* Recent Signals */}
        <section>
          <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-3">Recent Signals</h2>
          <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border)]">
            {signals.length === 0 ? (
              <p className="text-[var(--text-secondary)] text-sm">No recent signals</p>
            ) : (
              signals.map((signal, i) => (
                <SignalRow key={i} signal={signal} />
              ))
            )}
          </div>
        </section>
      </div>

      {/* Quick Stats */}
      <section className="grid grid-cols-3 gap-4">
        <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border)] text-center">
          <p className="text-2xl font-bold text-[var(--text-primary)]">{bots.length}</p>
          <p className="text-sm text-[var(--text-secondary)]">Total Bots</p>
        </div>
        <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border)] text-center">
          <p className="text-2xl font-bold text-[var(--text-primary)]">{signals.length}</p>
          <p className="text-sm text-[var(--text-secondary)]">Signals Today</p>
        </div>
        <div className="bg-[var(--bg-secondary)] rounded-lg p-4 border border-[var(--border)] text-center">
          <p className="text-2xl font-bold text-green-400">
            {bots.filter(b => b.status === 'running').length}
          </p>
          <p className="text-sm text-[var(--text-secondary)]">Running</p>
        </div>
      </section>
    </div>
  );
}
