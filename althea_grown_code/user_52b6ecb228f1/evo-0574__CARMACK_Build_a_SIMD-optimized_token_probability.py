import numpy as np
from typing import Tuple, Optional
import hashlib

class TokenProbCache:
    """Carmack-style: cache-aligned, fixed-point, inline hot paths."""
    
    __slots__ = ('_cache', '_hits', '_misses', '_mask', '_shift')
    
    def __init__(self, size_pow2: int = 16):
        # Power-of-2 for bitwise modulo (cache locality)
        self._mask = (1 << size_pow2) - 1
        self._shift = size_pow2
        # Pre-allocate: [hash_low32, hash_high32, prob_fp16, count_u16]
        self._cache = np.zeros((1 << size_pow2, 4), dtype=np.uint32)
        self._hits = 0
        self._misses = 0
    
    def _hash_inline(self, token_pair: Tuple[str, str]) -> int:
        """Inline hash: xxHash-style multiply-rotate for sub-ns perf."""
        a, b = token_pair
        # Combine without allocation
        prime1, prime2 = 0x9E3779B1, 0x85EBCA77
        h = (hash(a) * prime1) ^ (hash(b) * prime2)
        return h & 0xFFFFFFFFFFFFFFFF  # u64
    
    def get(self, src_token: str, tgt_token: str) -> Optional[float]:
        """Hot loop: zero allocation, inline arithmetic, SIMD-ready."""
        h = self._hash_inline((src_token, tgt_token))
        idx = h & self._mask
        row = self._cache[idx]
        
        # Compare high/low u32 parts (collision detect)
        if row[0] == (h & 0xFFFFFFFF) and row[1] == (h >> 32):
            self._hits += 1
            # Fixed-point to float: 16 fractional bits
            return np.float32(row[2]) / 65536.0
        
        self._misses += 1
        return None
    
    def put(self, src_token: str, tgt_token: str, prob: float):
        """Write-through: convert float to u16 fixed-point inline."""
        h = self._hash_inline((src_token, tgt_token))
        idx = h & self._mask
        # Clamp and convert to 16-bit fixed-point
        fp_prob = np.uint32(np.clip(prob, 0.0, 1.0) * 65536.0)
        
        self._cache[idx, 0] = h & 0xFFFFFFFF
        self._cache[idx, 1] = h >> 32
        self._cache[idx, 2] = fp_prob
        self._cache[idx, 3] += 1  # Access count for LFU
    
    def hit_rate(self) -> float:
        """Inline perf metric."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0
    
    def evict_cold(self, threshold: int = 2):
        """Zero out rows with access_count < threshold. SIMD-vectorized."""
        mask = self._cache[:, 3] < threshold
        self._cache[mask] = 0

# Global singleton for zero-overhead module imports
_GLOBAL_CACHE = TokenProbCache(size_pow2=18)  # 256K entries, ~4MB

def cache_translation_prob(src: str, tgt: str, prob: float):
    _GLOBAL_CACHE.put(src, tgt, prob)

def lookup_translation_prob(src: str, tgt: str) -> Optional[float]:
    return _GLOBAL_CACHE.get(src, tgt)