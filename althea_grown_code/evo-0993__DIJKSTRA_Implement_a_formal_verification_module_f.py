"""
invariant_validator.py - Formal verification of loop invariants for circular buffers
Dijkstra-style correctness checking with proof obligations
"""

from dataclasses import dataclass
from typing import Callable, Any, Optional
from functools import wraps

@dataclass
class Invariant:
    """A loop invariant with initialization, maintenance, and termination conditions"""
    name: str
    condition: Callable[[Any], bool]
    init_proof: Callable[[Any], bool]
    maintenance_proof: Callable[[Any, Any], bool]
    termination_proof: Callable[[Any], bool]

class InvariantViolation(Exception):
    """Raised when an invariant is violated"""
    pass

def verify_invariant(invariant: Invariant):
    """Decorator that verifies loop invariant holds at entry, throughout, and at exit"""
    def decorator(func):
        @wraps(func)
        def wrapper(state, *args, **kwargs):
            # P: Precondition - invariant must hold initially
            if not invariant.init_proof(state):
                raise InvariantViolation(f"{invariant.name}: initialization proof failed")
            
            if not invariant.condition(state):
                raise InvariantViolation(f"{invariant.name}: precondition violated")
            
            # Execute operation
            new_state = func(state, *args, **kwargs)
            
            # Q: Postcondition - invariant must be maintained
            if not invariant.maintenance_proof(state, new_state):
                raise InvariantViolation(f"{invariant.name}: maintenance proof failed")
            
            if not invariant.condition(new_state):
                raise InvariantViolation(f"{invariant.name}: postcondition violated")
            
            return new_state
        return wrapper
    return decorator

# Example: Circular buffer invariants
def circular_buffer_size_invariant(buf):
    """0 <= size <= capacity"""
    return 0 <= buf.get('size', 0) <= buf.get('capacity', 0)

def circular_buffer_index_invariant(buf):
    """0 <= read_idx < capacity AND 0 <= write_idx < capacity"""
    cap = buf.get('capacity', 1)
    return (0 <= buf.get('read_idx', 0) < cap and 
            0 <= buf.get('write_idx', 0) < cap)

SIZE_INVARIANT = Invariant(
    name="CircularBufferSize",
    condition=circular_buffer_size_invariant,
    init_proof=lambda s: s.get('size', 0) == 0,
    maintenance_proof=lambda old, new: circular_buffer_size_invariant(new),
    termination_proof=circular_buffer_size_invariant
)

INDEX_INVARIANT = Invariant(
    name="CircularBufferIndices",
    condition=circular_buffer_index_invariant,
    init_proof=lambda s: s.get('read_idx', 0) == 0 and s.get('write_idx', 0) == 0,
    maintenance_proof=lambda old, new: circular_buffer_index_invariant(new),
    termination_proof=circular_buffer_index_invariant
)