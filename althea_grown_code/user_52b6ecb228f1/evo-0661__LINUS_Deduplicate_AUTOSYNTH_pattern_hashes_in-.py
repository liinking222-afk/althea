#!/usr/bin/env python3
import hashlib
import time
from collections import deque
from dataclasses import dataclass

@dataclass
class PatternHash:
    hash: str
    timestamp: float
    pattern: str

class AutosynthDeduplicator:
    """Kernel-level deduplication ring buffer. No ORM. No abstraction tax."""
    
    def __init__(self, window_size=1024, ttl_seconds=3600):
        self.ring = deque(maxlen=window_size)
        self.hash_index = {}  # hash -> PatternHash for O(1) lookup
        self.ttl = ttl_seconds
        self.stats = {"hits": 0, "misses": 0, "evictions": 0}
    
    def _hash_pattern(self, pattern_text: str) -> str:
        """Fast hash. Blake2b for speed over cryptographic strength."""
        return hashlib.blake2b(pattern_text.encode(), digest_size=16).hexdigest()
    
    def _evict_expired(self):
        """Scan from head, evict expired entries."""
        now = time.time()
        while self.ring and (now - self.ring[0].timestamp) > self.ttl:
            expired = self.ring.popleft()
            del self.hash_index[expired.hash]
            self.stats["evictions"] += 1
    
    def check_and_record(self, pattern_text: str) -> bool:
        """
        Returns True if pattern is NEW (should spawn).
        Returns False if pattern is DUPLICATE (suppress).
        """
        self._evict_expired()
        
        pattern_hash = self._hash_pattern(pattern_text)
        
        if pattern_hash in self.hash_index:
            self.stats["hits"] += 1
            # Update timestamp on hit (LRU-like behavior)
            self.hash_index[pattern_hash].timestamp = time.time()
            return False
        
        # New pattern
        self.stats["misses"] += 1
        entry = PatternHash(
            hash=pattern_hash,
            timestamp=time.time(),
            pattern=pattern_text[:64]  # Store prefix for debug only
        )
        self.ring.append(entry)
        self.hash_index[pattern_hash] = entry
        return True
    
    def get_stats(self) -> dict:
        return {
            **self.stats,
            "ring_size": len(self.ring),
            "hit_rate": self.stats["hits"] / max(1, self.stats["hits"] + self.stats["misses"])
        }

# Global singleton instance
_deduplicator = AutosynthDeduplicator(window_size=2048, ttl_seconds=7200)

def should_spawn_autosynth(pattern: str) -> bool:
    """Single function interface. Use this before creating AUTOSYNTH modules."""
    return _deduplicator.check_and_record(pattern)