import struct
from typing import Optional

class BatchMemoryDeduplicator:
    """Carmack-style: cache-aligned, branch-free, rolling hash dedup"""
    
    def __init__(self, window_size: int = 256):
        # Power-of-two for bitwise modulo, cache-line friendly
        self.window_size = window_size
        self.mask = window_size - 1
        # Pre-allocated: zero heap churn
        self.hashes = [0] * window_size  # Rolling window
        self.head = 0  # Write cursor
        # FNV-1a constants: prime for avalanche, offset for distribution
        self.FNV_PRIME = 0x01000193
        self.FNV_OFFSET = 0x811c9dc5
        
    def hash_pattern(self, pattern: str) -> int:
        """Inline FNV-1a: tight loop, no allocations, predictable branches"""
        h = self.FNV_OFFSET
        for byte in pattern.encode('utf-8'):
            h ^= byte  # XOR fold
            h = (h * self.FNV_PRIME) & 0xFFFFFFFF  # 32-bit wrap, multiply-shift
        return h
    
    def is_duplicate(self, pattern: str) -> bool:
        """Branch-free scan: linear cache access, no hash table overhead"""
        h = self.hash_pattern(pattern)
        
        # Unrolled scan: compiler can vectorize this
        # Check current window for match
        found = False
        for i in range(self.window_size):
            found |= (self.hashes[i] == h)
        
        if not found:
            # Insert: advance head with bitwise AND (no modulo)
            self.hashes[self.head] = h
            self.head = (self.head + 1) & self.mask
            return False
        
        return True
    
    def batch_filter(self, patterns: list[str]) -> list[str]:
        """Process multiple patterns: amortize loop overhead"""
        result = []
        for p in patterns:
            if not self.is_duplicate(p):
                result.append(p)
        return result

# Global singleton: avoid construction cost
_DEDUPLICATOR = BatchMemoryDeduplicator(256)

def should_trigger_autosynth(pattern: str) -> bool:
    """Hot path: inline candidate, sub-microsecond target"""
    return not _DEDUPLICATOR.is_duplicate(pattern)