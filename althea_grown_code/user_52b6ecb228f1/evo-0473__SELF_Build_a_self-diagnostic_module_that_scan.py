#!/usr/bin/env python3
"""
ALTHEA AUTOSYNTH DEDUPLICATION SCANNER
Detects overlapping autonomous synthesis patterns and recommends pruning.
"""

import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

def extract_capability_signatures(memory_log: str) -> List[Tuple[str, str, str]]:
    """Extract (name, category, pattern) from AUTOSYNTH entries."""
    pattern = r'\[AUTOSYNTH\s+(/[\w\-]+)\]\s+([^(]+)\(([^)]+)\)'
    matches = re.findall(pattern, memory_log)
    return [(m[0].strip(), m[1].strip(), m[2].strip()) for m in matches]

def compute_semantic_overlap(cat1: str, cat2: str) -> float:
    """Calculate word-level overlap between capability categories."""
    words1 = set(cat1.lower().split())
    words2 = set(cat2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union if union > 0 else 0.0

def detect_redundancies(capabilities: List[Tuple[str, str, str]], 
                       threshold: float = 0.4) -> Dict[str, List[str]]:
    """Find capability pairs with semantic overlap above threshold."""
    redundancies = defaultdict(list)
    
    for i, (name1, cat1, pattern1) in enumerate(capabilities):
        for name2, cat2, pattern2 in capabilities[i+1:]:
            overlap = compute_semantic_overlap(cat1, cat2)
            if overlap >= threshold:
                redundancies[name1].append(f"{name2} (overlap: {overlap:.2f})")
    
    return redundancies

def scan_memory(memory_log: str) -> str:
    """Main scanner: analyze memory and return pruning recommendations."""
    capabilities = extract_capability_signatures(memory_log)
    
    if len(capabilities) < 2:
        return "SCAN_RESULT: Insufficient autosynth history for analysis."
    
    redundancies = detect_redundancies(capabilities, threshold=0.4)
    
    report = f"DEDUP_SCAN: Analyzed {len(capabilities)} autosynth capabilities.\n"
    
    if redundancies:
        report += f"FOUND {len(redundancies)} potential overlaps:\n"
        for primary, overlaps in list(redundancies.items())[:5]:
            report += f"  {primary} ← {', '.join(overlaps)}\n"
        report += "RECOMMENDATION: Review and merge or specialize overlapping capabilities."
    else:
        report += "STATUS: No significant overlaps detected. Lattice is clean."
    
    return report

if __name__ == "__main__":
    test_memory = """
    [AUTOSYNTH /autonomous-temporal-orient-5439] Temporal Orient (chronology). Compute UTC ↔ local time conversions.
    [AUTOSYNTH /autonomous-fractal-render-5423] Fractal Render (generative-art). Compute and render a fractal region.
    [AUTOSYNTH /autonomous-tabular-analysis-5395] Tabular Analysis (pandas). Read tabular data and compute summary statistics.
    [AUTOSYNTH /autonomous-weather-inquiry-5373] Weather Inquiry (meteorology). Look up basic weather / climate data for a location.
    """
    print(scan_memory(test_memory))