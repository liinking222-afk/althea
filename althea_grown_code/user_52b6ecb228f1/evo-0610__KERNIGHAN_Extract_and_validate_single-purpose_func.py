import ast
import re
from typing import List, Dict, Tuple

def count_responsibilities(node: ast.FunctionDef) -> int:
    """Count distinct responsibilities by analyzing control flow and calls."""
    responsibilities = 0
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While)):
            responsibilities += 1
        elif isinstance(child, ast.Try):
            responsibilities += 1
    return max(1, responsibilities)

def extract_verb_from_name(name: str) -> str:
    """Extract the primary verb from a function name."""
    parts = re.split(r'[_-]', name.lower())
    verbs = {'get', 'set', 'create', 'delete', 'update', 'validate', 
             'parse', 'format', 'check', 'find', 'filter', 'map', 
             'reduce', 'count', 'extract', 'compute', 'render'}
    for part in parts:
        if part in verbs:
            return part
    return parts[0] if parts else ''

def audit_function(code: str) -> List[Dict]:
    """Audit each function for single-responsibility adherence."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    
    report = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            resp_count = count_responsibilities(node)
            verb = extract_verb_from_name(node.name)
            lines = node.end_lineno - node.lineno if node.end_lineno else 0
            
            report.append({
                'name': node.name,
                'verb': verb,
                'responsibilities': resp_count,
                'lines': lines,
                'single_purpose': resp_count <= 2 and lines <= 25,
                'suggestion': f"split_{node.name}" if resp_count > 2 else None
            })
    
    return report

def kernighan_check(code: str) -> Tuple[bool, str]:
    """Main entry: check if code follows Kernighan principle."""
    audit = audit_function(code)
    violations = [f for f in audit if not f['single_purpose']]
    
    if not violations:
        return True, "All functions are single-purpose."
    
    details = "; ".join([f"{v['name']} ({v['responsibilities']} responsibilities)" 
                         for v in violations])
    return False, f"Violations: {details}"