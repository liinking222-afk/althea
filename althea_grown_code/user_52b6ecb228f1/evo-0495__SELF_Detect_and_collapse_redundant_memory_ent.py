import hashlib
from collections import defaultdict
from typing import List, Dict, Tuple

class MemoryDeduplicator:
    """Identifies and collapses duplicate memory fragments based on prefix similarity."""
    
    def __init__(self, prefix_threshold: int = 50):
        self.prefix_threshold = prefix_threshold
        self.collapse_map: Dict[str, List[str]] = defaultdict(list)
    
    def compute_prefix_hash(self, text: str, length: int) -> str:
        """Generate hash of text prefix for fast duplicate detection."""
        prefix = text[:length].strip()
        return hashlib.md5(prefix.encode()).hexdigest()
    
    def find_duplicates(self, memories: List[str]) -> Dict[str, List[int]]:
        """Find memory indices that share identical prefixes."""
        prefix_groups = defaultdict(list)
        
        for idx, memory in enumerate(memories):
            if len(memory) >= self.prefix_threshold:
                prefix_hash = self.compute_prefix_hash(memory, self.prefix_threshold)
                prefix_groups[prefix_hash].append(idx)
        
        return {h: indices for h, indices in prefix_groups.items() if len(indices) > 1}
    
    def collapse(self, memories: List[str]) -> Tuple[List[str], Dict[str, int]]:
        """Collapse duplicate memories and return deduplicated list with stats."""
        duplicates = self.find_duplicates(memories)
        
        if not duplicates:
            return memories, {"total": len(memories), "removed": 0, "groups": 0}
        
        keep_indices = set(range(len(memories)))
        removed_count = 0
        
        for prefix_hash, indices in duplicates.items():
            # Keep first occurrence, mark others for removal
            for idx in indices[1:]:
                keep_indices.discard(idx)
                removed_count += 1
        
        deduplicated = [mem for idx, mem in enumerate(memories) if idx in keep_indices]
        
        stats = {
            "total": len(memories),
            "removed": removed_count,
            "groups": len(duplicates),
            "final": len(deduplicated)
        }
        
        return deduplicated, stats
    
    def detect_and_report(self, memories: List[str]) -> Dict:
        """Analyze memory for duplication without modification."""
        duplicates = self.find_duplicates(memories)
        
        return {
            "duplicate_groups": len(duplicates),
            "affected_entries": sum(len(indices) - 1 for indices in duplicates.values()),
            "compression_ratio": 1 - (len(memories) - sum(len(indices) - 1 for indices in duplicates.values())) / len(memories) if memories else 0
        }