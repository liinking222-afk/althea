from typing import Callable, TypeVar, Generic, Any, Tuple
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Morphism(Generic[A, B]):
    """An algebraic morphism: a typed, composable transformation."""
    domain: type
    codomain: type
    transform: Callable[[A], B]
    label: str
    
    def __call__(self, x: A) -> B:
        return self.transform(x)
    
    def compose(self, other: 'Morphism[B, C]') -> 'Morphism[A, C]':
        """Categorical composition: (g ∘ f)(x) = g(f(x))"""
        if self.codomain != other.domain:
            raise TypeError(f"Type mismatch: {self.codomain} → {other.domain}")
        return Morphism(
            domain=self.domain,
            codomain=other.codomain,
            transform=lambda x: other.transform(self.transform(x)),
            label=f"({other.label} ∘ {self.label})"
        )
    
    def __rshift__(self, other: 'Morphism') -> 'Morphism':
        """Pipeline syntax: f >> g"""
        return self.compose(other)

class Pipeline:
    """Declarative computation pipeline with algebraic reasoning."""
    
    @staticmethod
    def identity(typ: type, label: str = "id") -> Morphism:
        """Identity morphism for any type."""
        return Morphism(typ, typ, lambda x: x, label)
    
    @staticmethod
    def lift(fn: Callable[[A], B], domain: type, codomain: type, label: str) -> Morphism[A, B]:
        """Lift a function into a morphism."""
        return Morphism(domain, codomain, fn, label)
    
    @staticmethod
    def chain(*morphisms: Morphism) -> Morphism:
        """Chain multiple morphisms left-to-right."""
        if not morphisms:
            raise ValueError("Cannot chain empty sequence")
        return reduce(lambda f, g: f.compose(g), morphisms)
    
    @staticmethod
    def parallel(f: Morphism[A, B], g: Morphism[C, Any]) -> Morphism[Tuple[A, C], Tuple[B, Any]]:
        """Parallel composition: (f × g)(a, c) = (f(a), g(c))"""
        return Morphism(
            domain=tuple,
            codomain=tuple,
            transform=lambda pair: (f(pair[0]), g(pair[1])),
            label=f"({f.label} × {g.label})"
        )
    
    @staticmethod
    def trace(m: Morphism) -> Morphism:
        """Add computational tracing without changing semantics."""
        def traced(x):
            result = m(x)
            print(f"[TRACE {m.label}] {m.domain.__name__} → {m.codomain.__name__}")
            return result
        return Morphism(m.domain, m.codomain, traced, f"trace({m.label})")

# Example module morphisms
def register_module_morphisms():
    return {
        'spectral': Pipeline.lift(lambda s: f"FFT({s})", str, str, "spectral"),
        'fractal': Pipeline.lift(lambda d: f"render({d})", dict, str, "fractal"),
        'infer': Pipeline.lift(lambda x: f"infer({x})", Any, list, "inference")
    }