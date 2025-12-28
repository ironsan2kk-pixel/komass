"""
KOMAS v4.0 — Volatility Filters
================================

Volatility-based filters for controlling when trades can be executed.

Filters:
- ATRFilter: Control trading based on ATR range (min/max boundaries)
- VolumeFilter: Control trading based on volume thresholds
- ExtremeFilter: Block trading during extreme volatility spikes

Chat #39: Filters Volatility
Author: KOMAS Team
Version: 4.0
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
import math

from .base import (
    BaseFilter,
    Signal,
    SignalContext,
    FilterDecision,
    FilterResult,
    FilterCategory,
    FilterPriority,
    create_pass_decision,
    create_block_decision,
    create_skip_decision
)
from .registry import register_filter

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================

# Default ATR settings
DEFAULT_ATR_PERIOD = 14
DEFAULT_ATR_MULTIPLIER = 3.0

# Default Volume settings
DEFAULT_VOLUME_MA_PERIOD = 20
DEFAULT_MIN_VOLUME_RATIO = 1.0

# Extreme volatility thresholds
DEFAULT_EXTREME_ATR_MULTIPLIER = 3.0
DEFAULT_EXTREME_VOLUME_MULTIPLIER = 5.0
DEFAULT_EXTREME_PAUSE_MINUTES = 60


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_atr_percent(atr: float, price: float) -> float:
    """
    Calculate ATR as percentage of price.
    
    Args:
        atr: ATR value
        price: Current price
        
    Returns:
        ATR as percentage (e.g., 2.5 for 2.5%)
    """
    if price <= 0:
        return 0.0
    return (atr / price) * 100


def calculate_volume_ratio(volume: float, avg_volume: float) -> float:
    """
    Calculate volume ratio compared to average.
    
    Args:
        volume: Current volume
        avg_volume: Average volume (e.g., 20-period MA)
        
    Returns:
        Volume ratio (e.g., 1.5 means 50% above average)
    """
    if avg_volume <= 0:
        return 0.0
    return volume / avg_volume


def is_extreme_atr(atr: float, avg_atr: float, multiplier: float = 3.0) -> bool:
    """
    Check if ATR indicates extreme volatility.
    
    Args:
        atr: Current ATR
        avg_atr: Average ATR
        multiplier: Threshold multiplier
        
    Returns:
        True if ATR is extreme
    """
    if avg_atr <= 0:
        return False
    return atr > avg_atr * multiplier


def is_extreme_volume(volume: float, avg_volume: float, multiplier: float = 5.0) -> bool:
    """
    Check if volume indicates extreme spike.
    
    Args:
        volume: Current volume
        avg_volume: Average volume
        multiplier: Threshold multiplier
        
    Returns:
        True if volume is extreme
    """
    if avg_volume <= 0:
        return False
    return volume > avg_volume * multiplier


def format_atr_value(atr: float, price: float, use_percent: bool = True) -> str:
    """
    Format ATR value for display.
    
    Args:
        atr: ATR value
        price: Current price
        use_percent: Display as percentage
        
    Returns:
        Formatted string
    """
    if use_percent:
        pct = calculate_atr_percent(atr, price)
        return f"{pct:.2f}%"
    return f"{atr:.2f}"


def get_volatility_state(
    atr: float,
    avg_atr: float,
    volume: float,
    avg_volume: float
) -> Dict[str, Any]:
    """
    Get comprehensive volatility state.
    
    Args:
        atr: Current ATR
        avg_atr: Average ATR
        volume: Current volume
        avg_volume: Average volume
        
    Returns:
        Dict with volatility metrics
    """
    atr_ratio = atr / avg_atr if avg_atr > 0 else 1.0
    volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
    
    # Determine state
    if atr_ratio > 3.0 or volume_ratio > 5.0:
        state = "extreme"
    elif atr_ratio > 1.5 or volume_ratio > 2.0:
        state = "high"
    elif atr_ratio < 0.5 or volume_ratio < 0.5:
        state = "low"
    else:
        state = "normal"
    
    return {
        "atr": atr,
        "avg_atr": avg_atr,
        "atr_ratio": atr_ratio,
        "volume": volume,
        "avg_volume": avg_volume,
        "volume_ratio": volume_ratio,
        "state": state
    }


def get_volatility_filter_summary(filters: List['BaseFilter']) -> Dict[str, Any]:
    """
    Get summary of all volatility filters.
    
    Args:
        filters: List of volatility filter instances
        
    Returns:
        Summary dict
    """
    enabled = []
    disabled = []
    
    for f in filters:
        if f.category != FilterCategory.VOLATILITY:
            continue
        if f.enabled:
            enabled.append({
                "name": f.name,
                "description": f.description,
                "config": f.config
            })
        else:
            disabled.append(f.name)
    
    return {
        "enabled_count": len(enabled),
        "disabled_count": len(disabled),
        "enabled_filters": enabled,
        "disabled_filters": disabled
    }


def create_volatility_filter_chain(
    atr_config: Optional[Dict] = None,
    volume_config: Optional[Dict] = None,
    extreme_config: Optional[Dict] = None
) -> List['BaseFilter']:
    """
    Create a chain of volatility filters with given configs.
    
    Args:
        atr_config: ATRFilter configuration
        volume_config: VolumeFilter configuration
        extreme_config: ExtremeFilter configuration
        
    Returns:
        List of filter instances
    """
    filters = []
    
    if atr_config is not None:
        filters.append(ATRFilter(atr_config))
    
    if volume_config is not None:
        filters.append(VolumeFilter(volume_config))
    
    if extreme_config is not None:
        filters.append(ExtremeFilter(extreme_config))
    
    return filters


# =============================================================================
# ATR FILTER
# =============================================================================

@register_filter
class ATRFilter(BaseFilter):
    """
    Filter based on ATR (Average True Range) boundaries.
    
    Can filter signals when:
    - ATR is too low (insufficient volatility for profits)
    - ATR is too high (too much risk)
    
    Supports both absolute ATR values and percentage of price.
    
    Usage:
        # Only trade when ATR is between 1% and 5% of price
        filter = ATRFilter({
            "min_atr": 1.0,
            "max_atr": 5.0,
            "use_atr_percent": True
        })
    """
    
    name = "atr_filter"
    description = "Filter signals based on ATR range (min/max boundaries)"
    category = FilterCategory.VOLATILITY
    priority = FilterPriority.MEDIUM
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Extract config values
        self.min_atr = self.config.get("min_atr", None)
        self.max_atr = self.config.get("max_atr", None)
        self.atr_period = self.config.get("atr_period", DEFAULT_ATR_PERIOD)
        self.use_atr_percent = self.config.get("use_atr_percent", True)
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """
        Check if ATR is within acceptable range.
        
        Args:
            signal: Trading signal
            context: Market context with ATR data
            
        Returns:
            FilterDecision with result
        """
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        # Check if we have ATR data
        if context.atr is None:
            logger.debug(f"[{self.name}] No ATR data available")
            return create_skip_decision(
                self.name,
                "No ATR data available",
                data_missing=True
            )
        
        current_atr = context.atr
        current_price = context.current_price
        
        # Convert to percentage if needed
        if self.use_atr_percent and current_price > 0:
            atr_value = calculate_atr_percent(current_atr, current_price)
            unit = "%"
        else:
            atr_value = current_atr
            unit = ""
        
        # Check minimum ATR
        if self.min_atr is not None and atr_value < self.min_atr:
            return create_block_decision(
                self.name,
                f"ATR too low: {atr_value:.2f}{unit} < {self.min_atr}{unit}",
                atr=atr_value,
                min_atr=self.min_atr,
                unit=unit
            )
        
        # Check maximum ATR
        if self.max_atr is not None and atr_value > self.max_atr:
            return create_block_decision(
                self.name,
                f"ATR too high: {atr_value:.2f}{unit} > {self.max_atr}{unit}",
                atr=atr_value,
                max_atr=self.max_atr,
                unit=unit
            )
        
        # ATR is within acceptable range
        return create_pass_decision(
            self.name,
            f"ATR within range: {atr_value:.2f}{unit}",
            atr=atr_value,
            min_atr=self.min_atr,
            max_atr=self.max_atr,
            unit=unit
        )
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable ATR filter"
            },
            "min_atr": {
                "type": "float",
                "default": None,
                "min": 0,
                "max": 100,
                "description": "Minimum ATR value (None = no minimum)"
            },
            "max_atr": {
                "type": "float",
                "default": None,
                "min": 0,
                "max": 100,
                "description": "Maximum ATR value (None = no maximum)"
            },
            "atr_period": {
                "type": "int",
                "default": DEFAULT_ATR_PERIOD,
                "min": 1,
                "max": 200,
                "description": "ATR calculation period"
            },
            "use_atr_percent": {
                "type": "bool",
                "default": True,
                "description": "Interpret min/max as percentage of price"
            }
        }


# =============================================================================
# VOLUME FILTER
# =============================================================================

@register_filter
class VolumeFilter(BaseFilter):
    """
    Filter based on volume thresholds.
    
    Can filter signals when:
    - Volume is below average (low liquidity)
    - Volume is below a minimum ratio vs average
    
    Usage:
        # Only trade when volume is at least 1.5x average
        filter = VolumeFilter({
            "min_volume_ratio": 1.5,
            "volume_ma_period": 20,
            "require_above_average": True
        })
    """
    
    name = "volume_filter"
    description = "Filter signals based on volume thresholds"
    category = FilterCategory.VOLATILITY
    priority = FilterPriority.MEDIUM
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Extract config values
        self.min_volume_ratio = self.config.get("min_volume_ratio", DEFAULT_MIN_VOLUME_RATIO)
        self.volume_ma_period = self.config.get("volume_ma_period", DEFAULT_VOLUME_MA_PERIOD)
        self.require_above_average = self.config.get("require_above_average", True)
        self.min_absolute_volume = self.config.get("min_absolute_volume", None)
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """
        Check if volume meets requirements.
        
        Args:
            signal: Trading signal
            context: Market context with volume data
            
        Returns:
            FilterDecision with result
        """
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        # Check if we have volume data
        if context.volume is None:
            logger.debug(f"[{self.name}] No volume data available")
            return create_skip_decision(
                self.name,
                "No volume data available",
                data_missing=True
            )
        
        current_volume = context.volume
        avg_volume = context.avg_volume
        
        # Check absolute minimum volume
        if self.min_absolute_volume is not None and current_volume < self.min_absolute_volume:
            return create_block_decision(
                self.name,
                f"Volume too low: {current_volume:.2f} < {self.min_absolute_volume}",
                volume=current_volume,
                min_absolute_volume=self.min_absolute_volume
            )
        
        # Check relative volume (vs average)
        if self.require_above_average and avg_volume is not None and avg_volume > 0:
            volume_ratio = calculate_volume_ratio(current_volume, avg_volume)
            
            if volume_ratio < self.min_volume_ratio:
                return create_block_decision(
                    self.name,
                    f"Volume ratio too low: {volume_ratio:.2f}x < {self.min_volume_ratio}x average",
                    volume=current_volume,
                    avg_volume=avg_volume,
                    volume_ratio=volume_ratio,
                    min_ratio=self.min_volume_ratio
                )
            
            return create_pass_decision(
                self.name,
                f"Volume OK: {volume_ratio:.2f}x average",
                volume=current_volume,
                avg_volume=avg_volume,
                volume_ratio=volume_ratio,
                min_ratio=self.min_volume_ratio
            )
        
        # No average volume check needed or no avg_volume data
        return create_pass_decision(
            self.name,
            f"Volume OK: {current_volume:.2f}",
            volume=current_volume
        )
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable volume filter"
            },
            "min_volume_ratio": {
                "type": "float",
                "default": DEFAULT_MIN_VOLUME_RATIO,
                "min": 0.0,
                "max": 10.0,
                "description": "Minimum volume ratio vs MA (e.g., 1.5 = 1.5x average)"
            },
            "volume_ma_period": {
                "type": "int",
                "default": DEFAULT_VOLUME_MA_PERIOD,
                "min": 1,
                "max": 200,
                "description": "Period for volume moving average"
            },
            "require_above_average": {
                "type": "bool",
                "default": True,
                "description": "Require volume to be above average"
            },
            "min_absolute_volume": {
                "type": "float",
                "default": None,
                "min": 0,
                "description": "Minimum absolute volume (None = no minimum)"
            }
        }


# =============================================================================
# EXTREME VOLATILITY FILTER
# =============================================================================

@register_filter
class ExtremeFilter(BaseFilter):
    """
    Filter that blocks trading during extreme volatility spikes.
    
    Monitors for:
    - ATR spikes (e.g., ATR > 3x average)
    - Volume spikes (e.g., Volume > 5x average)
    
    When extreme conditions are detected, trading is paused for
    a configurable duration.
    
    Usage:
        # Pause for 60 minutes after ATR > 3x or Volume > 5x
        filter = ExtremeFilter({
            "atr_multiplier": 3.0,
            "volume_multiplier": 5.0,
            "pause_minutes": 60
        })
    """
    
    name = "extreme_filter"
    description = "Block trading during extreme volatility spikes"
    category = FilterCategory.VOLATILITY
    priority = FilterPriority.CRITICAL  # High priority - check early
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # Extract config values
        self.atr_multiplier = self.config.get("atr_multiplier", DEFAULT_EXTREME_ATR_MULTIPLIER)
        self.volume_multiplier = self.config.get("volume_multiplier", DEFAULT_EXTREME_VOLUME_MULTIPLIER)
        self.pause_minutes = self.config.get("pause_minutes", DEFAULT_EXTREME_PAUSE_MINUTES)
        
        # Check both ATR and Volume by default
        self.check_atr = self.config.get("check_atr", True)
        self.check_volume = self.config.get("check_volume", True)
        
        # State: track when extreme condition was detected
        self._extreme_detected_at: Optional[datetime] = None
        self._extreme_reason: Optional[str] = None
        self._extreme_details: Dict[str, Any] = {}
    
    def should_allow(self, signal: Signal, context: SignalContext) -> FilterDecision:
        """
        Check for extreme volatility conditions.
        
        Args:
            signal: Trading signal
            context: Market context
            
        Returns:
            FilterDecision with result
        """
        if not self.enabled:
            return create_skip_decision(self.name, "Filter disabled")
        
        current_time = context.current_time
        
        # Check if we're still in pause period from previous extreme
        if self._extreme_detected_at is not None:
            pause_until = self._extreme_detected_at + timedelta(minutes=self.pause_minutes)
            if current_time < pause_until:
                remaining = int((pause_until - current_time).total_seconds() / 60)
                return create_block_decision(
                    self.name,
                    f"Extreme volatility pause: {remaining} min remaining ({self._extreme_reason})",
                    pause_until=pause_until.isoformat(),
                    remaining_minutes=remaining,
                    original_reason=self._extreme_reason,
                    **self._extreme_details
                )
            else:
                # Pause period ended
                self._extreme_detected_at = None
                self._extreme_reason = None
                self._extreme_details = {}
        
        # Check for current extreme conditions
        is_extreme = False
        reasons = []
        details = {}
        
        # Check ATR extreme
        if self.check_atr:
            atr_result = self._check_extreme_atr(context)
            if atr_result is not None:
                is_extreme = True
                reasons.append(atr_result["reason"])
                details.update(atr_result["details"])
        
        # Check Volume extreme
        if self.check_volume:
            volume_result = self._check_extreme_volume(context)
            if volume_result is not None:
                is_extreme = True
                reasons.append(volume_result["reason"])
                details.update(volume_result["details"])
        
        # If extreme detected, start pause
        if is_extreme:
            self._extreme_detected_at = current_time
            self._extreme_reason = "; ".join(reasons)
            self._extreme_details = details
            
            return create_block_decision(
                self.name,
                f"Extreme volatility detected: {self._extreme_reason}. Pausing {self.pause_minutes} min",
                pause_minutes=self.pause_minutes,
                **details
            )
        
        # No extreme conditions
        return create_pass_decision(
            self.name,
            "No extreme volatility detected",
            checked_atr=self.check_atr,
            checked_volume=self.check_volume
        )
    
    def _check_extreme_atr(self, context: SignalContext) -> Optional[Dict]:
        """
        Check for extreme ATR condition.
        
        Args:
            context: Market context
            
        Returns:
            Dict with reason and details if extreme, None otherwise
        """
        if context.atr is None:
            return None
        
        # Get average ATR from context or metadata
        avg_atr = context.htf_data.get("avg_atr")
        if avg_atr is None or avg_atr <= 0:
            # No average available, can't determine if extreme
            return None
        
        atr_ratio = context.atr / avg_atr
        
        if atr_ratio > self.atr_multiplier:
            return {
                "reason": f"ATR spike {atr_ratio:.1f}x > {self.atr_multiplier}x",
                "details": {
                    "atr": context.atr,
                    "avg_atr": avg_atr,
                    "atr_ratio": atr_ratio,
                    "atr_multiplier_threshold": self.atr_multiplier
                }
            }
        
        return None
    
    def _check_extreme_volume(self, context: SignalContext) -> Optional[Dict]:
        """
        Check for extreme volume condition.
        
        Args:
            context: Market context
            
        Returns:
            Dict with reason and details if extreme, None otherwise
        """
        if context.volume is None or context.avg_volume is None:
            return None
        
        if context.avg_volume <= 0:
            return None
        
        volume_ratio = context.volume / context.avg_volume
        
        if volume_ratio > self.volume_multiplier:
            return {
                "reason": f"Volume spike {volume_ratio:.1f}x > {self.volume_multiplier}x",
                "details": {
                    "volume": context.volume,
                    "avg_volume": context.avg_volume,
                    "volume_ratio": volume_ratio,
                    "volume_multiplier_threshold": self.volume_multiplier
                }
            }
        
        return None
    
    def reset(self) -> None:
        """Reset extreme detection state."""
        self._extreme_detected_at = None
        self._extreme_reason = None
        self._extreme_details = {}
    
    def get_pause_remaining(self, current_time: datetime) -> Optional[int]:
        """
        Get remaining pause time in minutes.
        
        Args:
            current_time: Current datetime
            
        Returns:
            Minutes remaining or None if not in pause
        """
        if self._extreme_detected_at is None:
            return None
        
        pause_until = self._extreme_detected_at + timedelta(minutes=self.pause_minutes)
        if current_time >= pause_until:
            return None
        
        return int((pause_until - current_time).total_seconds() / 60)
    
    def is_in_pause(self, current_time: datetime) -> bool:
        """
        Check if currently in pause period.
        
        Args:
            current_time: Current datetime
            
        Returns:
            True if in pause
        """
        return self.get_pause_remaining(current_time) is not None
    
    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "enabled": {
                "type": "bool",
                "default": True,
                "description": "Enable extreme volatility filter"
            },
            "atr_multiplier": {
                "type": "float",
                "default": DEFAULT_EXTREME_ATR_MULTIPLIER,
                "min": 1.5,
                "max": 10.0,
                "description": "ATR spike threshold (multiplier vs average)"
            },
            "volume_multiplier": {
                "type": "float",
                "default": DEFAULT_EXTREME_VOLUME_MULTIPLIER,
                "min": 2.0,
                "max": 20.0,
                "description": "Volume spike threshold (multiplier vs average)"
            },
            "pause_minutes": {
                "type": "int",
                "default": DEFAULT_EXTREME_PAUSE_MINUTES,
                "min": 5,
                "max": 1440,
                "description": "Pause duration after extreme detection (minutes)"
            },
            "check_atr": {
                "type": "bool",
                "default": True,
                "description": "Check for ATR spikes"
            },
            "check_volume": {
                "type": "bool",
                "default": True,
                "description": "Check for volume spikes"
            }
        }


# =============================================================================
# COMBINATION HELPERS
# =============================================================================

def create_volatility_profile(profile_name: str) -> Dict[str, Dict]:
    """
    Create predefined volatility filter configurations.
    
    Args:
        profile_name: Profile name (conservative, balanced, aggressive)
        
    Returns:
        Dict of filter_name -> config
    """
    profiles = {
        "conservative": {
            "atr_filter": {
                "enabled": True,
                "min_atr": 0.5,
                "max_atr": 3.0,
                "use_atr_percent": True
            },
            "volume_filter": {
                "enabled": True,
                "min_volume_ratio": 1.5,
                "require_above_average": True
            },
            "extreme_filter": {
                "enabled": True,
                "atr_multiplier": 2.5,
                "volume_multiplier": 4.0,
                "pause_minutes": 120
            }
        },
        "balanced": {
            "atr_filter": {
                "enabled": True,
                "min_atr": 0.3,
                "max_atr": 5.0,
                "use_atr_percent": True
            },
            "volume_filter": {
                "enabled": True,
                "min_volume_ratio": 1.0,
                "require_above_average": True
            },
            "extreme_filter": {
                "enabled": True,
                "atr_multiplier": 3.0,
                "volume_multiplier": 5.0,
                "pause_minutes": 60
            }
        },
        "aggressive": {
            "atr_filter": {
                "enabled": True,
                "min_atr": 0.1,
                "max_atr": 10.0,
                "use_atr_percent": True
            },
            "volume_filter": {
                "enabled": False
            },
            "extreme_filter": {
                "enabled": True,
                "atr_multiplier": 4.0,
                "volume_multiplier": 8.0,
                "pause_minutes": 30
            }
        },
        "disabled": {
            "atr_filter": {"enabled": False},
            "volume_filter": {"enabled": False},
            "extreme_filter": {"enabled": False}
        }
    }
    
    if profile_name not in profiles:
        logger.warning(f"Unknown volatility profile: {profile_name}, using 'balanced'")
        profile_name = "balanced"
    
    return profiles[profile_name]


def validate_volatility_config(config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate volatility filter configuration.
    
    Args:
        config: Configuration dict
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Validate ATR filter
    atr_config = config.get("atr_filter", {})
    if atr_config.get("enabled", True):
        min_atr = atr_config.get("min_atr")
        max_atr = atr_config.get("max_atr")
        
        if min_atr is not None and max_atr is not None:
            if min_atr >= max_atr:
                errors.append("ATR: min_atr must be less than max_atr")
        
        if min_atr is not None and min_atr < 0:
            errors.append("ATR: min_atr must be non-negative")
    
    # Validate Volume filter
    volume_config = config.get("volume_filter", {})
    if volume_config.get("enabled", True):
        ratio = volume_config.get("min_volume_ratio", 1.0)
        if ratio < 0:
            errors.append("Volume: min_volume_ratio must be non-negative")
    
    # Validate Extreme filter
    extreme_config = config.get("extreme_filter", {})
    if extreme_config.get("enabled", True):
        atr_mult = extreme_config.get("atr_multiplier", 3.0)
        vol_mult = extreme_config.get("volume_multiplier", 5.0)
        pause = extreme_config.get("pause_minutes", 60)
        
        if atr_mult < 1.0:
            errors.append("Extreme: atr_multiplier must be >= 1.0")
        if vol_mult < 1.0:
            errors.append("Extreme: volume_multiplier must be >= 1.0")
        if pause < 1:
            errors.append("Extreme: pause_minutes must be >= 1")
    
    return len(errors) == 0, errors
