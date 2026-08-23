import functools
from typing import Callable, Any, TypeVar, List, Tuple
from dataclasses import dataclass

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Transform:
    """Immutable transformation with algebraic properties"""
    name: str
    func: Callable
    
    def __rshift__(self, other: 'Transform') -> 'Transform':
        """Compose transforms: f >> g means g(f(x))"""
        return Transform(
            name=f"{self.name}⊚{other.name}",
            func=lambda x: other.func(self.func(x))
        )
    
    def __call__(self, x: Any) -> Any:
        return self.func(x)

class Pipeline:
    """Declarative pipeline builder with algebraic laws"""
    
    @staticmethod
    def identity() -> Transform:
        """Identity transform: id >> f = f >> id = f"""
        return Transform("id", lambda x: x)
    
    @staticmethod
    def map(f: Callable[[A], B]) -> Transform:
        """Lift function to transform"""
        return Transform(f"map({f.__name__})", lambda xs: [f(x) for x in xs])
    
    @staticmethod
    def filter(pred: Callable[[A], bool]) -> Transform:
        """Filter transform"""
        return Transform(f"filter({pred.__name__})", lambda xs: [x for x in xs if pred(x)])
    
    @staticmethod
    def reduce(f: Callable[[A, B], A], init: A) -> Transform:
        """Reduce transform"""
        return Transform(f"reduce({f.__name__})", lambda xs: functools.reduce(f, xs, init))
    
    @staticmethod
    def tap(f: Callable[[A], None]) -> Transform:
        """Side-effect without mutation (for logging/observation)"""
        return Transform(f"tap({f.__name__})", lambda x: (f(x), x)[1])
    
    @staticmethod
    def validate(laws: List[Tuple[str, Callable[[Transform], bool]]]) -> bool:
        """Check algebraic laws hold for given transform"""
        return all(law[1](law[0]) for law in laws)

def memory_extract(pattern: str) -> Callable:
    return lambda mem: [m for m in mem if pattern in m.get('type', '')]

def memory_score(key: str) -> Callable:
    return lambda mem: sorted(mem, key=lambda m: m.get(key, 0), reverse=True)

# Example: declarative memory query pipeline
query = (
    Pipeline.filter(lambda m: m.get('timestamp', 0) > 1000) >>
    Pipeline.map(lambda m: {**m, 'relevance': len(m.get('content', ''))}) >>
    Pipeline.filter(lambda m: m['relevance'] > 10)
)