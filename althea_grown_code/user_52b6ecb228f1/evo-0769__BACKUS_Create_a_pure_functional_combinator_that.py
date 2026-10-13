from typing import Callable, TypeVar, List, Tuple, Dict, Any
from functools import reduce
from dataclasses import dataclass

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')

@dataclass(frozen=True)
class Transform:
    """Immutable transformation as algebraic object"""
    name: str
    func: Callable[[Any], Any]
    
    def __rshift__(self, other: 'Transform') -> 'Transform':
        """Compose transformations: self >> other"""
        return Transform(
            name=f"({self.name} >> {other.name})",
            func=lambda x: other.func(self.func(x))
        )
    
    def __or__(self, other: 'Transform') -> 'Transform':
        """Parallel application: self | other returns tuple"""
        return Transform(
            name=f"({self.name} | {other.name})",
            func=lambda x: (self.func(x), other.func(x))
        )

def identity() -> Transform:
    return Transform("id", lambda x: x)

def filter_pattern(pattern: str) -> Transform:
    return Transform(
        f"filter({pattern})",
        lambda memories: [m for m in memories if pattern.lower() in str(m).lower()]
    )

def deduplicate() -> Transform:
    return Transform(
        "dedup",
        lambda items: list(dict.fromkeys(items))
    )

def frequency_collapse() -> Transform:
    return Transform(
        "freq_collapse",
        lambda items: {item: items.count(item) for item in set(items)}
    )

def extract_field(field: str) -> Transform:
    return Transform(
        f"extract({field})",
        lambda items: [item.get(field) if isinstance(item, dict) else getattr(item, field, None) for item in items]
    )

def compose(*transforms: Transform) -> Transform:
    """Right-to-left composition"""
    return reduce(lambda f, g: g >> f, reversed(transforms), identity())

def pipeline(*transforms: Transform) -> Transform:
    """Left-to-right pipeline (more intuitive)"""
    return reduce(lambda f, g: f >> g, transforms, identity())

# Example: declarative memory pipeline specification
memory_consolidation = pipeline(
    filter_pattern("AUTOSYNTH"),
    deduplicate(),
    frequency_collapse()
)

# Algebraic properties can be proven:
# (f >> g) >> h == f >> (g >> h)  [associativity]
# identity() >> f == f >> identity() == f  [identity]