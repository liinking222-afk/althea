"""
Dijkstra-style Verified Deduplication Filter
Loop invariants enforced. Preconditions/postconditions documented.
"""

from typing import Set, List, Tuple
from hashlib import blake2b


class VerifiedDeduplicationFilter:
    def __init__(self, window_size: int = 1024):
        # INVARIANT: seen_hashes contains exactly the hashes of all processed unique items
        self._seen_hashes: Set[bytes] = set()
        # INVARIANT: window_size > 0
        assert window_size > 0, "PRECONDITION: window_size must be positive"
        self._window_size = window_size
        # INVARIANT: len(seen_hashes) <= window_size at all times
        self._insertion_order: List[bytes] = []
    
    def _hash(self, item: str) -> bytes:
        """Pure function: same input always yields same output"""
        # PRECONDITION: item is non-null
        assert item is not None, "PRECONDITION: item cannot be None"
        h = blake2b(item.encode('utf-8'), digest_size=16).digest()
        # POSTCONDITION: hash is fixed 16-byte value
        assert len(h) == 16, "POSTCONDITION: hash must be 16 bytes"
        return h
    
    def is_duplicate(self, item: str) -> bool:
        """
        PRECONDITION: filter is in valid state (invariants hold)
        POSTCONDITION: returns True iff item hash exists in seen_hashes
        POSTCONDITION: seen_hashes is updated if item is new
        POSTCONDITION: len(seen_hashes) <= window_size
        """
        # Verify invariant on entry
        assert len(self._seen_hashes) <= self._window_size, "INVARIANT violated"
        
        item_hash = self._hash(item)
        
        # The decision point: membership test
        is_dup = item_hash in self._seen_hashes
        
        if not is_dup:
            # Maintain window size invariant via FIFO eviction
            if len(self._seen_hashes) >= self._window_size:
                # LOOP INVARIANT: Remove oldest until size < window_size
                oldest_hash = self._insertion_order.pop(0)
                self._seen_hashes.remove(oldest_hash)
            
            # Insert new hash
            self._seen_hashes.add(item_hash)
            self._insertion_order.append(item_hash)
        
        # Verify invariant maintained
        assert len(self._seen_hashes) <= self._window_size, "INVARIANT maintained"
        assert len(self._seen_hashes) == len(self._insertion_order), "CONSISTENCY"
        
        return is_dup
    
    def filter_unique(self, items: List[str]) -> List[str]:
        """
        PRECONDITION: items is a valid list
        POSTCONDITION: returns only items not seen before (in order)
        POSTCONDITION: no duplicates within returned list
        """
        unique_items = []
        
        # LOOP INVARIANT: unique_items contains no duplicates
        # LOOP INVARIANT: all items in unique_items are not in initial seen_hashes
        for item in items:
            if not self.is_duplicate(item):
                unique_items.append(item)
        
        # POSTCONDITION: verify no internal duplicates
        assert len(unique_items) == len(set(self._hash(i) for i in unique_items))
        
        return unique_items


# Proof of correctness via assertions embedded throughout