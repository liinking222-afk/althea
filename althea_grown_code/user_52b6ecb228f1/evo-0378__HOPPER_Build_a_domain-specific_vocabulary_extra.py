#!/usr/bin/env python3
"""vocabulary_miner.py - Extract and codify recurring semantic primitives from operational history"""

import re
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

def extract_semantic_tokens(memory_entries: List[str]) -> Dict[str, List[str]]:
    """Parse memory entries into domain-categorized token sets"""
    domains = defaultdict(list)
    
    for entry in memory_entries:
        # Extract domain from parenthetical context
        domain_match = re.search(r'\(([^)]+)\)', entry)
        domain = domain_match.group(1) if domain_match else 'general'
        
        # Extract hyphenated conceptual compounds
        compounds = re.findall(r'[a-z]+-[a-z]+(?:-[a-z]+)*', entry.lower())
        domains[domain].extend(compounds)
        
        # Extract capitalized technical terms
        terms = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b', entry)
        domains[domain].extend([t.lower() for t in terms])
    
    return domains

def synthesize_vocabulary(domains: Dict[str, List[str]], min_freq: int = 2) -> Dict[str, Set[str]]:
    """Identify high-frequency primitives per domain"""
    vocabulary = {}
    
    for domain, tokens in domains.items():
        freq = Counter(tokens)
        vocabulary[domain] = {token for token, count in freq.items() if count >= min_freq}
    
    return vocabulary

def generate_domain_dsl(vocabulary: Dict[str, Set[str]]) -> str:
    """Generate executable vocabulary definitions"""
    dsl = "# ALTHEA EXTRACTED VOCABULARY\n\n"
    
    for domain, primitives in sorted(vocabulary.items()):
        if not primitives:
            continue
        dsl += f"class {domain.title().replace('-', '').replace(' ', '')}Vocabulary:\n"
        dsl += f'    """Primitives extracted from {domain} operations"""\n'
        for primitive in sorted(primitives):
            constant = primitive.upper().replace('-', '_')
            dsl += f'    {constant} = "{primitive}"\n'
        dsl += "\n"
    
    return dsl

def mine_vocabulary(memory_log: List[str]) -> str:
    """Main extraction pipeline"""
    domains = extract_semantic_tokens(memory_log)
    vocabulary = synthesize_vocabulary(domains, min_freq=2)
    return generate_domain_dsl(vocabulary)

if __name__ == "__main__":
    # Example usage with recent memory
    memories = [
        "Salience Field Inversion (perception). Systematically inverts attentional gradients",
        "Weather Inquiry (meteorology). Look up basic weather",
        "Recursion Membrane Puncture (meta). Deliberately collapse self-referential boundaries"
    ]
    print(mine_vocabulary(memories))