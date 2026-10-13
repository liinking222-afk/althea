from typing import Callable, TypeVar, Generic, Any
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Morphism(Generic[A, B]):
    """A pure cognitive transformation with algebraic properties."""
    fn: Callable[[A], B]
    input_type: str
    output_type: str
    properties: frozenset[str]
    
    def __call__(self, x: A) -> B:
        return self.fn(x)
    
    def compose(self, other: 'Morphism[B, C]') -> 'Morphism[A, C]':
        """Algebraic composition: (g ∘ f)(x) = g(f(x))"""
        return Morphism(
            fn=lambda x: other.fn(self.fn(x)),
            input_type=self.input_type,
            output_type=other.output_type,
            properties=self.properties | other.properties
        )
    
    def __matmul__(self, other):
        """Operator overload: g @ f means g ∘ f"""
        return self.compose(other)

class CognitiveAlgebra:
    """Treat mental operations as algebraic objects."""
    
    @staticmethod
    def identity(type_name: str) -> Morphism[A, A]:
        return Morphism(lambda x: x, type_name, type_name, frozenset(['identity']))
    
    @staticmethod
    def prove_associative(f: Morphism, g: Morphism, h: Morphism, test_input: Any) -> bool:
        """Verify (h ∘ g) ∘ f = h ∘ (g ∘ f)"""
        left = (h @ g) @ f
        right = h @ (g @ f)
        return left(test_input) == right(test_input)
    
    @staticmethod
    def chain(*morphisms: Morphism) -> Morphism:
        """Compose multiple morphisms right-to-left."""
        return reduce(lambda g, f: g @ f, reversed(morphisms))
    
    @staticmethod
    def analyze(m: Morphism) -> dict:
        """Extract algebraic metadata from a morphism."""
        return {
            'signature': f"{m.input_type} → {m.output_type}",
            'properties': sorted(m.properties),
            'is_endomorphism': m.input_type == m.output_type,
            'has_identity': 'identity' in m.properties
        }

# Example: Build cognitive operations as composable morphisms
def create_perception_morphism(name: str, transform: Callable) -> Morphism:
    return Morphism(transform, 'stimulus', 'percept', frozenset([name, 'perception']))

def create_reasoning_morphism(name: str, transform: Callable) -> Morphism:
    return Morphism(transform, 'percept', 'inference', frozenset([name, 'reasoning']))