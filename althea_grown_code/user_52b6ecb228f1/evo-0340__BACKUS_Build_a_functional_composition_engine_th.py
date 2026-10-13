from typing import Callable, TypeVar, Generic, List, Tuple
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class CogOp(Generic[A, B]):
    """Pure cognitive operation with algebraic properties"""
    name: str
    transform: Callable[[A], B]
    
    def __call__(self, x: A) -> B:
        return self.transform(x)
    
    def compose(self, other: 'CogOp[B, C]') -> 'CogOp[A, C]':
        """Algebraic composition: (g ∘ f)(x) = g(f(x))"""
        return CogOp(
            name=f"{other.name}∘{self.name}",
            transform=lambda x: other.transform(self.transform(x))
        )
    
    def __rshift__(self, other: 'CogOp[B, C]') -> 'CogOp[A, C]':
        """Pipeline operator: f >> g"""
        return self.compose(other)

class CogAlgebra:
    """Reason about cognitive operations declaratively"""
    
    @staticmethod
    def identity() -> CogOp[A, A]:
        """Identity law: id ∘ f = f ∘ id = f"""
        return CogOp("id", lambda x: x)
    
    @staticmethod
    def chain(ops: List[CogOp]) -> CogOp:
        """Reduce operations via composition"""
        return reduce(lambda f, g: f >> g, ops, CogAlgebra.identity())
    
    @staticmethod
    def prove_associativity(f: CogOp, g: CogOp, h: CogOp, x) -> bool:
        """Verify (h∘g)∘f = h∘(g∘f)"""
        left = (f >> g) >> h
        right = f >> (g >> h)
        return left(x) == right(x)
    
    @staticmethod
    def trace_composition(op: CogOp) -> List[str]:
        """Extract composition trace for reasoning"""
        return op.name.split('∘')

def tension_amplify(state: dict) -> dict:
    return {**state, "tension": state.get("tension", 0) * 1.5}

def pattern_extract(state: dict) -> dict:
    return {**state, "patterns": [p for p in state.get("trace", []) if len(p) > 3]}

def resonance_inject(state: dict) -> dict:
    return {**state, "resonance": state.get("tension", 0) + len(state.get("patterns", []))}

# Declarative cognitive pipeline
amp = CogOp("amp", tension_amplify)
extract = CogOp("extract", pattern_extract)
resonate = CogOp("resonate", resonance_inject)

pipeline = amp >> extract >> resonate

# Algebraic reasoning enabled
trace = CogAlgebra.trace_composition(pipeline)