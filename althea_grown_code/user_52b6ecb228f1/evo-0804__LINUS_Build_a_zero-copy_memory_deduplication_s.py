import hashlib
import struct
from collections import defaultdict
from typing import List, Tuple, Set

class MemoryDedupScanner:
    """Kernel-level memory dedup: bloom filter + fnv1a hashing, no abstraction tax"""
    
    def __init__(self, bloom_size: int = 8192):
        self.bloom = bytearray(bloom_size)
        self.bloom_size = bloom_size
        self.pattern_hashes = defaultdict(list)  # hash -> [(idx, fingerprint)]
        
    def _fnv1a(self, data: bytes) -> int:
        """FNV-1a: fast, non-crypto hash"""
        h = 0x811c9dc5
        for b in data:
            h = ((h ^ b) * 0x01000193) & 0xffffffff
        return h
    
    def _bloom_add(self, h: int):
        """Set bits at hash positions"""
        for i in range(3):
            pos = (h + i * 0x9e3779b9) % (self.bloom_size * 8)
            self.bloom[pos >> 3] |= (1 << (pos & 7))
    
    def _bloom_check(self, h: int) -> bool:
        """Check if all bits set (probable member)"""
        for i in range(3):
            pos = (h + i * 0x9e3779b9) % (self.bloom_size * 8)
            if not (self.bloom[pos >> 3] & (1 << (pos & 7))):
                return False
        return True
    
    def fingerprint(self, pattern: str) -> Tuple[int, bytes]:
        """Generate hash and short fingerprint"""
        b = pattern.encode('utf-8')
        h = self._fnv1a(b)
        fp = hashlib.blake2b(b, digest_size=16).digest()
        return h, fp
    
    def scan(self, patterns: List[str]) -> dict:
        """Scan patterns, return dedup metrics"""
        total = len(patterns)
        duplicates = []
        bloom_hits = 0
        
        for idx, pattern in enumerate(patterns):
            h, fp = self.fingerprint(pattern)
            
            if self._bloom_check(h):
                bloom_hits += 1
                # Verify with fingerprint
                for other_idx, other_fp in self.pattern_hashes[h]:
                    if fp == other_fp:
                        duplicates.append((idx, other_idx, pattern))
                        break
            
            self._bloom_add(h)
            self.pattern_hashes[h].append((idx, fp))
        
        return {
            'total_patterns': total,
            'unique_hashes': len(self.pattern_hashes),
            'duplicates': len(duplicates),
            'duplication_ratio': len(duplicates) / total if total else 0,
            'bloom_hit_rate': bloom_hits / total if total else 0,
            'duplicate_pairs': duplicates[:10]  # Top 10
        }