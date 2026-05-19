#!/usr/bin/env python3
"""
Memory Invariant Validator - Dijkstra-style formal correctness for memory traces
Ensures: monotonic counters, bounded size variance, structural consistency
"""

from typing import Dict, Optional, Tuple
from dataclasses import dataclass

@dataclass(frozen=True)
class MemoryInvariant:
    """Immutable invariant state - no side effects"""
    min_size: int
    max_size: int
    last_count: int
    expected_size: int
    tolerance: float
    
    @staticmethod
    def initial(size: int) -> 'MemoryInvariant':
        return MemoryInvariant(size, size, -1, size, 0.15)

class MemoryValidator:
    """Validates memory entries against formal invariants"""
    
    def __init__(self):
        self._invariants: Dict[str, MemoryInvariant] = {}
    
    def validate(self, source: str, size: Tuple[int, int], 
                 memory_count: int, byte_size: int) -> Tuple[bool, str]:
        """
        PRE: memory_count >= 0, byte_size > 0, size components > 0
        POST: returns (valid, reason) where valid implies all invariants hold
        INVARIANT: memory_count is strictly monotonic per source
        """
        key = f"{source}_{size[0]}x{size[1]}"
        
        if key not in self._invariants:
            self._invariants[key] = MemoryInvariant.initial(byte_size)
            return (True, "initial")
        
        inv = self._invariants[key]
        
        # INVARIANT 1: Monotonic memory count (Dijkstra: no backward time)
        if memory_count <= inv.last_count:
            return (False, f"non_monotonic: {memory_count} <= {inv.last_count}")
        
        # INVARIANT 2: Bounded size variance (stability)
        min_allowed = inv.expected_size * (1 - inv.tolerance)
        max_allowed = inv.expected_size * (1 + inv.tolerance)
        if not (min_allowed <= byte_size <= max_allowed):
            return (False, f"size_violation: {byte_size} not in [{min_allowed:.0f}, {max_allowed:.0f}]")
        
        # Update invariants (pure functional update)
        new_min = min(inv.min_size, byte_size)
        new_max = max(inv.max_size, byte_size)
        new_expected = (inv.expected_size * 0.9) + (byte_size * 0.1)  # EMA
        
        self._invariants[key] = MemoryInvariant(
            new_min, new_max, memory_count, int(new_expected), inv.tolerance
        )
        
        return (True, "valid")
    
    def get_invariant_state(self, source: str, size: Tuple[int, int]) -> Optional[MemoryInvariant]:
        """Query invariant - read-only"""
        return self._invariants.get(f"{source}_{size[0]}x{size[1]}")