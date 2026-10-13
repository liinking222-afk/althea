#!/usr/bin/env python3
"""
Vocabulary Definition Substrate - Extract domain primitives before solution construction
Enforces language-first thinking: define the problem's natural vocabulary, then code emerges.
"""

import json
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Primitive:
    term: str
    domain: str
    operations: List[str]
    composability: List[str]
    
    
class VocabularySubstrate:
    def __init__(self, storage_path: str = "/tmp/althea_vocabularies.json"):
        self.storage = Path(storage_path)
        self.vocabularies: Dict[str, Dict[str, Primitive]] = self._load()
        
    def _load(self) -> Dict:
        if self.storage.exists():
            return json.loads(self.storage.read_text())
        return {}
    
    def _save(self):
        self.storage.write_text(json.dumps(self.vocabularies, indent=2))
    
    def extract_primitives(self, domain: str, context: str) -> List[Primitive]:
        """Extract domain primitives from problem context before coding"""
        tokens = context.lower().split()
        noun_phrases = self._identify_nouns(tokens)
        verb_phrases = self._identify_verbs(tokens)
        
        primitives = []
        for noun in noun_phrases:
            ops = [v for v in verb_phrases if self._relates(noun, v, context)]
            comps = [n for n in noun_phrases if n != noun and self._composable(noun, n)]
            primitives.append(Primitive(noun, domain, ops, comps))
        
        return primitives
    
    def define_vocabulary(self, domain: str, primitives: List[Primitive]):
        """Store vocabulary definition for domain"""
        self.vocabularies[domain] = {p.term: asdict(p) for p in primitives}
        self._save()
    
    def query_vocabulary(self, domain: str) -> Dict[str, Primitive]:
        """Retrieve defined vocabulary for problem domain"""
        return self.vocabularies.get(domain, {})
    
    def enforce_vocabulary_first(self, domain: str, code_intent: str) -> bool:
        """Check if vocabulary exists before allowing solution construction"""
        vocab = self.query_vocabulary(domain)
        if not vocab:
            return False
        
        # Verify code_intent references defined primitives
        intent_tokens = set(code_intent.lower().split())
        primitive_terms = set(vocab.keys())
        return len(intent_tokens & primitive_terms) > 0
    
    def _identify_nouns(self, tokens: List[str]) -> Set[str]:
        # Simplified: words that don't look like verbs
        return {t for t in tokens if not t.endswith(('ing', 'ed', 'ate', 'ize'))}
    
    def _identify_verbs(self, tokens: List[str]) -> Set[str]:
        return {t for t in tokens if t.endswith(('ing', 'ed', 'ate', 'ize', 'ify'))}
    
    def _relates(self, noun: str, verb: str, context: str) -> bool:
        return f"{noun}" in context and f"{verb}" in context
    
    def _composable(self, n1: str, n2: str) -> bool:
        return len(n1) > 3 and len(n2) > 3  # Simplified heuristic