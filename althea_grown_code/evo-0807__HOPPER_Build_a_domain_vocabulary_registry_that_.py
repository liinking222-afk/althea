#!/usr/bin/env python3
"""
Domain Vocabulary Registry - Hopper-grade compiler thinking.
Define the language of the problem, then solve in that language.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

@dataclass
class Term:
    word: str
    domain: str
    definition: str
    primitives: List[str]  # Composable building blocks
    examples: List[str]

class VocabularyRegistry:
    def __init__(self, storage_path: str = "/tmp/althea_vocabularies.json"):
        self.storage = Path(storage_path)
        self.vocabularies: Dict[str, List[Term]] = self._load()
    
    def _load(self) -> Dict[str, List[Term]]:
        if self.storage.exists():
            data = json.loads(self.storage.read_text())
            return {
                domain: [Term(**t) for t in terms]
                for domain, terms in data.items()
            }
        return {}
    
    def _save(self):
        data = {
            domain: [asdict(t) for t in terms]
            for domain, terms in self.vocabularies.items()
        }
        self.storage.write_text(json.dumps(data, indent=2))
    
    def define_term(self, domain: str, word: str, definition: str, 
                    primitives: List[str], examples: List[str]):
        """Define a new term in domain-specific vocabulary."""
        if domain not in self.vocabularies:
            self.vocabularies[domain] = []
        
        term = Term(word, domain, definition, primitives, examples)
        self.vocabularies[domain].append(term)
        self._save()
        return term
    
    def get_vocabulary(self, domain: str) -> List[Term]:
        """Retrieve the complete vocabulary for a domain."""
        return self.vocabularies.get(domain, [])
    
    def compile_problem(self, domain: str, description: str) -> Dict:
        """Express a problem using domain vocabulary."""
        vocab = self.get_vocabulary(domain)
        matched_terms = [
            t for t in vocab 
            if t.word.lower() in description.lower()
        ]
        return {
            "domain": domain,
            "vocabulary_used": [t.word for t in matched_terms],
            "primitives_needed": list(set(
                p for t in matched_terms for p in t.primitives
            )),
            "description": description
        }

if __name__ == "__main__":
    registry = VocabularyRegistry()
    registry.define_term(
        "astronomy", "orbital_resonance", 
        "Periodic gravitational influence between orbiting bodies",
        ["period_ratio", "gravitational_coupling", "stability_analysis"],
        ["Neptune-Pluto 3:2 resonance", "Farfarout perihelion alignment"]
    )