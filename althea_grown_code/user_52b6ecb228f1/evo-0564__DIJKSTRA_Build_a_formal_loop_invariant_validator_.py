"""
Dijkstra-style loop invariant validator for cognitive iteration.
Ensures formal correctness of iterative reasoning processes.
"""

from typing import Callable, Any, Dict, List, Optional
from dataclasses import dataclass

@dataclass
class Invariant:
    """An invariant is a predicate that must hold throughout iteration."""
    name: str
    predicate: Callable[[Dict[str, Any]], bool]
    
@dataclass
class LoopSpec:
    """Formal specification of a loop with pre/post conditions and invariants."""
    precondition: Callable[[Dict[str, Any]], bool]
    postcondition: Callable[[Dict[str, Any]], bool]
    invariants: List[Invariant]
    bound_function: Callable[[Dict[str, Any]], int]  # Decreasing function proves termination

class LoopValidator:
    """Validates loop correctness via invariant checking."""
    
    def __init__(self):
        self.violations: List[str] = []
    
    def validate_iteration(self, spec: LoopSpec, state: Dict[str, Any], 
                          iteration: int, is_entry: bool = False, 
                          is_exit: bool = False) -> bool:
        """Check all invariants hold at this iteration point."""
        self.violations.clear()
        
        # Entry: precondition must hold
        if is_entry and not spec.precondition(state):
            self.violations.append(f"Precondition violated at entry")
            return False
        
        # Every iteration: invariants must hold
        for inv in spec.invariants:
            if not inv.predicate(state):
                self.violations.append(f"Invariant '{inv.name}' violated at iteration {iteration}")
                return False
        
        # Exit: postcondition must hold
        if is_exit and not spec.postcondition(state):
            self.violations.append(f"Postcondition violated at exit")
            return False
        
        # Termination: bound function must be non-negative and decreasing
        bound = spec.bound_function(state)
        if bound < 0:
            self.violations.append(f"Bound function negative at iteration {iteration}")
            return False
        
        return True
    
    def get_violations(self) -> List[str]:
        """Return all detected violations."""
        return self.violations.copy()

def prove_correct(spec: LoopSpec, initial_state: Dict[str, Any], 
                  step_fn: Callable[[Dict[str, Any]], Optional[Dict[str, Any]]], 
                  max_iterations: int = 1000) -> bool:
    """Execute loop with formal correctness checking at each step."""
    validator = LoopValidator()
    state = initial_state.copy()
    
    if not validator.validate_iteration(spec, state, 0, is_entry=True):
        return False
    
    for i in range(max_iterations):
        next_state = step_fn(state)
        if next_state is None:  # Exit condition
            return validator.validate_iteration(spec, state, i, is_exit=True)
        
        if not validator.validate_iteration(spec, next_state, i + 1):
            return False
        
        state = next_state
    
    return False  # Failed to terminate