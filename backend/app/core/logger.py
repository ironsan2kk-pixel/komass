"""
Komas Trading System - Logger
==============================
Централизованное логирование с ротацией файлов.

Использование:
    from app.core.logger import get_logger
    
    logger = get_logger("my_module")
    logger.info("Hello!")
    logger.error("Something went wrong", exc_info=True)
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


# ═══════════════════════════════════════════════════════════════════
# КОНСТАНТЫ
# ═══════════════════════════════════════════════════════════════════

LOGS_DIR = Path(__file__).parent.parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOG_FILE = LOGS_DIR / f"komas_{datetime.now().strftime('%Y-%m-%d')}.log"
ERROR_LOG_FILE = LOGS_DIR / f"errors_{datetime.now().strftime('%Y-%m-%d')}.log"

# Формат логов
FILE_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s'
CONSOLE_FORMAT = '%(asctime)s | %(levelname)-8s | %(message)s'
DATE_FORMAT = '%H:%M:%S'


# ═══════════════════════════════════════════════════════════════════
# COLOR FORMATTER
# ═══════════════════════════════════════════════════════════════════

class ColorFormatter(logging.Formatter):
    """Цветной форматтер для консоли"""
    
    COLORS = {
        logging.DEBUG: "\x1b[38;5;244m",     # Gray
        logging.INFO: "\x1b[38;5;39m",        # Blue
        logging.WARNING: "\x1b[38;5;226m",    # Yellow
        logging.ERROR: "\x1b[38;5;196m",      # Red
        logging.CRITICAL: "\x1b[31;1m",       # Bold Red
    }
    RESET = "\x1b[0m"
    
    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


# ═══════════════════════════════════════════════════════════════════
# SETUP FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

_initialized = False


def setup_logger() -> None:
    """
    Настройка корневого логгера.
    Вызывается автоматически при первом get_logger().
    """
    global _initialized
    
    if _initialized:
        return
    
    # Clear existing handlers
    root = logging.getLogger()
    root.handlers = []
    root.setLevel(logging.DEBUG)
    
    # File format
    file_format = logging.Formatter(FILE_FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
    
    # Console format (colored)
    console_format = ColorFormatter(CONSOLE_FORMAT, datefmt=DATE_FORMAT)
    
    # Main log file handler
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_format)
    root.addHandler(file_handler)
    
    # Error log file handler
    error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    root.addHandler(error_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_format)
    root.addHandler(console_handler)
    
    # Reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    
    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """
    Получить логгер для модуля.
    
    Args:
        name: Имя модуля (например "data.binance")
    
    Returns:
        logging.Logger
    
    Пример:
        logger = get_logger("indicator.trg")
        logger.info("Calculating...")
    """
    setup_logger()
    return logging.getLogger(f"komas.{name}")


# ═══════════════════════════════════════════════════════════════════
# UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

def get_log_files() -> list:
    """Получить список файлов логов"""
    files = []
    for f in sorted(LOGS_DIR.glob("*.log"), reverse=True):
        files.append({
            "filename": f.name,
            "path": str(f),
            "size_kb": round(f.stat().st_size / 1024, 2),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    return files


def get_recent_logs(lines: int = 100) -> list:
    """Получить последние N строк лога"""
    if not LOG_FILE.exists():
        return []
    
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        return [line.strip() for line in all_lines[-lines:]]


def get_recent_errors(lines: int = 50) -> list:
    """Получить последние N строк ошибок"""
    if not ERROR_LOG_FILE.exists():
        return []
    
    with open(ERROR_LOG_FILE, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        return [line.strip() for line in all_lines[-lines:]]


def clear_old_logs(days: int = 7) -> list:
    """Удалить логи старше N дней"""
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
    deleted = []
    
    for f in LOGS_DIR.glob("*.log"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            deleted.append(f.name)
    
    return deleted
