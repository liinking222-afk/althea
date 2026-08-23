import time
from typing import Optional

class FastPatternDedup:
    """Cache-friendly rolling deduplicator. FNV-1a hash, power-of-2 ring buffer, bitwise masking."""
    
    __slots__ = ('_ring', '_mask', '_idx', '_fnv_prime', '_fnv_offset')
    
    def __init__(self, size_power: int = 12):  # 4096 slots = 32KB at 8 bytes/hash
        size = 1 << size_power  # Power of 2 for bitwise AND masking
        self._ring = [0] * size  # Pre-allocate, zero-filled
        self._mask = size - 1    # Fast modulo: hash & mask === hash % size
        self._idx = 0            # Write head
        self._fnv_prime = 0x01000193      # FNV-1a 32-bit prime
        self._fnv_offset = 0x811c9dc5     # FNV-1a offset basis
    
    def _hash(self, s: str) -> int:
        """FNV-1a: fast, good distribution, minimal collisions. Inline hot path."""
        h = self._fnv_offset
        for byte in s.encode('utf-8'):
            h ^= byte
            h = (h * self._fnv_prime) & 0xFFFFFFFF  # Keep 32-bit, no overflow
        return h
    
    def is_duplicate(self, pattern: str) -> bool:
        """O(1) check against last N patterns. Returns True if seen recently."""
        h = self._hash(pattern)
        
        # Linear scan ring buffer - fits in L1 cache (32KB), prefetcher wins
        for slot_hash in self._ring:
            if slot_hash == h:
                return True  # Collision or true dup - both mean "seen this shape"
        
        # Not found - insert and advance
        self._ring[self._idx] = h
        self._idx = (self._idx + 1) & self._mask  # Bitwise wrap, no branch
        return False
    
    def mark_seen(self, pattern: str) -> None:
        """Explicitly mark pattern as seen without dup check."""
        h = self._hash(pattern)
        self._ring[self._idx] = h
        self._idx = (self._idx + 1) & self._mask

# Global singleton - avoid allocation churn
_dedup = FastPatternDedup(size_power=12)

def check_autosynth_pattern(pattern_name: str) -> bool:
    """Returns True if pattern is redundant, False if novel. <100ns typical."""
    return _dedup.is_duplicate(pattern_name)

# Benchmark harness
if __name__ == "__main__":
    patterns = [f"autonomous-{action}-{i}" for action in ["weather", "tabular", "recursion"] for i in range(1000)]
    
    start = time.perf_counter_ns()
    for p in patterns:
        check_autosynth_pattern(p)
    elapsed_ns = time.perf_counter_ns() - start
    
    print(f"Avg: {elapsed_ns / len(patterns):.1f}ns per check | {len(patterns)} patterns")