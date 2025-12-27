"""
Komas Trading Server - Preset Tests
===================================
Unit tests for Dominant presets database and API.

Run:
    pytest tests/test_presets.py -v
"""
import pytest
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.database.presets_db import (
    ensure_presets_table,
    create_preset,
    get_preset,
    get_preset_by_name,
    list_presets,
    count_presets,
    update_preset,
    delete_preset,
    delete_presets_by_source,
    bulk_create_presets,
    get_preset_stats
)
from app.models.preset_models import (
    DominantParams,
    PresetCreate,
    DominantPresetCreate,
    PresetResponse
)
from app.migrations.seed_dominant_presets import GG_PRESETS, seed_all_dominant_presets


class TestPresetModels:
    """Test Pydantic models"""
    
    def test_dominant_params_valid(self):
        """Test valid Dominant params"""
        params = DominantParams(
            sensitivity=21,
            tp1_percent=1.0,
            tp2_percent=2.0,
            tp3_percent=3.0,
            tp4_percent=5.0,
            sl_percent=2.0,
            filter_type=0,
            sl_mode=0
        )
        assert params.sensitivity == 21
        assert params.filter_type == 0
    
    def test_dominant_params_validation(self):
        """Test param validation"""
        with pytest.raises(ValueError):
            DominantParams(
                sensitivity=0,  # Invalid - too low
                tp1_percent=1.0,
                tp2_percent=2.0,
                tp3_percent=3.0,
                tp4_percent=5.0,
                sl_percent=2.0
            )
    
    def test_dominant_preset_create(self):
        """Test DominantPresetCreate model"""
        preset = DominantPresetCreate(
            name="Test Preset",
            sensitivity=25,
            tp1_percent=1.0,
            tp2_percent=2.0,
            tp3_percent=3.0,
            tp4_percent=5.0,
            sl_percent=2.0,
            filter_type=1,
            category="mid-term"
        )
        
        generic = preset.to_preset_create()
        assert generic.indicator_type == "dominant"
        assert generic.params["sensitivity"] == 25
        assert generic.params["filter_type"] == 1


class TestPresetDatabase:
    """Test database operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup before each test"""
        ensure_presets_table()
        # Clean test presets
        delete_presets_by_source("test")
    
    def test_create_preset(self):
        """Test creating a preset"""
        preset = create_preset(
            name="Test Preset DB",
            indicator_type="dominant",
            category="mid-term",
            source="test",
            params={
                "sensitivity": 21,
                "tp1_percent": 1.0,
                "tp2_percent": 2.0,
                "tp3_percent": 3.0,
                "tp4_percent": 5.0,
                "sl_percent": 2.0,
                "filter_type": 0,
                "sl_mode": 0
            }
        )
        
        assert preset is not None
        assert preset["name"] == "Test Preset DB"
        assert preset["indicator_type"] == "dominant"
        assert preset["params"]["sensitivity"] == 21
        
        # Cleanup
        delete_preset(preset["id"])
    
    def test_get_preset(self):
        """Test getting preset by ID"""
        # Create first
        created = create_preset(
            name="Get Test",
            indicator_type="dominant",
            source="test",
            params={"sensitivity": 25, "tp1_percent": 1.0, "tp2_percent": 2.0, "tp3_percent": 3.0, "tp4_percent": 5.0, "sl_percent": 2.0}
        )
        
        # Get by ID
        fetched = get_preset(created["id"])
        assert fetched is not None
        assert fetched["name"] == "Get Test"
        
        # Cleanup
        delete_preset(created["id"])
    
    def test_list_presets(self):
        """Test listing presets with filters"""
        # Create test presets
        for i in range(3):
            create_preset(
                name=f"List Test {i}",
                indicator_type="dominant",
                category="short-term" if i < 2 else "mid-term",
                source="test",
                params={"sensitivity": 20 + i, "tp1_percent": 1.0, "tp2_percent": 2.0, "tp3_percent": 3.0, "tp4_percent": 5.0, "sl_percent": 2.0}
            )
        
        # List all test presets
        all_presets = list_presets(source="test")
        assert len(all_presets) >= 3
        
        # Filter by category
        short_term = list_presets(source="test", category="short-term")
        assert len(short_term) >= 2
        
        # Cleanup
        delete_presets_by_source("test")
    
    def test_update_preset(self):
        """Test updating preset"""
        created = create_preset(
            name="Update Test",
            indicator_type="dominant",
            source="test",
            params={"sensitivity": 21, "tp1_percent": 1.0, "tp2_percent": 2.0, "tp3_percent": 3.0, "tp4_percent": 5.0, "sl_percent": 2.0}
        )
        
        # Update
        updated = update_preset(
            created["id"],
            name="Update Test Modified",
            is_favorite=True
        )
        
        assert updated is not None
        assert updated["name"] == "Update Test Modified"
        assert updated["is_favorite"] == True
        
        # Cleanup
        delete_preset(created["id"])
    
    def test_delete_preset(self):
        """Test deleting preset"""
        created = create_preset(
            name="Delete Test",
            indicator_type="dominant",
            source="test",
            params={"sensitivity": 21, "tp1_percent": 1.0, "tp2_percent": 2.0, "tp3_percent": 3.0, "tp4_percent": 5.0, "sl_percent": 2.0}
        )
        
        # Delete
        deleted = delete_preset(created["id"])
        assert deleted == True
        
        # Verify gone
        assert get_preset(created["id"]) is None
    
    def test_count_presets(self):
        """Test counting presets"""
        initial_count = count_presets(source="test")
        
        # Create some
        for i in range(5):
            create_preset(
                name=f"Count Test {i}",
                indicator_type="dominant",
                source="test",
                params={"sensitivity": 20, "tp1_percent": 1.0, "tp2_percent": 2.0, "tp3_percent": 3.0, "tp4_percent": 5.0, "sl_percent": 2.0}
            )
        
        new_count = count_presets(source="test")
        assert new_count == initial_count + 5
        
        # Cleanup
        delete_presets_by_source("test")
    
    def test_get_stats(self):
        """Test getting preset statistics"""
        stats = get_preset_stats()
        
        assert "total_presets" in stats
        assert "by_indicator" in stats
        assert "by_category" in stats
        assert "by_source" in stats


class TestGGPresets:
    """Test GG presets migration"""
    
    def test_gg_presets_count(self):
        """Verify GG presets count"""
        assert len(GG_PRESETS) >= 100  # Should have 125 presets
    
    def test_gg_presets_structure(self):
        """Verify GG presets have required fields"""
        for preset in GG_PRESETS[:10]:  # Check first 10
            assert "name" in preset
            assert "sensitivity" in preset
            assert "tp_percents" in preset
            assert "sl_percent" in preset
            assert len(preset["tp_percents"]) == 4
    
    def test_gg_presets_categories(self):
        """Verify GG presets have valid categories"""
        valid_categories = {"scalp", "short-term", "mid-term", "swing", "long-term", "special"}
        
        for preset in GG_PRESETS:
            assert preset.get("category", "mid-term") in valid_categories
    
    def test_seed_presets(self):
        """Test seeding presets (full migration)"""
        # Delete existing to ensure clean test
        delete_presets_by_source("pine_script")
        
        # Seed
        result = seed_all_dominant_presets()
        
        assert result["created"] > 0
        assert result["errors"] == 0
        
        # Verify count
        total = count_presets(indicator_type="dominant", source="pine_script")
        assert total >= 100


# ============ RUN TESTS ============

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
