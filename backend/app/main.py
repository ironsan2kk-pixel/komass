"""
Komas Trading Server - Main Application
=======================================
FastAPI application with comprehensive logging
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
Path("data").mkdir(exist_ok=True)
Path("data/bots").mkdir(exist_ok=True)

# Log files
LOG_FILE = LOGS_DIR / f"komas_{datetime.now().strftime('%Y-%m-%d')}.log"
ERROR_LOG_FILE = LOGS_DIR / f"errors_{datetime.now().strftime('%Y-%m-%d')}.log"


class ColorFormatter(logging.Formatter):
    """Colored formatter for console output"""
    
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


def setup_logging():
    """Setup comprehensive logging to file and console"""
    
    # Clear existing handlers
    root = logging.getLogger()
    root.handlers = []
    root.setLevel(logging.DEBUG)
    
    # File format (detailed)
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-20s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console format (compact)
    console_format = ColorFormatter(
        '%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Main log file handler (all logs)
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_format)
    root.addHandler(file_handler)
    
    # Error log file handler (errors only)
    error_handler = logging.FileHandler(ERROR_LOG_FILE, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_format)
    root.addHandler(error_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_format)
    root.addHandler(console_handler)
    
    # Reduce noise from libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)


# Initialize logging
logger = setup_logging()


# ============ APPLICATION ============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("=" * 60)
    logger.info("KOMAS TRADING SERVER v3.5 - STARTING")
    logger.info(f"Log file: {LOG_FILE}")
    logger.info(f"Error log: {ERROR_LOG_FILE}")
    logger.info("=" * 60)
    
    # Start bots runner
    try:
        from app.core.bots import get_bots_runner
        runner = get_bots_runner()
        runner.start()
        logger.info("✓ Bots runner started")
    except Exception as e:
        logger.warning(f"✗ Failed to start bots runner: {e}")
    
    yield
    
    # Stop bots runner
    try:
        from app.core.bots import get_bots_runner
        runner = get_bots_runner()
        runner.stop()
        logger.info("✓ Bots runner stopped")
    except Exception as e:
        logger.warning(f"✗ Failed to stop bots runner: {e}")
    
    logger.info("=" * 60)
    logger.info("KOMAS TRADING SERVER - SHUTDOWN")
    logger.info("=" * 60)


# Create FastAPI app
app = FastAPI(
    title="Komas Trading Server",
    version="3.5",
    description="Full trading system with indicator, backtesting, optimization, and automated bots",
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


# ============ REQUEST LOGGING MIDDLEWARE ============

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing"""
    request_id = datetime.now().strftime('%H%M%S%f')[:10]
    
    # Log request
    logger.debug(f"[{request_id}] {request.method} {request.url.path}")
    
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration = (time.time() - start_time) * 1000  # ms
        
        # Log response
        status_emoji = "✓" if response.status_code < 400 else "✗"
        logger.info(f"[{request_id}] {status_emoji} {request.method} {request.url.path} - {response.status_code} ({duration:.0f}ms)")
        
        return response
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        logger.error(f"[{request_id}] ✗ {request.method} {request.url.path} - ERROR ({duration:.0f}ms)")
        logger.error(f"[{request_id}] Exception: {str(e)}")
        logger.error(f"[{request_id}] Traceback:\n{traceback.format_exc()}")
        raise


# ============ GLOBAL EXCEPTION HANDLER ============

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

try:
    from app.api.routes import router as main_router
    app.include_router(main_router, prefix="/api")
    logger.info("✓ Loaded: main routes")
except ImportError as e:
    logger.warning(f"✗ Failed to load main routes: {e}")

try:
    from app.api.optimizer_routes import router as optimizer_router
    app.include_router(optimizer_router)
    logger.info("✓ Loaded: optimizer routes")
except ImportError as e:
    logger.warning(f"✗ Failed to load optimizer routes: {e}")

try:
    from app.api.data_routes import router as data_router
    app.include_router(data_router)
    logger.info("✓ Loaded: data routes")
except ImportError as e:
    logger.warning(f"✗ Failed to load data routes: {e}")

try:
    from app.api.indicator_routes import router as indicator_router
    app.include_router(indicator_router)
    logger.info("✓ Loaded: indicator routes")
except ImportError as e:
    logger.warning(f"✗ Failed to load indicator routes: {e}")

try:
    from app.api.signals_routes import router as signals_router
    app.include_router(signals_router)
    logger.info("✓ Loaded: signals routes")
except ImportError as e:
    logger.warning(f"✗ Failed to load signals routes: {e}")

try:
    from app.api.notifications_routes import router as notifications_router
    app.include_router(notifications_router)
    logger.info("✓ Loaded: notifications routes")
except ImportError as e:
    logger.warning(f"✗ Failed to load notifications routes: {e}")

try:
    from app.api.bots_routes import router as bots_router
    app.include_router(bots_router)
    logger.info("✓ Loaded: bots routes")
except ImportError as e:
    logger.warning(f"✗ Failed to load bots routes: {e}")


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
        "version": "3.5",
        "log_file": str(LOG_FILE),
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    return {
        "message": "Komas Trading Server",
        "version": "3.5",
        "docs": "/docs",
        "logs": "/api/logs/list",
        "bots": "/api/bots/"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
