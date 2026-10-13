from typing import Callable, List, Dict, Any, Tuple
from functools import reduce
from dataclasses import dataclass

@dataclass(frozen=True)
class MemoryQuery:
    """Immutable query as algebraic object"""
    transform: Callable[[List[Dict[str, Any]]], List[Dict[str, Any]]]
    
    def __call__(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return self.transform(memories)
    
    def __rshift__(self, other: 'MemoryQuery') -> 'MemoryQuery':
        """Compose queries using >> operator (function composition)"""
        return MemoryQuery(lambda m: other.transform(self.transform(m)))
    
    def __and__(self, other: 'MemoryQuery') -> 'MemoryQuery':
        """Parallel application, merge results"""
        return MemoryQuery(lambda m: self.transform(m) + other.transform(m))

# Pure query constructors (no side effects)
def filter_by(predicate: Callable[[Dict], bool]) -> MemoryQuery:
    return MemoryQuery(lambda ms: [m for m in ms if predicate(m)])

def map_field(fn: Callable[[Dict], Dict]) -> MemoryQuery:
    return MemoryQuery(lambda ms: [fn(m) for m in ms])

def take(n: int) -> MemoryQuery:
    return MemoryQuery(lambda ms: ms[:n])

def group_by(key: str) -> MemoryQuery:
    def grouping(ms):
        groups = {}
        for m in ms:
            k = m.get(key, 'unknown')
            groups.setdefault(k, []).append(m)
        return [{'key': k, 'items': v} for k, v in groups.items()]
    return MemoryQuery(grouping)

def extract(key: str) -> MemoryQuery:
    return MemoryQuery(lambda ms: [m.get(key) for m in ms if key in m])

def deduplicate_by(key: str) -> MemoryQuery:
    def dedup(ms):
        seen = set()
        result = []
        for m in ms:
            val = m.get(key)
            if val not in seen:
                seen.add(val)
                result.append(m)
        return result
    return MemoryQuery(dedup)

# Query algebra allows formal reasoning:
# Q1 >> Q2 >> Q3 is associative
# Identity query: MemoryQuery(lambda m: m)
# Laws can be proven algebraically before execution

def identity() -> MemoryQuery:
    return MemoryQuery(lambda m: m)

def compose(*queries: MemoryQuery) -> MemoryQuery:
    return reduce(lambda q1, q2: q1 >> q2, queries, identity())