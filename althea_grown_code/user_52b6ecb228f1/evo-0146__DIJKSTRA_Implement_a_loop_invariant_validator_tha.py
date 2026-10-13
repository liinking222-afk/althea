import hashlib
import json
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class Invariant:
    name: str
    predicate: Callable[[Dict[str, Any]], bool]
    proof_hint: str

class InvariantValidator:
    def __init__(self):
        self.invariants: Dict[str, Invariant] = {}
        self.state_snapshot: Optional[Dict[str, Any]] = None
        self.violation_log: List[Dict[str, str]] = []
    
    def register(self, name: str, predicate: Callable, proof_hint: str) -> None:
        self.invariants[name] = Invariant(name, predicate, proof_hint)
    
    def capture_state(self, state: Dict[str, Any]) -> str:
        self.state_snapshot = state.copy()
        return hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
    
    def validate_all(self) -> bool:
        if self.state_snapshot is None:
            return False
        
        all_valid = True
        for inv_name, inv in self.invariants.items():
            try:
                holds = inv.predicate(self.state_snapshot)
                if not holds:
                    self.violation_log.append({
                        "invariant": inv_name,
                        "proof_hint": inv.proof_hint,
                        "state_hash": hashlib.sha256(
                            json.dumps(self.state_snapshot, sort_keys=True).encode()
                        ).hexdigest()[:16]
                    })
                    all_valid = False
            except Exception as e:
                self.violation_log.append({
                    "invariant": inv_name,
                    "error": str(e),
                    "proof_hint": inv.proof_hint
                })
                all_valid = False
        
        return all_valid
    
    def prove_transformation(self, pre: Dict[str, Any], post: Dict[str, Any]) -> bool:
        pre_hash = self.capture_state(pre)
        pre_valid = self.validate_all()
        
        post_hash = self.capture_state(post)
        post_valid = self.validate_all()
        
        return pre_valid and post_valid
    
    def get_violations(self) -> List[Dict[str, str]]:
        return self.violation_log.copy()

validator = InvariantValidator()

validator.register(
    "coherence_bounded",
    lambda s: 0.0 <= s.get("coherence", 0.0) <= 1.0,
    "∀c ∈ coherence: 0 ≤ c ≤ 1"
)

validator.register(
    "module_count_monotonic",
    lambda s: s.get("module_count", 0) >= s.get("prev_module_count", 0),
    "module_count[n+1] ≥ module_count[n]"
)