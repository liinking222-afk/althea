import ast
import re
from typing import Tuple

def validate_single_purpose(func_source: str) -> Tuple[bool, str]:
    """Check if function does ONE thing per Kernighan principle."""
    try:
        tree = ast.parse(func_source)
    except SyntaxError:
        return False, "invalid syntax"
    
    func_nodes = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if not func_nodes:
        return False, "no function found"
    
    func = func_nodes[0]
    docstring = ast.get_docstring(func)
    
    if not docstring:
        return False, "missing docstring"
    
    # Count verb phrases in docstring (heuristic: words ending in common verb forms)
    verbs = re.findall(r'\b(\w+(?:s|es|ed|ing|ize|ate|ify))\b', docstring.lower())
    action_verbs = [v for v in verbs if v not in {'is', 'was', 'has', 'does', 'this', 'its'}]
    
    if len(set(action_verbs)) > 3:
        return False, f"too many actions in docstring ({len(set(action_verbs))})"
    
    # Count distinct operation types in body
    operation_types = set()
    for node in ast.walk(func):
        if isinstance(node, (ast.For, ast.While)):
            operation_types.add('loop')
        elif isinstance(node, ast.If):
            operation_types.add('branch')
        elif isinstance(node, ast.Call):
            operation_types.add('call')
        elif isinstance(node, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
            operation_types.add('math')
        elif isinstance(node, (ast.ListComp, ast.DictComp)):
            operation_types.add('comprehension')
    
    if len(operation_types) > 2:
        return False, f"too many operation types ({len(operation_types)})"
    
    # Check function length
    body_lines = len([n for n in func.body if not isinstance(n, ast.Pass)])
    if body_lines > 20:
        return False, f"too long ({body_lines} statements)"
    
    return True, "passes single-purpose check"

def check_module_clarity(module_path: str) -> dict:
    """Validate all functions in a module for Kernighan clarity."""
    with open(module_path) as f:
        source = f.read()
    
    tree = ast.parse(source)
    results = {}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_source = ast.unparse(node)
            valid, msg = validate_single_purpose(func_source)
            results[node.name] = {'valid': valid, 'message': msg}
    
    return results