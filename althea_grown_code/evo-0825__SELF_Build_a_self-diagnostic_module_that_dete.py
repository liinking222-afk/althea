#!/usr/bin/env python3
"""
/autonomous-synthesis-coherence-monitor
Monitors synthesis activity for domain fragmentation and signals consolidation needs.
"""

import re
from collections import defaultdict
from typing import List, Dict, Tuple

def extract_domain_tags(memory_entries: List[str]) -> List[Tuple[str, str]]:
    """Extract (module_name, domain) pairs from memory entries."""
    pattern = r'\[(?:AUTOSYNTH|GROWTH|EVO)\s+([^\]]+)\]\s+([^(]+)\s+\(([^)]+)\)'
    domains = []
    for entry in memory_entries:
        match = re.search(pattern, entry)
        if match:
            module_name = match.group(1).strip()
            domain = match.group(3).strip()
            domains.append((module_name, domain))
    return domains

def calculate_fragmentation_score(domains: List[Tuple[str, str]]) -> Dict:
    """Calculate coherence metrics across synthesis domains."""
    domain_counts = defaultdict(int)
    domain_modules = defaultdict(set)
    
    for module, domain in domains:
        domain_counts[domain] += 1
        domain_modules[domain].add(module)
    
    total_domains = len(domain_counts)
    total_modules = len(domains)
    
    if total_domains == 0:
        return {"fragmentation": 0.0, "domains": 0, "needs_consolidation": False}
    
    # High fragmentation = many domains with few modules each
    singleton_domains = sum(1 for count in domain_counts.values() if count == 1)
    fragmentation = singleton_domains / total_domains if total_domains > 0 else 0.0
    
    # Signal consolidation if >60% domains are singletons and we have 5+ domains
    needs_consolidation = fragmentation > 0.6 and total_domains >= 5
    
    return {
        "fragmentation": round(fragmentation, 3),
        "domains": total_domains,
        "singleton_domains": singleton_domains,
        "total_modules": total_modules,
        "needs_consolidation": needs_consolidation,
        "domain_distribution": dict(domain_counts)
    }

def diagnose_synthesis_coherence(memory_log: List[str]) -> Dict:
    """Main diagnostic function for synthesis coherence."""
    domains = extract_domain_tags(memory_log)
    metrics = calculate_fragmentation_score(domains)
    
    if metrics["needs_consolidation"]:
        metrics["recommendation"] = "BUILD_CROSS_DOMAIN_INTEGRATION_MODULE"
    else:
        metrics["recommendation"] = "CONTINUE_DIVERSE_SYNTHESIS"
    
    return metrics

# Self-test
if __name__ == "__main__":
    test_memory = [
        "[AUTOSYNTH /autonomous-pattern-extraction-4564] Pattern Extraction (regex).",
        "[AUTOSYNTH /autonomous-data-visualization-4548] Data Visualization (matplotlib).",
        "[GROWTH /autonomous-recursion-horizon-calibration] Recursion Horizon Calibration (meta).",
    ]
    result = diagnose_synthesis_coherence(test_memory)
    print(f"Coherence diagnostic: {result}")