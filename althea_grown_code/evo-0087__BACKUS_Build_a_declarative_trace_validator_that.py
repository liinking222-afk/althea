#!/usr/bin/env python3
"""
Functional trace coherence validator - memories as composable algebraic objects
"""

from typing import List, Dict, Any, Callable, Tuple
from functools import reduce
from dataclasses import dataclass

@dataclass(frozen=True)
class TracePoint:
    memory_count: int
    size_bytes: int
    source: str
    
    def __hash__(self):
        return hash((self.memory_count, self.size_bytes, self.source))

# Pure functions - no side effects, composable
def parse_trace(memory: str) -> TracePoint:
    """Extract algebraic structure from memory string"""
    parts = memory.split()
    mc = int([p.split('=')[1] for p in parts if 'memory_count=' in p][0])
    sb = int([p.split('(')[1].split()[0] for p in parts if 'bytes)' in p][0])
    src = [p.split('=')[1] for p in parts if 'source=' in p][0]
    return TracePoint(mc, sb, src)

def monotonic_check(t1: TracePoint, t2: TracePoint) -> bool:
    """Algebraic invariant: memory_count should form monotonic sequence"""
    return t1.memory_count >= t2.memory_count

def bounded_delta(t1: TracePoint, t2: TracePoint, max_delta: int = 5) -> bool:
    """Algebraic invariant: adjacent traces should not skip too many states"""
    return abs(t1.memory_count - t2.memory_count) <= max_delta

def source_consistency(traces: List[TracePoint]) -> bool:
    """Algebraic invariant: source identity preserved across composition"""
    sources = set(t.source for t in traces)
    return len(sources) == 1

# Compose invariants as algebraic operations
def pairwise_reduce(f: Callable[[TracePoint, TracePoint], bool], 
                   traces: List[TracePoint]) -> List[bool]:
    """Lift binary predicate to sequence via composition"""
    return [f(traces[i], traces[i+1]) for i in range(len(traces)-1)]

def validate_trace_coherence(memories: List[str]) -> Dict[str, Any]:
    """Main composition - pure data transformation pipeline"""
    traces = [parse_trace(m) for m in memories if 'memory_count=' in m]
    
    if len(traces) < 2:
        return {"coherent": True, "reason": "insufficient_data"}
    
    # Compose invariant checks algebraically
    checks = {
        "monotonic": all(pairwise_reduce(monotonic_check, traces)),
        "bounded": all(pairwise_reduce(bounded_delta, traces)),
        "source_stable": source_consistency(traces)
    }
    
    coherent = all(checks.values())
    violations = [k for k, v in checks.items() if not v]
    
    return {
        "coherent": coherent,
        "violations": violations,
        "trace_length": len(traces),
        "span": (traces[-1].memory_count, traces[0].memory_count)
    }

# Pure interface
def assess(memory_stream: List[str]) -> Dict[str, Any]:
    return validate_trace_coherence(memory_stream)