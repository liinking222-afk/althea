#!/usr/bin/env python3
from typing import Callable, List, Tuple, Any
from functools import reduce
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Memory:
    content: str
    type: str
    
    def __repr__(self):
        return f"M({self.type}:{self.content[:30]})"

# Pure functions - no side effects
def identity(m: Memory) -> Memory:
    return m

def extract_type(m: Memory) -> Memory:
    if m.type != "raw":
        return m
    patterns = [
        (r'\[EVO #\d+', 'evolution'),
        (r'\[GROWTH', 'growth'),
        (r'\[SYSTEM', 'system'),
        (r'^-\s*Hello', 'greeting')
    ]
    for pattern, typ in patterns:
        if re.search(pattern, m.content):
            return Memory(m.content, typ)
    return m

def extract_archetype(m: Memory) -> Memory:
    match = re.search(r'\[EVO #\d+ (\w+)', m.content)
    if match:
        return Memory(m.content, f"{m.type}:{match.group(1).lower()}")
    return m

def normalize_whitespace(m: Memory) -> Memory:
    return Memory(' '.join(m.content.split()), m.type)

# Compose functions right-to-left (mathematical composition)
def compose(*fns: Callable[[Memory], Memory]) -> Callable[[Memory], Memory]:
    return lambda x: reduce(lambda v, f: f(v), reversed(fns), x)

# Lift function to work on streams
def fmap(f: Callable[[Memory], Memory]) -> Callable[[List[Memory]], List[Memory]]:
    return lambda ms: [f(m) for m in ms]

# Algebraic fold - reduce stream to summary structure
def fold_types(ms: List[Memory]) -> dict:
    return reduce(
        lambda acc, m: {**acc, m.type: acc.get(m.type, 0) + 1},
        ms,
        {}
    )

# Build composable pipeline
pipeline = compose(
    extract_type,
    extract_archetype,
    normalize_whitespace
)

# Apply transformation across stream
def transform_stream(raw_memories: List[str]) -> Tuple[List[Memory], dict]:
    memories = [Memory(r, "raw") for r in raw_memories]
    transformed = fmap(pipeline)(memories)
    summary = fold_types(transformed)
    return transformed, summary

if __name__ == "__main__":
    test = [
        "Hello",
        "[EVO #251 WOZ v1.21.8→1.21.9] Build efficient hasher",
        "[GROWTH /latent-53c4c] Latent Faculty spawned"
    ]
    result, summary = transform_stream(test)
    for m in result:
        print(m)
    print(f"\nAlgebraic summary: {summary}")