"""
Komas Trading System - Binance API Client
==========================================
Клиент для загрузки исторических данных с Binance.

Поддерживает:
- Binance Spot API
- Binance Futures API
- Retry logic с обработкой rate limits
- Параллельная загрузка
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
import aiohttp

from ..logger import get_logger

logger = get_logger("data.binance")


# ═══════════════════════════════════════════════════════════════════
# КОНСТАНТЫ
# ═══════════════════════════════════════════════════════════════════

BINANCE_SPOT_URL = "https://api.binance.com/api/v3/klines"
BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1/klines"

# Таймфреймы и их длительность в миллисекундах
TIMEFRAMES = {
    "1m": 60_000,
    "3m": 180_000,
    "5m": 300_000,
    "15m": 900_000,
    "30m": 1_800_000,
    "1h": 3_600_000,
    "2h": 7_200_000,
    "4h": 14_400_000,
    "6h": 21_600_000,
    "8h": 28_800_000,
    "12h": 43_200_000,
    "1d": 86_400_000,
}

# Начальные даты для загрузки
SPOT_START_DATE = datetime(2017, 8, 1)
FUTURES_START_DATE = datetime(2019, 9, 1)

# Топ-100 символов Binance Futures
BINANCE_SYMBOLS = [
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
    "PEPEUSDT", "FLOKIUSDT", "WIFUSDT", "ORDIUSDT", "JUPUSDT",
    "CKBUSDT", "ICXUSDT", "ONTUSDT", "VETUSDT", "ONEUSDT",
    "HOTUSDT", "ZENUSDT", "RVNUSDT", "DENTUSDT", "CELRUSDT",
    "MTLUSDT", "OGNUSDT", "NKNUSDT", "BANDUSDT", "KNCUSDT",
    "BALUSDT", "SKLUSDT", "CTSIUSDT", "LITUSDT", "UNFIUSDT",
]


# ═══════════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Candle:
    """Структура свечи"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class DownloadProgress:
    """Прогресс загрузки"""
    symbol: str
    timeframe: str
    percent: int
    current_date: str
    candles_count: int
    status: str  # downloading, completed, error, cancelled


# ═══════════════════════════════════════════════════════════════════
# BINANCE CLIENT
# ═══════════════════════════════════════════════════════════════════

class BinanceClient:
    """
    Асинхронный клиент для Binance API.
    
    Пример:
        client = BinanceClient()
        candles = await client.download_history("BTCUSDT", "1h")
    """
    
    def __init__(
        self,
        source: str = "spot",
        max_retries: int = 5,
        request_delay: float = 0.15,
        checkpoint_interval: int = 100
    ):
        """
        Args:
            source: "spot" или "futures"
            max_retries: Максимум попыток при ошибке
            request_delay: Задержка между запросами (сек)
            checkpoint_interval: Через сколько запросов сохранять
        """
        self.source = source
        self.max_retries = max_retries
        self.request_delay = request_delay
        self.checkpoint_interval = checkpoint_interval
        self.api_url = BINANCE_SPOT_URL if source == "spot" else BINANCE_FUTURES_URL
        
        self._cancelled = False
        self._session: Optional[aiohttp.ClientSession] = None
    
    @property
    def start_date(self) -> datetime:
        """Начальная дата для источника"""
        return SPOT_START_DATE if self.source == "spot" else FUTURES_START_DATE
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Получить или создать HTTP сессию"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=60)
            connector = aiohttp.TCPConnector(limit=5)
            self._session = aiohttp.ClientSession(
                timeout=timeout, 
                connector=connector
            )
        return self._session
    
    async def close(self):
        """Закрыть HTTP сессию"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def cancel(self):
        """Отменить текущую загрузку"""
        self._cancelled = True
        logger.info("Download cancelled by user")
    
    async def download_history(
        self,
        symbol: str,
        timeframe: str,
        start_ts: Optional[int] = None,
        end_ts: Optional[int] = None,
        on_progress: Optional[Callable[[DownloadProgress], None]] = None,
        on_checkpoint: Optional[Callable[[List[Candle]], None]] = None
    ) -> List[Candle]:
        """
        Загрузить историю свечей.
        
        Args:
            symbol: Торговая пара (BTCUSDT)
            timeframe: Таймфрейм (1h, 4h, 1d)
            start_ts: Начальная метка времени (мс)
            end_ts: Конечная метка времени (мс)
            on_progress: Callback для прогресса
            on_checkpoint: Callback для сохранения (каждые N запросов)
        
        Returns:
            Список свечей
        """
        self._cancelled = False
        interval_ms = TIMEFRAMES.get(timeframe, 3_600_000)
        
        # Определяем временной диапазон
        if start_ts is None:
            start_ts = int(self.start_date.timestamp() * 1000)
        if end_ts is None:
            end_ts = int(datetime.now().timestamp() * 1000)
        
        logger.info(f"Starting download: {symbol} {timeframe} ({self.source})")
        
        session = await self._get_session()
        all_candles: List[Candle] = []
        current_ts = start_ts
        request_count = 0
        
        while current_ts < end_ts and not self._cancelled:
            # Прогресс
            if on_progress:
                progress_pct = min(100, int((current_ts - start_ts) / (end_ts - start_ts) * 100))
                on_progress(DownloadProgress(
                    symbol=symbol,
                    timeframe=timeframe,
                    percent=progress_pct,
                    current_date=datetime.fromtimestamp(current_ts / 1000).strftime("%Y-%m-%d"),
                    candles_count=len(all_candles),
                    status="downloading"
                ))
            
            # Запрос с retry
            candles = await self._fetch_candles(session, symbol, timeframe, current_ts)
            
            if candles is None:
                # Критическая ошибка (invalid symbol и т.д.)
                break
            
            if not candles:
                # Нет данных - конец истории
                break
            
            all_candles.extend(candles)
            current_ts = int(candles[-1].timestamp.timestamp() * 1000) + interval_ms
            request_count += 1
            
            # Checkpoint
            if on_checkpoint and request_count % self.checkpoint_interval == 0:
                on_checkpoint(all_candles)
                logger.debug(f"{symbol}: Checkpoint at {len(all_candles):,} candles")
            
            # Rate limiting
            await asyncio.sleep(self.request_delay)
        
        if self._cancelled:
            logger.warning(f"{symbol}: Download cancelled")
        else:
            logger.info(f"{symbol}: Downloaded {len(all_candles):,} candles")
        
        return all_candles
    
    async def _fetch_candles(
        self,
        session: aiohttp.ClientSession,
        symbol: str,
        timeframe: str,
        start_ts: int
    ) -> Optional[List[Candle]]:
        """
        Загрузить батч свечей с retry logic.
        
        Returns:
            List[Candle] - успех
            [] - нет данных (конец истории)
            None - критическая ошибка (invalid symbol)
        """
        for retry in range(self.max_retries):
            try:
                async with session.get(
                    self.api_url,
                    params={
                        "symbol": symbol,
                        "interval": timeframe,
                        "startTime": start_ts,
                        "limit": 1000
                    }
                ) as response:
                    
                    # Rate limit
                    if response.status == 429:
                        wait = int(response.headers.get('Retry-After', 60))
                        logger.warning(f"Rate limited, waiting {wait}s...")
                        await asyncio.sleep(wait)
                        continue
                    
                    # IP ban
                    if response.status == 418:
                        logger.error("IP banned! Waiting 5 minutes...")
                        await asyncio.sleep(300)
                        continue
                    
                    # HTTP error
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} for {symbol}")
                        await asyncio.sleep(5)
                        continue
                    
                    data = await response.json()
                    
                    # API error
                    if isinstance(data, dict) and 'code' in data:
                        if data['code'] == -1121:  # Invalid symbol
                            logger.error(f"Invalid symbol: {symbol}")
                            return None
                        logger.warning(f"API error: {data}")
                        await asyncio.sleep(5)
                        continue
                    
                    # Нет данных
                    if not data:
                        return []
                    
                    # Парсим свечи
                    candles = []
                    for c in data:
                        candles.append(Candle(
                            timestamp=datetime.fromtimestamp(c[0] / 1000),
                            open=float(c[1]),
                            high=float(c[2]),
                            low=float(c[3]),
                            close=float(c[4]),
                            volume=float(c[5])
                        ))
                    
                    return candles
                    
            except asyncio.TimeoutError:
                logger.warning(f"Timeout for {symbol}, retry {retry + 1}")
                await asyncio.sleep(5)
            except aiohttp.ClientError as e:
                logger.warning(f"Connection error: {e}, retry {retry + 1}")
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await asyncio.sleep(5)
        
        logger.error(f"Failed to fetch {symbol} after {self.max_retries} retries")
        return []
    
    async def sync_latest(
        self,
        symbol: str,
        timeframe: str,
        last_ts: int
    ) -> List[Candle]:
        """
        Синхронизировать последние свечи (добавить новые).
        
        Args:
            symbol: Торговая пара
            timeframe: Таймфрейм
            last_ts: Timestamp последней имеющейся свечи (мс)
        
        Returns:
            Новые свечи
        """
        session = await self._get_session()
        
        try:
            async with session.get(
                self.api_url,
                params={
                    "symbol": symbol,
                    "interval": timeframe,
                    "startTime": last_ts,
                    "limit": 500
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status != 200:
                    return []
                
                data = await response.json()
                
                if not data or not isinstance(data, list):
                    return []
                
                candles = []
                for c in data:
                    candles.append(Candle(
                        timestamp=datetime.fromtimestamp(c[0] / 1000),
                        open=float(c[1]),
                        high=float(c[2]),
                        low=float(c[3]),
                        close=float(c[4]),
                        volume=float(c[5])
                    ))
                
                return candles
                
        except Exception as e:
            logger.error(f"Sync error for {symbol}: {e}")
            return []
