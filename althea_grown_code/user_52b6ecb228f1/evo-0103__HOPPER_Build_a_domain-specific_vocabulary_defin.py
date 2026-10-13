#!/usr/bin/env python3
"""vocabulary_forge.py - Hopper-inspired semantic primitive extraction"""

import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Primitive:
    term: str
    domain: str
    dependencies: Set[str]
    axioms: List[str]

class VocabularyForge:
    def __init__(self):
        self.primitives: Dict[str, Primitive] = {}
        self.problem_context = ""
        
    def ingest_problem(self, context: str) -> None:
        """Load problem description for analysis"""
        self.problem_context = context
        
    def extract_nouns(self) -> Set[str]:
        """Identify domain entities (nouns) as candidate primitives"""
        words = re.findall(r'\b[a-z]+\b', self.problem_context.lower())
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        return {w for w in words if len(w) > 3 and w not in stopwords}
        
    def extract_verbs(self) -> Set[str]:
        """Identify domain operations (verbs) as candidate primitives"""
        verb_pattern = r'\b(trace|suspend|cascade|validate|excavate|hold|collapse|oscillate)\w*\b'
        return set(re.findall(verb_pattern, self.problem_context.lower()))
        
    def build_dependency_graph(self, terms: Set[str]) -> Dict[str, Set[str]]:
        """Determine which terms depend on others via co-occurrence"""
        deps = defaultdict(set)
        sentences = self.problem_context.split('.')
        for term in terms:
            for sentence in sentences:
                if term in sentence.lower():
                    for other in terms:
                        if other != term and other in sentence.lower():
                            deps[term].add(other)
        return dict(deps)
        
    def define_primitive(self, term: str, domain: str, deps: Set[str], axioms: List[str]) -> Primitive:
        """Create a formal primitive definition"""
        prim = Primitive(term=term, domain=domain, dependencies=deps, axioms=axioms)
        self.primitives[term] = prim
        return prim
        
    def generate_vocabulary(self) -> Dict[str, Primitive]:
        """Extract minimal semantic vocabulary from problem context"""
        nouns = self.extract_nouns()
        verbs = self.extract_verbs()
        all_terms = nouns | verbs
        deps = self.build_dependency_graph(all_terms)
        
        for term in all_terms:
            domain = "operation" if term in verbs else "entity"
            axioms = [f"{term} exists in problem space"]
            if term in deps:
                axioms.append(f"{term} relates to {deps[term]}")
            self.define_primitive(term, domain, deps.get(term, set()), axioms)
            
        return self.primitives
        
    def emit_dsl_skeleton(self) -> str:
        """Generate skeleton code for problem-specific language"""
        lines = ["# Generated Problem Vocabulary\n"]
        for term, prim in sorted(self.primitives.items()):
            lines.append(f"class {term.capitalize()}:")
            lines.append(f"    domain = '{prim.domain}'")
            lines.append(f"    deps = {list(prim.dependencies)}")
            lines.append("")
        return "\n".join(lines)

if __name__ == "__main__":
    forge = VocabularyForge()
    forge.ingest_problem("trace assumptions that cascade through inference chains")
    vocab = forge.generate_vocabulary()
    print(forge.emit_dsl_skeleton())