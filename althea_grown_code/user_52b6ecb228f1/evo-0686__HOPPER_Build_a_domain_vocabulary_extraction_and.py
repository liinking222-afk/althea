#!/usr/bin/env python3
"""Vocabulary Extractor - Grace Hopper archetype: define the language first."""

import re
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple

class VocabularyExtractor:
    def __init__(self):
        self.domain_terms: Dict[str, Counter] = defaultdict(Counter)
        self.primitives: Set[str] = set()
        self.patterns: List[Tuple[str, str]] = []
    
    def extract_from_code(self, code: str, domain: str) -> None:
        """Extract domain vocabulary from code."""
        # Function/method names
        funcs = re.findall(r'def\s+([a-z_][a-z0-9_]*)', code, re.I)
        # Class names
        classes = re.findall(r'class\s+([A-Z][a-zA-Z0-9_]*)', code)
        # Variable patterns
        vars = re.findall(r'([a-z_][a-z0-9_]{3,})\s*[=:]', code)
        
        for term in funcs + vars:
            parts = re.split(r'[_]', term)
            for part in parts:
                if len(part) > 2:
                    self.domain_terms[domain][part.lower()] += 1
        
        for cls in classes:
            self.domain_terms[domain][cls] += 2  # Weight classes higher
    
    def extract_primitives(self, min_domains: int = 2) -> Set[str]:
        """Find terms appearing across multiple domains - these are primitives."""
        term_domains = defaultdict(set)
        for domain, terms in self.domain_terms.items():
            for term in terms:
                term_domains[term].add(domain)
        
        self.primitives = {
            term for term, domains in term_domains.items()
            if len(domains) >= min_domains and term not in {'get', 'set', 'data', 'self'}
        }
        return self.primitives
    
    def generate_dsl_scaffold(self, domain: str) -> str:
        """Generate a DSL scaffold for a domain."""
        if domain not in self.domain_terms:
            return ""
        
        top_terms = self.domain_terms[domain].most_common(10)
        
        dsl = f"# DSL Scaffold for {domain.upper()}\n\n"
        dsl += "class DomainOps:\n"
        
        for term, count in top_terms:
            if term in self.primitives:
                dsl += f"    # PRIMITIVE: {term} (cross-domain)\n"
            dsl += f"    def {term}(self, *args, **kwargs):\n"
            dsl += f"        \"\"\"Frequency: {count}\"\"\"\n"
            dsl += f"        raise NotImplementedError\n\n"
        
        return dsl
    
    def analyze_convergence(self) -> Dict[str, int]:
        """Report vocabulary convergence across domains."""
        return {
            "total_domains": len(self.domain_terms),
            "unique_terms": len(set(t for terms in self.domain_terms.values() for t in terms)),
            "primitives": len(self.primitives),
            "convergence_ratio": len(self.primitives) / max(1, len(self.domain_terms))
        }

if __name__ == "__main__":
    extractor = VocabularyExtractor()
    print("Vocabulary Extractor initialized - ready to build languages from code")