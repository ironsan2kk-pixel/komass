"""
Error Handling System
=====================
Centralized error handling with typed exceptions and error storage.
"""
import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any, List
from collections import deque
from threading import Lock
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════
# CUSTOM EXCEPTIONS
# ═══════════════════════════════════════════════════════════════

class KomasError(Exception):
    """Base exception for all Komas errors"""
    def __init__(self, message: str, code: str = "UNKNOWN", details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)


class DataError(KomasError):
    """Data loading/processing errors"""
    def __init__(self, message: str, symbol: str = None, timeframe: str = None):
        super().__init__(
            message=message,
            code="DATA_ERROR",
            details={"symbol": symbol, "timeframe": timeframe}
        )


class IndicatorError(KomasError):
    """Indicator calculation errors"""
    def __init__(self, message: str, indicator: str = None, params: Dict = None):
        super().__init__(
            message=message,
            code="INDICATOR_ERROR",
            details={"indicator": indicator, "params": params}
        )


class BacktestError(KomasError):
    """Backtest execution errors"""
    def __init__(self, message: str, settings: Dict = None):
        super().__init__(
            message=message,
            code="BACKTEST_ERROR",
            details={"settings": settings}
        )


class BotError(KomasError):
    """Bot management errors"""
    def __init__(self, message: str, bot_id: str = None, action: str = None):
        super().__init__(
            message=message,
            code="BOT_ERROR",
            details={"bot_id": bot_id, "action": action}
        )


class TelegramError(KomasError):
    """Telegram notification errors"""
    def __init__(self, message: str, channel_id: str = None):
        super().__init__(
            message=message,
            code="TELEGRAM_ERROR",
            details={"channel_id": channel_id}
        )


class OptimizationError(KomasError):
    """Optimization process errors"""
    def __init__(self, message: str, mode: str = None, progress: float = None):
        super().__init__(
            message=message,
            code="OPTIMIZATION_ERROR",
            details={"mode": mode, "progress": progress}
        )


class ValidationError(KomasError):
    """Input validation errors"""
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details={"field": field, "value": str(value) if value else None}
        )


# ═══════════════════════════════════════════════════════════════
# ERROR STORAGE (In-Memory Ring Buffer)
# ═══════════════════════════════════════════════════════════════

class ErrorStorage:
    """Thread-safe in-memory storage for recent errors"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.errors: deque = deque(maxlen=max_size)
        self.lock = Lock()
        self._error_counts: Dict[str, int] = {}

    def add(
        self,
        error_type: str,
        message: str,
        path: str = None,
        code: str = "UNKNOWN",
        details: Optional[Dict] = None,
        traceback_str: str = None
    ) -> Dict:
        """Add error to storage"""
        error_entry = {
            "id": len(self.errors) + 1,
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "code": code,
            "message": message,
            "path": path,
            "details": details or {},
            "traceback": traceback_str
        }

        with self.lock:
            self.errors.append(error_entry)

            # Update counts
            self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1

        return error_entry

    def get_recent(self, limit: int = 50, error_type: str = None) -> List[Dict]:
        """Get recent errors, optionally filtered by type"""
        with self.lock:
            errors_list = list(self.errors)

        # Filter by type if specified
        if error_type:
            errors_list = [e for e in errors_list if e["type"] == error_type]

        # Return most recent first
        return list(reversed(errors_list))[:limit]

    def get_stats(self) -> Dict:
        """Get error statistics"""
        with self.lock:
            return {
                "total_errors": len(self.errors),
                "max_size": self.max_size,
                "by_type": dict(self._error_counts),
                "last_error": self.errors[-1] if self.errors else None
            }

    def clear(self):
        """Clear all stored errors"""
        with self.lock:
            self.errors.clear()
            self._error_counts.clear()


# Global error storage instance
error_storage = ErrorStorage(max_size=1000)


# ═══════════════════════════════════════════════════════════════
# EXCEPTION HANDLERS
# ═══════════════════════════════════════════════════════════════

async def komas_exception_handler(request: Request, exc: KomasError) -> JSONResponse:
    """Handler for KomasError and subclasses"""
    tb = traceback.format_exc()

    # Log error
    logger.error(f"[{exc.code}] {exc.message} on {request.url.path}")

    # Store error
    error_storage.add(
        error_type=type(exc).__name__,
        message=exc.message,
        path=str(request.url.path),
        code=exc.code,
        details=exc.details,
        traceback_str=tb
    )

    return JSONResponse(
        status_code=400,
        content={
            "error": exc.message,
            "code": exc.code,
            "type": type(exc).__name__,
            "details": exc.details,
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat()
        }
    )


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unhandled exceptions"""
    tb = traceback.format_exc()

    # Log error
    logger.error(f"Unhandled error on {request.url.path}:\n{tb}")

    # Store error
    error_storage.add(
        error_type=type(exc).__name__,
        message=str(exc),
        path=str(request.url.path),
        code="UNHANDLED",
        traceback_str=tb
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "code": "UNHANDLED",
            "type": type(exc).__name__,
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat()
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handler for HTTP exceptions"""

    # Log if client error or server error
    if exc.status_code >= 400:
        logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")

        # Store only server errors (5xx)
        if exc.status_code >= 500:
            error_storage.add(
                error_type="HTTPException",
                message=str(exc.detail),
                path=str(request.url.path),
                code=f"HTTP_{exc.status_code}"
            )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "code": f"HTTP_{exc.status_code}",
            "type": "HTTPException",
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat()
        }
    )


# ═══════════════════════════════════════════════════════════════
# REGISTRATION HELPER
# ═══════════════════════════════════════════════════════════════

def register_exception_handlers(app):
    """Register all exception handlers with FastAPI app"""
    from fastapi import FastAPI

    app.add_exception_handler(KomasError, komas_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    logger.info("✔ Error handlers registered")
