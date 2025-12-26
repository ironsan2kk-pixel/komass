"""
Komas Trading Server - Binance WebSocket Client
================================================
Real-time data streaming from Binance WebSocket API

Features:
- Multiple stream subscriptions (klines, trades, ticker, book_ticker)
- Auto-reconnect with exponential backoff
- Callbacks for data processing
- Connection state management
- Thread-safe message handling
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Callable, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import websockets
from websockets.exceptions import ConnectionClosed, ConnectionClosedError

logger = logging.getLogger(__name__)


class StreamType(str, Enum):
    """Supported Binance stream types"""
    KLINE = "kline"
    TRADE = "trade"
    AGG_TRADE = "aggTrade"
    TICKER = "ticker"
    MINI_TICKER = "miniTicker"
    BOOK_TICKER = "bookTicker"
    DEPTH = "depth"


class ConnectionState(str, Enum):
    """WebSocket connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    CLOSING = "closing"


@dataclass
class StreamSubscription:
    """Represents a stream subscription"""
    stream_name: str
    stream_type: StreamType
    symbol: str
    interval: Optional[str] = None  # For klines
    callbacks: List[Callable] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def stream_id(self) -> str:
        """Unique identifier for the stream"""
        if self.interval:
            return f"{self.symbol.lower()}@{self.stream_type.value}_{self.interval}"
        return f"{self.symbol.lower()}@{self.stream_type.value}"


class BinanceWebSocket:
    """
    Binance WebSocket client with auto-reconnect
    
    Usage:
        ws = BinanceWebSocket()
        
        async def on_kline(data):
            print(f"Kline: {data}")
        
        await ws.connect()
        await ws.subscribe_kline("BTCUSDT", "1m", on_kline)
        await ws.run_forever()
    """
    
    # Binance WebSocket endpoints
    SPOT_WS_URL = "wss://stream.binance.com:9443/ws"
    SPOT_STREAM_URL = "wss://stream.binance.com:9443/stream"
    FUTURES_WS_URL = "wss://fstream.binance.com/ws"
    FUTURES_STREAM_URL = "wss://fstream.binance.com/stream"
    
    def __init__(
        self,
        use_futures: bool = False,
        max_reconnect_attempts: int = 10,
        reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 60.0,
        ping_interval: float = 30.0,
        ping_timeout: float = 10.0
    ):
        """
        Initialize WebSocket client
        
        Args:
            use_futures: Use Futures API instead of Spot
            max_reconnect_attempts: Max reconnection attempts (0 = infinite)
            reconnect_delay: Initial delay between reconnects (seconds)
            max_reconnect_delay: Maximum delay between reconnects
            ping_interval: Interval for ping/pong heartbeat
            ping_timeout: Timeout for pong response
        """
        self.use_futures = use_futures
        self.max_reconnect_attempts = max_reconnect_attempts
        self.reconnect_delay = reconnect_delay
        self.max_reconnect_delay = max_reconnect_delay
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        
        # State
        self._state = ConnectionState.DISCONNECTED
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._subscriptions: Dict[str, StreamSubscription] = {}
        self._reconnect_count = 0
        self._last_message_time = 0.0
        self._running = False
        self._tasks: List[asyncio.Task] = []
        
        # Global callbacks
        self._on_connect_callbacks: List[Callable] = []
        self._on_disconnect_callbacks: List[Callable] = []
        self._on_error_callbacks: List[Callable] = []
        self._on_message_callbacks: List[Callable] = []
        
        # Message queue for processing
        self._message_queue: asyncio.Queue = asyncio.Queue()
        
        logger.info(f"[WebSocket] Initialized ({'Futures' if use_futures else 'Spot'} API)")
    
    @property
    def state(self) -> ConnectionState:
        """Current connection state"""
        return self._state
    
    @property
    def is_connected(self) -> bool:
        """Check if connected"""
        return self._state == ConnectionState.CONNECTED and self._websocket is not None
    
    @property
    def subscriptions(self) -> Dict[str, StreamSubscription]:
        """Active subscriptions"""
        return self._subscriptions.copy()
    
    @property
    def subscription_count(self) -> int:
        """Number of active subscriptions"""
        return len(self._subscriptions)
    
    def _get_ws_url(self) -> str:
        """Get WebSocket URL based on configuration"""
        if self.use_futures:
            return self.FUTURES_STREAM_URL
        return self.SPOT_STREAM_URL
    
    def _build_stream_url(self) -> str:
        """Build URL with all subscribed streams"""
        if not self._subscriptions:
            return self._get_ws_url()
        
        streams = "/".join(sub.stream_id for sub in self._subscriptions.values())
        return f"{self._get_ws_url()}?streams={streams}"
    
    # ==================== Connection Management ====================
    
    async def connect(self) -> bool:
        """
        Establish WebSocket connection
        
        Returns:
            True if connected successfully
        """
        if self._state in (ConnectionState.CONNECTED, ConnectionState.CONNECTING):
            logger.warning("[WebSocket] Already connected or connecting")
            return self.is_connected
        
        self._state = ConnectionState.CONNECTING
        logger.info(f"[WebSocket] Connecting to {'Futures' if self.use_futures else 'Spot'} API...")
        
        try:
            url = self._build_stream_url()
            self._websocket = await websockets.connect(
                url,
                ping_interval=self.ping_interval,
                ping_timeout=self.ping_timeout,
                close_timeout=10
            )
            
            self._state = ConnectionState.CONNECTED
            self._reconnect_count = 0
            self._last_message_time = time.time()
            
            logger.info(f"[WebSocket] ✓ Connected to {url}")
            
            # Notify callbacks
            for callback in self._on_connect_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback()
                    else:
                        callback()
                except Exception as e:
                    logger.error(f"[WebSocket] Connect callback error: {e}")
            
            return True
            
        except Exception as e:
            self._state = ConnectionState.DISCONNECTED
            logger.error(f"[WebSocket] ✗ Connection failed: {e}")
            
            for callback in self._on_error_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(e)
                    else:
                        callback(e)
                except Exception as ce:
                    logger.error(f"[WebSocket] Error callback error: {ce}")
            
            return False
    
    async def disconnect(self):
        """Gracefully disconnect"""
        if self._state == ConnectionState.DISCONNECTED:
            return
        
        logger.info("[WebSocket] Disconnecting...")
        self._state = ConnectionState.CLOSING
        self._running = False
        
        # Cancel all tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
        
        # Close WebSocket
        if self._websocket:
            try:
                await self._websocket.close()
            except Exception as e:
                logger.warning(f"[WebSocket] Close error: {e}")
            finally:
                self._websocket = None
        
        self._state = ConnectionState.DISCONNECTED
        logger.info("[WebSocket] ✓ Disconnected")
        
        # Notify callbacks
        for callback in self._on_disconnect_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"[WebSocket] Disconnect callback error: {e}")
    
    async def _reconnect(self) -> bool:
        """
        Attempt to reconnect with exponential backoff
        
        Returns:
            True if reconnected successfully
        """
        if self._state == ConnectionState.CLOSING:
            return False
        
        self._state = ConnectionState.RECONNECTING
        self._reconnect_count += 1
        
        if self.max_reconnect_attempts > 0 and self._reconnect_count > self.max_reconnect_attempts:
            logger.error(f"[WebSocket] Max reconnect attempts ({self.max_reconnect_attempts}) exceeded")
            self._state = ConnectionState.DISCONNECTED
            return False
        
        # Exponential backoff
        delay = min(
            self.reconnect_delay * (2 ** (self._reconnect_count - 1)),
            self.max_reconnect_delay
        )
        
        logger.info(f"[WebSocket] Reconnecting in {delay:.1f}s (attempt {self._reconnect_count})")
        await asyncio.sleep(delay)
        
        # Close existing connection
        if self._websocket:
            try:
                await self._websocket.close()
            except:
                pass
            self._websocket = None
        
        return await self.connect()
    
    # ==================== Stream Subscriptions ====================
    
    async def subscribe_kline(
        self,
        symbol: str,
        interval: str,
        callback: Callable[[dict], Any]
    ) -> str:
        """
        Subscribe to kline/candlestick stream
        
        Args:
            symbol: Trading pair (e.g., "BTCUSDT")
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            callback: Function to call with kline data
            
        Returns:
            Stream ID
        """
        stream_id = f"{symbol.lower()}@kline_{interval}"
        
        if stream_id in self._subscriptions:
            self._subscriptions[stream_id].callbacks.append(callback)
            logger.debug(f"[WebSocket] Added callback to existing stream: {stream_id}")
            return stream_id
        
        subscription = StreamSubscription(
            stream_name=stream_id,
            stream_type=StreamType.KLINE,
            symbol=symbol.upper(),
            interval=interval,
            callbacks=[callback]
        )
        
        self._subscriptions[stream_id] = subscription
        logger.info(f"[WebSocket] ✓ Subscribed to kline: {symbol} {interval}")
        
        # Reconnect to update streams
        if self.is_connected:
            await self._update_subscriptions()
        
        return stream_id
    
    async def subscribe_trade(
        self,
        symbol: str,
        callback: Callable[[dict], Any],
        aggregate: bool = True
    ) -> str:
        """
        Subscribe to trade stream
        
        Args:
            symbol: Trading pair
            callback: Function to call with trade data
            aggregate: Use aggregated trades (recommended)
            
        Returns:
            Stream ID
        """
        stream_type = StreamType.AGG_TRADE if aggregate else StreamType.TRADE
        stream_id = f"{symbol.lower()}@{stream_type.value}"
        
        if stream_id in self._subscriptions:
            self._subscriptions[stream_id].callbacks.append(callback)
            return stream_id
        
        subscription = StreamSubscription(
            stream_name=stream_id,
            stream_type=stream_type,
            symbol=symbol.upper(),
            callbacks=[callback]
        )
        
        self._subscriptions[stream_id] = subscription
        logger.info(f"[WebSocket] ✓ Subscribed to trades: {symbol}")
        
        if self.is_connected:
            await self._update_subscriptions()
        
        return stream_id
    
    async def subscribe_ticker(
        self,
        symbol: str,
        callback: Callable[[dict], Any],
        mini: bool = False
    ) -> str:
        """
        Subscribe to ticker stream
        
        Args:
            symbol: Trading pair
            callback: Function to call with ticker data
            mini: Use mini ticker (less data, faster)
            
        Returns:
            Stream ID
        """
        stream_type = StreamType.MINI_TICKER if mini else StreamType.TICKER
        stream_id = f"{symbol.lower()}@{stream_type.value}"
        
        if stream_id in self._subscriptions:
            self._subscriptions[stream_id].callbacks.append(callback)
            return stream_id
        
        subscription = StreamSubscription(
            stream_name=stream_id,
            stream_type=stream_type,
            symbol=symbol.upper(),
            callbacks=[callback]
        )
        
        self._subscriptions[stream_id] = subscription
        logger.info(f"[WebSocket] ✓ Subscribed to ticker: {symbol}")
        
        if self.is_connected:
            await self._update_subscriptions()
        
        return stream_id
    
    async def subscribe_book_ticker(
        self,
        symbol: str,
        callback: Callable[[dict], Any]
    ) -> str:
        """
        Subscribe to best bid/ask stream
        
        Args:
            symbol: Trading pair
            callback: Function to call with book ticker data
            
        Returns:
            Stream ID
        """
        stream_id = f"{symbol.lower()}@bookTicker"
        
        if stream_id in self._subscriptions:
            self._subscriptions[stream_id].callbacks.append(callback)
            return stream_id
        
        subscription = StreamSubscription(
            stream_name=stream_id,
            stream_type=StreamType.BOOK_TICKER,
            symbol=symbol.upper(),
            callbacks=[callback]
        )
        
        self._subscriptions[stream_id] = subscription
        logger.info(f"[WebSocket] ✓ Subscribed to book ticker: {symbol}")
        
        if self.is_connected:
            await self._update_subscriptions()
        
        return stream_id
    
    async def unsubscribe(self, stream_id: str) -> bool:
        """
        Unsubscribe from a stream
        
        Args:
            stream_id: Stream identifier
            
        Returns:
            True if unsubscribed
        """
        if stream_id not in self._subscriptions:
            logger.warning(f"[WebSocket] Stream not found: {stream_id}")
            return False
        
        del self._subscriptions[stream_id]
        logger.info(f"[WebSocket] ✓ Unsubscribed from: {stream_id}")
        
        if self.is_connected:
            await self._update_subscriptions()
        
        return True
    
    async def unsubscribe_all(self):
        """Unsubscribe from all streams"""
        self._subscriptions.clear()
        logger.info("[WebSocket] ✓ Unsubscribed from all streams")
        
        if self.is_connected:
            await self._update_subscriptions()
    
    async def _update_subscriptions(self):
        """Reconnect to update stream subscriptions"""
        if not self._subscriptions:
            await self.disconnect()
            return
        
        # Reconnect with new URL containing updated streams
        logger.debug("[WebSocket] Updating subscriptions...")
        await self.disconnect()
        await asyncio.sleep(0.5)
        await self.connect()
    
    # ==================== Event Callbacks ====================
    
    def on_connect(self, callback: Callable):
        """Register callback for connection event"""
        self._on_connect_callbacks.append(callback)
    
    def on_disconnect(self, callback: Callable):
        """Register callback for disconnection event"""
        self._on_disconnect_callbacks.append(callback)
    
    def on_error(self, callback: Callable[[Exception], Any]):
        """Register callback for error event"""
        self._on_error_callbacks.append(callback)
    
    def on_message(self, callback: Callable[[dict], Any]):
        """Register callback for all messages"""
        self._on_message_callbacks.append(callback)
    
    # ==================== Message Processing ====================
    
    async def _process_message(self, message: str):
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)
            self._last_message_time = time.time()
            
            # Call global message callbacks
            for callback in self._on_message_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(data)
                    else:
                        callback(data)
                except Exception as e:
                    logger.error(f"[WebSocket] Message callback error: {e}")
            
            # Combined stream format: {"stream": "...", "data": {...}}
            if "stream" in data and "data" in data:
                stream_name = data["stream"]
                stream_data = data["data"]
                
                if stream_name in self._subscriptions:
                    sub = self._subscriptions[stream_name]
                    
                    # Parse and normalize data based on type
                    parsed_data = self._parse_stream_data(sub.stream_type, stream_data)
                    
                    # Call subscription callbacks
                    for callback in sub.callbacks:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(parsed_data)
                            else:
                                callback(parsed_data)
                        except Exception as e:
                            logger.error(f"[WebSocket] Subscription callback error: {e}")
            
            # Single stream format
            elif "e" in data:
                event_type = data.get("e")
                symbol = data.get("s", "").lower()
                
                # Find matching subscription
                for stream_id, sub in self._subscriptions.items():
                    if symbol in stream_id.lower():
                        parsed_data = self._parse_stream_data(sub.stream_type, data)
                        
                        for callback in sub.callbacks:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(parsed_data)
                                else:
                                    callback(parsed_data)
                            except Exception as e:
                                logger.error(f"[WebSocket] Callback error: {e}")
                        break
                        
        except json.JSONDecodeError as e:
            logger.warning(f"[WebSocket] Invalid JSON: {e}")
        except Exception as e:
            logger.error(f"[WebSocket] Process message error: {e}")
    
    def _parse_stream_data(self, stream_type: StreamType, data: dict) -> dict:
        """
        Parse and normalize stream data
        
        Returns standardized format for each stream type
        """
        if stream_type == StreamType.KLINE:
            k = data.get("k", data)
            return {
                "type": "kline",
                "symbol": k.get("s", data.get("s")),
                "interval": k.get("i"),
                "timestamp": k.get("t"),
                "open": float(k.get("o", 0)),
                "high": float(k.get("h", 0)),
                "low": float(k.get("l", 0)),
                "close": float(k.get("c", 0)),
                "volume": float(k.get("v", 0)),
                "is_closed": k.get("x", False),
                "trades": k.get("n", 0),
                "quote_volume": float(k.get("q", 0))
            }
        
        elif stream_type in (StreamType.TRADE, StreamType.AGG_TRADE):
            return {
                "type": "trade",
                "symbol": data.get("s"),
                "trade_id": data.get("a") or data.get("t"),
                "price": float(data.get("p", 0)),
                "quantity": float(data.get("q", 0)),
                "timestamp": data.get("T") or data.get("t"),
                "is_buyer_maker": data.get("m", False)
            }
        
        elif stream_type in (StreamType.TICKER, StreamType.MINI_TICKER):
            return {
                "type": "ticker",
                "symbol": data.get("s"),
                "price": float(data.get("c", 0)),
                "open": float(data.get("o", 0)),
                "high": float(data.get("h", 0)),
                "low": float(data.get("l", 0)),
                "volume": float(data.get("v", 0)),
                "quote_volume": float(data.get("q", 0)),
                "price_change": float(data.get("p", 0)),
                "price_change_percent": float(data.get("P", 0)),
                "timestamp": data.get("E")
            }
        
        elif stream_type == StreamType.BOOK_TICKER:
            return {
                "type": "book_ticker",
                "symbol": data.get("s"),
                "bid_price": float(data.get("b", 0)),
                "bid_qty": float(data.get("B", 0)),
                "ask_price": float(data.get("a", 0)),
                "ask_qty": float(data.get("A", 0)),
                "timestamp": data.get("u")
            }
        
        return data
    
    # ==================== Main Loop ====================
    
    async def run_forever(self):
        """
        Main event loop - run until disconnected
        
        Handles message receiving and reconnection
        """
        self._running = True
        
        while self._running:
            try:
                # Connect if not connected
                if not self.is_connected:
                    connected = await self.connect()
                    if not connected:
                        await asyncio.sleep(self.reconnect_delay)
                        continue
                
                # Receive message
                message = await self._websocket.recv()
                await self._process_message(message)
                
            except ConnectionClosed as e:
                logger.warning(f"[WebSocket] Connection closed: {e}")
                if self._running:
                    await self._reconnect()
                    
            except ConnectionClosedError as e:
                logger.warning(f"[WebSocket] Connection closed with error: {e}")
                if self._running:
                    await self._reconnect()
                    
            except asyncio.CancelledError:
                logger.info("[WebSocket] Run loop cancelled")
                break
                
            except Exception as e:
                logger.error(f"[WebSocket] Run loop error: {e}")
                if self._running:
                    await self._reconnect()
        
        # Cleanup
        await self.disconnect()
    
    async def run_once(self, timeout: float = None) -> Optional[dict]:
        """
        Receive a single message
        
        Args:
            timeout: Max time to wait (None = wait forever)
            
        Returns:
            Parsed message data or None
        """
        if not self.is_connected:
            return None
        
        try:
            message = await asyncio.wait_for(
                self._websocket.recv(),
                timeout=timeout
            )
            
            data = json.loads(message)
            self._last_message_time = time.time()
            return data
            
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            logger.error(f"[WebSocket] Run once error: {e}")
            return None
    
    # ==================== Status ====================
    
    def get_status(self) -> dict:
        """Get current WebSocket status"""
        return {
            "state": self._state.value,
            "connected": self.is_connected,
            "api": "futures" if self.use_futures else "spot",
            "subscriptions": len(self._subscriptions),
            "streams": list(self._subscriptions.keys()),
            "reconnect_count": self._reconnect_count,
            "last_message": datetime.fromtimestamp(self._last_message_time).isoformat() 
                if self._last_message_time > 0 else None
        }


# ==================== Convenience Functions ====================

async def create_price_stream(
    symbols: List[str],
    callback: Callable[[dict], Any],
    use_futures: bool = False
) -> BinanceWebSocket:
    """
    Quick helper to create a price ticker stream for multiple symbols
    
    Args:
        symbols: List of trading pairs
        callback: Function to call with ticker data
        use_futures: Use Futures API
        
    Returns:
        Connected WebSocket client
    """
    ws = BinanceWebSocket(use_futures=use_futures)
    await ws.connect()
    
    for symbol in symbols:
        await ws.subscribe_ticker(symbol, callback, mini=True)
    
    return ws


async def create_kline_stream(
    symbol: str,
    interval: str,
    callback: Callable[[dict], Any],
    use_futures: bool = False
) -> BinanceWebSocket:
    """
    Quick helper to create a kline stream
    
    Args:
        symbol: Trading pair
        interval: Kline interval
        callback: Function to call with kline data
        use_futures: Use Futures API
        
    Returns:
        Connected WebSocket client
    """
    ws = BinanceWebSocket(use_futures=use_futures)
    await ws.connect()
    await ws.subscribe_kline(symbol, interval, callback)
    
    return ws
