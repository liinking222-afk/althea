import ast
import inspect
from typing import Callable, Dict, Any

def validate_single_purpose(func: Callable) -> Dict[str, Any]:
    """Check if function does ONE thing. Return metrics."""
    source = inspect.getsource(func)
    tree = ast.parse(source)
    
    complexity = 0
    side_effects = 0
    branches = 0
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.While, ast.For)):
            complexity += 1
            branches += 1
        elif isinstance(node, ast.Try):
            complexity += len(node.handlers)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            side_effects += 1
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in {'append', 'update', 'pop', 'remove'}:
                    side_effects += 1
    
    is_single = complexity <= 2 and side_effects <= 1 and branches <= 1
    
    return {
        'passes': is_single,
        'complexity': complexity,
        'side_effects': side_effects,
        'branches': branches,
        'name': func.__name__,
        'verdict': 'SINGULAR' if is_single else 'FRAGMENTED'
    }

def name_clarity_score(func: Callable) -> float:
    """Score how well the name documents intent."""
    name = func.__name__
    doc = inspect.getdoc(func) or ""
    
    name_words = name.replace('_', ' ').split()
    doc_words = set(doc.lower().split())
    
    overlap = sum(1 for w in name_words if w.lower() in doc_words)
    verb_present = any(w in name for w in ['get', 'set', 'is', 'has', 'validate', 'check', 'find', 'create'])
    
    score = (len(name_words) * 0.3 + overlap * 0.4 + (1 if verb_present else 0) * 0.3)
    return min(score, 1.0)

def kernighan_audit(func: Callable) -> str:
    """Run complete Kernighan audit on function."""
    metrics = validate_single_purpose(func)
    clarity = name_clarity_score(func)
    
    result = f"{metrics['name']}: {metrics['verdict']}\n"
    result += f"  complexity={metrics['complexity']} "
    result += f"side_effects={metrics['side_effects']} "
    result += f"clarity={clarity:.2f}\n"
    result += f"  PASS" if metrics['passes'] and clarity > 0.5 else f"  FAIL"
    
    return result