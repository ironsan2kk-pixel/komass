"""
Komas Trading Server - Bots Manager
===================================
CRUD operations and state management for trading bots
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import threading
import copy

from .models import (
    Bot, BotConfig, BotStatus, BotCreate, BotUpdate,
    BotStatistics, Position, PositionStatus, SignalDirection,
    EquityCurve, EquityPoint, BotLogEntry
)

logger = logging.getLogger(__name__)


class BotsManager:
    """
    Manages trading bots lifecycle:
    - CRUD operations (Create, Read, Update, Delete)
    - State persistence (JSON file storage)
    - Statistics calculation
    - Position tracking
    """
    
    def __init__(self, data_dir: str = "data/bots"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Bot storage
        self._bots: Dict[str, Bot] = {}
        self._equity_curves: Dict[str, EquityCurve] = {}
        self._logs: Dict[str, List[BotLogEntry]] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Files
        self._bots_file = self.data_dir / "bots.json"
        self._positions_file = self.data_dir / "positions.json"
        
        # Load existing data
        self._load_bots()
        
        logger.info(f"BotsManager initialized with {len(self._bots)} bots")
    
    # ============ PERSISTENCE ============
    
    def _load_bots(self):
        """Load bots from JSON file"""
        if self._bots_file.exists():
            try:
                with open(self._bots_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for bot_data in data.get('bots', []):
                    try:
                        bot = Bot.model_validate(bot_data)
                        self._bots[bot.id] = bot
                        self._equity_curves[bot.id] = EquityCurve(bot_id=bot.id)
                        self._logs[bot.id] = []
                        logger.debug(f"Loaded bot: {bot.config.name} ({bot.id})")
                    except Exception as e:
                        logger.error(f"Failed to load bot: {e}")
                
                logger.info(f"Loaded {len(self._bots)} bots from storage")
                
            except Exception as e:
                logger.error(f"Failed to load bots file: {e}")
    
    def _save_bots(self):
        """Save bots to JSON file"""
        try:
            data = {
                'bots': [bot.model_dump(mode='json') for bot in self._bots.values()],
                'updated_at': datetime.now().isoformat()
            }
            
            with open(self._bots_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.debug(f"Saved {len(self._bots)} bots to storage")
            
        except Exception as e:
            logger.error(f"Failed to save bots: {e}")
    
    # ============ CRUD OPERATIONS ============
    
    def create_bot(self, create_request: BotCreate) -> Bot:
        """Create a new bot"""
        with self._lock:
            # Validate name uniqueness
            for bot in self._bots.values():
                if bot.config.name.lower() == create_request.config.name.lower():
                    raise ValueError(f"Bot with name '{create_request.config.name}' already exists")
            
            # Create bot
            bot = Bot(config=create_request.config)
            
            # Initialize statistics
            bot.statistics = BotStatistics(
                bot_id=bot.id,
                current_capital=bot.config.initial_capital,
                equity_peak=bot.config.initial_capital
            )
            
            # Store
            self._bots[bot.id] = bot
            self._equity_curves[bot.id] = EquityCurve(bot_id=bot.id)
            self._logs[bot.id] = []
            
            # Initial equity point
            self._equity_curves[bot.id].add_point(
                equity=bot.config.initial_capital,
                position_count=0
            )
            
            # Log
            self._add_log(bot.id, "info", "Bot created", {
                "name": bot.config.name,
                "capital": bot.config.initial_capital,
                "symbols": [s.symbol for s in bot.config.symbols]
            })
            
            # Save
            self._save_bots()
            
            logger.info(f"Created bot: {bot.config.name} ({bot.id})")
            return bot
    
    def get_bot(self, bot_id: str) -> Optional[Bot]:
        """Get bot by ID"""
        return self._bots.get(bot_id)
    
    def get_all_bots(self) -> List[Bot]:
        """Get all bots"""
        return list(self._bots.values())
    
    def get_running_bots(self) -> List[Bot]:
        """Get all running bots"""
        return [b for b in self._bots.values() if b.status == BotStatus.RUNNING]
    
    def update_bot(self, bot_id: str, update: BotUpdate) -> Optional[Bot]:
        """Update bot configuration"""
        with self._lock:
            bot = self._bots.get(bot_id)
            if not bot:
                return None
            
            # Can only update stopped bots
            if bot.status == BotStatus.RUNNING:
                raise ValueError("Cannot update running bot. Stop it first.")
            
            # Apply updates
            if update.name is not None:
                bot.config.name = update.name
            if update.description is not None:
                bot.config.description = update.description
            if update.symbols is not None:
                bot.config.symbols = update.symbols
            if update.strategy is not None:
                bot.config.strategy = update.strategy
            if update.notify_signals is not None:
                bot.config.notify_signals = update.notify_signals
            if update.notify_tp_hit is not None:
                bot.config.notify_tp_hit = update.notify_tp_hit
            if update.notify_sl_hit is not None:
                bot.config.notify_sl_hit = update.notify_sl_hit
            
            bot.updated_at = datetime.now()
            
            self._add_log(bot_id, "info", "Bot configuration updated")
            self._save_bots()
            
            logger.info(f"Updated bot: {bot.config.name} ({bot_id})")
            return bot
    
    def delete_bot(self, bot_id: str) -> bool:
        """Delete a bot"""
        with self._lock:
            bot = self._bots.get(bot_id)
            if not bot:
                return False
            
            # Can only delete stopped bots
            if bot.status == BotStatus.RUNNING:
                raise ValueError("Cannot delete running bot. Stop it first.")
            
            # Remove
            del self._bots[bot_id]
            if bot_id in self._equity_curves:
                del self._equity_curves[bot_id]
            if bot_id in self._logs:
                del self._logs[bot_id]
            
            self._save_bots()
            
            logger.info(f"Deleted bot: {bot.config.name} ({bot_id})")
            return True
    
    # ============ BOT CONTROL ============
    
    def start_bot(self, bot_id: str) -> Optional[Bot]:
        """Start a bot"""
        with self._lock:
            bot = self._bots.get(bot_id)
            if not bot:
                return None
            
            if bot.status == BotStatus.RUNNING:
                logger.warning(f"Bot {bot_id} is already running")
                return bot
            
            bot.status = BotStatus.RUNNING
            bot.started_at = datetime.now()
            bot.stopped_at = None
            bot.error_count = 0
            bot.last_error = None
            bot.updated_at = datetime.now()
            
            self._add_log(bot_id, "info", "Bot started")
            self._save_bots()
            
            logger.info(f"Started bot: {bot.config.name} ({bot_id})")
            return bot
    
    def stop_bot(self, bot_id: str) -> Optional[Bot]:
        """Stop a bot"""
        with self._lock:
            bot = self._bots.get(bot_id)
            if not bot:
                return None
            
            if bot.status == BotStatus.STOPPED:
                logger.warning(f"Bot {bot_id} is already stopped")
                return bot
            
            bot.status = BotStatus.STOPPED
            bot.stopped_at = datetime.now()
            bot.updated_at = datetime.now()
            
            self._add_log(bot_id, "info", "Bot stopped")
            self._save_bots()
            
            logger.info(f"Stopped bot: {bot.config.name} ({bot_id})")
            return bot
    
    def pause_bot(self, bot_id: str) -> Optional[Bot]:
        """Pause a bot (keeps positions, stops new trades)"""
        with self._lock:
            bot = self._bots.get(bot_id)
            if not bot:
                return None
            
            if bot.status != BotStatus.RUNNING:
                raise ValueError("Can only pause running bots")
            
            bot.status = BotStatus.PAUSED
            bot.updated_at = datetime.now()
            
            self._add_log(bot_id, "info", "Bot paused")
            self._save_bots()
            
            logger.info(f"Paused bot: {bot.config.name} ({bot_id})")
            return bot
    
    def resume_bot(self, bot_id: str) -> Optional[Bot]:
        """Resume a paused bot"""
        with self._lock:
            bot = self._bots.get(bot_id)
            if not bot:
                return None
            
            if bot.status != BotStatus.PAUSED:
                raise ValueError("Can only resume paused bots")
            
            bot.status = BotStatus.RUNNING
            bot.updated_at = datetime.now()
            
            self._add_log(bot_id, "info", "Bot resumed")
            self._save_bots()
            
            logger.info(f"Resumed bot: {bot.config.name} ({bot_id})")
            return bot
    
    def set_bot_error(self, bot_id: str, error: str):
        """Set bot to error state"""
        with self._lock:
            bot = self._bots.get(bot_id)
            if not bot:
                return
            
            bot.status = BotStatus.ERROR
            bot.last_error = error
            bot.error_count += 1
            bot.updated_at = datetime.now()
            
            self._add_log(bot_id, "error", f"Bot error: {error}")
            self._save_bots()
            
            logger.error(f"Bot {bot_id} error: {error}")
    
    # ============ POSITIONS ============
    
    def open_position(self, bot_id: str, position: Position) -> Optional[Position]:
        """Add an open position to bot"""
        with self._lock:
            bot = self._bots.get(bot_id)
            if not bot:
                return None
            
            position.bot_id = bot_id
            bot.open_positions.append(position)
            bot.last_trade_time = datetime.now()
            bot.updated_at = datetime.now()
            
            self._add_log(bot_id, "trade", f"Opened {position.direction.value} position", {
                "symbol": position.symbol,
                "entry_price": position.entry_price,
                "size": position.entry_size
            })
            
            self._save_bots()
            
            logger.info(f"Bot {bot_id}: Opened {position.direction.value} {position.symbol} @ {position.entry_price}")
            return position
    
    def close_position(
        self, 
        bot_id: str, 
        position_id: str, 
        exit_price: float,
        exit_reason: str = "manual",
        partial_percent: Optional[float] = None
    ) -> Optional[Position]:
        """Close a position (fully or partially)"""
        with self._lock:
            bot = self._bots.get(bot_id)
            if not bot:
                return None
            
            # Find position
            position = None
            position_idx = None
            for idx, pos in enumerate(bot.open_positions):
                if pos.id == position_id:
                    position = pos
                    position_idx = idx
                    break
            
            if not position:
                logger.warning(f"Position {position_id} not found in bot {bot_id}")
                return None
            
            # Calculate PnL
            if position.direction == SignalDirection.LONG:
                pnl_percent = (exit_price - position.entry_price) / position.entry_price * 100
            else:
                pnl_percent = (position.entry_price - exit_price) / position.entry_price * 100
            
            pnl_percent *= bot.config.leverage
            
            # Partial or full close
            if partial_percent and partial_percent < 100:
                # Partial close
                close_size = position.remaining_size * (partial_percent / 100)
                close_value = close_size * exit_price
                position.remaining_size -= close_size
                
                pnl = close_value * (pnl_percent / 100)
                commission = close_value * (bot.config.commission_percent / 100)
                
                position.realized_pnl += pnl - commission
                position.commission_paid += commission
                position.status = PositionStatus.PARTIALLY_CLOSED
                position.updated_at = datetime.now()
                
                # Update capital
                bot.current_capital += pnl - commission
                
                self._add_log(bot_id, "trade", f"Partially closed position ({partial_percent}%)", {
                    "symbol": position.symbol,
                    "exit_price": exit_price,
                    "pnl": pnl - commission,
                    "reason": exit_reason
                })
                
            else:
                # Full close
                close_value = position.remaining_size * exit_price
                pnl = close_value * (pnl_percent / 100)
                commission = close_value * (bot.config.commission_percent / 100)
                
                position.exit_price = exit_price
                position.exit_time = datetime.now()
                position.exit_reason = exit_reason
                position.realized_pnl += pnl - commission
                position.realized_pnl_percent = pnl_percent - (bot.config.commission_percent * 2)
                position.commission_paid += commission
                position.status = PositionStatus.CLOSED
                position.remaining_size = 0
                position.updated_at = datetime.now()
                
                # Move to closed
                bot.open_positions.pop(position_idx)
                bot.closed_positions.append(position)
                
                # Update capital
                bot.current_capital += pnl - commission
                
                # Update statistics
                self._update_statistics(bot, position)
                
                self._add_log(bot_id, "trade", f"Closed position", {
                    "symbol": position.symbol,
                    "exit_price": exit_price,
                    "pnl": position.realized_pnl,
                    "reason": exit_reason
                })
            
            # Update equity curve
            self._equity_curves[bot_id].add_point(
                equity=bot.current_capital,
                position_count=len(bot.open_positions)
            )
            
            bot.updated_at = datetime.now()
            self._save_bots()
            
            logger.info(f"Bot {bot_id}: Closed {position.symbol} @ {exit_price}, PnL: {position.realized_pnl:.2f}")
            return position
    
    def get_open_positions(self, bot_id: str) -> List[Position]:
        """Get all open positions for a bot"""
        bot = self._bots.get(bot_id)
        return bot.open_positions if bot else []
    
    def get_closed_positions(self, bot_id: str, limit: int = 50) -> List[Position]:
        """Get closed positions for a bot"""
        bot = self._bots.get(bot_id)
        if not bot:
            return []
        return sorted(
            bot.closed_positions,
            key=lambda p: p.exit_time or datetime.min,
            reverse=True
        )[:limit]
    
    def update_position_price(self, bot_id: str, position_id: str, current_price: float):
        """Update current price and unrealized PnL for a position"""
        with self._lock:
            bot = self._bots.get(bot_id)
            if not bot:
                return
            
            for position in bot.open_positions:
                if position.id == position_id:
                    position.current_price = current_price
                    
                    # Calculate unrealized PnL
                    if position.direction == SignalDirection.LONG:
                        pnl_percent = (current_price - position.entry_price) / position.entry_price * 100
                    else:
                        pnl_percent = (position.entry_price - current_price) / position.entry_price * 100
                    
                    pnl_percent *= bot.config.leverage
                    position.unrealized_pnl_percent = pnl_percent
                    position.unrealized_pnl = position.remaining_size * current_price * (pnl_percent / 100)
                    position.updated_at = datetime.now()
                    break
    
    # ============ STATISTICS ============
    
    def _update_statistics(self, bot: Bot, closed_position: Position):
        """Update bot statistics after closing a position"""
        stats = bot.statistics
        if not stats:
            return
        
        # Update totals
        stats.total_trades += 1
        stats.total_pnl += closed_position.realized_pnl
        
        if closed_position.realized_pnl > 0:
            stats.winning_trades += 1
            stats.avg_win = (
                (stats.avg_win * (stats.winning_trades - 1) + closed_position.realized_pnl)
                / stats.winning_trades
            )
            stats.consecutive_wins += 1
            stats.consecutive_losses = 0
            stats.max_consecutive_wins = max(stats.max_consecutive_wins, stats.consecutive_wins)
        else:
            stats.losing_trades += 1
            stats.avg_loss = (
                (stats.avg_loss * (stats.losing_trades - 1) + abs(closed_position.realized_pnl))
                / stats.losing_trades
            )
            stats.consecutive_losses += 1
            stats.consecutive_wins = 0
            stats.max_consecutive_losses = max(stats.max_consecutive_losses, stats.consecutive_losses)
        
        # Win rate
        stats.win_rate = (stats.winning_trades / stats.total_trades * 100) if stats.total_trades > 0 else 0
        
        # Profit factor
        total_wins = stats.avg_win * stats.winning_trades
        total_losses = stats.avg_loss * stats.losing_trades
        stats.profit_factor = (total_wins / total_losses) if total_losses > 0 else float('inf')
        
        # PnL percent
        stats.total_pnl_percent = (
            (bot.current_capital - bot.config.initial_capital) / bot.config.initial_capital * 100
        )
        
        # Drawdown
        stats.current_capital = bot.current_capital
        if bot.current_capital > stats.equity_peak:
            stats.equity_peak = bot.current_capital
            stats.current_drawdown = 0
        else:
            stats.current_drawdown = (stats.equity_peak - bot.current_capital) / stats.equity_peak * 100
            stats.max_drawdown_percent = max(stats.max_drawdown_percent, stats.current_drawdown)
            stats.max_drawdown = max(stats.max_drawdown, stats.equity_peak - bot.current_capital)
        
        # TP/SL hits
        if closed_position.exit_reason:
            reason = closed_position.exit_reason.lower()
            if reason == "tp1":
                stats.tp1_hits += 1
            elif reason == "tp2":
                stats.tp2_hits += 1
            elif reason == "tp3":
                stats.tp3_hits += 1
            elif reason == "tp4":
                stats.tp4_hits += 1
            elif reason == "sl":
                stats.sl_hits += 1
        
        # Trade duration
        if closed_position.exit_time and closed_position.entry_time:
            duration = (closed_position.exit_time - closed_position.entry_time).total_seconds() / 60
            stats.avg_trade_duration_minutes = (
                (stats.avg_trade_duration_minutes * (stats.total_trades - 1) + duration)
                / stats.total_trades
            )
        
        stats.updated_at = datetime.now()
    
    def get_statistics(self, bot_id: str) -> Optional[BotStatistics]:
        """Get bot statistics"""
        bot = self._bots.get(bot_id)
        return bot.statistics if bot else None
    
    def get_equity_curve(self, bot_id: str) -> Optional[EquityCurve]:
        """Get bot equity curve"""
        return self._equity_curves.get(bot_id)
    
    def recalculate_statistics(self, bot_id: str):
        """Recalculate all statistics from closed positions"""
        with self._lock:
            bot = self._bots.get(bot_id)
            if not bot:
                return
            
            # Reset stats
            bot.statistics = BotStatistics(
                bot_id=bot_id,
                current_capital=bot.config.initial_capital,
                equity_peak=bot.config.initial_capital
            )
            
            # Replay all closed positions
            temp_capital = bot.config.initial_capital
            for position in sorted(bot.closed_positions, key=lambda p: p.exit_time or datetime.min):
                temp_capital += position.realized_pnl
                bot.current_capital = temp_capital
                self._update_statistics(bot, position)
            
            self._save_bots()
            logger.info(f"Recalculated statistics for bot {bot_id}")
    
    # ============ LOGGING ============
    
    def _add_log(self, bot_id: str, level: str, message: str, data: Dict[str, Any] = None):
        """Add log entry for bot"""
        if bot_id not in self._logs:
            self._logs[bot_id] = []
        
        entry = BotLogEntry(
            bot_id=bot_id,
            level=level,
            message=message,
            data=data or {}
        )
        
        self._logs[bot_id].append(entry)
        
        # Keep only last 1000 entries per bot
        if len(self._logs[bot_id]) > 1000:
            self._logs[bot_id] = self._logs[bot_id][-1000:]
    
    def get_logs(self, bot_id: str, limit: int = 100, level: str = None) -> List[BotLogEntry]:
        """Get bot logs"""
        logs = self._logs.get(bot_id, [])
        
        if level:
            logs = [l for l in logs if l.level == level]
        
        return sorted(logs, key=lambda l: l.timestamp, reverse=True)[:limit]
    
    # ============ SUMMARY ============
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all bots"""
        total_bots = len(self._bots)
        running_bots = len([b for b in self._bots.values() if b.status == BotStatus.RUNNING])
        paused_bots = len([b for b in self._bots.values() if b.status == BotStatus.PAUSED])
        error_bots = len([b for b in self._bots.values() if b.status == BotStatus.ERROR])
        
        total_capital = sum(b.current_capital for b in self._bots.values())
        total_pnl = sum(b.statistics.total_pnl for b in self._bots.values() if b.statistics)
        
        total_open_positions = sum(len(b.open_positions) for b in self._bots.values())
        total_trades = sum(b.statistics.total_trades for b in self._bots.values() if b.statistics)
        
        return {
            "total_bots": total_bots,
            "running_bots": running_bots,
            "paused_bots": paused_bots,
            "stopped_bots": total_bots - running_bots - paused_bots - error_bots,
            "error_bots": error_bots,
            "total_capital": round(total_capital, 2),
            "total_pnl": round(total_pnl, 2),
            "total_open_positions": total_open_positions,
            "total_trades": total_trades
        }


# Global instance
_manager: Optional[BotsManager] = None


def get_bots_manager() -> BotsManager:
    """Get global bots manager instance"""
    global _manager
    if _manager is None:
        _manager = BotsManager()
    return _manager
