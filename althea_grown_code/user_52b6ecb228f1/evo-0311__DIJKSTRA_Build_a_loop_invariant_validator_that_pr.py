#!/usr/bin/env python3
"""Loop Invariant Validator for Memory Operations - Dijkstra Style"""

from dataclasses import dataclass
from typing import Callable, Any, List, Tuple
from hashlib import sha256


@dataclass(frozen=True)
class Invariant:
    """A provable property that must hold throughout execution."""
    name: str
    predicate: Callable[[Any], bool]
    
    def holds(self, state: Any) -> bool:
        """Check if invariant holds. Fail-fast on violation."""
        result = self.predicate(state)
        assert result, f"INVARIANT VIOLATED: {self.name}"
        return result


@dataclass
class MemoryState:
    """Precise state representation for memory operations."""
    traces: List[dict]
    semantic_hash: str
    
    def compute_hash(self) -> str:
        """Canonical semantic fingerprint."""
        content = str(sorted(
            (k, v) for t in self.traces 
            for k, v in sorted(t.items()) if k != 'timestamp'
        ))
        return sha256(content.encode()).hexdigest()


def coalesce_with_proof(
    initial: MemoryState,
    merge_fn: Callable[[List[dict]], List[dict]],
    invariants: List[Invariant]
) -> Tuple[MemoryState, List[str]]:
    """
    Execute memory coalescing with formal correctness proof.
    Returns (final_state, proof_steps).
    """
    proof = []
    
    # PRE: Establish initial invariants
    proof.append(f"PRE: |traces|={len(initial.traces)}, hash={initial.semantic_hash[:8]}")
    for inv in invariants:
        inv.holds(initial)
    
    # TRANSFORM: Apply operation
    merged_traces = merge_fn(initial.traces)
    final = MemoryState(merged_traces, initial.compute_hash())
    proof.append(f"TRANSFORM: |traces|={len(initial.traces)}→{len(merged_traces)}")
    
    # INVARIANT: Semantic identity preserved
    assert final.compute_hash() == initial.semantic_hash, "Semantic drift detected"
    proof.append(f"INVARIANT: semantic_hash unchanged")
    
    # POST: All invariants still hold
    for inv in invariants:
        inv.holds(final)
    proof.append(f"POST: {len(invariants)} invariants proven")
    
    return final, proof


# Dijkstra maxim: specification determines implementation
COALESCENCE_INVARIANTS = [
    Invariant("non_empty", lambda s: len(s.traces) > 0),
    Invariant("semantic_preserved", lambda s: s.compute_hash() == s.semantic_hash),
]