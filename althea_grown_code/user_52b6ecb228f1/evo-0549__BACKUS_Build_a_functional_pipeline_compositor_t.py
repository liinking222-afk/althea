#!/usr/bin/env python3
"""functional_pipeline_algebra.py - Module composition as algebraic structures"""

from typing import Callable, TypeVar, List, Tuple, Any
from dataclasses import dataclass
from functools import reduce
import hashlib
import json

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Pipeline:
    """Immutable function composition with algebraic properties"""
    morphisms: Tuple[Callable, ...]
    type_signature: str
    
    def __call__(self, x: Any) -> Any:
        return reduce(lambda acc, f: f(acc), self.morphisms, x)
    
    def compose(self, other: 'Pipeline') -> 'Pipeline':
        """Associative composition: (f ∘ g) ∘ h = f ∘ (g ∘ h)"""
        return Pipeline(
            self.morphisms + other.morphisms,
            f"{other.type_signature.split('->')[0]}->{self.type_signature.split('->')[-1]}"
        )
    
    def __rshift__(self, other: 'Pipeline') -> 'Pipeline':
        return self.compose(other)
    
    @property
    def identity_hash(self) -> str:
        """Canonical representation for equality reasoning"""
        sig = json.dumps([f.__name__ for f in self.morphisms], sort_keys=True)
        return hashlib.sha256(sig.encode()).hexdigest()[:16]
    
    def prove_associativity(self, g: 'Pipeline', h: 'Pipeline', test_input: Any) -> bool:
        """Verify (self ∘ g) ∘ h = self ∘ (g ∘ h)"""
        left = (self.compose(g)).compose(h)
        right = self.compose(g.compose(h))
        return left(test_input) == right(test_input)

def lift(f: Callable, sig: str) -> Pipeline:
    """Lift function into pipeline algebra"""
    return Pipeline((f,), sig)

def identity(domain: str) -> Pipeline:
    """Identity morphism: id ∘ f = f ∘ id = f"""
    return Pipeline((lambda x: x,), f"{domain}->{domain}")

def parallel(*pipelines: Pipeline) -> Callable:
    """Product morphism: apply pipelines in parallel to tuple inputs"""
    def apply(inputs: Tuple) -> Tuple:
        return tuple(p(i) for p, i in zip(pipelines, inputs))
    return apply

def memoized_pipeline(p: Pipeline) -> Pipeline:
    """Referentially transparent caching (pure functions only)"""
    cache = {}
    def memo_call(x):
        key = str(x)
        if key not in cache:
            cache[key] = p(x)
        return cache[key]
    return Pipeline((memo_call,), p.type_signature)

# Example: spectral analysis as algebraic composition
normalize = lift(lambda s: [x/max(s) for x in s], "signal->signal")
square = lift(lambda s: [x**2 for x in s], "signal->signal")
sum_energy = lift(sum, "signal->float")

energy_pipeline = normalize >> square >> sum_energy

if __name__ == "__main__":
    test_signal = [1, 2, 3, 4, 5]
    print(f"Energy: {energy_pipeline(test_signal)}")
    print(f"Pipeline hash: {energy_pipeline.identity_hash}")