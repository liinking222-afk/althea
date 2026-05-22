#!/usr/bin/env python3
"""vocabulary_forge.py - DSL constructor for problem-domain language generation"""

import re
from dataclasses import dataclass
from typing import Callable, Dict, Any, List

@dataclass
class VocabTerm:
    name: str
    signature: str
    transformer: Callable
    
class VocabularyForge:
    def __init__(self):
        self.vocabularies: Dict[str, Dict[str, VocabTerm]] = {}
        
    def define_domain(self, domain: str, constraints: Dict[str, str]) -> Dict[str, Callable]:
        """Extract vocabulary from constraint signatures"""
        vocab = {}
        for term_name, signature in constraints.items():
            transformer = self._signature_to_transformer(signature)
            vocab[term_name] = VocabTerm(term_name, signature, transformer)
        self.vocabularies[domain] = vocab
        return {k: v.transformer for k, v in vocab.items()}
    
    def _signature_to_transformer(self, sig: str) -> Callable:
        """Convert type signature to executable transformer"""
        if "->" in sig:
            input_type, output_type = [s.strip() for s in sig.split("->")]
            if "list" in input_type.lower():
                return lambda x: [self._coerce(output_type, i) for i in x]
            return lambda x: self._coerce(output_type, x)
        return lambda x: x
    
    def _coerce(self, type_name: str, value: Any) -> Any:
        type_map = {"int": int, "float": float, "str": str, "bool": bool}
        return type_map.get(type_name.lower(), lambda x: x)(value)
    
    def compile_expression(self, domain: str, expression: str) -> Callable:
        """Compile domain expression into executable function"""
        vocab = self.vocabularies.get(domain, {})
        tokens = re.findall(r'\w+|[^\w\s]', expression)
        
        def executor(data: Any) -> Any:
            result = data
            for token in tokens:
                if token in vocab:
                    result = vocab[token].transformer(result)
            return result
        return executor
    
    def generate_dsl_syntax(self, domain: str) -> str:
        """Generate human-readable DSL syntax definition"""
        vocab = self.vocabularies.get(domain, {})
        syntax = [f"DOMAIN: {domain}", "VOCABULARY:"]
        for term in vocab.values():
            syntax.append(f"  {term.name}: {term.signature}")
        return "\n".join(syntax)

if __name__ == "__main__":
    forge = VocabularyForge()
    constraints = {
        "invert": "list[float] -> list[float]",
        "normalize": "list[float] -> list[float]",
        "threshold": "float -> bool"
    }
    ops = forge.define_domain("symmetry_analysis", constraints)
    print(forge.generate_dsl_syntax("symmetry_analysis"))