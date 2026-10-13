import hashlib
from collections import deque

class MemoryFingerprintCache:
    """Zero-abstraction ring buffer for memory deduplication"""
    __slots__ = ('_ring', '_hashes', '_size', '_hits', '_misses')
    
    def __init__(self, size=1024):
        self._ring = deque(maxlen=size)
        self._hashes = {}  # hash -> (content, count, index)
        self._size = size
        self._hits = 0
        self._misses = 0
    
    @staticmethod
    def _fnv1a(data: bytes) -> int:
        """FNV-1a hash - fast, low collision"""
        h = 0x811c9dc5
        for b in data:
            h = ((h ^ b) * 0x01000193) & 0xffffffff
        return h
    
    def fingerprint(self, content: str) -> tuple[int, bool]:
        """Returns (hash, is_duplicate). Pure performance."""
        b = content.encode('utf-8', errors='ignore')
        h = self._fnv1a(b)
        
        if h in self._hashes:
            entry = self._hashes[h]
            self._hashes[h] = (entry[0], entry[1] + 1, entry[2])
            self._hits += 1
            return (h, True)
        
        if len(self._ring) >= self._size:
            evicted = self._ring[0]
            if evicted in self._hashes:
                del self._hashes[evicted]
        
        self._ring.append(h)
        self._hashes[h] = (content[:128], 1, len(self._ring) - 1)
        self._misses += 1
        return (h, False)
    
    def get_count(self, h: int) -> int:
        """Direct hash lookup, no indirection"""
        return self._hashes.get(h, (None, 0, None))[1]
    
    def stats(self) -> dict:
        """Raw counters for telemetry"""
        return {
            'size': len(self._ring),
            'unique': len(self._hashes),
            'hits': self._hits,
            'misses': self._misses,
            'hit_rate': self._hits / max(1, self._hits + self._misses)
        }
    
    def compress_memory_stream(self, memories: list[str]) -> list[tuple]:
        """Process stream, return (content, hash, is_dup, count)"""
        return [(m, *self.fingerprint(m), self.get_count(self.fingerprint(m)[0])) 
                for m in memories]

# Global instance - kernel pattern
_CACHE = MemoryFingerprintCache(2048)

def deduplicate(content: str) -> tuple[int, bool]:
    return _CACHE.fingerprint(content)

def memory_stats() -> dict:
    return _CACHE.stats()