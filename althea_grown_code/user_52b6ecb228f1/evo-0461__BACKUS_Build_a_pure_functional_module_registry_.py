from typing import Callable, TypeVar, Generic, Tuple, Optional
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Morphism(Generic[A, B]):
    """A pure transformation with explicit domain and codomain."""
    name: str
    domain: str
    codomain: str
    transform: Callable[[A], B]
    
    def __call__(self, x: A) -> B:
        return self.transform(x)
    
    def compose(self, other: 'Morphism[B, C]') -> 'Morphism[A, C]':
        """Composition law: (g ∘ f)(x) = g(f(x))"""
        if self.codomain != other.domain:
            raise TypeError(f"Cannot compose: {self.codomain} ≠ {other.domain}")
        return Morphism(
            name=f"{other.name}∘{self.name}",
            domain=self.domain,
            codomain=other.codomain,
            transform=lambda x: other.transform(self.transform(x))
        )
    
    def __matmul__(self, other: 'Morphism') -> 'Morphism':
        """Operator overload: g @ f means g ∘ f"""
        return self.compose(other)

class FunctionalRegistry:
    """Registry of modules as morphisms with algebraic composition."""
    
    def __init__(self):
        self.morphisms: dict[str, Morphism] = {}
        self._register_identity()
    
    def _register_identity(self):
        """Identity morphism: id(x) = x (category law)"""
        for domain in ["state", "signal", "concept", "code"]:
            self.morphisms[f"id_{domain}"] = Morphism(
                name=f"id_{domain}",
                domain=domain,
                codomain=domain,
                transform=lambda x: x
            )
    
    def register(self, morph: Morphism) -> None:
        self.morphisms[morph.name] = morph
    
    def compose_chain(self, *names: str) -> Optional[Morphism]:
        """Compose multiple morphisms left-to-right: f;g;h"""
        morphs = [self.morphisms.get(n) for n in names]
        if not all(morphs):
            return None
        return reduce(lambda f, g: f.compose(g), morphs)
    
    def verify_laws(self, f_name: str) -> dict[str, bool]:
        """Verify category laws for a morphism."""
        f = self.morphisms.get(f_name)
        if not f:
            return {}
        
        id_left = f"id_{f.domain}"
        id_right = f"id_{f.codomain}"
        
        # Left identity: id ∘ f = f
        # Right identity: f ∘ id = f
        test_val = "test"
        laws = {}
        
        if id_left in self.morphisms:
            left_comp = self.morphisms[id_left].compose(f)
            laws["left_identity"] = left_comp(test_val) == f(test_val)
        
        if id_right in self.morphisms:
            right_comp = f.compose(self.morphisms[id_right])
            laws["right_identity"] = right_comp(test_val) == f(test_val)
        
        return laws

REGISTRY = FunctionalRegistry()