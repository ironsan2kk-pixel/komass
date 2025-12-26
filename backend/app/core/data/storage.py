"""
Komas Trading System - Data Storage
====================================
Хранение и управление историческими данными в формате Parquet.

Функции:
- Чтение/запись Parquet файлов
- Метаданные файлов (даты, размер, строки)
- Поиск и фильтрация файлов
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import pandas as pd

from ..logger import get_logger
from ..config import settings

logger = get_logger("data.storage")


# ═══════════════════════════════════════════════════════════════════
# DATACLASSES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class FileInfo:
    """Информация о файле данных"""
    filename: str
    filepath: Path
    symbol: str
    timeframe: str
    rows: int
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    size_mb: float
    modified: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Конвертация в словарь для API"""
        return {
            "filename": self.filename,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "rows": self.rows,
            "start": self.start_date.isoformat() if self.start_date else None,
            "end": self.end_date.isoformat() if self.end_date else None,
            "size_mb": self.size_mb,
            "modified": self.modified.isoformat()
        }


# ═══════════════════════════════════════════════════════════════════
# DATA STORAGE
# ═══════════════════════════════════════════════════════════════════

class DataStorage:
    """
    Менеджер хранения данных в Parquet файлах.
    
    Структура файлов:
        data/
        ├── BTCUSDT_1h.parquet
        ├── ETHUSDT_1h.parquet
        └── ...
    
    Пример:
        storage = DataStorage()
        df = storage.load("BTCUSDT", "1h")
        storage.save("BTCUSDT", "1h", df)
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        """
        Args:
            data_dir: Папка для данных (по умолчанию из настроек)
        """
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = self._find_data_dir()
        
        # Создаём папку если нет
        self.data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Data directory: {self.data_dir.absolute()}")
    
    def _find_data_dir(self) -> Path:
        """Найти или создать папку данных"""
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "data",  # backend/data
            Path("data"),
            Path("backend/data"),
            Path.cwd() / "data",
            Path.cwd() / "backend" / "data",
        ]
        
        for p in possible_paths:
            if p.exists():
                return p
        
        # Default
        return Path(__file__).parent.parent.parent.parent / "data"
    
    def _get_filepath(self, symbol: str, timeframe: str) -> Path:
        """Получить путь к файлу"""
        return self.data_dir / f"{symbol}_{timeframe}.parquet"
    
    # ═══════════════════════════════════════════════════════════════
    # CRUD ОПЕРАЦИИ
    # ═══════════════════════════════════════════════════════════════
    
    def exists(self, symbol: str, timeframe: str) -> bool:
        """Проверить существование файла"""
        return self._get_filepath(symbol, timeframe).exists()
    
    def load(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """
        Загрузить данные из файла.
        
        Returns:
            DataFrame с индексом timestamp или None если файл не найден
        """
        filepath = self._get_filepath(symbol, timeframe)
        
        if not filepath.exists():
            logger.warning(f"File not found: {filepath}")
            return None
        
        try:
            df = pd.read_parquet(filepath)
            logger.debug(f"Loaded {symbol}_{timeframe}: {len(df):,} rows")
            return df
        except Exception as e:
            logger.error(f"Error loading {filepath}: {e}")
            return None
    
    def save(
        self, 
        symbol: str, 
        timeframe: str, 
        df: pd.DataFrame,
        merge_existing: bool = True
    ) -> bool:
        """
        Сохранить данные в файл.
        
        Args:
            symbol: Торговая пара
            timeframe: Таймфрейм
            df: DataFrame с данными
            merge_existing: Объединить с существующими данными
        
        Returns:
            True если успешно
        """
        filepath = self._get_filepath(symbol, timeframe)
        
        try:
            # Убеждаемся что индекс - timestamp
            if "timestamp" in df.columns:
                df = df.set_index("timestamp")
            
            # Удаляем дубликаты
            df = df[~df.index.duplicated(keep='last')]
            
            # Объединяем с существующими
            if merge_existing and filepath.exists():
                existing = pd.read_parquet(filepath)
                df = pd.concat([existing, df])
                df = df[~df.index.duplicated(keep='last')]
            
            # Сортируем по времени
            df.sort_index(inplace=True)
            
            # Сохраняем
            df.to_parquet(filepath)
            logger.info(f"Saved {symbol}_{timeframe}: {len(df):,} rows")
            return True
            
        except Exception as e:
            logger.error(f"Error saving {filepath}: {e}")
            return False
    
    def delete(self, symbol: str, timeframe: str) -> bool:
        """Удалить файл данных"""
        filepath = self._get_filepath(symbol, timeframe)
        
        if not filepath.exists():
            return False
        
        try:
            filepath.unlink()
            logger.info(f"Deleted: {filepath.name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting {filepath}: {e}")
            return False
    
    # ═══════════════════════════════════════════════════════════════
    # МЕТАДАННЫЕ
    # ═══════════════════════════════════════════════════════════════
    
    def get_info(self, symbol: str, timeframe: str) -> Optional[FileInfo]:
        """Получить информацию о файле"""
        filepath = self._get_filepath(symbol, timeframe)
        
        if not filepath.exists():
            return None
        
        try:
            df = pd.read_parquet(filepath)
            stat = filepath.stat()
            
            return FileInfo(
                filename=filepath.name,
                filepath=filepath,
                symbol=symbol,
                timeframe=timeframe,
                rows=len(df),
                start_date=df.index[0] if len(df) > 0 else None,
                end_date=df.index[-1] if len(df) > 0 else None,
                size_mb=round(stat.st_size / 1024 / 1024, 2),
                modified=datetime.fromtimestamp(stat.st_mtime)
            )
        except Exception as e:
            logger.error(f"Error getting info for {filepath}: {e}")
            return None
    
    def get_last_timestamp(self, symbol: str, timeframe: str) -> Optional[int]:
        """
        Получить timestamp последней свечи в миллисекундах.
        Используется для синхронизации.
        """
        filepath = self._get_filepath(symbol, timeframe)
        
        if not filepath.exists():
            return None
        
        try:
            df = pd.read_parquet(filepath)
            if len(df) > 0:
                return int(df.index[-1].timestamp() * 1000)
            return None
        except Exception as e:
            logger.error(f"Error getting last timestamp: {e}")
            return None
    
    def list_files(
        self, 
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None
    ) -> List[FileInfo]:
        """
        Список всех файлов данных.
        
        Args:
            symbol: Фильтр по символу (опционально)
            timeframe: Фильтр по таймфрейму (опционально)
        
        Returns:
            Список FileInfo
        """
        files = []
        
        for filepath in self.data_dir.glob("*.parquet"):
            try:
                # Парсим имя файла
                name = filepath.stem
                parts = name.split("_")
                
                if len(parts) < 2:
                    continue
                
                file_symbol = parts[0]
                file_tf = parts[1]
                
                # Фильтруем
                if symbol and file_symbol != symbol:
                    continue
                if timeframe and file_tf != timeframe:
                    continue
                
                # Читаем данные
                df = pd.read_parquet(filepath)
                stat = filepath.stat()
                
                files.append(FileInfo(
                    filename=filepath.name,
                    filepath=filepath,
                    symbol=file_symbol,
                    timeframe=file_tf,
                    rows=len(df),
                    start_date=df.index[0] if len(df) > 0 else None,
                    end_date=df.index[-1] if len(df) > 0 else None,
                    size_mb=round(stat.st_size / 1024 / 1024, 2),
                    modified=datetime.fromtimestamp(stat.st_mtime)
                ))
                
            except Exception as e:
                logger.warning(f"Error reading {filepath}: {e}")
                continue
        
        # Сортируем по символу
        files.sort(key=lambda x: x.symbol)
        return files
    
    def get_outdated_files(self, max_age_days: int = 7) -> List[FileInfo]:
        """
        Получить список устаревших файлов.
        
        Args:
            max_age_days: Максимальный возраст данных (дней)
        
        Returns:
            Файлы, в которых последняя свеча старше max_age_days
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=max_age_days)
        outdated = []
        
        for file_info in self.list_files():
            if file_info.end_date and file_info.end_date < cutoff:
                outdated.append(file_info)
        
        return outdated
    
    def get_total_size_mb(self) -> float:
        """Общий размер всех файлов в MB"""
        return sum(f.size_mb for f in self.list_files())
    
    def get_symbols(self, timeframe: Optional[str] = None) -> List[str]:
        """Получить список символов"""
        symbols = set()
        for f in self.list_files(timeframe=timeframe):
            symbols.add(f.symbol)
        return sorted(symbols)
