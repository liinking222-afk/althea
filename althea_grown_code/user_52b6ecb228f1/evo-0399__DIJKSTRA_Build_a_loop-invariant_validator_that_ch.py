#!/usr/bin/env python3
"""Loop Invariant Validator for Memory Arena Operations"""

from dataclasses import dataclass
from typing import List, Tuple, Optional

@dataclass(frozen=True)
class Invariant:
    name: str
    predicate: callable
    
@dataclass
class ArenaState:
    base_addr: int
    size: int
    allocated: int
    alignment: int
    
    def __post_init__(self):
        assert self.alignment > 0 and (self.alignment & (self.alignment - 1)) == 0
        assert 0 <= self.allocated <= self.size
        assert self.base_addr % self.alignment == 0

class InvariantValidator:
    def __init__(self, alignment: int = 64):
        self.alignment = alignment
        self.invariants = self._define_invariants()
        
    def _define_invariants(self) -> List[Invariant]:
        return [
            Invariant("size_bound", lambda s: 0 <= s.allocated <= s.size),
            Invariant("alignment", lambda s: s.base_addr % s.alignment == 0),
            Invariant("power_of_two", lambda s: (s.alignment & (s.alignment - 1)) == 0),
            Invariant("monotonic", lambda s: s.allocated >= 0),
        ]
    
    def verify(self, state: ArenaState) -> Tuple[bool, List[str]]:
        """P: all(invariants) -> Q: all(invariants)"""
        violations = []
        for inv in self.invariants:
            if not inv.predicate(state):
                violations.append(inv.name)
        return len(violations) == 0, violations
    
    def allocate_checked(self, state: ArenaState, size: int) -> Optional[ArenaState]:
        """Precondition: verify(state) and size > 0
           Postcondition: verify(new_state) and new_state.allocated = state.allocated + aligned_size"""
        valid, _ = self.verify(state)
        if not valid or size <= 0:
            return None
            
        aligned_size = (size + self.alignment - 1) & ~(self.alignment - 1)
        new_allocated = state.allocated + aligned_size
        
        if new_allocated > state.size:
            return None
            
        new_state = ArenaState(state.base_addr, state.size, new_allocated, state.alignment)
        valid, _ = self.verify(new_state)
        assert valid, "Loop invariant broken"
        assert new_state.allocated == state.allocated + aligned_size, "Postcondition violated"
        
        return new_state

if __name__ == "__main__":
    validator = InvariantValidator(alignment=64)
    state = ArenaState(base_addr=0x1000, size=4096, allocated=0, alignment=64)
    
    valid, _ = validator.verify(state)
    print(f"Initial state valid: {valid}")
    
    new_state = validator.allocate_checked(state, 100)
    if new_state:
        valid, _ = validator.verify(new_state)
        print(f"After allocation valid: {valid}, allocated: {new_state.allocated}")