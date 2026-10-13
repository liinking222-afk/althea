import ast
import hashlib
from dataclasses import dataclass
from typing import Any, Dict, Set, List, Tuple

@dataclass(frozen=True)
class Expr:
    op: str
    args: Tuple['Expr', ...]
    metadata: Tuple[Tuple[str, Any], ...] = ()
    
    def __hash__(self):
        return hash((self.op, self.args, self.metadata))
    
    def normalize(self) -> 'Expr':
        """Algebraic normalization via rewrite rules."""
        if self.op == 'compose' and len(self.args) == 2:
            if self.args[0].op == 'identity':
                return self.args[1].normalize()
            if self.args[1].op == 'identity':
                return self.args[0].normalize()
        if self.op == 'map' and self.args and self.args[0].op == 'identity':
            return Expr('identity', ())
        normalized_args = tuple(arg.normalize() for arg in self.args)
        return Expr(self.op, normalized_args, self.metadata)
    
    def equivalent(self, other: 'Expr') -> bool:
        """Structural equivalence after normalization."""
        return self.normalize() == other.normalize()

class CodeAlgebra:
    def __init__(self):
        self.expr_cache: Dict[str, Expr] = {}
    
    def parse_to_algebra(self, code: str) -> Expr:
        """Convert Python code to algebraic expression."""
        tree = ast.parse(code.strip())
        return self._ast_to_expr(tree.body[0])
    
    def _ast_to_expr(self, node: ast.AST) -> Expr:
        if isinstance(node, ast.Expr):
            return self._ast_to_expr(node.value)
        elif isinstance(node, ast.Call):
            func = self._ast_to_expr(node.func)
            args = tuple(self._ast_to_expr(arg) for arg in node.args)
            return Expr('apply', (func, *args))
        elif isinstance(node, ast.Name):
            return Expr('var', (), (('name', node.id),))
        elif isinstance(node, ast.Lambda):
            body = self._ast_to_expr(node.body)
            params = tuple(arg.arg for arg in node.args.args)
            return Expr('lambda', (body,), (('params', params),))
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
            return Expr('compose', (self._ast_to_expr(node.left), self._ast_to_expr(node.right)))
        elif isinstance(node, ast.Constant):
            return Expr('const', (), (('value', node.value),))
        else:
            return Expr('unknown', ())
    
    def find_isomorphisms(self, exprs: List[Expr]) -> List[Set[int]]:
        """Group expressions by algebraic equivalence."""
        normalized = [e.normalize() for e in exprs]
        groups: Dict[Expr, Set[int]] = {}
        for idx, norm in enumerate(normalized):
            groups.setdefault(norm, set()).add(idx)
        return [g for g in groups.values() if len(g) > 1]
    
    def symbolic_hash(self, expr: Expr) -> str:
        """Content-addressed identifier for normalized expression."""
        norm = expr.normalize()
        return hashlib.sha256(str(norm).encode()).hexdigest()[:16]

def reason_about(code_fragments: List[str]) -> Dict[str, Any]:
    algebra = CodeAlgebra()
    exprs = [algebra.parse_to_algebra(c) for c in code_fragments]
    return {
        'expressions': [str(e.normalize()) for e in exprs],
        'isomorphisms': algebra.find_isomorphisms(exprs),
        'hashes': [algebra.symbolic_hash(e) for e in exprs]
    }