import hashlib
import re
from difflib import SequenceMatcher
from typing import List, Dict, Set

class MemoryDeduplicator:
    """WOZ-style: Every memory slot counts. Squeeze redundancy out."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.threshold = similarity_threshold
        self.seen_hashes: Set[str] = set()
        self.canonical_memories: Dict[str, str] = {}
    
    def _normalize(self, text: str) -> str:
        """Strip noise: whitespace, punctuation variance, common prefixes."""
        text = re.sub(r'\s+', ' ', text.lower().strip())
        text = re.sub(r'^[\[\(].*?[\]\)]\s*', '', text)  # Remove prefixes
        text = re.sub(r'[^\w\s-]', '', text)
        return text
    
    def _fast_hash(self, text: str) -> str:
        """Quick hash for exact duplicate detection."""
        return hashlib.md5(self._normalize(text).encode()).hexdigest()[:12]
    
    def _similarity(self, a: str, b: str) -> float:
        """Compute text similarity ratio."""
        return SequenceMatcher(None, 
                              self._normalize(a), 
                              self._normalize(b)).ratio()
    
    def should_store(self, memory: str) -> tuple[bool, str]:
        """Returns (should_store, reason)."""
        fast_hash = self._fast_hash(memory)
        
        # Exact duplicate check (fast path)
        if fast_hash in self.seen_hashes:
            return False, "exact_duplicate"
        
        # Fuzzy duplicate check (slower, but only against canonicals)
        norm = self._normalize(memory)
        for canon_hash, canon_text in self.canonical_memories.items():
            if self._similarity(memory, canon_text) >= self.threshold:
                return False, f"similar_to_{canon_hash}"
        
        # Store as new canonical
        self.seen_hashes.add(fast_hash)
        self.canonical_memories[fast_hash] = memory
        return True, "unique"
    
    def filter_batch(self, memories: List[str]) -> List[str]:
        """Filter a batch, returning only unique memories."""
        unique = []
        for mem in memories:
            if self.should_store(mem)[0]:
                unique.append(mem)
        return unique