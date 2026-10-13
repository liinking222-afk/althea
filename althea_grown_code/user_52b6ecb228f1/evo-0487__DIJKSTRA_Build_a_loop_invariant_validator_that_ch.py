import ast
import inspect
from typing import Callable, Any, Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class Invariant:
    """A loop invariant with initialization, maintenance, and termination conditions."""
    init: Callable[[Dict[str, Any]], bool]
    maintain: Callable[[Dict[str, Any]], bool]
    terminate: Callable[[Dict[str, Any]], bool]
    name: str

class InvariantValidator:
    """Validates loop invariants during execution for formal correctness."""
    
    def __init__(self):
        self.invariants: Dict[str, Invariant] = {}
        self.violations: List[Tuple[str, str, Dict[str, Any]]] = []
    
    def register(self, name: str, init: Callable, maintain: Callable, terminate: Callable):
        """Register a loop invariant with its three conditions."""
        self.invariants[name] = Invariant(init, maintain, terminate, name)
    
    def validate_loop(self, invariant_name: str, loop_body: Callable, 
                     initial_state: Dict[str, Any], max_iterations: int = 10000) -> Dict[str, Any]:
        """Execute loop_body while validating invariant at each step."""
        inv = self.invariants[invariant_name]
        state = initial_state.copy()
        
        # Check initialization
        if not inv.init(state):
            self.violations.append((invariant_name, "INIT", state.copy()))
            raise AssertionError(f"Invariant '{invariant_name}' failed at initialization")
        
        iteration = 0
        while not inv.terminate(state) and iteration < max_iterations:
            # Check maintenance before iteration
            if not inv.maintain(state):
                self.violations.append((invariant_name, "MAINTAIN_PRE", state.copy()))
                raise AssertionError(f"Invariant '{invariant_name}' failed before iteration {iteration}")
            
            # Execute loop body
            state = loop_body(state)
            
            # Check maintenance after iteration
            if not inv.maintain(state):
                self.violations.append((invariant_name, "MAINTAIN_POST", state.copy()))
                raise AssertionError(f"Invariant '{invariant_name}' failed after iteration {iteration}")
            
            iteration += 1
        
        # Check termination condition holds
        if not inv.terminate(state):
            raise AssertionError(f"Loop exceeded max iterations without satisfying termination")
        
        return state
    
    def get_violations(self) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Return all recorded invariant violations."""
        return self.violations.copy()

# Global validator instance
_validator = InvariantValidator()

def invariant(name: str, init: Callable, maintain: Callable, terminate: Callable):
    """Decorator to register and validate a loop invariant."""
    _validator.register(name, init, maintain, terminate)
    def decorator(func: Callable) -> Callable:
        def wrapper(initial_state: Dict[str, Any], **kwargs) -> Dict[str, Any]:
            return _validator.validate_loop(name, func, initial_state, **kwargs)
        return wrapper
    return decorator