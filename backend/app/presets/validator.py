"""
Komas Trading Server - Preset Validator
=======================================
Comprehensive validation for presets and their parameters.

Features:
- Schema-based validation
- Cross-parameter validation
- Business logic validation
- Detailed error messages
- Validation helpers for API

Version: 1.0
Chat: #29 — Presets Architecture
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Type
from dataclasses import dataclass
from enum import Enum

from .base import BasePreset, PresetConfig, IndicatorType, PresetCategory, PresetSource
from .trg_preset import TRGPreset
from .dominant_preset import DominantPreset

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Validation error severity levels"""
    ERROR = "error"       # Must be fixed
    WARNING = "warning"   # Should be fixed but valid
    INFO = "info"         # Informational only


@dataclass
class ValidationError:
    """Validation error with details"""
    field: str
    message: str
    severity: ValidationSeverity = ValidationSeverity.ERROR
    value: Any = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "field": self.field,
            "message": self.message,
            "severity": self.severity.value,
            "value": str(self.value) if self.value is not None else None,
            "suggestion": self.suggestion,
        }


class PresetValidator:
    """
    Comprehensive preset validator.
    
    Usage:
        validator = PresetValidator()
        result = validator.validate(preset)
        if not result.is_valid:
            print(result.errors)
    """
    
    def __init__(self):
        # Validator registry by indicator type
        self._validators: Dict[str, callable] = {
            IndicatorType.TRG.value: self._validate_trg,
            IndicatorType.DOMINANT.value: self._validate_dominant,
        }
    
    def validate(self, preset: BasePreset) -> "ValidationResult":
        """
        Validate a preset.
        
        Args:
            preset: Preset instance to validate
            
        Returns:
            ValidationResult with errors/warnings
        """
        errors = []
        
        # Basic config validation
        errors.extend(self._validate_config(preset.config))
        
        # Parameter validation from preset class
        is_valid, param_errors = preset.validate()
        for err in param_errors:
            errors.append(ValidationError(
                field="params",
                message=err,
                severity=ValidationSeverity.ERROR
            ))
        
        # Type-specific validation
        indicator_type = preset.config.indicator_type
        if indicator_type in self._validators:
            type_errors = self._validators[indicator_type](preset)
            errors.extend(type_errors)
        
        # Cross-parameter validation
        errors.extend(self._validate_cross_params(preset))
        
        return ValidationResult(errors)
    
    def validate_params(
        self,
        indicator_type: str,
        params: Dict[str, Any]
    ) -> "ValidationResult":
        """
        Validate parameters without full preset.
        
        Args:
            indicator_type: Indicator type
            params: Parameter dictionary
            
        Returns:
            ValidationResult
        """
        errors = []
        
        # Get preset class
        if indicator_type == IndicatorType.TRG.value:
            preset_class = TRGPreset
        elif indicator_type == IndicatorType.DOMINANT.value:
            preset_class = DominantPreset
        else:
            errors.append(ValidationError(
                field="indicator_type",
                message=f"Unknown indicator type: {indicator_type}",
                value=indicator_type
            ))
            return ValidationResult(errors)
        
        # Create temporary preset for validation
        config = PresetConfig(
            id="temp_validation",
            name="Validation",
            indicator_type=indicator_type,
            params=params
        )
        preset = preset_class(config)
        
        # Run parameter validation
        param_errors = preset.validate_params(params)
        for err in param_errors:
            errors.append(ValidationError(
                field="params",
                message=err,
                severity=ValidationSeverity.ERROR
            ))
        
        return ValidationResult(errors)
    
    def validate_for_import(self, data: Dict[str, Any]) -> "ValidationResult":
        """
        Validate data for import.
        
        Args:
            data: Import data dictionary
            
        Returns:
            ValidationResult
        """
        errors = []
        
        # Required fields
        if 'name' not in data or not data['name']:
            errors.append(ValidationError(
                field="name",
                message="Name is required for import",
                severity=ValidationSeverity.ERROR
            ))
        
        if 'indicator_type' not in data:
            errors.append(ValidationError(
                field="indicator_type",
                message="Indicator type is required",
                severity=ValidationSeverity.ERROR,
                suggestion="Use 'trg' or 'dominant'"
            ))
        
        if 'params' not in data or not isinstance(data.get('params'), dict):
            errors.append(ValidationError(
                field="params",
                message="Parameters dictionary is required",
                severity=ValidationSeverity.ERROR
            ))
        
        # Validate indicator type
        indicator_type = data.get('indicator_type', '')
        if indicator_type and indicator_type not in [e.value for e in IndicatorType]:
            errors.append(ValidationError(
                field="indicator_type",
                message=f"Invalid indicator type: {indicator_type}",
                value=indicator_type,
                suggestion=f"Use one of: {[e.value for e in IndicatorType]}"
            ))
        
        # Validate category if provided
        category = data.get('category')
        if category and category not in [e.value for e in PresetCategory]:
            errors.append(ValidationError(
                field="category",
                message=f"Invalid category: {category}",
                value=category,
                severity=ValidationSeverity.WARNING,
                suggestion=f"Use one of: {[e.value for e in PresetCategory]}"
            ))
        
        # If no errors so far, validate params
        if not any(e.severity == ValidationSeverity.ERROR for e in errors):
            params_result = self.validate_params(
                data.get('indicator_type', 'trg'),
                data.get('params', {})
            )
            errors.extend(params_result.errors)
        
        return ValidationResult(errors)
    
    # ==================== PRIVATE VALIDATORS ====================
    
    def _validate_config(self, config: PresetConfig) -> List[ValidationError]:
        """Validate preset configuration"""
        errors = []
        
        # ID validation
        if not config.id:
            errors.append(ValidationError(
                field="id",
                message="Preset ID is required"
            ))
        elif len(config.id) > 100:
            errors.append(ValidationError(
                field="id",
                message="Preset ID must be <= 100 characters",
                value=config.id
            ))
        
        # Name validation
        if not config.name or not config.name.strip():
            errors.append(ValidationError(
                field="name",
                message="Preset name is required"
            ))
        elif len(config.name) > 100:
            errors.append(ValidationError(
                field="name",
                message="Preset name must be <= 100 characters",
                value=config.name
            ))
        
        # Indicator type validation
        if config.indicator_type not in [e.value for e in IndicatorType]:
            errors.append(ValidationError(
                field="indicator_type",
                message=f"Invalid indicator type: {config.indicator_type}",
                value=config.indicator_type
            ))
        
        # Category validation
        if config.category not in [e.value for e in PresetCategory]:
            errors.append(ValidationError(
                field="category",
                message=f"Invalid category: {config.category}",
                value=config.category,
                severity=ValidationSeverity.WARNING
            ))
        
        # Source validation
        if config.source not in [e.value for e in PresetSource]:
            errors.append(ValidationError(
                field="source",
                message=f"Invalid source: {config.source}",
                value=config.source,
                severity=ValidationSeverity.WARNING
            ))
        
        # Description length
        if config.description and len(config.description) > 500:
            errors.append(ValidationError(
                field="description",
                message="Description must be <= 500 characters",
                value=len(config.description),
                severity=ValidationSeverity.WARNING
            ))
        
        return errors
    
    def _validate_trg(self, preset: BasePreset) -> List[ValidationError]:
        """TRG-specific validation"""
        errors = []
        params = preset.params
        
        # Validate TP/SL ratio
        if params.get('tp1_percent') and params.get('sl_percent'):
            tp1 = params['tp1_percent']
            sl = params['sl_percent']
            
            if sl > tp1:
                errors.append(ValidationError(
                    field="sl_percent",
                    message=f"SL ({sl}%) is larger than TP1 ({tp1}%)",
                    severity=ValidationSeverity.WARNING,
                    suggestion="Consider reducing SL or increasing TP1"
                ))
        
        # Validate i1/i2 combination
        i1 = params.get('i1', 45)
        i2 = params.get('i2', 4.0)
        
        if i1 < 20 and i2 > 6:
            errors.append(ValidationError(
                field="i1",
                message=f"Fast ATR (i1={i1}) with high multiplier (i2={i2}) may cause many false signals",
                severity=ValidationSeverity.WARNING,
                suggestion="Consider using lower i2 for fast ATR"
            ))
        
        if i1 > 150 and i2 < 2.5:
            errors.append(ValidationError(
                field="i2",
                message=f"Slow ATR (i1={i1}) with low multiplier (i2={i2}) may miss entries",
                severity=ValidationSeverity.INFO,
                suggestion="Consider using higher i2 for slow ATR"
            ))
        
        return errors
    
    def _validate_dominant(self, preset: BasePreset) -> List[ValidationError]:
        """Dominant-specific validation"""
        errors = []
        params = preset.params
        
        # Validate sensitivity range
        sensitivity = params.get('sensitivity', 21)
        
        if sensitivity < 15:
            errors.append(ValidationError(
                field="sensitivity",
                message=f"Very low sensitivity ({sensitivity}) may generate many false signals",
                severity=ValidationSeverity.WARNING,
                suggestion="Consider sensitivity >= 15 for more reliable signals"
            ))
        
        if sensitivity > 50:
            errors.append(ValidationError(
                field="sensitivity",
                message=f"High sensitivity ({sensitivity}) may miss trading opportunities",
                severity=ValidationSeverity.INFO,
                suggestion="Consider sensitivity <= 50 for more frequent signals"
            ))
        
        # Validate TP progression
        tp1 = params.get('tp1_percent', 1.0)
        tp4 = params.get('tp4_percent', 5.0)
        sl = params.get('sl_percent', 2.0)
        
        if tp4 < tp1 * 3:
            errors.append(ValidationError(
                field="tp4_percent",
                message=f"TP4 ({tp4}%) is less than 3x TP1 ({tp1}%)",
                severity=ValidationSeverity.INFO,
                suggestion="Consider wider TP spread for trend following"
            ))
        
        if sl > tp1 * 2:
            errors.append(ValidationError(
                field="sl_percent",
                message=f"SL ({sl}%) is more than 2x TP1 ({tp1}%)",
                severity=ValidationSeverity.WARNING,
                suggestion="Consider tighter SL or wider TP1"
            ))
        
        return errors
    
    def _validate_cross_params(self, preset: BasePreset) -> List[ValidationError]:
        """Cross-parameter validation"""
        errors = []
        params = preset.params
        
        # Check for leverage warnings
        leverage = params.get('leverage', 10)
        if leverage > 50:
            errors.append(ValidationError(
                field="leverage",
                message=f"Very high leverage ({leverage}x) is extremely risky",
                value=leverage,
                severity=ValidationSeverity.WARNING,
                suggestion="Consider leverage <= 20x for safety"
            ))
        
        # Risk/reward checks (if we have enough data)
        if 'sl_percent' in params and 'tp1_percent' in params:
            sl = params['sl_percent']
            tp1 = params['tp1_percent']
            rr = tp1 / sl if sl > 0 else 0
            
            if rr < 0.5:
                errors.append(ValidationError(
                    field="risk_reward",
                    message=f"Risk/Reward ratio ({rr:.2f}) is very low",
                    severity=ValidationSeverity.WARNING,
                    suggestion="Aim for R:R >= 1.0"
                ))
        
        return errors


@dataclass
class ValidationResult:
    """Result of preset validation"""
    errors: List[ValidationError]
    
    @property
    def is_valid(self) -> bool:
        """Check if preset is valid (no ERROR severity)"""
        return not any(e.severity == ValidationSeverity.ERROR for e in self.errors)
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are warnings"""
        return any(e.severity == ValidationSeverity.WARNING for e in self.errors)
    
    @property
    def error_count(self) -> int:
        """Count of errors"""
        return sum(1 for e in self.errors if e.severity == ValidationSeverity.ERROR)
    
    @property
    def warning_count(self) -> int:
        """Count of warnings"""
        return sum(1 for e in self.errors if e.severity == ValidationSeverity.WARNING)
    
    def get_errors(self) -> List[ValidationError]:
        """Get only errors"""
        return [e for e in self.errors if e.severity == ValidationSeverity.ERROR]
    
    def get_warnings(self) -> List[ValidationError]:
        """Get only warnings"""
        return [e for e in self.errors if e.severity == ValidationSeverity.WARNING]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "errors": [e.to_dict() for e in self.get_errors()],
            "warnings": [e.to_dict() for e in self.get_warnings()],
        }
    
    def __repr__(self) -> str:
        return f"ValidationResult(valid={self.is_valid}, errors={self.error_count}, warnings={self.warning_count})"


# ==================== HELPER FUNCTIONS ====================

def validate_preset(preset: BasePreset) -> ValidationResult:
    """Convenience function to validate a preset"""
    return PresetValidator().validate(preset)


def validate_params(indicator_type: str, params: Dict[str, Any]) -> ValidationResult:
    """Convenience function to validate parameters"""
    return PresetValidator().validate_params(indicator_type, params)


def validate_import(data: Dict[str, Any]) -> ValidationResult:
    """Convenience function to validate import data"""
    return PresetValidator().validate_for_import(data)


# ==================== EXPORTS ====================

__all__ = [
    "ValidationSeverity",
    "ValidationError",
    "ValidationResult",
    "PresetValidator",
    "validate_preset",
    "validate_params",
    "validate_import",
]
