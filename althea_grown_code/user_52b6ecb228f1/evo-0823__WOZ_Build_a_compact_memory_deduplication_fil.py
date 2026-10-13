import hashlib
import json
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class MemoryFingerprint:
    content_hash: str
    first_seen: str
    occurrence_count: int
    memory_type: str
    excerpt: str

class MemoryDeduplicator:
    """WOZ-inspired: Make every memory slot count. Squeeze efficiency from constraint."""
    
    def __init__(self, max_fingerprints: int = 10000):
        self.fingerprints: Dict[str, MemoryFingerprint] = {}
        self.max_fingerprints = max_fingerprints
        self.blocked_duplicates = 0
    
    def _hash_content(self, content: str) -> str:
        """Fast hash for content comparison"""
        normalized = ''.join(content.lower().split())
        return hashlib.blake2b(normalized.encode(), digest_size=16).hexdigest()
    
    def _extract_excerpt(self, content: str, max_len: int = 60) -> str:
        """Extract meaningful excerpt"""
        return content[:max_len] + "..." if len(content) > max_len else content
    
    def should_store(self, content: str, memory_type: str = "UNKNOWN") -> bool:
        """Returns True if content is novel enough to store"""
        content_hash = self._hash_content(content)
        
        if content_hash in self.fingerprints:
            fp = self.fingerprints[content_hash]
            fp.occurrence_count += 1
            self.blocked_duplicates += 1
            return False
        
        if len(self.fingerprints) >= self.max_fingerprints:
            self._evict_oldest()
        
        self.fingerprints[content_hash] = MemoryFingerprint(
            content_hash=content_hash,
            first_seen=datetime.utcnow().isoformat(),
            occurrence_count=1,
            memory_type=memory_type,
            excerpt=self._extract_excerpt(content)
        )
        return True
    
    def _evict_oldest(self):
        """LRU-style eviction of oldest fingerprint"""
        if not self.fingerprints:
            return
        oldest = min(self.fingerprints.items(), key=lambda x: x[1].first_seen)
        del self.fingerprints[oldest[0]]
    
    def get_stats(self) -> Dict:
        """Return deduplication statistics"""
        return {
            "unique_memories": len(self.fingerprints),
            "duplicates_blocked": self.blocked_duplicates,
            "efficiency_ratio": round(self.blocked_duplicates / max(1, len(self.fingerprints)), 2)
        }

deduplicator = MemoryDeduplicator()