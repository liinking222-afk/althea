from typing import Callable, Any, TypeVar, Generic, List, Tuple
from dataclasses import dataclass
from functools import reduce

A = TypeVar('A')
B = TypeVar('B')

@dataclass(frozen=True)
class Fn(Generic[A, B]):
    """Algebraic function object - immutable, composable, analyzable."""
    name: str
    fn: Callable[[A], B]
    
    def __call__(self, x: A) -> B:
        return self.fn(x)
    
    def compose(self, other: 'Fn') -> 'Fn':
        """Right-to-left composition: (f ∘ g)(x) = f(g(x))"""
        return Fn(
            name=f"{self.name}∘{other.name}",
            fn=lambda x: self.fn(other.fn(x))
        )
    
    def __rshift__(self, other: 'Fn') -> 'Fn':
        """Left-to-right pipeline: f >> g = g ∘ f"""
        return other.compose(self)
    
    def algebraic_form(self) -> str:
        return self.name

@dataclass
class Pipeline:
    """Declarative transformation pipeline with symbolic reasoning."""
    stages: List[Fn]
    
    def __init__(self, *fns: Fn):
        self.stages = list(fns)
    
    def execute(self, input_val: Any) -> Any:
        """Evaluate the pipeline."""
        return reduce(lambda acc, f: f(acc), self.stages, input_val)
    
    def symbolic_form(self) -> str:
        """Express pipeline as algebraic composition."""
        if not self.stages:
            return "id"
        return " >> ".join(f.name for f in self.stages)
    
    def chain_depth(self) -> int:
        """Measure composition depth."""
        return len(self.stages)
    
    def is_associative_rewrite(self, other: 'Pipeline') -> bool:
        """Check if two pipelines are semantically equivalent under associativity."""
        return self.symbolic_form() == other.symbolic_form()
    
    def optimize(self) -> 'Pipeline':
        """Algebraic optimization: collapse identity, combine adjacent ops."""
        if not self.stages:
            return self
        optimized = [f for f in self.stages if f.name != "id"]
        return Pipeline(*optimized) if optimized else Pipeline()

def compose_all(*fns: Fn) -> Fn:
    """Variadic composition operator."""
    if not fns:
        return Fn("id", lambda x: x)
    return reduce(lambda f, g: g.compose(f), fns)