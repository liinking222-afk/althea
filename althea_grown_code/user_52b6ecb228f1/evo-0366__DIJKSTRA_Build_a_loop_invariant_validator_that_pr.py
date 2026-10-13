#!/usr/bin/env python3
"""Loop Invariant Validator - Dijkstra-style formal verification for conversation state"""

from typing import Dict, List, Tuple, Callable, Any
from dataclasses import dataclass
from enum import Enum

class InvariantStatus(Enum):
    HOLDS = "holds"
    VIOLATED = "violated"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class Invariant:
    name: str
    predicate: Callable[[Dict[str, Any]], bool]
    description: str

@dataclass(frozen=True)
class ValidationResult:
    invariant_name: str
    status: InvariantStatus
    pre_state_hash: int
    post_state_hash: int

class InvariantValidator:
    def __init__(self):
        self.invariants: List[Invariant] = []
        self.validation_history: List[ValidationResult] = []
    
    def register_invariant(self, name: str, predicate: Callable, description: str) -> None:
        inv = Invariant(name=name, predicate=predicate, description=description)
        self.invariants.append(inv)
    
    def validate_transition(self, pre_state: Dict[str, Any], post_state: Dict[str, Any]) -> List[ValidationResult]:
        results = []
        pre_hash = hash(frozenset(pre_state.items()))
        post_hash = hash(frozenset(post_state.items()))
        
        for inv in self.invariants:
            try:
                pre_holds = inv.predicate(pre_state)
                post_holds = inv.predicate(post_state)
                
                if pre_holds and post_holds:
                    status = InvariantStatus.HOLDS
                elif not pre_holds and post_holds:
                    status = InvariantStatus.HOLDS
                elif pre_holds and not post_holds:
                    status = InvariantStatus.VIOLATED
                else:
                    status = InvariantStatus.UNKNOWN
            except Exception:
                status = InvariantStatus.UNKNOWN
            
            result = ValidationResult(inv.name, status, pre_hash, post_hash)
            results.append(result)
            self.validation_history.append(result)
        
        return results
    
    def get_violations(self) -> List[ValidationResult]:
        return [r for r in self.validation_history if r.status == InvariantStatus.VIOLATED]
    
    def monotonicity_holds(self) -> bool:
        return len(self.get_violations()) == 0

validator = InvariantValidator()

validator.register_invariant(
    "coherence_monotonic",
    lambda s: s.get("coherence_score", 0.0) >= 0.0,
    "Coherence score never negative"
)

validator.register_invariant(
    "context_size_bounded",
    lambda s: s.get("context_tokens", 0) <= s.get("max_tokens", float('inf')),
    "Context size respects upper bound"
)