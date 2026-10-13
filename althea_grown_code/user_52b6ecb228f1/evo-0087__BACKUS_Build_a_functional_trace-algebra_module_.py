#!/usr/bin/env python3
"""trace_algebra.py - Functional composition for memory trace reasoning"""

from typing import Callable, List, TypeVar, Tuple, Any
from functools import reduce
from dataclasses import dataclass
import re

A = TypeVar('A')
B = TypeVar('B')

@dataclass(frozen=True)
class Trace:
    """Immutable trace element"""
    type: str
    content: str
    metadata: tuple
    
    def map(self, f: Callable[[str], str]) -> 'Trace':
        return Trace(self.type, f(self.content), self.metadata)

def compose(*fns: Callable) -> Callable:
    """Right-to-left function composition: compose(f, g)(x) = f(g(x))"""
    return reduce(lambda f, g: lambda x: f(g(x)), fns, lambda x: x)

def lift(f: Callable[[A], B]) -> Callable[[Trace], Trace]:
    """Lift function to operate on Trace functor"""
    return lambda t: t.map(f)

def extract_pattern(pattern: str) -> Callable[[str], List[str]]:
    """Extract regex pattern (returns list for flatMap compatibility)"""
    return lambda s: re.findall(pattern, s)

def parse_memory(line: str) -> Trace:
    """Parse memory line into Trace"""
    parts = line.split()
    return Trace(
        type=parts[0].strip('[]'),
        content=' '.join(parts[1:]),
        metadata=tuple(re.findall(r'\w+=\w+', line))
    )

def sequence_coherence(traces: List[Trace]) -> float:
    """Measure algebraic coherence: ratio of preserved structure under composition"""
    if len(traces) < 2:
        return 1.0
    
    transitions = [(traces[i].type, traces[i+1].type) for i in range(len(traces)-1)]
    unique_transitions = len(set(transitions))
    total_transitions = len(transitions)
    
    return 1.0 - (unique_transitions / (total_transitions + 1))

def find_invariants(traces: List[Trace]) -> List[str]:
    """Extract invariant properties across trace transformations"""
    if not traces:
        return []
    
    common_meta = set(traces[0].metadata)
    for trace in traces[1:]:
        common_meta &= set(trace.metadata)
    
    return sorted(list(common_meta))

def compose_trace_analysis(*analyzers: Callable[[List[Trace]], Any]) -> Callable[[List[Trace]], Tuple]:
    """Compose multiple trace analyzers into single algebraic operation"""
    return lambda traces: tuple(a(traces) for a in analyzers)

# Algebraic trace pipeline
analyze_traces = compose_trace_analysis(
    sequence_coherence,
    find_invariants,
    lambda ts: len(ts)
)