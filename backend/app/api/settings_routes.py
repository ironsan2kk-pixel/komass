"""
KOMAS Settings API v1.0
=======================
API для управления настройками системы:
- API ключи бирж (Binance, Bybit, OKX)
- Уведомления (Telegram, Discord)
- Системные настройки
- Настройки календаря

Endpoints:
- GET/POST /api/settings/api-keys
- POST /api/settings/api-keys/{exchange}/test
- GET/POST /api/settings/notifications
- POST /api/settings/notifications/{type}/test
- GET/POST /api/settings/system
- GET /api/settings/system/info
- POST /api/settings/system/clear-cache
- GET/POST /api/settings/calendar
"""

import os
import json
import time
import hashlib
import platform
import psutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

# Cryptography for API keys encryption
try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

router = APIRouter(prefix="/api/settings", tags=["settings"])

# === Paths ===
DATA_DIR = Path("data")
SETTINGS_DIR = DATA_DIR / "settings"
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)

API_KEYS_FILE = SETTINGS_DIR / "api_keys.json"
NOTIFICATIONS_FILE = SETTINGS_DIR / "notifications.json"
SYSTEM_FILE = SETTINGS_DIR / "system.json"
CALENDAR_FILE = SETTINGS_DIR / "calendar.json"

# === Encryption Key (generate once and store) ===
ENCRYPTION_KEY_FILE = SETTINGS_DIR / ".encryption_key"

def get_encryption_key() -> bytes:
    """Get or generate encryption key for API secrets"""
    if not CRYPTO_AVAILABLE:
        return b""
    
    if ENCRYPTION_KEY_FILE.exists():
        return ENCRYPTION_KEY_FILE.read_bytes()
    else:
        key = Fernet.generate_key()
        ENCRYPTION_KEY_FILE.write_bytes(key)
        return key

def encrypt_value(value: str) -> str:
    """Encrypt sensitive value"""
    if not CRYPTO_AVAILABLE or not value:
        return value
    try:
        f = Fernet(get_encryption_key())
        return f.encrypt(value.encode()).decode()
    except Exception:
        return value

def decrypt_value(value: str) -> str:
    """Decrypt sensitive value"""
    if not CRYPTO_AVAILABLE or not value:
        return value
    try:
        f = Fernet(get_encryption_key())
        return f.decrypt(value.encode()).decode()
    except Exception:
        return value

def mask_key(key: str) -> str:
    """Mask API key for display"""
    if not key or len(key) < 8:
        return "****"
    return key[:4] + "****" + key[-4:]


# ===========================================
# Pydantic Models
# ===========================================

class ExchangeApiKey(BaseModel):
    api_key: str = ""
    api_secret: str = ""
    passphrase: str = ""  # OKX only
    testnet: bool = False

class ApiKeysRequest(BaseModel):
    binance: Optional[ExchangeApiKey] = None
    bybit: Optional[ExchangeApiKey] = None
    okx: Optional[ExchangeApiKey] = None

class NotificationSettings(BaseModel):
    enabled: bool = False
    notify_signals: bool = True
    notify_trades: bool = True
    notify_errors: bool = True

class TelegramSettings(NotificationSettings):
    bot_token: str = ""
    chat_id: str = ""

class DiscordSettings(NotificationSettings):
    webhook_url: str = ""

class NotificationsRequest(BaseModel):
    telegram: Optional[TelegramSettings] = None
    discord: Optional[DiscordSettings] = None

class SystemSettings(BaseModel):
    auto_start: bool = False
    log_level: str = "INFO"
    max_log_size_mb: int = 100
    data_retention_days: int = 90
    backup_enabled: bool = False
    backup_interval_hours: int = 24

class CalendarSettings(BaseModel):
    block_trading: bool = False
    minutes_before: int = 15
    minutes_after: int = 15
    min_impact: str = "high"  # high, medium, low


# ===========================================
# Helper Functions
# ===========================================

def load_json_file(filepath: Path, default: dict = None) -> dict:
    """Load JSON file with UTF-8 encoding"""
    if default is None:
        default = {}
    try:
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return default

def save_json_file(filepath: Path, data: dict) -> bool:
    """Save JSON file with UTF-8 encoding"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False


# ===========================================
# API Keys Endpoints
# ===========================================

@router.get("/api-keys")
async def get_api_keys():
    """Get API keys (masked for security)"""
    data = load_json_file(API_KEYS_FILE, {
        "binance": {"api_key": "", "api_secret": "", "testnet": False, "connected": False},
        "bybit": {"api_key": "", "api_secret": "", "testnet": False, "connected": False},
        "okx": {"api_key": "", "api_secret": "", "passphrase": "", "testnet": False, "connected": False},
    })
    
    # Mask secrets for response
    result = {}
    for exchange, keys in data.items():
        result[exchange] = {
            "api_key": mask_key(decrypt_value(keys.get("api_key", ""))),
            "api_secret": "****" if keys.get("api_secret") else "",
            "passphrase": "****" if keys.get("passphrase") else "",
            "testnet": keys.get("testnet", False),
            "connected": keys.get("connected", False),
        }
    
    return result


@router.post("/api-keys/{exchange}")
async def save_api_key(exchange: str, data: ExchangeApiKey):
    """Save API key for exchange"""
    if exchange not in ["binance", "bybit", "okx"]:
        raise HTTPException(status_code=400, detail=f"Unknown exchange: {exchange}")
    
    current = load_json_file(API_KEYS_FILE, {})
    
    # Encrypt sensitive data
    current[exchange] = {
        "api_key": encrypt_value(data.api_key) if data.api_key else "",
        "api_secret": encrypt_value(data.api_secret) if data.api_secret else "",
        "passphrase": encrypt_value(data.passphrase) if data.passphrase else "",
        "testnet": data.testnet,
        "connected": False,
    }
    
    if save_json_file(API_KEYS_FILE, current):
        return {"success": True, "message": f"{exchange.upper()} API keys saved"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save API keys")


@router.post("/api-keys/{exchange}/test")
async def test_api_connection(exchange: str):
    """Test API connection for exchange"""
    if exchange not in ["binance", "bybit", "okx"]:
        raise HTTPException(status_code=400, detail=f"Unknown exchange: {exchange}")
    
    current = load_json_file(API_KEYS_FILE, {})
    keys = current.get(exchange, {})
    
    api_key = decrypt_value(keys.get("api_key", ""))
    api_secret = decrypt_value(keys.get("api_secret", ""))
    testnet = keys.get("testnet", False)
    
    if not api_key or not api_secret:
        return {"success": False, "error": "API keys not configured"}
    
    # Test connection based on exchange
    try:
        if exchange == "binance":
            result = await test_binance_connection(api_key, api_secret, testnet)
        elif exchange == "bybit":
            result = await test_bybit_connection(api_key, api_secret, testnet)
        elif exchange == "okx":
            passphrase = decrypt_value(keys.get("passphrase", ""))
            result = await test_okx_connection(api_key, api_secret, passphrase, testnet)
        else:
            result = {"success": False, "error": "Unknown exchange"}
        
        # Update connected status
        if result.get("success"):
            current[exchange]["connected"] = True
            save_json_file(API_KEYS_FILE, current)
        
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_binance_connection(api_key: str, api_secret: str, testnet: bool) -> dict:
    """Test Binance API connection"""
    try:
        import hmac
        import hashlib
        import httpx
        
        base_url = "https://testnet.binance.vision" if testnet else "https://api.binance.com"
        timestamp = int(time.time() * 1000)
        query = f"timestamp={timestamp}"
        signature = hmac.new(api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/api/v3/account",
                params={"timestamp": timestamp, "signature": signature},
                headers={"X-MBX-APIKEY": api_key},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "balance_count": len(data.get("balances", [])),
                    "can_trade": data.get("canTrade", False)
                }
            else:
                return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_bybit_connection(api_key: str, api_secret: str, testnet: bool) -> dict:
    """Test Bybit API connection"""
    try:
        import hmac
        import hashlib
        import httpx
        
        base_url = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"
        timestamp = str(int(time.time() * 1000))
        recv_window = "5000"
        
        param_str = f"{timestamp}{api_key}{recv_window}"
        signature = hmac.new(api_secret.encode(), param_str.encode(), hashlib.sha256).hexdigest()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}/v5/account/wallet-balance",
                params={"accountType": "UNIFIED"},
                headers={
                    "X-BAPI-API-KEY": api_key,
                    "X-BAPI-SIGN": signature,
                    "X-BAPI-TIMESTAMP": timestamp,
                    "X-BAPI-RECV-WINDOW": recv_window,
                },
                timeout=10
            )
            
            data = response.json()
            if data.get("retCode") == 0:
                return {"success": True, "message": "Connected to Bybit"}
            else:
                return {"success": False, "error": data.get("retMsg", "Unknown error")}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_okx_connection(api_key: str, api_secret: str, passphrase: str, testnet: bool) -> dict:
    """Test OKX API connection"""
    try:
        import hmac
        import hashlib
        import base64
        import httpx
        
        base_url = "https://www.okx.com"  # OKX uses same URL, testnet via header
        timestamp = datetime.utcnow().isoformat(timespec='milliseconds') + 'Z'
        
        method = "GET"
        request_path = "/api/v5/account/balance"
        
        prehash = f"{timestamp}{method}{request_path}"
        signature = base64.b64encode(
            hmac.new(api_secret.encode(), prehash.encode(), hashlib.sha256).digest()
        ).decode()
        
        headers = {
            "OK-ACCESS-KEY": api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": passphrase,
        }
        if testnet:
            headers["x-simulated-trading"] = "1"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{base_url}{request_path}",
                headers=headers,
                timeout=10
            )
            
            data = response.json()
            if data.get("code") == "0":
                return {"success": True, "message": "Connected to OKX"}
            else:
                return {"success": False, "error": data.get("msg", "Unknown error")}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ===========================================
# Notifications Endpoints
# ===========================================

@router.get("/notifications")
async def get_notifications():
    """Get notification settings"""
    data = load_json_file(NOTIFICATIONS_FILE, {
        "telegram": {
            "enabled": False,
            "bot_token": "",
            "chat_id": "",
            "notify_signals": True,
            "notify_trades": True,
            "notify_errors": True,
        },
        "discord": {
            "enabled": False,
            "webhook_url": "",
            "notify_signals": True,
            "notify_trades": True,
            "notify_errors": True,
        },
    })
    
    # Mask sensitive data
    if data.get("telegram", {}).get("bot_token"):
        data["telegram"]["bot_token"] = mask_key(data["telegram"]["bot_token"])
    if data.get("discord", {}).get("webhook_url"):
        url = data["discord"]["webhook_url"]
        data["discord"]["webhook_url"] = url[:30] + "****" if len(url) > 30 else "****"
    
    return data


@router.post("/notifications")
async def save_notifications(data: NotificationsRequest):
    """Save notification settings"""
    current = load_json_file(NOTIFICATIONS_FILE, {})
    
    if data.telegram:
        current["telegram"] = {
            "enabled": data.telegram.enabled,
            "bot_token": encrypt_value(data.telegram.bot_token) if data.telegram.bot_token and not data.telegram.bot_token.endswith("****") else current.get("telegram", {}).get("bot_token", ""),
            "chat_id": data.telegram.chat_id,
            "notify_signals": data.telegram.notify_signals,
            "notify_trades": data.telegram.notify_trades,
            "notify_errors": data.telegram.notify_errors,
        }
    
    if data.discord:
        current["discord"] = {
            "enabled": data.discord.enabled,
            "webhook_url": encrypt_value(data.discord.webhook_url) if data.discord.webhook_url and not data.discord.webhook_url.endswith("****") else current.get("discord", {}).get("webhook_url", ""),
            "notify_signals": data.discord.notify_signals,
            "notify_trades": data.discord.notify_trades,
            "notify_errors": data.discord.notify_errors,
        }
    
    if save_json_file(NOTIFICATIONS_FILE, current):
        return {"success": True, "message": "Notification settings saved"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save settings")


@router.post("/notifications/{notification_type}/test")
async def test_notification(notification_type: str):
    """Send test notification"""
    if notification_type not in ["telegram", "discord"]:
        raise HTTPException(status_code=400, detail=f"Unknown notification type: {notification_type}")
    
    current = load_json_file(NOTIFICATIONS_FILE, {})
    settings = current.get(notification_type, {})
    
    if not settings.get("enabled"):
        return {"success": False, "error": f"{notification_type.capitalize()} notifications disabled"}
    
    try:
        if notification_type == "telegram":
            result = await send_telegram_test(settings)
        else:
            result = await send_discord_test(settings)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


async def send_telegram_test(settings: dict) -> dict:
    """Send test message to Telegram"""
    try:
        import httpx
        
        bot_token = decrypt_value(settings.get("bot_token", ""))
        chat_id = settings.get("chat_id", "")
        
        if not bot_token or not chat_id:
            return {"success": False, "error": "Bot token or chat ID not configured"}
        
        message = "🧪 KOMAS Test Notification\n\nТестовое сообщение от Komas Trading Server v3.5"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": message, "parse_mode": "HTML"},
                timeout=10
            )
            
            data = response.json()
            if data.get("ok"):
                return {"success": True, "message": "Test message sent to Telegram"}
            else:
                return {"success": False, "error": data.get("description", "Unknown error")}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def send_discord_test(settings: dict) -> dict:
    """Send test message to Discord webhook"""
    try:
        import httpx
        
        webhook_url = decrypt_value(settings.get("webhook_url", ""))
        
        if not webhook_url:
            return {"success": False, "error": "Webhook URL not configured"}
        
        payload = {
            "content": "🧪 **KOMAS Test Notification**\n\nТестовое сообщение от Komas Trading Server v3.5",
            "username": "KOMAS Bot"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(webhook_url, json=payload, timeout=10)
            
            if response.status_code in [200, 204]:
                return {"success": True, "message": "Test message sent to Discord"}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ===========================================
# System Settings Endpoints
# ===========================================

@router.get("/system")
async def get_system_settings():
    """Get system settings"""
    return load_json_file(SYSTEM_FILE, {
        "auto_start": False,
        "log_level": "INFO",
        "max_log_size_mb": 100,
        "data_retention_days": 90,
        "backup_enabled": False,
        "backup_interval_hours": 24,
    })


@router.post("/system")
async def save_system_settings(settings: SystemSettings):
    """Save system settings"""
    data = {
        "auto_start": settings.auto_start,
        "log_level": settings.log_level,
        "max_log_size_mb": settings.max_log_size_mb,
        "data_retention_days": settings.data_retention_days,
        "backup_enabled": settings.backup_enabled,
        "backup_interval_hours": settings.backup_interval_hours,
    }
    
    if save_json_file(SYSTEM_FILE, data):
        return {"success": True, "message": "System settings saved"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save settings")


@router.get("/system/info")
async def get_system_info():
    """Get system information"""
    try:
        # Get uptime
        import subprocess
        
        # Version info
        version = "3.5.1"
        python_version = platform.python_version()
        
        # System info
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        
        # Database size
        db_path = DATA_DIR / "komas.db"
        db_size = f"{db_path.stat().st_size / 1024 / 1024:.1f} MB" if db_path.exists() else "N/A"
        
        # Uptime (process)
        process = psutil.Process()
        uptime_seconds = time.time() - process.create_time()
        hours, remainder = divmod(int(uptime_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{hours}h {minutes}m {seconds}s"
        
        return {
            "version": version,
            "python_version": python_version,
            "platform": platform.system(),
            "uptime": uptime,
            "cpu_percent": cpu_percent,
            "memory_used": f"{memory.used / 1024 / 1024 / 1024:.1f} GB",
            "memory_total": f"{memory.total / 1024 / 1024 / 1024:.1f} GB",
            "memory_percent": memory.percent,
            "disk_used": f"{disk.used / 1024 / 1024 / 1024:.1f} GB",
            "disk_total": f"{disk.total / 1024 / 1024 / 1024:.1f} GB",
            "disk_percent": disk.percent,
            "db_size": db_size,
        }
    except Exception as e:
        return {
            "version": "3.5.1",
            "python_version": platform.python_version(),
            "error": str(e)
        }


@router.post("/system/clear-cache")
async def clear_cache():
    """Clear system cache"""
    try:
        cache_dir = DATA_DIR / "cache"
        if cache_dir.exists():
            import shutil
            shutil.rmtree(cache_dir)
            cache_dir.mkdir(exist_ok=True)
        
        # Clear __pycache__ directories
        for pycache in Path(".").rglob("__pycache__"):
            import shutil
            shutil.rmtree(pycache, ignore_errors=True)
        
        return {"success": True, "message": "Cache cleared"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ===========================================
# Calendar Settings Endpoints
# ===========================================

@router.get("/calendar")
async def get_calendar_settings():
    """Get calendar settings for trading block"""
    return load_json_file(CALENDAR_FILE, {
        "block_trading": False,
        "minutes_before": 15,
        "minutes_after": 15,
        "min_impact": "high",
    })


@router.post("/calendar")
async def save_calendar_settings(settings: CalendarSettings):
    """Save calendar settings"""
    data = {
        "block_trading": settings.block_trading,
        "minutes_before": settings.minutes_before,
        "minutes_after": settings.minutes_after,
        "min_impact": settings.min_impact,
    }
    
    if save_json_file(CALENDAR_FILE, data):
        return {"success": True, "message": "Calendar settings saved"}
    else:
        raise HTTPException(status_code=500, detail="Failed to save settings")
