"""
Indicator Cache
===============
LRU Cache with TTL for calculation results.
"""
import json
import hashlib
import threading
import time
from collections import OrderedDict
from typing import Optional, Dict, Any


class LRUCache:
    """Thread-safe LRU Cache with TTL"""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def _make_key(self, settings: dict) -> str:
        """Create hash key from settings (excluding force_recalculate)"""
        key_data = {k: v for k, v in sorted(settings.items()) if k != 'force_recalculate'}
        key_str = json.dumps(key_data, sort_keys=True, default=str)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, settings: dict) -> Optional[dict]:
        """Get cached result if exists and not expired"""
        key = self._make_key(settings)

        with self.lock:
            if key not in self.cache:
                self.misses += 1
                return None

            # Check TTL
            if time.time() - self.timestamps[key] > self.ttl_seconds:
                del self.cache[key]
                del self.timestamps[key]
                self.misses += 1
                return None

            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            return self.cache[key]

    def set(self, settings: dict, value: dict):
        """Store result in cache"""
        key = self._make_key(settings)

        with self.lock:
            # Remove oldest if at capacity
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]

            self.cache[key] = value
            self.timestamps[key] = time.time()

    def clear(self):
        """Clear all cached entries"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
            self.hits = 0
            self.misses = 0

    def stats(self) -> dict:
        """Get cache statistics"""
        with self.lock:
            total = self.hits + self.misses
            hit_rate = round((self.hits / total * 100) if total > 0 else 0, 1)
            return {
                "entries": len(self.cache),
                "max_size": self.max_size,
                "ttl_seconds": self.ttl_seconds,
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": hit_rate
            }


# Global cache instance
calculation_cache = LRUCache(max_size=100, ttl_seconds=300)
