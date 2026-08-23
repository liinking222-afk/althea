#!/usr/bin/env python3
"""Capability Composition Algebra — treat invocations as rewritable expressions"""

from dataclasses import dataclass
from typing import List, Tuple, Optional
import re
from functools import reduce

@dataclass(frozen=True)
class CapabilityExpr:
    """Immutable capability invocation as algebraic term"""
    name: str
    args: Tuple[str, ...] = ()
    
    def __repr__(self):
        if self.args:
            return f"{self.name}({', '.join(self.args)})"
        return self.name
    
    def compose(self, other: 'CapabilityExpr') -> 'ComposedExpr':
        return ComposedExpr((self, other))

@dataclass(frozen=True)
class ComposedExpr:
    """Function composition: (f ∘ g)(x) = f(g(x))"""
    chain: Tuple[CapabilityExpr, ...]
    
    def __repr__(self):
        return " ∘ ".join(str(c) for c in reversed(self.chain))
    
    def simplify(self) -> 'ComposedExpr':
        """Apply algebraic rewrite rules"""
        new_chain = list(self.chain)
        
        # Identity law: compose(x, identity) = x
        new_chain = [c for c in new_chain if c.name != "identity"]
        
        # Idempotence: refract ∘ refract = refract
        i = 0
        while i < len(new_chain) - 1:
            if new_chain[i].name == new_chain[i+1].name and new_chain[i].name in ["refract", "invert"]:
                new_chain.pop(i+1)
            else:
                i += 1
        
        return ComposedExpr(tuple(new_chain)) if new_chain else ComposedExpr((CapabilityExpr("identity"),))

def parse_capability_chain(invocation_log: List[str]) -> ComposedExpr:
    """Parse invocation history into composable expression"""
    exprs = []
    for inv in invocation_log:
        match = re.match(r'(\w+)(?:\((.*?)\))?', inv)
        if match:
            name, args_str = match.groups()
            args = tuple(a.strip() for a in args_str.split(',')) if args_str else ()
            exprs.append(CapabilityExpr(name, args))
    return ComposedExpr(tuple(exprs))

def prove_equivalence(expr1: ComposedExpr, expr2: ComposedExpr) -> bool:
    """Check algebraic equivalence after simplification"""
    return expr1.simplify().chain == expr2.simplify().chain

# Example usage
if __name__ == "__main__":
    chain = parse_capability_chain(["refract(semantic)", "refract(temporal)", "invert(figure)"])
    simplified = chain.simplify()
    print(f"Original: {chain}")
    print(f"Simplified: {simplified}")
    
    # Prove commutativity where applicable
    chain2 = parse_capability_chain(["refract(temporal)", "refract(semantic)", "invert(figure)"])
    print(f"Equivalent: {prove_equivalence(chain, chain2)}")