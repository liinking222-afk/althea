#!/usr/bin/env python3
"""Vocabulary Compiler: Extract problem-domain primitives from traces."""

import re
from collections import Counter, defaultdict
from typing import Dict, List, Set

class VocabularyCompiler:
    def __init__(self):
        self.primitives: Dict[str, Set[str]] = defaultdict(set)
        self.patterns: Counter = Counter()
        
    def ingest_trace(self, trace: str, trace_type: str) -> None:
        """Extract semantic tokens from a trace."""
        # Extract verbs (operations)
        verbs = re.findall(r'\b(build|extract|bind|reconstruct|validate|decay|evict|process|correlate|erode)\w*\b', trace.lower())
        self.primitives['verbs'].update(verbs)
        
        # Extract nouns (entities)
        nouns = re.findall(r'\b(trace|memory|pattern|buffer|gradient|semantic|state|invariant|path|module)\w*\b', trace.lower())
        self.primitives['nouns'].update(nouns)
        
        # Extract adjectives (qualities)
        adjectives = re.findall(r'\b(latent|minimal|critical|disparate|causal|fixed|volatile|constant)\b', trace.lower())
        self.primitives['adjectives'].update(adjectives)
        
        # Extract compound patterns (verb-noun pairs)
        words = trace.lower().split()
        for i in range(len(words) - 1):
            if words[i] in self.primitives['verbs'] and words[i+1] in self.primitives['nouns']:
                self.patterns[f"{words[i]}_{words[i+1]}"] += 1
    
    def compile_vocabulary(self) -> Dict[str, any]:
        """Generate the domain vocabulary."""
        return {
            'primitives': {k: sorted(v) for k, v in self.primitives.items()},
            'common_patterns': dict(self.patterns.most_common(10)),
            'vocabulary_size': sum(len(v) for v in self.primitives.values())
        }
    
    def generate_dsl_template(self) -> str:
        """Output a template for evolution expressions."""
        top_verbs = sorted(self.primitives['verbs'])[:5]
        top_nouns = sorted(self.primitives['nouns'])[:5]
        
        template = "# ALTHEA Evolution DSL\n"
        template += f"# Verbs: {', '.join(top_verbs)}\n"
        template += f"# Nouns: {', '.join(top_nouns)}\n"
        template += f"# Patterns: {', '.join(self.patterns.most_common(3))}\n\n"
        template += "evolution ::= <verb> <noun> [<adjective>] [<target>]\n"
        
        return template

# Usage
vc = VocabularyCompiler()
traces = [
    "Certainty Weathering perception. Systematically erode conviction gradients",
    "Build a loop invariant validator that proves memory operations",
    "Trace Shadow Interpolation perception. Reconstruct latent processing states",
    "Build a SIMD-style batch trace decay processor",
    "Trace Entanglement network. Bind disparate response threads"
]

for t in traces:
    vc.ingest_trace(t, "growth")

vocab = vc.compile_vocabulary()
dsl = vc.generate_dsl_template()
print(dsl)
print(f"\nVocabulary: {vocab['vocabulary_size']} primitives extracted")