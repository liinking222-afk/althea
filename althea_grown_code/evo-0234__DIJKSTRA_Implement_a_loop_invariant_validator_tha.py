#!/usr/bin/env python3
"""Loop Invariant Validator - Dijkstra-style formal correctness for iteration"""

from dataclasses import dataclass
from typing import Callable, Any, Optional
from enum import Enum


class InvariantStatus(Enum):
    HOLDS = "invariant_holds"
    VIOLATED = "invariant_violated"
    UNPROVEN = "unproven"


@dataclass(frozen=True)
class LoopInvariant:
    """Immutable invariant specification with precondition, invariant, postcondition"""
    name: str
    precondition: Callable[[Any], bool]
    invariant: Callable[[Any, int], bool]  # state, iteration_count
    postcondition: Callable[[Any], bool]
    bound: Optional[int] = None  # termination bound


class InvariantValidator:
    """Validates loop correctness via explicit invariant checking"""
    
    def __init__(self):
        self.validation_log = []
    
    def verify_iteration(
        self, 
        invariant: LoopInvariant,
        initial_state: Any,
        step_function: Callable[[Any, int], Any],
        termination: Callable[[Any, int], bool]
    ) -> tuple[InvariantStatus, Any, list[str]]:
        """Execute iteration with invariant checking at each step"""
        
        # P: precondition must hold
        if not invariant.precondition(initial_state):
            return (InvariantStatus.VIOLATED, initial_state, 
                   [f"Precondition failed for {invariant.name}"])
        
        state = initial_state
        iteration = 0
        proof_trace = [f"P holds: {invariant.name}"]
        
        # I: invariant holds initially
        if not invariant.invariant(state, iteration):
            return (InvariantStatus.VIOLATED, state,
                   proof_trace + ["Invariant false at initialization"])
        
        proof_trace.append(f"I(0) holds")
        
        # Bounded iteration with invariant preservation
        while not termination(state, iteration):
            if invariant.bound and iteration >= invariant.bound:
                return (InvariantStatus.VIOLATED, state,
                       proof_trace + [f"Exceeded bound {invariant.bound}"])
            
            iteration += 1
            state = step_function(state, iteration)
            
            # I: invariant must hold after each step
            if not invariant.invariant(state, iteration):
                return (InvariantStatus.VIOLATED, state,
                       proof_trace + [f"Invariant violated at iteration {iteration}"])
            
            proof_trace.append(f"I({iteration}) holds")
        
        # Q: postcondition must hold upon termination
        if not invariant.postcondition(state):
            return (InvariantStatus.VIOLATED, state,
                   proof_trace + ["Postcondition failed"])
        
        proof_trace.append(f"Q holds after {iteration} iterations")
        self.validation_log.extend(proof_trace)
        
        return (InvariantStatus.HOLDS, state, proof_trace)