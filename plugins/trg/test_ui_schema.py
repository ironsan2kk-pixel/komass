# -*- coding: utf-8 -*-
"""
Tests for TRG UI Schema
=======================
Comprehensive test suite for ui_schema.py

Run with: pytest test_ui_schema.py -v
"""

import pytest
import json
from ui_schema import (
    # Enums
    FieldType, SectionType, TabType,
    # Classes
    FieldOption, UIField, UISection, UITab, TRGUISchema,
    # Functions
    get_ui_schema, get_schema_dict, get_defaults, validate_settings
)


# =============================================================================
# ENUM TESTS
# =============================================================================

class TestEnums:
    """Test enum definitions"""
    
    def test_field_type_values(self):
        """Verify all field types"""
        assert FieldType.NUMBER.value == "number"
        assert FieldType.SLIDER.value == "slider"
        assert FieldType.SELECT.value == "select"
        assert FieldType.CHECKBOX.value == "checkbox"
        assert FieldType.TOGGLE.value == "toggle"
        assert FieldType.BUTTON_GROUP.value == "button_group"
        assert FieldType.TEXT.value == "text"
        assert FieldType.COLOR.value == "color"
        assert FieldType.RANGE.value == "range"
        assert FieldType.DYNAMIC_LIST.value == "dynamic_list"
    
    def test_section_type_values(self):
        """Verify section types"""
        assert SectionType.STATIC.value == "static"
        assert SectionType.COLLAPSIBLE.value == "collapsible"
        assert SectionType.DYNAMIC.value == "dynamic"
    
    def test_tab_type_values(self):
        """Verify tab types"""
        assert TabType.CHART.value == "chart"
        assert TabType.STATS.value == "stats"
        assert TabType.TABLE.value == "table"
        assert TabType.PANEL.value == "panel"
        assert TabType.CUSTOM.value == "custom"


# =============================================================================
# DATA CLASS TESTS
# =============================================================================

class TestFieldOption:
    """Test FieldOption dataclass"""
    
    def test_basic_option(self):
        """Test basic option creation"""
        opt = FieldOption(value="test", label="Test Label")
        assert opt.value == "test"
        assert opt.label == "Test Label"
        assert opt.icon == ""
        assert opt.color == ""
    
    def test_option_with_icon(self):
        """Test option with icon"""
        opt = FieldOption(value=1, label="One", icon="📊")
        assert opt.icon == "📊"
    
    def test_to_dict(self):
        """Test dictionary conversion"""
        opt = FieldOption(value="val", label="Label", icon="🔥", color="#ff0000")
        d = opt.to_dict()
        assert d["value"] == "val"
        assert d["label"] == "Label"
        assert d["icon"] == "🔥"
        assert d["color"] == "#ff0000"
    
    def test_to_dict_excludes_empty(self):
        """Test that empty values are excluded"""
        opt = FieldOption(value="x", label="X")
        d = opt.to_dict()
        assert "icon" not in d
        assert "color" not in d


class TestUIField:
    """Test UIField dataclass"""
    
    def test_basic_field(self):
        """Test basic field creation"""
        field = UIField(
            id="test_field",
            type=FieldType.NUMBER,
            label="Test Field",
            default=10
        )
        assert field.id == "test_field"
        assert field.type == FieldType.NUMBER
        assert field.label == "Test Field"
        assert field.default == 10
    
    def test_number_field_with_constraints(self):
        """Test number field with min/max/step"""
        field = UIField(
            id="num",
            type=FieldType.NUMBER,
            label="Number",
            default=50,
            min=0,
            max=100,
            step=5
        )
        assert field.min == 0
        assert field.max == 100
        assert field.step == 5
    
    def test_select_field(self):
        """Test select field with options"""
        field = UIField(
            id="sel",
            type=FieldType.SELECT,
            label="Select",
            options=[
                FieldOption(value="a", label="Option A"),
                FieldOption(value="b", label="Option B"),
            ]
        )
        assert len(field.options) == 2
    
    def test_to_dict_minimal(self):
        """Test minimal dict conversion"""
        field = UIField(id="x", type=FieldType.TEXT, label="X")
        d = field.to_dict()
        assert d["id"] == "x"
        assert d["type"] == "text"
        assert d["label"] == "X"
        # Optional fields should not be present
        assert "min" not in d
        assert "max" not in d
    
    def test_to_dict_full(self):
        """Test full dict conversion"""
        field = UIField(
            id="full",
            type=FieldType.NUMBER,
            label="Full Field",
            default=100,
            min=0,
            max=200,
            step=10,
            suffix="%",
            description="A full field",
            depends_on="other_field",
            depends_value=True,
            required=True,
            width="half"
        )
        d = field.to_dict()
        assert d["id"] == "full"
        assert d["default"] == 100
        assert d["min"] == 0
        assert d["max"] == 200
        assert d["step"] == 10
        assert d["suffix"] == "%"
        assert d["description"] == "A full field"
        assert d["depends_on"] == "other_field"
        assert d["depends_value"] == True
        assert d["required"] == True
        assert d["width"] == "half"


class TestUISection:
    """Test UISection dataclass"""
    
    def test_basic_section(self):
        """Test basic section creation"""
        section = UISection(
            id="test",
            title="Test Section",
            icon="📊",
            fields=[]
        )
        assert section.id == "test"
        assert section.title == "Test Section"
        assert section.icon == "📊"
        assert section.type == SectionType.COLLAPSIBLE
        assert section.default_open == True
    
    def test_section_with_fields(self):
        """Test section with fields"""
        section = UISection(
            id="s1",
            title="Section 1",
            icon="🔧",
            fields=[
                UIField(id="f1", type=FieldType.NUMBER, label="Field 1"),
                UIField(id="f2", type=FieldType.CHECKBOX, label="Field 2"),
            ]
        )
        assert len(section.fields) == 2
    
    def test_to_dict(self):
        """Test section dict conversion"""
        section = UISection(
            id="sec",
            title="Section",
            icon="⚙️",
            type=SectionType.STATIC,
            default_open=False,
            order=5,
            fields=[
                UIField(id="f", type=FieldType.TEXT, label="F")
            ]
        )
        d = section.to_dict()
        assert d["id"] == "sec"
        assert d["title"] == "Section"
        assert d["icon"] == "⚙️"
        assert d["type"] == "static"
        assert d["default_open"] == False
        assert d["order"] == 5
        assert len(d["fields"]) == 1


class TestUITab:
    """Test UITab dataclass"""
    
    def test_basic_tab(self):
        """Test basic tab creation"""
        tab = UITab(id="chart", label="Chart", icon="📈")
        assert tab.id == "chart"
        assert tab.label == "Chart"
        assert tab.icon == "📈"
        assert tab.type == TabType.CUSTOM
    
    def test_tab_with_component(self):
        """Test tab with component"""
        tab = UITab(
            id="stats",
            label="Stats",
            icon="📊",
            type=TabType.STATS,
            component="StatsPanel",
            default=True
        )
        assert tab.component == "StatsPanel"
        assert tab.default == True
    
    def test_to_dict(self):
        """Test tab dict conversion"""
        tab = UITab(
            id="t1",
            label="Tab 1",
            icon="🔥",
            type=TabType.PANEL,
            order=3,
            component="MyComponent"
        )
        d = tab.to_dict()
        assert d["id"] == "t1"
        assert d["label"] == "Tab 1"
        assert d["icon"] == "🔥"
        assert d["type"] == "panel"
        assert d["order"] == 3
        assert d["component"] == "MyComponent"


# =============================================================================
# TRG UI SCHEMA TESTS
# =============================================================================

class TestTRGUISchema:
    """Test TRGUISchema class"""
    
    @pytest.fixture
    def schema(self):
        """Create schema instance"""
        return TRGUISchema()
    
    def test_version(self, schema):
        """Test version constants"""
        assert schema.VERSION == "1.0.0"
        assert schema.PLUGIN_VERSION == "1.4.0"
    
    def test_sections_exist(self, schema):
        """Test all expected sections exist"""
        section_ids = [s.id for s in schema._sections]
        expected = [
            "data", "indicator", "take_profit", "stop_loss",
            "leverage", "filters", "reentry", "adaptive", "capital"
        ]
        for s in expected:
            assert s in section_ids, f"Missing section: {s}"
    
    def test_section_count(self, schema):
        """Test section count"""
        assert len(schema._sections) == 9
    
    def test_tabs_exist(self, schema):
        """Test all expected tabs exist"""
        tab_ids = [t.id for t in schema._tabs]
        expected = ["chart", "stats", "trades", "monthly", "optimizer", "heatmap"]
        for t in expected:
            assert t in tab_ids, f"Missing tab: {t}"
    
    def test_tab_count(self, schema):
        """Test tab count"""
        assert len(schema._tabs) == 6
    
    def test_defaults_populated(self, schema):
        """Test defaults are populated"""
        defaults = schema.get_defaults()
        assert "trg_atr_length" in defaults
        assert "trg_multiplier" in defaults
        assert "tp_count" in defaults
        assert "sl_percent" in defaults
    
    def test_default_values(self, schema):
        """Test specific default values"""
        defaults = schema.get_defaults()
        assert defaults["trg_atr_length"] == 45
        assert defaults["trg_multiplier"] == 4.0
        assert defaults["tp_count"] == 4
        assert defaults["sl_percent"] == 8.0
        assert defaults["leverage"] == 1
    
    def test_get_schema(self, schema):
        """Test get_schema returns complete structure"""
        full = schema.get_schema()
        assert "version" in full
        assert "plugin_version" in full
        assert "sidebar" in full
        assert "tabs" in full
        assert "defaults" in full
        assert "validation" in full
    
    def test_get_sidebar_schema(self, schema):
        """Test sidebar schema"""
        sidebar = schema.get_sidebar_schema()
        assert "sections" in sidebar
        assert len(sidebar["sections"]) == 9
    
    def test_get_tabs_schema(self, schema):
        """Test tabs schema"""
        tabs = schema.get_tabs_schema()
        assert len(tabs) == 6
        assert all("id" in t for t in tabs)
    
    def test_get_section(self, schema):
        """Test getting specific section"""
        section = schema.get_section("indicator")
        assert section is not None
        assert section["id"] == "indicator"
        assert section["title"] == "TRG Indicator"
    
    def test_get_section_not_found(self, schema):
        """Test getting non-existent section"""
        section = schema.get_section("nonexistent")
        assert section is None
    
    def test_get_field(self, schema):
        """Test getting specific field"""
        field = schema.get_field("trg_atr_length")
        assert field is not None
        assert field["id"] == "trg_atr_length"
        assert field["type"] == "number"
    
    def test_get_field_not_found(self, schema):
        """Test getting non-existent field"""
        field = schema.get_field("nonexistent")
        assert field is None
    
    def test_to_json(self, schema):
        """Test JSON export"""
        json_str = schema.to_json()
        parsed = json.loads(json_str)
        assert "version" in parsed
        assert "sidebar" in parsed


class TestTRGUISchemaValidation:
    """Test validation functionality"""
    
    @pytest.fixture
    def schema(self):
        return TRGUISchema()
    
    def test_valid_settings(self, schema):
        """Test validation of valid settings"""
        settings = {
            "trg_atr_length": 45,
            "trg_multiplier": 4.0,
            "tp_count": 4,
            "sl_percent": 8.0,
            "leverage": 10,
            "use_commission": False,
        }
        is_valid, errors = schema.validate_settings(settings)
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_number_below_min(self, schema):
        """Test validation fails for number below min"""
        settings = {"trg_atr_length": 5}  # min is 10
        is_valid, errors = schema.validate_settings(settings)
        assert not is_valid
        assert any("below minimum" in e for e in errors)
    
    def test_invalid_number_above_max(self, schema):
        """Test validation fails for number above max"""
        settings = {"trg_atr_length": 500}  # max is 200
        is_valid, errors = schema.validate_settings(settings)
        assert not is_valid
        assert any("above maximum" in e for e in errors)
    
    def test_invalid_type(self, schema):
        """Test validation fails for wrong type"""
        settings = {"trg_atr_length": "not a number"}
        is_valid, errors = schema.validate_settings(settings)
        assert not is_valid
        assert any("Expected number" in e for e in errors)
    
    def test_empty_settings(self, schema):
        """Test validation with empty settings"""
        is_valid, errors = schema.validate_settings({})
        # Empty should be valid (no required fields by default)
        assert is_valid


class TestTRGUISchemaPresets:
    """Test preset functionality"""
    
    @pytest.fixture
    def schema(self):
        return TRGUISchema()
    
    def test_filter_presets_exist(self, schema):
        """Test filter presets exist"""
        presets = schema.get_filter_presets()
        assert len(presets) >= 5
    
    def test_filter_preset_structure(self, schema):
        """Test filter preset structure"""
        presets = schema.get_filter_presets()
        for preset in presets:
            assert "name" in preset
            assert "use_supertrend" in preset
            assert "use_rsi_filter" in preset
            assert "use_adx_filter" in preset
            assert "use_volume_filter" in preset
    
    def test_tp_presets_exist(self, schema):
        """Test TP presets exist"""
        presets = schema.get_tp_presets()
        assert len(presets) >= 5
    
    def test_tp_preset_structure(self, schema):
        """Test TP preset structure"""
        presets = schema.get_tp_presets()
        for preset in presets:
            assert "name" in preset
            assert "tp_count" in preset
            assert "tp1_percent" in preset
    
    def test_optimization_ranges_exist(self, schema):
        """Test optimization ranges exist"""
        ranges = schema.get_optimization_ranges()
        assert "trg_atr_length" in ranges
        assert "trg_multiplier" in ranges
        assert "sl_percent" in ranges


# =============================================================================
# SINGLETON TESTS
# =============================================================================

class TestSingleton:
    """Test singleton pattern"""
    
    def test_get_ui_schema_returns_same_instance(self):
        """Test singleton returns same instance"""
        s1 = get_ui_schema()
        s2 = get_ui_schema()
        assert s1 is s2
    
    def test_get_schema_dict(self):
        """Test convenience function"""
        schema = get_schema_dict()
        assert isinstance(schema, dict)
        assert "version" in schema
    
    def test_get_defaults_function(self):
        """Test convenience function"""
        defaults = get_defaults()
        assert isinstance(defaults, dict)
        assert "trg_atr_length" in defaults
    
    def test_validate_settings_function(self):
        """Test convenience function"""
        is_valid, errors = validate_settings({"trg_atr_length": 45})
        assert isinstance(is_valid, bool)
        assert isinstance(errors, list)


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests"""
    
    def test_full_schema_json_roundtrip(self):
        """Test JSON roundtrip"""
        schema = get_ui_schema()
        json_str = schema.to_json()
        parsed = json.loads(json_str)
        
        # Re-serialize
        json_str2 = json.dumps(parsed, indent=2, ensure_ascii=False)
        parsed2 = json.loads(json_str2)
        
        assert parsed == parsed2
    
    def test_all_defaults_are_valid(self):
        """Test all default values pass validation"""
        schema = get_ui_schema()
        defaults = schema.get_defaults()
        is_valid, errors = schema.validate_settings(defaults)
        assert is_valid, f"Default settings invalid: {errors}"
    
    def test_tp_fields_have_correct_depends(self):
        """Test TP fields have correct dependencies"""
        schema = get_ui_schema()
        section = schema.get_section("take_profit")
        
        for field in section["fields"]:
            if field["id"].startswith("tp") and field["id"] != "tp_count":
                # TP percent and amount fields should depend on tp_count
                assert "depends_on" in field, f"Field {field['id']} missing depends_on"
                assert field["depends_on"] == "tp_count"
    
    def test_filter_fields_have_correct_depends(self):
        """Test filter fields have correct dependencies"""
        schema = get_ui_schema()
        section = schema.get_section("filters")
        
        filter_params = [
            ("supertrend_period", "use_supertrend"),
            ("rsi_period", "use_rsi_filter"),
            ("adx_period", "use_adx_filter"),
            ("volume_ma_period", "use_volume_filter"),
        ]
        
        for field_id, depends_on in filter_params:
            field = None
            for f in section["fields"]:
                if f["id"] == field_id:
                    field = f
                    break
            assert field is not None, f"Missing field: {field_id}"
            assert field.get("depends_on") == depends_on
    
    def test_indicator_section_fields(self):
        """Test indicator section has correct fields"""
        schema = get_ui_schema()
        section = schema.get_section("indicator")
        
        field_ids = [f["id"] for f in section["fields"]]
        assert "trg_atr_length" in field_ids
        assert "trg_multiplier" in field_ids
    
    def test_all_tabs_have_components(self):
        """Test all tabs have component defined"""
        schema = get_ui_schema()
        tabs = schema.get_tabs_schema()
        
        for tab in tabs:
            assert "component" in tab, f"Tab {tab['id']} missing component"
            assert tab["component"], f"Tab {tab['id']} has empty component"


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
