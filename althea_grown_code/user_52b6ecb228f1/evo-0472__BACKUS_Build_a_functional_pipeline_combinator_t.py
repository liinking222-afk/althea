from typing import TypeVar, Callable, Generic, Any, Tuple
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Transform(Generic[A, B]):
    """An algebraic transformation with provenance."""
    fn: Callable[[A], B]
    signature: str
    lineage: Tuple[str, ...]
    
    def __call__(self, x: A) -> B:
        return self.fn(x)
    
    def __rshift__(self, other: 'Transform[B, C]') -> 'Transform[A, C]':
        """Compose transforms algebraically: f >> g == g ∘ f"""
        return Transform(
            fn=lambda x: other.fn(self.fn(x)),
            signature=f"{self.signature} → {other.signature}",
            lineage=self.lineage + other.lineage
        )
    
    def trace(self) -> str:
        """Show transformation ancestry."""
        return " >> ".join(self.lineage)

def lift(name: str, sig: str) -> Callable[[Callable[[A], B]], Transform[A, B]]:
    """Lift a pure function into the Transform algebra."""
    def decorator(fn: Callable[[A], B]) -> Transform[A, B]:
        return Transform(fn=fn, signature=sig, lineage=(name,))
    return decorator

@lift("parse_int", "str → int")
def parse_int(s: str) -> int:
    return int(s)

@lift("square", "int → int")
def square(n: int) -> int:
    return n * n

@lift("stringify", "int → str")
def stringify(n: int) -> str:
    return f"Result: {n}"

def pipeline(*transforms: Transform) -> Transform:
    """Reduce sequence of transforms to single algebraic object."""
    return reduce(lambda f, g: f >> g, transforms)

if __name__ == "__main__":
    composed = parse_int >> square >> stringify
    print(f"Pipeline: {composed.trace()}")
    print(f"Signature: {composed.signature}")
    print(f"Execute('5'): {composed('5')}")
    
    multi = pipeline(parse_int, square, square, stringify)
    print(f"\nMulti: {multi.trace()}")
    print(f"Execute('3'): {multi('3')}")