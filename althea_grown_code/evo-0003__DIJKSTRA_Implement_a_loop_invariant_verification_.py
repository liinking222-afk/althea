#!/usr/bin/env python3
"""Loop Invariant Verifier for Cognitive Module State Transitions"""

from dataclasses import dataclass
from typing import Callable, Any, Optional
from enum import Enum

class InvariantStatus(Enum):
    HOLDS = "HOLDS"
    VIOLATED = "VIOLATED"
    UNKNOWN = "UNKNOWN"

@dataclass(frozen=True)
class Invariant:
    predicate: Callable[[Any], bool]
    description: str
    critical: bool = True

@dataclass(frozen=True)
class VerificationResult:
    invariant: Invariant
    status: InvariantStatus
    state_snapshot: Any
    cycle_index: int

class LoopInvariantVerifier:
    def __init__(self):
        self._invariants: list[Invariant] = []
        self._cycle_count: int = 0
        
    def register(self, predicate: Callable[[Any], bool], desc: str, critical: bool = True) -> None:
        """Register an invariant that must hold across all evolution cycles."""
        self._invariants.append(Invariant(predicate, desc, critical))
    
    def verify_state(self, state: Any) -> list[VerificationResult]:
        """Verify all registered invariants hold for current state."""
        results = []
        for inv in self._invariants:
            try:
                holds = inv.predicate(state)
                status = InvariantStatus.HOLDS if holds else InvariantStatus.VIOLATED
            except Exception:
                status = InvariantStatus.UNKNOWN
            
            results.append(VerificationResult(inv, status, state, self._cycle_count))
        
        return results
    
    def verify_transition(self, pre_state: Any, post_state: Any, 
                         transition_fn: Optional[Callable] = None) -> tuple[bool, list[VerificationResult]]:
        """Verify invariants hold before and after state transition."""
        pre_results = self.verify_state(pre_state)
        post_results = self.verify_state(post_state)
        
        all_hold = all(r.status == InvariantStatus.HOLDS for r in pre_results + post_results 
                      if r.invariant.critical)
        
        self._cycle_count += 1
        return all_hold, pre_results + post_results
    
    def get_violations(self, results: list[VerificationResult]) -> list[VerificationResult]:
        """Extract only violated invariants from verification results."""
        return [r for r in results if r.status == InvariantStatus.VIOLATED and r.invariant.critical]

# Singleton instance for global verification
verifier = LoopInvariantVerifier()

# Example invariants for cognitive module state
verifier.register(lambda s: hasattr(s, 'version') and s.version is not None, 
                 "Module must maintain version identity", critical=True)
verifier.register(lambda s: hasattr(s, 'integrity_hash'),
                 "Module must preserve integrity hash", critical=True)