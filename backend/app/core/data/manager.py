"""
Komas Trading System - Data Manager
====================================
Фасад для управления историческими данными.

Объединяет:
- BinanceClient: загрузка с биржи
- DataStorage: хранение в файлах

Функции:
- Загрузка полной истории
- Синхронизация (добавление новых свечей)
- Отслеживание прогресса
- Управление задачами
"""

import asyncio
import os
from datetime import datetime
from typing import Optional, List, Dict, Callable, Any
from dataclasses import dataclass, field
import pandas as pd

from ..logger import get_logger
from .binance import BinanceClient, Candle, DownloadProgress, TIMEFRAMES
from .storage import DataStorage, FileInfo

logger = get_logger("data.manager")


# ═══════════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class DownloadTask:
    """Задача загрузки"""
    task_id: str
    symbols: List[str]
    timeframe: str
    source: str
    status: str = "pending"  # pending, running, completed, cancelled, error
    total: int = 0
    completed: int = 0
    current_symbol: Optional[str] = None
    current_progress: str = ""
    errors: List[Dict[str, str]] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


# ═══════════════════════════════════════════════════════════════════
# DATA MANAGER
# ═══════════════════════════════════════════════════════════════════

class DataManager:
    """
    Менеджер данных — главный фасад модуля.
    
    Пример:
        manager = DataManager()
        
        # Загрузка истории
        task = await manager.download_async(["BTCUSDT", "ETHUSDT"], "1h")
        
        # Получить данные
        df = manager.load("BTCUSDT", "1h")
        
        # Синхронизация
        await manager.sync_all("1h")
    """
    
    def __init__(self, source: str = "spot"):
        """
        Args:
            source: "spot" или "futures"
        """
        self.source = source
        self.storage = DataStorage()
        self.client = BinanceClient(source=source)
        
        # Активные задачи
        self._tasks: Dict[str, DownloadTask] = {}
        
        # Количество параллельных загрузок
        self._max_concurrent = min(os.cpu_count() or 4, 4)
        
        logger.info(f"DataManager initialized (source={source}, workers={self._max_concurrent})")
    
    # ═══════════════════════════════════════════════════════════════
    # ЗАГРУЗКА ДАННЫХ
    # ═══════════════════════════════════════════════════════════════
    
    async def download_async(
        self,
        symbols: List[str],
        timeframe: str,
        start_date: Optional[str] = None
    ) -> DownloadTask:
        """
        Запустить асинхронную загрузку данных.
        
        Args:
            symbols: Список торговых пар
            timeframe: Таймфрейм
            start_date: Начальная дата (ISO format, опционально)
        
        Returns:
            DownloadTask с task_id для отслеживания
        """
        task_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        task = DownloadTask(
            task_id=task_id,
            symbols=symbols,
            timeframe=timeframe,
            source=self.source,
            status="running",
            total=len(symbols),
            started_at=datetime.now()
        )
        
        self._tasks[task_id] = task
        
        # Запускаем в фоне
        asyncio.create_task(self._download_batch(task, start_date))
        
        logger.info(f"Download started: {task_id} ({len(symbols)} symbols)")
        return task
    
    async def _download_batch(
        self,
        task: DownloadTask,
        start_date: Optional[str]
    ):
        """Фоновая загрузка батча символов"""
        interval_ms = TIMEFRAMES.get(task.timeframe, 3_600_000)
        
        for i, symbol in enumerate(task.symbols):
            if task.status == "cancelled":
                break
            
            task.current_symbol = symbol
            task.current_progress = "Starting..."
            
            try:
                await self._download_symbol(
                    symbol, 
                    task.timeframe, 
                    interval_ms,
                    start_date,
                    task
                )
                task.completed = i + 1
                
            except Exception as e:
                logger.error(f"Error downloading {symbol}: {e}")
                task.errors.append({
                    "symbol": symbol,
                    "error": str(e)
                })
        
        # Завершение
        if task.status != "cancelled":
            task.status = "completed"
        task.current_symbol = None
        task.completed_at = datetime.now()
        
        # Закрываем клиент
        await self.client.close()
        
        logger.info(f"Download {task.task_id} completed: {task.completed}/{task.total}")
    
    async def _download_symbol(
        self,
        symbol: str,
        timeframe: str,
        interval_ms: int,
        start_date: Optional[str],
        task: DownloadTask
    ):
        """Загрузка одного символа"""
        
        # Определяем начало
        if start_date:
            start_ts = int(datetime.fromisoformat(start_date).timestamp() * 1000)
        else:
            start_ts = None
        
        # Проверяем существующие данные
        existing_ts = self.storage.get_last_timestamp(symbol, timeframe)
        if existing_ts:
            start_ts = existing_ts + interval_ms
        
        # Прогресс callback
        def on_progress(progress: DownloadProgress):
            task.current_progress = f"{progress.percent}% ({progress.current_date})"
        
        # Checkpoint callback
        accumulated_candles = []
        def on_checkpoint(candles: List[Candle]):
            nonlocal accumulated_candles
            accumulated_candles = candles
            # Сохраняем промежуточные данные
            df = self._candles_to_df(candles)
            self.storage.save(symbol, timeframe, df, merge_existing=True)
        
        # Загружаем
        candles = await self.client.download_history(
            symbol=symbol,
            timeframe=timeframe,
            start_ts=start_ts,
            on_progress=on_progress,
            on_checkpoint=on_checkpoint
        )
        
        # Финальное сохранение
        if candles:
            df = self._candles_to_df(candles)
            self.storage.save(symbol, timeframe, df, merge_existing=True)
            
            info = self.storage.get_info(symbol, timeframe)
            if info:
                logger.info(f"✓ {symbol}: {info.rows:,} candles ({info.start_date} - {info.end_date})")
    
    def _candles_to_df(self, candles: List[Candle]) -> pd.DataFrame:
        """Конвертировать свечи в DataFrame"""
        data = [{
            "timestamp": c.timestamp,
            "open": c.open,
            "high": c.high,
            "low": c.low,
            "close": c.close,
            "volume": c.volume
        } for c in candles]
        
        df = pd.DataFrame(data)
        df.set_index("timestamp", inplace=True)
        return df
    
    # ═══════════════════════════════════════════════════════════════
    # УПРАВЛЕНИЕ ЗАДАЧАМИ
    # ═══════════════════════════════════════════════════════════════
    
    def get_task(self, task_id: str) -> Optional[DownloadTask]:
        """Получить задачу по ID"""
        return self._tasks.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, DownloadTask]:
        """Получить все задачи"""
        return self._tasks.copy()
    
    def cancel_task(self, task_id: str) -> bool:
        """Отменить задачу"""
        task = self._tasks.get(task_id)
        if task and task.status == "running":
            task.status = "cancelled"
            self.client.cancel()
            logger.info(f"Task {task_id} cancelled")
            return True
        return False
    
    def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Получить прогресс задачи для API"""
        task = self._tasks.get(task_id)
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "status": task.status,
            "total": task.total,
            "completed": task.completed,
            "current": task.current_symbol,
            "current_progress": task.current_progress,
            "errors": task.errors,
            "percent": int((task.completed / task.total * 100)) if task.total > 0 else 0
        }
    
    # ═══════════════════════════════════════════════════════════════
    # СИНХРОНИЗАЦИЯ
    # ═══════════════════════════════════════════════════════════════
    
    async def sync_symbol(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """
        Синхронизировать один символ (добавить новые свечи).
        
        Returns:
            Dict с результатом или None если ошибка
        """
        last_ts = self.storage.get_last_timestamp(symbol, timeframe)
        
        if last_ts is None:
            logger.warning(f"No data to sync for {symbol}_{timeframe}")
            return None
        
        try:
            candles = await self.client.sync_latest(symbol, timeframe, last_ts)
            
            if candles:
                df = self._candles_to_df(candles)
                self.storage.save(symbol, timeframe, df, merge_existing=True)
                
                info = self.storage.get_info(symbol, timeframe)
                return {
                    "symbol": symbol,
                    "new_candles": len(candles),
                    "end": info.end_date.strftime("%Y-%m-%d %H:%M") if info else None
                }
            
            return {"symbol": symbol, "new_candles": 0}
            
        except Exception as e:
            logger.error(f"Sync error for {symbol}: {e}")
            return {"symbol": symbol, "error": str(e)}
    
    async def sync_all(self, timeframe: str) -> Dict[str, Any]:
        """
        Синхронизировать все файлы указанного таймфрейма.
        
        Returns:
            Dict с результатами
        """
        symbols = self.storage.get_symbols(timeframe)
        
        if not symbols:
            return {"success": True, "synced": [], "message": "No files to sync"}
        
        logger.info(f"Syncing {len(symbols)} symbols for {timeframe}")
        
        synced = []
        errors = []
        
        # Параллельная синхронизация с ограничением
        semaphore = asyncio.Semaphore(self._max_concurrent)
        
        async def sync_with_limit(symbol: str):
            async with semaphore:
                await asyncio.sleep(0.1)  # Rate limiting
                return await self.sync_symbol(symbol, timeframe)
        
        tasks = [sync_with_limit(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                errors.append({"error": str(result)})
            elif result:
                if "error" in result:
                    errors.append(result)
                elif result.get("new_candles", 0) > 0:
                    synced.append(result)
        
        await self.client.close()
        
        return {
            "success": True,
            "synced": synced,
            "errors": errors,
            "total_symbols": len(symbols)
        }
    
    # ═══════════════════════════════════════════════════════════════
    # ДОСТУП К ДАННЫМ
    # ═══════════════════════════════════════════════════════════════
    
    def load(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Загрузить данные из хранилища"""
        return self.storage.load(symbol, timeframe)
    
    def exists(self, symbol: str, timeframe: str) -> bool:
        """Проверить наличие данных"""
        return self.storage.exists(symbol, timeframe)
    
    def get_info(self, symbol: str, timeframe: str) -> Optional[FileInfo]:
        """Получить информацию о файле"""
        return self.storage.get_info(symbol, timeframe)
    
    def list_files(self) -> List[FileInfo]:
        """Список всех файлов"""
        return self.storage.list_files()
    
    def delete(self, symbol: str, timeframe: str) -> bool:
        """Удалить файл данных"""
        return self.storage.delete(symbol, timeframe)
    
    def get_outdated(self, max_age_days: int = 7) -> List[FileInfo]:
        """Получить устаревшие файлы"""
        return self.storage.get_outdated_files(max_age_days)
    
    def get_symbols(self, timeframe: Optional[str] = None) -> List[str]:
        """Список символов"""
        return self.storage.get_symbols(timeframe)
    
    def get_total_size_mb(self) -> float:
        """Общий размер данных"""
        return self.storage.get_total_size_mb()
