"""
Komas Trading Server - Preset Architecture Tests
================================================
Unit tests for the preset system.

Run: python -m pytest tests/test_presets.py -v

Chat: #29 — Presets Architecture
"""

import pytest
import json
from datetime import datetime

# Import preset module
import sys
sys.path.insert(0, 'backend/app')

from presets import (
    # Base
    BasePreset,
    PresetConfig,
    PresetMetrics,
    IndicatorType,
    PresetCategory,
    PresetSource,
    FilterProfile,
    
    # Implementations
    TRGPreset,
    DominantPreset,
    
    # Registry
    PresetRegistry,
    get_registry,
    
    # Validator
    validate_preset,
    validate_params,
    validate_import,
    ValidationSeverity,
    
    # Generator
    generate_trg_presets,
    generate_dominant_presets,
    TRGSystemGenerator,
    DominantSystemGenerator,
)


# ==================== FIXTURES ====================

@pytest.fixture
def trg_params():
    """Default TRG parameters"""
    return {
        "i1": 45,
        "i2": 4.0,
        "tp_count": 4,
        "tp1_percent": 1.05,
        "tp1_amount": 50,
        "tp2_percent": 1.95,
        "tp2_amount": 30,
        "tp3_percent": 3.75,
        "tp3_amount": 15,
        "tp4_percent": 6.0,
        "tp4_amount": 5,
        "sl_percent": 2.0,
        "sl_mode": "fixed",
    }


@pytest.fixture
def dominant_params():
    """Default Dominant parameters"""
    return {
        "sensitivity": 21,
        "tp1_percent": 1.0,
        "tp2_percent": 2.0,
        "tp3_percent": 3.0,
        "tp4_percent": 5.0,
        "sl_percent": 2.0,
        "sl_mode": 0,
        "filter_type": 0,
        "fixed_stop": True,
    }


@pytest.fixture
def trg_config(trg_params):
    """TRG preset config"""
    return PresetConfig(
        id="TRG_TEST_001",
        name="Test TRG Preset",
        indicator_type="trg",
        category="mid-term",
        source="manual",
        params=trg_params,
    )


@pytest.fixture
def dominant_config(dominant_params):
    """Dominant preset config"""
    return PresetConfig(
        id="DOM_TEST_001",
        name="Test Dominant Preset",
        indicator_type="dominant",
        category="mid-term",
        source="manual",
        params=dominant_params,
    )


# ==================== BASE TESTS ====================

class TestPresetConfig:
    """Tests for PresetConfig"""
    
    def test_create_config(self, trg_params):
        config = PresetConfig(
            id="TEST_001",
            name="Test",
            indicator_type="trg",
            params=trg_params
        )
        assert config.id == "TEST_001"
        assert config.name == "Test"
        assert config.indicator_type == "trg"
        assert config.category == "mid-term"  # default
    
    def test_config_to_dict(self, trg_config):
        data = trg_config.to_dict()
        assert "id" in data
        assert "name" in data
        assert "params" in data
        assert data["indicator_type"] == "trg"
    
    def test_config_from_dict(self, trg_params):
        data = {
            "id": "TEST_002",
            "name": "From Dict",
            "indicator_type": "trg",
            "params": trg_params,
        }
        config = PresetConfig.from_dict(data)
        assert config.id == "TEST_002"
        assert config.name == "From Dict"
    
    def test_config_json_roundtrip(self, trg_config):
        json_str = trg_config.to_json()
        restored = PresetConfig.from_json(json_str)
        assert restored.id == trg_config.id
        assert restored.name == trg_config.name
        assert restored.params == trg_config.params


class TestPresetMetrics:
    """Tests for PresetMetrics"""
    
    def test_create_metrics(self):
        metrics = PresetMetrics(
            win_rate=0.65,
            profit_factor=1.8,
            total_profit_percent=45.5
        )
        assert metrics.win_rate == 0.65
        assert metrics.profit_factor == 1.8
    
    def test_metrics_to_dict_excludes_none(self):
        metrics = PresetMetrics(win_rate=0.65)
        data = metrics.to_dict()
        assert "win_rate" in data
        assert "profit_factor" not in data  # None excluded
    
    def test_metrics_from_dict(self):
        data = {"win_rate": 0.7, "sharpe_ratio": 1.5}
        metrics = PresetMetrics.from_dict(data)
        assert metrics.win_rate == 0.7
        assert metrics.sharpe_ratio == 1.5


# ==================== TRG PRESET TESTS ====================

class TestTRGPreset:
    """Tests for TRG Preset"""
    
    def test_create_preset(self, trg_config):
        preset = TRGPreset(trg_config)
        assert preset.id == "TRG_TEST_001"
        assert preset.name == "Test TRG Preset"
        assert preset.INDICATOR_TYPE == "trg"
    
    def test_get_default_params(self):
        config = PresetConfig(
            id="TEST",
            name="Test",
            indicator_type="trg",
            params={}
        )
        preset = TRGPreset(config)
        defaults = preset.get_default_params()
        
        assert "i1" in defaults
        assert "i2" in defaults
        assert defaults["i1"] == 45
        assert defaults["i2"] == 4.0
    
    def test_validate_valid_params(self, trg_config):
        preset = TRGPreset(trg_config)
        is_valid, errors = preset.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_invalid_i1(self, trg_params):
        trg_params["i1"] = 5  # Too low
        config = PresetConfig(
            id="TEST",
            name="Test",
            indicator_type="trg",
            params=trg_params
        )
        preset = TRGPreset(config)
        is_valid, errors = preset.validate()
        assert not is_valid
        assert any("i1" in e for e in errors)
    
    def test_validate_invalid_tp_amounts(self, trg_params):
        trg_params["tp1_amount"] = 40  # Sum != 100
        config = PresetConfig(
            id="TEST",
            name="Test",
            indicator_type="trg",
            params=trg_params
        )
        preset = TRGPreset(config)
        is_valid, errors = preset.validate()
        assert not is_valid
        assert any("100%" in e for e in errors)
    
    def test_calculate_category(self, trg_params):
        config = PresetConfig(
            id="TEST",
            name="Test",
            indicator_type="trg",
            params=trg_params
        )
        preset = TRGPreset(config)
        
        # Test different i1 values
        assert preset.calculate_category({"i1": 15}) == "scalp"
        assert preset.calculate_category({"i1": 30}) == "short-term"
        assert preset.calculate_category({"i1": 60}) == "mid-term"
        assert preset.calculate_category({"i1": 100}) == "swing"
        assert preset.calculate_category({"i1": 180}) == "long-term"
    
    def test_generate_name(self, trg_params):
        config = PresetConfig(
            id="TEST",
            name="Test",
            indicator_type="trg",
            params=trg_params
        )
        preset = TRGPreset(config)
        name = preset.generate_name(trg_params)
        assert name == "N_45_40"  # N filter, i1=45, i2=4.0
    
    def test_create_system_preset(self):
        preset = TRGPreset.create_system_preset(
            i1=60,
            i2=4.0,
            filter_profile=FilterProfile.TREND
        )
        assert preset.id == "TRG_SYS_T_60_40"
        assert preset.params["i1"] == 60
        assert preset.params["i2"] == 4.0
        assert preset.params["supertrend_enabled"] == True
    
    def test_generate_all_system_presets(self):
        presets = TRGPreset.generate_all_system_presets()
        assert len(presets) == 200  # 8 × 5 × 5
        
        # Check unique IDs
        ids = [p.id for p in presets]
        assert len(ids) == len(set(ids))


# ==================== DOMINANT PRESET TESTS ====================

class TestDominantPreset:
    """Tests for Dominant Preset"""
    
    def test_create_preset(self, dominant_config):
        preset = DominantPreset(dominant_config)
        assert preset.id == "DOM_TEST_001"
        assert preset.INDICATOR_TYPE == "dominant"
    
    def test_validate_valid_params(self, dominant_config):
        preset = DominantPreset(dominant_config)
        is_valid, errors = preset.validate()
        assert is_valid
        assert len(errors) == 0
    
    def test_validate_invalid_sensitivity(self, dominant_params):
        dominant_params["sensitivity"] = 5  # Too low
        config = PresetConfig(
            id="TEST",
            name="Test",
            indicator_type="dominant",
            params=dominant_params
        )
        preset = DominantPreset(config)
        is_valid, errors = preset.validate()
        assert not is_valid
        assert any("sensitivity" in e for e in errors)
    
    def test_calculate_category(self, dominant_params):
        config = PresetConfig(
            id="TEST",
            name="Test",
            indicator_type="dominant",
            params=dominant_params
        )
        preset = DominantPreset(config)
        
        assert preset.calculate_category({"sensitivity": 12}) == "scalp"
        assert preset.calculate_category({"sensitivity": 21}) == "short-term"
        assert preset.calculate_category({"sensitivity": 35}) == "mid-term"
        assert preset.calculate_category({"sensitivity": 50}) == "swing"
        assert preset.calculate_category({"sensitivity": 60}) == "long-term"
    
    def test_generate_name(self, dominant_params):
        config = PresetConfig(
            id="TEST",
            name="Test",
            indicator_type="dominant",
            params=dominant_params
        )
        preset = DominantPreset(config)
        name = preset.generate_name(dominant_params)
        assert name == "DOM_21_F0_SL0"


# ==================== REGISTRY TESTS ====================

class TestPresetRegistry:
    """Tests for PresetRegistry"""
    
    def test_singleton(self):
        reg1 = get_registry()
        reg2 = get_registry()
        assert reg1 is reg2
    
    def test_registered_types(self):
        registry = get_registry()
        types = registry.get_registered_types()
        assert "trg" in types
        assert "dominant" in types
    
    def test_get_preset_class(self):
        registry = get_registry()
        
        trg_class = registry.get_preset_class("trg")
        assert trg_class == TRGPreset
        
        dom_class = registry.get_preset_class("dominant")
        assert dom_class == DominantPreset
        
        unknown = registry.get_preset_class("unknown")
        assert unknown is None


# ==================== VALIDATOR TESTS ====================

class TestPresetValidator:
    """Tests for PresetValidator"""
    
    def test_validate_params_valid(self, trg_params):
        result = validate_params("trg", trg_params)
        assert result.is_valid
        assert result.error_count == 0
    
    def test_validate_params_invalid(self):
        result = validate_params("trg", {"i1": 5})  # Invalid i1
        assert not result.is_valid
        assert result.error_count > 0
    
    def test_validate_import_valid(self, trg_params):
        data = {
            "name": "Import Test",
            "indicator_type": "trg",
            "params": trg_params
        }
        result = validate_import(data)
        assert result.is_valid
    
    def test_validate_import_missing_name(self):
        data = {
            "indicator_type": "trg",
            "params": {}
        }
        result = validate_import(data)
        assert not result.is_valid
        assert any("name" in e.field for e in result.get_errors())
    
    def test_validation_warnings(self, trg_params):
        trg_params["leverage"] = 100  # Very high leverage
        result = validate_params("trg", trg_params)
        # Should be valid but with warnings
        assert result.has_warnings


# ==================== GENERATOR TESTS ====================

class TestPresetGenerator:
    """Tests for PresetGenerator"""
    
    def test_trg_generator_count(self):
        generator = TRGSystemGenerator(save_to_db=False)
        assert generator.get_total_count() == 200
    
    def test_trg_generator_generate(self):
        generator = TRGSystemGenerator(save_to_db=False)
        presets = list(generator.generate_all())
        assert len(presets) == 200
    
    def test_dominant_generator_count(self):
        generator = DominantSystemGenerator(save_to_db=False)
        count = generator.get_total_count()
        assert count > 0  # At least some presets
    
    def test_generator_with_progress(self):
        progress_calls = []
        
        def progress_callback(current, total):
            progress_calls.append((current, total))
        
        generator = TRGSystemGenerator(save_to_db=False)
        generator.set_progress_callback(progress_callback)
        
        # Run without saving
        for _ in generator.generate_all():
            pass
        
        assert len(progress_calls) == 200


# ==================== INTEGRATION TESTS ====================

class TestPresetIntegration:
    """Integration tests"""
    
    def test_create_validate_export_import(self, trg_params):
        # Create preset
        preset = TRGPreset.create_from_params(
            params=trg_params,
            name="Integration Test"
        )
        
        # Validate
        is_valid, errors = preset.validate()
        assert is_valid
        
        # Export to JSON
        json_str = preset.to_json()
        data = json.loads(json_str)
        
        # Validate import data
        result = validate_import(data)
        assert result.is_valid
    
    def test_clone_preset(self, trg_config):
        original = TRGPreset(trg_config)
        clone = original.clone(new_name="Cloned Preset")
        
        assert clone.name == "Cloned Preset"
        assert clone.id != original.id
        assert clone.params == original.params
    
    def test_update_params(self, trg_config):
        preset = TRGPreset(trg_config)
        
        # Valid update
        success = preset.update_params({"i1": 60})
        assert success
        assert preset.params["i1"] == 60
        
        # Invalid update
        success = preset.update_params({"i1": 5})
        assert not success


# ==================== MAIN ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
