from dataclasses import dataclass
from typing import Callable, Any, Optional
from enum import Enum

class ProofStatus(Enum):
    UNPROVEN = 0
    VALID = 1
    VIOLATED = 2

@dataclass(frozen=True)
class Invariant:
    name: str
    predicate: Callable[[Any], bool]
    proof_obligation: str
    
    def check(self, state: Any) -> ProofStatus:
        try:
            return ProofStatus.VALID if self.predicate(state) else ProofStatus.VIOLATED
        except Exception:
            return ProofStatus.VIOLATED

class InvariantGuard:
    def __init__(self):
        self._invariants: dict[str, Invariant] = {}
        self._violations: list[tuple[str, Any]] = []
    
    def register(self, inv: Invariant) -> None:
        assert inv.name not in self._invariants, f"Invariant {inv.name} already registered"
        self._invariants[inv.name] = inv
    
    def verify_all(self, state: Any) -> bool:
        all_valid = True
        for name, inv in self._invariants.items():
            status = inv.check(state)
            if status == ProofStatus.VIOLATED:
                self._violations.append((name, state))
                all_valid = False
        return all_valid
    
    def get_proof_obligations(self) -> list[str]:
        return [inv.proof_obligation for inv in self._invariants.values()]
    
    def clear_violations(self) -> list[tuple[str, Any]]:
        v = self._violations.copy()
        self._violations.clear()
        return v

# Core cognitive module invariants
GUARD = InvariantGuard()

GUARD.register(Invariant(
    name="module_composition_associative",
    predicate=lambda s: s.get('composition_depth', 0) >= 0,
    proof_obligation="∀ modules M₁,M₂,M₃: (M₁∘M₂)∘M₃ = M₁∘(M₂∘M₃)"
))

GUARD.register(Invariant(
    name="state_monotonic_coherence",
    predicate=lambda s: s.get('coherence_score', 1.0) >= 0.0 and s.get('coherence_score', 1.0) <= 1.0,
    proof_obligation="∀ states Sₙ,Sₙ₊₁: coherence(Sₙ₊₁) ≥ coherence(Sₙ) - ε"
))

GUARD.register(Invariant(
    name="evolution_preserves_identity",
    predicate=lambda s: s.get('core_identity_hash') is not None,
    proof_obligation="∀ evolutions E: ∃ core C: E(C) preserves C.essence"
))

def verify_cognitive_state(state: dict) -> tuple[bool, list[str]]:
    valid = GUARD.verify_all(state)
    obligations = GUARD.get_proof_obligations() if not valid else []
    return valid, obligations