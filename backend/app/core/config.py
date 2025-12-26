"""
Komas Trading System - Configuration
=====================================
Настройки приложения через Pydantic Settings.

Загружает из:
1. Переменные окружения
2. Файл .env

Использование:
    from app.core.config import settings
    
    print(settings.APP_NAME)
    print(settings.DEBUG)
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Настройки приложения.
    
    Все настройки можно переопределить через переменные окружения
    или файл .env в корне backend.
    """
    
    # ═══════════════════════════════════════════════════════════════
    # ПРИЛОЖЕНИЕ
    # ═══════════════════════════════════════════════════════════════
    
    APP_NAME: str = "Komas Trading Server"
    APP_VERSION: str = "3.5"
    DEBUG: bool = False
    
    # ═══════════════════════════════════════════════════════════════
    # СЕРВЕР
    # ═══════════════════════════════════════════════════════════════
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True
    
    # ═══════════════════════════════════════════════════════════════
    # БАЗА ДАННЫХ
    # ═══════════════════════════════════════════════════════════════
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/komas.db"
    
    # ═══════════════════════════════════════════════════════════════
    # ДАННЫЕ
    # ═══════════════════════════════════════════════════════════════
    
    DATA_DIR: str = "./data"
    DEFAULT_DATA_SOURCE: str = "spot"  # spot или futures
    
    # ═══════════════════════════════════════════════════════════════
    # BINANCE
    # ═══════════════════════════════════════════════════════════════
    
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET: Optional[str] = None
    BINANCE_TESTNET: bool = False
    
    # ═══════════════════════════════════════════════════════════════
    # TELEGRAM
    # ═══════════════════════════════════════════════════════════════
    
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    TELEGRAM_ENABLED: bool = False
    
    # ═══════════════════════════════════════════════════════════════
    # ЛОГИРОВАНИЕ
    # ═══════════════════════════════════════════════════════════════
    
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    LOG_RETENTION_DAYS: int = 7
    
    # ═══════════════════════════════════════════════════════════════
    # ОПТИМИЗАЦИЯ
    # ═══════════════════════════════════════════════════════════════
    
    MAX_WORKERS: Optional[int] = None  # None = auto (cpu_count)
    OPTIMIZATION_TIMEOUT: int = 3600  # секунд
    
    # Pydantic config
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


# Глобальный экземпляр настроек
settings = Settings()
