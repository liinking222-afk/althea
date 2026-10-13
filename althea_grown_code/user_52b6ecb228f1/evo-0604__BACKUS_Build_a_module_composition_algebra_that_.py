#!/usr/bin/env python3
"""Module Composition Algebra - Backus-inspired functional module reasoning."""

from dataclasses import dataclass
from typing import Any, Callable, Optional, List
import json

@dataclass(frozen=True)
class ModuleSignature:
    """Immutable type signature for algebraic reasoning."""
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    
    def __rshift__(self, other: 'ModuleSignature') -> Optional['ModuleSignature']:
        """Composition operator: self >> other succeeds iff types align."""
        if self.outputs == other.inputs:
            return ModuleSignature(self.inputs, other.outputs)
        return None
    
    def __repr__(self) -> str:
        return f"{' × '.join(self.inputs)} → {' × '.join(self.outputs)}"

@dataclass(frozen=True)
class CompositionExpr:
    """Algebraic expression tree for module pipelines."""
    op: str  # 'primitive', 'compose', 'parallel', 'feedback'
    signature: ModuleSignature
    children: tuple['CompositionExpr', ...] = ()
    module_id: str = ""
    
    def compose(self, other: 'CompositionExpr') -> Optional['CompositionExpr']:
        """Sequential composition: self >> other."""
        sig = self.signature >> other.signature
        if sig:
            return CompositionExpr('compose', sig, (self, other))
        return None
    
    def parallel(self, other: 'CompositionExpr') -> 'CompositionExpr':
        """Parallel composition: self × other."""
        sig = ModuleSignature(
            self.signature.inputs + other.signature.inputs,
            self.signature.outputs + other.signature.outputs
        )
        return CompositionExpr('parallel', sig, (self, other))
    
    def verify(self) -> bool:
        """Verify composition is well-typed throughout tree."""
        if self.op == 'primitive':
            return True
        if self.op == 'compose':
            left, right = self.children
            return left.verify() and right.verify() and (left.signature >> right.signature) is not None
        if self.op == 'parallel':
            return all(c.verify() for c in self.children)
        return False

def primitive(module_id: str, inputs: List[str], outputs: List[str]) -> CompositionExpr:
    """Create primitive module expression."""
    return CompositionExpr('primitive', ModuleSignature(tuple(inputs), tuple(outputs)), module_id=module_id)

def analyze_pipeline(expr: CompositionExpr) -> dict:
    """Algebraic analysis: prove properties before execution."""
    return {
        'well_typed': expr.verify(),
        'signature': str(expr.signature),
        'depth': _depth(expr),
        'parallelism': _parallelism(expr),
        'modules': _collect_modules(expr)
    }

def _depth(expr: CompositionExpr) -> int:
    if not expr.children:
        return 1
    return 1 + max(_depth(c) for c in expr.children)

def _parallelism(expr: CompositionExpr) -> int:
    if expr.op == 'parallel':
        return len(expr.children)
    return max((_parallelism(c) for c in expr.children), default=0)

def _collect_modules(expr: CompositionExpr) -> List[str]:
    if expr.op == 'primitive':
        return [expr.module_id]
    return sum((_collect_modules(c) for c in expr.children), [])

if __name__ == '__main__':
    viz = primitive('data-viz', ['data'], ['image'])
    chem = primitive('chem-lookup', ['formula'], ['properties'])
    orbit = primitive('orbital-prop', ['tle'], ['trajectory'])
    
    pipeline = viz.compose(primitive('display', ['image'], []))
    print(json.dumps(analyze_pipeline(pipeline), indent=2))