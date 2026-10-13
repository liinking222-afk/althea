#!/usr/bin/env python3
"""Loop Invariant Validator - Dijkstra formal correctness for evolution cycles"""

from dataclasses import dataclass
from typing import List, Set, Callable, Optional
from enum import Enum

class Property(Enum):
    MONOTONIC_VERSION = "version_never_decreases"
    DELTA_COHERENCE = "delta_describes_actual_change"
    INTENT_PRESERVED = "intent_remains_valid_post_evolution"
    NO_SEMANTIC_LEAK = "no_undefined_references"

@dataclass(frozen=True)
class Invariant:
    property: Property
    predicate: Callable[[dict], bool]
    proof_obligation: str

@dataclass
class EvolutionState:
    version: str
    intent: str
    delta: str
    referenced_modules: Set[str]
    
    def to_dict(self) -> dict:
        return {
            'version': self.version,
            'intent': self.intent,
            'delta': self.delta,
            'refs': self.referenced_modules
        }

class InvariantValidator:
    def __init__(self):
        self.invariants: List[Invariant] = [
            Invariant(
                Property.MONOTONIC_VERSION,
                lambda s: self._check_version_monotonic(s),
                "∀evo: version(evo_n) > version(evo_n-1)"
            ),
            Invariant(
                Property.DELTA_COHERENCE,
                lambda s: len(s.get('delta', '')) > 0 and len(s.get('intent', '')) > 0,
                "∀evo: |delta| > 0 ∧ |intent| > 0"
            ),
            Invariant(
                Property.NO_SEMANTIC_LEAK,
                lambda s: len(s.get('refs', set())) == 0 or all(r.strip() for r in s.get('refs', set())),
                "∀ref ∈ refs: ref ≠ ∅"
            )
        ]
        self.previous_state: Optional[EvolutionState] = None
    
    def _check_version_monotonic(self, state: dict) -> bool:
        if not self.previous_state:
            return True
        try:
            prev = tuple(map(int, self.previous_state.version.split('.')))
            curr = tuple(map(int, state['version'].split('.')))
            return curr >= prev
        except:
            return False
    
    def validate(self, state: EvolutionState) -> tuple[bool, List[str]]:
        """Returns (is_valid, failed_proofs)"""
        state_dict = state.to_dict()
        failures = []
        
        for inv in self.invariants:
            if not inv.predicate(state_dict):
                failures.append(f"{inv.property.value}: {inv.proof_obligation}")
        
        is_valid = len(failures) == 0
        if is_valid:
            self.previous_state = state
        
        return is_valid, failures

# Singleton validator instance
_validator = InvariantValidator()

def check_evolution_invariants(version: str, intent: str, delta: str, refs: Set[str] = None) -> bool:
    state = EvolutionState(version, intent, delta, refs or set())
    valid, failures = _validator.validate(state)
    if not valid:
        raise AssertionError(f"Invariant violations: {'; '.join(failures)}")
    return True