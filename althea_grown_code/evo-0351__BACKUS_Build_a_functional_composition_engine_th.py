#!/usr/bin/env python3
"""Functional composition engine for module evolution chains."""

from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple
from functools import reduce
import re

@dataclass(frozen=True)
class ModuleTransform:
    """Immutable algebraic representation of a module evolution."""
    version_from: str
    version_to: str
    archetype: str
    intent: str
    
    def __rshift__(self, other: 'ModuleTransform') -> Optional['ModuleTransform']:
        """Compose transformations if compatible (versions align)."""
        if self.version_to == other.version_from:
            return ModuleTransform(
                self.version_from, other.version_to,
                f"{self.archetype}∘{other.archetype}",
                f"{self.intent} THEN {other.intent}"
            )
        return None
    
    def inverse(self) -> 'ModuleTransform':
        """Return inverse transformation."""
        return ModuleTransform(self.version_to, self.version_from, 
                             f"¬{self.archetype}", f"REVERT: {self.intent}")

def parse_evolution(log_line: str) -> Optional[ModuleTransform]:
    """Parse evolution log into algebraic form."""
    match = re.search(r'\[EVO #\d+ (\w+) v([\d.]+)→([\d.]+)\] (.+?) —', log_line)
    if match:
        return ModuleTransform(match.group(2), match.group(3), 
                             match.group(1), match.group(4))
    return None

def compose_chain(transforms: List[ModuleTransform]) -> Optional[ModuleTransform]:
    """Reduce list of transformations to single composed transform."""
    def comp(acc, t):
        return acc >> t if acc else t
    return reduce(comp, transforms, None)

def find_paths(start: str, end: str, transforms: List[ModuleTransform]) -> List[List[ModuleTransform]]:
    """Find all composition paths from start to end version."""
    paths = []
    def search(current: str, path: List[ModuleTransform]):
        if current == end:
            paths.append(path[:])
            return
        for t in transforms:
            if t.version_from == current and t not in path:
                path.append(t)
                search(t.version_to, path)
                path.pop()
    search(start, [])
    return paths

def verify_associativity(t1: ModuleTransform, t2: ModuleTransform, t3: ModuleTransform) -> bool:
    """Verify (f∘g)∘h == f∘(g∘h) for given transforms."""
    left = (t1 >> t2) >> t3 if t1 >> t2 else None
    right = t1 >> (t2 >> t3) if t2 >> t3 else None
    return left == right if left and right else False

if __name__ == "__main__":
    import sys
    transforms = [parse_evolution(line) for line in sys.stdin if '[EVO' in line]
    transforms = [t for t in transforms if t]
    
    for t in transforms:
        print(f"{t.version_from}→{t.version_to} [{t.archetype}]")
    
    if len(transforms) >= 2:
        composed = compose_chain(transforms)
        if composed:
            print(f"\nCOMPOSED: {composed.version_from}→{composed.version_to}")