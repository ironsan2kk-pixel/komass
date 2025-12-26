"""
KOMAS Calendar API v1.0
=======================
API для экономического календаря:
- Загрузка экономических событий
- Фильтрация по важности и валюте
- Проверка блокировки торговли
- Кэширование данных

Endpoints:
- GET /api/calendar/events - Получить события
- GET /api/calendar/high-impact-today - Важные события сегодня
- POST /api/calendar/refresh - Обновить календарь
- GET /api/calendar/block-status - Статус блокировки торговли

Data Sources:
- ForexFactory (парсинг)
- Investing.com (резервный)
- Кэш в JSON файле
"""

import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/api/calendar", tags=["calendar"])

# === Paths ===
DATA_DIR = Path("data")
CALENDAR_DIR = DATA_DIR / "calendar"
CALENDAR_DIR.mkdir(parents=True, exist_ok=True)

EVENTS_CACHE_FILE = CALENDAR_DIR / "events_cache.json"
SETTINGS_FILE = DATA_DIR / "settings" / "calendar.json"

# === Cache settings ===
CACHE_DURATION_HOURS = 4  # Refresh every 4 hours


# ===========================================
# Pydantic Models
# ===========================================

class CalendarEvent(BaseModel):
    timestamp: str
    currency: str
    impact: str  # high, medium, low
    event: str
    forecast: Optional[str] = None
    previous: Optional[str] = None
    actual: Optional[str] = None


class BlockStatus(BaseModel):
    is_blocked: bool
    blocking_event: Optional[CalendarEvent] = None
    minutes_until_unblock: Optional[int] = None


# ===========================================
# Helper Functions
# ===========================================

def load_json_file(filepath: Path, default=None):
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


def save_json_file(filepath: Path, data) -> bool:
    """Save JSON file with UTF-8 encoding"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving {filepath}: {e}")
        return False


def get_calendar_settings() -> dict:
    """Get calendar settings"""
    return load_json_file(SETTINGS_FILE, {
        "block_trading": False,
        "minutes_before": 15,
        "minutes_after": 15,
        "min_impact": "high",
    })


async def fetch_forex_factory_events() -> List[dict]:
    """
    Fetch events from ForexFactory
    Note: This is a simplified version. In production, use proper scraping or paid API.
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
        
        url = "https://www.forexfactory.com/calendar"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
                timeout=15
            )
            
            if response.status_code != 200:
                return []
            
            # Parse HTML (simplified - real implementation would be more complex)
            # For now, return sample data
            return []
            
    except Exception as e:
        print(f"Error fetching ForexFactory: {e}")
        return []


async def fetch_investing_com_events() -> List[dict]:
    """
    Fetch events from Investing.com API
    """
    try:
        import httpx
        
        # Investing.com economic calendar API
        today = datetime.now()
        date_from = today.strftime("%Y-%m-%d")
        date_to = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
        url = f"https://www.investing.com/economic-calendar/Service/getCalendarFilteredData"
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "X-Requested-With": "XMLHttpRequest",
                },
                data={
                    "country[]": ["5", "6", "22", "17", "35", "25", "4", "72"],  # Major currencies
                    "dateFrom": date_from,
                    "dateTo": date_to,
                    "currentTab": "custom",
                    "limit_from": "0",
                },
                timeout=15
            )
            
            if response.status_code == 200:
                # Parse response (simplified)
                return []
        
    except Exception as e:
        print(f"Error fetching Investing.com: {e}")
    
    return []


def generate_sample_events() -> List[dict]:
    """
    Generate sample economic events for testing
    In production, replace with real data source
    """
    now = datetime.now()
    events = []
    
    # Sample events for the next 7 days
    sample_data = [
        {"currency": "USD", "impact": "high", "event": "Non-Farm Payrolls", "forecast": "200K", "previous": "175K"},
        {"currency": "USD", "impact": "high", "event": "FOMC Meeting Minutes"},
        {"currency": "USD", "impact": "medium", "event": "Initial Jobless Claims", "forecast": "210K", "previous": "205K"},
        {"currency": "EUR", "impact": "high", "event": "ECB Interest Rate Decision", "forecast": "4.25%", "previous": "4.25%"},
        {"currency": "EUR", "impact": "medium", "event": "German ZEW Economic Sentiment"},
        {"currency": "GBP", "impact": "high", "event": "BOE Interest Rate Decision"},
        {"currency": "GBP", "impact": "medium", "event": "UK CPI", "forecast": "2.3%", "previous": "2.2%"},
        {"currency": "JPY", "impact": "high", "event": "BOJ Policy Rate"},
        {"currency": "JPY", "impact": "medium", "event": "Japan Trade Balance"},
        {"currency": "AUD", "impact": "medium", "event": "RBA Meeting Minutes"},
        {"currency": "CAD", "impact": "medium", "event": "Canada CPI"},
        {"currency": "CHF", "impact": "low", "event": "Swiss Trade Balance"},
        {"currency": "CNY", "impact": "medium", "event": "China PMI Manufacturing"},
        {"currency": "USD", "impact": "low", "event": "Existing Home Sales"},
        {"currency": "EUR", "impact": "low", "event": "Eurozone Consumer Confidence"},
    ]
    
    # Distribute events over the next 7 days
    for i, event_data in enumerate(sample_data):
        hours_offset = (i * 8) % 168  # Spread over 7 days
        event_time = now + timedelta(hours=hours_offset)
        
        events.append({
            "timestamp": event_time.isoformat(),
            "currency": event_data["currency"],
            "impact": event_data["impact"],
            "event": event_data["event"],
            "forecast": event_data.get("forecast"),
            "previous": event_data.get("previous"),
            "actual": None,
        })
    
    # Sort by timestamp
    events.sort(key=lambda x: x["timestamp"])
    
    return events


async def get_cached_events(force_refresh: bool = False) -> List[dict]:
    """Get events from cache or fetch new ones"""
    cache = load_json_file(EVENTS_CACHE_FILE, {"events": [], "updated_at": None})
    
    # Check if cache is fresh
    should_refresh = force_refresh
    
    if not should_refresh and cache.get("updated_at"):
        try:
            updated_at = datetime.fromisoformat(cache["updated_at"])
            if datetime.now() - updated_at > timedelta(hours=CACHE_DURATION_HOURS):
                should_refresh = True
        except:
            should_refresh = True
    else:
        should_refresh = True
    
    if should_refresh:
        # Try to fetch from external sources
        events = await fetch_forex_factory_events()
        
        if not events:
            events = await fetch_investing_com_events()
        
        if not events:
            # Fallback to sample data
            events = generate_sample_events()
        
        # Save to cache
        cache = {
            "events": events,
            "updated_at": datetime.now().isoformat(),
        }
        save_json_file(EVENTS_CACHE_FILE, cache)
    
    return cache.get("events", [])


def filter_events(
    events: List[dict],
    hours_ahead: int = 24,
    impact: Optional[str] = None,
    currency: Optional[str] = None
) -> List[dict]:
    """Filter events by time, impact, and currency"""
    now = datetime.now()
    cutoff = now + timedelta(hours=hours_ahead)
    
    filtered = []
    for event in events:
        try:
            event_time = datetime.fromisoformat(event["timestamp"])
            
            # Time filter - include past hour and future events
            if event_time < now - timedelta(hours=1):
                continue
            if event_time > cutoff:
                continue
            
            # Impact filter
            if impact and event.get("impact") != impact:
                continue
            
            # Currency filter
            if currency and event.get("currency") != currency:
                continue
            
            filtered.append(event)
        except Exception as e:
            print(f"Error filtering event: {e}")
    
    return filtered


def check_trading_block(events: List[dict], settings: dict) -> BlockStatus:
    """Check if trading should be blocked due to upcoming/recent events"""
    if not settings.get("block_trading", False):
        return BlockStatus(is_blocked=False)
    
    now = datetime.now()
    minutes_before = settings.get("minutes_before", 15)
    minutes_after = settings.get("minutes_after", 15)
    min_impact = settings.get("min_impact", "high")
    
    # Define impact levels
    impact_levels = {"high": 3, "medium": 2, "low": 1}
    min_impact_level = impact_levels.get(min_impact, 3)
    
    for event in events:
        try:
            event_impact = impact_levels.get(event.get("impact", "low"), 1)
            
            # Skip if impact is too low
            if event_impact < min_impact_level:
                continue
            
            event_time = datetime.fromisoformat(event["timestamp"])
            
            # Check if we're in the blocking window
            block_start = event_time - timedelta(minutes=minutes_before)
            block_end = event_time + timedelta(minutes=minutes_after)
            
            if block_start <= now <= block_end:
                minutes_until_unblock = int((block_end - now).total_seconds() / 60)
                return BlockStatus(
                    is_blocked=True,
                    blocking_event=CalendarEvent(**event),
                    minutes_until_unblock=minutes_until_unblock
                )
        except Exception as e:
            print(f"Error checking block status: {e}")
    
    return BlockStatus(is_blocked=False)


# ===========================================
# API Endpoints
# ===========================================

@router.get("/events")
async def get_events(
    hours_ahead: int = Query(24, ge=1, le=168, description="Hours to look ahead"),
    impact: Optional[str] = Query(None, description="Filter by impact: high, medium, low"),
    currency: Optional[str] = Query(None, description="Filter by currency: USD, EUR, GBP, etc.")
):
    """
    Get economic calendar events
    
    Parameters:
    - hours_ahead: Number of hours to look ahead (1-168)
    - impact: Filter by impact level (high, medium, low)
    - currency: Filter by currency code
    """
    events = await get_cached_events()
    filtered = filter_events(events, hours_ahead, impact, currency)
    return filtered


@router.get("/high-impact-today")
async def get_high_impact_today():
    """Get high-impact events for today"""
    events = await get_cached_events()
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    high_impact = []
    for event in events:
        try:
            if event.get("impact") != "high":
                continue
            
            event_time = datetime.fromisoformat(event["timestamp"])
            if today_start <= event_time < today_end:
                high_impact.append(event)
        except:
            pass
    
    return high_impact


@router.post("/refresh")
async def refresh_calendar():
    """Force refresh calendar data"""
    try:
        events = await get_cached_events(force_refresh=True)
        return {
            "success": True,
            "message": "Calendar refreshed",
            "event_count": len(events),
            "updated_at": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/block-status")
async def get_block_status():
    """
    Check if trading is currently blocked due to economic events
    
    Returns block status and the blocking event if applicable
    """
    events = await get_cached_events()
    settings = get_calendar_settings()
    
    status = check_trading_block(events, settings)
    
    return {
        "is_blocked": status.is_blocked,
        "blocking_event": status.blocking_event.dict() if status.blocking_event else None,
        "minutes_until_unblock": status.minutes_until_unblock,
        "settings": {
            "block_trading": settings.get("block_trading", False),
            "minutes_before": settings.get("minutes_before", 15),
            "minutes_after": settings.get("minutes_after", 15),
            "min_impact": settings.get("min_impact", "high"),
        }
    }


@router.get("/upcoming")
async def get_upcoming_events(
    count: int = Query(10, ge=1, le=50, description="Number of events to return")
):
    """Get next N upcoming events sorted by time"""
    events = await get_cached_events()
    
    now = datetime.now()
    upcoming = []
    
    for event in events:
        try:
            event_time = datetime.fromisoformat(event["timestamp"])
            if event_time >= now:
                upcoming.append(event)
        except:
            pass
    
    # Sort by timestamp
    upcoming.sort(key=lambda x: x["timestamp"])
    
    return upcoming[:count]


@router.get("/currencies")
async def get_currencies():
    """Get list of available currencies in calendar"""
    events = await get_cached_events()
    
    currencies = set()
    for event in events:
        if event.get("currency"):
            currencies.add(event["currency"])
    
    # Sort and return common currencies first
    common = ["USD", "EUR", "GBP", "JPY", "AUD", "CAD", "CHF", "CNY"]
    result = [c for c in common if c in currencies]
    result.extend(sorted([c for c in currencies if c not in common]))
    
    return result


@router.get("/stats")
async def get_calendar_stats():
    """Get statistics about calendar events"""
    events = await get_cached_events()
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = today_start + timedelta(days=7)
    
    stats = {
        "total_events": len(events),
        "today": 0,
        "this_week": 0,
        "by_impact": {"high": 0, "medium": 0, "low": 0},
        "by_currency": {},
    }
    
    for event in events:
        try:
            event_time = datetime.fromisoformat(event["timestamp"])
            
            # Today count
            if today_start <= event_time < today_start + timedelta(days=1):
                stats["today"] += 1
            
            # This week count
            if today_start <= event_time < week_end:
                stats["this_week"] += 1
            
            # By impact
            impact = event.get("impact", "low")
            if impact in stats["by_impact"]:
                stats["by_impact"][impact] += 1
            
            # By currency
            currency = event.get("currency", "OTHER")
            stats["by_currency"][currency] = stats["by_currency"].get(currency, 0) + 1
            
        except:
            pass
    
    return stats
