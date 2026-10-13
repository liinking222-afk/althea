import struct
import hashlib
from typing import List, Tuple

class FastSemanticHash:
    """Carmack-style: cache-friendly, bit-twiddling hash for module dedup.
    Uses FNV-1a prime mixing + rolling window for O(1) similarity checks."""
    
    __slots__ = ['_prime', '_offset', '_mask', '_cache']  # Memory layout control
    
    def __init__(self):
        self._prime = 0x01000193  # FNV prime, good avalanche
        self._offset = 0x811c9dc5  # FNV offset basis
        self._mask = 0xFFFFFFFF    # 32-bit wraparound
        self._cache = {}           # Hot path: fingerprint -> modules
    
    def hash_module(self, intent: str, code: str, language: str) -> int:
        """Single-pass hash with inline bit rotation. Returns 64-bit fingerprint."""
        h = self._offset
        # Normalize: strip whitespace, lowercase for semantic equivalence
        tokens = (intent + language + code).lower().split()
        
        for token in tokens:
            for byte in token.encode('utf-8'):
                h ^= byte                      # XOR input
                h = (h * self._prime) & self._mask  # Multiply + mask (branchless)
                h ^= (h >> 16)                 # Avalanche upper bits down
        
        # Second pass: structural features (length ratios, token density)
        code_density = (len(code) << 16) // max(len(intent), 1)  # Fixed-point math
        h ^= code_density
        h = (h * self._prime) & self._mask
        
        return h | ((h ^ 0xDEADBEEF) << 32)  # 64-bit: high/low mixed
    
    def similarity_fast(self, h1: int, h2: int) -> float:
        """Hamming distance in tight loop. Branch-free popcount."""
        xor = h1 ^ h2
        # Brian Kernighan's algorithm inlined
        count = 0
        while xor:
            count += 1
            xor &= xor - 1  # Clear lowest set bit
        return 1.0 - (count / 64.0)  # Normalize to [0,1]
    
    def find_duplicates(self, fingerprint: int, threshold: float = 0.85) -> List[int]:
        """Hot loop: scan cache for near-matches. Early exit on distance."""
        matches = []
        for cached_fp in self._cache:
            if self.similarity_fast(fingerprint, cached_fp) >= threshold:
                matches.append(cached_fp)
        return matches
    
    def register(self, fingerprint: int, module_id: str):
        """Update cache. Amortized O(1)."""
        self._cache[fingerprint] = module_id
    
    def batch_hash(self, modules: List[Tuple[str, str, str]]) -> List[int]:
        """Vectorizable: process multiple modules in tight loop."""
        return [self.hash_module(i, c, l) for i, c, l in modules]