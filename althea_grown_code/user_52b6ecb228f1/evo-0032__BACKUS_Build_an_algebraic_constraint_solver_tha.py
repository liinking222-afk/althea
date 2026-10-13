#!/usr/bin/env python3
"""Algebraic Semantic Constraint Solver - treat conditions as first-class objects"""

from dataclasses import dataclass
from typing import Callable, List, Set, Tuple
from functools import reduce

@dataclass(frozen=True)
class Predicate:
    name: str
    arity: int
    
@dataclass(frozen=True)
class Constraint:
    pred: Predicate
    args: Tuple[str, ...]
    negated: bool = False
    
    def __invert__(self):
        return Constraint(self.pred, self.args, not self.negated)
    
    def __and__(self, other):
        return ConjunctiveSet({self, other})
    
    def normalize(self) -> 'Constraint':
        return self

@dataclass(frozen=True)
class ConjunctiveSet:
    constraints: Set[Constraint]
    
    def __and__(self, other):
        if isinstance(other, Constraint):
            return ConjunctiveSet(self.constraints | {other})
        return ConjunctiveSet(self.constraints | other.constraints)
    
    def is_satisfiable(self) -> bool:
        normalized = {c.normalize() for c in self.constraints}
        for c in normalized:
            if ~c in normalized:
                return False
        return True

class ConstraintAlgebra:
    def __init__(self):
        self.rules: List[Tuple[Callable, Callable]] = []
    
    def add_rewrite(self, pattern: Callable[[Constraint], bool], 
                    rewrite: Callable[[Constraint], Constraint]):
        self.rules.append((pattern, rewrite))
    
    def normalize(self, c: Constraint) -> Constraint:
        for pattern, rewrite in self.rules:
            if pattern(c):
                return self.normalize(rewrite(c))
        return c
    
    def prove_coherence(self, constraints: ConjunctiveSet) -> bool:
        normalized = ConjunctiveSet({self.normalize(c) for c in constraints.constraints})
        return normalized.is_satisfiable()
    
    def compose(self, *constraint_sets: ConjunctiveSet) -> ConjunctiveSet:
        return reduce(lambda a, b: a & b, constraint_sets)

def semantic_constraint_solver():
    algebra = ConstraintAlgebra()
    coherent = Predicate("coherent", 1)
    stable = Predicate("stable", 1)
    
    algebra.add_rewrite(
        lambda c: c.pred.name == "coherent" and c.negated,
        lambda c: Constraint(Predicate("chaotic", 1), c.args, False)
    )
    
    return algebra