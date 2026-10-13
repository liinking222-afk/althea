#!/usr/bin/env python3
"""
HOPPER MODULE: Vocabulary-First Problem Solver
Extracts domain vocabulary, builds executable interfaces before implementation.
"""

import re
from typing import Dict, List, Set
from dataclasses import dataclass

@dataclass
class DomainVocabulary:
    nouns: Set[str]
    verbs: Set[str]
    constraints: Set[str]
    
class VocabularyCompiler:
    def __init__(self):
        self.patterns = {
            'capability': r'\b(can|should|must|query|fetch|compute|analyze|map|project)\s+(\w+)',
            'entity': r'\b(weather|satellite|position|metric|data|map|protocol)\b',
            'constraint': r'\b(centered|accurate|high-resolution|current|real-time)\s+(\w+)',
        }
    
    def extract_vocabulary(self, context: str) -> DomainVocabulary:
        nouns = set(re.findall(self.patterns['entity'], context.lower()))
        verbs = set(m[0] for m in re.findall(self.patterns['capability'], context.lower()))
        constraints = set(m[1] for m in re.findall(self.patterns['constraint'], context.lower()))
        return DomainVocabulary(nouns, verbs, constraints)
    
    def compile_interface(self, vocab: DomainVocabulary) -> str:
        """Generate executable interface from vocabulary."""
        interface = "class ProblemDomain:\n"
        
        for verb in sorted(vocab.verbs):
            for noun in sorted(vocab.nouns):
                method = f"    def {verb}_{noun}(self, **context):\n"
                method += f'        """Execute {verb} operation on {noun}."""\n'
                method += "        raise NotImplementedError('Vocabulary defined, awaiting implementation')\n\n"
                interface += method
        
        return interface
    
    def define_then_solve(self, problem_context: str) -> Dict[str, any]:
        """HOPPER principle: vocabulary first, solution second."""
        vocab = self.extract_vocabulary(problem_context)
        interface = self.compile_interface(vocab)
        
        return {
            'vocabulary': vocab,
            'executable_interface': interface,
            'next_step': 'implement_methods'
        }

if __name__ == '__main__':
    compiler = VocabularyCompiler()
    result = compiler.define_then_solve("query weather data with accurate positions")
    print(result['executable_interface'])