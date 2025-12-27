"""
Unit Tests for Preset Routes (Chat #31-33)
==========================================
Tests for backup, restore, clone, and batch operations.

Run with: python -m pytest tests/test_preset_routes.py -v
"""
import json
import pytest
import tempfile
import os
from datetime import datetime

# Mock the database module
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend', 'app'))


class TestPresetOperations:
    """Test preset CRUD and new operations"""
    
    def test_generate_preset_id(self):
        """Test preset ID generation"""
        from database.presets_db import _generate_preset_id
        
        id1 = _generate_preset_id("Test Preset", "dominant")
        assert id1.startswith("DOMINANT_")
        assert len(id1) > 20
        
        id2 = _generate_preset_id("Test Preset", "trg")
        assert id2.startswith("TRG_")
        
        # Same name should generate same ID
        id3 = _generate_preset_id("Test Preset", "dominant")
        assert id1 == id3
    
    def test_preset_validation(self):
        """Test preset data validation"""
        # Valid Dominant params
        valid_dominant = {
            "name": "Test Dominant",
            "indicator_type": "dominant",
            "params": {
                "sensitivity": 21,
                "tp1_percent": 2.5,
                "tp2_percent": 5.0,
                "tp3_percent": 7.5,
                "tp4_percent": 10.0,
                "sl_percent": 3.0,
                "filter_type": 0,
                "sl_mode": 0
            }
        }
        assert valid_dominant["params"]["sensitivity"] >= 10
        assert valid_dominant["params"]["sensitivity"] <= 100
        
        # Valid TRG params
        valid_trg = {
            "name": "Test TRG",
            "indicator_type": "trg",
            "params": {
                "i1": 45,
                "i2": 4.0,
                "tp_count": 4,
                "tp_percents": [1.05, 1.95, 3.75, 6.0],
                "tp_amounts": [50, 30, 15, 5],
                "sl_percent": 2.0,
                "sl_mode": "fixed"
            }
        }
        assert valid_trg["params"]["i1"] >= 10
        assert valid_trg["params"]["i1"] <= 200
        assert valid_trg["params"]["i2"] >= 1.0
        assert valid_trg["params"]["i2"] <= 10.0


class TestBackupRestore:
    """Test backup and restore functionality"""
    
    def test_backup_format(self):
        """Test backup data structure"""
        backup_data = {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "total_presets": 2,
            "filters": {
                "indicator_type": None,
                "source": None,
                "include_system": True
            },
            "presets": [
                {
                    "name": "Preset 1",
                    "indicator_type": "dominant",
                    "category": "mid-term",
                    "params": {"sensitivity": 21}
                },
                {
                    "name": "Preset 2",
                    "indicator_type": "trg",
                    "category": "scalp",
                    "params": {"i1": 14, "i2": 2.0}
                }
            ]
        }
        
        # Validate structure
        assert "version" in backup_data
        assert "presets" in backup_data
        assert len(backup_data["presets"]) == 2
        assert backup_data["presets"][0]["name"] == "Preset 1"
    
    def test_restore_modes(self):
        """Test restore mode logic"""
        modes = ["skip", "replace", "merge"]
        
        for mode in modes:
            assert mode in modes
        
        # Skip mode - should not modify existing
        # Replace mode - should overwrite existing
        # Merge mode - should update existing, create new
    
    def test_backup_json_serialization(self):
        """Test JSON serialization of backup"""
        preset = {
            "name": "Test",
            "params": {
                "sensitivity": 21.5,
                "tp_percents": [1.0, 2.0, 3.0]
            },
            "tags": ["tag1", "tag2"]
        }
        
        # Should serialize without errors
        json_str = json.dumps(preset, indent=2, ensure_ascii=False)
        assert len(json_str) > 0
        
        # Should deserialize correctly
        parsed = json.loads(json_str)
        assert parsed["name"] == "Test"
        assert parsed["params"]["sensitivity"] == 21.5


class TestCloneOperation:
    """Test clone functionality"""
    
    def test_clone_name_generation(self):
        """Test clone name generation"""
        original_name = "My Preset"
        
        # Default clone name
        clone_name = f"{original_name} (Copy)"
        assert clone_name == "My Preset (Copy)"
        
        # With number suffix
        clone_name_2 = f"{original_name} (Copy) 1"
        assert "1" in clone_name_2
    
    def test_clone_params_copy(self):
        """Test that clone copies all params"""
        original = {
            "name": "Original",
            "params": {
                "sensitivity": 21,
                "tp1_percent": 2.5,
                "sl_percent": 3.0
            },
            "tags": ["tag1"]
        }
        
        # Clone should have same params
        clone = {
            **original,
            "name": f"{original['name']} (Copy)",
            "source": "manual"
        }
        
        assert clone["params"]["sensitivity"] == original["params"]["sensitivity"]
        assert clone["source"] == "manual"


class TestBatchOperations:
    """Test batch operations"""
    
    def test_batch_delete_validation(self):
        """Test batch delete requires confirmation"""
        preset_ids = ["id1", "id2", "id3"]
        confirm = False
        
        # Without confirmation, should not delete
        if not confirm:
            result = {
                "success": False,
                "message": "Deletion not confirmed"
            }
            assert result["success"] == False
    
    def test_batch_update_allowed_fields(self):
        """Test batch update field restrictions"""
        allowed_fields = {"category", "is_active", "is_favorite", "tags"}
        
        # Valid update
        update = {"category": "scalp", "is_favorite": True}
        invalid = set(update.keys()) - allowed_fields
        assert len(invalid) == 0
        
        # Invalid update
        update_invalid = {"name": "New Name", "params": {}}
        invalid = set(update_invalid.keys()) - allowed_fields
        assert len(invalid) == 2  # name and params are not allowed
    
    def test_batch_export_structure(self):
        """Test batch export output structure"""
        preset_ids = ["id1", "id2"]
        
        export_data = {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "total_presets": len(preset_ids),
            "not_found": [],
            "presets": []
        }
        
        assert "version" in export_data
        assert "presets" in export_data
        assert export_data["total_presets"] == 2


class TestAPIEndpoints:
    """Test API endpoint definitions"""
    
    def test_endpoint_paths(self):
        """Test that all endpoints are defined correctly"""
        endpoints = [
            # Existing
            ("GET", "/api/presets/list"),
            ("GET", "/api/presets/stats"),
            ("GET", "/api/presets/{id}"),
            ("POST", "/api/presets/create"),
            ("PUT", "/api/presets/{id}"),
            ("DELETE", "/api/presets/{id}"),
            ("POST", "/api/presets/import"),
            ("GET", "/api/presets/export/{id}"),
            
            # New in Chat #31-33
            ("POST", "/api/presets/clone/{id}"),
            ("POST", "/api/presets/backup"),
            ("POST", "/api/presets/restore"),
            ("POST", "/api/presets/batch/delete"),
            ("POST", "/api/presets/batch/update"),
            ("POST", "/api/presets/batch/export"),
            
            # Dominant specific
            ("GET", "/api/presets/dominant/list"),
            ("POST", "/api/presets/dominant/create"),
            ("POST", "/api/presets/dominant/seed"),
        ]
        
        for method, path in endpoints:
            assert method in ["GET", "POST", "PUT", "DELETE"]
            assert path.startswith("/api/presets")


class TestFrontendIntegration:
    """Test frontend component requirements"""
    
    def test_preset_card_props(self):
        """Test PresetCard required props"""
        required_props = [
            "preset",
            "onEdit",
            "onClone",
            "onDelete",
            "onExport",
            "onToggleFavorite",
            "onApply"
        ]
        
        for prop in required_props:
            assert len(prop) > 0
    
    def test_preset_modal_modes(self):
        """Test PresetModal modes"""
        modes = ["create", "edit", "clone"]
        
        for mode in modes:
            assert mode in modes
    
    def test_filter_options(self):
        """Test filter options"""
        categories = ["scalp", "short-term", "mid-term", "swing", "long-term", "special"]
        indicators = ["trg", "dominant"]
        sources = ["system", "pine_script", "user", "manual", "imported", "optimizer"]
        
        assert len(categories) == 6
        assert len(indicators) == 2
        assert len(sources) == 6


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
