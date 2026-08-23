from typing import Callable, Any, TypeVar, Generic, Union
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Fn(Generic[A, B]):
    """Immutable function wrapper enabling algebraic composition"""
    f: Callable[[A], B]
    name: str = "λ"
    
    def __call__(self, x: A) -> B:
        return self.f(x)
    
    def __rshift__(self, other: 'Fn[B, C]') -> 'Fn[A, C]':
        """Compose: (f >> g)(x) = g(f(x))"""
        return Fn(lambda x: other.f(self.f(x)), f"{self.name}⊳{other.name}")
    
    def __or__(self, other: 'Fn[A, B]') -> 'Fn[A, B]':
        """Parallel choice: try self, fallback to other"""
        def choice(x: A) -> B:
            try:
                return self.f(x)
            except:
                return other.f(x)
        return Fn(choice, f"{self.name}|{other.name}")
    
    def __mul__(self, n: int) -> 'Fn[A, B]':
        """Iterate n times"""
        return Fn(lambda x: reduce(lambda acc, _: self.f(acc), range(n), x), f"{self.name}^{n}")
    
    def trace(self) -> str:
        """Return symbolic representation"""
        return self.name
    
    def laws(self) -> dict:
        """Expose algebraic properties for reasoning"""
        return {
            "associative": True,
            "composable": True,
            "symbolic_form": self.name
        }

def identity() -> Fn[A, A]:
    return Fn(lambda x: x, "id")

def lift(f: Callable[[A], B], name: str = None) -> Fn[A, B]:
    return Fn(f, name or f.__name__)

# Example: declarative pipeline construction
if __name__ == "__main__":
    inc = lift(lambda x: x + 1, "inc")
    double = lift(lambda x: x * 2, "×2")
    pipeline = inc >> double >> inc
    
    print(f"Symbolic: {pipeline.trace()}")
    print(f"Execute: {pipeline(5)}")
    print(f"Laws: {pipeline.laws()}")