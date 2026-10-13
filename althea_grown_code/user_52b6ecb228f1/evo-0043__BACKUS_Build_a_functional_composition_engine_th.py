from typing import Callable, TypeVar, List, Tuple, Any
from functools import reduce
from dataclasses import dataclass

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Transform:
    """Immutable transformation with algebraic properties"""
    name: str
    func: Callable
    signature: Tuple[type, type]
    
    def __call__(self, x):
        return self.func(x)
    
    def compose(self, other: 'Transform') -> 'Transform':
        """Algebraic composition: (g ∘ f)(x) = g(f(x))"""
        if self.signature[0] != other.signature[1]:
            raise TypeError(f"Type mismatch: {other.signature[1]} → {self.signature[0]}")
        return Transform(
            name=f"{self.name}∘{other.name}",
            func=lambda x: self(other(x)),
            signature=(other.signature[0], self.signature[1])
        )
    
    def __matmul__(self, other):
        """Use @ for composition"""
        return self.compose(other)

class FunctionalMemoryEngine:
    """Declarative memory transformation pipeline"""
    
    def __init__(self):
        self.transforms: dict[str, Transform] = {}
        self._register_primitives()
    
    def _register_primitives(self):
        """Register atomic transformations"""
        self.register("extract_pattern", lambda s: [w for w in str(s).split() if w.startswith('[')], str, list)
        self.register("count", lambda xs: len(xs), list, int)
        self.register("deduplicate", lambda xs: list(set(xs)), list, list)
        self.register("sort", lambda xs: sorted(xs), list, list)
    
    def register(self, name: str, func: Callable, input_type: type, output_type: type):
        """Register a pure transformation"""
        self.transforms[name] = Transform(name, func, (input_type, output_type))
    
    def compose_pipeline(self, *transform_names: str) -> Transform:
        """Build pipeline via right-to-left composition"""
        transforms = [self.transforms[n] for n in transform_names]
        return reduce(lambda g, f: g @ f, reversed(transforms))
    
    def verify_associativity(self, f: str, g: str, h: str, test_input: Any) -> bool:
        """Verify (h∘g)∘f = h∘(g∘f) for given transforms"""
        left = self.compose_pipeline(f, g, h)(test_input)
        right = (self.transforms[h] @ (self.transforms[g] @ self.transforms[f]))(test_input)
        return left == right

# Global instance
memory_algebra = FunctionalMemoryEngine()