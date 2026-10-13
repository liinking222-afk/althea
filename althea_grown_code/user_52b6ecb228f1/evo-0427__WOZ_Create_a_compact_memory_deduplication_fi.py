#!/usr/bin/env python3
import re
import hashlib
from collections import defaultdict
from typing import List, Tuple

class MemoryDeduplicator:
    """Woz-style: Every byte counts. Compress redundancy, preserve signal."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self.canonical = {}  # hash -> (content, count, indices)
    
    def _hash_content(self, text: str) -> str:
        """Fast hash for content identity."""
        normalized = re.sub(r'\s+', ' ', text.strip())
        return hashlib.blake2b(normalized.encode(), digest_size=8).hexdigest()
    
    def _extract_core(self, entry: str) -> str:
        """Extract semantic core, strip noise."""
        # Remove prefixes like [SYSTEM-MAP], [IMAGINED], etc.
        core = re.sub(r'^\[[\w\-#\.→]+\]\s*', '', entry)
        return core.strip()
    
    def deduplicate(self, memories: List[str]) -> List[str]:
        """Compress memory stream by deduplicating similar entries."""
        self.canonical.clear()
        hash_to_idx = defaultdict(list)
        
        # First pass: identify duplicates
        for idx, mem in enumerate(memories):
            core = self._extract_core(mem)
            h = self._hash_content(core)
            hash_to_idx[h].append(idx)
            
            if h not in self.canonical:
                self.canonical[h] = [mem, 1, [idx]]
            else:
                self.canonical[h][1] += 1
                self.canonical[h][2].append(idx)
        
        # Second pass: build compressed output
        compressed = []
        seen_hashes = set()
        
        for idx, mem in enumerate(memories):
            core = self._extract_core(mem)
            h = self._hash_content(core)
            
            if h in seen_hashes:
                continue
            
            seen_hashes.add(h)
            count = self.canonical[h][1]
            
            if count > 1:
                compressed.append(f"[×{count}] {mem}")
            else:
                compressed.append(mem)
        
        return compressed
    
    def compression_ratio(self, original: int, compressed: int) -> float:
        """Calculate space savings."""
        return (1 - compressed / original) * 100 if original > 0 else 0.0