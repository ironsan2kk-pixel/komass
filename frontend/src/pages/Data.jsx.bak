/**
 * Data Page v3.5.2
 * =================
 * Управление рыночными данными
 * 
 * Features:
 * - Загрузка списка символов с backend (80+ пар)
 * - Фильтр Top 20/50/100/All
 * - Поиск по символу
 * - Выбор Spot/Futures
 * - Batch загрузка нескольких пар
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { dataApi } from '../api';
import toast from 'react-hot-toast';
import { Download, Trash2, RefreshCw, Search, Filter } from 'lucide-react';

const TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d'];
const TOP_FILTERS = [
  { label: 'Top 20', value: 20 },
  { label: 'Top 50', value: 50 },
  { label: 'Top 100', value: 100 },
  { label: 'Все', value: 999 },
];

export default function Data() {
  // Symbols from API
  const [allSymbols, setAllSymbols] = useState([]);
  const [topFilter, setTopFilter] = useState(20);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Data files
  const [dataFiles, setDataFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Download settings
  const [selectedSymbols, setSelectedSymbols] = useState([]);
  const [selectedTimeframe, setSelectedTimeframe] = useState('1h');
  const [source, setSource] = useState('spot');
  const [downloading, setDownloading] = useState(false);

  // Filtered symbols based on top filter and search
  const filteredSymbols = useMemo(() => {
    let result = allSymbols.slice(0, topFilter);
    
    if (searchQuery) {
      const query = searchQuery.toUpperCase();
      result = allSymbols.filter(s => 
        s.symbol.includes(query) || s.baseAsset.includes(query)
      );
    }
    
    return result;
  }, [allSymbols, topFilter, searchQuery]);

  // Load symbols from backend
  const loadSymbols = useCallback(async () => {
    try {
      const res = await dataApi.getSymbols();
      setAllSymbols(res.data?.symbols || []);
    } catch (err) {
      console.error('Failed to load symbols:', err);
      toast.error('Ошибка загрузки списка символов');
    }
  }, []);

  // Load available data files
  const loadDataFiles = useCallback(async () => {
    setLoading(true);
    try {
      const res = await dataApi.getAvailable();
      setDataFiles(res.data?.files || []);
    } catch (err) {
      console.error('Failed to load data files:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSymbols();
    loadDataFiles();
  }, [loadSymbols, loadDataFiles]);

  // Toggle symbol selection
  const toggleSymbol = (symbol) => {
    setSelectedSymbols(prev => 
      prev.includes(symbol) 
        ? prev.filter(s => s !== symbol)
        : [...prev, symbol]
    );
  };

  // Select all visible symbols
  const selectAll = () => {
    const visibleSymbols = filteredSymbols.map(s => s.symbol);
    setSelectedSymbols(visibleSymbols);
  };

  // Clear selection
  const clearSelection = () => {
    setSelectedSymbols([]);
  };

  // Download selected symbols
  const downloadData = async () => {
    if (selectedSymbols.length === 0) {
      toast.error('Выберите хотя бы один символ');
      return;
    }

    setDownloading(true);
    try {
      const res = await dataApi.download({
        symbols: selectedSymbols,
        timeframe: selectedTimeframe,
        source: source,
      });
      
      if (res.data?.success) {
        toast.success(`Загрузка ${selectedSymbols.length} пар запущена`);
        setSelectedSymbols([]);
      }
      
      // Poll for completion
      setTimeout(() => loadDataFiles(), 5000);
    } catch (err) {
      console.error('Download failed:', err);
      toast.error('Ошибка: ' + (err.response?.data?.detail || err.message));
    } finally {
      setDownloading(false);
    }
  };

  // Delete data file
  const deleteFile = async (item) => {
    const filename = item.filename;
    if (!confirm(`Удалить ${filename}?`)) return;
    
    try {
      await dataApi.deleteFile(filename);
      toast.success(`Удалено: ${filename}`);
      await loadDataFiles();
    } catch (err) {
      console.error('Delete failed:', err);
      toast.error('Ошибка удаления');
    }
  };

  // Check if symbol is already downloaded
  const isDownloaded = (symbol) => {
    return dataFiles.some(f => 
      f.symbol === symbol && f.timeframe === selectedTimeframe
    );
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">📁 Управление данными</h1>
        <button
          onClick={() => { loadSymbols(); loadDataFiles(); }}
          className="flex items-center gap-2 px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm"
        >
          <RefreshCw className="h-4 w-4" />
          Обновить
        </button>
      </div>

      {/* Download Section */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
        <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
          <Download className="h-5 w-5 text-blue-400" />
          Загрузить данные с Binance
        </h2>
        
        {/* Filters Row */}
        <div className="flex flex-wrap items-center gap-4 mb-4">
          {/* Top Filter */}
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-gray-400" />
            <div className="flex bg-gray-700 rounded-lg p-1">
              {TOP_FILTERS.map(f => (
                <button
                  key={f.value}
                  onClick={() => setTopFilter(f.value)}
                  className={`px-3 py-1 rounded text-sm transition-colors ${
                    topFilter === f.value 
                      ? 'bg-blue-600 text-white' 
                      : 'text-gray-400 hover:text-white'
                  }`}
                >
                  {f.label}
                </button>
              ))}
            </div>
          </div>

          {/* Search */}
          <div className="relative flex-1 max-w-xs">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Поиск символа..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-gray-700 pl-10 pr-4 py-2 rounded-lg text-sm"
            />
          </div>

          {/* Timeframe */}
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
            className="bg-gray-700 px-3 py-2 rounded-lg text-sm"
          >
            {TIMEFRAMES.map(tf => (
              <option key={tf} value={tf}>{tf}</option>
            ))}
          </select>

          {/* Source */}
          <select
            value={source}
            onChange={(e) => setSource(e.target.value)}
            className="bg-gray-700 px-3 py-2 rounded-lg text-sm"
          >
            <option value="spot">Spot</option>
            <option value="futures">Futures</option>
          </select>
        </div>

        {/* Selection Actions */}
        <div className="flex items-center gap-4 mb-4">
          <button
            onClick={selectAll}
            className="text-sm text-blue-400 hover:text-blue-300"
          >
            Выбрать все ({filteredSymbols.length})
          </button>
          <button
            onClick={clearSelection}
            className="text-sm text-gray-400 hover:text-gray-300"
          >
            Сбросить
          </button>
          <span className="text-sm text-gray-500">
            Выбрано: <span className="text-white font-medium">{selectedSymbols.length}</span>
          </span>
        </div>

        {/* Symbols Grid */}
        <div className="grid grid-cols-6 sm:grid-cols-8 md:grid-cols-10 lg:grid-cols-12 gap-2 mb-4 max-h-64 overflow-y-auto">
          {filteredSymbols.map(s => {
            const isSelected = selectedSymbols.includes(s.symbol);
            const downloaded = isDownloaded(s.symbol);
            
            return (
              <button
                key={s.symbol}
                onClick={() => toggleSymbol(s.symbol)}
                className={`px-2 py-1.5 rounded text-xs font-medium transition-all ${
                  isSelected 
                    ? 'bg-blue-600 text-white ring-2 ring-blue-400' 
                    : downloaded
                      ? 'bg-green-900/30 text-green-400 border border-green-700'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                }`}
                title={downloaded ? `${s.symbol} уже загружен` : s.symbol}
              >
                {s.baseAsset}
                {downloaded && ' ✓'}
              </button>
            );
          })}
        </div>

        {/* Download Button */}
        <button
          onClick={downloadData}
          disabled={downloading || selectedSymbols.length === 0}
          className="w-full bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 
                     px-4 py-3 rounded-lg font-medium flex items-center justify-center gap-2"
        >
          {downloading ? (
            <>
              <span className="animate-spin">⏳</span>
              Загрузка...
            </>
          ) : (
            <>
              <Download className="h-5 w-5" />
              Загрузить {selectedSymbols.length > 0 ? `(${selectedSymbols.length} пар)` : ''}
            </>
          )}
        </button>

        <p className="mt-3 text-xs text-gray-500">
          Данные загружаются за последний год. Зелёные — уже загружены для выбранного таймфрейма.
        </p>
      </div>

      {/* Downloaded Data Table */}
      <div className="bg-gray-800 border border-gray-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold">📊 Загруженные данные</h2>
          <span className="text-sm text-gray-500">{dataFiles.length} файлов</span>
        </div>

        {loading ? (
          <div className="text-center py-8 text-gray-500">
            <span className="animate-spin inline-block">⏳</span> Загрузка...
          </div>
        ) : dataFiles.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>Нет загруженных данных</p>
            <p className="text-xs mt-2">Выберите символы выше и нажмите "Загрузить"</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-400 border-b border-gray-700">
                  <th className="text-left py-3">Символ</th>
                  <th className="text-left py-3">TF</th>
                  <th className="text-right py-3">Свечей</th>
                  <th className="text-left py-3">Период</th>
                  <th className="text-right py-3">Размер</th>
                  <th className="text-center py-3 w-16"></th>
                </tr>
              </thead>
              <tbody>
                {dataFiles.map((d, i) => (
                  <tr key={i} className="border-b border-gray-700/50 hover:bg-gray-700/30">
                    <td className="py-2.5 font-medium">{d.symbol}</td>
                    <td className="py-2.5 text-gray-400">{d.timeframe}</td>
                    <td className="py-2.5 text-right text-blue-400">
                      {(d.rows || 0).toLocaleString()}
                    </td>
                    <td className="py-2.5 text-xs text-gray-500">
                      {d.start?.split('T')[0] || '—'} → {d.end?.split('T')[0] || '—'}
                    </td>
                    <td className="py-2.5 text-right text-gray-400">
                      {d.size_mb?.toFixed(1)} MB
                    </td>
                    <td className="py-2.5 text-center">
                      <button
                        onClick={() => deleteFile(d)}
                        className="text-red-400 hover:text-red-300 p-1"
                        title="Удалить"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="bg-gray-800/50 border border-gray-700 rounded-xl p-4 text-sm text-gray-400">
        <p><strong>💡 Рекомендации:</strong></p>
        <ul className="list-disc list-inside mt-2 space-y-1">
          <li>Для бэктеста нужно минимум 3000 свечей (3-4 месяца на 1h)</li>
          <li>Top 20 — самые ликвидные пары с наименьшим спредом</li>
          <li>Futures данные могут отличаться от Spot</li>
        </ul>
      </div>
    </div>
  );
}
