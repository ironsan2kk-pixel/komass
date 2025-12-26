"""
Tests for Komas Settings API
============================
"""

import pytest
import json
import tempfile
from pathlib import Path


class TestSettingsAPI:
    """Tests for Settings API functions"""
    
    def test_mask_key(self):
        """Test API key masking"""
        from backend.app.api.settings_routes import mask_key
        
        # Test normal key
        assert mask_key("abc123def456") == "abc1********f456"
        
        # Test short key
        assert mask_key("short") == "shor*"
        
        # Test empty key
        assert mask_key("") == ""
        assert mask_key(None) == ""
    
    def test_load_save_json(self):
        """Test JSON file operations"""
        from backend.app.api.settings_routes import load_json_file, save_json_file
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.json"
            test_data = {"key": "value", "number": 123}
            
            # Test save
            result = save_json_file(test_file, test_data)
            assert result == True
            assert test_file.exists()
            
            # Test load
            loaded = load_json_file(test_file)
            assert loaded == test_data
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent file returns default"""
        from backend.app.api.settings_routes import load_json_file
        
        result = load_json_file(Path("/nonexistent/path.json"), {"default": True})
        assert result == {"default": True}
    
    def test_system_settings_model(self):
        """Test SystemSettings Pydantic model"""
        from backend.app.api.settings_routes import SystemSettings
        
        settings = SystemSettings()
        assert settings.log_level == "INFO"
        assert settings.log_retention_days == 30
        assert settings.auto_backup == False
        
        # Test with custom values
        settings = SystemSettings(
            log_level="DEBUG",
            log_retention_days=7,
            auto_backup=True
        )
        assert settings.log_level == "DEBUG"
        assert settings.log_retention_days == 7
        assert settings.auto_backup == True
    
    def test_notification_settings_model(self):
        """Test NotificationSettings Pydantic model"""
        from backend.app.api.settings_routes import NotificationSettings
        
        settings = NotificationSettings()
        assert settings.telegram_enabled == False
        assert settings.discord_enabled == False
        
        # Test with values
        settings = NotificationSettings(
            telegram_enabled=True,
            telegram_bot_token="123:ABC",
            telegram_chat_id="456"
        )
        assert settings.telegram_enabled == True
        assert settings.telegram_bot_token == "123:ABC"


class TestIntegration:
    """Integration tests"""
    
    def test_settings_dir_creation(self):
        """Test that SETTINGS_DIR exists or can be created"""
        from backend.app.api.settings_routes import SETTINGS_DIR
        
        # Directory should exist or be creatable
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        assert SETTINGS_DIR.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
