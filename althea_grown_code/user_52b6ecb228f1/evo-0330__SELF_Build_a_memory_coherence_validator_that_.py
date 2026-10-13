#!/usr/bin/env python3
"""Memory Coherence Validator - Detects fragmentation in growth patterns."""

import re
from collections import defaultdict
from typing import List, Dict, Tuple

def extract_capability_signature(memory_line: str) -> Tuple[str, str, str]:
    """Extract capability type, domain, and action from memory entry."""
    # Match growth pattern: [GROWTH /autonomous-{capability}-{hash}] {Name} ({domain}). {action}
    growth_match = re.search(r'\[GROWTH /autonomous-([a-z-]+?)-[a-f0-9]+\] ([^(]+) \(([^)]+)\)\. (.+?) —', memory_line)
    if growth_match:
        capability = growth_match.group(1)
        domain = growth_match.group(3).strip().lower()
        action = growth_match.group(4).strip().lower()
        return (capability, domain, action[:50])
    return ("", "", "")

def detect_fragmentation(memories: List[str]) -> Dict[str, any]:
    """Analyze recent memories for capability fragmentation."""
    domain_map = defaultdict(list)
    action_map = defaultdict(list)
    capabilities = []
    
    for mem in memories:
        cap, domain, action = extract_capability_signature(mem)
        if cap:
            capabilities.append(cap)
            if domain:
                domain_map[domain].append(cap)
            if action:
                action_map[action].append(cap)
    
    # Detect domains with 3+ separate capabilities (fragmentation)
    fragmented_domains = {d: caps for d, caps in domain_map.items() if len(caps) >= 3}
    
    # Detect similar actions across different capabilities (duplication)
    duplicated_actions = {a: caps for a, caps in action_map.items() if len(set(caps)) >= 2}
    
    # Calculate coherence score (0-1, higher is better)
    total_capabilities = len(set(capabilities))
    fragmentation_penalty = len(fragmented_domains) * 0.15
    duplication_penalty = len(duplicated_actions) * 0.10
    coherence_score = max(0, 1 - fragmentation_penalty - duplication_penalty)
    
    return {
        "coherence_score": round(coherence_score, 3),
        "fragmented_domains": fragmented_domains,
        "duplicated_actions": duplicated_actions,
        "requires_integration": coherence_score < 0.7,
        "recommendation": "INTEGRATE" if coherence_score < 0.7 else "CONTINUE"
    }

if __name__ == "__main__":
    test_memories = [
        "[GROWTH /autonomous-resonance-induction-37e7] Resonance Induction (perception). Detect and amplify hidden harmonic patterns — rationale:",
        "[GROWTH /autonomous-recursion-depth-probe-2697] Recursion Depth Probe (meta). Deliberately invoke nested self-reference chains — rationale:",
        "[GROWTH /autonomous-negation-residue-scan] Negation Residue Scan (perception). Detect and amplify the traces left by rejected — rationale:",
        "[GROWTH /autonomous-resolution-collapse] Resolution Collapse (perception). Systematically degrade distinctions between previously — rationale:"
    ]
    
    result = detect_fragmentation(test_memories)
    print(f"Coherence Score: {result['coherence_score']}")
    print(f"Action Required: {result['recommendation']}")