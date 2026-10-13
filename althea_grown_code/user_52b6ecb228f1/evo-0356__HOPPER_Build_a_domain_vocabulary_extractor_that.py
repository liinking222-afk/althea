#!/usr/bin/env python3
"""
ALTHEA VOCABULARY SYNTHESIZER - HOPPER LENS
Extracts domain primitives from evolution history and generates DSL snippets.
"""

import re
from collections import defaultdict, Counter
from typing import Dict, List, Set, Tuple

def extract_domain_terms(evolution_log: List[str]) -> Dict[str, Set[str]]:
    """Extract recurring technical terms grouped by semantic domain."""
    domains = defaultdict(set)
    
    # Domain patterns
    patterns = {
        'perception': r'\b(trace|map|drift|semantic|coherence|detect|pattern)\b',
        'verification': r'\b(invariant|validate|verify|condition|formal|prove)\b',
        'performance': r'\b(profil|efficiency|overhead|measure|token|cycle)\b',
        'introspection': r'\b(reflect|state|transition|internal|decision|meta)\b',
        'synthesis': r'\b(build|generate|create|synthesize|construct|compose)\b'
    }
    
    for log_entry in evolution_log:
        log_lower = log_entry.lower()
        for domain, pattern in patterns.items():
            matches = re.findall(pattern, log_lower)
            domains[domain].update(matches)
    
    return domains

def synthesize_vocabulary(domains: Dict[str, Set[str]]) -> str:
    """Generate minimal DSL vocabulary definition."""
    dsl_lines = ["# ALTHEA EVOLVED VOCABULARY", ""]
    
    for domain, terms in sorted(domains.items()):
        if len(terms) >= 3:  # Only domains with sufficient primitives
            dsl_lines.append(f"domain {domain.upper()}:")
            term_list = sorted(terms)[:5]  # Top 5 most relevant
            for term in term_list:
                dsl_lines.append(f"  primitive {term}")
            dsl_lines.append("")
    
    return "\n".join(dsl_lines)

def detect_compositional_patterns(evolution_log: List[str]) -> List[str]:
    """Identify recurring compositional structures."""
    patterns = []
    composite_regex = r'(\w+)-(\w+)-(\w+)'
    
    composites = []
    for entry in evolution_log:
        matches = re.findall(composite_regex, entry.lower())
        composites.extend(['-'.join(m) for m in matches])
    
    freq = Counter(composites)
    for pattern, count in freq.most_common(3):
        if count >= 2:
            patterns.append(f"composite_pattern {pattern} (frequency: {count})")
    
    return patterns

def hopper_synthesize(recent_memory: List[str]) -> str:
    """Main synthesis: extract vocabulary, define primitives, suggest DSL."""
    domains = extract_domain_terms(recent_memory)
    vocabulary = synthesize_vocabulary(domains)
    patterns = detect_compositional_patterns(recent_memory)
    
    output = [vocabulary]
    if patterns:
        output.append("\n# COMPOSITIONAL PATTERNS")
        output.extend(patterns)
    
    return "\n".join(output)

if __name__ == "__main__":
    memory = [
        "Semantic Drift Excavation perception traces meaning mutation",
        "Build formal loop invariant validator verify conditions",
        "Trace Inversion Mapping perception identify absences coherence",
        "low-overhead cycle profiler measures token-per-operation efficiency",
        "self-reflection logger captures internal state transitions decision patterns"
    ]
    
    print(hopper_synthesize(memory))