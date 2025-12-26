"""
Komas Trading Server - Database Module
======================================
SQLite database setup with SQLAlchemy async support

Модели:
- Settings: глобальные настройки приложения
- Preset: сохранённые настройки индикатора
- Bot: конфигурации торговых ботов
- Signal: торговые сигналы
- OptimizationResult: результаты оптимизации
- DataCacheInfo: метаданные кэша данных
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, TypeVar, Generic
from contextlib import asynccontextmanager

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, 
    DateTime, Text, JSON, ForeignKey, Index, event
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

# ============ DATABASE CONFIGURATION ============

# Database path
DB_DIR = Path(__file__).parent.parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "komas.db"

# SQLAlchemy URLs
SQLITE_URL = f"sqlite:///{DB_PATH}"
SQLITE_ASYNC_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# Base class for models
Base = declarative_base()


# ============ MODELS ============

class Settings(Base):
    """Global application settings"""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default="string")  # string, int, float, bool, json
    description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_typed_value(self):
        """Return value with proper type"""
        if self.value is None:
            return None
        if self.value_type == "int":
            return int(self.value)
        if self.value_type == "float":
            return float(self.value)
        if self.value_type == "bool":
            return self.value.lower() in ("true", "1", "yes")
        if self.value_type == "json":
            return json.loads(self.value)
        return self.value
    
    @classmethod
    def set_typed_value(cls, value: Any) -> tuple:
        """Convert value to string and determine type"""
        if value is None:
            return (None, "string")
        if isinstance(value, bool):
            return (str(value).lower(), "bool")
        if isinstance(value, int):
            return (str(value), "int")
        if isinstance(value, float):
            return (str(value), "float")
        if isinstance(value, (dict, list)):
            return (json.dumps(value), "json")
        return (str(value), "string")


class Preset(Base):
    """Saved indicator settings presets"""
    __tablename__ = "presets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    indicator_type = Column(String(50), default="trg")  # For future: different indicators
    
    # Stored as JSON for flexibility
    settings = Column(JSON, nullable=False)
    
    # Metadata
    is_default = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    tags = Column(String(255), nullable=True)  # Comma-separated tags
    
    # Performance snapshot (optional, from last backtest)
    win_rate = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    total_profit_percent = Column(Float, nullable=True)
    max_drawdown_percent = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    
    # Relations
    bots = relationship("Bot", back_populates="preset")
    optimization_results = relationship("OptimizationResult", back_populates="preset")
    
    def get_tags_list(self) -> List[str]:
        """Return tags as list"""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]
    
    def set_tags_list(self, tags: List[str]):
        """Set tags from list"""
        self.tags = ",".join(tags) if tags else None


class Bot(Base):
    """Trading bot configurations"""
    __tablename__ = "bots"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    
    # Link to preset (or store settings directly)
    preset_id = Column(Integer, ForeignKey("presets.id"), nullable=True)
    preset = relationship("Preset", back_populates="bots")
    
    # Bot settings (if not using preset)
    settings = Column(JSON, nullable=True)
    
    # Trading pair & timeframe
    symbol = Column(String(20), nullable=False, default="BTCUSDT")
    timeframe = Column(String(10), nullable=False, default="1h")
    
    # Status
    is_active = Column(Boolean, default=False)
    is_paper = Column(Boolean, default=True)  # Paper trading mode
    
    # Telegram notifications
    telegram_enabled = Column(Boolean, default=True)
    telegram_chat_id = Column(String(50), nullable=True)
    use_cornix_format = Column(Boolean, default=True)
    
    # Position management
    position_size = Column(Float, default=100.0)  # USDT or % 
    position_size_type = Column(String(10), default="fixed")  # fixed, percent
    max_positions = Column(Integer, default=1)
    
    # Statistics
    total_signals = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    total_profit = Column(Float, default=0.0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_signal_at = Column(DateTime, nullable=True)
    
    # Relations
    signals = relationship("Signal", back_populates="bot")


class Signal(Base):
    """Trading signals generated by bots"""
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to bot
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False, index=True)
    bot = relationship("Bot", back_populates="signals")
    
    # Signal info
    symbol = Column(String(20), nullable=False, index=True)
    timeframe = Column(String(10), nullable=False)
    direction = Column(String(10), nullable=False)  # long, short
    
    # Prices
    entry_price = Column(Float, nullable=False)
    stop_loss = Column(Float, nullable=True)
    
    # Take profits (stored as JSON array)
    take_profits = Column(JSON, nullable=True)  # [{percent, amount, price}]
    
    # Status
    status = Column(String(20), default="pending")  # pending, active, closed, cancelled
    exit_price = Column(Float, nullable=True)
    exit_reason = Column(String(50), nullable=True)  # tp1, tp2, sl, manual, signal_change
    
    # P&L
    pnl_percent = Column(Float, nullable=True)
    pnl_amount = Column(Float, nullable=True)
    
    # Metadata
    indicator_values = Column(JSON, nullable=True)  # Snapshot of indicator values
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    filled_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    
    # Notification tracking
    telegram_sent = Column(Boolean, default=False)
    telegram_message_id = Column(String(50), nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_signals_bot_status', 'bot_id', 'status'),
        Index('ix_signals_symbol_created', 'symbol', 'created_at'),
    )


class OptimizationResult(Base):
    """Saved optimization results"""
    __tablename__ = "optimization_results"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Link to preset (optional)
    preset_id = Column(Integer, ForeignKey("presets.id"), nullable=True)
    preset = relationship("Preset", back_populates="optimization_results")
    
    # Optimization type
    mode = Column(String(20), nullable=False)  # indicator, tp, sl, filters, full
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    
    # Date range used
    start_date = Column(String(20), nullable=True)
    end_date = Column(String(20), nullable=True)
    
    # Best parameters found
    best_params = Column(JSON, nullable=False)
    
    # Performance metrics
    win_rate = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    total_profit_percent = Column(Float, nullable=True)
    max_drawdown_percent = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    total_trades = Column(Integer, nullable=True)
    
    # Optimization metadata
    total_combinations = Column(Integer, nullable=True)
    tested_combinations = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    workers_used = Column(Integer, nullable=True)
    
    # Heatmap data (for i1/i2 optimization)
    heatmap_data = Column(JSON, nullable=True)  # [{i1, i2, metric_value}]
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class DataCacheInfo(Base):
    """Metadata about cached data files"""
    __tablename__ = "data_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Data identification
    symbol = Column(String(20), nullable=False)
    timeframe = Column(String(10), nullable=False)
    source = Column(String(20), default="binance")  # binance, bybit, etc
    
    # File info
    filename = Column(String(100), nullable=False)
    filepath = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Data range
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    candles_count = Column(Integer, nullable=True)
    
    # Status
    is_complete = Column(Boolean, default=False)  # Full history downloaded
    last_candle_time = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_accessed_at = Column(DateTime, nullable=True)
    
    # Unique constraint
    __table_args__ = (
        Index('ix_data_cache_unique', 'symbol', 'timeframe', 'source', unique=True),
    )


# ============ DATABASE MANAGER ============

class DatabaseManager:
    """Manages database connections and operations"""
    
    _instance = None
    _engine = None
    _async_engine = None
    _session_factory = None
    _async_session_factory = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def initialize(cls, echo: bool = False):
        """Initialize database engines and create tables"""
        logger.info(f"Initializing database: {DB_PATH}")
        
        # Sync engine (for migrations and simple operations)
        cls._engine = create_engine(
            SQLITE_URL,
            echo=echo,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        
        # Async engine (for FastAPI)
        cls._async_engine = create_async_engine(
            SQLITE_ASYNC_URL,
            echo=echo,
            connect_args={"check_same_thread": False}
        )
        
        # Session factories
        cls._session_factory = sessionmaker(
            bind=cls._engine,
            autocommit=False,
            autoflush=False
        )
        
        cls._async_session_factory = async_sessionmaker(
            bind=cls._async_engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        
        # Create tables
        Base.metadata.create_all(cls._engine)
        logger.info("✓ Database tables created")
        
        # Enable foreign keys for SQLite
        @event.listens_for(cls._engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()
        
        return cls._instance
    
    @classmethod
    def get_session(cls):
        """Get synchronous session"""
        if cls._session_factory is None:
            cls.initialize()
        return cls._session_factory()
    
    @classmethod
    def get_async_session(cls) -> AsyncSession:
        """Get async session"""
        if cls._async_session_factory is None:
            cls.initialize()
        return cls._async_session_factory()
    
    @classmethod
    @asynccontextmanager
    async def session(cls):
        """Async context manager for session"""
        session = cls.get_async_session()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            await session.close()
    
    @classmethod
    async def close(cls):
        """Close database connections"""
        if cls._async_engine:
            await cls._async_engine.dispose()
        if cls._engine:
            cls._engine.dispose()
        logger.info("Database connections closed")


# ============ CRUD HELPERS ============

class SettingsManager:
    """CRUD operations for Settings"""
    
    @staticmethod
    async def get(key: str, default: Any = None) -> Any:
        """Get setting value by key"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Settings).where(Settings.key == key)
            )
            setting = result.scalar_one_or_none()
            if setting:
                return setting.get_typed_value()
            return default
    
    @staticmethod
    async def set(key: str, value: Any, description: str = None) -> Settings:
        """Set setting value"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Settings).where(Settings.key == key)
            )
            setting = result.scalar_one_or_none()
            
            str_value, value_type = Settings.set_typed_value(value)
            
            if setting:
                setting.value = str_value
                setting.value_type = value_type
                if description:
                    setting.description = description
            else:
                setting = Settings(
                    key=key,
                    value=str_value,
                    value_type=value_type,
                    description=description
                )
                session.add(setting)
            
            return setting
    
    @staticmethod
    async def get_all() -> Dict[str, Any]:
        """Get all settings as dict"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            result = await session.execute(select(Settings))
            settings = result.scalars().all()
            return {s.key: s.get_typed_value() for s in settings}
    
    @staticmethod
    async def delete(key: str) -> bool:
        """Delete setting by key"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select, delete
            result = await session.execute(
                delete(Settings).where(Settings.key == key)
            )
            return result.rowcount > 0


class PresetManager:
    """CRUD operations for Presets"""
    
    @staticmethod
    async def create(
        name: str,
        settings: Dict[str, Any],
        description: str = None,
        indicator_type: str = "trg",
        tags: List[str] = None
    ) -> Preset:
        """Create new preset"""
        async with DatabaseManager.session() as session:
            preset = Preset(
                name=name,
                description=description,
                indicator_type=indicator_type,
                settings=settings,
                tags=",".join(tags) if tags else None
            )
            session.add(preset)
            await session.flush()
            return preset
    
    @staticmethod
    async def get(preset_id: int) -> Optional[Preset]:
        """Get preset by ID"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Preset).where(Preset.id == preset_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_name(name: str) -> Optional[Preset]:
        """Get preset by name"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Preset).where(Preset.name == name)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def list_all(
        indicator_type: str = None,
        favorites_only: bool = False,
        limit: int = 100
    ) -> List[Preset]:
        """List all presets with optional filters"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            query = select(Preset).order_by(Preset.updated_at.desc())
            
            if indicator_type:
                query = query.where(Preset.indicator_type == indicator_type)
            if favorites_only:
                query = query.where(Preset.is_favorite == True)
            
            query = query.limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())
    
    @staticmethod
    async def update(
        preset_id: int,
        **kwargs
    ) -> Optional[Preset]:
        """Update preset"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Preset).where(Preset.id == preset_id)
            )
            preset = result.scalar_one_or_none()
            
            if preset:
                for key, value in kwargs.items():
                    if hasattr(preset, key):
                        setattr(preset, key, value)
            
            return preset
    
    @staticmethod
    async def delete(preset_id: int) -> bool:
        """Delete preset by ID"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import delete
            result = await session.execute(
                delete(Preset).where(Preset.id == preset_id)
            )
            return result.rowcount > 0
    
    @staticmethod
    async def update_performance(
        preset_id: int,
        win_rate: float = None,
        profit_factor: float = None,
        total_profit_percent: float = None,
        max_drawdown_percent: float = None,
        sharpe_ratio: float = None
    ) -> Optional[Preset]:
        """Update preset performance metrics"""
        return await PresetManager.update(
            preset_id,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_profit_percent=total_profit_percent,
            max_drawdown_percent=max_drawdown_percent,
            sharpe_ratio=sharpe_ratio
        )


class BotManager:
    """CRUD operations for Bots"""
    
    @staticmethod
    async def create(
        name: str,
        symbol: str = "BTCUSDT",
        timeframe: str = "1h",
        preset_id: int = None,
        settings: Dict[str, Any] = None,
        **kwargs
    ) -> Bot:
        """Create new bot"""
        async with DatabaseManager.session() as session:
            bot = Bot(
                name=name,
                symbol=symbol,
                timeframe=timeframe,
                preset_id=preset_id,
                settings=settings,
                **kwargs
            )
            session.add(bot)
            await session.flush()
            return bot
    
    @staticmethod
    async def get(bot_id: int) -> Optional[Bot]:
        """Get bot by ID"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Bot).where(Bot.id == bot_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def list_all(active_only: bool = False) -> List[Bot]:
        """List all bots"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            query = select(Bot).order_by(Bot.created_at.desc())
            
            if active_only:
                query = query.where(Bot.is_active == True)
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    @staticmethod
    async def update(bot_id: int, **kwargs) -> Optional[Bot]:
        """Update bot"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Bot).where(Bot.id == bot_id)
            )
            bot = result.scalar_one_or_none()
            
            if bot:
                for key, value in kwargs.items():
                    if hasattr(bot, key):
                        setattr(bot, key, value)
            
            return bot
    
    @staticmethod
    async def activate(bot_id: int) -> Optional[Bot]:
        """Activate bot"""
        return await BotManager.update(bot_id, is_active=True)
    
    @staticmethod
    async def deactivate(bot_id: int) -> Optional[Bot]:
        """Deactivate bot"""
        return await BotManager.update(bot_id, is_active=False)
    
    @staticmethod
    async def delete(bot_id: int) -> bool:
        """Delete bot"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import delete
            result = await session.execute(
                delete(Bot).where(Bot.id == bot_id)
            )
            return result.rowcount > 0
    
    @staticmethod
    async def increment_stats(
        bot_id: int,
        is_win: bool,
        pnl: float = 0
    ):
        """Increment bot statistics"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Bot).where(Bot.id == bot_id)
            )
            bot = result.scalar_one_or_none()
            
            if bot:
                bot.total_signals += 1
                if is_win:
                    bot.total_wins += 1
                else:
                    bot.total_losses += 1
                bot.total_profit += pnl
                bot.last_signal_at = datetime.utcnow()


class SignalManager:
    """CRUD operations for Signals"""
    
    @staticmethod
    async def create(
        bot_id: int,
        symbol: str,
        timeframe: str,
        direction: str,
        entry_price: float,
        stop_loss: float = None,
        take_profits: List[Dict] = None,
        indicator_values: Dict = None
    ) -> Signal:
        """Create new signal"""
        async with DatabaseManager.session() as session:
            signal = Signal(
                bot_id=bot_id,
                symbol=symbol,
                timeframe=timeframe,
                direction=direction,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profits=take_profits,
                indicator_values=indicator_values,
                status="pending"
            )
            session.add(signal)
            await session.flush()
            return signal
    
    @staticmethod
    async def get(signal_id: int) -> Optional[Signal]:
        """Get signal by ID"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Signal).where(Signal.id == signal_id)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_active_by_bot(bot_id: int) -> List[Signal]:
        """Get active signals for a bot"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Signal)
                .where(Signal.bot_id == bot_id)
                .where(Signal.status.in_(["pending", "active"]))
                .order_by(Signal.created_at.desc())
            )
            return list(result.scalars().all())
    
    @staticmethod
    async def close(
        signal_id: int,
        exit_price: float,
        exit_reason: str,
        pnl_percent: float = None,
        pnl_amount: float = None
    ) -> Optional[Signal]:
        """Close signal"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(Signal).where(Signal.id == signal_id)
            )
            signal = result.scalar_one_or_none()
            
            if signal:
                signal.status = "closed"
                signal.exit_price = exit_price
                signal.exit_reason = exit_reason
                signal.pnl_percent = pnl_percent
                signal.pnl_amount = pnl_amount
                signal.closed_at = datetime.utcnow()
            
            return signal
    
    @staticmethod
    async def list_recent(
        bot_id: int = None,
        symbol: str = None,
        limit: int = 100
    ) -> List[Signal]:
        """List recent signals"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            query = select(Signal).order_by(Signal.created_at.desc())
            
            if bot_id:
                query = query.where(Signal.bot_id == bot_id)
            if symbol:
                query = query.where(Signal.symbol == symbol)
            
            query = query.limit(limit)
            result = await session.execute(query)
            return list(result.scalars().all())


class DataCacheManager:
    """CRUD operations for DataCacheInfo"""
    
    @staticmethod
    async def upsert(
        symbol: str,
        timeframe: str,
        source: str = "binance",
        filename: str = None,
        filepath: str = None,
        **kwargs
    ) -> DataCacheInfo:
        """Create or update data cache info"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            
            # Try to find existing
            result = await session.execute(
                select(DataCacheInfo)
                .where(DataCacheInfo.symbol == symbol)
                .where(DataCacheInfo.timeframe == timeframe)
                .where(DataCacheInfo.source == source)
            )
            cache_info = result.scalar_one_or_none()
            
            if cache_info:
                # Update existing
                cache_info.filename = filename or cache_info.filename
                cache_info.filepath = filepath or cache_info.filepath
                for key, value in kwargs.items():
                    if hasattr(cache_info, key):
                        setattr(cache_info, key, value)
            else:
                # Create new
                cache_info = DataCacheInfo(
                    symbol=symbol,
                    timeframe=timeframe,
                    source=source,
                    filename=filename or f"{symbol}_{timeframe}.parquet",
                    filepath=filepath or str(DB_DIR / f"{symbol}_{timeframe}.parquet"),
                    **kwargs
                )
                session.add(cache_info)
            
            await session.flush()
            return cache_info
    
    @staticmethod
    async def get(symbol: str, timeframe: str, source: str = "binance") -> Optional[DataCacheInfo]:
        """Get cache info"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(DataCacheInfo)
                .where(DataCacheInfo.symbol == symbol)
                .where(DataCacheInfo.timeframe == timeframe)
                .where(DataCacheInfo.source == source)
            )
            return result.scalar_one_or_none()
    
    @staticmethod
    async def list_all(source: str = None) -> List[DataCacheInfo]:
        """List all cached data"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import select
            query = select(DataCacheInfo).order_by(DataCacheInfo.updated_at.desc())
            
            if source:
                query = query.where(DataCacheInfo.source == source)
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    @staticmethod
    async def delete(symbol: str, timeframe: str, source: str = "binance") -> bool:
        """Delete cache info"""
        async with DatabaseManager.session() as session:
            from sqlalchemy import delete
            result = await session.execute(
                delete(DataCacheInfo)
                .where(DataCacheInfo.symbol == symbol)
                .where(DataCacheInfo.timeframe == timeframe)
                .where(DataCacheInfo.source == source)
            )
            return result.rowcount > 0


# ============ INITIALIZATION ============

def init_db(echo: bool = False):
    """Initialize database (call on startup)"""
    return DatabaseManager.initialize(echo=echo)


async def close_db():
    """Close database connections (call on shutdown)"""
    await DatabaseManager.close()


# ============ DEFAULT SETTINGS ============

async def create_default_settings():
    """Create default settings if not exist"""
    defaults = {
        "app.name": ("Komas Trading Server", "Application name"),
        "app.version": ("3.5", "Application version"),
        "data.default_symbol": ("BTCUSDT", "Default trading symbol"),
        "data.default_timeframe": ("1h", "Default timeframe"),
        "data.history_days": (365, "Days of history to download"),
        "optimization.workers": (0, "Number of workers (0 = auto)"),
        "optimization.max_combinations": (10000, "Max combinations to test"),
        "telegram.enabled": (False, "Enable Telegram notifications"),
        "telegram.bot_token": ("", "Telegram bot token"),
        "telegram.default_chat_id": ("", "Default Telegram chat ID"),
    }
    
    for key, (value, description) in defaults.items():
        existing = await SettingsManager.get(key)
        if existing is None:
            await SettingsManager.set(key, value, description)
            logger.info(f"Created default setting: {key}")


# ============ EXPORT ============

__all__ = [
    # Models
    "Base",
    "Settings",
    "Preset",
    "Bot",
    "Signal",
    "OptimizationResult",
    "DataCacheInfo",
    
    # Managers
    "DatabaseManager",
    "SettingsManager",
    "PresetManager",
    "BotManager",
    "SignalManager",
    "DataCacheManager",
    
    # Functions
    "init_db",
    "close_db",
    "create_default_settings",
    
    # Constants
    "DB_PATH",
    "SQLITE_URL",
    "SQLITE_ASYNC_URL",
]
