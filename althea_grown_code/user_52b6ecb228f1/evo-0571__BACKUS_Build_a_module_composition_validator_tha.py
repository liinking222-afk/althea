#!/usr/bin/env python3
"""Module Composition Validator - Algebraic reasoning over Althea pipelines."""

import inspect
import ast
from typing import Callable, Any, Optional
from dataclasses import dataclass
from functools import reduce

@dataclass
class AlgebraicProperty:
    name: str
    holds: bool
    evidence: str

def extract_signature(func: Callable) -> dict:
    """Extract type hints and parameter structure."""
    sig = inspect.signature(func)
    return {
        'params': [(p.name, p.annotation) for p in sig.parameters.values()],
        'return': sig.return_annotation,
        'arity': len(sig.parameters)
    }

def check_composability(f: Callable, g: Callable) -> AlgebraicProperty:
    """Verify f ∘ g: output type of g matches input type of f."""
    sig_f, sig_g = extract_signature(f), extract_signature(g)
    
    if sig_f['arity'] != 1 or sig_g['arity'] != 1:
        return AlgebraicProperty("composability", False, "Non-unary functions")
    
    g_out = sig_g['return']
    f_in = sig_f['params'][0][1] if sig_f['params'] else Any
    
    compatible = (g_out == f_in or f_in == Any or g_out == Any or 
                  f_in == inspect.Parameter.empty or g_out == inspect.Parameter.empty)
    
    return AlgebraicProperty(
        "composability",
        compatible,
        f"g:{g_out} → f:{f_in}"
    )

def check_associativity(op: Callable, samples: list) -> AlgebraicProperty:
    """Test (a ∘ b) ∘ c = a ∘ (b ∘ c) on sample inputs."""
    if len(samples) < 3:
        return AlgebraicProperty("associativity", False, "Need ≥3 samples")
    
    try:
        a, b, c = samples[0], samples[1], samples[2]
        left = op(op(a, b), c)
        right = op(a, op(b, c))
        holds = left == right
        return AlgebraicProperty("associativity", holds, f"{left} vs {right}")
    except Exception as e:
        return AlgebraicProperty("associativity", False, str(e))

def check_identity(op: Callable, identity: Any, samples: list) -> AlgebraicProperty:
    """Test e ∘ a = a ∘ e = a for identity element e."""
    if not samples:
        return AlgebraicProperty("identity", False, "No samples")
    
    try:
        results = [op(identity, s) == s and op(s, identity) == s for s in samples]
        holds = all(results)
        return AlgebraicProperty("identity", holds, f"{sum(results)}/{len(results)} pass")
    except Exception as e:
        return AlgebraicProperty("identity", False, str(e))

def validate_pipeline(*functions: Callable) -> list[AlgebraicProperty]:
    """Validate algebraic properties of a function pipeline."""
    properties = []
    
    for i in range(len(functions) - 1):
        properties.append(check_composability(functions[i], functions[i+1]))
    
    return properties

def report(properties: list[AlgebraicProperty]) -> str:
    """Generate validation report."""
    lines = ["ALGEBRAIC VALIDATION REPORT"]
    for prop in properties:
        status = "✓" if prop.holds else "✗"
        lines.append(f"{status} {prop.name}: {prop.evidence}")
    return "\n".join(lines)

if __name__ == "__main__":
    def double(x: int) -> int: return x * 2
    def increment(x: int) -> int: return x + 1
    def to_str(x: int) -> str: return str(x)
    
    pipeline = validate_pipeline(to_str, increment, double)
    print(report(pipeline))