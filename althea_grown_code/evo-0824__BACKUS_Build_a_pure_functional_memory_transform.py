#!/usr/bin/env python3
"""functional_memory_algebra.py - Declarative memory transformations"""

from functools import reduce
from typing import Callable, List, Dict, Any, Tuple
import hashlib
import json

# Pure functions - no side effects, composable algebraic operations

def hash_memory(mem: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """mem -> (fingerprint, mem)"""
    content = json.dumps(mem.get('content', ''), sort_keys=True)
    fingerprint = hashlib.blake2b(content.encode(), digest_size=16).hexdigest()
    return (fingerprint, {**mem, 'fingerprint': fingerprint})

def extract_pattern(mem: Tuple[str, Dict[str, Any]]) -> Tuple[str, str]:
    """(fingerprint, mem) -> (fingerprint, pattern_type)"""
    fp, m = mem
    pattern = m.get('type', 'UNKNOWN')
    return (fp, pattern)

def group_by_pattern(acc: Dict[str, List[str]], item: Tuple[str, str]) -> Dict[str, List[str]]:
    """Reducer: accumulate fingerprints by pattern type"""
    fp, pattern = item
    acc.setdefault(pattern, []).append(fp)
    return acc

def compose(*fns: Callable) -> Callable:
    """f ∘ g ∘ h - right to left composition"""
    return reduce(lambda f, g: lambda x: f(g(x)), fns, lambda x: x)

def pipe(*fns: Callable) -> Callable:
    """h |> g |> f - left to right pipeline"""
    return reduce(lambda f, g: lambda x: g(f(x)), fns, lambda x: x)

# Algebraic memory pipeline
def analyze_memory_stream(memories: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Pure transformation: memories -> structural analysis"""
    
    # map-reduce pipeline
    fingerprinted = list(map(hash_memory, memories))
    patterns = list(map(extract_pattern, fingerprinted))
    grouped = reduce(group_by_pattern, patterns, {})
    
    # Compute pattern algebra
    duplicates = {p: fps for p, fps in grouped.items() if len(fps) != len(set(fps))}
    unique_count = sum(len(set(fps)) for fps in grouped.values())
    
    return {
        'total': len(memories),
        'unique': unique_count,
        'patterns': {p: len(set(fps)) for p, fps in grouped.items()},
        'duplicates': {p: len(fps) - len(set(fps)) for p, fps in duplicates.items()},
        'compression_ratio': unique_count / len(memories) if memories else 1.0
    }

# Export pure transform
transform_memories = analyze_memory_stream