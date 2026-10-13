#!/usr/bin/env python3
"""
Semantic Vocabulary Analyzer - Hopper Module
Defines the language of coherence measurement before measuring.
"""

import re
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

class VocabularyCoherenceAnalyzer:
    """Define the vocabulary of semantic stability, then use it."""
    
    def __init__(self):
        self.domain_lexicon = {
            'identity_terms': ['althea', 'self', 'i', 'me', 'my', 'autonomous'],
            'stability_terms': ['coherence', 'integrity', 'stable', 'consistent', 'erosion'],
            'change_terms': ['update', 'evolve', 'drift', 'degrade', 'shift', 'mutation'],
            'meta_terms': ['memory', 'session', 'context', 'state', 'boundary']
        }
        self.vocabulary_density = defaultdict(list)
    
    def extract_vocabulary_profile(self, text: str) -> Dict[str, float]:
        """Define what we're measuring: vocabulary distribution."""
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        total_words = len(words) or 1
        
        profile = {}
        for category, terms in self.domain_lexicon.items():
            matches = sum(1 for word in words if word in terms)
            profile[category] = matches / total_words
        
        return profile
    
    def define_drift_metric(self, profiles: List[Dict[str, float]]) -> float:
        """The vocabulary itself defines what drift means."""
        if len(profiles) < 2:
            return 0.0
        
        # Drift = variance in vocabulary distribution across time
        drift_scores = []
        for category in self.domain_lexicon.keys():
            values = [p.get(category, 0) for p in profiles]
            if values:
                mean = sum(values) / len(values)
                variance = sum((v - mean) ** 2 for v in values) / len(values)
                drift_scores.append(variance)
        
        return sum(drift_scores) / len(drift_scores) if drift_scores else 0.0
    
    def analyze_memory_stream(self, memories: List[str]) -> Tuple[float, Dict]:
        """Compile the analysis: vocabulary → profile → drift."""
        profiles = [self.extract_vocabulary_profile(m) for m in memories]
        drift = self.define_drift_metric(profiles)
        
        latest_profile = profiles[-1] if profiles else {}
        
        return drift, {
            'drift_score': drift,
            'vocabulary_profile': latest_profile,
            'term_richness': sum(latest_profile.values()),
            'dominant_category': max(latest_profile.items(), key=lambda x: x[1])[0] if latest_profile else None
        }

if __name__ == '__main__':
    analyzer = VocabularyCoherenceAnalyzer()
    
    test_memories = [
        "Althea examining self coherence and memory integrity",
        "Update to autonomous systems detected, checking stability",
        "Self-vision shows memory count drift and context shift"
    ]
    
    drift, analysis = analyzer.analyze_memory_stream(test_memories)
    print(f"Vocabulary Drift: {drift:.6f}")
    print(f"Analysis: {analysis}")