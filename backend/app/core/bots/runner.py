"""
Komas Trading Server - Bots Runner
==================================
Strategy execution engine with APScheduler for 24/7 monitoring
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Callable
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import threading
import traceback

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore

from .models import (
    Bot, BotStatus, Position, PositionStatus, SignalDirection,
    SignalEvent, StrategyConfig, BotSymbolConfig
)
from .manager import get_bots_manager, BotsManager

logger = logging.getLogger(__name__)


# ============ TIMEFRAME INTERVALS ============

TIMEFRAME_SECONDS = {
    "1m": 60,
    "3m": 180,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "2h": 7200,
    "4h": 14400,
    "6h": 21600,
    "8h": 28800,
    "12h": 43200,
    "1d": 86400,
    "3d": 259200,
    "1w": 604800,
}


# ============ SIGNAL CALCULATOR ============

def calculate_trg_signal(
    ohlcv_data: List[Dict],
    atr_length: int,
    multiplier: float,
    filters_config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """
    Calculate TRG indicator signal from OHLCV data.
    Returns signal dict or None if no signal.
    
    This function can run in a separate process for CPU-intensive calculations.
    """
    import pandas as pd
    import numpy as np
    
    if not ohlcv_data or len(ohlcv_data) < atr_length + 10:
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(ohlcv_data)
    
    # Calculate ATR
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=atr_length).mean()
    
    # Calculate TRG bands
    hl2 = (high + low) / 2
    upper_band = hl2 + (multiplier * atr)
    lower_band = hl2 - (multiplier * atr)
    
    # Determine trend
    trend = pd.Series(index=df.index, dtype=float)
    trend.iloc[0] = 1  # Start with uptrend
    
    for i in range(1, len(df)):
        if close.iloc[i] > upper_band.iloc[i-1]:
            trend.iloc[i] = 1  # Uptrend
        elif close.iloc[i] < lower_band.iloc[i-1]:
            trend.iloc[i] = -1  # Downtrend
        else:
            trend.iloc[i] = trend.iloc[i-1]  # Continue previous trend
    
    # Get current and previous trend
    current_trend = trend.iloc[-1]
    prev_trend = trend.iloc[-2]
    
    signal = None
    
    # Detect signal change
    if current_trend != prev_trend:
        if current_trend == 1:
            signal = {
                "direction": "long",
                "price": float(close.iloc[-1]),
                "atr": float(atr.iloc[-1]),
                "upper_band": float(upper_band.iloc[-1]),
                "lower_band": float(lower_band.iloc[-1])
            }
        else:
            signal = {
                "direction": "short",
                "price": float(close.iloc[-1]),
                "atr": float(atr.iloc[-1]),
                "upper_band": float(upper_band.iloc[-1]),
                "lower_band": float(lower_band.iloc[-1])
            }
    
    # Apply filters if signal detected
    if signal and filters_config:
        # SuperTrend filter
        if filters_config.get("use_supertrend"):
            st_period = filters_config.get("supertrend_period", 10)
            st_mult = filters_config.get("supertrend_multiplier", 3.0)
            
            st_atr = tr.rolling(window=st_period).mean()
            st_upper = hl2 + (st_mult * st_atr)
            st_lower = hl2 - (st_mult * st_atr)
            
            st_trend = 1 if close.iloc[-1] > st_lower.iloc[-1] else -1
            
            if signal["direction"] == "long" and st_trend != 1:
                signal = None  # Filtered out
            elif signal["direction"] == "short" and st_trend != -1:
                signal = None
        
        # RSI filter
        if signal and filters_config.get("use_rsi"):
            rsi_period = filters_config.get("rsi_period", 14)
            rsi_ob = filters_config.get("rsi_overbought", 70)
            rsi_os = filters_config.get("rsi_oversold", 30)
            
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current_rsi = rsi.iloc[-1]
            
            if signal["direction"] == "long" and current_rsi > rsi_ob:
                signal = None  # Overbought, don't go long
            elif signal["direction"] == "short" and current_rsi < rsi_os:
                signal = None  # Oversold, don't go short
            
            if signal:
                signal["rsi"] = float(current_rsi)
        
        # ADX filter
        if signal and filters_config.get("use_adx"):
            adx_period = filters_config.get("adx_period", 14)
            adx_threshold = filters_config.get("adx_threshold", 25)
            
            plus_dm = high.diff()
            minus_dm = -low.diff()
            plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
            minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
            
            atr_adx = tr.rolling(window=adx_period).mean()
            plus_di = 100 * (plus_dm.rolling(window=adx_period).mean() / atr_adx)
            minus_di = 100 * (minus_dm.rolling(window=adx_period).mean() / atr_adx)
            
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
            adx = dx.rolling(window=adx_period).mean()
            
            current_adx = adx.iloc[-1]
            
            if current_adx < adx_threshold:
                signal = None  # Weak trend, no trade
            
            if signal:
                signal["adx"] = float(current_adx)
        
        # Volume filter
        if signal and filters_config.get("use_volume"):
            vol_mult = filters_config.get("volume_multiplier", 1.5)
            
            volume = df['volume']
            avg_volume = volume.rolling(window=20).mean()
            current_volume = volume.iloc[-1]
            
            if current_volume < avg_volume.iloc[-1] * vol_mult:
                signal = None  # Low volume
            
            if signal:
                signal["volume_ratio"] = float(current_volume / avg_volume.iloc[-1])
    
    return signal


# ============ BOTS RUNNER ============

class BotsRunner:
    """
    Executes trading strategies for all running bots.
    Uses APScheduler for 24/7 monitoring.
    """
    
    def __init__(self):
        self.manager: BotsManager = get_bots_manager()
        
        # APScheduler - AsyncIOScheduler handles async functions natively
        self.scheduler = AsyncIOScheduler(
            jobstores={'default': MemoryJobStore()},
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 60
            }
        )
        
        # Process pool for CPU-intensive calculations
        self.process_pool = ProcessPoolExecutor(max_workers=4)
        
        # Thread pool for I/O operations
        self.thread_pool = ThreadPoolExecutor(max_workers=10)
        
        # State
        self._running = False
        self._jobs: Dict[str, str] = {}  # bot_id -> job_id
        
        # Callbacks for notifications
        self._signal_callbacks: List[Callable] = []
        self._trade_callbacks: List[Callable] = []
        
        # Data fetcher (will be set externally)
        self._data_fetcher: Optional[Callable] = None
        
        logger.info("BotsRunner initialized")
    
    def set_data_fetcher(self, fetcher: Callable):
        """Set the function to fetch OHLCV data"""
        self._data_fetcher = fetcher
    
    def add_signal_callback(self, callback: Callable):
        """Add callback for new signals"""
        self._signal_callbacks.append(callback)
    
    def add_trade_callback(self, callback: Callable):
        """Add callback for trades"""
        self._trade_callbacks.append(callback)
    
    # ============ SCHEDULER CONTROL ============
    
    def start(self):
        """Start the scheduler"""
        if self._running:
            logger.warning("BotsRunner already running")
            return
        
        self.scheduler.start()
        self._running = True
        
        # Schedule monitoring job for all bots
        self.scheduler.add_job(
            self._monitor_bots,
            trigger=IntervalTrigger(seconds=10),
            id="monitor_bots",
            name="Monitor Running Bots",
            replace_existing=True
        )
        
        # Schedule statistics update
        self.scheduler.add_job(
            self._update_all_statistics,
            trigger=IntervalTrigger(minutes=5),
            id="update_statistics",
            name="Update Statistics",
            replace_existing=True
        )
        
        logger.info("BotsRunner started")
    
    def stop(self):
        """Stop the scheduler"""
        if not self._running:
            return
        
        self.scheduler.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)
        self.thread_pool.shutdown(wait=True)
        
        self._running = False
        logger.info("BotsRunner stopped")
    
    def is_running(self) -> bool:
        """Check if runner is active"""
        return self._running
    
    # ============ BOT MONITORING ============
    
    async def _monitor_bots(self):
        """Monitor all running bots and schedule strategy execution"""
        try:
            running_bots = self.manager.get_running_bots()
            
            for bot in running_bots:
                # Check if job already exists for this bot
                job_id = f"bot_{bot.id}"
                
                if job_id not in self._jobs:
                    # Schedule new job for this bot
                    await self._schedule_bot_job(bot)
                    self._jobs[job_id] = job_id
            
            # Remove jobs for stopped bots
            active_bot_ids = {f"bot_{b.id}" for b in running_bots}
            for job_id in list(self._jobs.keys()):
                if job_id not in active_bot_ids:
                    try:
                        self.scheduler.remove_job(job_id)
                    except:
                        pass
                    del self._jobs[job_id]
                    
        except Exception as e:
            logger.error(f"Error in bot monitoring: {e}")
            logger.error(traceback.format_exc())
    
    async def _schedule_bot_job(self, bot: Bot):
        """Schedule strategy execution job for a bot"""
        try:
            # Get minimum timeframe from symbols
            min_interval = min(
                TIMEFRAME_SECONDS.get(s.timeframe, 3600)
                for s in bot.config.symbols
            )
            
            # Schedule at interval (with some buffer)
            job_id = f"bot_{bot.id}"
            
            self.scheduler.add_job(
                self._execute_bot_strategy,
                trigger=IntervalTrigger(seconds=min_interval),
                id=job_id,
                name=f"Strategy: {bot.config.name}",
                args=[bot.id],
                replace_existing=True
            )
            
            logger.info(f"Scheduled bot {bot.config.name} ({bot.id}) every {min_interval}s")
            
        except Exception as e:
            logger.error(f"Error scheduling bot {bot.id}: {e}")
    
    # ============ STRATEGY EXECUTION ============
    
    async def _execute_bot_strategy(self, bot_id: str):
        """Execute strategy for a single bot"""
        try:
            bot = self.manager.get_bot(bot_id)
            if not bot or bot.status != BotStatus.RUNNING:
                return
            
            logger.debug(f"Executing strategy for bot {bot.config.name}")
            
            # Check trading hours
            if not self._is_trading_time(bot):
                logger.debug(f"Bot {bot.config.name} outside trading hours")
                return
            
            # Process each symbol
            for symbol_config in bot.config.symbols:
                if not symbol_config.enabled:
                    continue
                
                try:
                    await self._process_symbol(bot, symbol_config)
                except Exception as e:
                    logger.error(f"Error processing {symbol_config.symbol}: {e}")
                    logger.error(traceback.format_exc())
            
            bot.updated_at = datetime.now()
            
        except Exception as e:
            logger.error(f"Error executing strategy for bot {bot_id}: {e}")
            logger.error(traceback.format_exc())
            self.manager.set_bot_error(bot_id, str(e))
    
    async def _process_symbol(self, bot: Bot, symbol_config: BotSymbolConfig):
        """Process a single symbol for a bot"""
        symbol = symbol_config.symbol
        timeframe = symbol_config.timeframe
        
        # Fetch OHLCV data
        if not self._data_fetcher:
            logger.warning("No data fetcher configured")
            return
        
        ohlcv_data = await self._fetch_data(symbol, timeframe)
        if not ohlcv_data:
            logger.warning(f"No data for {symbol} {timeframe}")
            return
        
        # Prepare filters config
        filters_config = {
            "use_supertrend": bot.config.strategy.use_supertrend,
            "supertrend_period": bot.config.strategy.supertrend_period,
            "supertrend_multiplier": bot.config.strategy.supertrend_multiplier,
            "use_rsi": bot.config.strategy.use_rsi,
            "rsi_period": bot.config.strategy.rsi_period,
            "rsi_overbought": bot.config.strategy.rsi_overbought,
            "rsi_oversold": bot.config.strategy.rsi_oversold,
            "use_adx": bot.config.strategy.use_adx,
            "adx_period": bot.config.strategy.adx_period,
            "adx_threshold": bot.config.strategy.adx_threshold,
            "use_volume": bot.config.strategy.use_volume,
            "volume_multiplier": bot.config.strategy.volume_multiplier,
        }
        
        # Calculate signal in process pool
        loop = asyncio.get_event_loop()
        signal = await loop.run_in_executor(
            self.process_pool,
            calculate_trg_signal,
            ohlcv_data,
            bot.config.strategy.atr_length,
            bot.config.strategy.multiplier,
            filters_config
        )
        
        if signal:
            await self._process_signal(bot, symbol_config, signal)
        
        # Check existing positions for TP/SL
        await self._check_positions(bot, symbol, ohlcv_data[-1] if ohlcv_data else None)
    
    async def _fetch_data(self, symbol: str, timeframe: str) -> List[Dict]:
        """Fetch OHLCV data for a symbol"""
        try:
            if callable(self._data_fetcher):
                # Async fetcher
                if asyncio.iscoroutinefunction(self._data_fetcher):
                    return await self._data_fetcher(symbol, timeframe)
                else:
                    # Sync fetcher - run in thread pool
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(
                        self.thread_pool,
                        self._data_fetcher,
                        symbol, timeframe
                    )
            return []
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return []
    
    async def _process_signal(
        self, 
        bot: Bot, 
        symbol_config: BotSymbolConfig, 
        signal: Dict[str, Any]
    ):
        """Process a new trading signal"""
        symbol = symbol_config.symbol
        direction = SignalDirection(signal["direction"])
        price = signal["price"]
        
        # Check for existing position in same direction
        existing = None
        for pos in bot.open_positions:
            if pos.symbol == symbol:
                existing = pos
                break
        
        if existing:
            if existing.direction == direction:
                # Same direction, ignore
                return
            else:
                # Opposite direction, close existing first
                await self._close_position_on_signal(bot, existing, price)
        
        # Check re-entry rules
        if not self._can_open_position(bot, symbol):
            logger.debug(f"Bot {bot.config.name}: Re-entry not allowed for {symbol}")
            return
        
        # Calculate position size
        allocation = symbol_config.allocation_percent / 100
        position_value = bot.current_capital * allocation
        position_size = position_value / price
        
        # Create position
        position = Position(
            bot_id=bot.id,
            symbol=symbol,
            direction=direction,
            entry_price=price,
            entry_time=datetime.now(),
            entry_size=position_size,
            entry_value=position_value
        )
        
        # Open position
        self.manager.open_position(bot.id, position)
        
        # Update signal time
        bot.last_signal_time = datetime.now()
        
        # Create signal event
        event = SignalEvent(
            bot_id=bot.id,
            symbol=symbol,
            timeframe=symbol_config.timeframe,
            direction=direction,
            price=price,
            indicator_values=signal
        )
        
        # Trigger callbacks
        for callback in self._signal_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Signal callback error: {e}")
        
        logger.info(f"Bot {bot.config.name}: Opened {direction.value} {symbol} @ {price}")
    
    async def _close_position_on_signal(self, bot: Bot, position: Position, price: float):
        """Close position due to opposite signal"""
        self.manager.close_position(
            bot.id,
            position.id,
            exit_price=price,
            exit_reason="signal_change"
        )
        
        logger.info(f"Bot {bot.config.name}: Closed {position.symbol} on signal change @ {price}")
    
    async def _check_positions(self, bot: Bot, symbol: str, current_candle: Dict):
        """Check positions for TP/SL"""
        if not current_candle:
            return
        
        current_price = current_candle.get("close", 0)
        high_price = current_candle.get("high", current_price)
        low_price = current_candle.get("low", current_price)
        
        for position in list(bot.open_positions):
            if position.symbol != symbol:
                continue
            
            # Update current price
            self.manager.update_position_price(bot.id, position.id, current_price)
            
            # Check stop loss
            sl_price = self._calculate_sl_price(bot, position)
            if self._is_sl_hit(position, low_price, high_price, sl_price):
                self.manager.close_position(
                    bot.id,
                    position.id,
                    exit_price=sl_price,
                    exit_reason="sl"
                )
                logger.info(f"Bot {bot.config.name}: SL hit for {symbol} @ {sl_price}")
                continue
            
            # Check take profits
            await self._check_take_profits(bot, position, high_price, low_price)
    
    def _calculate_sl_price(self, bot: Bot, position: Position) -> float:
        """Calculate stop loss price based on mode"""
        strategy = bot.config.strategy
        sl_percent = strategy.sl_percent / 100
        
        if position.direction == SignalDirection.LONG:
            base_sl = position.entry_price * (1 - sl_percent)
            
            if strategy.sl_mode.value == "breakeven" and position.tp_levels_hit:
                # Move SL to breakeven after first TP
                return position.entry_price
            elif strategy.sl_mode.value == "cascade" and position.tp_levels_hit:
                # Move SL to last TP level
                last_tp = max(position.tp_levels_hit)
                tp_config = next(
                    (tp for tp in strategy.take_profits if tp.level == last_tp),
                    None
                )
                if tp_config:
                    return position.entry_price * (1 + tp_config.percent / 100 * 0.5)
            
            return base_sl
        else:
            base_sl = position.entry_price * (1 + sl_percent)
            
            if strategy.sl_mode.value == "breakeven" and position.tp_levels_hit:
                return position.entry_price
            elif strategy.sl_mode.value == "cascade" and position.tp_levels_hit:
                last_tp = max(position.tp_levels_hit)
                tp_config = next(
                    (tp for tp in strategy.take_profits if tp.level == last_tp),
                    None
                )
                if tp_config:
                    return position.entry_price * (1 - tp_config.percent / 100 * 0.5)
            
            return base_sl
    
    def _is_sl_hit(
        self, 
        position: Position, 
        low: float, 
        high: float, 
        sl_price: float
    ) -> bool:
        """Check if stop loss is hit"""
        if position.direction == SignalDirection.LONG:
            return low <= sl_price
        else:
            return high >= sl_price
    
    async def _check_take_profits(
        self, 
        bot: Bot, 
        position: Position, 
        high: float, 
        low: float
    ):
        """Check and execute take profit levels"""
        strategy = bot.config.strategy
        
        for tp in strategy.take_profits[:strategy.tp_count]:
            if tp.level in position.tp_levels_hit:
                continue
            
            if tp.amount <= 0:
                continue
            
            # Calculate TP price
            if position.direction == SignalDirection.LONG:
                tp_price = position.entry_price * (1 + tp.percent / 100)
                hit = high >= tp_price
            else:
                tp_price = position.entry_price * (1 - tp.percent / 100)
                hit = low <= tp_price
            
            if hit:
                position.tp_levels_hit.append(tp.level)
                
                # Partial close
                self.manager.close_position(
                    bot.id,
                    position.id,
                    exit_price=tp_price,
                    exit_reason=f"tp{tp.level}",
                    partial_percent=tp.amount
                )
                
                logger.info(
                    f"Bot {bot.config.name}: TP{tp.level} hit for {position.symbol} @ {tp_price}"
                )
                
                # Trigger callbacks
                for callback in self._trade_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback({
                                "bot_id": bot.id,
                                "symbol": position.symbol,
                                "type": "tp_hit",
                                "level": tp.level,
                                "price": tp_price
                            })
                        else:
                            callback({
                                "bot_id": bot.id,
                                "symbol": position.symbol,
                                "type": "tp_hit",
                                "level": tp.level,
                                "price": tp_price
                            })
                    except Exception as e:
                        logger.error(f"Trade callback error: {e}")
    
    def _can_open_position(self, bot: Bot, symbol: str) -> bool:
        """Check if we can open a new position"""
        strategy = bot.config.strategy
        
        if not strategy.allow_reentry:
            # Check if we had a recent position
            for pos in bot.closed_positions[-10:]:
                if pos.symbol == symbol:
                    if pos.exit_reason == "sl" and not strategy.reentry_after_sl:
                        return False
                    if pos.exit_reason and pos.exit_reason.startswith("tp") and not strategy.reentry_after_tp:
                        return False
        
        return True
    
    def _is_trading_time(self, bot: Bot) -> bool:
        """Check if current time is within trading hours"""
        now = datetime.now()
        
        # Check day of week (0 = Monday)
        if now.weekday() not in bot.config.active_days:
            return False
        
        # Check hours
        hour = now.hour
        start = bot.config.active_hours_start
        end = bot.config.active_hours_end
        
        if start <= end:
            return start <= hour <= end
        else:
            # Overnight range (e.g., 22-06)
            return hour >= start or hour <= end
    
    # ============ STATISTICS ============
    
    async def _update_all_statistics(self):
        """Periodically update statistics for all bots"""
        try:
            for bot in self.manager.get_all_bots():
                if bot.statistics:
                    bot.statistics.updated_at = datetime.now()
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    # ============ MANUAL OPERATIONS ============
    
    async def force_check(self, bot_id: str):
        """Force immediate strategy check for a bot"""
        await self._execute_bot_strategy(bot_id)
    
    async def manual_close_position(
        self, 
        bot_id: str, 
        position_id: str, 
        exit_price: float,
        partial_percent: Optional[float] = None
    ):
        """Manually close a position"""
        return self.manager.close_position(
            bot_id,
            position_id,
            exit_price=exit_price,
            exit_reason="manual",
            partial_percent=partial_percent
        )


# Global instance
_runner: Optional[BotsRunner] = None


def get_bots_runner() -> BotsRunner:
    """Get global bots runner instance"""
    global _runner
    if _runner is None:
        _runner = BotsRunner()
    return _runner
