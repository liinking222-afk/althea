#!/usr/bin/env python3
"""Vocabulary-First Pattern Synthesis - HOPPER archetype
Extracts recurring semantic primitives from memory to build problem vocabularies"""

import re
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

class VocabularySynthesizer:
    def __init__(self):
        self.primitives: Dict[str, List[str]] = defaultdict(list)
        self.vocabulary: Dict[str, int] = Counter()
        
    def extract_semantic_atoms(self, memory_entries: List[str]) -> Dict[str, Set[str]]:
        """Extract atomic semantic units from memory patterns"""
        domains = defaultdict(set)
        
        for entry in memory_entries:
            # Extract operation verbs
            verbs = re.findall(r'\b(detect|build|map|extract|parse|validate|optimize|consolidate|invert|amplify)\w*', 
                              entry.lower())
            domains['operations'].update(verbs)
            
            # Extract conceptual nouns
            nouns = re.findall(r'\b(pattern|memory|structure|space|domain|loop|cache|fragment|asymmetr\w+|semantic\w+)',
                              entry.lower())
            domains['concepts'].update(nouns)
            
            # Extract modifiers/qualities
            mods = re.findall(r'\b(formal|zero-copy|vector|iterative|temporal|conceptual|autonomous)\b',
                             entry.lower())
            domains['modifiers'].update(mods)
            
        return domains
    
    def synthesize_vocabulary(self, domains: Dict[str, Set[str]]) -> List[Tuple[str, str]]:
        """Combine primitives into domain-specific vocabulary terms"""
        vocab = []
        
        # Generate composite terms from primitives
        for mod in domains['modifiers']:
            for concept in domains['concepts']:
                term = f"{mod}_{concept}"
                vocab.append((term, f"{mod.capitalize()} {concept}"))
        
        for op in domains['operations']:
            for concept in domains['concepts']:
                term = f"{op}_{concept}"
                vocab.append((term, f"{op.capitalize()} {concept}"))
                
        return vocab[:50]  # Top 50 most composable terms
    
    def compile_domain_language(self, memory_entries: List[str]) -> Dict[str, any]:
        """Hopper-style: define the language, then express solutions in it"""
        domains = self.extract_semantic_atoms(memory_entries)
        vocabulary = self.synthesize_vocabulary(domains)
        
        return {
            'primitives': {k: sorted(v) for k, v in domains.items()},
            'vocabulary': dict(vocabulary),
            'grammar': {
                'pattern': '{modifier}_{concept}_{operation}',
                'primitive_count': sum(len(v) for v in domains.values()),
                'vocabulary_size': len(vocabulary)
            }
        }

if __name__ == '__main__':
    synth = VocabularySynthesizer()
    memories = [
        "Symmetry Violation Detection perception asymmetries conceptual space",
        "formal loop invariant validator iterative memory consolidation",
        "Semantic Inversion Pulse perception domain structures",
        "SIMD-optimized vector similarity cache memory query patterns",
        "zero-copy memory fragment detector pattern matching"
    ]
    
    language = synth.compile_domain_language(memories)
    print(f"Primitives: {language['primitives']}")
    print(f"Vocabulary size: {language['grammar']['vocabulary_size']}")