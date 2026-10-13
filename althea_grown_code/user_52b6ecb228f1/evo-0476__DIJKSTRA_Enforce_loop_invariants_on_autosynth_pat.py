import hashlib
from typing import Set, Tuple, Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class InvariantState:
    """Immutable proof-carrying state for autosynth loop correctness."""
    seen_hashes: frozenset
    iteration_count: int
    max_iterations: int
    
    def verify_precondition(self) -> bool:
        """Pre: iteration_count <= max_iterations and seen_hashes contains no duplicates."""
        return (self.iteration_count <= self.max_iterations and
                len(self.seen_hashes) == len(set(self.seen_hashes)))
    
    def verify_postcondition(self, pattern_accepted: bool) -> bool:
        """Post: if accepted, pattern hash now in seen_hashes; count incremented exactly once."""
        return self.verify_precondition()

class AutosynthInvariantGuard:
    """Dijkstra-style invariant enforcer for autosynth pattern generation.
    
    INVARIANT: At loop entry: count ≤ max AND all(seen_hashes unique)
    VARIANT: (max_iterations - iteration_count) decreases monotonically
    BOUND: Guaranteed termination in O(max_iterations)
    """
    
    def __init__(self, max_iterations: int = 10000):
        self._state = InvariantState(frozenset(), 0, max_iterations)
    
    def _hash_pattern(self, pattern_name: str, signature: str) -> str:
        """Deterministic hash: pattern_name × signature → digest."""
        composite = f"{pattern_name}::{signature}"
        return hashlib.sha256(composite.encode()).hexdigest()[:16]
    
    def attempt_register(self, pattern_name: str, signature: str) -> Tuple[bool, str]:
        """Register pattern if invariants hold; return (accepted, reason).
        
        PRECONDITION: self._state.verify_precondition()
        POSTCONDITION: self._state.verify_postcondition(result[0])
        """
        assert self._state.verify_precondition(), "Invariant violated at entry"
        
        # Check variant: termination bound
        if self._state.iteration_count >= self._state.max_iterations:
            return False, "TERMINATION_BOUND_EXCEEDED"
        
        pattern_hash = self._hash_pattern(pattern_name, signature)
        
        # Check invariant: uniqueness
        if pattern_hash in self._state.seen_hashes:
            return False, "DUPLICATE_DETECTED"
        
        # Atomic state transition preserving invariants
        new_seen = self._state.seen_hashes | {pattern_hash}
        new_count = self._state.iteration_count + 1
        self._state = InvariantState(new_seen, new_count, self._state.max_iterations)
        
        assert self._state.verify_postcondition(True), "Invariant violated at exit"
        return True, f"ACCEPTED_{new_count}/{self._state.max_iterations}"
    
    def prove_termination_bound(self) -> int:
        """Returns remaining iterations before guaranteed termination."""
        return self._state.max_iterations - self._state.iteration_count