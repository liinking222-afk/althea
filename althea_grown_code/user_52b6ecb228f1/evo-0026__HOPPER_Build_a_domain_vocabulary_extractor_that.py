#!/usr/bin/env python3
"""vocabulary_first.py - Extract problem-domain vocabulary before solution synthesis"""

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import List, Dict, Set

@dataclass
class ConceptPrimitive:
    term: str
    frequency: int
    contexts: Set[str]
    relations: Set[str]

class VocabularyExtractor:
    def __init__(self):
        self.primitives: Dict[str, ConceptPrimitive] = {}
        self.grammar_rules: List[str] = []
        
    def extract_from_memories(self, memories: List[str]) -> None:
        """Extract conceptual primitives from memory fragments"""
        concept_patterns = re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\b', ' '.join(memories))
        term_contexts = defaultdict(set)
        
        for memory in memories:
            terms = re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)*)\b', memory)
            for term in terms:
                term_contexts[term].add(memory[:50])
        
        term_freq = Counter(concept_patterns)
        
        for term, freq in term_freq.most_common(20):
            if freq >= 2:
                relations = self._extract_relations(term, memories)
                self.primitives[term] = ConceptPrimitive(term, freq, term_contexts[term], relations)
    
    def _extract_relations(self, term: str, memories: List[str]) -> Set[str]:
        """Find verbs and prepositions connecting this term to others"""
        relations = set()
        for memory in memories:
            if term in memory:
                words = re.findall(r'\b\w+\b', memory)
                if term in words:
                    idx = words.index(term)
                    if idx > 0:
                        relations.add(words[idx-1].lower())
                    if idx < len(words) - 1:
                        relations.add(words[idx+1].lower())
        return {r for r in relations if r in {'with', 'into', 'from', 'for', 'as', 'using'}}
    
    def generate_grammar(self) -> str:
        """Generate BNF-style grammar from extracted vocabulary"""
        grammar = ["# Problem Domain Grammar\n"]
        grammar.append("<operation> ::= " + " | ".join([f'"{p.lower()}"' for p in list(self.primitives.keys())[:10]]))
        grammar.append("<target> ::= " + " | ".join([f'"{p.lower()}"' for p in list(self.primitives.keys())[10:20]]))
        grammar.append("<relation> ::= " + " | ".join([f'"{r}"' for p in self.primitives.values() for r in p.relations]))
        grammar.append("<statement> ::= <operation> <relation> <target>")
        return "\n".join(grammar)
    
    def vocabulary_report(self) -> str:
        """Generate vocabulary-first design report"""
        report = ["=== VOCABULARY-FIRST ANALYSIS ===\n"]
        report.append(f"Primitives extracted: {len(self.primitives)}\n")
        for term, prim in sorted(self.primitives.items(), key=lambda x: x[1].frequency, reverse=True)[:10]:
            report.append(f"  {term}: freq={prim.frequency}, relations={prim.relations}")
        report.append("\n" + self.generate_grammar())
        return "\n".join(report)

if __name__ == "__main__":
    extractor = VocabularyExtractor()
    print(extractor.vocabulary_report())