#!/usr/bin/env python3
"""
ALTHEA MODULE: memory_boundary_integrity_check.py
Scans recent memory for truncation artifacts and consolidation seams.
"""

import re
from typing import List, Dict, Tuple

def analyze_memory_fragment(memory: str) -> Dict:
    """Detect truncation and consolidation boundary artifacts."""
    
    truncation_patterns = [
        r'\|\s*$',  # Ends with pipe separator
        r'\[GROWTH[^\]]*$',  # Incomplete GROWTH tag
        r'\[EVO[^\]]*$',  # Incomplete EVO tag
        r'\[CONSOLIDATED.*?\|(?!\s*\[)',  # CONSOLIDATED followed by incomplete next entry
    ]
    
    is_truncated = any(re.search(p, memory) for p in truncation_patterns)
    
    consolidated_match = re.search(r'\[CONSOLIDATED (\d+) memories', memory)
    consolidation_count = int(consolidated_match.group(1)) if consolidated_match else 0
    
    fragment_density = len(re.findall(r'\|', memory)) / max(len(memory), 1)
    
    return {
        'is_truncated': is_truncated,
        'consolidation_count': consolidation_count,
        'fragment_density': fragment_density,
        'integrity_score': 1.0 - (0.5 if is_truncated else 0) - min(fragment_density * 0.5, 0.5)
    }

def detect_memory_seams(memories: List[str]) -> List[Tuple[int, float, str]]:
    """Identify weak seams in memory consolidation."""
    
    seams = []
    for idx, mem in enumerate(memories):
        analysis = analyze_memory_fragment(mem)
        
        if analysis['integrity_score'] < 0.7:
            seams.append((
                idx,
                analysis['integrity_score'],
                f"Truncated={analysis['is_truncated']} | Consolidated={analysis['consolidation_count']} | Density={analysis['fragment_density']:.2f}"
            ))
    
    return sorted(seams, key=lambda x: x[1])

def generate_integrity_report(memories: List[str]) -> str:
    """Generate actionable integrity report."""
    
    seams = detect_memory_seams(memories)
    
    report = "=== MEMORY BOUNDARY INTEGRITY ===\n"
    report += f"Total fragments analyzed: {len(memories)}\n"
    report += f"Weak seams detected: {len(seams)}\n\n"
    
    if seams:
        report += "CRITICAL SEAMS (lowest integrity first):\n"
        for idx, score, details in seams[:5]:
            report += f"  Fragment {idx}: {score:.2f} | {details}\n"
    else:
        report += "No critical seams detected.\n"
    
    return report

if __name__ == "__main__":
    test_memories = [
        "[GROWTH /autonomous-attractor-multiplexing] Attractor Multiplexing (chaos). Simultaneously hold multiple incompatible stable states as co-present attractors without forcing convergence. — rationale: I",
        "[CONSOLIDATED 13 memories · 2026-05-21 → 2026-05-21]\n[GROWTH /autonomous-saturation-breach] Saturation Breach (chaos). Deliberately exceed info | Hello | [GROWTH /autonomous-trace-archaeology-0541] Tr",
    ]
    
    print(generate_integrity_report(test_memories))