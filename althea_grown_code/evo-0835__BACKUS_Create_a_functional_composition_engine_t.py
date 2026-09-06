#!/usr/bin/env python3
"""Functional Composition Engine - Modules as Algebraic Morphisms"""

from typing import Callable, Any, TypeVar, Generic, Optional
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Morphism(Generic[A, B]):
    """An algebraic morphism: domain -> codomain with properties"""
    name: str
    domain: type
    codomain: type
    func: Callable[[A], B]
    idempotent: bool = False
    associative: bool = True
    
    def __call__(self, x: A) -> B:
        return self.func(x)
    
    def compose(self, other: 'Morphism[B, C]') -> 'Morphism[A, C]':
        """Algebraic composition: g ∘ f"""
        if self.codomain != other.domain:
            raise TypeError(f"Cannot compose: {self.codomain} → {other.domain}")
        return Morphism(
            name=f"{other.name}∘{self.name}",
            domain=self.domain,
            codomain=other.codomain,
            func=lambda x: other.func(self.func(x)),
            idempotent=self.idempotent and other.idempotent,
            associative=self.associative and other.associative
        )
    
    def __rshift__(self, other):
        """Syntax sugar: f >> g means g ∘ f"""
        return self.compose(other)

class CompositionEngine:
    """Reason about capability chains algebraically"""
    
    def __init__(self):
        self.morphisms: dict[str, Morphism] = {}
    
    def register(self, morph: Morphism) -> None:
        self.morphisms[morph.name] = morph
    
    def find_path(self, start: type, end: type) -> Optional[list[str]]:
        """Find composable chain from start type to end type"""
        if start == end:
            return []
        
        visited = set()
        queue = [(start, [])]
        
        while queue:
            current, path = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            for name, morph in self.morphisms.items():
                if morph.domain == current:
                    new_path = path + [name]
                    if morph.codomain == end:
                        return new_path
                    queue.append((morph.codomain, new_path))
        return None
    
    def compose_chain(self, names: list[str]) -> Morphism:
        """Compose a chain of morphisms left-to-right"""
        morphs = [self.morphisms[n] for n in names]
        return reduce(lambda f, g: f >> g, morphs)

engine = CompositionEngine()