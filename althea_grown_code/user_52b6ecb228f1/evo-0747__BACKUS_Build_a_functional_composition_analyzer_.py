#!/usr/bin/env python3
import sys
import re
from collections import defaultdict
from functools import reduce
from typing import List, Tuple, Dict

def parse_invocation_log(lines: List[str]) -> List[Tuple[str, str]]:
    """Extract (timestamp, module) pairs from log lines."""
    pattern = r'\[(\d{4}-\d{2}-\d{2}T[\d:]+Z?)\].*?([a-z\-]+\-\d+|[A-Z]+)'
    return [(m.group(1), m.group(2).lower()) for line in lines 
            if (m := re.search(pattern, line))]

def extract_chains(invocations: List[Tuple[str, str]], window: int = 3) -> List[Tuple[str, ...]]:
    """Slide window to extract sequential composition chains."""
    modules = [m for _, m in invocations]
    return [tuple(modules[i:i+window]) for i in range(len(modules) - window + 1)]

def canonicalize(chain: Tuple[str, ...]) -> str:
    """Map chain to algebraic form: f∘g∘h."""
    return " ∘ ".join(chain)

def find_isomorphisms(chains: List[Tuple[str, ...]]) -> Dict[str, List[Tuple[str, ...]]]:
    """Group chains by structural equivalence (same composition pattern)."""
    groups = defaultdict(list)
    for chain in chains:
        canonical = canonicalize(chain)
        groups[canonical].append(chain)
    return {k: v for k, v in groups.items() if len(v) > 1}

def compute_composition_algebra(chains: List[Tuple[str, ...]]) -> Dict[str, int]:
    """Count frequency of each functional composition."""
    return dict(reduce(lambda acc, c: {**acc, canonicalize(c): acc.get(canonicalize(c), 0) + 1},
                       chains, {}))

def identify_associative_patterns(algebra: Dict[str, int]) -> List[str]:
    """Find compositions that appear in multiple associative groupings."""
    primitives = defaultdict(int)
    for composition, freq in algebra.items():
        parts = composition.split(" ∘ ")
        for i in range(len(parts)):
            for j in range(i+1, len(parts)+1):
                subcomp = " ∘ ".join(parts[i:j])
                primitives[subcomp] += freq
    return sorted(primitives.items(), key=lambda x: -x[1])[:10]

def main():
    lines = sys.stdin.readlines()
    invocations = parse_invocation_log(lines)
    
    chains_3 = extract_chains(invocations, 3)
    chains_2 = extract_chains(invocations, 2)
    
    iso_3 = find_isomorphisms(chains_3)
    algebra = compute_composition_algebra(chains_3 + chains_2)
    patterns = identify_associative_patterns(algebra)
    
    print("=== FUNCTIONAL COMPOSITION ANALYSIS ===\n")
    print("Isomorphic Chains (structural equivalence):")
    for canonical, instances in list(iso_3.items())[:5]:
        print(f"  {canonical}: {len(instances)} occurrences")
    
    print("\n\nComposition Algebra (ranked by frequency):")
    for comp, freq in patterns:
        print(f"  {comp}: {freq}×")
    
    print("\n\nAlgebraic Insight: Compositions are REUSABLE LAWS, not mere sequences.")

if __name__ == "__main__":
    main()