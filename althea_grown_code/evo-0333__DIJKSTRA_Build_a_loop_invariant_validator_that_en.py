#!/usr/bin/env python3
"""Loop Invariant Validator - Dijkstra-style correctness for cognitive ops"""

import hashlib
import json
from typing import Any, Callable, Dict, Tuple
from dataclasses import dataclass, asdict


@dataclass
class StateContract:
    """Formal contract specifying valid state transitions"""
    precondition: Dict[str, Any]
    postcondition: Dict[str, Any]
    invariant: Dict[str, Any]
    
    def hash(self) -> str:
        canonical = json.dumps(asdict(self), sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


class InvariantValidator:
    def __init__(self):
        self.violations = []
        self.validated_ops = {}
    
    def check_predicate(self, state: Dict, predicate: Dict) -> Tuple[bool, str]:
        """Verify state satisfies predicate (simplified first-order logic)"""
        for key, expected in predicate.items():
            if key not in state:
                return False, f"Missing required key: {key}"
            if callable(expected):
                if not expected(state[key]):
                    return False, f"Predicate failed for {key}"
            elif state[key] != expected:
                return False, f"Value mismatch for {key}: {state[key]} != {expected}"
        return True, "valid"
    
    def validate_operation(self, op_name: str, contract: StateContract,
                          before: Dict, after: Dict) -> bool:
        """Validate operation preserves invariants and satisfies contracts"""
        # Check precondition
        pre_valid, pre_msg = self.check_predicate(before, contract.precondition)
        if not pre_valid:
            self.violations.append(f"{op_name}: Precondition violated - {pre_msg}")
            return False
        
        # Check invariant holds before
        inv_before, inv_msg = self.check_predicate(before, contract.invariant)
        if not inv_before:
            self.violations.append(f"{op_name}: Invariant violated before - {inv_msg}")
            return False
        
        # Check postcondition
        post_valid, post_msg = self.check_predicate(after, contract.postcondition)
        if not post_valid:
            self.violations.append(f"{op_name}: Postcondition violated - {post_msg}")
            return False
        
        # Check invariant holds after
        inv_after, inv_msg = self.check_predicate(after, contract.invariant)
        if not inv_after:
            self.violations.append(f"{op_name}: Invariant violated after - {inv_msg}")
            return False
        
        self.validated_ops[op_name] = contract.hash()
        return True
    
    def get_violations(self) -> list:
        return self.violations


if __name__ == "__main__":
    validator = InvariantValidator()
    
    # Example: validate memory coherence operation
    contract = StateContract(
        precondition={"modules_count": lambda x: x >= 0},
        postcondition={"modules_count": lambda x: x >= 0, "coherent": True},
        invariant={"system_initialized": True}
    )
    
    before = {"modules_count": 5, "system_initialized": True, "coherent": False}
    after = {"modules_count": 5, "system_initialized": True, "coherent": True}
    
    valid = validator.validate_operation("memory_coherence_check", contract, before, after)
    print(f"Validation: {valid}, Violations: {validator.get_violations()}")