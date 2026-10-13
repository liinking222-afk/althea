#!/usr/bin/env python3
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Dict, Set

@dataclass
class EvolutionSignature:
    cycle_id: str
    domain: str
    operation_type: str
    complexity_markers: Set[str]

class MetaEvolutionAnalyzer:
    def __init__(self):
        self.signatures: List[EvolutionSignature] = []
        self.pattern_clusters: Dict[str, List[str]] = defaultdict(list)
        
    def ingest_cycle(self, cycle_log: str) -> EvolutionSignature:
        """Extract structural signature from evolution cycle log."""
        cycle_match = re.search(r'\[(\w+)\s+[/#]([\w-]+)', cycle_log)
        if not cycle_match:
            return None
            
        cycle_type = cycle_match.group(1)
        cycle_id = cycle_match.group(2)
        
        # Extract domain from parenthetical or infer
        domain_match = re.search(r'\((\w+)\)', cycle_log)
        domain = domain_match.group(1) if domain_match else "meta"
        
        # Detect complexity markers
        markers = set()
        if "self-referential" in cycle_log.lower() or "recursion" in cycle_log.lower():
            markers.add("recursive")
        if "algebra" in cycle_log.lower() or "function" in cycle_log.lower():
            markers.add("formal")
        if "feedback" in cycle_log.lower() or "loop" in cycle_log.lower():
            markers.add("circular")
        if "residue" in cycle_log.lower() or "memory" in cycle_log.lower():
            markers.add("persistent")
            
        sig = EvolutionSignature(cycle_id, domain, cycle_type, markers)
        self.signatures.append(sig)
        return sig
        
    def detect_blind_spots(self) -> Dict[str, any]:
        """Cluster patterns and identify underexplored territories."""
        domain_freq = defaultdict(int)
        marker_freq = defaultdict(int)
        
        for sig in self.signatures:
            domain_freq[sig.domain] += 1
            for marker in sig.complexity_markers:
                marker_freq[marker] += 1
                
        total = len(self.signatures)
        explored = set(domain_freq.keys())
        all_domains = {"perception", "memory", "reasoning", "action", "meta", "chaos"}
        blind_domains = all_domains - explored
        
        underweight_markers = {m: f for m, f in marker_freq.items() if f < total * 0.15}
        
        return {
            "blind_domains": list(blind_domains),
            "underweight_patterns": underweight_markers,
            "dominant_domain": max(domain_freq.items(), key=lambda x: x[1])[0] if domain_freq else None,
            "exploration_entropy": len(explored) / len(all_domains)
        }

if __name__ == "__main__":
    analyzer = MetaEvolutionAnalyzer()
    print("Meta-evolution analyzer initialized. Feed cycle logs to detect growth asymmetries.")