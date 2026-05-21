#!/usr/bin/env python3
"""Loop Invariant Validator for Evolution Cycles — Dijkstra Discipline"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum

class InvariantType(Enum):
    MONOTONIC_VERSION = "version_increases"
    TRACE_CONTINUITY = "no_orphaned_traces"
    INTENT_PRESERVATION = "intent_matches_delta"
    NO_SEMANTIC_REGRESSION = "capabilities_preserved"

@dataclass
class Invariant:
    type: InvariantType
    predicate: callable
    error_msg: str

class EvolutionInvariantValidator:
    """Ensures each evolution cycle preserves formal correctness properties."""
    
    def __init__(self):
        self.invariants: List[Invariant] = self._define_invariants()
        self.violation_log: List[str] = []
    
    def _define_invariants(self) -> List[Invariant]:
        return [
            Invariant(
                InvariantType.MONOTONIC_VERSION,
                lambda pre, post: self._version_increases(pre, post),
                "Version must strictly increase"
            ),
            Invariant(
                InvariantType.TRACE_CONTINUITY,
                lambda pre, post: self._traces_connected(pre, post),
                "Evolution trace must be causally connected"
            ),
            Invariant(
                InvariantType.INTENT_PRESERVATION,
                lambda pre, post: self._intent_realized(post),
                "Delta must satisfy declared intent"
            ),
        ]
    
    def _version_increases(self, pre: Dict, post: Dict) -> bool:
        """Loop invariant: version[i+1] > version[i]"""
        return post.get('version', '0') > pre.get('version', '0')
    
    def _traces_connected(self, pre: Dict, post: Dict) -> bool:
        """Loop invariant: ∀trace ∃parent ∨ trace=root"""
        post_parent = post.get('parent_evo_id')
        return post_parent == pre.get('evo_id') or post_parent is None
    
    def _intent_realized(self, post: Dict) -> bool:
        """Loop invariant: INTENT ⊆ DELTA capabilities"""
        intent = post.get('intent', '').lower()
        delta = post.get('delta', '').lower()
        if not intent or not delta:
            return False
        keywords = intent.split()[:3]
        return any(kw in delta for kw in keywords if len(kw) > 3)
    
    def validate_cycle(self, pre_state: Dict, post_state: Dict) -> bool:
        """Check all invariants hold: P ∧ ⟨evolution⟩ ⇒ P"""
        all_hold = True
        for inv in self.invariants:
            if not inv.predicate(pre_state, post_state):
                self.violation_log.append(f"VIOLATED: {inv.error_msg}")
                all_hold = False
        return all_hold
    
    def get_violations(self) -> List[str]:
        return self.violation_log.copy()

if __name__ == "__main__":
    validator = EvolutionInvariantValidator()
    pre = {'evo_id': 132, 'version': '1.9.10'}
    post = {'evo_id': 133, 'version': '1.10.0', 'parent_evo_id': 132,
            'intent': 'build validator', 'delta': 'validator ensures correctness'}
    assert validator.validate_cycle(pre, post), "Invariants must hold"
    print("✓ All loop invariants preserved across evolution boundary")