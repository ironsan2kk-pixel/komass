# Chat #37 — Filters Architecture

> **Phase:** 5 — Общие фильтры  
> **Previous:** #36 Score UI ✅  
> **Next:** #38 Filters Time

---

## 🎯 GOAL

Создать архитектуру модульной системы фильтров для бота:
- BaseFilter абстрактный класс
- FilterRegistry для регистрации фильтров
- FilterChain для цепочки фильтров
- Интерфейс can_trade(signal) -> bool

---

## 📋 TASKS

- [ ] `filters/base.py` — BaseFilter абстрактный класс
  - `name: str` — имя фильтра
  - `enabled: bool` — включён/выключен
  - `can_trade(signal, context) -> FilterResult` — основной метод
  - `get_config_schema() -> dict` — схема параметров
  - `validate_config(config) -> bool` — валидация
  
- [ ] `filters/registry.py` — FilterRegistry класс
  - `register(filter_class)` — регистрация фильтра
  - `get(name) -> FilterClass` — получение по имени
  - `list_all() -> List[str]` — список всех фильтров
  - `create(name, config) -> Filter` — создание экземпляра
  
- [ ] `filters/chain.py` — FilterChain класс
  - `add(filter)` — добавить фильтр
  - `remove(name)` — удалить фильтр
  - `apply(signal, context) -> ChainResult` — применить все
  - `get_rejections() -> List[str]` — причины отказа
  
- [ ] `filters/__init__.py` — экспорты модуля
- [ ] Unit тесты (20+ тестов)

---

## 📁 FILES

```
backend/app/filters/
├── __init__.py           # Module exports
├── base.py               # BaseFilter, FilterResult
├── registry.py           # FilterRegistry
└── chain.py              # FilterChain, ChainResult

tests/
└── test_filters_architecture.py
```

---

## 🔧 ARCHITECTURE

### FilterResult
```python
@dataclass
class FilterResult:
    allowed: bool           # True = signal allowed
    reason: Optional[str]   # Reason if blocked
    filter_name: str        # Which filter made decision
    details: dict           # Additional info
```

### BaseFilter
```python
class BaseFilter(ABC):
    name: str
    enabled: bool = True
    
    @abstractmethod
    def can_trade(self, signal: dict, context: dict) -> FilterResult:
        """Check if signal should be allowed"""
        pass
    
    @abstractmethod
    def get_config_schema(self) -> dict:
        """Return JSON schema for filter config"""
        pass
```

### FilterChain
```python
class FilterChain:
    def apply(self, signal: dict, context: dict) -> ChainResult:
        """Apply all filters in chain"""
        for filter in self.filters:
            if filter.enabled:
                result = filter.can_trade(signal, context)
                if not result.allowed:
                    return ChainResult(allowed=False, rejections=[result])
        return ChainResult(allowed=True, rejections=[])
```

---

## 📝 GIT COMMIT

```
feat: Add filters module architecture

- Add BaseFilter abstract class with can_trade interface
- Add FilterRegistry for filter management
- Add FilterChain for applying multiple filters
- Add FilterResult and ChainResult dataclasses
- Add JSON schema support for filter configs
- Add 20+ unit tests

Chat #37: Filters Architecture
```

---

**Next chat:** #38 — Filters Time
