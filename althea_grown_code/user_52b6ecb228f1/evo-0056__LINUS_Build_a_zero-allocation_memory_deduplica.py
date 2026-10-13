import hashlib
from collections import deque
from typing import Optional

class MemoryDedup:
    """Zero-copy deduplication filter using rolling hash window."""
    
    __slots__ = ('_hashes', '_window', '_capacity', '_hits', '_misses')
    
    def __init__(self, capacity: int = 256):
        self._hashes = {}  # hash -> count
        self._window = deque(maxlen=capacity)
        self._capacity = capacity
        self._hits = 0
        self._misses = 0
    
    def _hash(self, content: str) -> int:
        """FNV-1a hash - fast, non-crypto."""
        h = 2166136261
        for byte in content.encode('utf-8'):
            h ^= byte
            h = (h * 16777619) & 0xffffffff
        return h
    
    def check(self, content: str) -> bool:
        """Returns True if content is novel (should be stored)."""
        h = self._hash(content)
        
        if h in self._hashes:
            self._hits += 1
            self._hashes[h] += 1
            return False
        
        self._misses += 1
        self._hashes[h] = 1
        self._window.append(h)
        
        # Evict oldest if at capacity
        if len(self._window) == self._capacity:
            oldest = self._window[0]
            self._hashes[oldest] -= 1
            if self._hashes[oldest] == 0:
                del self._hashes[oldest]
        
        return True
    
    def stats(self) -> dict:
        """Return hit rate and memory pressure."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0.0
        return {
            'hit_rate': hit_rate,
            'unique_entries': len(self._hashes),
            'capacity_used': len(self._window) / self._capacity,
            'total_queries': total
        }
    
    def should_consolidate(self) -> bool:
        """Signal when redundancy exceeds 40%."""
        total = self._hits + self._misses
        return total > 20 and (self._hits / total) > 0.4

# Global instance
_dedup = MemoryDedup(capacity=128)

def filter_growth(operation: str) -> Optional[str]:
    """Returns operation if novel, None if duplicate."""
    return operation if _dedup.check(operation) else None

def get_dedup_stats() -> dict:
    return _dedup.stats()

def consolidation_warning() -> bool:
    return _dedup.should_consolidate()