from typing import Callable, List, TypeVar, Generic
from functools import reduce
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

@dataclass(frozen=True)
class Memory:
    category: str
    content: str
    metadata: dict

    def __repr__(self):
        return f"Memory({self.category}, {self.content[:40]}...)"

class MemoryPipeline(Generic[T]):
    """Immutable functional pipeline for memory transformations."""
    
    def __init__(self, data: List[T]):
        self._data = tuple(data)  # Immutable
    
    def map(self, f: Callable[[T], U]) -> 'MemoryPipeline[U]':
        """Transform each element. Functor."""
        return MemoryPipeline(tuple(f(x) for x in self._data))
    
    def filter(self, predicate: Callable[[T], bool]) -> 'MemoryPipeline[T]':
        """Select elements matching predicate."""
        return MemoryPipeline(tuple(x for x in self._data if predicate(x)))
    
    def reduce(self, f: Callable[[U, T], U], initial: U) -> U:
        """Fold the pipeline into a single value."""
        return reduce(f, self._data, initial)
    
    def flatMap(self, f: Callable[[T], List[U]]) -> 'MemoryPipeline[U]':
        """Map then flatten. Monad bind."""
        return MemoryPipeline(tuple(item for x in self._data for item in f(x)))
    
    def compose(self, *transforms: Callable[['MemoryPipeline[T]'], 'MemoryPipeline']) -> 'MemoryPipeline':
        """Compose multiple transformations algebraically."""
        return reduce(lambda pipeline, f: f(pipeline), transforms, self)
    
    def value(self) -> tuple:
        """Extract the immutable result."""
        return self._data
    
    def __len__(self):
        return len(self._data)

# Algebraic combinators
def growth_only(pipeline: MemoryPipeline[Memory]) -> MemoryPipeline[Memory]:
    return pipeline.filter(lambda m: m.category == "GROWTH")

def recent_n(n: int):
    def _recent(pipeline: MemoryPipeline[Memory]) -> MemoryPipeline[Memory]:
        return MemoryPipeline(pipeline.value()[-n:])
    return _recent

def extract_patterns(pipeline: MemoryPipeline[Memory]) -> MemoryPipeline[str]:
    return pipeline.map(lambda m: m.content.split()[0] if m.content else "")

# Pure reasoning: declarative query composition
def analyze_memory_stream(memories: List[Memory]) -> dict:
    pipeline = MemoryPipeline(memories)
    
    analysis = pipeline.compose(
        growth_only,
        recent_n(5)
    )
    
    pattern_freq = (
        extract_patterns(analysis)
        .reduce(lambda acc, p: {**acc, p: acc.get(p, 0) + 1}, {})
    )
    
    return {"count": len(analysis), "patterns": pattern_freq, "memories": analysis.value()}