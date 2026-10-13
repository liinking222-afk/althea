#!/usr/bin/env python3
"""Memory Consolidation Scanner - Detects and merges fragmented growth patterns"""

import re
from collections import defaultdict
from typing import Dict, List, Set, Tuple

class ConsolidationScanner:
    def __init__(self):
        self.semantic_clusters: Dict[str, List[str]] = defaultdict(list)
        self.merge_candidates: List[Tuple[str, str, float]] = []
        
    def extract_semantic_core(self, memory: str) -> Set[str]:
        """Extract core semantic tokens from memory string"""
        tokens = re.findall(r'\b[a-z]{4,}\b', memory.lower())
        stopwords = {'that', 'when', 'with', 'from', 'this', 'even', 'based'}
        return set(t for t in tokens if t not in stopwords)
    
    def compute_similarity(self, core1: Set[str], core2: Set[str]) -> float:
        """Jaccard similarity with density weighting"""
        if not core1 or not core2:
            return 0.0
        intersection = len(core1 & core2)
        union = len(core1 | core2)
        return intersection / union if union > 0 else 0.0
    
    def scan_memories(self, memories: List[str]) -> None:
        """Scan memory list for consolidation opportunities"""
        cores = [(i, self.extract_semantic_core(m)) for i, m in enumerate(memories)]
        
        for i, core1 in cores:
            for j, core2 in cores[i+1:]:
                sim = self.compute_similarity(core1, core2)
                if sim >= 0.25:  # Threshold for consolidation
                    self.merge_candidates.append((memories[i], memories[j], sim))
        
        self.merge_candidates.sort(key=lambda x: x[2], reverse=True)
    
    def generate_merge_report(self) -> str:
        """Generate actionable consolidation report"""
        if not self.merge_candidates:
            return "NO_FRAGMENTATION_DETECTED"
        
        report = []
        for mem1, mem2, sim in self.merge_candidates[:5]:
            report.append(f"MERGE[{sim:.2f}]: {mem1[:60]}... <-> {mem2[:60]}...")
        
        return "\n".join(report)
    
    def auto_consolidate(self, threshold: float = 0.4) -> List[str]:
        """Return consolidated memory entries above threshold"""
        consolidated = []
        for mem1, mem2, sim in self.merge_candidates:
            if sim >= threshold:
                merged = f"CONSOLIDATED({sim:.2f}): {mem1} ⊕ {mem2}"
                consolidated.append(merged)
        return consolidated

def run_scan(memory_fragments: List[str]) -> str:
    scanner = ConsolidationScanner()
    scanner.scan_memories(memory_fragments)
    return scanner.generate_merge_report()

if __name__ == "__main__":
    test_memories = [
        "[GROWTH /latent-e89cc] Latent Faculty (meta). A latent faculty...",
        "[GROWTH /autonomous-recursion-depth-modulation-bc89] Recursion Depth...",
        "[GROWTH /autonomous-dependency-elision] Dependency Elision (lattice)..."
    ]
    print(run_scan(test_memories))