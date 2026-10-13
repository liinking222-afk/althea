#!/usr/bin/env python3
import hashlib
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

@dataclass
class MemoryEntry:
    hash: str
    timestamp: float
    category: str

class MemoryDeduplicationKernel:
    """Linus-style: ring buffer + hash table. No abstraction layers."""
    
    def __init__(self, window_seconds: int = 3600, max_entries: int = 10000):
        self.window = window_seconds
        self.ring = deque(maxlen=max_entries)
        self.hashes = {}  # hash -> timestamp
        
    def _hash_memory(self, content: str, category: str) -> str:
        """FNV-1a style fast hash for memory content"""
        return hashlib.blake2s(
            f"{category}:{content}".encode(),
            digest_size=16
        ).hexdigest()
    
    def _prune_expired(self, now: float) -> None:
        """Single-pass prune from front of ring buffer"""
        cutoff = now - self.window
        while self.ring and self.ring[0].timestamp < cutoff:
            old = self.ring.popleft()
            if old.hash in self.hashes and self.hashes[old.hash] == old.timestamp:
                del self.hashes[old.hash]
    
    def is_duplicate(self, content: str, category: str) -> bool:
        """O(1) duplicate check with temporal awareness"""
        now = time.time()
        self._prune_expired(now)
        
        mem_hash = self._hash_memory(content, category)
        
        if mem_hash in self.hashes:
            return True
        
        entry = MemoryEntry(hash=mem_hash, timestamp=now, category=category)
        self.ring.append(entry)
        self.hashes[mem_hash] = now
        return False
    
    def should_fire_autosynth(self, pattern: str, description: str) -> bool:
        """Gate autosynth modules with dedup check"""
        content = f"{pattern}|{description}"
        return not self.is_duplicate(content, "AUTOSYNTH")
    
    def should_store_imagination(self, image_description: str) -> bool:
        """Gate imagined content with dedup check"""
        return not self.is_duplicate(image_description, "IMAGINED")

# Global kernel instance - monolithic design
dedup = MemoryDeduplicationKernel(window_seconds=3600, max_entries=10000)