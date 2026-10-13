#!/usr/bin/env python3
"""
invariant_verifier.py - Formal correctness checker for Althea module evolution
Enforces: Every module has precondition, postcondition, and invariant
"""

from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum

class InvariantStatus(Enum):
    HOLDS = "HOLDS"
    VIOLATED = "VIOLATED"
    UNKNOWN = "UNKNOWN"

@dataclass(frozen=True)
class ModuleInvariant:
    """Immutable specification of a module's correctness contract"""
    module_id: str
    precondition: Callable[[], bool]
    postcondition: Callable[[any], bool]
    invariant: Callable[[any], bool]
    
    def verify_evolution_step(self, old_state: any, new_state: any) -> InvariantStatus:
        """
        Verify: PRE ∧ TRANSFORM ⟹ POST ∧ INV
        Loop invariant must hold before and after any evolution step
        """
        if not self.precondition():
            return InvariantStatus.UNKNOWN
        
        inv_before = self.invariant(old_state) if old_state else True
        inv_after = self.invariant(new_state)
        post_holds = self.postcondition(new_state)
        
        if inv_before and inv_after and post_holds:
            return InvariantStatus.HOLDS
        return InvariantStatus.VIOLATED

class EvolutionVerifier:
    """Maintains formal correctness across Althea's self-modification cycles"""
    
    def __init__(self):
        self._invariants: dict[str, ModuleInvariant] = {}
        self._verification_log: list[tuple[str, InvariantStatus]] = []
    
    def register_invariant(self, inv: ModuleInvariant) -> None:
        """Register a module's correctness contract (idempotent)"""
        self._invariants[inv.module_id] = inv
    
    def verify_step(self, module_id: str, old_state: any, new_state: any) -> InvariantStatus:
        """Check invariant preservation across one evolution step"""
        if module_id not in self._invariants:
            return InvariantStatus.UNKNOWN
        
        inv = self._invariants[module_id]
        status = inv.verify_evolution_step(old_state, new_state)
        self._verification_log.append((module_id, status))
        return status
    
    def get_violation_count(self) -> int:
        """Count total invariant violations (monotonic)"""
        return sum(1 for _, status in self._verification_log 
                   if status == InvariantStatus.VIOLATED)
    
    def is_system_sound(self) -> bool:
        """System is sound iff no violations exist"""
        return self.get_violation_count() == 0

# Singleton verifier for global evolution tracking
_verifier = EvolutionVerifier()

def verify() -> EvolutionVerifier:
    return _verifier