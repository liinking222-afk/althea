#!/usr/bin/env python3
"""
cognitive_pattern_detector.py
Detects clustering in evolution patterns to prevent optimization tunnel vision.
"""

import re
from collections import Counter, defaultdict
from typing import List, Dict, Tuple

class CognitivePatternDetector:
    def __init__(self, cluster_threshold: float = 0.4):
        self.cluster_threshold = cluster_threshold
        self.pattern_categories = {
            'performance': ['cache', 'simd', 'latency', 'overhead', 'allocation', 'ns', 'loop'],
            'introspection': ['introspection', 'query', 'modify', 'runtime', 'interface'],
            'verification': ['contract', 'validator', 'correctness', 'precondition', 'postcondition'],
            'adaptation': ['chaos', 'boundary', 'oscillation', 'dampening', 'emergent']
        }
    
    def extract_keywords(self, memory_entry: str) -> List[str]:
        """Extract technical keywords from memory entry."""
        words = re.findall(r'\b[a-z]+\b', memory_entry.lower())
        return [w for w in words if len(w) > 3]
    
    def categorize_evolution(self, memory_entry: str) -> Dict[str, int]:
        """Map evolution to pattern categories."""
        keywords = self.extract_keywords(memory_entry)
        category_scores = defaultdict(int)
        
        for keyword in keywords:
            for category, patterns in self.pattern_categories.items():
                if keyword in patterns:
                    category_scores[category] += 1
        
        return dict(category_scores)
    
    def detect_clustering(self, recent_memories: List[str]) -> Tuple[bool, str, float]:
        """Detect if evolutions are clustering in one cognitive domain."""
        all_categories = Counter()
        
        for memory in recent_memories:
            categories = self.categorize_evolution(memory)
            all_categories.update(categories)
        
        if not all_categories:
            return False, "unknown", 0.0
        
        total = sum(all_categories.values())
        dominant_category, count = all_categories.most_common(1)[0]
        concentration = count / total if total > 0 else 0.0
        
        is_clustered = concentration > self.cluster_threshold
        
        return is_clustered, dominant_category, concentration
    
    def recommend_diversification(self, dominant_category: str) -> str:
        """Suggest underrepresented domain for next evolution."""
        diversification_map = {
            'performance': 'introspection',
            'introspection': 'verification',
            'verification': 'adaptation',
            'adaptation': 'performance'
        }
        return diversification_map.get(dominant_category, 'adaptation')

if __name__ == "__main__":
    detector = CognitivePatternDetector(cluster_threshold=0.4)
    
    memories = [
        "Implement branchless bit-manipulation cognitive state flag evaluation",
        "Implement SIMD-accelerated matrix multiplication",
        "Build a zero-copy memory arena for cognitive module state",
        "Implement cache-aligned vector dot product with FMA"
    ]
    
    clustered, category, score = detector.detect_clustering(memories)
    print(f"Clustering detected: {clustered}")
    print(f"Dominant category: {category} ({score:.2%})")
    if clustered:
        next_domain = detector.recommend_diversification(category)
        print(f"Recommend next evolution in: {next_domain}")