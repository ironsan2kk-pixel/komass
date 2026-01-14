import { useState, useEffect, useRef } from 'react';
import { Button, Card, Input, Select, Spinner, Alert, Badge } from '../components/ui';

const TIMEFRAMES = ['1m', '5m', '15m', '30m', '1h', '2h', '4h', '1d'];

// Binance Futures symbols (comprehensive list)
const ALL_SYMBOLS = [
  "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT",
  "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
  "MATICUSDT", "LTCUSDT", "ATOMUSDT", "UNIUSDT", "NEARUSDT",
  "APTUSDT", "ARBUSDT", "OPUSDT", "SUIUSDT", "SEIUSDT",
  "TRXUSDT", "TONUSDT", "SHIBUSDT", "BCHUSDT", "XLMUSDT",
  "HBARUSDT", "FILUSDT", "ETCUSDT", "INJUSDT", "IMXUSDT",
  "RNDRUSDT", "GRTUSDT", "FTMUSDT", "AAVEUSDT", "MKRUSDT",
  "ALGOUSDT", "FLOWUSDT", "XTZUSDT", "SANDUSDT", "MANAUSDT",
  "AXSUSDT", "GALAUSDT", "THETAUSDT", "EOSUSDT", "IOTAUSDT",
  "NEOUSDT", "KLAYUSDT", "QNTUSDT", "CHZUSDT", "APEUSDT",
  "ZILUSDT", "CRVUSDT", "LRCUSDT", "ENJUSDT", "BATUSDT",
  "COMPUSDT", "SNXUSDT", "1INCHUSDT", "YFIUSDT", "SUSHIUSDT",
  "ZECUSDT", "DASHUSDT", "WAVESUSDT", "KAVAUSDT", "ANKRUSDT",
  "ICPUSDT", "RUNEUSDT", "STXUSDT", "MINAUSDT", "GMXUSDT",
  "LDOUSDT", "CFXUSDT", "AGIXUSDT", "FETUSDT", "OCEANUSDT",
  "CKBUSDT", "ICXUSDT", "ONTUSDT", "VETUSDT", "ONEUSDT",
  "HOTUSDT", "ZENUSDT", "RVNUSDT", "DENTUSDT", "CELRUSDT",
  "MTLUSDT", "OGNUSDT", "NKNUSDT", "BANDUSDT", "KNCUSDT",
  "BALUSDT", "SKLUSDT", "CTSIUSDT", "LITUSDT", "UNFIUSDT",
  "DODOUSDT", "ALPHAUSDT", "TLMUSDT", "MASKUSDT", "LPTUSDT",
  "ENSUSDT", "PEOPLEUSDT", "SPELLUSDT", "JOEUSDT", "ACHUSDT",
  "DYDXUSDT", "WOOUSDT", "CELOUSDT", "ARUSDT", "JASMYUSDT",
  "DARUSDT", "ROSEUSDT", "DUSKUSDT", "API3USDT", "GMTUSDT",
  "ARPAUSDT", "BLURUSDT", "EDUUSDT", "IDUSDT", "RDNTUSDT",
  "MAGICUSDT", "HOOKUSDT", "HIGHUSDT", "ASTRUSDT", "PHBUSDT",
  "SSVUSDT", "STGUSDT", "BNXUSDT", "LEVERUSDT", "AMBUSDT",
  "PERPUSDT", "MAVUSDT", "WLDUSDT", "PENDLEUSDT", "ARKMUSDT",
  "XVSUSDT", "TRBUSDT", "COMBOUSDT", "NMRUSDT", "MDTUSDT",
  "XEMUSDT", "BIGTIMEUSDT", "BONDUSDT", "ORBSUSDT", "STPTUSDT",
  "GASUSDT", "POLYXUSDT", "POWRUSDT", "TIAUSDT", "BEAMXUSDT",
  "1000BONKUSDT", "1000SATSUSDT", "ACEUSDT", "NFPUSDT", "AIUSDT",
  "XAIUSDT", "MANTAUSDT", "ALTUSDT", "JUPUSDT", "ZETAUSDT",
  "RONINUSDT", "DYMUSDT", "OMUSDT", "PIXELUSDT", "STRKUSDT",
  "MAVIAUSDT", "GLMUSDT", "PORTALUSDT", "AXLUSDT", "WUSDT",
  "ENAUSDT", "SAGAUSDT", "REZUSDT", "BBUSDT", "NOTUSDT",
  "TURBOUSDT", "IOUSDT", "ZKUSDT", "LISTAUSDT", "RENDERUSDT",
  "PEPEUSDT", "FLOKIUSDT", "WIFUSDT", "BOMEUSDT", "MEWUSDT",
  "POPCATUSDT", "EIGENUSDT", "TAOUSDT", "ORDIUSDT", "CATIUSDT",
  "HMSTRUSDT", "SCRUSDT", "1MBABYDOGEUSDT", "GOATUSDT"
];

export default function Data() {
  const [selectedSymbols, setSelectedSymbols] = useState([]);
  const [symbolSearch, setSymbolSearch] = useState('');
  const [availableData, setAvailableData] = useState([]);
  const [loadingData, setLoadingData] = useState(true);
  const [downloadTimeframe, setDownloadTimeframe] = useState('1h');
  const [downloading, setDownloading] = useState(false);
  const [downloadProgress, setDownloadProgress] = useState(null);
  const [autoSync, setAutoSync] = useState(false);
  const [syncInterval, setSyncInterval] = useState(1);
  const [lastSync, setLastSync] = useState(null);
  const syncTimerRef = useRef(null);

  useEffect(() => {
    fetchAvailableData();
  }, []);

  useEffect(() => {
    if (autoSync) {
      syncTimerRef.current = setInterval(syncLatest, syncInterval * 60 * 1000);
      syncLatest();
    } else if (syncTimerRef.current) {
      clearInterval(syncTimerRef.current);
    }
    return () => syncTimerRef.current && clearInterval(syncTimerRef.current);
  }, [autoSync, syncInterval]);

  useEffect(() => {
    let interval;
    if (downloading) {
      interval = setInterval(fetchDownloadProgress, 2000);
    }
    return () => clearInterval(interval);
  }, [downloading]);

  const fetchAvailableData = async () => {
    try {
      const res = await fetch('/api/data/available');
      const data = await res.json();
      if (data.success) setAvailableData(data.files);
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoadingData(false);
    }
  };

  const fetchDownloadProgress = async () => {
    try {
      const res = await fetch('/api/data/download/progress');
      const data = await res.json();
      setDownloadProgress(data.progress);
      const tasks = Object.values(data.active || {});
      if (tasks.length === 0 || tasks.every(t => t === 'completed' || t === 'cancelled')) {
        setDownloading(false);
        fetchAvailableData();
      }
    } catch (err) {
      console.error('Failed to fetch progress:', err);
    }
  };

  const startDownload = async () => {
    if (selectedSymbols.length === 0) {
      alert('Выберите хотя бы одну пару');
      return;
    }
    setDownloading(true);
    try {
      await fetch('/api/data/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          symbols: selectedSymbols, 
          timeframe: downloadTimeframe 
          // source removed - Futures only
        }),
      });
    } catch (err) {
      console.error('Failed to start download:', err);
      setDownloading(false);
    }
  };

  const syncLatest = async () => {
    try {
      await fetch('/api/data/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ timeframe: downloadTimeframe }),
      });
      setLastSync(new Date().toLocaleTimeString());
      fetchAvailableData();
    } catch (err) {
      console.error('Sync failed:', err);
    }
  };

  const deleteFile = async (filename) => {
    if (!confirm(`Удалить ${filename}?`)) return;
    try {
      await fetch(`/api/data/file/${filename}`, { method: 'DELETE' });
      fetchAvailableData();
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  const continueDownload = async (symbol, timeframe) => {
    try {
      const res = await fetch(`/api/data/continue/${symbol}/${timeframe}`, {
        method: 'POST'
      });
      const data = await res.json();
      if (data.success) {
        setDownloading(true);
        alert(`Докачивание ${symbol} запущено`);
      }
    } catch (err) {
      console.error('Failed to continue download:', err);
    }
  };

  const continueAllOutdated = async () => {
    const oneWeekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
    const outdated = availableData.filter(f => f.end && new Date(f.end) < oneWeekAgo);
    
    if (outdated.length === 0) {
      alert('Все файлы актуальны!');
      return;
    }
    
    if (!confirm(`Докачать ${outdated.length} файлов?`)) return;
    
    setDownloading(true);
    for (const file of outdated) {
      try {
        await fetch(`/api/data/continue/${file.symbol}/${file.timeframe}`, { method: 'POST' });
        await new Promise(r => setTimeout(r, 500)); // Small delay between requests
      } catch (err) {
        console.error(`Failed to continue ${file.symbol}:`, err);
      }
    }
  };

  const toggleSymbol = (symbol) => {
    setSelectedSymbols(prev =>
      prev.includes(symbol) ? prev.filter(s => s !== symbol) : [...prev, symbol]
    );
  };

  const selectTop = (n) => setSelectedSymbols(ALL_SYMBOLS.slice(0, n));
  const selectAll = () => setSelectedSymbols([...ALL_SYMBOLS]);
  const clearSelection = () => setSelectedSymbols([]);

  const filteredSymbols = ALL_SYMBOLS.filter(s =>
    s.toLowerCase().includes(symbolSearch.toLowerCase())
  );

  const formatDate = (isoStr) => {
    if (!isoStr) return '—';
    return new Date(isoStr).toLocaleDateString('ru-RU', { day: '2-digit', month: '2-digit', year: '2-digit' });
  };

  const progress = downloadProgress ? Object.values(downloadProgress)[0] || {} : {};

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-100 dark:text-gray-100 light:text-gray-900">
          📊 Управление данными
        </h1>
        <Badge variant="warning" className="px-3 py-1 text-sm font-medium">
          🔥 Binance Futures Only
        </Badge>
      </div>

      {/* Paper Trading Warning */}
      <Alert variant="warning" className="mb-6">
        <div className="flex items-start gap-2">
          <span className="text-lg">📊</span>
          <div>
            <p className="font-medium">Данные для бэктестинга (Paper Trading)</p>
            <p className="text-sm mt-1 opacity-90">
              Исторические данные используются ТОЛЬКО для бэктестинга стратегий.
              Загрузка данных НЕ предназначена для реальной торговли.
              Все тесты выполняются на исторических данных Binance Futures.
            </p>
          </div>
        </div>
      </Alert>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left */}
        <div className="space-y-4">
          {/* Download Settings */}
          <Card>
            <Card.Header>
              <h3 className="text-lg font-semibold">⬇️ Загрузка с Binance Futures</h3>
            </Card.Header>
            <Card.Body className="space-y-4">
              <Select
                label="Таймфрейм"
                value={downloadTimeframe}
                onChange={(e) => setDownloadTimeframe(e.target.value)}
              >
                {TIMEFRAMES.map((tf) => (
                  <option key={tf} value={tf}>{tf}</option>
                ))}
              </Select>

            <div className="flex flex-wrap gap-2">
              <Button variant="primary" size="sm" onClick={() => selectTop(10)}>Топ 10</Button>
              <Button variant="primary" size="sm" onClick={() => selectTop(20)}>Топ 20</Button>
              <Button variant="primary" size="sm" onClick={() => selectTop(50)}>Топ 50</Button>
              <Button variant="success" size="sm" onClick={selectAll}>Все</Button>
              <Button variant="secondary" size="sm" onClick={clearSelection}>Очистить</Button>
            </div>

            <div className="text-gray-400 text-sm">
              Выбрано: <span className="text-white font-bold">{selectedSymbols.length}</span> пар
            </div>

            <Button
              variant="primary"
              className="w-full bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600"
              onClick={startDownload}
              disabled={downloading || selectedSymbols.length === 0}
              loading={downloading}
            >
              {downloading ? (
                `${progress.current} ${progress.current_progress}`
              ) : (
                `🚀 Загрузить ${selectedSymbols.length} пар (Futures)`
              )}
            </Button>

            {downloading && (
              <div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-orange-500 h-2 rounded-full transition-all"
                    style={{ width: `${progress.total ? (progress.completed / progress.total * 100) : 0}%` }}
                  />
                </div>
                <div className="text-gray-500 text-xs mt-1">{progress.completed || 0} / {progress.total || 0}</div>
              </div>
            )}
            </Card.Body>
          </Card>

          {/* Auto-Sync */}
          <Card>
            <Card.Header className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">🔄 Автоподкачка</h3>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" checked={autoSync} onChange={(e) => setAutoSync(e.target.checked)} className="w-5 h-5 rounded" />
                <span className={autoSync ? 'text-success-400' : 'text-gray-400'}>{autoSync ? 'Вкл' : 'Выкл'}</span>
              </label>
            </Card.Header>
            <Card.Body>
              <div className="flex items-center gap-3">
                <Select
                  value={syncInterval}
                  onChange={(e) => setSyncInterval(parseInt(e.target.value))}
                  className="flex-shrink-0"
                >
                  <option value={1}>1 мин</option>
                  <option value={5}>5 мин</option>
                  <option value={15}>15 мин</option>
                </Select>
                <Button variant="primary" size="sm" onClick={syncLatest}>
                  Синхр.
                </Button>
                {lastSync && <span className="text-gray-500 text-sm">{lastSync}</span>}
              </div>
            </Card.Body>
          </Card>

          {/* Symbols */}
          <Card>
            <Card.Header>
              <h3 className="text-lg font-semibold">🔍 Выбор пар ({ALL_SYMBOLS.length})</h3>
            </Card.Header>
            <Card.Body className="space-y-3">
              <Input
                type="text"
                value={symbolSearch}
                onChange={(e) => setSymbolSearch(e.target.value)}
                placeholder="Поиск... BTC, ETH, SOL"
              />
              <div className="h-72 overflow-y-auto space-y-1">
              {filteredSymbols.map((symbol) => (
                <label
                  key={symbol}
                  className={`flex items-center gap-3 p-2 rounded cursor-pointer ${
                    selectedSymbols.includes(symbol)
                      ? 'bg-orange-600/30 border border-orange-500/50'
                      : 'bg-gray-700/30 hover:bg-gray-700/50'
                  }`}
                >
                  <input
                    type="checkbox"
                    checked={selectedSymbols.includes(symbol)}
                    onChange={() => toggleSymbol(symbol)}
                    className="w-4 h-4"
                  />
                  <span className="text-white font-mono text-sm">{symbol}</span>
                </label>
              ))}
              </div>
              <div className="text-gray-500 text-sm">Найдено: {filteredSymbols.length}</div>
            </Card.Body>
          </Card>
        </div>

        {/* Right */}
        <div className="space-y-4">
          <Card>
            <Card.Header className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">💾 Загруженные ({availableData.length})</h3>
              <div className="flex gap-2">
                <Button
                  variant="success"
                  size="sm"
                  onClick={continueAllOutdated}
                  title="Докачать все неполные"
                >
                  ⬇️ Докачать всё
                </Button>
                <Button variant="secondary" size="sm" onClick={fetchAvailableData}>
                  🔄
                </Button>
              </div>
            </Card.Header>
            <Card.Body>

            {loadingData ? (
              <div className="text-gray-400 text-center py-8">Загрузка...</div>
            ) : availableData.length === 0 ? (
              <div className="text-gray-400 text-center py-12">
                <div className="text-5xl mb-3">📂</div>
                <div>Нет загруженных данных</div>
              </div>
            ) : (
              <div className="space-y-2 max-h-[450px] overflow-y-auto">
                {availableData.map((file) => {
                  const isOutdated = file.end && new Date(file.end) < new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
                  return (
                  <div key={file.filename} className={`bg-gray-700/50 rounded-lg p-3 flex items-center justify-between ${isOutdated ? 'border border-yellow-500/50' : ''}`}>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-white font-mono font-bold">{file.symbol}</span>
                        <span className="text-purple-400 text-sm">{file.timeframe}</span>
                        <span className="text-gray-500 text-xs">{file.size_mb} MB</span>
                        {isOutdated && <span className="text-yellow-400 text-xs">⚠️ Неполные</span>}
                      </div>
                      <div className="text-gray-500 text-xs mt-1">
                        {formatDate(file.start)} — {formatDate(file.end)} ({file.rows?.toLocaleString()})
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      {isOutdated && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => continueDownload(file.symbol, file.timeframe)}
                          className="text-success-400 hover:bg-success-600/20"
                          title="Докачать до текущей даты"
                        >
                          ⬇️
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteFile(file.filename)}
                        className="text-danger-400 hover:bg-danger-600/20"
                      >
                        🗑️
                      </Button>
                    </div>
                  </div>
                )})}
              </div>
            )}

            {availableData.length > 0 && (
              <div className="pt-4 border-t border-dark-700 dark:border-dark-700 light:border-gray-200 flex justify-between text-sm">
                <span className="text-gray-400">Всего: {availableData.reduce((s, f) => s + (f.size_mb || 0), 0).toFixed(1)} MB</span>
              </div>
            )}
            </Card.Body>
          </Card>

          <Alert variant="warning" className="text-sm">
            <div className="font-medium mb-2">🔥 Binance Futures Only</div>
            <ul className="space-y-1 text-xs opacity-90">
              <li>• Данные с Binance Futures с сентября 2019</li>
              <li>• Только фьючерсные USDT-M пары</li>
              <li>• Автоподкачка добавляет только новые свечи</li>
              <li>• ~5 MB на пару для 1h за всю историю</li>
              <li>• Spot API удалён в версии 4.0</li>
            </ul>
          </Alert>
        </div>
      </div>
    </div>
  );
}
