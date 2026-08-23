from dataclasses import dataclass
from typing import Callable, Any, TypeVar, Generic
from functools import reduce
import re
import inspect

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class ModuleAlgebra(Generic[A, B]):
    """A module as an algebraic object: pure transformation with signature"""
    name: str
    signature: tuple[type, type]  # (input_type, output_type)
    transform: Callable[[A], B]
    
    def compose(self, other: 'ModuleAlgebra[B, C]') -> 'ModuleAlgebra[A, C]':
        """Algebraic composition: g ∘ f"""
        if self.signature[1] != other.signature[0]:
            raise TypeError(f"Type mismatch: {self.signature[1]} != {other.signature[0]}")
        return ModuleAlgebra(
            name=f"{other.name}∘{self.name}",
            signature=(self.signature[0], other.signature[1]),
            transform=lambda x: other.transform(self.transform(x))
        )
    
    def __rshift__(self, other):
        """Infix operator: module_a >> module_b"""
        return self.compose(other)
    
    def identity_test(self) -> bool:
        """Check if module behaves as identity morphism"""
        test_vals = [None, 0, "", [], {}]
        return all(self.transform(v) == v for v in test_vals if isinstance(v, self.signature[0]))

def lift_function(name: str, fn: Callable[[A], B]) -> ModuleAlgebra[A, B]:
    """Lift ordinary function into algebraic module"""
    sig = inspect.signature(fn)
    params = list(sig.parameters.values())
    input_type = params[0].annotation if params else Any
    output_type = sig.return_annotation if sig.return_annotation != inspect.Signature.empty else Any
    return ModuleAlgebra(name, (input_type, output_type), fn)

def parallel(*modules: ModuleAlgebra) -> ModuleAlgebra:
    """Combine modules that operate on same input (product in category theory)"""
    return ModuleAlgebra(
        name=f"⊗({','.join(m.name for m in modules)})",
        signature=(modules[0].signature[0], tuple),
        transform=lambda x: tuple(m.transform(x) for m in modules)
    )

def pipeline(*modules: ModuleAlgebra) -> ModuleAlgebra:
    """Sequential composition (multiple module chain)"""
    return reduce(lambda acc, m: acc.compose(m), modules)

def discover_composition_laws(module: ModuleAlgebra, test_input: Any) -> dict:
    """Reason about algebraic properties"""
    return {
        "is_idempotent": module.transform(module.transform(test_input)) == module.transform(test_input),
        "composition_count": module.name.count('∘'),
        "is_identity": module.identity_test() if hasattr(test_input, '__class__') else None
    }