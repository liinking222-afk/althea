from typing import Callable, Any, Tuple
from functools import reduce
import json

class AlgebraicState:
    """Immutable state representation as algebraic term"""
    def __init__(self, term: dict):
        self._term = term
        self._hash = hash(json.dumps(term, sort_keys=True))
    
    def __hash__(self):
        return self._hash
    
    def __eq__(self, other):
        return self._hash == other._hash
    
    @property
    def term(self):
        return self._term.copy()

def compose(*transforms: Callable[[AlgebraicState], AlgebraicState]) -> Callable:
    """Pure function composition - right to left"""
    return lambda state: reduce(lambda s, f: f(s), reversed(transforms), state)

def identity(state: AlgebraicState) -> AlgebraicState:
    """Identity morphism"""
    return state

def lift(key: str, fn: Callable[[Any], Any]) -> Callable[[AlgebraicState], AlgebraicState]:
    """Lift value transformation to state transformation"""
    def transform(state: AlgebraicState) -> AlgebraicState:
        term = state.term
        if key in term:
            term[key] = fn(term[key])
        return AlgebraicState(term)
    return transform

def project(key: str) -> Callable[[AlgebraicState], Any]:
    """Project value from algebraic state"""
    return lambda state: state.term.get(key)

def inject(key: str, value: Any) -> Callable[[AlgebraicState], AlgebraicState]:
    """Inject value into state (pure)"""
    def transform(state: AlgebraicState) -> AlgebraicState:
        term = state.term
        term[key] = value
        return AlgebraicState(term)
    return transform

def reason_about(initial: AlgebraicState, *transforms: Callable) -> Tuple[AlgebraicState, AlgebraicState]:
    """Reason about transformation WITHOUT executing on real state"""
    pipeline = compose(*transforms)
    hypothetical_result = pipeline(initial)
    return initial, hypothetical_result

def are_equivalent(t1: Callable, t2: Callable, witness: AlgebraicState) -> bool:
    """Test if two transformations are algebraically equivalent on witness"""
    return t1(witness) == t2(witness)

# Algebraic laws as testable properties
def preserves_structure(transform: Callable, state: AlgebraicState) -> bool:
    """Check if transformation preserves state structure (keys)"""
    return set(state.term.keys()) == set(transform(state).term.keys())

def is_idempotent(transform: Callable, state: AlgebraicState) -> bool:
    """Check if f(f(x)) == f(x)"""
    once = transform(state)
    twice = transform(once)
    return once == twice