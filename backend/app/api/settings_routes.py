"""
Komas Trading Server - Settings API
===================================
User settings and presets management
"""
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path

router = APIRouter(prefix="/api/settings", tags=["Settings"])

# Data directory for storing settings
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

PRESETS_FILE = DATA_DIR / "presets.json"
SETTINGS_FILE = DATA_DIR / "settings.json"


# ============ MODELS ============

class IndicatorPreset(BaseModel):
    """Indicator preset configuration"""
    id: Optional[str] = None
    name: str
    description: str = ""
    
    # TRG Indicator
    trg_atr_length: int = Field(default=45, ge=10, le=200)
    trg_multiplier: float = Field(default=4.0, ge=1.0, le=10.0)
    
    # Take Profits
    tp_count: int = Field(default=4, ge=1, le=10)
    tp1_percent: float = Field(default=1.05)
    tp1_amount: float = Field(default=50)
    tp2_percent: float = Field(default=1.95)
    tp2_amount: float = Field(default=30)
    tp3_percent: float = Field(default=3.75)
    tp3_amount: float = Field(default=15)
    tp4_percent: float = Field(default=6.0)
    tp4_amount: float = Field(default=5)
    
    # Stop Loss
    sl_percent: float = Field(default=2.0)
    sl_mode: str = Field(default="fixed")  # fixed, breakeven, cascade
    
    # Filters
    use_supertrend: bool = False
    supertrend_period: int = 10
    supertrend_multiplier: float = 3.0
    
    use_rsi: bool = False
    rsi_period: int = 14
    rsi_overbought: int = 70
    rsi_oversold: int = 30
    
    use_adx: bool = False
    adx_period: int = 14
    adx_threshold: int = 25
    
    use_volume: bool = False
    volume_multiplier: float = 1.5
    
    # Trading
    leverage: int = Field(default=1, ge=1, le=125)
    commission_enabled: bool = True
    commission_percent: float = 0.075
    
    # Timestamps
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class UserSettings(BaseModel):
    """User settings"""
    default_symbol: str = "BTCUSDT"
    default_timeframe: str = "1h"
    default_preset_id: Optional[str] = None
    
    # UI preferences
    theme: str = "dark"
    auto_refresh: bool = True
    refresh_interval: int = 30  # seconds
    
    # Notifications
    notify_signals: bool = True
    notify_tp_hit: bool = True
    notify_sl_hit: bool = True
    telegram_enabled: bool = False
    telegram_chat_id: Optional[str] = None


# ============ HELPER FUNCTIONS ============

def load_presets() -> List[Dict]:
    """Load presets from file"""
    if PRESETS_FILE.exists():
        with open(PRESETS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return get_default_presets()


def save_presets(presets: List[Dict]):
    """Save presets to file"""
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(presets, f, indent=2, ensure_ascii=False)


def load_settings() -> Dict:
    """Load user settings from file"""
    if SETTINGS_FILE.exists():
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return UserSettings().model_dump()


def save_settings(settings: Dict):
    """Save user settings to file"""
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def get_default_presets() -> List[Dict]:
    """Get default presets"""
    return [
        {
            "id": "default",
            "name": "Default",
            "description": "Standard TRG settings",
            "trg_atr_length": 45,
            "trg_multiplier": 4.0,
            "tp_count": 4,
            "tp1_percent": 1.05, "tp1_amount": 50,
            "tp2_percent": 1.95, "tp2_amount": 30,
            "tp3_percent": 3.75, "tp3_amount": 15,
            "tp4_percent": 6.0, "tp4_amount": 5,
            "sl_percent": 2.0,
            "sl_mode": "fixed",
            "use_supertrend": False,
            "use_rsi": False,
            "use_adx": False,
            "use_volume": False,
            "leverage": 1,
            "commission_enabled": True,
            "commission_percent": 0.075,
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "conservative",
            "name": "Conservative",
            "description": "Lower risk, smaller take profits",
            "trg_atr_length": 60,
            "trg_multiplier": 5.0,
            "tp_count": 2,
            "tp1_percent": 0.75, "tp1_amount": 60,
            "tp2_percent": 1.5, "tp2_amount": 40,
            "tp3_percent": 2.0, "tp3_amount": 0,
            "tp4_percent": 3.0, "tp4_amount": 0,
            "sl_percent": 1.5,
            "sl_mode": "fixed",
            "use_supertrend": True,
            "supertrend_period": 10,
            "supertrend_multiplier": 3.0,
            "use_rsi": True,
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "use_adx": False,
            "use_volume": False,
            "leverage": 1,
            "commission_enabled": True,
            "commission_percent": 0.075,
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "aggressive",
            "name": "Aggressive",
            "description": "Higher risk, larger take profits",
            "trg_atr_length": 30,
            "trg_multiplier": 3.0,
            "tp_count": 6,
            "tp1_percent": 1.5, "tp1_amount": 25,
            "tp2_percent": 3.0, "tp2_amount": 20,
            "tp3_percent": 5.0, "tp3_amount": 20,
            "tp4_percent": 8.0, "tp4_amount": 15,
            "sl_percent": 3.0,
            "sl_mode": "cascade",
            "use_supertrend": False,
            "use_rsi": False,
            "use_adx": True,
            "adx_period": 14,
            "adx_threshold": 25,
            "use_volume": True,
            "volume_multiplier": 1.5,
            "leverage": 3,
            "commission_enabled": True,
            "commission_percent": 0.075,
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "scalper",
            "name": "Scalper",
            "description": "Quick trades, small profits",
            "trg_atr_length": 20,
            "trg_multiplier": 2.5,
            "tp_count": 2,
            "tp1_percent": 0.5, "tp1_amount": 70,
            "tp2_percent": 1.0, "tp2_amount": 30,
            "tp3_percent": 1.5, "tp3_amount": 0,
            "tp4_percent": 2.0, "tp4_amount": 0,
            "sl_percent": 1.0,
            "sl_mode": "breakeven",
            "use_supertrend": False,
            "use_rsi": True,
            "rsi_period": 7,
            "rsi_overbought": 65,
            "rsi_oversold": 35,
            "use_adx": False,
            "use_volume": True,
            "volume_multiplier": 2.0,
            "leverage": 5,
            "commission_enabled": True,
            "commission_percent": 0.075,
            "created_at": datetime.now().isoformat()
        }
    ]


# ============ PRESETS ENDPOINTS ============

@router.get("/presets")
async def get_presets():
    """Get all presets"""
    presets = load_presets()
    return {
        "success": True,
        "count": len(presets),
        "presets": presets
    }


@router.get("/presets/{preset_id}")
async def get_preset(preset_id: str):
    """Get a specific preset by ID"""
    presets = load_presets()
    for p in presets:
        if p.get("id") == preset_id:
            return {"success": True, "preset": p}
    raise HTTPException(404, f"Preset '{preset_id}' not found")


@router.post("/presets")
async def create_preset(preset: IndicatorPreset):
    """Create a new preset"""
    presets = load_presets()
    
    # Generate ID if not provided
    if not preset.id:
        preset.id = f"preset_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Check for duplicate ID
    for p in presets:
        if p.get("id") == preset.id:
            raise HTTPException(400, f"Preset with ID '{preset.id}' already exists")
    
    # Add timestamps
    preset.created_at = datetime.now().isoformat()
    preset.updated_at = datetime.now().isoformat()
    
    presets.append(preset.model_dump())
    save_presets(presets)
    
    return {"success": True, "preset": preset.model_dump()}


@router.put("/presets/{preset_id}")
async def update_preset(preset_id: str, preset: IndicatorPreset):
    """Update an existing preset"""
    presets = load_presets()
    
    for i, p in enumerate(presets):
        if p.get("id") == preset_id:
            preset.id = preset_id
            preset.created_at = p.get("created_at")
            preset.updated_at = datetime.now().isoformat()
            presets[i] = preset.model_dump()
            save_presets(presets)
            return {"success": True, "preset": presets[i]}
    
    raise HTTPException(404, f"Preset '{preset_id}' not found")


@router.delete("/presets/{preset_id}")
async def delete_preset(preset_id: str):
    """Delete a preset"""
    presets = load_presets()
    
    # Don't allow deleting default presets
    if preset_id in ["default", "conservative", "aggressive", "scalper"]:
        raise HTTPException(400, "Cannot delete default presets")
    
    original_count = len(presets)
    presets = [p for p in presets if p.get("id") != preset_id]
    
    if len(presets) == original_count:
        raise HTTPException(404, f"Preset '{preset_id}' not found")
    
    save_presets(presets)
    return {"success": True, "message": f"Preset '{preset_id}' deleted"}


@router.post("/presets/reset")
async def reset_presets():
    """Reset presets to defaults"""
    presets = get_default_presets()
    save_presets(presets)
    return {"success": True, "message": "Presets reset to defaults", "count": len(presets)}


# ============ SETTINGS ENDPOINTS ============

@router.get("")
async def get_settings():
    """Get user settings"""
    settings = load_settings()
    return {"success": True, "settings": settings}


@router.post("")
async def save_user_settings(settings: UserSettings):
    """Save user settings"""
    save_settings(settings.model_dump())
    return {"success": True, "settings": settings.model_dump()}


@router.post("/reset")
async def reset_settings():
    """Reset settings to defaults"""
    settings = UserSettings().model_dump()
    save_settings(settings)
    return {"success": True, "settings": settings}
