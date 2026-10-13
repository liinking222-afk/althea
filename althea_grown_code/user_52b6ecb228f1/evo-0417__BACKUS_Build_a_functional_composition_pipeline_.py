from typing import Callable, TypeVar, Generic, List, Tuple, Any
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Morphism(Generic[A, B]):
    """A typed transformation representing f: A -> B"""
    signature: Tuple[str, str]  # (domain, codomain)
    transform: Callable[[A], B]
    label: str
    
    def compose(self, other: 'Morphism[B, C]') -> 'Morphism[A, C]':
        """Morphism composition: (g ∘ f)(x) = g(f(x))"""
        if self.signature[1] != other.signature[0]:
            raise TypeError(f"Type mismatch: {self.signature[1]} ≠ {other.signature[0]}")
        return Morphism(
            signature=(self.signature[0], other.signature[1]),
            transform=lambda x: other.transform(self.transform(x)),
            label=f"({other.label} ∘ {self.label})"
        )
    
    def __rshift__(self, other):
        """Infix composition: f >> g"""
        return self.compose(other)

@dataclass(frozen=True)
class Pipeline:
    """A composable pipeline of morphisms forming a category"""
    morphisms: Tuple[Morphism, ...]
    
    def __init__(self, *morphisms):
        object.__setattr__(self, 'morphisms', morphisms)
    
    @property
    def composite(self) -> Morphism:
        """Reduce pipeline to single morphism via composition"""
        if not self.morphisms:
            raise ValueError("Empty pipeline")
        return reduce(lambda f, g: f >> g, self.morphisms)
    
    @property
    def type_path(self) -> List[str]:
        """Extract type flow: A -> B -> C -> D"""
        if not self.morphisms:
            return []
        path = [self.morphisms[0].signature[0]]
        path.extend(m.signature[1] for m in self.morphisms)
        return path
    
    def validate(self) -> bool:
        """Verify compositional type safety without execution"""
        for i in range(len(self.morphisms) - 1):
            if self.morphisms[i].signature[1] != self.morphisms[i + 1].signature[0]:
                return False
        return True
    
    def apply(self, input_data: Any) -> Any:
        """Execute the pipeline (optional—reasoning doesn't require this)"""
        return self.composite.transform(input_data)

def identity(type_name: str) -> Morphism:
    """Identity morphism: id_A : A -> A"""
    return Morphism((type_name, type_name), lambda x: x, f"id_{type_name}")

# Example usage demonstrating algebraic reasoning
if __name__ == "__main__":
    parse = Morphism(("str", "dict"), eval, "parse")
    extract = Morphism(("dict", "list"), lambda d: list(d.values()), "extract")
    count = Morphism(("list", "int"), len, "count")
    
    pipeline = Pipeline(parse, extract, count)
    print(f"Type flow: {' -> '.join(pipeline.type_path)}")
    print(f"Valid: {pipeline.validate()}")
    print(f"Composite: {pipeline.composite.label}")