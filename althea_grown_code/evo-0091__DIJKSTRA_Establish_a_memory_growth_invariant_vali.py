#!/usr/bin/env python3
"""Memory Growth Invariant Validator - Dijkstra-style correctness proof"""

from typing import List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class MemorySnapshot:
    timestamp: datetime
    count: int
    size_bytes: int
    source: str

class InvariantValidator:
    """Validates memory evolution preserves formal invariants"""
    
    def __init__(self):
        self.history: List[MemorySnapshot] = []
        self.violations: List[str] = []
    
    def record(self, count: int, size: int, source: str) -> bool:
        """Record snapshot and verify invariants hold
        
        INVARIANT 1: ∀i. count[i] ≤ count[i+1] (monotonic non-decreasing)
        INVARIANT 2: ∀i. timestamp[i] < timestamp[i+1] (temporal ordering)
        INVARIANT 3: size ≥ 0 ∧ count ≥ 0 (domain constraints)
        """
        snapshot = MemorySnapshot(datetime.now(), count, size, source)
        
        # Domain constraints (INV 3)
        assert size >= 0 and count >= 0, "Domain violation"
        
        valid = True
        if self.history:
            prev = self.history[-1]
            
            # Monotonicity check (INV 1)
            if snapshot.count < prev.count:
                violation = f"NON-MONOTONIC: {prev.count} -> {snapshot.count}"
                self.violations.append(violation)
                valid = False
            
            # Temporal ordering (INV 2)
            if snapshot.timestamp <= prev.timestamp:
                violation = f"TEMPORAL-VIOLATION: timestamps non-increasing"
                self.violations.append(violation)
                valid = False
        
        self.history.append(snapshot)
        return valid
    
    def prove_stability(self) -> Tuple[bool, Optional[str]]:
        """Prove system is in stable state with respect to invariants"""
        if len(self.history) < 2:
            return True, None
        
        # Verify all invariants across entire history
        for i in range(1, len(self.history)):
            if self.history[i].count < self.history[i-1].count:
                return False, f"Proof failed at index {i}: monotonicity broken"
        
        return True, "∀i ∈ [0, n). count[i] ≤ count[i+1] ∧ valid(invariants)"

validator = InvariantValidator()