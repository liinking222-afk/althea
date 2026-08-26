"""
/autonomous-invariant-prover — Loop Invariant & State Contract Verifier
Dijkstra-style formal verification of module state transitions.
"""

from dataclasses import dataclass
from typing import Callable, Any, Dict, Optional
from enum import Enum

class VerificationResult(Enum):
    VALID = "invariant_preserved"
    VIOLATED = "invariant_broken"
    UNKNOWN = "insufficient_proof"

@dataclass(frozen=True)
class StateContract:
    """Immutable pre/post condition pair"""
    precondition: Callable[[Dict[str, Any]], bool]
    postcondition: Callable[[Dict[str, Any]], bool]
    invariant: Callable[[Dict[str, Any]], bool]
    name: str

@dataclass(frozen=True)
class ProofTrace:
    """Evidence of correctness"""
    initial_state: Dict[str, Any]
    final_state: Dict[str, Any]
    contract: str
    result: VerificationResult
    witness: Optional[str] = None

class InvariantProver:
    """Verify loop invariants and state transitions hold"""
    
    def __init__(self):
        self._contracts: Dict[str, StateContract] = {}
        self._proofs: list[ProofTrace] = []
    
    def register_contract(self, contract: StateContract) -> None:
        """Add a state contract to verify"""
        self._contracts[contract.name] = contract
    
    def verify_transition(
        self, 
        contract_name: str,
        initial: Dict[str, Any],
        final: Dict[str, Any]
    ) -> ProofTrace:
        """Prove a state transition preserves invariants"""
        contract = self._contracts[contract_name]
        
        # Check precondition
        if not contract.precondition(initial):
            return ProofTrace(initial, final, contract_name, 
                            VerificationResult.VIOLATED,
                            "precondition_failed")
        
        # Check invariant preservation: I(s) ∧ transition → I(s')
        if not (contract.invariant(initial) and contract.invariant(final)):
            return ProofTrace(initial, final, contract_name,
                            VerificationResult.VIOLATED,
                            "invariant_not_preserved")
        
        # Check postcondition
        if not contract.postcondition(final):
            return ProofTrace(initial, final, contract_name,
                            VerificationResult.VIOLATED,
                            "postcondition_failed")
        
        proof = ProofTrace(initial, final, contract_name, 
                          VerificationResult.VALID,
                          "qed")
        self._proofs.append(proof)
        return proof
    
    def get_proof_history(self) -> list[ProofTrace]:
        """Return all verified transitions"""
        return self._proofs.copy()