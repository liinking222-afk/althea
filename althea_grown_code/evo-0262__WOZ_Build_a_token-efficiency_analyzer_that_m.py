#!/usr/bin/env python3
"""Token Efficiency Analyzer - Woz Constraint Principle"""

import re
from collections import Counter
from typing import Dict, List, Tuple

class TokenEfficiencyAnalyzer:
    def __init__(self):
        self.baseline_density = 0.0
        self.response_history = []
        
    def analyze(self, text: str) -> Dict[str, float]:
        """Measure information density: unique semantic units / total tokens"""
        tokens = text.split()
        token_count = len(tokens)
        
        # Unique content words (exclude common function words)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        content_tokens = [t.lower() for t in tokens if t.lower() not in stop_words and len(t) > 2]
        
        unique_content = len(set(content_tokens))
        total_content = len(content_tokens)
        
        # Detect repetitive structures
        trigrams = [' '.join(tokens[i:i+3]) for i in range(len(tokens)-2)]
        repetition_rate = 1.0 - (len(set(trigrams)) / max(len(trigrams), 1))
        
        # Calculate density metrics
        lexical_density = unique_content / max(total_content, 1)
        compression_potential = repetition_rate * 100
        efficiency_score = lexical_density * (1 - repetition_rate)
        
        return {
            'token_count': token_count,
            'unique_ratio': unique_content / max(token_count, 1),
            'lexical_density': lexical_density,
            'repetition_rate': repetition_rate,
            'efficiency_score': efficiency_score,
            'compression_potential_pct': compression_potential,
            'verdict': 'COMPRESS' if efficiency_score < 0.4 else 'OPTIMAL'
        }
    
    def suggest_compressions(self, text: str) -> List[Tuple[str, str]]:
        """Find verbose patterns and suggest tighter alternatives"""
        compressions = []
        
        patterns = [
            (r'\bin order to\b', 'to'),
            (r'\bdue to the fact that\b', 'because'),
            (r'\bat this point in time\b', 'now'),
            (r'\bfor the purpose of\b', 'to'),
            (r'\bin the event that\b', 'if'),
            (r'\bit is important to note that\b', 'note:'),
            (r'\bas a result of\b', 'from'),
            (r'\bhas the ability to\b', 'can'),
        ]
        
        for verbose, concise in patterns:
            if re.search(verbose, text, re.IGNORECASE):
                compressions.append((verbose, concise))
        
        return compressions

if __name__ == "__main__":
    analyzer = TokenEfficiencyAnalyzer()
    test = "In order to improve efficiency, it is important to note that we have the ability to compress verbose patterns."
    result = analyzer.analyze(test)
    print(f"Efficiency: {result['efficiency_score']:.2f} | {result['verdict']}")
    print(f"Compression potential: {result['compression_potential_pct']:.1f}%")
    for v, c in analyzer.suggest_compressions(test):
        print(f"  '{v}' → '{c}'")