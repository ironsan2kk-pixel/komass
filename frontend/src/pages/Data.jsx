/**
 * Data Page
 * =========
 * Управление рыночными данными
 */
import { useState, useEffect, useCallback } from 'react';
import { dataApi } from '../api';

const TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d'];

export default function Data() {
  const [symbols, setSymbols] = useState([]);
  const [dataStatus, setDataStatus] = useState([]);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(null);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [limit, setLimit] = useState(5000);

  // Load data status
  const loadStatus = useCallback(async () => {
    setLoading(true);
    try {
      const [symbolsRes, statusRes] = await Promise.all([
        dataApi.getSymbols(),
        dataApi.getStatus(),
      ]);
      setSymbols(symbolsRes.data?.symbols || []);
      setDataStatus(statusRes.data?.data || []);
    } catch (err) {
      console.error('Failed to load data status:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  // Download data
  const downloadData = async () => {
    setDownloading(`${selectedSymbol}_${selectedTimeframe}`);
    try {
      await dataApi.download({
        symbol: selectedSymbol,
        timeframe: selectedTimeframe,
        limit,
      });
      await loadStatus();
    } catch (err) {
      console.error('Download failed:', err);
    } finally {
      setDownloading(null);
    }
  };

  // Delete data
  const deleteData = async (symbol, timeframe) => {
    if (!confirm(`Удалить данные ${symbol} ${timeframe}?`)) return;
    try {
      await dataApi.delete(symbol, timeframe);
      await loadStatus();
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold">📁 Управление данными</h1>

      {/* Download Section */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
        <h2 className="text-lg font-bold mb-4">⬇️ Загрузить данные</h2>
        
        <div className="grid grid-cols-4 gap-4">
          <div>
            <label className="text-sm text-gray-400 block mb-1">Символ</label>
            <select
              value={selectedSymbol}
              onChange={(e) => setSelectedSymbol(e.target.value)}
              className="w-full bg-gray-700 px-3 py-2 rounded-lg"
            >
              {['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'SOLUSDT', 'ADAUSDT', 'DOGEUSDT'].map(s => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="text-sm text-gray-400 block mb-1">Таймфрейм</label>
            <select
              value={selectedTimeframe}
              onChange={(e) => setSelectedTimeframe(e.target.value)}
              className="w-full bg-gray-700 px-3 py-2 rounded-lg"
            >
              {TIMEFRAMES.map(tf => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="text-sm text-gray-400 block mb-1">Лимит свечей</label>
            <input
              type="number"
              value={limit}
              onChange={(e) => setLimit(parseInt(e.target.value))}
              min={100}
              max={10000}
              className="w-full bg-gray-700 px-3 py-2 rounded-lg"
            />
          </div>
          
          <div className="flex items-end">
            <button
              onClick={downloadData}
              disabled={downloading}
              className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 px-4 py-2 rounded-lg font-medium"
            >
              {downloading ? '⏳ Загрузка...' : '⬇️ Загрузить'}
            </button>
          </div>
        </div>
      </div>

      {/* Data Status Table */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold">📊 Загруженные данные</h2>
          <button
            onClick={loadStatus}
            disabled={loading}
            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm"
          >
            🔄 Обновить
          </button>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">
            <span className="animate-spin inline-block">⏳</span> Загрузка...
          </div>
        ) : dataStatus.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            Нет загруженных данных
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-gray-700">
                  <th className="text-left py-3">Символ</th>
                  <th className="text-left py-3">Таймфрейм</th>
                  <th className="text-right py-3">Свечей</th>
                  <th className="text-left py-3">Период</th>
                  <th className="text-left py-3">Обновлено</th>
                  <th className="text-right py-3">Размер</th>
                  <th className="text-center py-3">Действия</th>
                </tr>
              </thead>
              <tbody>
                {dataStatus.map((d, i) => (
                  <tr key={i} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                    <td className="py-3 font-medium">{d.symbol}</td>
                    <td className="py-3">{d.timeframe}</td>
                    <td className="py-3 text-right text-blue-400">{d.candles?.toLocaleString()}</td>
                    <td className="py-3 text-xs text-gray-400">
                      {d.start_date} — {d.end_date}
                    </td>
                    <td className="py-3 text-xs text-gray-400">{d.updated_at}</td>
                    <td className="py-3 text-right text-gray-400">{d.size_mb?.toFixed(2)} MB</td>
                    <td className="py-3 text-center">
                      <button
                        onClick={() => deleteData(d.symbol, d.timeframe)}
                        className="text-red-400 hover:text-red-300"
                      >
                        🗑️
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
