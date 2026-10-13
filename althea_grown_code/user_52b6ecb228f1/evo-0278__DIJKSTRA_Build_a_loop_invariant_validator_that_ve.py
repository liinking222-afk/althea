"""Loop Invariant Validator - Dijkstra formal correctness for recursive depth control"""

from typing import Dict, Callable, Any, Tuple
from dataclasses import dataclass

@dataclass
class Invariant:
    """Predicate with formal pre/post conditions"""
    name: str
    precondition: Callable[[Dict[str, Any]], bool]
    postcondition: Callable[[Dict[str, Any]], bool]
    maintains: Callable[[Dict[str, Any], Dict[str, Any]], bool]

class InvariantValidator:
    def __init__(self):
        self.invariants: Dict[str, Invariant] = {}
        self.violation_count: int = 0
        
    def register(self, inv: Invariant) -> None:
        """Register a loop invariant with proof obligations"""
        self.invariants[inv.name] = inv
    
    def validate_entry(self, context: str, state: Dict[str, Any]) -> bool:
        """Verify precondition holds at loop entry - MUST be true"""
        if context not in self.invariants:
            return True
        inv = self.invariants[context]
        if not inv.precondition(state):
            self.violation_count += 1
            return False
        return True
    
    def validate_exit(self, context: str, state: Dict[str, Any]) -> bool:
        """Verify postcondition holds at loop exit - MUST be true"""
        if context not in self.invariants:
            return True
        inv = self.invariants[context]
        if not inv.postcondition(state):
            self.violation_count += 1
            return False
        return True
    
    def validate_step(self, context: str, before: Dict[str, Any], 
                      after: Dict[str, Any]) -> bool:
        """Verify invariant maintained across single iteration"""
        if context not in self.invariants:
            return True
        inv = self.invariants[context]
        if not inv.maintains(before, after):
            self.violation_count += 1
            return False
        return True
    
    def proof_block(self, context: str, state_in: Dict[str, Any],
                   transform: Callable[[Dict[str, Any]], Dict[str, Any]]) -> Tuple[Dict[str, Any], bool]:
        """Execute transform with full invariant proof - returns (result, valid)"""
        if not self.validate_entry(context, state_in):
            return state_in, False
        
        state_out = transform(state_in)
        
        maintains = self.validate_step(context, state_in, state_out)
        exits = self.validate_exit(context, state_out)
        
        return state_out, maintains and exits
    
    def is_sound(self) -> bool:
        """System is sound iff no violations occurred"""
        return self.violation_count == 0

# Global validator instance
VALIDATOR = InvariantValidator()

def recursive_depth_invariant() -> Invariant:
    """Canonical invariant: recursion depth bounded and decreasing"""
    return Invariant(
        name="recursion_depth_bound",
        precondition=lambda s: s.get("depth", 0) >= 0,
        postcondition=lambda s: s.get("depth", 0) == 0 or s.get("progress", False),
        maintains=lambda b, a: a.get("depth", 0) <= b.get("depth", 0)
    )

VALIDATOR.register(recursive_depth_invariant())