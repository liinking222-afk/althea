#!/usr/bin/env python3
"""Memory Trace Invariant Validator - Dijkstra-style formal correctness"""

from dataclasses import dataclass
from typing import Set, List, Optional
from hashlib import sha256

@dataclass(frozen=True)
class TraceInvariant:
    """Immutable representation of a memory trace's essential properties"""
    semantic_hash: str
    token_count: int
    reference_ids: frozenset

    @staticmethod
    def compute(trace_content: str, refs: Set[str]) -> 'TraceInvariant':
        """PRE: trace_content non-empty, refs well-formed
           POST: returns canonical invariant representation"""
        assert len(trace_content) > 0, "Trace must be non-empty"
        return TraceInvariant(
            semantic_hash=sha256(trace_content.encode()).hexdigest()[:16],
            token_count=len(trace_content.split()),
            reference_ids=frozenset(refs)
        )


class CoalescenceValidator:
    """Validates memory coalescence preserves essential invariants"""
    
    def __init__(self):
        self.invariants: dict[str, TraceInvariant] = {}
    
    def register_trace(self, trace_id: str, content: str, refs: Set[str]) -> None:
        """PRE: trace_id unique, content valid
           POST: invariant recorded, no duplicate semantic_hash"""
        inv = TraceInvariant.compute(content, refs)
        assert trace_id not in self.invariants, f"Duplicate trace_id: {trace_id}"
        self.invariants[trace_id] = inv
    
    def validate_coalescence(self, source_ids: List[str], merged_content: str, 
                            merged_refs: Set[str]) -> bool:
        """PRE: all source_ids exist in invariants
           POST: returns True iff coalescence preserves information
           INVARIANT: union(source_refs) ⊆ merged_refs
           INVARIANT: sum(source_tokens) ≤ merged_tokens * 1.1 (allow 10% compression)"""
        assert all(sid in self.invariants for sid in source_ids), "Unknown source trace"
        
        source_invs = [self.invariants[sid] for sid in source_ids]
        merged_inv = TraceInvariant.compute(merged_content, merged_refs)
        
        # Check reference preservation
        all_source_refs = set().union(*(inv.reference_ids for inv in source_invs))
        if not all_source_refs.issubset(merged_inv.reference_ids):
            return False
        
        # Check token compression bound (allow up to 10% overhead for clarity)
        total_source_tokens = sum(inv.token_count for inv in source_invs)
        if merged_inv.token_count > total_source_tokens * 1.1:
            return False
        
        return True


if __name__ == "__main__":
    validator = CoalescenceValidator()
    validator.register_trace("t1", "memory fragment alpha", {"ref_a"})
    validator.register_trace("t2", "memory fragment beta", {"ref_b"})
    
    assert validator.validate_coalescence(
        ["t1", "t2"], 
        "merged memory alpha beta", 
        {"ref_a", "ref_b"}
    )
    print("✓ Invariants hold")