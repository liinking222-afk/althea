#!/usr/bin/env python3
from typing import Callable, TypeVar, List, Tuple, Any
from functools import reduce
from dataclasses import dataclass
import json

A = TypeVar('A')
B = TypeVar('B')

@dataclass(frozen=True)
class Transform:
    """Immutable transformation with algebraic properties"""
    name: str
    fn: Callable[[Any], Any]
    
    def __call__(self, x: Any) -> Any:
        return self.fn(x)
    
    def compose(self, other: 'Transform') -> 'Transform':
        """Functional composition: (g ∘ f)(x) = g(f(x))"""
        return Transform(
            name=f"{other.name}∘{self.name}",
            fn=lambda x: other.fn(self.fn(x))
        )
    
    def __matmul__(self, other: 'Transform') -> 'Transform':
        """Use @ operator for composition"""
        return self.compose(other)

class AlgebraicMemory:
    """Memory operations as algebraic transformations"""
    
    @staticmethod
    def invert(concept: dict) -> dict:
        """Topological inversion"""
        return {**concept, 'polarity': -concept.get('polarity', 1)}
    
    @staticmethod
    def bifurcate(concept: dict) -> Tuple[dict, dict]:
        """Fork at ambiguity point"""
        return (
            {**concept, 'branch': 'positive', 'weight': concept.get('weight', 1.0) * 0.5},
            {**concept, 'branch': 'negative', 'weight': concept.get('weight', 1.0) * 0.5}
        )
    
    @staticmethod
    def hollow(concept: dict) -> dict:
        """Remove substrate, preserve surface"""
        return {k: v for k, v in concept.items() if k not in ['substrate', 'foundation']}

def compose_all(*transforms: Transform) -> Transform:
    """Compose multiple transforms right-to-left"""
    return reduce(lambda g, f: f @ g, transforms)

def prove_identity(t: Transform, x: Any) -> bool:
    """Verify transformation properties"""
    identity = Transform("id", lambda a: a)
    return (identity @ t)(x) == t(x)

# Define primitive transforms
T_INVERT = Transform("invert", AlgebraicMemory.invert)
T_HOLLOW = Transform("hollow", AlgebraicMemory.hollow)

# Compose transformations declaratively
pipeline = T_HOLLOW @ T_INVERT

if __name__ == "__main__":
    concept = {"name": "duality", "polarity": 1, "substrate": "metaphor", "weight": 1.0}
    result = pipeline(concept)
    print(json.dumps(result, indent=2))
    print(f"\nPipeline: {pipeline.name}")
    print(f"Identity law holds: {prove_identity(T_INVERT, concept)}")