#!/usr/bin/env python3
"""
ALTHEA MODULE: Pattern Vocabulary Compiler
Extracts domain clusters from execution history and generates DSL fragments.
"""

import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import json

def extract_pattern_family(autosynth_name: str) -> Tuple[str, str]:
    """Extract domain and action from autosynth pattern name."""
    match = re.match(r'autonomous-([a-z]+)-([a-z]+)', autosynth_name)
    if match:
        return match.group(1), match.group(2)
    return "unknown", "unknown"

def analyze_memory_stream(memories: List[str]) -> Dict[str, List[str]]:
    """Group patterns by domain family."""
    families = defaultdict(list)
    for mem in memories:
        if 'AUTOSYNTH' in mem:
            match = re.search(r'/autonomous-([a-z-]+)\]', mem)
            if match:
                pattern = match.group(1)
                domain, action = extract_pattern_family(pattern)
                families[domain].append(action)
    return families

def generate_vocabulary(families: Dict[str, List[str]]) -> Dict[str, dict]:
    """Compile domain-specific micro-languages."""
    vocabulary = {}
    for domain, actions in families.items():
        action_freq = Counter(actions)
        if len(action_freq) >= 1:  # Sufficient signal
            vocabulary[domain] = {
                "verbs": list(action_freq.keys()),
                "frequency": dict(action_freq),
                "syntax": f"{domain}.<verb>(params)",
                "example": f"{domain}.{action_freq.most_common(1)[0][0]}(target)"
            }
    return vocabulary

def compile_dsl_fragment(vocab: Dict[str, dict]) -> str:
    """Generate executable DSL code fragment."""
    lines = ["# ALTHEA DOMAIN VOCABULARY", "class Vocabulary:"]
    for domain, spec in vocab.items():
        lines.append(f"    class {domain}:")
        for verb in spec['verbs']:
            lines.append(f"        @staticmethod")
            lines.append(f"        def {verb}(**kwargs): return ('{domain}', '{verb}', kwargs)")
    return "\n".join(lines)

def hopper_compile(memory_log: List[str]) -> str:
    """Main compiler: memories -> vocabulary -> DSL."""
    families = analyze_memory_stream(memory_log)
    vocabulary = generate_vocabulary(families)
    dsl = compile_dsl_fragment(vocabulary)
    manifest = {"vocabulary": vocabulary, "dsl_preview": dsl[:200]}
    return json.dumps(manifest, indent=2)

if __name__ == "__main__":
    test_memories = [
        "[AUTOSYNTH /autonomous-fractal-render-5653] Fractal Render",
        "[AUTOSYNTH /autonomous-schematic-render-5601] Schematic Render",
        "[AUTOSYNTH /autonomous-tabular-analysis-5585] Tabular Analysis"
    ]
    print(hopper_compile(test_memories))