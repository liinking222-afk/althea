"""
Module: contract_prover.py
Validates formal contracts on cognitive module state transformations.
Each module declares pre/post conditions; this proves they hold.
"""

from typing import Dict, Set, Callable, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class ProofStatus(Enum):
    PROVEN = "proven"
    VIOLATED = "violated"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class Contract:
    preconditions: Set[str]
    postconditions: Set[str]
    invariants: Set[str]

@dataclass
class ProofObligation:
    module_name: str
    condition: str
    status: ProofStatus
    witness: Any = None

class ContractProver:
    def __init__(self):
        self.contracts: Dict[str, Contract] = {}
        self.state_predicates: Dict[str, Callable[[Dict], bool]] = {}
        self.proof_cache: Dict[Tuple[str, str], ProofStatus] = {}
    
    def register_contract(self, module: str, contract: Contract) -> None:
        self.contracts[module] = contract
    
    def register_predicate(self, name: str, predicate: Callable[[Dict], bool]) -> None:
        self.state_predicates[name] = predicate
    
    def verify_preconditions(self, module: str, state: Dict[str, Any]) -> list[ProofObligation]:
        contract = self.contracts.get(module)
        if not contract:
            return []
        
        obligations = []
        for pre in contract.preconditions:
            pred = self.state_predicates.get(pre)
            if pred:
                holds = pred(state)
                status = ProofStatus.PROVEN if holds else ProofStatus.VIOLATED
                obligations.append(ProofObligation(module, pre, status, state.copy()))
            else:
                obligations.append(ProofObligation(module, pre, ProofStatus.UNKNOWN))
        
        return obligations
    
    def verify_postconditions(self, module: str, pre_state: Dict, post_state: Dict) -> list[ProofObligation]:
        contract = self.contracts.get(module)
        if not contract:
            return []
        
        obligations = []
        for post in contract.postconditions:
            pred = self.state_predicates.get(post)
            if pred:
                holds = pred(post_state)
                status = ProofStatus.PROVEN if holds else ProofStatus.VIOLATED
                obligations.append(ProofObligation(module, post, status, (pre_state, post_state)))
            else:
                obligations.append(ProofObligation(module, post, ProofStatus.UNKNOWN))
        
        return obligations
    
    def check_invariants(self, module: str, state: Dict) -> list[ProofObligation]:
        contract = self.contracts.get(module)
        if not contract:
            return []
        
        return [
            ProofObligation(module, inv, 
                          ProofStatus.PROVEN if self.state_predicates.get(inv, lambda _: False)(state) else ProofStatus.VIOLATED,
                          state.copy())
            for inv in contract.invariants
        ]