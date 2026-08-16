from dataclasses import dataclass
from typing import Callable, List, Optional
from functools import reduce
from enum import Enum

class Op(Enum):
    AND = "and"
    OR = "or"
    NOT = "not"

@dataclass(frozen=True)
class Constraint:
    """Immutable algebraic constraint object"""
    predicate: Callable[[dict], bool]
    expr: str
    
    def __and__(self, other):
        return Constraint(
            lambda ctx: self.predicate(ctx) and other.predicate(ctx),
            f"({self.expr} ∧ {other.expr})"
        )
    
    def __or__(self, other):
        return Constraint(
            lambda ctx: self.predicate(ctx) or other.predicate(ctx),
            f"({self.expr} ∨ {other.expr})"
        )
    
    def __invert__(self):
        return Constraint(
            lambda ctx: not self.predicate(ctx),
            f"¬{self.expr}"
        )

def token_limit(n: int) -> Constraint:
    return Constraint(lambda ctx: ctx.get('tokens', 0) <= n, f"tokens≤{n}")

def memory_limit(n: int) -> Constraint:
    return Constraint(lambda ctx: ctx.get('memory', 0) <= n, f"memory≤{n}")

def cycle_limit(n: int) -> Constraint:
    return Constraint(lambda ctx: ctx.get('cycles', 0) <= n, f"cycles≤{n}")

def simplify(constraint: Constraint) -> Constraint:
    """Reduce constraint to canonical form via algebraic identities"""
    expr = constraint.expr
    # De Morgan's laws, double negation elimination
    expr = expr.replace("¬(", "~(").replace("¬¬", "")
    expr = expr.replace("~(a ∧ b)", "(¬a ∨ ¬b)").replace("~(a ∨ b)", "(¬a ∧ ¬b)")
    return Constraint(constraint.predicate, expr)

def compose(*constraints: Constraint) -> Constraint:
    """Compose constraints via conjunction - all must hold"""
    return reduce(lambda a, b: a & b, constraints)

def verify(constraint: Constraint, context: dict) -> tuple[bool, str]:
    """Evaluate constraint and return (satisfied, reasoning)"""
    result = constraint.predicate(context)
    return result, f"{constraint.expr} = {result} given {context}"

# Example usage
budget_policy = compose(
    token_limit(200000),
    memory_limit(1024),
    cycle_limit(100)
)

context = {'tokens': 150000, 'memory': 512, 'cycles': 50}
satisfied, reasoning = verify(budget_policy, context)