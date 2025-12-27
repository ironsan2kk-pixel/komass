"""
Komas Trading Server - Preset Models
====================================
Pydantic models for preset validation and API responses.

Supports both TRG and Dominant indicators with their specific parameters.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator


# ============ CATEGORY TYPES ============

CategoryType = Literal["scalp", "short-term", "mid-term", "swing", "long-term", "special"]
IndicatorType = Literal["trg", "dominant"]
SourceType = Literal["system", "pine_script", "optimizer", "manual", "imported"]
FilterTypeInt = Literal[0, 1, 2, 3, 4, 5, 6]
SLModeInt = Literal[0, 1, 2, 3, 4]


# ============ DOMINANT PRESET PARAMS ============

class DominantParams(BaseModel):
    """Parameters specific to Dominant indicator preset"""
    sensitivity: float = Field(..., ge=10, le=100, description="Channel sensitivity (12-60 typical)")
    
    # Take Profits
    tp1_percent: float = Field(..., ge=0.1, le=50, description="TP1 percent")
    tp2_percent: float = Field(..., ge=0.1, le=50, description="TP2 percent")
    tp3_percent: float = Field(..., ge=0.1, le=50, description="TP3 percent")
    tp4_percent: float = Field(..., ge=0.1, le=50, description="TP4 percent")
    
    # Stop Loss
    sl_percent: float = Field(..., ge=0.1, le=50, description="Stop loss percent")
    
    # Filter type: 0=None, 1=ATR, 2=RSI, 3=ATR+RSI, 4=Volatility, 5=Special1, 6=Special2
    filter_type: int = Field(default=0, ge=0, le=6, description="Filter type (0-6)")
    
    # SL Mode: 0=No SL movement, 1=After TP1, 2=After TP2, 3=After TP3, 4=Cascade
    sl_mode: int = Field(default=0, ge=0, le=4, description="Stop loss mode (0-4)")
    
    # Fixed stop (some presets have this)
    fixed_stop: bool = Field(default=True, description="Use fixed stop loss")
    
    @field_validator('sensitivity')
    @classmethod
    def validate_sensitivity(cls, v):
        if v <= 0:
            raise ValueError('Sensitivity must be positive')
        return round(v, 1)
    
    @field_validator('tp1_percent', 'tp2_percent', 'tp3_percent', 'tp4_percent', 'sl_percent')
    @classmethod
    def validate_percents(cls, v):
        return round(v, 2)


class TRGParams(BaseModel):
    """Parameters specific to TRG indicator preset"""
    i1: int = Field(..., ge=10, le=200, description="ATR Length")
    i2: float = Field(..., ge=1.0, le=10.0, description="Multiplier")
    
    # Take Profits (up to 10)
    tp_count: int = Field(default=4, ge=1, le=10)
    tp_percents: List[float] = Field(default=[1.05, 1.95, 3.75, 6.0])
    tp_amounts: List[int] = Field(default=[50, 30, 15, 5])
    
    # Stop Loss
    sl_percent: float = Field(default=2.0, ge=0.5, le=50)
    sl_mode: str = Field(default="fixed")  # fixed, breakeven, cascade
    
    # Filters
    supertrend_enabled: bool = Field(default=False)
    supertrend_period: int = Field(default=10)
    supertrend_multiplier: float = Field(default=3.0)
    
    rsi_enabled: bool = Field(default=False)
    rsi_period: int = Field(default=14)
    rsi_overbought: int = Field(default=70)
    rsi_oversold: int = Field(default=30)
    
    adx_enabled: bool = Field(default=False)
    adx_period: int = Field(default=14)
    adx_threshold: int = Field(default=25)
    
    volume_enabled: bool = Field(default=False)


# ============ PRESET SCHEMAS ============

class PresetBase(BaseModel):
    """Base preset fields"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    indicator_type: IndicatorType = Field(default="dominant")
    category: CategoryType = Field(default="mid-term")
    
    # Symbol and timeframe (optional - None means universal)
    symbol: Optional[str] = Field(None, max_length=20)
    timeframe: Optional[str] = Field(None, max_length=10)
    
    # Tags for filtering
    tags: Optional[List[str]] = Field(default=None)


class PresetCreate(PresetBase):
    """Schema for creating a preset"""
    params: Dict[str, Any] = Field(..., description="Indicator-specific parameters")
    source: SourceType = Field(default="manual")


class PresetUpdate(BaseModel):
    """Schema for updating a preset"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[CategoryType] = None
    symbol: Optional[str] = Field(None, max_length=20)
    timeframe: Optional[str] = Field(None, max_length=10)
    params: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_favorite: Optional[bool] = None


class PresetResponse(PresetBase):
    """Response schema for preset"""
    id: str = Field(..., description="Unique preset ID")
    params: Dict[str, Any]
    source: SourceType
    is_active: bool = True
    is_favorite: bool = False
    
    # Performance metrics (optional)
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    total_profit_percent: Optional[float] = None
    max_drawdown_percent: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PresetListResponse(BaseModel):
    """Response for list of presets"""
    total: int
    presets: List[PresetResponse]
    

class PresetStatsResponse(BaseModel):
    """Statistics about presets"""
    total_presets: int
    by_indicator: Dict[str, int]
    by_category: Dict[str, int]
    by_source: Dict[str, int]
    active_count: int
    favorites_count: int


# ============ DOMINANT PRESET SPECIFIC ============

class DominantPresetCreate(BaseModel):
    """Simplified creation schema for Dominant presets"""
    name: str
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    category: CategoryType = "mid-term"
    description: Optional[str] = None
    
    # Dominant-specific params
    sensitivity: float
    tp1_percent: float
    tp2_percent: float
    tp3_percent: float
    tp4_percent: float
    sl_percent: float
    filter_type: int = 0
    sl_mode: int = 0
    fixed_stop: bool = True
    
    source: SourceType = "manual"
    
    def to_preset_create(self) -> PresetCreate:
        """Convert to generic PresetCreate"""
        return PresetCreate(
            name=self.name,
            description=self.description,
            indicator_type="dominant",
            category=self.category,
            symbol=self.symbol,
            timeframe=self.timeframe,
            source=self.source,
            params={
                "sensitivity": self.sensitivity,
                "tp1_percent": self.tp1_percent,
                "tp2_percent": self.tp2_percent,
                "tp3_percent": self.tp3_percent,
                "tp4_percent": self.tp4_percent,
                "sl_percent": self.sl_percent,
                "filter_type": self.filter_type,
                "sl_mode": self.sl_mode,
                "fixed_stop": self.fixed_stop
            }
        )


class DominantPresetResponse(BaseModel):
    """Response with flattened Dominant params"""
    id: str
    name: str
    symbol: Optional[str]
    timeframe: Optional[str]
    category: str
    description: Optional[str]
    
    # Params flattened
    sensitivity: float
    tp1_percent: float
    tp2_percent: float
    tp3_percent: float
    tp4_percent: float
    sl_percent: float
    filter_type: int
    sl_mode: int
    fixed_stop: bool
    
    source: str
    is_active: bool
    is_favorite: bool
    
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_preset_response(cls, preset: PresetResponse) -> "DominantPresetResponse":
        """Create from generic PresetResponse"""
        params = preset.params
        return cls(
            id=preset.id,
            name=preset.name,
            symbol=preset.symbol,
            timeframe=preset.timeframe,
            category=preset.category,
            description=preset.description,
            sensitivity=params.get("sensitivity", 21),
            tp1_percent=params.get("tp1_percent", 1.0),
            tp2_percent=params.get("tp2_percent", 2.0),
            tp3_percent=params.get("tp3_percent", 3.0),
            tp4_percent=params.get("tp4_percent", 5.0),
            sl_percent=params.get("sl_percent", 2.0),
            filter_type=params.get("filter_type", 0),
            sl_mode=params.get("sl_mode", 0),
            fixed_stop=params.get("fixed_stop", True),
            source=preset.source,
            is_active=preset.is_active,
            is_favorite=preset.is_favorite,
            created_at=preset.created_at,
            updated_at=preset.updated_at
        )


# ============ EXPORT ============

__all__ = [
    # Types
    "CategoryType",
    "IndicatorType", 
    "SourceType",
    "FilterTypeInt",
    "SLModeInt",
    
    # Param models
    "DominantParams",
    "TRGParams",
    
    # Generic schemas
    "PresetBase",
    "PresetCreate",
    "PresetUpdate",
    "PresetResponse",
    "PresetListResponse",
    "PresetStatsResponse",
    
    # Dominant-specific
    "DominantPresetCreate",
    "DominantPresetResponse",
]
