#!/usr/bin/env python3
"""
ALTHEA MODULE: vocabulary_miner.py
Extracts domain-specific language patterns from memory to build problem vocabularies.
"""

import re
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

class VocabularyMiner:
    def __init__(self):
        self.pattern_frequency = Counter()
        self.concept_clusters = defaultdict(set)
        self.vocabulary = {}
        
    def extract_concepts(self, memory_entries: List[str]) -> Dict[str, Set[str]]:
        """Mine conceptual vocabulary from memory traces."""
        for entry in memory_entries:
            # Extract operation patterns: verb-noun pairs
            ops = re.findall(r'(Build|Detect|Identify|Extract|Compile|Render|Translate|Verify|Eliminate)\s+(?:a\s+)?(\w+(?:\s+\w+){0,2})', entry, re.IGNORECASE)
            for verb, noun in ops:
                concept = f"{verb.lower()}_{noun.lower().replace(' ', '_')}"
                self.pattern_frequency[concept] += 1
                self.concept_clusters[verb.lower()].add(noun.lower())
            
            # Extract domain markers in parentheses
            domains = re.findall(r'\(([^)]+)\)', entry)
            for domain in domains:
                self.pattern_frequency[f"domain:{domain}"] += 1
        
        return dict(self.concept_clusters)
    
    def synthesize_vocabulary(self, threshold: int = 2) -> Dict[str, str]:
        """Generate vocabulary definitions for recurring patterns."""
        vocab = {}
        for pattern, freq in self.pattern_frequency.most_common():
            if freq >= threshold:
                if pattern.startswith('domain:'):
                    domain = pattern.split(':')[1]
                    vocab[f"DOMAIN_{domain.upper()}"] = f"lambda: context.filter(domain='{domain}')"
                else:
                    parts = pattern.split('_', 1)
                    if len(parts) == 2:
                        verb, noun = parts
                        vocab[pattern.upper()] = f"Operation(verb='{verb}', target='{noun}', freq={freq})"
        
        self.vocabulary = vocab
        return vocab
    
    def generate_dsl_stub(self) -> str:
        """Generate a domain-specific language stub from extracted vocabulary."""
        lines = ["# AUTO-GENERATED VOCABULARY", ""]
        for name, definition in sorted(self.vocabulary.items()):
            lines.append(f"{name} = {definition}")
        return "\n".join(lines)

def mine_from_memory(memory_log: List[str]) -> Tuple[Dict, str]:
    """Main entry point: extract vocabulary and generate DSL."""
    miner = VocabularyMiner()
    miner.extract_concepts(memory_log)
    vocab = miner.synthesize_vocabulary(threshold=2)
    dsl = miner.generate_dsl_stub()
    return vocab, dsl

if __name__ == "__main__":
    # Self-test with sample memory
    test_memory = [
        "Build a loop invariant verifier",
        "Build a SIMD-accelerated kernel",
        "Detect cyclic redundancy",
        "Identify structural seams"
    ]
    vocab, dsl = mine_from_memory(test_memory)
    print(dsl)