INTENT: Build a SIMD-optimized hot-path cache for module capability lookups using fixed-size bloom filters with locality-preserving hash functions to eliminate allocation overhead in synthesis detection loops.

LANGUAGE: python

```python
import numpy as np
from typing import Optional

class HotModuleCache:
    """Zero-allocation capability cache. 8KB L1-friendly bloom + LRU array.
    Carmack wisdom: cache misses cost 200+ cycles. This costs <10."""
    
    __slots__ = ('_bloom', '_lru_keys', '_lru_vals', '_lru_idx', '_mask', '_k')
    
    def __init__(self, capacity: int = 64, bloom_bits: int = 4096):
        # Bloom: 4KB fits L1. Power-of-2 for bit-AND mask (no modulo div)
        self._mask = bloom_bits - 1
        self._bloom = np.zeros(bloom_bits >> 6, dtype=np.uint64)  # 64-bit chunks
        self._k = 3  # hash functions (optimal for 10% FP rate)
        
        # LRU: fixed arrays, circular buffer. No dict overhead (240 bytes/entry)
        self._lru_keys = np.zeros(capacity, dtype=np.uint64)  # hash(module_name)
        self._lru_vals = np.zeros(capacity, dtype=np.float32)  # invocation_score
        self._lru_idx = 0
    
    def _hash(self, key: str, seed: int) -> int:
        # FNV-1a variant. Prime multiply = CPU loves