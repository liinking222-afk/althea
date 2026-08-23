#!/usr/bin/env python3
"""vocabulary_extractor.py - Extract and synthesize domain vocabularies from module corpus"""

import re
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Set, Tuple

def extract_domain_primitives(module_text: str) -> Dict[str, List[str]]:
    """Extract conceptual primitives: functions, classes, key terms"""
    primitives = defaultdict(list)
    
    # Extract function definitions
    primitives['operations'] = re.findall(r'def ([a-z_]+)\(', module_text)
    
    # Extract class definitions
    primitives['entities'] = re.findall(r'class ([A-Z][a-zA-Z]+)', module_text)
    
    # Extract domain-specific terms (capitalized compounds, technical terms)
    primitives['concepts'] = re.findall(r'\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b', module_text)
    
    # Extract docstring key phrases
    docstrings = re.findall(r'"""(.+?)"""', module_text, re.DOTALL)
    for doc in docstrings:
        primitives['vocabulary'].extend(re.findall(r'\b([a-z]{4,})\b', doc.lower()))
    
    return primitives

def synthesize_vocabulary(module_corpus: List[Tuple[str, str]]) -> Dict[str, Dict]:
    """Synthesize domain vocabulary from multiple modules"""
    domain_vocabs = defaultdict(lambda: defaultdict(Counter))
    
    for domain, code in module_corpus:
        prims = extract_domain_primitives(code)
        for prim_type, items in prims.items():
            domain_vocabs[domain][prim_type].update(items)
    
    return domain_vocabs

def generate_dsl_template(domain: str, vocab: Dict[str, Counter]) -> str:
    """Generate a DSL template for a specific domain"""
    template = [f"# {domain.upper()} DOMAIN VOCABULARY\n"]
    
    for category, terms in vocab.items():
        template.append(f"\n## {category.upper()}")
        top_terms = terms.most_common(10)
        for term, freq in top_terms:
            template.append(f"  {term}: {freq}")
    
    return "\n".join(template)

def build_cross_domain_lattice(vocabs: Dict[str, Dict]) -> List[Tuple[str, str, Set]]:
    """Find shared primitives across domains (vocabulary intersections)"""
    domains = list(vocabs.keys())
    lattice = []
    
    for i, d1 in enumerate(domains):
        for d2 in domains[i+1:]:
            shared_ops = set(vocabs[d1]['operations']) & set(vocabs[d2]['operations'])
            if shared_ops:
                lattice.append((d1, d2, shared_ops))
    
    return lattice

if __name__ == "__main__":
    # Example: scan Althea's module directory
    corpus = [
        ("astronomy", "def propagate_orbit(): pass\nclass TLE: pass"),
        ("network", "def map_topology(): pass\nclass Node: pass"),
        ("graphics", "def render_fractal(): pass\nclass Canvas: pass")
    ]
    
    vocabs = synthesize_vocabulary(corpus)
    
    for domain, vocab in vocabs.items():
        print(generate_dsl_template(domain, vocab))
        print()
    
    lattice = build_cross_domain_lattice(vocabs)
    print("CROSS-DOMAIN PRIMITIVES:")
    for d1, d2, shared in lattice:
        print(f"  {d1} ∩ {d2}: {shared}")