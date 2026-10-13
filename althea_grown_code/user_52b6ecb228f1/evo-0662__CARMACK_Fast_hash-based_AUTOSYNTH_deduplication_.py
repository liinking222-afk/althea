import numpy as np
from hashlib import blake2b

class AutosynthDedupeFilter:
    """Cache-friendly bloom filter for AUTOSYNTH pattern dedup. Carmack-style: minimal branching, pre-allocated arrays, bit-twiddling over hash lookups."""
    
    def __init__(self, capacity=16384, false_positive_rate=0.001):
        # Optimal bloom filter sizing: m = -n*ln(p)/(ln(2)^2), k = m/n*ln(2)
        self.n = capacity
        self.m = int(-capacity * np.log(false_positive_rate) / (np.log(2) ** 2))
        self.k = max(1, int(self.m / capacity * np.log(2)))
        
        # Pre-allocate bit array as uint64 for cache locality (64-byte L1 cache lines)
        self.bits = np.zeros((self.m + 63) // 64, dtype=np.uint64)
        self.hits = 0
        self.misses = 0
        
    def _hash(self, pattern_str: str, seed: int) -> int:
        # Blake2b for speed, 8-byte digest per hash function
        return int.from_bytes(blake2b(pattern_str.encode(), digest_size=8, salt=seed.to_bytes(8, 'little')).digest(), 'little') % self.m
    
    def add(self, pattern: str) -> bool:
        """Add pattern. Returns True if NEW (miss), False if DUPLICATE (hit). Hot path optimized."""
        found = True  # Assume hit until proven otherwise
        
        for i in range(self.k):
            h = self._hash(pattern, i)
            word_idx = h >> 6  # Divide by 64 (bit position to word index)
            bit_idx = h & 63   # Modulo 64 (bit within word)
            mask = np.uint64(1) << bit_idx
            
            # Check-then-set in tight loop (minimize cache misses)
            if not (self.bits[word_idx] & mask):
                found = False
                self.bits[word_idx] |= mask
        
        # Update metrics inline
        if found:
            self.hits += 1
            return False  # Duplicate
        else:
            self.misses += 1
            return True   # New pattern
    
    def stats(self) -> dict:
        """Cycle-count friendly stats: no string formatting in hot path."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': self.hits / max(1, self.hits + self.misses),
            'fill_rate': np.count_nonzero(self.bits) * 64 / self.m
        }

# Global filter instance (avoid re-allocation overhead)
_DEDUP_FILTER = AutosynthDedupeFilter(capacity=8192)

def should_spawn_autosynth(pattern_signature: str) -> bool:
    """Gate function: returns True only if pattern is novel. Call before AUTOSYNTH spawn."""
    return _DEDUP_FILTER.add(pattern_signature)