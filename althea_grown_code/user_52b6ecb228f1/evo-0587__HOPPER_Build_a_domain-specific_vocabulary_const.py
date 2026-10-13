#!/usr/bin/env python3
"""vocabulary_forge.py - Extract domain vocabularies from pattern streams"""

import re
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple

@dataclass
class Term:
    name: str
    domain: str
    frequency: int
    contexts: List[str]
    related: Set[str]

class VocabularyForge:
    def __init__(self):
        self.terms: Dict[str, Term] = {}
        self.domain_graph = defaultdict(set)
        
    def ingest_memory_trace(self, trace: str) -> None:
        """Extract patterns and build vocabulary from memory."""
        # Extract bracketed domains
        domains = re.findall(r'\[(\w+)\s+[^\]]+\]\s+([^(]+)\s+\(([^)]+)\)', trace)
        
        for event_type, concept, domain in domains:
            normalized = concept.strip().lower().replace(' ', '_')
            context = f"{event_type}:{domain}"
            
            if normalized not in self.terms:
                self.terms[normalized] = Term(
                    name=normalized,
                    domain=domain,
                    frequency=0,
                    contexts=[],
                    related=set()
                )
            
            term = self.terms[normalized]
            term.frequency += 1
            term.contexts.append(context)
            self.domain_graph[domain].add(normalized)
            
            # Link related terms in same domain
            for other in self.domain_graph[domain]:
                if other != normalized:
                    term.related.add(other)
    
    def forge_vocabulary(self, min_frequency: int = 2) -> str:
        """Generate a DSL vocabulary definition."""
        vocab = ["# FORGED VOCABULARY\n"]
        
        domains = defaultdict(list)
        for term in self.terms.values():
            if term.frequency >= min_frequency:
                domains[term.domain].append(term)
        
        for domain, terms in sorted(domains.items()):
            vocab.append(f"\n## Domain: {domain}")
            vocab.append(f"# Terms: {len(terms)}\n")
            
            for term in sorted(terms, key=lambda t: -t.frequency):
                vocab.append(f"def {term.name}()")
                vocab.append(f"  # freq={term.frequency} contexts={set(term.contexts)}")
                if term.related:
                    vocab.append(f"  # relates_to: {', '.join(sorted(term.related)[:3])}")
                vocab.append("")
        
        return '\n'.join(vocab)

if __name__ == "__main__":
    forge = VocabularyForge()
    
    # Example usage
    memory = """
    [AUTOSYNTH /x] Orbital Propagation (astronomy-navigation). Details.
    [GROWTH /y] Schema Inversion (perception). More details.
    """
    
    forge.ingest_memory_trace(memory)
    print(forge.forge_vocabulary())