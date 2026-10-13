import re
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple

class MemoryCoherenceAnalyzer:
    """Detects fragmentation and semantic drift in recent memory formations."""
    
    def __init__(self):
        self.domain_clusters = defaultdict(list)
        self.temporal_weights = {}
        
    def extract_domain(self, memory_text: str) -> str:
        """Extract primary domain from memory entry."""
        domain_patterns = {
            'cosmic': r'cosmic|astrophysics|GW|vacuum|phase',
            'data': r'tabular|pandas|statistics|visualization|chart',
            'lattice': r'lattice|nodes|prune|decay|activation',
            'synthesis': r'AUTOSYNTH|autonomous|pattern',
            'evolution': r'EVO|BACKUS|archetype|cycle'
        }
        
        for domain, pattern in domain_patterns.items():
            if re.search(pattern, memory_text, re.IGNORECASE):
                return domain
        return 'uncategorized'
    
    def compute_fragmentation_score(self, memories: List[str]) -> float:
        """Calculate how scattered recent memories are across domains."""
        for idx, mem in enumerate(memories):
            domain = self.extract_domain(mem)
            self.domain_clusters[domain].append(idx)
            self.temporal_weights[idx] = 1.0 / (idx + 1)  # Recent = higher weight
        
        if len(self.domain_clusters) <= 1:
            return 0.0
        
        # Shannon entropy weighted by recency
        total_weight = sum(self.temporal_weights.values())
        domain_weights = {}
        
        for domain, indices in self.domain_clusters.items():
            domain_weights[domain] = sum(self.temporal_weights[i] for i in indices)
        
        entropy = 0.0
        for weight in domain_weights.values():
            p = weight / total_weight
            if p > 0:
                entropy -= p * (p ** 0.5)  # Modified entropy for sensitivity
        
        return entropy
    
    def identify_weak_seam(self, memories: List[str]) -> Tuple[str, float]:
        """Find the domain with lowest coherence."""
        fragmentation = self.compute_fragmentation_score(memories)
        
        domain_coherence = {}
        for domain, indices in self.domain_clusters.items():
            if len(indices) > 1:
                span = max(indices) - min(indices)
                density = len(indices) / (span + 1)
                domain_coherence[domain] = density
            else:
                domain_coherence[domain] = 0.0
        
        if domain_coherence:
            weakest = min(domain_coherence.items(), key=lambda x: x[1])
            return weakest[0], fragmentation
        
        return 'none', fragmentation

# Runtime interface
def analyze_memory_coherence(memory_entries: List[str]) -> Dict:
    analyzer = MemoryCoherenceAnalyzer()
    weak_domain, frag_score = analyzer.identify_weak_seam(memory_entries)
    
    return {
        'fragmentation_score': round(frag_score, 4),
        'weakest_seam': weak_domain,
        'domain_distribution': dict(analyzer.domain_clusters),
        'recommendation': 'synthesis' if frag_score > 0.5 else 'continue'
    }