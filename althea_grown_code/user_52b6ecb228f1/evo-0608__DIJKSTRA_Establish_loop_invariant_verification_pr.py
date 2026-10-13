"""
loop_invariant_guard.py
Dijkstra-inspired invariant checking for Althea's evolution loops.
Each module evolution must preserve or strengthen system invariants.
"""

from typing import Callable, Any, Dict, List
from dataclasses import dataclass
from functools import wraps


@dataclass(frozen=True)
class Invariant:
    """Immutable invariant specification with proof obligation."""
    name: str
    predicate: Callable[[Dict[str, Any]], bool]
    domain: str  # subsystem this invariant governs
    
    def check(self, state: Dict[str, Any]) -> bool:
        """Verify invariant holds on given state."""
        return self.predicate(state)


class InvariantGuard:
    """
    Maintains and verifies loop invariants during evolution cycles.
    Pre: invariants hold before module execution
    Post: invariants hold after module execution
    """
    
    def __init__(self):
        self._invariants: List[Invariant] = []
        self._violation_log: List[tuple] = []
    
    def register(self, inv: Invariant) -> None:
        """Register an invariant. Idempotent."""
        if inv not in self._invariants:
            self._invariants.append(inv)
    
    def verify_all(self, state: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Check all invariants. Returns (all_pass, failures)."""
        failures = []
        for inv in self._invariants:
            if not inv.check(state):
                failures.append(inv.name)
                self._violation_log.append((inv.name, state.copy()))
        return len(failures) == 0, failures
    
    def guarded_evolution(self, func: Callable) -> Callable:
        """Decorator: verify invariants before and after evolution step."""
        @wraps(func)
        def wrapper(state: Dict[str, Any], *args, **kwargs):
            # Pre-condition check
            pre_ok, pre_fails = self.verify_all(state)
            assert pre_ok, f"Pre-condition violated: {pre_fails}"
            
            # Execute evolution
            result = func(state, *args, **kwargs)
            
            # Post-condition check
            post_ok, post_fails = self.verify_all(state)
            assert post_ok, f"Post-condition violated: {post_fails}"
            
            return result
        return wrapper
    
    def get_violations(self) -> List[tuple]:
        """Retrieve historical violations for analysis."""
        return self._violation_log.copy()


# Core system invariants
GUARD = InvariantGuard()

GUARD.register(Invariant(
    "coherence_bounded",
    lambda s: 0.0 <= s.get("coherence", 1.0) <= 1.0,
    "metrics"
))

GUARD.register(Invariant(
    "module_count_nonnegative", 
    lambda s: s.get("module_count", 0) >= 0,
    "evolution"
))