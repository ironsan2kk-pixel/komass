"""
Komas Trading Server - Main Application
=======================================
FastAPI application with comprehensive logging
Version: 3.5.2
"""
import os
import sys
import logging
import traceback
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import time

# ============ LOGGING SETUP ============

# Create logs directory
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Create data directory
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Log files
LOG_FILE = LOGS_DIR / f"komas_{datetime.now().strftime('%Y-%m-%d')}.log"
ERROR_LOG_FILE = LOGS_DIR / f"errors_{datetime.now().strftime('%Y-%m-%d')}.log"


class ColorFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
    COLORS = {
        logging.DEBUG: "\x1b[38;5;244m",
        logging.INFO: "\x1b[38;5;39m",
        logging.WARNING: "\x1b[38;5;226m",
        logging.ERROR: "\x1b[38;5;196m",
        logging.CRITICAL: "\x1b[31;1m",
    }
    RESET = "\x1b[0m"
    
    def format(self, record):
        color = self.COLORS.get(record.levelno, "")
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        return super().format(record)


def setup_logging():
    """Setup comprehensive logging to file and console"""
    
    root = logging.getLogger()
    root.handlers = []
    root.setLevel(logging.DEBUG)
    
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_format = ColorFormatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Main log file
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_format)
    root.addHandler(file_handler)
    
    # Error log file
    error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    root.addHandler(error_handler)
    
    # Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_format)
    root.addHandler(console_handler)
    
    # Reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


logger = setup_logging()


# ============ APPLICATION ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("=" * 60)
    logger.info("KOMAS TRADING SERVER v3.5.1 - STARTING")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info(f"Error log: {ERROR_LOG_FILE}")
    logger.info(f"Data dir: {DATA_DIR}")
    logger.info("=" * 60)
    yield
    logger.info("=" * 60)
    logger.info("KOMAS TRADING SERVER - SHUTDOWN")
    logger.info("=" * 60)


app = FastAPI(
    title="Komas Trading Server",
    version="3.5.1",
    description="Trading system with indicator, backtesting, and optimization",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============ REQUEST LOGGING ============

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    request_id = datetime.now().strftime('%H%M%S%f')[:10]
    
    logger.debug(f"[{request_id}] {request.method} {request.url.path}")
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000
        
        status_emoji = "OK" if response.status_code < 400 else "ERR"
        logger.info(f"[{request_id}] {status_emoji} {request.method} {request.url.path} - {response.status_code} ({duration:.0f}ms)")
        
        return response
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"[{request_id}] ERR {request.method} {request.url.path} - ERROR ({duration:.0f}ms)")
        logger.error(f"[{request_id}] Exception: {str(e)}")
        logger.error(f"[{request_id}] Traceback:\n{traceback.format_exc()}")
        raise


# ============ EXCEPTION HANDLERS ============

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log all unhandled exceptions"""
    logger.error(f"Unhandled exception on {request.method} {request.url.path}")
    logger.error(f"Exception type: {type(exc).__name__}")
    logger.error(f"Exception message: {str(exc)}")
    logger.error(f"Traceback:\n{traceback.format_exc()}")
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Log HTTP exceptions"""
    if exc.status_code >= 500:
        logger.error(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    elif exc.status_code >= 400:
        logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path),
            "timestamp": datetime.now().isoformat()
        }
    )


# ============ IMPORT ROUTERS ============

# Data Routes
try:
    from app.api.data_routes import router as data_router
    app.include_router(data_router)
    logger.info("[OK] Loaded: data_routes")
except ImportError as e:
    logger.error(f"[FAIL] data_routes: {e}")

# Indicator Routes
try:
    from app.api.indicator_routes import router as indicator_router
    app.include_router(indicator_router)
    logger.info("[OK] Loaded: indicator_routes")
except ImportError as e:
    logger.error(f"[FAIL] indicator_routes: {e}")

# Signals Routes
try:
    from app.api.signals import router as signals_router
    app.include_router(signals_router)
    logger.info("[OK] Loaded: signals")
except ImportError as e:
    logger.warning(f"[SKIP] signals: {e}")

# Plugins Routes
try:
    from app.api.plugins import router as plugins_router
    app.include_router(plugins_router)
    logger.info("[OK] Loaded: plugins")
except ImportError as e:
    logger.warning(f"[SKIP] plugins: {e}")

# WebSocket Routes
try:
    from app.api.ws import router as ws_router
    app.include_router(ws_router)
    logger.info("[OK] Loaded: ws (websocket)")
except ImportError as e:
    logger.warning(f"[SKIP] ws: {e}")

# Database Routes
try:
    from app.api.db_routes import router as db_router
    app.include_router(db_router)
    logger.info("[OK] Loaded: db_routes")
except ImportError as e:
    logger.warning(f"[SKIP] db_routes: {e}")

# Settings Routes
try:
    from app.api.settings_routes import router as settings_router
    app.include_router(settings_router)
    logger.info("[OK] Loaded: settings_routes")
except ImportError as e:
    logger.warning(f"[SKIP] settings_routes: {e}")

# Calendar Routes
try:
    from app.api.calendar_routes import router as calendar_router
    app.include_router(calendar_router)
    logger.info("[OK] Loaded: calendar_routes")
except ImportError as e:
    logger.warning(f"[SKIP] calendar_routes: {e}")


# ============ LOG ENDPOINTS ============

@app.get("/api/logs/list")
async def list_logs():
    """List available log files"""
    logs = []
    for f in sorted(LOGS_DIR.glob("*.log"), reverse=True):
        logs.append({
            "filename": f.name,
            "size_kb": round(f.stat().st_size / 1024, 2),
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    return {"logs_dir": str(LOGS_DIR), "files": logs}


@app.get("/api/logs/today")
async def get_today_log(lines: int = 100):
    """Get last N lines of today's log"""
    if not LOG_FILE.exists():
        return {"error": "No log file for today", "lines": []}
    
    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
    
    return {
        "file": LOG_FILE.name,
        "total_lines": len(all_lines),
        "showing": len(last_lines),
        "lines": [line.strip() for line in last_lines]
    }


@app.get("/api/logs/errors")
async def get_errors(lines: int = 50):
    """Get last N lines of error log"""
    if not ERROR_LOG_FILE.exists():
        return {"error": "No error log for today", "lines": []}
    
    with open(ERROR_LOG_FILE, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
    
    return {
        "file": ERROR_LOG_FILE.name,
        "total_lines": len(all_lines),
        "showing": len(last_lines),
        "lines": [line.strip() for line in last_lines]
    }


@app.get("/api/logs/download/{filename}")
async def download_log(filename: str):
    """Download a specific log file"""
    filepath = LOGS_DIR / filename
    if not filepath.exists() or not filepath.is_file():
        raise HTTPException(404, "Log file not found")
    
    if not str(filepath).startswith(str(LOGS_DIR)):
        raise HTTPException(403, "Access denied")
    
    return FileResponse(
        filepath,
        filename=filename,
        media_type="text/plain"
    )


@app.get("/api/logs/clear")
async def clear_old_logs(days: int = 7):
    """Delete logs older than N days"""
    cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)
    deleted = []
    
    for f in LOGS_DIR.glob("*.log"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            deleted.append(f.name)
            logger.info(f"Deleted old log: {f.name}")
    
    return {"deleted": deleted, "kept_days": days}


# ============ HEALTH & INFO ============

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": "Komas Trading Server",
        "version": "3.5.1",
        "log_file": str(LOG_FILE),
        "data_dir": str(DATA_DIR),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    return {
        "message": "Komas Trading Server",
        "version": "3.5.2",
        "docs": "/docs",
        "health": "/health",
        "logs": "/api/logs/list",
        "endpoints": {
            "data": "/api/data/",
            "indicator": "/api/indicator/",
            "signals": "/api/signals/",
            "plugins": "/api/plugins/",
            "ws": "/api/ws/",
            "db": "/api/db/",
            "settings": "/api/settings/",
            "calendar": "/api/calendar/"
        }
    }


@app.get("/api/info")
async def api_info():
    """Get information about loaded API routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods) if route.methods else [],
                "name": route.name if hasattr(route, 'name') else None
            })
    
    return {
        "version": "3.5.1",
        "total_routes": len(routes),
        "routes": sorted(routes, key=lambda x: x['path'])
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
