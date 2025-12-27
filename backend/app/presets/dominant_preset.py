"""
Komas Trading Server - Dominant Preset
======================================
Preset implementation for Dominant indicator.

Dominant Parameters:
- sensitivity: Channel sensitivity (12-60)
- tp1_percent - tp4_percent: Take profit levels
- sl_percent: Stop loss percent
- filter_type: 0-6 filter types
- sl_mode: 0-4 SL modes
- fixed_stop: Use fixed stop loss

125 System Presets (from GG Pine Script strategies)

Version: 1.0
Chat: #29 — Presets Architecture
"""

from typing import Dict, List, Any, Optional
from .base import (
    BasePreset, PresetConfig, PresetCategory, PresetSource,
    IndicatorType
)


class DominantPreset(BasePreset):
    """
    Dominant indicator preset.
    
    Features:
    - Channel + Fibonacci based signals
    - 4 take profit levels
    - 5 stop loss modes
    - 7 filter types
    """
    
    INDICATOR_TYPE = IndicatorType.DOMINANT.value
    DEFAULT_CATEGORY = PresetCategory.MID_TERM.value
    
    # Filter type descriptions
    FILTER_TYPES = {
        0: "None",
        1: "ATR Condition",
        2: "RSI Condition", 
        3: "ATR + RSI Combined",
        4: "Volatility",
        5: "Special 1",
        6: "Special 2",
    }
    
    # SL mode descriptions
    SL_MODES = {
        0: "No SL Movement",
        1: "After TP1",
        2: "After TP2",
        3: "After TP3",
        4: "Cascade",
    }
    
    def get_default_params(self) -> Dict[str, Any]:
        """Return default Dominant parameters"""
        return {
            # Core indicator
            "sensitivity": 21,
            
            # Take profits
            "tp1_percent": 1.0,
            "tp2_percent": 2.0,
            "tp3_percent": 3.0,
            "tp4_percent": 5.0,
            
            # Stop loss
            "sl_percent": 2.0,
            "sl_mode": 0,
            "fixed_stop": True,
            
            # Filter
            "filter_type": 0,
            
            # Trading
            "leverage": 10,
            "commission_enabled": True,
            "commission_percent": 0.04,
        }
    
    def validate_params(self, params: Dict[str, Any]) -> List[str]:
        """Validate Dominant parameters"""
        errors = []
        
        # Validate sensitivity
        sensitivity = params.get("sensitivity", 21)
        if not isinstance(sensitivity, (int, float)) or sensitivity < 10 or sensitivity > 100:
            errors.append(f"sensitivity must be between 10 and 100, got {sensitivity}")
        
        # Validate TP percents (must be increasing)
        prev_percent = 0
        for i in range(1, 5):
            key = f"tp{i}_percent"
            percent = params.get(key, i * 1.0)
            if not isinstance(percent, (int, float)) or percent <= 0 or percent > 100:
                errors.append(f"{key} must be between 0 and 100, got {percent}")
            elif percent <= prev_percent:
                errors.append(f"{key} ({percent}%) must be greater than previous TP ({prev_percent}%)")
            prev_percent = percent
        
        # Validate SL percent
        sl_percent = params.get("sl_percent", 2.0)
        if not isinstance(sl_percent, (int, float)) or sl_percent < 0.1 or sl_percent > 50:
            errors.append(f"sl_percent must be between 0.1 and 50, got {sl_percent}")
        
        # Validate SL mode
        sl_mode = params.get("sl_mode", 0)
        if not isinstance(sl_mode, int) or sl_mode < 0 or sl_mode > 4:
            errors.append(f"sl_mode must be between 0 and 4, got {sl_mode}")
        
        # Validate filter type
        filter_type = params.get("filter_type", 0)
        if not isinstance(filter_type, int) or filter_type < 0 or filter_type > 6:
            errors.append(f"filter_type must be between 0 and 6, got {filter_type}")
        
        # Validate fixed_stop
        fixed_stop = params.get("fixed_stop", True)
        if not isinstance(fixed_stop, bool):
            errors.append(f"fixed_stop must be boolean, got {type(fixed_stop)}")
        
        return errors
    
    def get_param_schema(self) -> Dict[str, Dict[str, Any]]:
        """Return parameter schema for UI generation"""
        return {
            # Core parameters
            "sensitivity": {
                "type": "float",
                "label": "Sensitivity",
                "default": 21,
                "min": 10,
                "max": 100,
                "step": 1,
                "group": "main"
            },
            
            # Take profits
            "tp1_percent": {
                "type": "float",
                "label": "TP1 %",
                "default": 1.0,
                "min": 0.1,
                "max": 50.0,
                "step": 0.1,
                "group": "tp"
            },
            "tp2_percent": {
                "type": "float",
                "label": "TP2 %",
                "default": 2.0,
                "min": 0.1,
                "max": 50.0,
                "step": 0.1,
                "group": "tp"
            },
            "tp3_percent": {
                "type": "float",
                "label": "TP3 %",
                "default": 3.0,
                "min": 0.1,
                "max": 50.0,
                "step": 0.1,
                "group": "tp"
            },
            "tp4_percent": {
                "type": "float",
                "label": "TP4 %",
                "default": 5.0,
                "min": 0.1,
                "max": 50.0,
                "step": 0.1,
                "group": "tp"
            },
            
            # Stop loss
            "sl_percent": {
                "type": "float",
                "label": "Stop Loss %",
                "default": 2.0,
                "min": 0.1,
                "max": 50.0,
                "step": 0.1,
                "group": "sl"
            },
            "sl_mode": {
                "type": "select",
                "label": "SL Mode",
                "default": 0,
                "options": [0, 1, 2, 3, 4],
                "labels": ["No Movement", "After TP1", "After TP2", "After TP3", "Cascade"],
                "group": "sl"
            },
            "fixed_stop": {
                "type": "bool",
                "label": "Fixed Stop",
                "default": True,
                "group": "sl"
            },
            
            # Filter
            "filter_type": {
                "type": "select",
                "label": "Filter Type",
                "default": 0,
                "options": [0, 1, 2, 3, 4, 5, 6],
                "labels": ["None", "ATR", "RSI", "ATR+RSI", "Volatility", "Special 1", "Special 2"],
                "group": "filters"
            },
        }
    
    def calculate_category(self, params: Dict[str, Any]) -> str:
        """
        Calculate category based on sensitivity.
        
        Higher sensitivity = slower signals = longer trades
        """
        sensitivity = params.get("sensitivity", 21)
        
        if sensitivity <= 15:
            return PresetCategory.SCALP.value
        elif sensitivity <= 25:
            return PresetCategory.SHORT_TERM.value
        elif sensitivity <= 40:
            return PresetCategory.MID_TERM.value
        elif sensitivity <= 55:
            return PresetCategory.SWING.value
        else:
            return PresetCategory.LONG_TERM.value
    
    def generate_name(self, params: Dict[str, Any]) -> str:
        """
        Generate preset name from parameters.
        
        Format: DOM_{sensitivity}_F{filter_type}_SL{sl_mode}
        Example: DOM_21_F0_SL0, DOM_35_F3_SL2
        """
        sensitivity = int(params.get("sensitivity", 21))
        filter_type = int(params.get("filter_type", 0))
        sl_mode = int(params.get("sl_mode", 0))
        
        return f"DOM_{sensitivity}_F{filter_type}_SL{sl_mode}"
    
    def get_filter_description(self) -> str:
        """Get human-readable filter description"""
        filter_type = self.params.get("filter_type", 0)
        return self.FILTER_TYPES.get(filter_type, "Unknown")
    
    def get_sl_mode_description(self) -> str:
        """Get human-readable SL mode description"""
        sl_mode = self.params.get("sl_mode", 0)
        return self.SL_MODES.get(sl_mode, "Unknown")
    
    @classmethod
    def create_from_pine_preset(
        cls,
        name: str,
        sensitivity: float,
        tp1: float,
        tp2: float,
        tp3: float,
        tp4: float,
        sl: float,
        filter_type: int = 0,
        sl_mode: int = 0,
        fixed_stop: bool = True,
        category: str = None,
        description: str = None,
    ) -> "DominantPreset":
        """
        Create preset from Pine Script parameters.
        Used for importing the 125 system presets from GG strategies.
        
        Args:
            name: Preset name
            sensitivity: Channel sensitivity
            tp1-tp4: Take profit percentages
            sl: Stop loss percentage
            filter_type: Filter type (0-6)
            sl_mode: SL mode (0-4)
            fixed_stop: Use fixed stop loss
            category: Optional category override
            description: Optional description
            
        Returns:
            DominantPreset instance
        """
        params = {
            "sensitivity": sensitivity,
            "tp1_percent": tp1,
            "tp2_percent": tp2,
            "tp3_percent": tp3,
            "tp4_percent": tp4,
            "sl_percent": sl,
            "filter_type": filter_type,
            "sl_mode": sl_mode,
            "fixed_stop": fixed_stop,
        }
        
        # Generate ID
        preset_id = f"DOM_SYS_{name.replace(' ', '_').replace('/', '_')[:30]}"
        
        # Calculate category if not provided
        if category is None:
            temp = cls(PresetConfig(
                id="temp", name="temp", indicator_type=cls.INDICATOR_TYPE, params=params
            ))
            category = temp.calculate_category(params)
        
        config = PresetConfig(
            id=preset_id,
            name=name,
            indicator_type=cls.INDICATOR_TYPE,
            category=category,
            source=PresetSource.PINE_SCRIPT.value,
            params=params,
            description=description or f"Dominant preset: sens={sensitivity}, filter={filter_type}, sl_mode={sl_mode}",
            tags=["system", "dominant", f"sens_{int(sensitivity)}", f"filter_{filter_type}"],
        )
        
        return cls(config)
    
    @classmethod
    def get_system_presets_data(cls) -> List[Dict[str, Any]]:
        """
        Get example data for system presets.
        The full 125 presets are loaded from seed_dominant_presets.py
        
        Returns:
            List of example preset dictionaries
        """
        # These are example presets - the full 125 presets
        # are in seed_dominant_presets.py from GG Pine Script
        return [
            # Scalp presets
            {"name": "Scalp Fast", "sensitivity": 12, "tp1": 0.5, "tp2": 1.0, "tp3": 1.5, "tp4": 2.5, "sl": 1.0, "filter_type": 0, "sl_mode": 0, "category": "scalp"},
            {"name": "Scalp Medium", "sensitivity": 15, "tp1": 0.7, "tp2": 1.2, "tp3": 1.8, "tp4": 3.0, "sl": 1.2, "filter_type": 1, "sl_mode": 1, "category": "scalp"},
            
            # Short-term presets
            {"name": "Short Aggressive", "sensitivity": 18, "tp1": 0.8, "tp2": 1.5, "tp3": 2.2, "tp4": 3.5, "sl": 1.5, "filter_type": 0, "sl_mode": 0, "category": "short-term"},
            {"name": "Short Balanced", "sensitivity": 21, "tp1": 1.0, "tp2": 2.0, "tp3": 3.0, "tp4": 5.0, "sl": 2.0, "filter_type": 2, "sl_mode": 1, "category": "short-term"},
            {"name": "Short Conservative", "sensitivity": 25, "tp1": 1.2, "tp2": 2.5, "tp3": 4.0, "tp4": 6.0, "sl": 2.5, "filter_type": 3, "sl_mode": 2, "category": "short-term"},
            
            # Mid-term presets
            {"name": "Mid Classic", "sensitivity": 30, "tp1": 1.5, "tp2": 3.0, "tp3": 5.0, "tp4": 8.0, "sl": 3.0, "filter_type": 0, "sl_mode": 1, "category": "mid-term"},
            {"name": "Mid Trend", "sensitivity": 35, "tp1": 2.0, "tp2": 4.0, "tp3": 6.0, "tp4": 10.0, "sl": 3.5, "filter_type": 1, "sl_mode": 2, "category": "mid-term"},
            {"name": "Mid Safe", "sensitivity": 40, "tp1": 2.5, "tp2": 5.0, "tp3": 7.5, "tp4": 12.0, "sl": 4.0, "filter_type": 3, "sl_mode": 2, "category": "mid-term"},
            
            # Swing presets
            {"name": "Swing Standard", "sensitivity": 45, "tp1": 3.0, "tp2": 6.0, "tp3": 9.0, "tp4": 15.0, "sl": 5.0, "filter_type": 0, "sl_mode": 2, "category": "swing"},
            {"name": "Swing Wide", "sensitivity": 50, "tp1": 4.0, "tp2": 8.0, "tp3": 12.0, "tp4": 20.0, "sl": 6.0, "filter_type": 1, "sl_mode": 3, "category": "swing"},
            
            # Long-term presets
            {"name": "Long Position", "sensitivity": 55, "tp1": 5.0, "tp2": 10.0, "tp3": 15.0, "tp4": 25.0, "sl": 8.0, "filter_type": 0, "sl_mode": 4, "category": "long-term"},
            {"name": "Long Trend", "sensitivity": 60, "tp1": 6.0, "tp2": 12.0, "tp3": 18.0, "tp4": 30.0, "sl": 10.0, "filter_type": 1, "sl_mode": 4, "category": "long-term"},
        ]
    
    @classmethod
    def generate_system_presets(cls) -> List["DominantPreset"]:
        """
        Generate all system presets from data.
        
        Returns:
            List of DominantPreset instances
        """
        presets = []
        
        for data in cls.get_system_presets_data():
            preset = cls.create_from_pine_preset(
                name=data["name"],
                sensitivity=data["sensitivity"],
                tp1=data["tp1"],
                tp2=data["tp2"],
                tp3=data["tp3"],
                tp4=data["tp4"],
                sl=data["sl"],
                filter_type=data.get("filter_type", 0),
                sl_mode=data.get("sl_mode", 0),
                fixed_stop=data.get("fixed_stop", True),
                category=data.get("category"),
            )
            presets.append(preset)
        
        return presets


# ==================== EXPORTS ====================

__all__ = ["DominantPreset"]
