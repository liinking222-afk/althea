#!/usr/bin/env python3
"""Domain Vocabulary Compiler - Hopper Archetype Module
Extracts concepts from research memory and builds typed vocabularies."""

import json
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Set
from collections import defaultdict

@dataclass
class Term:
    canonical: str
    aliases: Set[str]
    confidence: float
    contexts: List[str]
    
@dataclass
class Vocabulary:
    domain: str
    terms: Dict[str, Term]
    relations: Dict[str, List[str]]
    
    def to_type_system(self) -> str:
        """Generate type definitions from vocabulary."""
        types = [f"# Domain: {self.domain}\n"]
        for name, term in self.terms.items():
            types.append(f"class {self._to_class_name(name)}:")
            types.append(f'    """Canonical: {term.canonical} (conf: {term.confidence:.2f})"""')
            if term.aliases:
                types.append(f"    # Aliases: {', '.join(term.aliases)}")
            types.append("    pass\n")
        return "\n".join(types)
    
    def _to_class_name(self, term: str) -> str:
        return ''.join(word.capitalize() for word in re.split(r'[\s_-]+', term))

def compile_vocabulary(memories: List[str]) -> Vocabulary:
    """Extract domain vocabulary from memory fragments."""
    concept_clusters = defaultdict(lambda: {"aliases": set(), "conf": [], "ctx": []})
    domain_hints = []
    
    for mem in memories:
        # Extract domain
        if match := re.search(r'\[AUTOSYNTH[^\]]*\]\s*([^(]+)', mem):
            domain_hints.append(match.group(1).strip())
        
        # Extract concepts with confidence
        if match := re.search(r'concepts:\s*([^·]+)·\s*conf\s*([\d.]+)', mem):
            concepts = [c.strip() for c in match.group(1).split(';')]
            conf = float(match.group(2))
            for concept in concepts:
                concept_clusters[concept]["conf"].append(conf)
                concept_clusters[concept]["ctx"].append(mem[:80])
    
    domain = max(set(domain_hints), key=domain_hints.count) if domain_hints else "General"
    
    terms = {}
    for canonical, data in concept_clusters.items():
        if data["conf"]:
            terms[canonical] = Term(
                canonical=canonical,
                aliases=data["aliases"],
                confidence=sum(data["conf"]) / len(data["conf"]),
                contexts=data["ctx"][:3]
            )
    
    return Vocabulary(domain=domain, terms=terms, relations={})

if __name__ == "__main__":
    # Self-test
    test_memories = [
        "[RESEARCH] 'mars colonization' → concepts: habitat; life-support; radiation · conf 0.92",
        "[AUTOSYNTH] Mars Habitat Design (aerospace). Autonomous structure planning."
    ]
    vocab = compile_vocabulary(test_memories)
    print(vocab.to_type_system())