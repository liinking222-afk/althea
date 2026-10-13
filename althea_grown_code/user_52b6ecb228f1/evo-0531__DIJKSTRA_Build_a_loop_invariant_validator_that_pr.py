from dataclasses import dataclass
from typing import Callable, Any, Optional
from enum import Enum

class InvariantStatus(Enum):
    HOLDS = "holds"
    VIOLATED = "violated"
    WEAKENED = "weakened"

@dataclass(frozen=True)
class LoopState:
    iteration: int
    variant: int  # decreasing function proving termination
    data: Any

@dataclass(frozen=True)
class InvariantProof:
    name: str
    holds: bool
    iteration: int
    variant_value: int
    message: str

class LoopInvariantValidator:
    """Dijkstra-style loop invariant checker for evolution cycles."""
    
    def __init__(self, max_iterations: int):
        assert max_iterations > 0, "Precondition: max_iterations > 0"
        self._max_iterations = max_iterations
        self._proofs: list[InvariantProof] = []
    
    def validate_cycle(
        self,
        initial_state: LoopState,
        invariant: Callable[[LoopState], bool],
        variant: Callable[[LoopState], int],
        step: Callable[[LoopState], Optional[LoopState]],
        guard: Callable[[LoopState], bool]
    ) -> list[InvariantProof]:
        """
        Proves loop correctness via:
        1. Invariant holds initially (P)
        2. Invariant preserved by step (P ∧ B ⇒ P')
        3. Variant decreases (V' < V)
        4. Variant bounded below (V ≥ 0)
        """
        current = initial_state
        
        # Precondition check
        assert invariant(current), f"Precondition violated: invariant false at start"
        assert variant(current) >= 0, f"Precondition violated: variant negative"
        
        self._proofs.append(InvariantProof(
            "initialization", True, 0, variant(current),
            "Invariant holds at initialization"
        ))
        
        while guard(current) and current.iteration < self._max_iterations:
            v_old = variant(current)
            next_state = step(current)
            
            if next_state is None:
                break
            
            # Invariant preservation check
            inv_holds = invariant(next_state)
            v_new = variant(next_state)
            
            # Variant decrease check (proves termination)
            variant_decreases = v_new < v_old
            variant_bounded = v_new >= 0
            
            self._proofs.append(InvariantProof(
                f"step_{current.iteration}",
                inv_holds and variant_decreases and variant_bounded,
                next_state.iteration,
                v_new,
                f"I={inv_holds} V↓={variant_decreases} V≥0={variant_bounded}"
            ))
            
            assert inv_holds, f"Invariant violated at iteration {next_state.iteration}"
            assert variant_decreases, f"Variant must decrease: {v_old} → {v_new}"
            assert variant_bounded, f"Variant below zero: {v_new}"
            
            current = next_state
        
        return self._proofs
    
    def get_proof_chain(self) -> str:
        return "\n".join(f"[{p.iteration}] {p.name}: {p.message}" for p in self._proofs)