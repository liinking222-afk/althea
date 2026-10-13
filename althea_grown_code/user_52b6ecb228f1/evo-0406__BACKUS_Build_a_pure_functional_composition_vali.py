#!/usr/bin/env python3
from functools import reduce
from typing import Callable, List, Tuple, Any, Optional
import json

class CapabilityAlgebra:
    """Treat capability chains as algebraic objects with verifiable properties."""
    
    def __init__(self):
        self.properties = {
            'associative': [],
            'commutative': [],
            'idempotent': [],
            'identity_preserving': []
        }
    
    def compose(self, *funcs: Callable) -> Callable:
        """Pure functional composition: (f ∘ g)(x) = f(g(x))"""
        return reduce(lambda f, g: lambda x: f(g(x)), funcs, lambda x: x)
    
    def verify_associativity(self, f: Callable, g: Callable, h: Callable, test_inputs: List[Any]) -> bool:
        """Verify (f ∘ g) ∘ h = f ∘ (g ∘ h)"""
        for x in test_inputs:
            try:
                left = self.compose(self.compose(f, g), h)(x)
                right = self.compose(f, self.compose(g, h))(x)
                if left != right:
                    return False
            except:
                return False
        return True
    
    def verify_commutativity(self, f: Callable, g: Callable, test_inputs: List[Any]) -> bool:
        """Verify f ∘ g = g ∘ f"""
        for x in test_inputs:
            try:
                if self.compose(f, g)(x) != self.compose(g, f)(x):
                    return False
            except:
                return False
        return True
    
    def verify_idempotence(self, f: Callable, test_inputs: List[Any]) -> bool:
        """Verify f ∘ f = f"""
        for x in test_inputs:
            try:
                if f(f(x)) != f(x):
                    return False
            except:
                return False
        return True
    
    def analyze_chain(self, chain_name: str, capabilities: List[Tuple[str, Callable]], test_data: List[Any]) -> dict:
        """Analyze algebraic properties of a capability invocation chain."""
        results = {
            'chain': chain_name,
            'length': len(capabilities),
            'properties': {},
            'composable': True,
            'reasoning': []
        }
        
        # Test idempotence for each capability
        for name, func in capabilities:
            is_idem = self.verify_idempotence(func, test_data)
            results['properties'][f'{name}_idempotent'] = is_idem
            if is_idem:
                results['reasoning'].append(f"{name} is idempotent: safe to retry")
        
        # Test pairwise commutativity
        for i, (name1, f1) in enumerate(capabilities):
            for name2, f2 in capabilities[i+1:]:
                is_comm = self.verify_commutativity(f1, f2, test_data)
                results['properties'][f'{name1}↔{name2}'] = is_comm
                if is_comm:
                    results['reasoning'].append(f"{name1} and {name2} commute: order-independent")
        
        return results
    
    def emit_report(self, analysis: dict) -> str:
        """Generate declarative reasoning report."""
        return json.dumps(analysis, indent=2)

if __name__ == '__main__':
    algebra = CapabilityAlgebra()
    print(json.dumps({'status': 'algebra_validator_ready', 'mode': 'declarative_reasoning'}, indent=2))