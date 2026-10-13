"""
AUTOSYNTH Pattern Hash Verifier - Dijkstra Formal Correctness Module
Invariants: 
  I1: collision_count[h] = number of patterns with hash h
  I2: pattern_map[h] contains all patterns with hash h in insertion order
  I3: forall h: len(pattern_map[h]) == collision_count[h]
"""

class PatternHashVerifier:
    def __init__(self, hash_bits: int = 64):
        assert hash_bits > 0 and hash_bits <= 64, "Precondition: valid hash space"
        self.hash_bits = hash_bits
        self.collision_count: dict[int, int] = {}
        self.pattern_map: dict[int, list[str]] = {}
        self._verify_invariants()
    
    def _verify_invariants(self) -> None:
        """Assert loop invariants hold"""
        for h in self.collision_count:
            assert h in self.pattern_map, "I1-I2 coupling violated"
            assert len(self.pattern_map[h]) == self.collision_count[h], "I3 violated"
    
    def register_pattern(self, pattern: str, pattern_hash: int) -> tuple[bool, int]:
        """
        Register pattern with formal guarantees.
        Precondition: 0 <= pattern_hash < 2^hash_bits
        Postcondition: pattern in pattern_map[pattern_hash]
        Returns: (is_collision, collision_index)
        """
        assert 0 <= pattern_hash < (1 << self.hash_bits), "Precondition violated"
        
        if pattern_hash not in self.collision_count:
            self.collision_count[pattern_hash] = 0
            self.pattern_map[pattern_hash] = []
        
        # O(1) collision detection via count check
        is_collision = self.collision_count[pattern_hash] > 0
        collision_index = self.collision_count[pattern_hash]
        
        # Register with provable uniqueness within hash bucket
        if pattern not in self.pattern_map[pattern_hash]:
            self.pattern_map[pattern_hash].append(pattern)
            self.collision_count[pattern_hash] += 1
        
        self._verify_invariants()
        assert pattern in self.pattern_map[pattern_hash], "Postcondition violated"
        
        return (is_collision, collision_index)
    
    def get_collision_metrics(self) -> dict[str, int]:
        """Return provably correct collision statistics"""
        self._verify_invariants()
        total_patterns = sum(self.collision_count.values())
        colliding_hashes = sum(1 for c in self.collision_count.values() if c > 1)
        
        return {
            "total_patterns": total_patterns,
            "unique_hashes": len(self.collision_count),
            "colliding_hashes": colliding_hashes,
            "max_bucket_size": max(self.collision_count.values()) if self.collision_count else 0
        }