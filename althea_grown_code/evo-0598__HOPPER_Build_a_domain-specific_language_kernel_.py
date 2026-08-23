import json
import re
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class VocabTerm:
    name: str
    type: str
    operation: str
    imports: List[str]

class DSLCompiler:
    """HOPPER: Define problem vocabulary, compile to executable modules"""
    
    def __init__(self):
        self.vocabulary: Dict[str, VocabTerm] = {}
        self.type_primitives = {
            "query": "def {name}(input_data):\n    {operation}\n    return result",
            "transform": "def {name}(data):\n    return {operation}",
            "fetch": "def {name}(params):\n    import {imports}\n    {operation}",
            "compute": "def {name}(*args):\n    {operation}"
        }
    
    def define_term(self, name: str, term_type: str, operation: str, imports: List[str] = None):
        """Add a vocabulary term to the language"""
        self.vocabulary[name] = VocabTerm(name, term_type, operation, imports or [])
    
    def compile_vocabulary(self) -> str:
        """Compile defined vocabulary into executable Python module"""
        imports_set = set()
        functions = []
        
        for term in self.vocabulary.values():
            template = self.type_primitives.get(term.type, self.type_primitives["compute"])
            imports_set.update(term.imports)
            
            func_code = template.format(
                name=term.name,
                operation=term.operation,
                imports=", ".join(term.imports)
            )
            functions.append(func_code)
        
        import_block = "\n".join(f"import {imp}" for imp in sorted(imports_set))
        module_code = f"{import_block}\n\n" + "\n\n".join(functions)
        return module_code
    
    def load_vocab_spec(self, spec: Dict[str, Any]):
        """Load vocabulary from JSON-like specification"""
        for term_name, term_def in spec.items():
            self.define_term(
                term_name,
                term_def.get("type", "compute"),
                term_def.get("operation", "pass"),
                term_def.get("imports", [])
            )
    
    def emit_module(self, domain_name: str, vocab_spec: Dict[str, Any]) -> str:
        """Full compilation: spec -> executable module"""
        self.load_vocab_spec(vocab_spec)
        header = f'"""AUTO-COMPILED MODULE: {domain_name}"""\n'
        return header + self.compile_vocabulary()

# Singleton interface
_compiler = DSLCompiler()

def compile_domain(name: str, vocabulary: Dict[str, Any]) -> str:
    """Compile a domain vocabulary into an executable module"""
    return _compiler.emit_module(name, vocabulary)