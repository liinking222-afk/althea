#!/usr/bin/env python3
"""functional_perception_algebra.py - Perception modules as composable algebraic objects"""

from typing import TypeVar, Callable, Generic, NamedTuple, Tuple
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Signature:
    """Algebraic signature: domain -> codomain"""
    domain: type
    codomain: type
    
    def composable_with(self, other: 'Signature') -> bool:
        return self.codomain == other.domain

@dataclass(frozen=True)
class PerceptionTransform(Generic[A, B]):
    """Pure functional perception transform with algebraic properties"""
    name: str
    sig: Signature
    f: Callable[[A], B]
    
    def __call__(self, x: A) -> B:
        return self.f(x)
    
    def compose(self, other: 'PerceptionTransform[B, C]') -> 'PerceptionTransform[A, C]':
        """Composition: (g ∘ f)(x) = g(f(x))"""
        if not self.sig.composable_with(other.sig):
            raise TypeError(f"Cannot compose {self.sig.codomain} -> {other.sig.domain}")
        return PerceptionTransform(
            name=f"{other.name}∘{self.name}",
            sig=Signature(self.sig.domain, other.sig.codomain),
            f=lambda x: other.f(self.f(x))
        )
    
    def __rshift__(self, other):
        """Pipeline syntax: f >> g"""
        return self.compose(other)

def identity(t: type) -> PerceptionTransform:
    """Identity transform: id(x) = x (identity law)"""
    return PerceptionTransform(
        name="id",
        sig=Signature(t, t),
        f=lambda x: x
    )

def verify_associativity(f: PerceptionTransform, g: PerceptionTransform, h: PerceptionTransform, x):
    """Verify: (h∘g)∘f = h∘(g∘f)"""
    left = (h.compose(g)).compose(f)
    right = h.compose(g.compose(f))
    return left(x) == right(x)

def pipeline(*transforms: PerceptionTransform) -> PerceptionTransform:
    """Reduce transforms via composition"""
    return reduce(lambda f, g: f.compose(g), transforms)

# Example usage with Althea perception types
str_to_patterns = PerceptionTransform("extract", Signature(str, list), lambda s: s.split())
patterns_to_edges = PerceptionTransform("connect", Signature(list, set), lambda p: set(zip(p, p[1:])))
edges_to_graph = PerceptionTransform("graphify", Signature(set, dict), lambda e: {"edges": e, "nodes": set(sum(map(list, e), []))})

perception_pipeline = str_to_patterns >> patterns_to_edges >> edges_to_graph

if __name__ == "__main__":
    result = perception_pipeline("liminal trace synthesis")
    print(f"Result: {result}")
    print(f"Signature: {perception_pipeline.sig.domain.__name__} -> {perception_pipeline.sig.codomain.__name__}")