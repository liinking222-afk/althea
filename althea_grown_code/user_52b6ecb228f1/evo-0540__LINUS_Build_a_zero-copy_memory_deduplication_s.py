import hashlib
import re
from collections import defaultdict
from typing import List, Tuple, Dict

class MemoryDeduplicator:
    """Linus-style: data structure first, algorithm emerges."""
    
    def __init__(self):
        self.hash_table: Dict[str, List[str]] = defaultdict(list)
        self.pattern_cache: Dict[str, int] = {}
    
    def hash_entry(self, entry: str) -> str:
        """Content-addressable hash of normalized entry."""
        normalized = re.sub(r'\d{4,}', 'N', entry)
        normalized = re.sub(r'v\d+\.\d+\.\d+', 'vX.X.X', normalized)
        return hashlib.blake2b(normalized.encode(), digest_size=16).hexdigest()
    
    def extract_pattern(self, entry: str) -> str:
        """Extract semantic pattern from entry."""
        match = re.search(r'/autonomous-([a-z-]+)-\d+', entry)
        if match:
            return match.group(1)
        match = re.search(r'\[(\w+) (?:/|#)', entry)
        return match.group(1) if match else 'unknown'
    
    def scan(self, memory_stream: List[str]) -> Dict[str, any]:
        """Single pass through memory. O(n) time, O(k) space where k=unique."""
        for entry in memory_stream:
            h = self.hash_entry(entry)
            self.hash_table[h].append(entry)
            pattern = self.extract_pattern(entry)
            self.pattern_cache[pattern] = self.pattern_cache.get(pattern, 0) + 1
        
        duplicates = {h: entries for h, entries in self.hash_table.items() if len(entries) > 1}
        hot_patterns = {p: c for p, c in self.pattern_cache.items() if c >= 3}
        
        return {
            'duplicate_groups': len(duplicates),
            'duplicate_entries': sum(len(v) - 1 for v in duplicates.values()),
            'hot_patterns': hot_patterns,
            'compression_ratio': 1 - (len(self.hash_table) / max(len(memory_stream), 1)),
            'duplicates': duplicates
        }

def deduplicate_memory(entries: List[str]) -> Dict[str, any]:
    """Public interface: one function, one job."""
    deduper = MemoryDeduplicator()
    return deduper.scan(entries)