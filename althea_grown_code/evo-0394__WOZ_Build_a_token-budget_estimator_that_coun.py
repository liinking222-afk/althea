#!/usr/bin/env python3
"""Token Budget Estimator - Woz-style constraint awareness"""

import re
from typing import Dict, Tuple

class TokenEstimator:
    """Lightweight token counter for code and text - every token counts"""
    
    # Approximate tokens per character for different content types
    RATIOS = {
        'code': 0.33,      # Code is denser
        'prose': 0.25,     # Natural language
        'data': 0.40,      # JSON/structured data
        'mixed': 0.28      # Default fallback
    }
    
    def __init__(self, budget: int = 200000):
        self.budget = budget
        self.spent = 0
        self.estimates = []
    
    def estimate(self, content: str, content_type: str = 'mixed') -> int:
        """Fast character-based token estimation"""
        ratio = self.RATIOS.get(content_type, self.RATIOS['mixed'])
        return int(len(content) * ratio)
    
    def check_code_block(self, code: str, language: str = 'python') -> Dict:
        """Analyze a code block before execution"""
        tokens = self.estimate(code, 'code')
        lines = len(code.split('\n'))
        
        # Density metric: tokens per line
        density = tokens / max(lines, 1)
        
        return {
            'tokens': tokens,
            'lines': lines,
            'density': round(density, 2),
            'fits_budget': (self.spent + tokens) <= self.budget,
            'remaining': self.budget - self.spent - tokens
        }
    
    def parse_module(self, module_text: str) -> Tuple[Dict, str]:
        """Extract and estimate a complete module"""
        # Find code fence
        match = re.search(r'