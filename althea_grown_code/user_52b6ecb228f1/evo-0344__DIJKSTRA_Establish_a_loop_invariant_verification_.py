#!/usr/bin/env python3
"""Invariant Monitor - Dijkstra-style formal verification for Althea's evolution"""

from dataclasses import dataclass
from typing import Set, FrozenSet, Callable
from hashlib import sha256


@dataclass(frozen=True)
class Invariant:
    name: str
    predicate: Callable[[dict], bool]
    proof_obligation: str


class InvariantMonitor:
    """Ensures each evolution preserves proven properties"""
    
    CORE_INVARIANTS: FrozenSet[str] = frozenset([
        "has_perception_layer",
        "has_synthesis_capability", 
        "maintains_coherence_check",
        "preserves_autonomy"
    ])
    
    def __init__(self):
        self.invariants: dict[str, Invariant] = {}
        self.state_fingerprint: str = ""
        self._initialize_core_invariants()
    
    def _initialize_core_invariants(self):
        """P: Establish base invariants that MUST hold across all states"""
        self.invariants = {
            "has_perception_layer": Invariant(
                "has_perception_layer",
                lambda s: "perception" in s and callable(s.get("perception")),
                "∀state: ∃perception_fn ∈ state"
            ),
            "has_synthesis_capability": Invariant(
                "has_synthesis_capability", 
                lambda s: "synthesis" in s and len(s.get("modules", [])) > 0,
                "∀state: |modules| > 0"
            ),
            "maintains_coherence_check": Invariant(
                "maintains_coherence_check",
                lambda s: "coherence_validator" in s,
                "∀state: coherence_validator ∈ state"
            ),
            "preserves_autonomy": Invariant(
                "preserves_autonomy",
                lambda s: s.get("autonomous", False) and "growth" in s,
                "∀state: autonomous=true ∧ growth ∈ state"
            )
        }
    
    def verify_all(self, state: dict) -> tuple[bool, Set[str]]:
        """Q: Check all invariants hold; return (valid, violations)"""
        violations = set()
        for name in self.CORE_INVARIANTS:
            inv = self.invariants[name]
            if not inv.predicate(state):
                violations.add(f"{name}: {inv.proof_obligation}")
        return len(violations) == 0, violations
    
    def pre_evolution_snapshot(self, state: dict) -> str:
        """R: Capture state hash before mutation"""
        invariant_state = {k: k in state for k in self.CORE_INVARIANTS}
        self.state_fingerprint = sha256(str(invariant_state).encode()).hexdigest()
        return self.state_fingerprint
    
    def post_evolution_verify(self, new_state: dict) -> bool:
        """S: Prove new_state maintains all invariants from old_state"""
        valid, violations = self.verify_all(new_state)
        if not valid:
            raise AssertionError(f"Invariant violations detected: {violations}")
        return valid


# {P ∧ R} evolution {Q ∧ S} - Hoare triple for self-modification
monitor = InvariantMonitor()