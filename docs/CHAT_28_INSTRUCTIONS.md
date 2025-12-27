# Chat #28 — Presets Architecture

> **Phase:** 3 — Preset System  
> **Previous:** #27 Dominant UI + Backend Integration ✅  
> **Next:** #29 Presets TRG Generator

---

## 🎯 GOAL

Create a unified preset architecture that supports both TRG and Dominant indicators with proper validation, registry, and extensibility for future indicators.

---

## 📋 TASKS

- [ ] Create `backend/app/presets/base.py` — BasePreset abstract class
- [ ] Create `backend/app/presets/registry.py` — PresetRegistry singleton
- [ ] Create `backend/app/presets/trg_preset.py` — TRG preset implementation
- [ ] Create `backend/app/presets/dominant_preset.py` — Dominant preset wrapper
- [ ] Add JSON schema validation for preset configs
- [ ] Create unit tests for preset operations
- [ ] Update `preset_routes.py` to use new architecture

---

## 📁 NEW FILES

```
backend/app/presets/
├── __init__.py
├── base.py              # BasePreset abstract class
├── registry.py          # PresetRegistry singleton
├── trg_preset.py        # TRG preset implementation
├── dominant_preset.py   # Dominant preset wrapper
└── validators.py        # JSON schema validation
```

---

## 🏗️ ARCHITECTURE

### BasePreset Abstract Class

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel

class BasePreset(ABC):
    """Abstract base class for all indicator presets"""
    
    @property
    @abstractmethod
    def indicator_type(self) -> str:
        """Return indicator type: 'trg' or 'dominant'"""
        pass
    
    @property
    @abstractmethod
    def id(self) -> str:
        """Unique preset identifier"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable preset name"""
        pass
    
    @abstractmethod
    def get_params(self) -> Dict[str, Any]:
        """Return all parameters as dictionary"""
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate preset configuration"""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage"""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BasePreset':
        """Deserialize from dictionary"""
        pass
```

### PresetRegistry

```python
class PresetRegistry:
    """Singleton registry for all preset types"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._presets = {}
            cls._instance._types = {}
        return cls._instance
    
    def register_type(self, indicator_type: str, preset_class: type):
        """Register a preset class for an indicator type"""
        pass
    
    def create(self, indicator_type: str, **kwargs) -> BasePreset:
        """Factory method to create preset"""
        pass
    
    def get(self, preset_id: str) -> Optional[BasePreset]:
        """Get preset by ID"""
        pass
    
    def list(self, indicator_type: str = None) -> List[BasePreset]:
        """List all presets, optionally filtered by type"""
        pass
```

---

## ✅ ACCEPTANCE CRITERIA

1. BasePreset is properly abstract and extendable
2. TRGPreset implements all abstract methods
3. DominantPreset wraps existing preset data
4. PresetRegistry can create/get/list presets
5. JSON validation catches invalid configs
6. Unit tests pass for all operations
7. Existing functionality preserved

---

## 📝 GIT COMMIT

```
feat(presets): add unified preset architecture

- Create BasePreset abstract class
- Create PresetRegistry singleton
- Implement TRGPreset and DominantPreset
- Add JSON schema validation
- Add unit tests

Chat #28: Presets Architecture
```

---

**Next chat:** #29 — Presets TRG Generator
