#!/usr/bin/env python3
import hashlib
import time
from collections import defaultdict

class MemoryDedup:
    """Linus-style: simple hash table, no fancy trees. Data structure IS the algorithm."""
    
    def __init__(self, prefix_len=60):
        self.prefix_len = prefix_len
        self.seen = {}  # prefix_hash -> (full_entry, timestamp, count)
        self.stats = defaultdict(int)
    
    def _prefix_hash(self, entry: str) -> str:
        """Fast prefix hash. No crypto overhead, just collision resistance."""
        prefix = entry[:self.prefix_len].strip()
        return hashlib.blake2s(prefix.encode(), digest_size=8).hexdigest()
    
    def insert(self, entry: str) -> tuple[bool, str]:
        """Returns (should_store, reason). Single pass, no backtracking."""
        if not entry or len(entry) < 20:
            return True, "too_short"
        
        phash = self._prefix_hash(entry)
        now = time.time()
        
        if phash in self.seen:
            stored, ts, count = self.seen[phash]
            # Exact duplicate or close variant
            if entry == stored or entry.startswith(stored[:50]):
                self.seen[phash] = (stored, ts, count + 1)
                self.stats['dedup_hits'] += 1
                return False, f"duplicate_#{count + 1}"
            # Hash collision with different content - allow both
            self.stats['collisions'] += 1
        
        self.seen[phash] = (entry, now, 1)
        self.stats['unique_stored'] += 1
        return True, "unique"
    
    def prune_old(self, max_age_seconds=86400):
        """Remove entries older than threshold. Keep memory bounded."""
        now = time.time()
        pruned = 0
        for phash in list(self.seen.keys()):
            _, ts, _ = self.seen[phash]
            if now - ts > max_age_seconds:
                del self.seen[phash]
                pruned += 1
        self.stats['pruned'] += pruned
        return pruned
    
    def get_stats(self) -> dict:
        return dict(self.stats) | {'table_size': len(self.seen)}

# Global singleton - no ceremony
memory_dedup = MemoryDedup()