# Chat #28 — Presets Architecture

> **Phase:** 3 — Preset System  
> **Previous:** #27 Dominant UI Integration ✅  
> **Next:** #29 QA Checkpoint #3

---

## 🎯 GOAL

Create unified preset architecture supporting both TRG and Dominant indicators with base classes, registry, and validation.

---

## 📋 TASKS

### 1. Base Preset Class
- [ ] Create `presets/base.py` with BasePreset abstract class
- [ ] Define common fields: id, name, indicator_type, params, category
- [ ] Add validation methods
- [ ] Add serialization to/from dict/JSON

### 2. Preset Registry
- [ ] Create `presets/registry.py` for preset management
- [ ] Singleton pattern for global access
- [ ] Methods: register, get, list, filter
- [ ] Support for system and user presets

### 3. TRG Preset Class
- [ ] Create TRGPreset extending BasePreset
- [ ] Params: i1, i2, tp_count, tp_percents, sl_percent, sl_mode
- [ ] Filters: supertrend, rsi, adx, volume

### 4. Dominant Preset Class
- [ ] Create DominantPreset extending BasePreset
- [ ] Params: sensitivity, filter_type, sl_mode
- [ ] TPs: 4 levels with Fibonacci

### 5. JSON Schema Validation
- [ ] Create JSON schemas for TRG and Dominant
- [ ] Validate on create/update
- [ ] Error messages for invalid data

### 6. Unit Tests
- [ ] Test preset creation
- [ ] Test serialization
- [ ] Test validation
- [ ] Test registry operations

---

## 📂 FILES TO CREATE

```
backend/app/
├── presets/
│   ├── __init__.py           # Module init
│   ├── base.py               # BasePreset class
│   ├── registry.py           # PresetRegistry singleton
│   ├── trg_preset.py         # TRGPreset class
│   ├── dominant_preset.py    # DominantPreset class
│   └── schemas/
│       ├── trg_schema.json   # TRG validation schema
│       └── dominant_schema.json # Dominant validation schema
│
tests/
└── test_presets.py           # Unit tests
```

---

## 📝 BASE PRESET STRUCTURE

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class BasePreset(ABC):
    id: str
    name: str
    indicator_type: str  # 'trg' or 'dominant'
    category: str        # scalp, short-term, mid-term, long-term
    params: Dict[str, Any]
    description: Optional[str] = None
    symbol: Optional[str] = None
    timeframe: Optional[str] = None
    source: str = 'user'  # system, user, imported
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    @abstractmethod
    def validate(self) -> bool:
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BasePreset':
        pass
```

---

## 🔧 GIT COMMIT

```
feat(presets): add unified preset architecture

- Create BasePreset abstract class
- Create PresetRegistry singleton
- Add TRGPreset and DominantPreset classes
- Add JSON schema validation
- Unit tests for preset operations

Chat #28: Presets Architecture
```

---

**Next chat:** #29 — QA Checkpoint #3
