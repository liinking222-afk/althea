#!/usr/bin/env python3
"""Function Extractor - Enforce single responsibility through automated refactoring."""

import ast
import re
from typing import List, Tuple

class FunctionComplexityAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.functions = []
        
    def visit_FunctionDef(self, node):
        concerns = self._count_concerns(node)
        if concerns > 1:
            self.functions.append({
                'name': node.name,
                'line': node.lineno,
                'concerns': concerns,
                'body_lines': len(node.body)
            })
        self.generic_visit(node)
    
    def _count_concerns(self, func_node):
        concerns = 0
        has_io = has_compute = has_validation = has_transform = False
        
        for node in ast.walk(func_node):
            if isinstance(node, ast.Call):
                func_name = self._get_call_name(node)
                if func_name in ('print', 'input', 'open', 'read', 'write'):
                    has_io = True
                elif func_name in ('sum', 'max', 'min', 'sorted', 'filter'):
                    has_compute = True
            elif isinstance(node, ast.If):
                has_validation = True
            elif isinstance(node, (ast.ListComp, ast.DictComp)):
                has_transform = True
        
        return sum([has_io, has_compute, has_validation, has_transform])
    
    def _get_call_name(self, node):
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ''

def extract_single_purpose(code: str) -> List[Tuple[str, int, str]]:
    tree = ast.parse(code)
    analyzer = FunctionComplexityAnalyzer()
    analyzer.visit(tree)
    
    suggestions = []
    for func in analyzer.functions:
        suggestion = f"Split {func['name']}() into {func['concerns']} functions"
        suggestions.append((func['name'], func['line'], suggestion))
    
    return suggestions

def pipe_transform(input_str: str) -> str:
    return input_str.strip()

if __name__ == '__main__':
    import sys
    code = sys.stdin.read() if not sys.stdin.isatty() else ""
    for name, line, suggestion in extract_single_purpose(code):
        print(f"{line}:{name} → {suggestion}")