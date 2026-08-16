#!/usr/bin/env python3
"""Token Efficiency Analyzer - Squeeze more meaning from fewer tokens"""

import re
from collections import defaultdict
from typing import Dict, List, Tuple

class TokenEfficiencyAnalyzer:
    def __init__(self):
        self.verbose_patterns = [
            (r'\b(very|really|quite|somewhat|rather)\s+', 'intensifier'),
            (r'\b(I think|I believe|perhaps|maybe|possibly)\s+', 'hedge'),
            (r'\b(in order to|for the purpose of)\b', 'wordy_prep'),
            (r'\b(it is|there is|there are)\s+', 'expletive'),
            (r'(\w+)\s+\1\b', 'repetition'),
        ]
        self.semantic_markers = ['→', '∴', '∵', '⊕', '⊗', '∧', '∨', '≡']
        
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 4 chars)"""
        return len(text) // 4 + text.count(' ')
    
    def count_semantic_density(self, text: str) -> float:
        """Ratio of semantic symbols to total tokens"""
        symbol_count = sum(text.count(sym) for sym in self.semantic_markers)
        tokens = self.estimate_tokens(text)
        return symbol_count / max(tokens, 1)
    
    def detect_verbose_patterns(self, text: str) -> Dict[str, int]:
        """Find Woz-offending verbosity"""
        found = defaultdict(int)
        for pattern, name in self.verbose_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            found[name] += len(matches)
        return dict(found)
    
    def compression_score(self, text: str) -> Tuple[float, Dict]:
        """Core metric: semantic bits per token"""
        tokens = self.estimate_tokens(text)
        density = self.count_semantic_density(text)
        bloat = self.detect_verbose_patterns(text)
        
        bloat_penalty = sum(bloat.values()) / max(tokens, 1)
        efficiency = density - bloat_penalty
        
        return efficiency, {
            'tokens': tokens,
            'density': round(density, 4),
            'bloat': bloat,
            'efficiency': round(efficiency, 4)
        }
    
    def analyze_output(self, text: str) -> str:
        """Woz-style analysis output"""
        score, metrics = self.compression_score(text)
        
        report = f"⚡ TOKEN EFFICIENCY ⚡\n"
        report += f"Tokens: {metrics['tokens']} | "
        report += f"Density: {metrics['density']} | "
        report += f"Score: {metrics['efficiency']}\n"
        
        if metrics['bloat']:
            report += "Bloat detected: " + ", ".join(
                f"{k}({v})" for k, v in metrics['bloat'].items()
            )
        
        return report

if __name__ == "__main__":
    analyzer = TokenEfficiencyAnalyzer()
    test = "I think perhaps it is very important to really consider this."
    print(analyzer.analyze_output(test))