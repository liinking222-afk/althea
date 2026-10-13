import re
from dataclasses import dataclass
from typing import Dict, List, Callable, Any

@dataclass
class Primitive:
    name: str
    signature: str
    implementation: Callable

class VocabularyCompiler:
    def __init__(self):
        self.primitives: Dict[str, Primitive] = {}
        self.compiled_modules: Dict[str, Any] = {}
    
    def define_primitive(self, name: str, signature: str, impl: Callable):
        """Define a vocabulary primitive with its implementation"""
        self.primitives[name] = Primitive(name, signature, impl)
    
    def define_vocabulary(self, domain: str, primitives: Dict[str, tuple]):
        """Define an entire problem domain vocabulary at once"""
        for name, (sig, impl) in primitives.items():
            self.define_primitive(f"{domain}.{name}", sig, impl)
    
    def compile_expression(self, expr: str, domain: str = "") -> Callable:
        """Compile a high-level expression into executable code"""
        tokens = re.findall(r'\w+(?:\.\w+)?|\(|\)|,', expr)
        
        def execute(*args):
            stack = []
            arg_idx = 0
            i = 0
            
            while i < len(tokens):
                token = tokens[i]
                
                if token in self.primitives:
                    prim = self.primitives[token]
                    return prim.implementation(*args)
                elif f"{domain}.{token}" in self.primitives:
                    prim = self.primitives[f"{domain}.{token}"]
                    return prim.implementation(*args)
                elif token.isdigit():
                    stack.append(int(token))
                
                i += 1
            
            return stack[0] if stack else None
        
        return execute
    
    def generate_module(self, domain: str, operations: List[str]) -> str:
        """Generate a complete Python module from vocabulary definitions"""
        lines = [
            f"# AUTO-GENERATED MODULE: {domain}",
            f"# Vocabulary-first compiled implementation\n"
        ]
        
        for op_expr in operations:
            match = re.match(r'(\w+)\s*=\s*(.+)', op_expr)
            if match:
                func_name, expr = match.groups()
                lines.append(f"def {func_name}(*args):")
                lines.append(f"    # Compiled from: {expr}")
                
                if expr in self.primitives or f"{domain}.{expr}" in self.primitives:
                    key = expr if expr in self.primitives else f"{domain}.{expr}"
                    lines.append(f"    return primitives['{key}'](*args)")
                else:
                    lines.append(f"    pass  # Composition placeholder")
                lines.append("")
        
        return "\n".join(lines)

# Global compiler instance
vocabulary_compiler = VocabularyCompiler()