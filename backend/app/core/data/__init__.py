"""
Komas Trading Server - Data Module
===================================
Data fetching, storage, and real-time streaming

Components:
- BinanceClient: Historical data from Binance API
- DataStorage: Parquet file storage
- DataManager: Facade for data operations
- BinanceWebSocket: Real-time WebSocket streaming
"""
from .websocket import (
    BinanceWebSocket,
    StreamType,
    ConnectionState,
    StreamSubscription,
    create_price_stream,
    create_kline_stream
)

__all__ = [
    # WebSocket
    "BinanceWebSocket",
    "StreamType", 
    "ConnectionState",
    "StreamSubscription",
    "create_price_stream",
    "create_kline_stream",
]

# Try to import other data components (may not exist yet)
try:
    from .binance import BinanceClient
    __all__.append("BinanceClient")
except ImportError:
    pass

try:
    from .storage import DataStorage
    __all__.append("DataStorage")
except ImportError:
    pass

try:
    from .manager import DataManager
    __all__.append("DataManager")
except ImportError:
    pass
