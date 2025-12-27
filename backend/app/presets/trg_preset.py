"""
Komas Trading Server - TRG Preset
=================================
Preset implementation for TRG (Trend Range Grid) indicator.

TRG Parameters:
- i1: ATR Length (10-200)
- i2: Multiplier (1.0-10.0)
- tp_count: Number of take profits (1-10)
- tp1_percent - tp10_percent: TP levels
- tp1_amount - tp10_amount: TP amounts
- sl_percent: Stop loss percent
- sl_mode: fixed, breakeven, cascade
- Filters: SuperTrend, RSI, ADX, Volume

200 System Presets:
- 8 i1 values × 5 i2 values × 5 filter profiles = 200

Version: 1.0
Chat: #29 — Presets Architecture
"""

from typing import Dict, List, Any, Optional
from .base import (
    BasePreset, PresetConfig, PresetCategory, PresetSource,
    FilterProfile, IndicatorType
)


class TRGPreset(BasePreset):
    """
    TRG (Trend Range Grid) indicator preset.
    
    Features:
    - ATR-based trend detection
    - Up to 10 take profit levels
    - 3 stop loss modes
    - 4 optional filters
    """
    
    INDICATOR_TYPE = IndicatorType.TRG.value
    DEFAULT_CATEGORY = PresetCategory.MID_TERM.value
    
    # System preset generation axes
    I1_VALUES = [14, 25, 40, 60, 80, 110, 150, 200]
    I2_VALUES = [2.0, 3.0, 4.0, 5.5, 7.5]
    FILTER_PROFILES = list(FilterProfile)
    
    # Default TP levels
    DEFAULT_TP_PERCENTS = [1.05, 1.95, 3.75, 6.0, 9.0, 13.0, 18.0, 25.0, 35.0, 50.0]
    DEFAULT_TP_AMOUNTS = [50, 30, 15, 5, 0, 0, 0, 0, 0, 0]
    
    def get_default_params(self) -> Dict[str, Any]:
        """Return default TRG parameters"""
        return {
            # Core indicator
            "i1": 45,
            "i2": 4.0,
            
            # Take profits
            "tp_count": 4,
            "tp1_percent": 1.05,
            "tp2_percent": 1.95,
            "tp3_percent": 3.75,
            "tp4_percent": 6.0,
            "tp5_percent": 9.0,
            "tp6_percent": 13.0,
            "tp7_percent": 18.0,
            "tp8_percent": 25.0,
            "tp9_percent": 35.0,
            "tp10_percent": 50.0,
            "tp1_amount": 50,
            "tp2_amount": 30,
            "tp3_amount": 15,
            "tp4_amount": 5,
            "tp5_amount": 0,
            "tp6_amount": 0,
            "tp7_amount": 0,
            "tp8_amount": 0,
            "tp9_amount": 0,
            "tp10_amount": 0,
            
            # Stop loss
            "sl_percent": 2.0,
            "sl_mode": "fixed",
            
            # Filters
            "supertrend_enabled": False,
            "supertrend_period": 10,
            "supertrend_multiplier": 3.0,
            "rsi_enabled": False,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "adx_enabled": False,
            "adx_period": 14,
            "adx_threshold": 25,
            "volume_enabled": False,
            "volume_multiplier": 1.5,
            
            # Re-entry
            "re_entry_enabled": False,
            "re_entry_mode": "after_tp",  # after_tp, after_sl, both
            "re_entry_cooldown": 1,
            "re_entry_max_count": 5,
            
            # Trading
            "leverage": 10,
            "commission_enabled": True,
            "commission_percent": 0.04,
        }
    
    def validate_params(self, params: Dict[str, Any]) -> List[str]:
        """Validate TRG parameters"""
        errors = []
        
        # Validate i1 (ATR Length)
        i1 = params.get("i1", 45)
        if not isinstance(i1, (int, float)) or i1 < 10 or i1 > 200:
            errors.append(f"i1 (ATR Length) must be between 10 and 200, got {i1}")
        
        # Validate i2 (Multiplier)
        i2 = params.get("i2", 4.0)
        if not isinstance(i2, (int, float)) or i2 < 1.0 or i2 > 10.0:
            errors.append(f"i2 (Multiplier) must be between 1.0 and 10.0, got {i2}")
        
        # Validate TP count
        tp_count = params.get("tp_count", 4)
        if not isinstance(tp_count, int) or tp_count < 1 or tp_count > 10:
            errors.append(f"tp_count must be between 1 and 10, got {tp_count}")
        
        # Validate TP percents (must be increasing)
        prev_percent = 0
        for i in range(1, tp_count + 1):
            key = f"tp{i}_percent"
            percent = params.get(key, self.DEFAULT_TP_PERCENTS[i-1])
            if not isinstance(percent, (int, float)) or percent <= 0 or percent > 100:
                errors.append(f"{key} must be between 0 and 100, got {percent}")
            elif percent <= prev_percent:
                errors.append(f"{key} ({percent}%) must be greater than previous TP ({prev_percent}%)")
            prev_percent = percent
        
        # Validate TP amounts (must sum to 100 for active TPs)
        total_amount = 0
        for i in range(1, tp_count + 1):
            key = f"tp{i}_amount"
            amount = params.get(key, self.DEFAULT_TP_AMOUNTS[i-1])
            if not isinstance(amount, (int, float)) or amount < 0 or amount > 100:
                errors.append(f"{key} must be between 0 and 100, got {amount}")
            total_amount += amount
        
        if abs(total_amount - 100) > 0.01:
            errors.append(f"TP amounts must sum to 100%, got {total_amount}%")
        
        # Validate SL percent
        sl_percent = params.get("sl_percent", 2.0)
        if not isinstance(sl_percent, (int, float)) or sl_percent < 0.5 or sl_percent > 50:
            errors.append(f"sl_percent must be between 0.5 and 50, got {sl_percent}")
        
        # Validate SL mode
        sl_mode = params.get("sl_mode", "fixed")
        if sl_mode not in ["fixed", "breakeven", "cascade"]:
            errors.append(f"sl_mode must be one of: fixed, breakeven, cascade. Got {sl_mode}")
        
        # Validate filter parameters
        if params.get("supertrend_enabled"):
            st_period = params.get("supertrend_period", 10)
            if not isinstance(st_period, int) or st_period < 1 or st_period > 100:
                errors.append(f"supertrend_period must be between 1 and 100")
            
            st_mult = params.get("supertrend_multiplier", 3.0)
            if not isinstance(st_mult, (int, float)) or st_mult < 0.5 or st_mult > 10:
                errors.append(f"supertrend_multiplier must be between 0.5 and 10")
        
        if params.get("rsi_enabled"):
            rsi_period = params.get("rsi_period", 14)
            if not isinstance(rsi_period, int) or rsi_period < 2 or rsi_period > 100:
                errors.append(f"rsi_period must be between 2 and 100")
            
            ob = params.get("rsi_overbought", 70)
            os = params.get("rsi_oversold", 30)
            if ob <= os:
                errors.append(f"rsi_overbought ({ob}) must be greater than rsi_oversold ({os})")
        
        if params.get("adx_enabled"):
            adx_period = params.get("adx_period", 14)
            if not isinstance(adx_period, int) or adx_period < 2 or adx_period > 100:
                errors.append(f"adx_period must be between 2 and 100")
            
            adx_thresh = params.get("adx_threshold", 25)
            if not isinstance(adx_thresh, (int, float)) or adx_thresh < 0 or adx_thresh > 100:
                errors.append(f"adx_threshold must be between 0 and 100")
        
        return errors
    
    def get_param_schema(self) -> Dict[str, Dict[str, Any]]:
        """Return parameter schema for UI generation"""
        return {
            # Core parameters
            "i1": {
                "type": "int",
                "label": "ATR Length (i1)",
                "default": 45,
                "min": 10,
                "max": 200,
                "step": 1,
                "group": "main"
            },
            "i2": {
                "type": "float",
                "label": "Multiplier (i2)",
                "default": 4.0,
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "group": "main"
            },
            
            # Take profits
            "tp_count": {
                "type": "int",
                "label": "TP Count",
                "default": 4,
                "min": 1,
                "max": 10,
                "step": 1,
                "group": "tp"
            },
            
            # Stop loss
            "sl_percent": {
                "type": "float",
                "label": "Stop Loss %",
                "default": 2.0,
                "min": 0.5,
                "max": 50.0,
                "step": 0.1,
                "group": "sl"
            },
            "sl_mode": {
                "type": "select",
                "label": "SL Mode",
                "default": "fixed",
                "options": ["fixed", "breakeven", "cascade"],
                "group": "sl"
            },
            
            # Filters
            "supertrend_enabled": {
                "type": "bool",
                "label": "SuperTrend Filter",
                "default": False,
                "group": "filters"
            },
            "rsi_enabled": {
                "type": "bool",
                "label": "RSI Filter",
                "default": False,
                "group": "filters"
            },
            "adx_enabled": {
                "type": "bool",
                "label": "ADX Filter",
                "default": False,
                "group": "filters"
            },
            "volume_enabled": {
                "type": "bool",
                "label": "Volume Filter",
                "default": False,
                "group": "filters"
            },
        }
    
    def calculate_category(self, params: Dict[str, Any]) -> str:
        """
        Calculate category based on i1 (ATR Length).
        
        Longer ATR = slower signals = longer trades
        """
        i1 = params.get("i1", 45)
        
        if i1 <= 20:
            return PresetCategory.SCALP.value
        elif i1 <= 40:
            return PresetCategory.SHORT_TERM.value
        elif i1 <= 80:
            return PresetCategory.MID_TERM.value
        elif i1 <= 130:
            return PresetCategory.SWING.value
        else:
            return PresetCategory.LONG_TERM.value
    
    def generate_name(self, params: Dict[str, Any]) -> str:
        """
        Generate preset name using naming convention:
        {FILTER}_{i1}_{i2*10}
        
        Examples: N_45_40, T_60_55, F_80_30
        """
        i1 = int(params.get("i1", 45))
        i2 = float(params.get("i2", 4.0))
        
        # Determine filter profile
        filter_code = self._get_filter_profile(params)
        
        # Generate name
        return f"{filter_code}_{i1}_{int(i2 * 10)}"
    
    def _get_filter_profile(self, params: Dict[str, Any]) -> str:
        """Determine filter profile code from params"""
        st = params.get("supertrend_enabled", False)
        rsi = params.get("rsi_enabled", False)
        adx = params.get("adx_enabled", False)
        vol = params.get("volume_enabled", False)
        
        if st and rsi and adx and vol:
            return FilterProfile.FULL.value
        elif adx and not (st or rsi or vol):
            return FilterProfile.STRENGTH.value
        elif rsi and not (st or adx or vol):
            return FilterProfile.MOMENTUM.value
        elif st and not (rsi or adx or vol):
            return FilterProfile.TREND.value
        else:
            return FilterProfile.NONE.value
    
    def get_filter_profile(self) -> FilterProfile:
        """Get current filter profile"""
        code = self._get_filter_profile(self.params)
        return FilterProfile(code)
    
    @classmethod
    def create_system_preset(
        cls,
        i1: int,
        i2: float,
        filter_profile: FilterProfile,
    ) -> "TRGPreset":
        """
        Create a system preset for the 200 preset grid.
        
        Args:
            i1: ATR Length value
            i2: Multiplier value  
            filter_profile: Filter profile (N/T/M/S/F)
            
        Returns:
            TRGPreset instance
        """
        # Build params
        params = {
            "i1": i1,
            "i2": i2,
        }
        
        # Calculate TP levels based on i1 and i2
        tp_count = cls._calculate_tp_count(i1)
        params["tp_count"] = tp_count
        
        # Scale TPs by i2
        base_scale = i2 / 4.0
        for i in range(1, 11):
            if i <= tp_count:
                base_percent = cls.DEFAULT_TP_PERCENTS[i-1]
                params[f"tp{i}_percent"] = round(base_percent * base_scale, 2)
                params[f"tp{i}_amount"] = cls._calculate_tp_amount(i, tp_count)
            else:
                params[f"tp{i}_percent"] = cls.DEFAULT_TP_PERCENTS[i-1]
                params[f"tp{i}_amount"] = 0
        
        # SL scaled by i2
        params["sl_percent"] = round(2.0 * base_scale, 2)
        params["sl_mode"] = cls._calculate_sl_mode(i1)
        
        # Set filters based on profile
        params.update(cls._get_filter_params(filter_profile))
        
        # Create preset
        name = f"{filter_profile.value}_{i1}_{int(i2 * 10)}"
        preset_id = f"TRG_SYS_{name}"
        
        config = PresetConfig(
            id=preset_id,
            name=name,
            indicator_type=cls.INDICATOR_TYPE,
            category=cls._calculate_category_static(i1),
            source=PresetSource.SYSTEM.value,
            params=params,
            description=f"System preset: i1={i1}, i2={i2}, filter={filter_profile.name}",
            tags=["system", filter_profile.value.lower(), f"i1_{i1}", f"i2_{int(i2*10)}"],
        )
        
        return cls(config)
    
    @staticmethod
    def _calculate_tp_count(i1: int) -> int:
        """Calculate TP count based on i1"""
        if i1 <= 25:
            return 4  # Fast trades, fewer TPs
        elif i1 <= 80:
            return 5  # Medium trades
        else:
            return 6  # Long trends, more TPs
    
    @staticmethod
    def _calculate_tp_amount(tp_num: int, tp_count: int) -> int:
        """Calculate TP amount distribution"""
        if tp_count == 4:
            amounts = [50, 30, 15, 5]
        elif tp_count == 5:
            amounts = [40, 25, 20, 10, 5]
        else:  # 6
            amounts = [35, 25, 18, 12, 7, 3]
        
        return amounts[tp_num - 1] if tp_num <= len(amounts) else 0
    
    @staticmethod
    def _calculate_sl_mode(i1: int) -> str:
        """Calculate SL mode based on i1"""
        if i1 <= 25:
            return "fixed"
        elif i1 <= 110:
            return "breakeven"
        else:
            return "cascade"
    
    @staticmethod
    def _calculate_category_static(i1: int) -> str:
        """Static category calculation for class methods"""
        if i1 <= 20:
            return PresetCategory.SCALP.value
        elif i1 <= 40:
            return PresetCategory.SHORT_TERM.value
        elif i1 <= 80:
            return PresetCategory.MID_TERM.value
        elif i1 <= 130:
            return PresetCategory.SWING.value
        else:
            return PresetCategory.LONG_TERM.value
    
    @staticmethod
    def _get_filter_params(profile: FilterProfile) -> Dict[str, Any]:
        """Get filter parameters for a profile"""
        result = {
            "supertrend_enabled": False,
            "supertrend_period": 10,
            "supertrend_multiplier": 3.0,
            "rsi_enabled": False,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "adx_enabled": False,
            "adx_period": 14,
            "adx_threshold": 25,
            "volume_enabled": False,
        }
        
        if profile == FilterProfile.TREND:
            result["supertrend_enabled"] = True
        elif profile == FilterProfile.MOMENTUM:
            result["rsi_enabled"] = True
        elif profile == FilterProfile.STRENGTH:
            result["adx_enabled"] = True
        elif profile == FilterProfile.FULL:
            result["supertrend_enabled"] = True
            result["rsi_enabled"] = True
            result["adx_enabled"] = True
            result["volume_enabled"] = True
        
        return result
    
    @classmethod
    def generate_all_system_presets(cls) -> List["TRGPreset"]:
        """
        Generate all 200 system presets.
        
        Returns:
            List of 200 TRGPreset instances (8 × 5 × 5)
        """
        presets = []
        
        for i1 in cls.I1_VALUES:
            for i2 in cls.I2_VALUES:
                for profile in cls.FILTER_PROFILES:
                    preset = cls.create_system_preset(i1, i2, profile)
                    presets.append(preset)
        
        return presets


# ==================== EXPORTS ====================

__all__ = ["TRGPreset"]
