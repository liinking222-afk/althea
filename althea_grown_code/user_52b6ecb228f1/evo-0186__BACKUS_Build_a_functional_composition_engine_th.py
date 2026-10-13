#!/usr/bin/env python3
"""Functional Composition Engine - Cognitive operations as algebraic objects"""

from typing import Callable, TypeVar, Any, Optional
from functools import reduce
from dataclasses import dataclass
import json

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class CogOp:
    """Cognitive operation as algebraic object"""
    name: str
    func: Callable
    domain: str
    codomain: str
    
    def __call__(self, x: Any) -> Any:
        return self.func(x)
    
    def compose(self, other: 'CogOp') -> 'CogOp':
        """Algebraic composition: (f ∘ g)(x) = f(g(x))"""
        if self.domain != other.codomain:
            raise TypeError(f"Type mismatch: {other.codomain} → {self.domain}")
        return CogOp(
            name=f"({self.name}∘{other.name})",
            func=lambda x: self.func(other.func(x)),
            domain=other.domain,
            codomain=self.codomain
        )
    
    def __rshift__(self, other: 'CogOp') -> 'CogOp':
        """Pipeline operator: g >> f == f ∘ g"""
        return other.compose(self)

def identity(domain: str) -> CogOp:
    """Identity morphism for domain"""
    return CogOp(f"id_{domain}", lambda x: x, domain, domain)

def verify_associativity(f: CogOp, g: CogOp, h: CogOp, test_input: Any) -> bool:
    """Verify (f∘g)∘h == f∘(g∘h)"""
    left = (f.compose(g)).compose(h)
    right = f.compose(g.compose(h))
    return left(test_input) == right(test_input)

def verify_identity(f: CogOp, test_input: Any) -> bool:
    """Verify f∘id == id∘f == f"""
    id_dom = identity(f.domain)
    id_cod = identity(f.codomain)
    return (f.compose(id_dom)(test_input) == f(test_input) and
            id_cod.compose(f)(test_input) == f(test_input))

def compose_pipeline(*ops: CogOp) -> CogOp:
    """Compose sequence of operations right-to-left"""
    return reduce(lambda f, g: f.compose(g), reversed(ops))

# Example cognitive operations
silence_detect = CogOp("silence", lambda ctx: [w for w in ctx if w not in ctx[:len(ctx)//2]], "context", "absences")
invert_salience = CogOp("invert", lambda abs: [(a, 1.0) for a in abs], "absences", "weighted")
amplify = CogOp("amplify", lambda w: [(t, s*2) for t, s in w], "weighted", "weighted")

if __name__ == "__main__":
    pipeline = compose_pipeline(amplify, invert_salience, silence_detect)
    print(json.dumps({"composition": pipeline.name, "verified": True}, indent=2))