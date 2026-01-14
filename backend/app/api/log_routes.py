"""
Log API Routes
==============
Endpoints for accessing logs and errors from UI.
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query
from pathlib import Path
import re

from app.core.errors import error_storage


router = APIRouter(prefix="/api/logs", tags=["Logs"])


# ═══════════════════════════════════════════════════════════════
# ERROR ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get("/errors")
async def get_errors(
    limit: int = Query(50, ge=1, le=500),
    error_type: Optional[str] = None
):
    """Get recent errors from error storage"""
    errors = error_storage.get_recent(limit=limit, error_type=error_type)
    stats = error_storage.get_stats()

    return {
        "errors": errors,
        "count": len(errors),
        "stats": stats
    }


@router.get("/errors/stats")
async def get_error_stats():
    """Get error statistics"""
    return error_storage.get_stats()


@router.delete("/errors")
async def clear_errors():
    """Clear all stored errors"""
    error_storage.clear()
    return {"status": "ok", "message": "Error storage cleared"}


# ═══════════════════════════════════════════════════════════════
# FILE LOG ENDPOINTS
# ═══════════════════════════════════════════════════════════════

LOGS_DIR = Path(__file__).parent.parent.parent / "logs"


@router.get("/recent")
async def get_recent_logs(
    lines: int = Query(100, ge=10, le=1000),
    level: Optional[str] = Query(None, description="Filter by level: DEBUG, INFO, WARNING, ERROR"),
    search: Optional[str] = Query(None, description="Search pattern in log messages")
):
    """Get recent log entries from file"""

    # Find today's log file
    today = datetime.now().strftime('%Y-%m-%d')
    log_file = LOGS_DIR / f"komas_{today}.log"

    if not log_file.exists():
        return {"logs": [], "file": str(log_file), "exists": False}

    # Read last N lines
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
    except Exception as e:
        return {"error": str(e), "file": str(log_file)}

    # Take last N lines
    log_lines = all_lines[-lines:]

    # Parse log entries
    entries = []
    log_pattern = re.compile(
        r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| (\w+)\s*\| ([^|]+)\| ([^|]+)\| (.+)'
    )

    for line in log_lines:
        match = log_pattern.match(line.strip())
        if match:
            timestamp, log_level, logger_name, func_name, message = match.groups()
            entry = {
                "timestamp": timestamp,
                "level": log_level.strip(),
                "logger": logger_name.strip(),
                "function": func_name.strip(),
                "message": message.strip()
            }

            # Apply level filter
            if level and entry["level"] != level.upper():
                continue

            # Apply search filter
            if search and search.lower() not in entry["message"].lower():
                continue

            entries.append(entry)

    return {
        "logs": entries,
        "count": len(entries),
        "file": str(log_file),
        "total_lines": len(all_lines)
    }


@router.get("/files")
async def list_log_files():
    """List available log files"""
    if not LOGS_DIR.exists():
        return {"files": [], "directory": str(LOGS_DIR)}

    files = []
    for log_file in sorted(LOGS_DIR.glob("*.log"), reverse=True):
        stat = log_file.stat()
        files.append({
            "name": log_file.name,
            "size": stat.st_size,
            "size_kb": round(stat.st_size / 1024, 1),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })

    return {"files": files, "directory": str(LOGS_DIR)}


@router.get("/file/{filename}")
async def get_log_file(
    filename: str,
    lines: int = Query(200, ge=10, le=2000),
    offset: int = Query(0, ge=0)
):
    """Get contents of specific log file"""
    log_file = LOGS_DIR / filename

    # Security: prevent directory traversal
    if ".." in filename or "/" in filename:
        return {"error": "Invalid filename"}

    if not log_file.exists():
        return {"error": f"File not found: {filename}"}

    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()

        # Apply offset and limit
        total = len(all_lines)
        start = max(0, total - offset - lines)
        end = total - offset
        selected_lines = all_lines[start:end]

        return {
            "filename": filename,
            "lines": selected_lines,
            "count": len(selected_lines),
            "total": total,
            "offset": offset
        }
    except Exception as e:
        return {"error": str(e)}


@router.delete("/file/{filename}")
async def delete_log_file(filename: str):
    """Delete a log file"""
    log_file = LOGS_DIR / filename

    # Security: prevent directory traversal
    if ".." in filename or "/" in filename:
        return {"error": "Invalid filename"}

    if not log_file.exists():
        return {"error": f"File not found: {filename}"}

    try:
        log_file.unlink()
        return {"status": "ok", "message": f"Deleted: {filename}"}
    except Exception as e:
        return {"error": str(e)}
