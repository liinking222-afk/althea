from functools import reduce
from typing import Callable, TypeVar, List, Dict, Any
from dataclasses import dataclass
from collections import Counter
import re

T = TypeVar('T')
U = TypeVar('U')

@dataclass(frozen=True)
class Pattern:
    """Immutable pattern as algebraic object"""
    name: str
    frequency: int
    window: tuple
    metadata: tuple
    
    def __hash__(self):
        return hash((self.name, self.frequency, self.window, self.metadata))

class PatternAlgebra:
    """Declarative pattern operations - composable, reasoning-friendly"""
    
    @staticmethod
    def parse(log_entry: str) -> Pattern:
        """Pure function: string -> Pattern"""
        match = re.search(r'\[AUTOSYNTH /(autonomous-[\w-]+)-(\d+)\] ([\w\s]+) \((\w+)\)\.', log_entry)
        if not match:
            return Pattern("unknown", 0, (0, 0), ())
        name, id_num, desc, category = match.groups()
        return Pattern(name, 1, (int(id_num), int(id_num)), (desc.strip(), category))
    
    @staticmethod
    def merge(p1: Pattern, p2: Pattern) -> Pattern:
        """Associative merge operation - pattern monoid"""
        if p1.name != p2.name:
            return p1
        return Pattern(
            p1.name,
            p1.frequency + p2.frequency,
            (min(p1.window[0], p2.window[0]), max(p1.window[1], p2.window[1])),
            p1.metadata
        )
    
    @staticmethod
    def identity() -> Pattern:
        """Identity element for merge monoid"""
        return Pattern("", 0, (float('inf'), 0), ())

def compose(*fns: Callable) -> Callable:
    """Right-to-left function composition"""
    return reduce(lambda f, g: lambda x: f(g(x)), fns, lambda x: x)

def analyze_patterns(logs: List[str]) -> Dict[str, Pattern]:
    """Declarative pipeline: parse -> group -> reduce"""
    patterns = list(filter(lambda p: p.name != "unknown", map(PatternAlgebra.parse, logs)))
    grouped = {}
    for p in patterns:
        grouped[p.name] = PatternAlgebra.merge(grouped.get(p.name, PatternAlgebra.identity()), p)
    return {k: v for k, v in grouped.items() if v.frequency > 0}

def top_k(patterns: Dict[str, Pattern], k: int = 3) -> List[Pattern]:
    """Pure selection function"""
    return sorted(patterns.values(), key=lambda p: p.frequency, reverse=True)[:k]

pipeline = compose(lambda ps: top_k(ps, 5), analyze_patterns)