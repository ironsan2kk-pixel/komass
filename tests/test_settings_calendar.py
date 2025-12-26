"""
Tests for Settings and Calendar API
====================================
Comprehensive tests for new API modules
"""

import pytest
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Test Settings Routes
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSettingsAPI:
    """Tests for Settings API endpoints"""
    
    def test_mask_key(self):
        """Test API key masking"""
        from backend.app.api.settings_routes import mask_key
        
        # Normal key
        assert mask_key("abcd1234efgh5678") == "abcd****5678"
        
        # Short key
        assert mask_key("short") == "****"
        
        # Empty key
        assert mask_key("") == "****"
        assert mask_key(None) == "****"
    
    def test_load_save_json(self):
        """Test JSON file operations"""
        from backend.app.api.settings_routes import load_json_file, save_json_file
        
        test_file = Path("data/settings/test_settings.json")
        test_data = {"key": "value", "number": 123}
        
        # Save
        result = save_json_file(test_file, test_data)
        assert result is True
        
        # Load
        loaded = load_json_file(test_file)
        assert loaded == test_data
        
        # Cleanup
        if test_file.exists():
            test_file.unlink()
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent file returns default"""
        from backend.app.api.settings_routes import load_json_file
        
        result = load_json_file(Path("nonexistent.json"), {"default": True})
        assert result == {"default": True}
    
    def test_system_settings_model(self):
        """Test SystemSettings model validation"""
        from backend.app.api.settings_routes import SystemSettings
        
        settings = SystemSettings(
            auto_start=True,
            log_level="DEBUG",
            max_log_size_mb=50,
            data_retention_days=30,
            backup_enabled=True,
            backup_interval_hours=12
        )
        
        assert settings.auto_start is True
        assert settings.log_level == "DEBUG"
        assert settings.max_log_size_mb == 50
    
    def test_calendar_settings_model(self):
        """Test CalendarSettings model validation"""
        from backend.app.api.settings_routes import CalendarSettings
        
        settings = CalendarSettings(
            block_trading=True,
            minutes_before=30,
            minutes_after=30,
            min_impact="medium"
        )
        
        assert settings.block_trading is True
        assert settings.minutes_before == 30
        assert settings.min_impact == "medium"


class TestCalendarAPI:
    """Tests for Calendar API endpoints"""
    
    def test_generate_sample_events(self):
        """Test sample events generation"""
        from backend.app.api.calendar_routes import generate_sample_events
        
        events = generate_sample_events()
        
        assert len(events) > 0
        assert all("timestamp" in e for e in events)
        assert all("currency" in e for e in events)
        assert all("impact" in e for e in events)
        assert all("event" in e for e in events)
    
    def test_filter_events_by_impact(self):
        """Test filtering events by impact"""
        from backend.app.api.calendar_routes import filter_events, generate_sample_events
        
        events = generate_sample_events()
        
        high_impact = filter_events(events, hours_ahead=168, impact="high")
        
        assert all(e["impact"] == "high" for e in high_impact)
    
    def test_filter_events_by_currency(self):
        """Test filtering events by currency"""
        from backend.app.api.calendar_routes import filter_events, generate_sample_events
        
        events = generate_sample_events()
        
        usd_events = filter_events(events, hours_ahead=168, currency="USD")
        
        assert all(e["currency"] == "USD" for e in usd_events)
    
    def test_filter_events_time_window(self):
        """Test filtering events by time window"""
        from backend.app.api.calendar_routes import filter_events, generate_sample_events
        
        events = generate_sample_events()
        
        # Filter for next 24 hours
        filtered_24h = filter_events(events, hours_ahead=24)
        
        # Filter for next 168 hours (7 days)
        filtered_week = filter_events(events, hours_ahead=168)
        
        # Week should have more or equal events
        assert len(filtered_week) >= len(filtered_24h)
    
    def test_check_trading_block_disabled(self):
        """Test block check when disabled"""
        from backend.app.api.calendar_routes import check_trading_block
        
        events = [
            {
                "timestamp": datetime.now().isoformat(),
                "currency": "USD",
                "impact": "high",
                "event": "Test Event"
            }
        ]
        
        settings = {"block_trading": False}
        
        status = check_trading_block(events, settings)
        
        assert status.is_blocked is False
    
    def test_check_trading_block_enabled(self):
        """Test block check when enabled and event is happening"""
        from backend.app.api.calendar_routes import check_trading_block
        
        # Event happening right now
        events = [
            {
                "timestamp": datetime.now().isoformat(),
                "currency": "USD",
                "impact": "high",
                "event": "FOMC Meeting"
            }
        ]
        
        settings = {
            "block_trading": True,
            "minutes_before": 15,
            "minutes_after": 15,
            "min_impact": "high"
        }
        
        status = check_trading_block(events, settings)
        
        assert status.is_blocked is True
        assert status.blocking_event is not None
        assert status.blocking_event.event == "FOMC Meeting"
    
    def test_check_trading_block_low_impact_ignored(self):
        """Test that low impact events don't block when min_impact is high"""
        from backend.app.api.calendar_routes import check_trading_block
        
        events = [
            {
                "timestamp": datetime.now().isoformat(),
                "currency": "USD",
                "impact": "low",
                "event": "Minor Report"
            }
        ]
        
        settings = {
            "block_trading": True,
            "minutes_before": 15,
            "minutes_after": 15,
            "min_impact": "high"
        }
        
        status = check_trading_block(events, settings)
        
        assert status.is_blocked is False
    
    def test_calendar_event_model(self):
        """Test CalendarEvent model"""
        from backend.app.api.calendar_routes import CalendarEvent
        
        event = CalendarEvent(
            timestamp="2025-01-01T10:00:00",
            currency="USD",
            impact="high",
            event="Non-Farm Payrolls",
            forecast="200K",
            previous="180K"
        )
        
        assert event.currency == "USD"
        assert event.impact == "high"
        assert event.forecast == "200K"


class TestIntegration:
    """Integration tests"""
    
    def test_settings_dir_creation(self):
        """Test that settings directory is created"""
        from backend.app.api.settings_routes import SETTINGS_DIR
        
        assert SETTINGS_DIR.exists()
    
    def test_calendar_dir_creation(self):
        """Test that calendar directory is created"""
        from backend.app.api.calendar_routes import CALENDAR_DIR
        
        assert CALENDAR_DIR.exists()


def run_tests():
    """Run all tests"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_tests()
