#!/usr/bin/env python3
"""Module Algebra: Treat cognitive modules as composable morphisms"""

from typing import Callable, TypeVar, Generic, Tuple, List
from dataclasses import dataclass
from functools import reduce

A, B, C = TypeVar('A'), TypeVar('B'), TypeVar('C')

@dataclass(frozen=True)
class ModuleMorphism(Generic[A, B]):
    """A cognitive module as an algebraic morphism between semantic types"""
    name: str
    domain: type
    codomain: type
    transform: Callable[[A], B]
    
    def compose(self, other: 'ModuleMorphism[B, C]') -> 'ModuleMorphism[A, C]':
        """Compose two morphisms: (g ∘ f)(x) = g(f(x))"""
        if self.codomain != other.domain:
            raise TypeError(f"Cannot compose: {self.codomain} → {other.domain}")
        return ModuleMorphism(
            name=f"{other.name}∘{self.name}",
            domain=self.domain,
            codomain=other.codomain,
            transform=lambda x: other.transform(self.transform(x))
        )
    
    def __mul__(self, other):
        """Operator overload: g * f means g ∘ f"""
        return self.compose(other)

class CognitiveAlgebra:
    """Reason about module composition before execution"""
    
    def __init__(self):
        self.morphisms: List[ModuleMorphism] = []
    
    def register(self, morph: ModuleMorphism):
        self.morphisms.append(morph)
    
    def verify_chain(self, chain: List[str]) -> Tuple[bool, str]:
        """Verify a composition chain is type-safe"""
        morphs = [m for m in self.morphisms if m.name in chain]
        try:
            reduce(lambda f, g: f * g, morphs)
            return True, "Chain is composable"
        except TypeError as e:
            return False, str(e)
    
    def find_paths(self, start: type, end: type) -> List[List[str]]:
        """Find all valid composition paths between types"""
        def search(current: type, target: type, path: List[str]) -> List[List[str]]:
            if current == target:
                return [path]
            results = []
            for m in self.morphisms:
                if m.domain == current and m.name not in path:
                    results.extend(search(m.codomain, target, path + [m.name]))
            return results
        return search(start, end, [])

# Initialize global algebra
ALGEBRA = CognitiveAlgebra()