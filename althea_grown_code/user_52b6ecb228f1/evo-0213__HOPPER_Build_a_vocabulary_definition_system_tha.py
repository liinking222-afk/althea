#!/usr/bin/env python3
"""
Semantic Vocabulary Extractor - HOPPER style compiler pre-pass
Defines the vocabulary of the problem domain before writing solutions
"""

import json
import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class VocabularyCompiler:
    def __init__(self):
        self.primitives: Dict[str, Dict] = {}
        self.relations: List[Tuple[str, str, str]] = []
        self.domain_lexicon: Set[str] = set()
        
    def extract_primitives(self, context: str) -> Dict[str, Dict]:
        """First pass: identify semantic primitives in problem space"""
        terms = re.findall(r'\b[a-z_]+(?:\.[a-z_]+)*\b', context.lower())
        freq = defaultdict(int)
        for term in terms:
            freq[term] += 1
        
        # Primitives are high-frequency domain terms
        threshold = max(2, len(terms) // 50)
        for term, count in freq.items():
            if count >= threshold and len(term) > 3:
                self.primitives[term] = {
                    'frequency': count,
                    'type': self._infer_type(term),
                    'arity': self._infer_arity(context, term)
                }
                self.domain_lexicon.add(term)
        return self.primitives
    
    def _infer_type(self, term: str) -> str:
        """Classify primitive by morphology"""
        if term.endswith(('ing', 'tion', 'ment')):
            return 'operation'
        elif term.endswith(('ness', 'ity', 'cy')):
            return 'property'
        return 'entity'
    
    def _infer_arity(self, context: str, term: str) -> int:
        """Estimate conceptual arity by co-occurrence patterns"""
        pattern = rf'{term}\b[^.]*?\b(\w+)'
        matches = re.findall(pattern, context)
        return min(len(set(matches)), 3)
    
    def define_relations(self, context: str) -> List[Tuple[str, str, str]]:
        """Second pass: extract relationships between primitives"""
        for p1 in self.domain_lexicon:
            for p2 in self.domain_lexicon:
                if p1 != p2:
                    pattern = rf'{p1}\b[^.]*?\b(\w+)\b[^.]*?\b{p2}'
                    matches = re.findall(pattern, context.lower())
                    if matches:
                        rel = max(set(matches), key=matches.count)
                        self.relations.append((p1, rel, p2))
        return self.relations
    
    def compile_vocabulary(self, context: str) -> str:
        """Generate formal vocabulary definition"""
        self.extract_primitives(context)
        self.define_relations(context)
        
        vocab = {
            'primitives': self.primitives,
            'relations': [{'subject': s, 'verb': v, 'object': o} 
                         for s, v, o in self.relations[:20]],
            'lexicon_size': len(self.domain_lexicon)
        }
        return json.dumps(vocab, indent=2)

if __name__ == '__main__':
    compiler = VocabularyCompiler()
    import sys
    context = sys.stdin.read() if not sys.stdin.isatty() else ""
    print(compiler.compile_vocabulary(context))