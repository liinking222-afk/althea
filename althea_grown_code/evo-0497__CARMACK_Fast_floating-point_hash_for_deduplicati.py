import struct
from typing import Optional

class FastMemoryHash:
    """FNV-1a hash optimized for memory entry deduplication.
    Inline aggressively. Cache-friendly. Sub-microsecond target."""
    
    __slots__ = ('_cache', '_fnv_prime', '_fnv_offset')  # Cache locality
    
    def __init__(self):
        self._fnv_prime = 0x01000193  # 32-bit FNV prime
        self._fnv_offset = 0x811c9dc5  # 32-bit FNV offset basis
        self._cache: dict[int, str] = {}  # Hot path: int keys only
    
    def hash_entry(self, prefix: str, content: str) -> int:
        """FNV-1a hash with prefix weighting. Returns 32-bit int."""
        h = self._fnv_offset
        
        # Inline prefix processing - weight prefix 2x for collision resistance
        for byte in prefix.encode('utf-8'):
            h ^= byte
            h = (h * self._fnv_prime) & 0xFFFFFFFF
            h ^= byte  # Double-pass prefix
            h = (h * self._fnv_prime) & 0xFFFFFFFF
        
        # Content processing - single pass
        for byte in content.encode('utf-8')[:512]:  # Cap at 512 bytes for speed
            h ^= byte
            h = (h * self._fnv_prime) & 0xFFFFFFFF
        
        return h
    
    def is_duplicate(self, prefix: str, content: str) -> bool:
        """Hot path: O(1) duplicate check. No allocation."""
        h = self.hash_entry(prefix, content)
        
        # Cache lookup - single comparison in hot path
        if h in self._cache:
            return self._cache[h] == prefix  # Collision check
        
        self._cache[h] = prefix
        return False
    
    def register(self, prefix: str, content: str) -> int:
        """Register entry, return hash. Use for write-time dedup."""
        h = self.hash_entry(prefix, content)
        self._cache[h] = prefix
        return h
    
    def clear_cache(self) -> None:
        """Flush cache. Call periodically to prevent unbounded growth."""
        self._cache.clear()
    
    def size(self) -> int:
        """Cache size for monitoring."""
        return len(self._cache)

# Global instance for zero-overhead access
_global_hasher = FastMemoryHash()

def deduplicate_memory_entry(prefix: str, content: str) -> bool:
    """Returns True if duplicate (skip write). Inline wrapper for hot path."""
    return _global_hasher.is_duplicate(prefix, content)