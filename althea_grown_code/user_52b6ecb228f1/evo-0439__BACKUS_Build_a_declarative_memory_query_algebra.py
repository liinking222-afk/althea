from typing import Callable, Any, List, Dict, TypeVar, Generic
from functools import reduce
from dataclasses import dataclass

T = TypeVar('T')
U = TypeVar('U')

@dataclass
class Query(Generic[T]):
    """Algebraic query object - immutable, composable, lazily evaluated"""
    memories: List[T]
    
    def filter(self, predicate: Callable[[T], bool]) -> 'Query[T]':
        return Query([m for m in self.memories if predicate(m)])
    
    def map(self, transform: Callable[[T], U]) -> 'Query[U]':
        return Query([transform(m) for m in self.memories])
    
    def fold(self, combiner: Callable[[U, T], U], initial: U) -> U:
        return reduce(combiner, self.memories, initial)
    
    def take(self, n: int) -> 'Query[T]':
        return Query(self.memories[:n])
    
    def sort_by(self, key: Callable[[T], Any], reverse: bool = False) -> 'Query[T]':
        return Query(sorted(self.memories, key=key, reverse=reverse))
    
    def group_by(self, key: Callable[[T], str]) -> Dict[str, 'Query[T]']:
        groups: Dict[str, List[T]] = {}
        for m in self.memories:
            k = key(m)
            groups.setdefault(k, []).append(m)
        return {k: Query(v) for k, v in groups.items()}
    
    def exists(self, predicate: Callable[[T], bool]) -> bool:
        return any(predicate(m) for m in self.memories)
    
    def count(self) -> int:
        return len(self.memories)
    
    def compose(self, *transforms: Callable[['Query'], 'Query']) -> 'Query':
        return reduce(lambda q, f: f(q), transforms, self)
    
    def materialize(self) -> List[T]:
        return self.memories.copy()

def from_memories(memories: List[T]) -> Query[T]:
    return Query(memories)

# Algebraic laws demonstrable:
# Query(m).filter(p1).filter(p2) == Query(m).filter(lambda x: p1(x) and p2(x))
# Query(m).map(f).map(g) == Query(m).map(lambda x: g(f(x)))
# Query(m).take(n).take(k) == Query(m).take(min(n, k))

def example_cognitive_query(memories: List[Dict]) -> Dict[str, int]:
    """Growth pattern velocity analysis as pure function composition"""
    return (from_memories(memories)
            .filter(lambda m: m.get('type') in ['GROWTH', 'EVO'])
            .group_by(lambda m: m.get('type', 'UNKNOWN'))
            .items()
            |> dict
            |> {k: q.count() for k, q in _.items()})