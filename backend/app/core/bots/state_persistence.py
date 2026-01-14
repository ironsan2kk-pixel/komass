"""
Komas Trading Server - Bot State Persistence
=============================================
Save and restore bot state for recovery after server restart
"""
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger("komas.bots.persistence")


@dataclass
class PositionState:
    """Saved position state"""
    symbol: str
    direction: str
    size: float
    entry_price: float
    current_price: float
    entry_time: str
    take_profit_levels: List[Dict]
    stop_loss_price: float
    pnl: float
    pnl_percent: float


@dataclass
class BotState:
    """Complete bot state snapshot"""
    bot_id: str
    name: str
    status: str

    # Capital
    initial_capital: float
    current_capital: float
    peak_capital: float

    # Positions
    positions: List[PositionState]

    # Statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    total_pnl_percent: float

    # Risk
    max_drawdown: float
    current_drawdown: float

    # Timestamps
    started_at: str
    last_updated: str
    last_trade_at: Optional[str] = None

    # Daily stats
    daily_pnl: Dict[str, float] = None
    daily_trades: Dict[str, int] = None

    def __post_init__(self):
        if self.daily_pnl is None:
            self.daily_pnl = {}
        if self.daily_trades is None:
            self.daily_trades = {}


class StatePersistence:
    """
    Bot State Persistence Manager

    Saves and restores bot states to/from JSON files:
    - Active positions
    - Capital and P&L
    - Trading statistics
    - Risk metrics

    Usage:
        persistence = StatePersistence()

        # Save state
        persistence.save_bot_state(bot_id, state)

        # Restore state
        state = persistence.load_bot_state(bot_id)

        # List all saved states
        states = persistence.list_saved_states()
    """

    def __init__(self, state_dir: Optional[Path] = None):
        """Initialize persistence manager"""
        if state_dir is None:
            # Default to backend/data/bot_states/
            base_dir = Path(__file__).parent.parent.parent.parent
            state_dir = base_dir / "data" / "bot_states"

        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"State persistence initialized: {self.state_dir}")

    def save_bot_state(self, bot_id: str, state: BotState) -> bool:
        """
        Save bot state to JSON file

        Args:
            bot_id: Unique bot identifier
            state: BotState object

        Returns:
            True if successful
        """
        try:
            # Convert to dict
            state_dict = asdict(state)

            # Add metadata
            state_dict["_metadata"] = {
                "version": "1.0",
                "saved_at": datetime.now().isoformat(),
                "bot_id": bot_id
            }

            # Save to file
            file_path = self.state_dir / f"{bot_id}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved state for bot {bot_id}: {file_path}")

            # Create backup
            self._create_backup(bot_id, state_dict)

            return True

        except Exception as e:
            logger.error(f"Failed to save bot state {bot_id}: {e}")
            return False

    def load_bot_state(self, bot_id: str) -> Optional[BotState]:
        """
        Load bot state from JSON file

        Args:
            bot_id: Unique bot identifier

        Returns:
            BotState object or None if not found
        """
        try:
            file_path = self.state_dir / f"{bot_id}.json"

            if not file_path.exists():
                logger.warning(f"No saved state found for bot {bot_id}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                state_dict = json.load(f)

            # Remove metadata
            state_dict.pop("_metadata", None)

            # Convert positions back to PositionState objects
            positions = []
            for pos_dict in state_dict.get("positions", []):
                positions.append(PositionState(**pos_dict))

            state_dict["positions"] = positions

            # Create BotState
            state = BotState(**state_dict)

            logger.info(f"Loaded state for bot {bot_id}")
            return state

        except Exception as e:
            logger.error(f"Failed to load bot state {bot_id}: {e}")
            return None

    def delete_bot_state(self, bot_id: str) -> bool:
        """
        Delete saved bot state

        Args:
            bot_id: Unique bot identifier

        Returns:
            True if deleted
        """
        try:
            file_path = self.state_dir / f"{bot_id}.json"

            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted state for bot {bot_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete bot state {bot_id}: {e}")
            return False

    def list_saved_states(self) -> List[Dict[str, Any]]:
        """
        List all saved bot states

        Returns:
            List of state metadata
        """
        states = []

        try:
            for file_path in self.state_dir.glob("*.json"):
                if file_path.stem.startswith("backup_"):
                    continue

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        state_dict = json.load(f)

                    metadata = state_dict.get("_metadata", {})
                    metadata["bot_id"] = file_path.stem
                    metadata["name"] = state_dict.get("name", "Unknown")
                    metadata["status"] = state_dict.get("status", "unknown")
                    metadata["positions_count"] = len(state_dict.get("positions", []))
                    metadata["current_capital"] = state_dict.get("current_capital", 0)

                    states.append(metadata)

                except Exception as e:
                    logger.warning(f"Failed to read state file {file_path}: {e}")

            # Sort by last updated
            states.sort(key=lambda x: x.get("saved_at", ""), reverse=True)

            logger.info(f"Found {len(states)} saved bot states")
            return states

        except Exception as e:
            logger.error(f"Failed to list saved states: {e}")
            return []

    def restore_all_active_bots(self) -> List[BotState]:
        """
        Restore all bots that were in active state

        Returns:
            List of active bot states
        """
        active_bots = []

        states = self.list_saved_states()
        for state_meta in states:
            if state_meta.get("status") in ["running", "paused"]:
                bot_id = state_meta["bot_id"]
                state = self.load_bot_state(bot_id)

                if state:
                    active_bots.append(state)
                    logger.info(f"Restored active bot: {bot_id} ({state.name})")

        logger.info(f"Restored {len(active_bots)} active bots")
        return active_bots

    def _create_backup(self, bot_id: str, state_dict: Dict):
        """Create timestamped backup of bot state"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.state_dir / f"backup_{bot_id}_{timestamp}.json"

            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(state_dict, f, indent=2, ensure_ascii=False)

            # Clean old backups (keep last 10)
            backups = sorted(
                self.state_dir.glob(f"backup_{bot_id}_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )

            for old_backup in backups[10:]:
                old_backup.unlink()
                logger.debug(f"Deleted old backup: {old_backup}")

        except Exception as e:
            logger.warning(f"Failed to create backup for {bot_id}: {e}")

    def cleanup_old_states(self, days: int = 30):
        """
        Clean up old bot states

        Args:
            days: Remove states older than N days
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days * 24 * 3600)

            removed = 0
            for file_path in self.state_dir.glob("*.json"):
                if file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    removed += 1
                    logger.info(f"Removed old state: {file_path}")

            logger.info(f"Cleanup completed: removed {removed} old states")

        except Exception as e:
            logger.error(f"Failed to cleanup old states: {e}")


# Global persistence instance
_persistence_instance: Optional[StatePersistence] = None


def get_state_persistence() -> StatePersistence:
    """Get global state persistence instance"""
    global _persistence_instance

    if _persistence_instance is None:
        _persistence_instance = StatePersistence()

    return _persistence_instance


# Helper functions for easy access

def save_bot_state(bot_id: str, state: BotState) -> bool:
    """Save bot state"""
    return get_state_persistence().save_bot_state(bot_id, state)


def load_bot_state(bot_id: str) -> Optional[BotState]:
    """Load bot state"""
    return get_state_persistence().load_bot_state(bot_id)


def delete_bot_state(bot_id: str) -> bool:
    """Delete bot state"""
    return get_state_persistence().delete_bot_state(bot_id)


def restore_all_active_bots() -> List[BotState]:
    """Restore all active bots"""
    return get_state_persistence().restore_all_active_bots()
