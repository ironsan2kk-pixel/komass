"""
Komas Trading Server - WebSocket API
====================================
REST and SSE endpoints for real-time data streaming

Features:
- Server-Sent Events (SSE) for real-time price updates
- WebSocket status and management
- Multiple symbol subscriptions
- Connection state monitoring
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Set
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ws", tags=["WebSocket"])

# ==================== Global State ====================

# Active WebSocket client (singleton for now)
_ws_client = None
_ws_task = None

# SSE clients tracking
_sse_clients: Dict[str, Set[asyncio.Queue]] = {}  # stream_id -> set of queues
_price_cache: Dict[str, dict] = {}  # symbol -> last price data


# ==================== Request/Response Models ====================

class SubscribeRequest(BaseModel):
    """Request to subscribe to streams"""
    symbols: List[str]
    stream_type: str = "ticker"  # ticker, kline, trade, book_ticker
    interval: Optional[str] = "1m"  # For kline streams


class UnsubscribeRequest(BaseModel):
    """Request to unsubscribe from streams"""
    stream_ids: List[str]


class WSStatusResponse(BaseModel):
    """WebSocket status response"""
    connected: bool
    state: str
    api: str
    subscriptions: int
    streams: List[str]
    reconnect_count: int
    last_message: Optional[str]


# ==================== Internal Functions ====================

def _get_ws_client():
    """Get or create WebSocket client"""
    global _ws_client
    
    if _ws_client is None:
        from app.core.data.websocket import BinanceWebSocket
        _ws_client = BinanceWebSocket(use_futures=False)
        logger.info("[WS API] Created new BinanceWebSocket client")
    
    return _ws_client


async def _on_ticker_update(data: dict):
    """Handle ticker update - broadcast to SSE clients"""
    symbol = data.get("symbol", "").upper()
    if not symbol:
        return
    
    # Update cache
    _price_cache[symbol] = data
    
    # Broadcast to SSE clients subscribed to this symbol
    stream_id = f"{symbol.lower()}@miniTicker"
    
    if stream_id in _sse_clients:
        message = json.dumps({
            "type": "ticker",
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
        dead_queues = set()
        for queue in _sse_clients[stream_id]:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                dead_queues.add(queue)
        
        # Remove dead queues
        _sse_clients[stream_id] -= dead_queues


async def _on_kline_update(data: dict):
    """Handle kline update - broadcast to SSE clients"""
    symbol = data.get("symbol", "").upper()
    interval = data.get("interval", "")
    if not symbol or not interval:
        return
    
    stream_id = f"{symbol.lower()}@kline_{interval}"
    
    if stream_id in _sse_clients:
        message = json.dumps({
            "type": "kline",
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
        dead_queues = set()
        for queue in _sse_clients[stream_id]:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                dead_queues.add(queue)
        
        _sse_clients[stream_id] -= dead_queues


async def _on_trade_update(data: dict):
    """Handle trade update - broadcast to SSE clients"""
    symbol = data.get("symbol", "").upper()
    if not symbol:
        return
    
    stream_id = f"{symbol.lower()}@aggTrade"
    
    if stream_id in _sse_clients:
        message = json.dumps({
            "type": "trade",
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
        dead_queues = set()
        for queue in _sse_clients[stream_id]:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                dead_queues.add(queue)
        
        _sse_clients[stream_id] -= dead_queues


async def _on_book_ticker_update(data: dict):
    """Handle book ticker update - broadcast to SSE clients"""
    symbol = data.get("symbol", "").upper()
    if not symbol:
        return
    
    stream_id = f"{symbol.lower()}@bookTicker"
    
    if stream_id in _sse_clients:
        message = json.dumps({
            "type": "book_ticker",
            "data": data,
            "timestamp": datetime.now().isoformat()
        })
        
        dead_queues = set()
        for queue in _sse_clients[stream_id]:
            try:
                queue.put_nowait(message)
            except asyncio.QueueFull:
                dead_queues.add(queue)
        
        _sse_clients[stream_id] -= dead_queues


async def _start_ws_loop():
    """Start WebSocket event loop in background"""
    global _ws_task
    
    ws = _get_ws_client()
    
    if _ws_task is not None and not _ws_task.done():
        logger.warning("[WS API] WebSocket loop already running")
        return
    
    async def run_loop():
        try:
            await ws.run_forever()
        except asyncio.CancelledError:
            logger.info("[WS API] WebSocket loop cancelled")
        except Exception as e:
            logger.error(f"[WS API] WebSocket loop error: {e}")
    
    _ws_task = asyncio.create_task(run_loop())
    logger.info("[WS API] Started WebSocket background loop")


async def _stop_ws_loop():
    """Stop WebSocket event loop"""
    global _ws_task, _ws_client
    
    if _ws_task is not None:
        _ws_task.cancel()
        try:
            await _ws_task
        except asyncio.CancelledError:
            pass
        _ws_task = None
    
    if _ws_client is not None:
        await _ws_client.disconnect()
    
    logger.info("[WS API] Stopped WebSocket loop")


# ==================== REST Endpoints ====================

@router.get("/status")
async def get_ws_status() -> dict:
    """
    Get WebSocket connection status
    
    Returns current state, subscriptions, and connection info
    """
    ws = _get_ws_client()
    status = ws.get_status()
    
    # Add SSE client counts
    sse_clients_count = sum(len(clients) for clients in _sse_clients.values())
    status["sse_clients"] = sse_clients_count
    status["cached_prices"] = len(_price_cache)
    
    return status


@router.post("/connect")
async def connect_ws():
    """
    Connect to Binance WebSocket
    
    Establishes connection and starts background loop
    """
    ws = _get_ws_client()
    
    if ws.is_connected:
        return {"success": True, "message": "Already connected", "status": ws.get_status()}
    
    try:
        connected = await ws.connect()
        
        if connected:
            await _start_ws_loop()
            return {"success": True, "message": "Connected", "status": ws.get_status()}
        else:
            return {"success": False, "message": "Connection failed"}
            
    except Exception as e:
        logger.error(f"[WS API] Connect error: {e}")
        raise HTTPException(500, f"Connection failed: {str(e)}")


@router.post("/disconnect")
async def disconnect_ws():
    """
    Disconnect from Binance WebSocket
    
    Stops background loop and closes connection
    """
    await _stop_ws_loop()
    
    return {"success": True, "message": "Disconnected"}


@router.post("/subscribe")
async def subscribe_streams(request: SubscribeRequest):
    """
    Subscribe to streams for given symbols
    
    Args:
        symbols: List of trading pairs (e.g., ["BTCUSDT", "ETHUSDT"])
        stream_type: Type of stream (ticker, kline, trade, book_ticker)
        interval: Kline interval (required for kline streams)
    """
    ws = _get_ws_client()
    
    if not ws.is_connected:
        await ws.connect()
        await _start_ws_loop()
    
    subscribed = []
    errors = []
    
    callback_map = {
        "ticker": _on_ticker_update,
        "kline": _on_kline_update,
        "trade": _on_trade_update,
        "book_ticker": _on_book_ticker_update
    }
    
    callback = callback_map.get(request.stream_type)
    if not callback:
        raise HTTPException(400, f"Unknown stream type: {request.stream_type}")
    
    for symbol in request.symbols:
        try:
            if request.stream_type == "ticker":
                stream_id = await ws.subscribe_ticker(symbol, callback, mini=True)
            elif request.stream_type == "kline":
                stream_id = await ws.subscribe_kline(symbol, request.interval, callback)
            elif request.stream_type == "trade":
                stream_id = await ws.subscribe_trade(symbol, callback)
            elif request.stream_type == "book_ticker":
                stream_id = await ws.subscribe_book_ticker(symbol, callback)
            else:
                raise ValueError(f"Unknown stream type: {request.stream_type}")
            
            # Initialize SSE client set for this stream
            if stream_id not in _sse_clients:
                _sse_clients[stream_id] = set()
            
            subscribed.append({"symbol": symbol, "stream_id": stream_id})
            
        except Exception as e:
            logger.error(f"[WS API] Subscribe error for {symbol}: {e}")
            errors.append({"symbol": symbol, "error": str(e)})
    
    return {
        "success": len(errors) == 0,
        "subscribed": subscribed,
        "errors": errors,
        "total_subscriptions": ws.subscription_count
    }


@router.post("/unsubscribe")
async def unsubscribe_streams(request: UnsubscribeRequest):
    """
    Unsubscribe from streams
    
    Args:
        stream_ids: List of stream IDs to unsubscribe
    """
    ws = _get_ws_client()
    
    unsubscribed = []
    errors = []
    
    for stream_id in request.stream_ids:
        try:
            result = await ws.unsubscribe(stream_id)
            
            if result:
                # Remove from SSE clients
                if stream_id in _sse_clients:
                    del _sse_clients[stream_id]
                
                unsubscribed.append(stream_id)
            else:
                errors.append({"stream_id": stream_id, "error": "Not found"})
                
        except Exception as e:
            logger.error(f"[WS API] Unsubscribe error for {stream_id}: {e}")
            errors.append({"stream_id": stream_id, "error": str(e)})
    
    return {
        "success": len(errors) == 0,
        "unsubscribed": unsubscribed,
        "errors": errors,
        "total_subscriptions": ws.subscription_count
    }


@router.post("/unsubscribe-all")
async def unsubscribe_all():
    """Unsubscribe from all streams"""
    ws = _get_ws_client()
    
    await ws.unsubscribe_all()
    _sse_clients.clear()
    _price_cache.clear()
    
    return {
        "success": True,
        "message": "Unsubscribed from all streams",
        "total_subscriptions": 0
    }


@router.get("/prices")
async def get_cached_prices(
    symbols: Optional[str] = Query(None, description="Comma-separated symbols")
):
    """
    Get cached price data
    
    Returns last known prices for subscribed symbols
    """
    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        return {
            symbol: _price_cache.get(symbol) 
            for symbol in symbol_list 
            if symbol in _price_cache
        }
    
    return _price_cache


@router.get("/streams")
async def list_streams():
    """List all active streams"""
    ws = _get_ws_client()
    
    return {
        "streams": [
            {
                "stream_id": stream_id,
                "symbol": sub.symbol,
                "type": sub.stream_type.value,
                "interval": sub.interval,
                "sse_clients": len(_sse_clients.get(stream_id, set()))
            }
            for stream_id, sub in ws.subscriptions.items()
        ],
        "total": ws.subscription_count
    }


# ==================== SSE Endpoints ====================

@router.get("/sse/prices")
async def sse_prices(
    symbols: str = Query(..., description="Comma-separated symbols")
):
    """
    Server-Sent Events stream for price updates
    
    Subscribe to real-time price updates for given symbols.
    
    Args:
        symbols: Comma-separated list of trading pairs
        
    Returns:
        SSE stream with price updates
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    
    ws = _get_ws_client()
    
    # Ensure connection and subscriptions
    if not ws.is_connected:
        await ws.connect()
        await _start_ws_loop()
    
    # Subscribe to symbols
    for symbol in symbol_list:
        stream_id = f"{symbol.lower()}@miniTicker"
        
        if stream_id not in ws.subscriptions:
            await ws.subscribe_ticker(symbol, _on_ticker_update, mini=True)
        
        if stream_id not in _sse_clients:
            _sse_clients[stream_id] = set()
    
    async def event_generator():
        """Generate SSE events"""
        queue = asyncio.Queue(maxsize=100)
        
        # Register queue for each symbol
        stream_ids = [f"{s.lower()}@miniTicker" for s in symbol_list]
        
        for stream_id in stream_ids:
            _sse_clients[stream_id].add(queue)
        
        try:
            # Send initial cached data
            for symbol in symbol_list:
                if symbol in _price_cache:
                    data = json.dumps({
                        "type": "ticker",
                        "data": _price_cache[symbol],
                        "timestamp": datetime.now().isoformat()
                    })
                    yield f"data: {data}\n\n"
            
            # Stream updates
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    # Send heartbeat
                    yield f": heartbeat\n\n"
                    
        except asyncio.CancelledError:
            pass
        finally:
            # Cleanup - remove queue from all streams
            for stream_id in stream_ids:
                if stream_id in _sse_clients:
                    _sse_clients[stream_id].discard(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/sse/klines")
async def sse_klines(
    symbol: str = Query(..., description="Trading pair"),
    interval: str = Query("1m", description="Kline interval")
):
    """
    Server-Sent Events stream for kline updates
    
    Subscribe to real-time candlestick updates.
    
    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        interval: Kline interval (1m, 5m, 15m, 1h, etc.)
        
    Returns:
        SSE stream with kline updates
    """
    symbol = symbol.upper()
    stream_id = f"{symbol.lower()}@kline_{interval}"
    
    ws = _get_ws_client()
    
    # Ensure connection and subscription
    if not ws.is_connected:
        await ws.connect()
        await _start_ws_loop()
    
    if stream_id not in ws.subscriptions:
        await ws.subscribe_kline(symbol, interval, _on_kline_update)
    
    if stream_id not in _sse_clients:
        _sse_clients[stream_id] = set()
    
    async def event_generator():
        """Generate SSE events"""
        queue = asyncio.Queue(maxsize=100)
        _sse_clients[stream_id].add(queue)
        
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    yield f": heartbeat\n\n"
                    
        except asyncio.CancelledError:
            pass
        finally:
            _sse_clients[stream_id].discard(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/sse/trades")
async def sse_trades(
    symbol: str = Query(..., description="Trading pair")
):
    """
    Server-Sent Events stream for trade updates
    
    Subscribe to real-time trade updates.
    
    Args:
        symbol: Trading pair (e.g., "BTCUSDT")
        
    Returns:
        SSE stream with trade updates
    """
    symbol = symbol.upper()
    stream_id = f"{symbol.lower()}@aggTrade"
    
    ws = _get_ws_client()
    
    if not ws.is_connected:
        await ws.connect()
        await _start_ws_loop()
    
    if stream_id not in ws.subscriptions:
        await ws.subscribe_trade(symbol, _on_trade_update)
    
    if stream_id not in _sse_clients:
        _sse_clients[stream_id] = set()
    
    async def event_generator():
        """Generate SSE events"""
        queue = asyncio.Queue(maxsize=100)
        _sse_clients[stream_id].add(queue)
        
        try:
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {message}\n\n"
                except asyncio.TimeoutError:
                    yield f": heartbeat\n\n"
                    
        except asyncio.CancelledError:
            pass
        finally:
            _sse_clients[stream_id].discard(queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ==================== Quick Actions ====================

@router.post("/quick/start-prices")
async def quick_start_prices(
    symbols: str = Query("BTCUSDT,ETHUSDT,BNBUSDT", description="Comma-separated symbols")
):
    """
    Quick start: Connect and subscribe to price tickers
    
    Convenience endpoint to quickly start receiving prices
    """
    symbol_list = [s.strip().upper() for s in symbols.split(",")]
    
    ws = _get_ws_client()
    
    # Connect
    if not ws.is_connected:
        await ws.connect()
        await _start_ws_loop()
    
    # Subscribe
    subscribed = []
    for symbol in symbol_list:
        try:
            stream_id = await ws.subscribe_ticker(symbol, _on_ticker_update, mini=True)
            if stream_id not in _sse_clients:
                _sse_clients[stream_id] = set()
            subscribed.append(symbol)
        except Exception as e:
            logger.error(f"[WS API] Quick subscribe error for {symbol}: {e}")
    
    return {
        "success": True,
        "message": f"Started price stream for {len(subscribed)} symbols",
        "symbols": subscribed,
        "sse_url": f"/api/ws/sse/prices?symbols={','.join(subscribed)}"
    }


@router.post("/quick/stop")
async def quick_stop():
    """
    Quick stop: Unsubscribe from all and disconnect
    
    Convenience endpoint to stop all WebSocket activity
    """
    ws = _get_ws_client()
    
    await ws.unsubscribe_all()
    await _stop_ws_loop()
    
    _sse_clients.clear()
    _price_cache.clear()
    
    return {
        "success": True,
        "message": "Stopped all WebSocket streams"
    }
