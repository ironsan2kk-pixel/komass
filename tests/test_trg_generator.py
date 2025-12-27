"""
Komas Trading Server - TRG Preset Generator Tests
=================================================
Unit tests for TRG preset generation and validation.

Test coverage:
- Preset generation (200 presets)
- Naming convention
- Parameter validation
- TP/SL calculations
- Filter profiles
- Database operations

Chat: #30 — Presets TRG Generator
"""

import pytest
import sys
import os
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))
os.environ["PYTHONPATH"] = str(backend_path / "app")


class TestTRGPresetGeneration:
    """Test TRG preset generation"""
    
    def test_preset_count(self):
        """Test that 200 presets are generated (8 × 5 × 5)"""
        from app.presets import TRGPreset, FilterProfile
        
        total = len(TRGPreset.I1_VALUES) * len(TRGPreset.I2_VALUES) * len(list(FilterProfile))
        assert total == 200, f"Expected 200 presets, got {total}"
    
    def test_i1_values(self):
        """Test i1 values are correct"""
        from app.presets import TRGPreset
        
        expected = [14, 25, 40, 60, 80, 110, 150, 200]
        assert TRGPreset.I1_VALUES == expected
    
    def test_i2_values(self):
        """Test i2 values are correct"""
        from app.presets import TRGPreset
        
        expected = [2.0, 3.0, 4.0, 5.5, 7.5]
        assert TRGPreset.I2_VALUES == expected
    
    def test_filter_profiles(self):
        """Test filter profiles are correct"""
        from app.presets import FilterProfile
        
        profiles = list(FilterProfile)
        assert len(profiles) == 5
        
        codes = [p.value for p in profiles]
        assert set(codes) == {"N", "T", "M", "S", "F"}


class TestTRGPresetNaming:
    """Test TRG preset naming convention"""
    
    def test_naming_format(self):
        """Test preset ID format: TRG_SYS_{FILTER}_{i1}_{i2*10}"""
        from app.presets import TRGPreset, FilterProfile
        
        preset = TRGPreset.create_system_preset(45, 4.0, FilterProfile.NONE)
        
        assert preset.id == "TRG_SYS_N_45_40"
        assert preset.name == "N_45_40"
    
    def test_naming_examples(self):
        """Test naming convention examples from docs"""
        from app.presets import TRGPreset, FilterProfile
        
        test_cases = [
            (14, 2.0, FilterProfile.NONE, "N_14_20"),
            (40, 4.0, FilterProfile.TREND, "T_40_40"),
            (60, 5.5, FilterProfile.MOMENTUM, "M_60_55"),
            (110, 3.0, FilterProfile.STRENGTH, "S_110_30"),
            (200, 7.5, FilterProfile.FULL, "F_200_75"),
        ]
        
        for i1, i2, profile, expected_name in test_cases:
            preset = TRGPreset.create_system_preset(i1, i2, profile)
            assert preset.name == expected_name, f"Expected {expected_name}, got {preset.name}"


class TestTRGPresetValidation:
    """Test TRG preset validation"""
    
    def test_valid_preset(self):
        """Test that generated presets are valid"""
        from app.presets import TRGPreset, FilterProfile
        
        preset = TRGPreset.create_system_preset(45, 4.0, FilterProfile.NONE)
        is_valid, errors = preset.validate()
        
        assert is_valid, f"Preset should be valid but got errors: {errors}"
    
    def test_all_presets_valid(self):
        """Test that all 200 presets are valid"""
        from app.presets import TRGPreset, FilterProfile
        
        invalid_count = 0
        invalid_presets = []
        
        for i1 in TRGPreset.I1_VALUES:
            for i2 in TRGPreset.I2_VALUES:
                for profile in TRGPreset.FILTER_PROFILES:
                    preset = TRGPreset.create_system_preset(i1, i2, profile)
                    is_valid, errors = preset.validate()
                    
                    if not is_valid:
                        invalid_count += 1
                        invalid_presets.append((preset.name, errors))
        
        assert invalid_count == 0, f"{invalid_count} invalid presets: {invalid_presets[:5]}"


class TestTRGPresetParameters:
    """Test TRG preset parameter calculations"""
    
    def test_tp_count_by_i1(self):
        """Test TP count based on i1 value"""
        from app.presets import TRGPreset, FilterProfile
        
        # i1 <= 25 -> 4 TPs
        preset = TRGPreset.create_system_preset(14, 4.0, FilterProfile.NONE)
        assert preset.params["tp_count"] == 4
        
        preset = TRGPreset.create_system_preset(25, 4.0, FilterProfile.NONE)
        assert preset.params["tp_count"] == 4
        
        # i1 26-80 -> 5 TPs
        preset = TRGPreset.create_system_preset(40, 4.0, FilterProfile.NONE)
        assert preset.params["tp_count"] == 5
        
        preset = TRGPreset.create_system_preset(80, 4.0, FilterProfile.NONE)
        assert preset.params["tp_count"] == 5
        
        # i1 > 80 -> 6 TPs
        preset = TRGPreset.create_system_preset(110, 4.0, FilterProfile.NONE)
        assert preset.params["tp_count"] == 6
        
        preset = TRGPreset.create_system_preset(200, 4.0, FilterProfile.NONE)
        assert preset.params["tp_count"] == 6
    
    def test_sl_mode_by_i1(self):
        """Test SL mode based on i1 value"""
        from app.presets import TRGPreset, FilterProfile
        
        # i1 <= 25 -> fixed
        preset = TRGPreset.create_system_preset(14, 4.0, FilterProfile.NONE)
        assert preset.params["sl_mode"] == "fixed"
        
        # i1 26-110 -> breakeven
        preset = TRGPreset.create_system_preset(60, 4.0, FilterProfile.NONE)
        assert preset.params["sl_mode"] == "breakeven"
        
        # i1 > 110 -> cascade
        preset = TRGPreset.create_system_preset(150, 4.0, FilterProfile.NONE)
        assert preset.params["sl_mode"] == "cascade"
    
    def test_tp_amounts_sum_to_100(self):
        """Test that TP amounts sum to 100%"""
        from app.presets import TRGPreset, FilterProfile
        
        for i1 in TRGPreset.I1_VALUES:
            for i2 in TRGPreset.I2_VALUES:
                for profile in TRGPreset.FILTER_PROFILES:
                    preset = TRGPreset.create_system_preset(i1, i2, profile)
                    
                    tp_count = preset.params["tp_count"]
                    total = sum(
                        preset.params[f"tp{i}_amount"]
                        for i in range(1, tp_count + 1)
                    )
                    
                    assert total == 100, f"TP amounts should sum to 100, got {total} for {preset.name}"
    
    def test_tp_scaling_by_i2(self):
        """Test that TP levels are scaled by i2"""
        from app.presets import TRGPreset, FilterProfile
        
        # Base case: i2 = 4.0 (scale factor = 1.0)
        base_preset = TRGPreset.create_system_preset(60, 4.0, FilterProfile.NONE)
        base_tp1 = base_preset.params["tp1_percent"]
        
        # Higher i2 = higher TPs
        high_preset = TRGPreset.create_system_preset(60, 7.5, FilterProfile.NONE)
        high_tp1 = high_preset.params["tp1_percent"]
        
        assert high_tp1 > base_tp1, f"Higher i2 should give higher TP: {high_tp1} vs {base_tp1}"
        
        # Lower i2 = lower TPs
        low_preset = TRGPreset.create_system_preset(60, 2.0, FilterProfile.NONE)
        low_tp1 = low_preset.params["tp1_percent"]
        
        assert low_tp1 < base_tp1, f"Lower i2 should give lower TP: {low_tp1} vs {base_tp1}"


class TestTRGFilterProfiles:
    """Test TRG filter profile settings"""
    
    def test_none_profile(self):
        """Test N (None) profile has no filters"""
        from app.presets import TRGPreset, FilterProfile
        
        preset = TRGPreset.create_system_preset(60, 4.0, FilterProfile.NONE)
        
        assert not preset.params["supertrend_enabled"]
        assert not preset.params["rsi_enabled"]
        assert not preset.params["adx_enabled"]
        assert not preset.params["volume_enabled"]
    
    def test_trend_profile(self):
        """Test T (Trend) profile has only SuperTrend"""
        from app.presets import TRGPreset, FilterProfile
        
        preset = TRGPreset.create_system_preset(60, 4.0, FilterProfile.TREND)
        
        assert preset.params["supertrend_enabled"]
        assert not preset.params["rsi_enabled"]
        assert not preset.params["adx_enabled"]
        assert not preset.params["volume_enabled"]
    
    def test_momentum_profile(self):
        """Test M (Momentum) profile has only RSI"""
        from app.presets import TRGPreset, FilterProfile
        
        preset = TRGPreset.create_system_preset(60, 4.0, FilterProfile.MOMENTUM)
        
        assert not preset.params["supertrend_enabled"]
        assert preset.params["rsi_enabled"]
        assert not preset.params["adx_enabled"]
        assert not preset.params["volume_enabled"]
    
    def test_strength_profile(self):
        """Test S (Strength) profile has only ADX"""
        from app.presets import TRGPreset, FilterProfile
        
        preset = TRGPreset.create_system_preset(60, 4.0, FilterProfile.STRENGTH)
        
        assert not preset.params["supertrend_enabled"]
        assert not preset.params["rsi_enabled"]
        assert preset.params["adx_enabled"]
        assert not preset.params["volume_enabled"]
    
    def test_full_profile(self):
        """Test F (Full) profile has all filters"""
        from app.presets import TRGPreset, FilterProfile
        
        preset = TRGPreset.create_system_preset(60, 4.0, FilterProfile.FULL)
        
        assert preset.params["supertrend_enabled"]
        assert preset.params["rsi_enabled"]
        assert preset.params["adx_enabled"]
        assert preset.params["volume_enabled"]


class TestTRGPresetCategory:
    """Test TRG preset category assignment"""
    
    def test_category_by_i1(self):
        """Test category assignment based on i1"""
        from app.presets import TRGPreset, FilterProfile
        
        test_cases = [
            (14, "scalp"),       # <= 20
            (25, "short-term"),  # 21-40
            (40, "short-term"),
            (60, "mid-term"),    # 41-80
            (80, "mid-term"),
            (110, "swing"),      # 81-130
            (150, "long-term"),  # > 130
            (200, "long-term"),
        ]
        
        for i1, expected_category in test_cases:
            preset = TRGPreset.create_system_preset(i1, 4.0, FilterProfile.NONE)
            assert preset.config.category == expected_category, \
                f"i1={i1} should have category {expected_category}, got {preset.config.category}"


class TestTRGPresetDatabase:
    """Test TRG preset database operations"""
    
    def test_preset_serialization(self):
        """Test that preset can be serialized to dict"""
        from app.presets import TRGPreset, FilterProfile
        
        preset = TRGPreset.create_system_preset(60, 4.0, FilterProfile.NONE)
        data = preset.to_dict()
        
        assert "id" in data
        assert "name" in data
        assert "params" in data
        assert "category" in data
        assert data["id"] == "TRG_SYS_N_60_40"
    
    def test_preset_export_json(self):
        """Test that preset can be exported to JSON"""
        import json
        from app.presets import TRGPreset, FilterProfile
        
        preset = TRGPreset.create_system_preset(60, 4.0, FilterProfile.NONE)
        json_str = preset.config.to_json()
        
        # Should be valid JSON
        data = json.loads(json_str)
        assert data["id"] == "TRG_SYS_N_60_40"


class TestTRGPresetGrid:
    """Test TRG preset grid information"""
    
    def test_grid_dimensions(self):
        """Test grid dimensions are correct"""
        from app.presets import TRGPreset, FilterProfile
        
        assert len(TRGPreset.I1_VALUES) == 8
        assert len(TRGPreset.I2_VALUES) == 5
        assert len(list(FilterProfile)) == 5
    
    def test_unique_preset_ids(self):
        """Test all preset IDs are unique"""
        from app.presets import TRGPreset, FilterProfile
        
        preset_ids = set()
        
        for i1 in TRGPreset.I1_VALUES:
            for i2 in TRGPreset.I2_VALUES:
                for profile in TRGPreset.FILTER_PROFILES:
                    preset = TRGPreset.create_system_preset(i1, i2, profile)
                    
                    assert preset.id not in preset_ids, f"Duplicate ID: {preset.id}"
                    preset_ids.add(preset.id)
        
        assert len(preset_ids) == 200


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
