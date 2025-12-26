"""
Komas Trading System - Data API
================================
REST API для управления историческими данными.

Endpoints:
- GET  /api/data/symbols     - Список доступных символов
- GET  /api/data/timeframes  - Список таймфреймов
- GET  /api/data/available   - Загруженные файлы
- POST /api/data/download    - Начать загрузку
- GET  /api/data/download/progress - Прогресс загрузки
- POST /api/data/download/cancel/{task_id} - Отменить загрузку
- POST /api/data/sync        - Синхронизировать данные
- POST /api/data/continue/{symbol}/{tf} - Докачать символ
- DELETE /api/data/file/{filename} - Удалить файл
- GET  /api/data/debug       - Отладка путей
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from ..core.logger import get_logger
from ..core.data import DataManager, BinanceClient, BINANCE_SYMBOLS, TIMEFRAMES

logger = get_logger("api.data")
router = APIRouter(prefix="/api/data", tags=["Data Management"])

# Глобальный менеджер данных
_manager: Optional[DataManager] = None


def get_manager() -> DataManager:
    """Получить singleton менеджера данных"""
    global _manager
    if _manager is None:
        _manager = DataManager(source="spot")
    return _manager


# ═══════════════════════════════════════════════════════════════════
# МОДЕЛИ ЗАПРОСОВ
# ═══════════════════════════════════════════════════════════════════

class DownloadRequest(BaseModel):
    symbols: List[str]
    timeframe: str = "1h"
    start_date: Optional[str] = None
    source: str = "spot"


class SyncRequest(BaseModel):
    symbols: Optional[List[str]] = None
    timeframe: str = "1h"


# ═══════════════════════════════════════════════════════════════════
# СПРАВОЧНЫЕ ENDPOINTS
# ═══════════════════════════════════════════════════════════════════

@router.get("/symbols")
async def get_symbols():
    """Получить список доступных символов Binance"""
    symbols = []
    for s in BINANCE_SYMBOLS:
        base = s.replace("USDT", "").replace("1000", "")
        symbols.append({
            "symbol": s,
            "baseAsset": base,
            "quoteAsset": "USDT"
        })
    
    logger.debug(f"Returned {len(symbols)} symbols")
    return {
        "success": True,
        "count": len(symbols),
        "symbols": symbols
    }


@router.get("/timeframes")
async def get_timeframes():
    """Получить список таймфреймов"""
    tf_list = [
        {"value": "1m", "label": "1 минута", "ms": 60000},
        {"value": "5m", "label": "5 минут", "ms": 300000},
        {"value": "15m", "label": "15 минут", "ms": 900000},
        {"value": "30m", "label": "30 минут", "ms": 1800000},
        {"value": "1h", "label": "1 час", "ms": 3600000},
        {"value": "2h", "label": "2 часа", "ms": 7200000},
        {"value": "4h", "label": "4 часа", "ms": 14400000},
        {"value": "1d", "label": "1 день", "ms": 86400000},
    ]
    return {"success": True, "timeframes": tf_list}


# ═══════════════════════════════════════════════════════════════════
# ФАЙЛЫ ДАННЫХ
# ═══════════════════════════════════════════════════════════════════

@router.get("/available")
async def get_available_data():
    """Получить список загруженных файлов"""
    manager = get_manager()
    files = manager.list_files()
    
    return {
        "success": True,
        "count": len(files),
        "files": [f.to_dict() for f in files],
        "total_size_mb": manager.get_total_size_mb()
    }


@router.get("/outdated")
async def get_outdated_files(max_age_days: int = 7):
    """Получить устаревшие файлы"""
    manager = get_manager()
    outdated = manager.get_outdated(max_age_days)
    
    return {
        "success": True,
        "count": len(outdated),
        "files": [f.to_dict() for f in outdated]
    }


@router.delete("/file/{filename}")
async def delete_file(filename: str):
    """Удалить файл данных"""
    # Парсим имя файла
    if not filename.endswith(".parquet"):
        raise HTTPException(400, "Invalid filename")
    
    name = filename.replace(".parquet", "")
    parts = name.split("_")
    
    if len(parts) < 2:
        raise HTTPException(400, "Invalid filename format")
    
    symbol = parts[0]
    timeframe = parts[1]
    
    manager = get_manager()
    
    if manager.delete(symbol, timeframe):
        logger.info(f"Deleted file: {filename}")
        return {"success": True, "message": f"Deleted {filename}"}
    
    raise HTTPException(404, "File not found")


# ═══════════════════════════════════════════════════════════════════
# ЗАГРУЗКА ДАННЫХ
# ═══════════════════════════════════════════════════════════════════

@router.post("/download")
async def start_download(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Начать загрузку исторических данных.
    
    Загрузка выполняется в фоне. Используйте /download/progress для отслеживания.
    """
    if not request.symbols:
        raise HTTPException(400, "No symbols provided")
    
    # Создаём менеджер с нужным источником
    global _manager
    _manager = DataManager(source=request.source)
    manager = _manager
    
    # Запускаем загрузку
    task = await manager.download_async(
        symbols=request.symbols,
        timeframe=request.timeframe,
        start_date=request.start_date
    )
    
    logger.info(f"Download started: {task.task_id} for {len(request.symbols)} symbols")
    
    return {
        "success": True,
        "task_id": task.task_id,
        "symbols": request.symbols,
        "timeframe": request.timeframe,
        "source": request.source,
        "message": f"Download started from Binance {request.source.upper()}"
    }


@router.get("/download/progress")
async def get_download_progress():
    """Получить прогресс всех загрузок"""
    manager = get_manager()
    tasks = manager.get_all_tasks()
    
    active = {}
    progress = {}
    
    for task_id, task in tasks.items():
        active[task_id] = task.status
        progress[task_id] = manager.get_progress(task_id)
    
    return {
        "active": active,
        "progress": progress
    }


@router.post("/download/cancel/{task_id}")
async def cancel_download(task_id: str):
    """Отменить загрузку"""
    manager = get_manager()
    
    if manager.cancel_task(task_id):
        logger.info(f"Download cancelled: {task_id}")
        return {"success": True, "message": "Download cancelled"}
    
    return {"success": False, "message": "Task not found or already completed"}


# ═══════════════════════════════════════════════════════════════════
# СИНХРОНИЗАЦИЯ
# ═══════════════════════════════════════════════════════════════════

@router.post("/sync")
async def sync_data(request: SyncRequest):
    """
    Синхронизировать данные (добавить новые свечи).
    
    Если symbols не указан — синхронизирует все файлы указанного таймфрейма.
    """
    manager = get_manager()
    
    if request.symbols:
        # Синхронизируем конкретные символы
        results = []
        for symbol in request.symbols:
            result = await manager.sync_symbol(symbol, request.timeframe)
            if result:
                results.append(result)
        
        return {
            "success": True,
            "synced": [r for r in results if "error" not in r],
            "errors": [r for r in results if "error" in r]
        }
    else:
        # Синхронизируем все
        return await manager.sync_all(request.timeframe)


@router.post("/continue/{symbol}/{timeframe}")
async def continue_download(symbol: str, timeframe: str):
    """Докачать данные для конкретного символа"""
    manager = get_manager()
    
    task = await manager.download_async(
        symbols=[symbol],
        timeframe=timeframe
    )
    
    logger.info(f"Continue download: {symbol}_{timeframe}")
    
    return {
        "success": True,
        "task_id": task.task_id,
        "symbol": symbol,
        "message": f"Continuing download for {symbol}"
    }


# ═══════════════════════════════════════════════════════════════════
# ОТЛАДКА
# ═══════════════════════════════════════════════════════════════════

@router.get("/debug")
async def debug_paths():
    """Отладочная информация о путях и файлах"""
    import os
    from pathlib import Path
    
    manager = get_manager()
    storage = manager.storage
    
    return {
        "cwd": str(Path.cwd()),
        "data_dir": str(storage.data_dir.absolute()),
        "data_dir_exists": storage.data_dir.exists(),
        "files_count": len(manager.list_files()),
        "total_size_mb": manager.get_total_size_mb(),
        "symbols_count": len(manager.get_symbols()),
        "env_pwd": os.environ.get("PWD", "not set"),
    }


@router.get("/info/{symbol}/{timeframe}")
async def get_file_info(symbol: str, timeframe: str):
    """Получить информацию о конкретном файле"""
    manager = get_manager()
    info = manager.get_info(symbol, timeframe)
    
    if not info:
        raise HTTPException(404, f"File not found: {symbol}_{timeframe}")
    
    return {
        "success": True,
        "file": info.to_dict()
    }
