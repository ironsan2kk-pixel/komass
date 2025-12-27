"""
Komas Trading Server - Data Management API
==========================================
Full history download with retry logic and parallel processing
Binance FUTURES ONLY (v4.0)
"""
import os
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
import pandas as pd
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

router = APIRouter(prefix="/api/data", tags=["Data Management"])

# Try multiple possible data locations
def find_data_dir():
    possible_paths = [
        Path(__file__).parent.parent.parent / "data",  # backend/data
        Path("data"),  # relative
        Path("backend/data"),  # from root
        Path("../data"),  # from backend
        Path.cwd() / "data",  # current dir / data
        Path.cwd() / "backend" / "data",  # current dir / backend / data
    ]
    
    for p in possible_paths:
        if p.exists():
            print(f"[Data] Found existing DATA_DIR: {p.absolute()}")
            return p
    
    # Default: create in backend folder
    default = Path(__file__).parent.parent.parent / "data"
    default.mkdir(exist_ok=True)
    print(f"[Data] Created DATA_DIR: {default.absolute()}")
    return default

DATA_DIR = find_data_dir()

# Active downloads tracking
active_downloads = {}
download_progress = {}

# Parallel workers
NUM_WORKERS = os.cpu_count() or 4
MAX_CONCURRENT_DOWNLOADS = min(NUM_WORKERS, 4)  # Limit to avoid API rate limits

# Binance Futures API URL (ONLY Futures supported)
BINANCE_FUTURES_URL = "https://fapi.binance.com/fapi/v1/klines"

# Binance Futures symbols list
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
]


class DownloadRequest(BaseModel):
    symbols: List[str]
    timeframe: str = "1h"
    start_date: Optional[str] = None
    # source removed - Futures only


@router.get("/symbols")
async def get_binance_symbols():
    symbols = []
    for s in BINANCE_SYMBOLS:
        base = s.replace("USDT", "").replace("1000", "")
        symbols.append({"symbol": s, "baseAsset": base, "quoteAsset": "USDT"})
    return {"success": True, "count": len(symbols), "symbols": symbols}


@router.get("/debug")
async def debug_paths():
    """Debug endpoint to check paths and files"""
    import os
    
    files_in_data_dir = []
    if DATA_DIR.exists():
        files_in_data_dir = list(DATA_DIR.glob("*.parquet"))
    
    return {
        "cwd": str(Path.cwd()),
        "data_dir": str(DATA_DIR.absolute()),
        "data_dir_exists": DATA_DIR.exists(),
        "parquet_files_count": len(files_in_data_dir),
        "parquet_files": [f.name for f in files_in_data_dir[:20]],  # First 20
        "env_pwd": os.environ.get("PWD", "not set"),
        "api_source": "Binance Futures"
    }


@router.get("/available")
async def get_available_data():
    files = []
    for filepath in DATA_DIR.glob("*.parquet"):
        try:
            df = pd.read_parquet(filepath)
            stat = filepath.stat()
            name = filepath.stem
            parts = name.split("_")
            symbol = parts[0] if parts else name
            timeframe = parts[1] if len(parts) > 1 else "unknown"
            
            files.append({
                "filename": filepath.name,
                "symbol": symbol,
                "timeframe": timeframe,
                "rows": len(df),
                "start": df.index[0].isoformat() if len(df) > 0 else None,
                "end": df.index[-1].isoformat() if len(df) > 0 else None,
                "size_mb": round(stat.st_size / 1024 / 1024, 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        except Exception as e:
            files.append({"filename": filepath.name, "error": str(e)})
    
    files.sort(key=lambda x: x.get("symbol", ""))
    return {"success": True, "count": len(files), "files": files}


@router.post("/download")
async def start_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    task_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    background_tasks.add_task(
        download_history, task_id, request.symbols, request.timeframe, 
        request.start_date
    )
    
    return {
        "success": True,
        "task_id": task_id,
        "symbols": request.symbols,
        "timeframe": request.timeframe,
        "source": "futures",
        "message": "Download started from Binance FUTURES"
    }


@router.get("/download/progress")
async def get_download_progress():
    return {"active": active_downloads, "progress": download_progress}


@router.post("/download/cancel/{task_id}")
async def cancel_download(task_id: str):
    if task_id in active_downloads:
        active_downloads[task_id] = "cancelled"
        return {"success": True, "message": "Download cancelled"}
    return {"success": False, "message": "Task not found"}


async def download_history(
    task_id: str,
    symbols: List[str],
    timeframe: str,
    start_date: Optional[str]
):
    """Background task to download historical data from Binance Futures"""
    import aiohttp
    
    active_downloads[task_id] = "running"
    download_progress[task_id] = {
        "total": len(symbols),
        "completed": 0,
        "current": None,
        "current_progress": "",
        "errors": [],
        "source": "futures"
    }
    
    tf_ms = {
        "1m": 60000, "3m": 180000, "5m": 300000, "15m": 900000,
        "30m": 1800000, "1h": 3600000, "2h": 7200000, "4h": 14400000,
        "6h": 21600000, "8h": 28800000, "12h": 43200000, "1d": 86400000
    }
    
    interval_ms = tf_ms.get(timeframe, 3600000)
    
    # Longer timeout for large downloads
    timeout = aiohttp.ClientTimeout(total=60)
    connector = aiohttp.TCPConnector(limit=5)  # Limit concurrent connections
    
    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        for i, symbol in enumerate(symbols):
            if active_downloads.get(task_id) == "cancelled":
                break
                
            download_progress[task_id]["current"] = symbol
            download_progress[task_id]["current_progress"] = "Starting..."
            
            try:
                result = await download_symbol_with_retry(
                    session, symbol, timeframe, interval_ms, start_date, task_id
                )
                download_progress[task_id]["completed"] = i + 1
                
                if result:
                    print(f"[Data] ✓ {symbol} {timeframe}: {result['rows']:,} candles ({result['start']} - {result['end']})")
                    
            except Exception as e:
                print(f"[Data] ✗ Error {symbol}: {e}")
                download_progress[task_id]["errors"].append({
                    "symbol": symbol, "error": str(e)
                })
    
    active_downloads[task_id] = "completed"
    download_progress[task_id]["current"] = None


async def download_symbol_with_retry(
    session,
    symbol: str,
    timeframe: str,
    interval_ms: int,
    start_date: Optional[str],
    task_id: str,
    max_retries: int = 5
) -> Optional[dict]:
    """Download with retry logic and progress tracking - Futures only"""
    
    filepath = DATA_DIR / f"{symbol}_{timeframe}.parquet"
    
    # Determine start time - Futures data available from Sept 2019
    if start_date:
        start_ts = int(datetime.fromisoformat(start_date).timestamp() * 1000)
    else:
        start_ts = int(datetime(2019, 9, 1).timestamp() * 1000)
    
    end_ts = int(datetime.now().timestamp() * 1000)
    
    # Load existing data
    existing_df = None
    if filepath.exists():
        try:
            existing_df = pd.read_parquet(filepath)
            last_ts = int(existing_df.index[-1].timestamp() * 1000)
            start_ts = last_ts + interval_ms
            
            if start_ts >= end_ts - interval_ms:
                return {
                    "rows": len(existing_df),
                    "start": existing_df.index[0].strftime("%Y-%m-%d"),
                    "end": existing_df.index[-1].strftime("%Y-%m-%d"),
                    "status": "up_to_date"
                }
        except:
            existing_df = None
    
    all_candles = []
    current_ts = start_ts
    consecutive_errors = 0
    request_count = 0
    
    while current_ts < end_ts:
        # Check if cancelled
        if active_downloads.get(task_id) == "cancelled":
            break
        
        # Progress update
        progress_pct = min(100, int((current_ts - start_ts) / (end_ts - start_ts) * 100))
        candle_date = datetime.fromtimestamp(current_ts / 1000).strftime("%Y-%m-%d")
        download_progress[task_id]["current_progress"] = f"{progress_pct}% ({candle_date})"
        
        retry_count = 0
        success = False
        
        while retry_count < max_retries and not success:
            try:
                async with session.get(
                    BINANCE_FUTURES_URL,
                    params={
                        "symbol": symbol,
                        "interval": timeframe,
                        "startTime": current_ts,
                        "limit": 1000
                    }
                ) as response:
                    
                    # Check rate limit
                    if response.status == 429:
                        wait_time = int(response.headers.get('Retry-After', 60))
                        print(f"[Data] Rate limited, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        retry_count += 1
                        continue
                    
                    if response.status == 418:  # IP ban
                        print(f"[Data] IP banned! Waiting 5 minutes...")
                        await asyncio.sleep(300)
                        retry_count += 1
                        continue
                    
                    if response.status != 200:
                        print(f"[Data] HTTP {response.status} for {symbol}")
                        retry_count += 1
                        await asyncio.sleep(5)
                        continue
                    
                    data = await response.json()
                    
                    # Check for API error
                    if isinstance(data, dict) and 'code' in data:
                        if data['code'] == -1121:  # Invalid symbol
                            print(f"[Data] Invalid symbol: {symbol}")
                            return None
                        print(f"[Data] API error: {data}")
                        retry_count += 1
                        await asyncio.sleep(5)
                        continue
                    
                    if not data:
                        # No more data available
                        success = True
                        current_ts = end_ts  # Exit loop
                        break
                    
                    # Process candles
                    for candle in data:
                        all_candles.append({
                            "timestamp": datetime.fromtimestamp(candle[0] / 1000),
                            "open": float(candle[1]),
                            "high": float(candle[2]),
                            "low": float(candle[3]),
                            "close": float(candle[4]),
                            "volume": float(candle[5]),
                        })
                    
                    # Move to next batch
                    current_ts = data[-1][0] + interval_ms
                    success = True
                    consecutive_errors = 0
                    request_count += 1
                    
                    # Rate limiting - Futures limit: 2400 requests per minute
                    # So we do ~20-30 requests per second max
                    await asyncio.sleep(0.1)
                    
                    # Save periodically (every 100 requests)
                    if request_count % 100 == 0 and all_candles:
                        await save_candles(filepath, existing_df, all_candles)
                        print(f"[Data] {symbol}: Saved {len(all_candles):,} candles (checkpoint)")
                    
            except asyncio.TimeoutError:
                print(f"[Data] Timeout for {symbol}, retry {retry_count + 1}/{max_retries}")
                retry_count += 1
                await asyncio.sleep(5)
                
            except Exception as e:
                print(f"[Data] Error: {e}, retry {retry_count + 1}/{max_retries}")
                retry_count += 1
                await asyncio.sleep(5)
        
        if not success:
            consecutive_errors += 1
            if consecutive_errors >= 3:
                print(f"[Data] Too many consecutive errors for {symbol}, stopping")
                break
            # Try to continue from next timestamp
            current_ts += interval_ms * 1000
    
    # Final save
    if all_candles:
        result = await save_candles(filepath, existing_df, all_candles)
        return result
    elif existing_df is not None:
        return {
            "rows": len(existing_df),
            "start": existing_df.index[0].strftime("%Y-%m-%d"),
            "end": existing_df.index[-1].strftime("%Y-%m-%d"),
            "status": "no_new_data"
        }
    
    return None


async def save_candles(filepath, existing_df, new_candles) -> dict:
    """Save candles to parquet file"""
    new_df = pd.DataFrame(new_candles)
    new_df.set_index("timestamp", inplace=True)
    new_df = new_df[~new_df.index.duplicated(keep='last')]
    
    if existing_df is not None:
        df = pd.concat([existing_df, new_df])
        df = df[~df.index.duplicated(keep='last')]
        df.sort_index(inplace=True)
    else:
        df = new_df
    
    df.to_parquet(filepath)
    
    return {
        "rows": len(df),
        "start": df.index[0].strftime("%Y-%m-%d"),
        "end": df.index[-1].strftime("%Y-%m-%d"),
        "new_candles": len(new_candles)
    }


@router.post("/sync")
async def sync_latest(symbols: List[str] = None, timeframe: str = "1h"):
    """Sync latest candles for symbols (parallel) - Futures only"""
    import aiohttp
    
    if not symbols:
        symbols = []
        for f in DATA_DIR.glob(f"*_{timeframe}.parquet"):
            symbol = f.stem.replace(f"_{timeframe}", "")
            symbols.append(symbol)
    
    if not symbols:
        return {"success": True, "synced": [], "message": "No files to sync"}
    
    synced = []
    errors = []
    
    async def sync_symbol(session, symbol):
        """Sync a single symbol from Binance Futures"""
        try:
            filepath = DATA_DIR / f"{symbol}_{timeframe}.parquet"
            if not filepath.exists():
                return None
            
            df = pd.read_parquet(filepath)
            last_ts = int(df.index[-1].timestamp() * 1000)
            
            async with session.get(
                BINANCE_FUTURES_URL,
                params={
                    "symbol": symbol,
                    "interval": timeframe,
                    "startTime": last_ts,
                    "limit": 500
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                data = await response.json()
                
                if data and isinstance(data, list):
                    new_candles = []
                    for candle in data:
                        new_candles.append({
                            "timestamp": datetime.fromtimestamp(candle[0] / 1000),
                            "open": float(candle[1]),
                            "high": float(candle[2]),
                            "low": float(candle[3]),
                            "close": float(candle[4]),
                            "volume": float(candle[5]),
                        })
                    
                    if new_candles:
                        new_df = pd.DataFrame(new_candles)
                        new_df.set_index("timestamp", inplace=True)
                        
                        df = pd.concat([df, new_df])
                        df = df[~df.index.duplicated(keep='last')]
                        df.sort_index(inplace=True)
                        df.to_parquet(filepath)
                        
                        return {
                            "symbol": symbol,
                            "new_candles": len(new_candles),
                            "end": df.index[-1].strftime("%Y-%m-%d %H:%M")
                        }
            return None
        except Exception as e:
            return {"symbol": symbol, "error": str(e)}
    
    # Parallel sync with semaphore to limit concurrent requests
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
    
    async def sync_with_limit(session, symbol):
        async with semaphore:
            await asyncio.sleep(0.1)  # Small delay for rate limiting
            return await sync_symbol(session, symbol)
    
    async with aiohttp.ClientSession() as session:
        tasks = [sync_with_limit(session, symbol) for symbol in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                errors.append({"error": str(result)})
            elif result is not None:
                if "error" in result:
                    errors.append(result)
                else:
                    synced.append(result)
    
    return {
        "success": True, 
        "synced": synced, 
        "errors": errors,
        "parallel_workers": MAX_CONCURRENT_DOWNLOADS,
        "source": "futures"
    }


@router.delete("/file/{filename}")
async def delete_file(filename: str):
    filepath = DATA_DIR / filename
    if filepath.exists():
        filepath.unlink()
        return {"success": True, "message": f"Deleted {filename}"}
    raise HTTPException(404, "File not found")


@router.post("/continue/{symbol}/{timeframe}")
async def continue_download(symbol: str, timeframe: str, background_tasks: BackgroundTasks):
    """Continue downloading a specific symbol that was interrupted - Futures only"""
    
    task_id = f"continue_{symbol}_{datetime.now().strftime('%H%M%S')}"
    
    background_tasks.add_task(
        download_history, task_id, [symbol], timeframe, None
    )
    
    return {
        "success": True,
        "task_id": task_id,
        "symbol": symbol,
        "source": "futures",
        "message": f"Continuing download for {symbol} from Binance FUTURES"
    }
